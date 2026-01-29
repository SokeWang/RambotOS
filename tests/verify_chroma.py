import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.memory import MemoryManager
from loguru import logger

def test_chroma():
    try:
        logger.info("Starting ChromaDB test...")
        # Initialize MemoryManager (will use long_term_memory by default)
        mm = MemoryManager(collection_name="test_collection")
        logger.info("ChromaDB initialized.")
        
        # Test add
        test_content = f"This is a test memory created at {os.getpid()}"
        mm.add_memory("tester", test_content)
        logger.info("Added test memory.")
        
        # Test retrieve
        results = mm.retrieve_memories("test memory", k=1)
        logger.info(f"Retrieved: {results}")
        
        if len(results) > 0 and results[0]['content'] == test_content:
            logger.info("Verification SUCCESS: ChromaDB is working correctly.")
        else:
            logger.error("Verification FAILED: Results mismatch or empty.")
            
    except Exception as e:
        logger.error(f"Verification FAILED with error: {e}")

if __name__ == "__main__":
    test_chroma()
