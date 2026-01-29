import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config.config import CFG
from utils.exceptions import ToolRetrievalError
from loguru import logger
import os

class ToolRetriever:
    def __init__(self, collection_name="tool_vectors"):
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
            logger.info(f"ChromaDB Tool Retriever initialized (Path: {db_path}, Collection: {collection_name}).")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB Tool Retriever: {e}")
            raise ToolRetrievalError("Failed to initialize tool database", {"error": str(e)})

    def index_tools(self, tools):
        """
        Tools are expected to be a list of LangChain tools.
        Indexing involves clearing existing tools and adding new ones with embeddings.
        """
        try:
            # Check for existing collection and delete all items if they exist
            # Note: ChromaDB doesn't have a simple delete_all on collection level without deleting collection
            # but we can get all IDs and delete them.
            all_ids = self.collection.get()["ids"]
            if all_ids:
                self.collection.delete(ids=all_ids)
            
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for tool in tools:
                name = getattr(tool, "name", "unknown")
                description = getattr(tool, "description", "")
                text = f"Tool Name: {name}\nDescription: {description}"
                
                embedding = self.embeddings.embed_query(text)
                
                ids.append(name) # Using tool name as ID
                embeddings.append(embedding)
                metadatas.append({"name": name, "description": description})
                documents.append(text)

            if ids:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
                logger.info(f"Indexed {len(ids)} tools into ChromaDB (Collection: {self.collection.name}).")
        except Exception as e:
            logger.error(f"Failed to index tools: {e}")
            raise ToolRetrievalError("Failed to index tools", {"error": str(e)})

    def retrieve(self, query, k=5):
        """
        Retrieve top-k most relevant tools for the given query.
        """
        if not query.strip():
            return []
            
        try:
            query_embedding = self.embeddings.embed_query(query)
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["metadatas"]
            )
            
            tool_names = []
            if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
                for metadata in results['metadatas'][0]:
                    tool_names.append(metadata.get("name"))
            
            logger.info(f"Retrieved {len(tool_names)} tools from ChromaDB for query: {query[:50]}...")
            return tool_names
        except Exception as e:
            logger.error(f"Tool retrieval failed from ChromaDB: {e}")
            # Instead of failing, return empty to allow agent to proceed with default tools
            return []
