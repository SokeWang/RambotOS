import pymongo
from loguru import logger

class MongoPool:
    def __init__(self):
        try:
            # Assuming default local MongoDB
            self.client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
            # Verify connection
            self.client.server_info()
            self.db = self.client["rambot_history"]
            logger.info("MongoDB Connection Pool initialized.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Fallback to a mock or just let it fail later
            self.client = None
            self.db = None

    def get_collection(self, name):
        if self.db is not None:
            return self.db[name]
        return None

_pool = None

def get_mongo_pool():
    global _pool
    if _pool is None:
        _pool = MongoPool()
    return _pool
