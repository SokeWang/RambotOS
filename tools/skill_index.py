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

BASE_SKILLS_PATH = "/Users/wangpeidong/Documents/RambotOS/skills"


@dataclass
class SkillMetadata:
    """Metadata for a single skill"""
    name: str
    description: str
    path: str
    tools: List[str]  # List of tool names provided by this skill
    

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
            db_path = "./db/skill_embeddings"
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
            skill_dir = os.path.join(BASE_SKILLS_PATH, skill_dir_name)
            
            if not os.path.isdir(skill_dir):
                continue
            
            skill_md_path = os.path.join(skill_dir, "SKILL.md")
            if not os.path.exists(skill_md_path):
                continue
            
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
                
                metadata = SkillMetadata(
                    name=name,
                    description=description,
                    path=skill_md_path,
                    tools=tools
                )
                
                self.skills[name] = metadata
                
            except Exception as e:
                logger.error(f"SkillIndex: Error parsing {skill_md_path}: {e}")
        
        # Update directory mtime
        self._skills_dir_mtime = os.path.getmtime(BASE_SKILLS_PATH)
        self._last_scan_time = time.time()
        
        # Invalidate summary cache
        self._summary_cache = None
    
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
            
            for skill_name, metadata in self.skills.items():
                # Create searchable text
                text = f"{metadata.name}: {metadata.description}"
                
                # Generate embedding
                embedding = self._embeddings.embed_query(text)
                
                # Store in ChromaDB
                self._collection.upsert(
                    ids=[skill_name],
                    embeddings=[embedding],
                    metadatas=[{
                        "name": metadata.name,
                        "description": metadata.description,
                        "path": metadata.path
                    }],
                    documents=[text]
                )
            
            self._embeddings_ready = True
            logger.info(f"SkillIndex: Embeddings generated for {len(self.skills)} skills")
            
        except Exception as e:
            logger.error(f"SkillIndex: Failed to generate embeddings: {e}")
    
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
        
        Args:
            query: User intent or task description
            top_k: Number of top skills to return
            
        Returns:
            List of skill names ranked by relevance
        """
        if not self._embeddings_ready:
            logger.warning("SkillIndex: Embeddings not ready, returning all skills")
            return self.get_all_skill_names()[:top_k]
        
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
                logger.info(f"SkillIndex: Retrieved skills for '{query}': {skill_names}")
                return skill_names
            
        except Exception as e:
            logger.error(f"SkillIndex: Search failed: {e}")
        
        # Fallback: return all skills
        return self.get_all_skill_names()[:top_k]
    
    def get_skill_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
        """Get metadata for a specific skill"""
        return self.skills.get(skill_name)
    
    def get_retrieve_tool(self):
        """
        Create a tool that allows the agent to retrieve relevant skills.
        
        Returns:
            LangChain tool for skill retrieval
        """
        skill_index_ref = self
        
        @tool
        def retrieve_skills(task_description: str) -> str:
            """
            Search and load skills relevant to the task.
            Call this ONLY when you need capabilities beyond your current tools.
            After calling this, your tool set will be expanded with the relevant skills.
            
            Args:
                task_description: Description of what you need to accomplish
                
            Returns:
                Information about loaded skills
            """
            relevant_skills = skill_index_ref.search_skills_by_intent(task_description, top_k=3)
            
            if not relevant_skills:
                return "No relevant skills found."
            
            # Return special marker for agent rebuild
            skill_list = ",".join(relevant_skills)
            return f"RELOAD_AGENT:{skill_list}"
        
        return retrieve_skills


# Global singleton instance
skill_index = SkillIndex()
