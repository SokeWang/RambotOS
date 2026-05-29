"""
Skill Index Manager - Intelligent skill discovery and retrieval system

This module provides:
1. Fast in-memory skill metadata indexing
2. Vector-based semantic search for skill retrieval
3. Automatic change detection and refresh
4. Support for intent-based skill selection
"""

import os
import re
import time
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from loguru import logger
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.tools import tool
from config.config import CFG

BASE_SKILLS_PATH = CFG.SKILLS_PATH


@dataclass
class SkillMetadata:
    """Metadata for a single skill"""
    name: str
    description: str
    path: str
    tools: List[str]  # List of tool names provided by this skill
    mtime: float = 0.0 # Modification time for change detection
    

class SkillIndex:
    """
    Centralized skill indexing and retrieval system.
    
    Features:
    - In-memory skill metadata cache
    - Vector embeddings for semantic search
    - Automatic change detection
    - O(1) skill summary retrieval
    """
    
    def __init__(self):
        self.skills: Dict[str, SkillMetadata] = {}
        self._last_scan_time = 0
        self._skills_dir_mtime = 0
        self._summary_cache: Optional[str] = None
        
        # ChromaDB for vector search
        self._chroma_client = None
        self._collection = None
        self._embeddings = None
        
        # Track if embeddings are ready
        self._embeddings_ready = False
        
    def initialize(self):
        """Initialize the skill index (synchronous startup)"""
        logger.info("SkillIndex: Initializing...")
        
        # Scan skills directory
        self._scan_skills()
        
        # Initialize ChromaDB for vector search
        try:
            db_path = os.path.join(CFG.PROJECT_ROOT, "backend", "db", "skill_embeddings")
            os.makedirs(db_path, exist_ok=True)
            
            self._chroma_client = chromadb.PersistentClient(path=db_path)
            self._collection = self._chroma_client.get_or_create_collection(
                name="skill_embeddings"
            )
            
            self._embeddings = GoogleGenerativeAIEmbeddings(
                google_api_key=CFG.api_key,
                model=CFG.embedding_model
            )
            
            # Generate embeddings asynchronously (non-blocking)
            self._generate_embeddings()
            
            logger.info(f"SkillIndex: Initialized with {len(self.skills)} skills")
        except Exception as e:
            logger.error(f"SkillIndex: Failed to initialize ChromaDB: {e}")
    
    def _scan_skills(self):
        """Scan skills directory and extract metadata"""
        if not os.path.exists(BASE_SKILLS_PATH):
            logger.warning(f"Skills directory not found: {BASE_SKILLS_PATH}")
            return
        
        self.skills.clear()
        
        for skill_dir_name in os.listdir(BASE_SKILLS_PATH):
            metadata = self._parse_skill_md(skill_dir_name)
            if metadata:
                self.skills[metadata.name] = metadata
        
        # Update directory mtime
        self._skills_dir_mtime = os.path.getmtime(BASE_SKILLS_PATH)
        self._last_scan_time = time.time()
        
        # Invalidate summary cache
        self._summary_cache = None

    def _parse_skill_md(self, skill_dir_name: str) -> Optional[SkillMetadata]:
        """Parse metadata for a single skill directory"""
        skill_dir = os.path.join(BASE_SKILLS_PATH, skill_dir_name)
        if not os.path.isdir(skill_dir):
            return None
        
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(skill_md_path):
            return None
        
        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse frontmatter
            name_match = re.search(r'^name:\s*(.*)$', content, re.MULTILINE)
            desc_match = re.search(r'^description:\s*(.*)$', content, re.MULTILINE)
            
            name = name_match.group(1).strip() if name_match else skill_dir_name
            description = desc_match.group(1).strip() if desc_match else "No description"
            
            # Extract tool names (if documented)
            tools = self._extract_tool_names(content)
            
            return SkillMetadata(
                name=name,
                description=description,
                path=skill_md_path,
                tools=tools,
                mtime=os.path.getmtime(skill_md_path)
            )
        except Exception as e:
            logger.error(f"SkillIndex: Error parsing {skill_md_path}: {e}")
            return None
    
    def _extract_tool_names(self, skill_content: str) -> List[str]:
        """Extract tool names from skill documentation"""
        # Simple heuristic: look for function definitions in scripts section
        # This can be enhanced based on your skill documentation format
        tools = []
        # For now, return empty list - can be enhanced later
        return tools
    
    def _generate_embeddings(self):
        """Generate embeddings for all skills (runs in background)"""
        try:
            logger.info("SkillIndex: Generating embeddings for skills...")
            
            # 1. Update/Add existing skills
            for metadata in self.skills.values():
                self._upsert_skill_embedding(metadata)
            
            # 2. Pruning: Remove skills from ChromaDB that no longer exist on disk
            self._prune_index()
            
            self._embeddings_ready = True
            logger.info(f"SkillIndex: Embeddings synchronized for {len(self.skills)} skills")
            
        except Exception as e:
            logger.error(f"SkillIndex: Failed to generate embeddings: {e}")

    def _prune_index(self):
        """Remove entries from ChromaDB that are not in the current self.skills cache"""
        if not self._collection:
            return
        try:
            results = self._collection.get()
            existing_ids = set(results['ids'])
            current_ids = set(self.skills.keys())
            
            to_delete = list(existing_ids - current_ids)
            if to_delete:
                logger.info(f"SkillIndex: Pruning {len(to_delete)} orphaned entries from vector index: {to_delete}")
                self._collection.delete(ids=to_delete)
        except Exception as e:
            logger.error(f"SkillIndex: Failed to prune index: {e}")

    def _upsert_skill_embedding(self, metadata: SkillMetadata):
        """
        Generate and store embedding for a single skill.
        Includes mtime check to avoid redundant API calls.
        """
        if not self._embeddings or not self._collection:
            return
            
        try:
            # Check existing record in ChromaDB
            existing = self._collection.get(ids=[metadata.name])
            if existing and existing['metadatas']:
                stored_mtime = existing['metadatas'][0].get('mtime', 0.0)
                # If mtime matches, skip embedding generation
                if abs(stored_mtime - metadata.mtime) < 0.001:
                    logger.debug(f"SkillIndex: Skipping unchanged skill: {metadata.name}")
                    return

            # Create searchable text
            text = f"{metadata.name}: {metadata.description}"
            
            # Generate embedding
            embedding = self._embeddings.embed_query(text)
            
            # Store in ChromaDB
            self._collection.upsert(
                ids=[metadata.name],
                embeddings=[embedding],
                metadatas=[{
                    "name": metadata.name,
                    "description": metadata.description,
                    "path": metadata.path,
                    "mtime": metadata.mtime
                }],
                documents=[text]
            )
            logger.info(f"SkillIndex: Updated index for skill: {metadata.name}")
        except Exception as e:
            logger.error(f"SkillIndex: Failed to upsert embedding for {metadata.name}: {e}")

    def remove_skill(self, skill_name: str):
        """Remove a skill from both memory and vector index"""
        if skill_name in self.skills:
            del self.skills[skill_name]
        
        if self._collection:
            try:
                self._collection.delete(ids=[skill_name])
                logger.info(f"SkillIndex: Removed skill '{skill_name}' from vector index.")
            except Exception as e:
                logger.error(f"SkillIndex: Failed to delete skill {skill_name} from index: {e}")
        
        self._summary_cache = None

    def update_skill(self, skill_dir_name: str) -> bool:
        """
        Incremental update for a single skill.
        Useful when AI generates or edits a SKILL.md.
        If the dir doesn't exist anymore, it performs a removal.
        """
        metadata = self._parse_skill_md(skill_dir_name)
        
        if not metadata:
            # Assume deletion if metadata cannot be parsed/found
            # Note: skill_dir_name here might need to be resolved to skill name
            # For robustness, we'll try to remove it if it exists in our cache
            logger.info(f"SkillIndex: Directory '{skill_dir_name}' not found or invalid. Attempting removal...")
            self.remove_skill(skill_dir_name)
            return True
            
        # Update in-memory cache
        self.skills[metadata.name] = metadata
        
        # Update vector database
        self._upsert_skill_embedding(metadata)
        
        # Invalidate summary cache
        self._summary_cache = None
        
        logger.info(f"SkillIndex: Incremental update completed for skill: {metadata.name}")
        return True
    
    def refresh_if_needed(self) -> bool:
        """
        Check if skills directory or any SKILL.md has changed and refresh if needed.
        
        Returns:
            True if refresh occurred, False otherwise
        """
        if not os.path.exists(BASE_SKILLS_PATH):
            return False
        
        # Check directory mtime (detects new/deleted skill folders)
        current_dir_mtime = os.path.getmtime(BASE_SKILLS_PATH)
        dir_changed = current_dir_mtime > self._skills_dir_mtime
        
        # Check individual SKILL.md files (detects content changes)
        files_changed = False
        if not dir_changed:
            for skill_dir_name in os.listdir(BASE_SKILLS_PATH):
                skill_dir = os.path.join(BASE_SKILLS_PATH, skill_dir_name)
                if not os.path.isdir(skill_dir):
                    continue
                
                skill_md_path = os.path.join(skill_dir, "SKILL.md")
                if os.path.exists(skill_md_path):
                    file_mtime = os.path.getmtime(skill_md_path)
                    # Check if this file is newer than our last scan
                    if file_mtime > self._last_scan_time:
                        files_changed = True
                        break
        
        if dir_changed or files_changed:
            logger.info("SkillIndex: Changes detected, refreshing...")
            self._scan_skills()
            self._generate_embeddings()
            return True
        
        return False
    
    def get_all_skills_summary(self) -> str:
        """
        Get formatted summary of all skills (cached).
        
        Returns:
            Formatted string with all skill descriptions
        """
        if self._summary_cache is not None:
            return self._summary_cache
        
        if not self.skills:
            return "No skills available."
        
        lines = []
        for metadata in self.skills.values():
            lines.append(f"- **{metadata.name}**: {metadata.description} (Path: {metadata.path})")
        
        self._summary_cache = "\n".join(lines)
        return self._summary_cache
    
    def get_all_skill_names(self) -> List[str]:
        """Get list of all skill names"""
        return list(self.skills.keys())
    
    def search_skills_by_intent(self, query: str, top_k: int = 3) -> List[str]:
        """
        Search for relevant skills using vector similarity.
        Strict mode: Returns empty list if not ready or no confident matches.
        
        Args:
            query: User intent or task description
            top_k: Number of top skills to return
            
        Returns:
            List of skill names ranked by relevance, or empty list if no matches.
        """
        if not self._embeddings_ready:
            logger.warning("SkillIndex: Embeddings not ready, returning empty list")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self._embeddings.embed_query(query)
            
            # Search in ChromaDB
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, len(self.skills))
            )
            
            if results and results['ids'] and len(results['ids'][0]) > 0:
                skill_names = results['ids'][0]
                # Log top distance for quality monitoring
                if results.get('distances') and results['distances'][0]:
                    dist = results['distances'][0][0]
                    logger.info(f"SkillIndex: Retrieved skills for '{query}': {skill_names} (Best Dist: {dist:.4f})")
                
                return skill_names
            
        except Exception as e:
            logger.error(f"SkillIndex: Search failed: {e}")
        
        return []
    
    def get_skill_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
        """Get metadata for a specific skill"""
        return self.skills.get(skill_name)


# Global singleton instance
skill_index = SkillIndex()
