import chromadb
import sys
from chromadb.config import Settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config.config import CFG
import time
from loguru import logger
from typing import List, Dict
import os

class MemoryManager:
    def __init__(self, collection_name="long_term_memory"):
        # Initialize ChromaDB Persistent Client
        # Use user's home directory for persistence when frozen/packaged
        if getattr(sys, 'frozen', False):
            db_path = os.path.expanduser("~/.rambot/db/chroma_data")
        else:
            db_path = "./db/chroma_data"
            
        if not os.path.exists(db_path):
            os.makedirs(db_path, exist_ok=True)
            
        try:
            # Explicitly disable telemetry to avoid dynamic import issues in PyInstaller (posthog error)
            settings = Settings(anonymized_telemetry=False)
            self.client = chromadb.PersistentClient(path=db_path, settings=settings)
            # Get or create the collection
            self.collection = self.client.get_or_create_collection(name=collection_name)
            
            self.embeddings = GoogleGenerativeAIEmbeddings(
                google_api_key=CFG.api_key,
                model=CFG.embedding_model
            )
            logger.info(f"ChromaDB Memory Manager initialized (Path: {db_path}, Collection: {collection_name}).")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise e

    def add_fact(self, fact: Dict, session_id: str = "global"):
        """
        Add a structured fact to long-term memory.
        fact: {"subject": "...", "predicate": "...", "object": "..."}
        """
        try:
            subject = fact.get("subject", "").strip()
            predicate = fact.get("predicate", "").strip()
            obj = fact.get("object", "").strip()
            
            if not subject or not predicate or not obj:
                return

            text = f"{subject} {predicate} {obj}"
            
            # Check for existing identical facts in this session to prevent duplicates
            # We use a filter for the exact triple and session
            existing = self.collection.get(
                where={
                    "$and": [
                        {"session_id": session_id},
                        {"subject": subject},
                        {"predicate": predicate},
                        {"object": obj}
                    ]
                },
                limit=1
            )

            if existing and existing['ids']:
                # Fact exists, just update the timestamp
                mem_id = existing['ids'][0]
                self.collection.update(
                    ids=[mem_id],
                    metadatas=[{
                        "type": "fact",
                        "subject": subject,
                        "predicate": predicate,
                        "object": obj,
                        "timestamp": time.time(),
                        "session_id": session_id
                    }]
                )
                logger.info(f"Updated timestamp for existing Fact (Session: {session_id}): {text}")
                return

            # New fact, add it
            embedding = self.embeddings.embed_query(text)
            mem_id = f"fact_{time.time()}_{session_id}"
            
            self.collection.add(
                ids=[mem_id],
                embeddings=[embedding],
                metadatas=[{
                    "type": "fact",
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                    "timestamp": time.time(),
                    "session_id": session_id
                }],
                documents=[text]
            )
            logger.info(f"Added Fact to ChromaDB (Session: {session_id}): {text}")
        except Exception as e:
            logger.error(f"Failed to add fact to ChromaDB: {e}")



    def retrieve_memories(self, query: str, session_id: str = "global", k: int = 5) -> List[Dict]:
        """
        Retrieve top-k relevant facts for a specific session.
        """
        try:
            query_embedding = self.embeddings.embed_query(query)
            
            # Query ChromaDB with session_id filter
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where={"session_id": session_id},
                include=["metadatas", "documents"]
            )
            
            memories = []
            if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
                for i in range(len(results['metadatas'][0])):
                    metadata = results['metadatas'][0][i]
                    doc = results['documents'][0][i]
                    memories.append({
                        "id": results['ids'][0][i],
                        "subject": metadata.get("subject"),
                        "predicate": metadata.get("predicate"),
                        "object": metadata.get("object"),
                        "text": doc,
                        "timestamp": metadata.get("timestamp")
                    })
            
            logger.info(f"Retrieved {len(memories)} facts for session {session_id}")
            return memories
        except Exception as e:
            logger.error(f"Failed to retrieve memories for session {session_id}: {e}")
            return []

    def get_all_memories(self, session_id: str = None) -> List[Dict]:
        # Implementation remains similar but returns fact fields
        try:
            query = {}
            if session_id:
                query = {"session_id": session_id}
                
            results = self.collection.get(
                where=query if query else None,
                include=["metadatas", "documents"],
            )
            
            memories = []
            if results and results['metadatas']:
                for i in range(len(results['metadatas'])):
                    metadata = results['metadatas'][i]
                    doc = results['documents'][i]
                    memories.append({
                        "id": results['ids'][i],
                        "subject": metadata.get("subject"),
                        "predicate": metadata.get("predicate"),
                        "object": metadata.get("object"),
                        "text": doc,
                        "timestamp": metadata.get("timestamp"),
                        "session_id": metadata.get("session_id", "global")
                    })
            
            memories.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            return memories
        except Exception as e:
            logger.error(f"Failed to get memories: {e}")
            return []

# Export global singleton
memory_manager = MemoryManager()
