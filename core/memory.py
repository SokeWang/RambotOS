import chromadb
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
        db_path = "./db/chroma_data"
        if not os.path.exists(db_path):
            os.makedirs(db_path, exist_ok=True)
            
        try:
            self.client = chromadb.PersistentClient(path=db_path)
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

    def add_memory(self, role: str, content: str):
        """
        Add a message to long-term memory with its embedding.
        """
        try:
            text = f"{role}: {content}"
            embedding = self.embeddings.embed_query(text)
            
            # Generate a unique ID based on timestamp and role
            mem_id = f"{role}_{time.time()}"
            
            self.collection.add(
                ids=[mem_id],
                embeddings=[embedding],
                metadatas=[{
                    "role": role,
                    "content": content,
                    "timestamp": time.time()
                }],
                documents=[text]
            )
            logger.info(f"Added to ChromaDB memory: {role}: {content[:50]}...")
        except Exception as e:
            logger.error(f"Failed to add to ChromaDB memory: {e}")

    def retrieve_memories(self, query: str, k: int = 3) -> List[Dict]:
        """
        Retrieve top-k relevant memories based on the query.
        """
        try:
            query_embedding = self.embeddings.embed_query(query)
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["metadatas", "documents"]
            )
            
            memories = []
            if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
                for i in range(len(results['metadatas'][0])):
                    metadata = results['metadatas'][0][i]
                    doc = results['documents'][0][i]
                    memories.append({
                        "role": metadata.get("role"),
                        "content": metadata.get("content"),
                        "text": doc,
                        "timestamp": metadata.get("timestamp")
                    })
            
            logger.info(f"Retrieved {len(memories)} memories from ChromaDB for query: {query[:50]}...")
            return memories
        except Exception as e:
            logger.error(f"Failed to retrieve memories from ChromaDB: {e}")
            return []

    def get_tool(self):
        """
        Returns a LangChain tool for searching long-term memory.
        """
        from langchain_core.tools import tool

        @tool
        def search_memory(query: str):
            """
            Search your long-term memory for past conversations, personal facts, and previous interactions.
            Use this when the user asks about something you should remember from the past.
            """
            memories = self.retrieve_memories(query, k=5)
            if not memories:
                return "No relevant past memories found."
            
            res = "Found the following relevant past interactions:\n"
            for m in memories:
                res += f"- [{m['role']}]: {m['content']}\n"
            return res

        return search_memory
