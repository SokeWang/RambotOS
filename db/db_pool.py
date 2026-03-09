import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

class MongoPool:
    def __init__(self):
        self.uri = "mongodb://localhost:27017/"
        try:
            # Legacy Sync Client
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=2000)
            self.client.server_info()
            self.db = self.client["rambot_history"]
            
            # Async Motor Client
            self.async_client = AsyncIOMotorClient(self.uri)
            self.async_db = self.async_client["rambot_history"]
            
            logger.info("MongoDB Connection Pool (Sync + Async) initialized.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
            self.async_client = None
            self.async_db = None

    def get_collection(self, name):
        if self.db is not None:
            return self.db[name]
        return None

    def get_async_collection(self, name):
        if self.async_db is not None:
            return self.async_db[name]
        return None

_pool = None

def get_mongo_pool():
    global _pool
    if _pool is None:
        _pool = MongoPool()
    return _pool
