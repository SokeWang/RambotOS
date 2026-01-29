import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.memory import MemoryManager
from loguru import logger

def test_weaviate():
    try:
        logger.info("Starting Weaviate test...")
        # Override collection name for test
        mm = MemoryManager(collection_name="TestCollection")
        logger.info("Weaviate initialized.")
        
        # Test add
        mm.add_memory("tester", "This is a test memory.")
        logger.info("Added test memory.")
        
        # Test retrieve
        results = mm.retrieve_memories("test", k=1)
        logger.info(f"Retrieved: {results}")
        
        if len(results) > 0:
            logger.info("Verification SUCCESS.")
        else:
            logger.error("Verification FAILED: No results retrieved.")
            
    except Exception as e:
        logger.error(f"Verification FAILED with error: {e}")

if __name__ == "__main__":
    test_weaviate()
