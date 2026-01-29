from db.db_pool import get_mongo_pool
import time

class History:
    def __init__(self):
        # 使用连接池而不是直接创建连接
        self.pool = get_mongo_pool()
        self.collection = self.pool.get_collection("history")

    def add(self, role, content):
        self.collection.insert_one({"role": role, "content": content, "time": time.time()})

    def get(self, limit=20, with_time=False):
        if with_time:
            return [message for message in self.collection.find({}, {"_id": 0, "role": 1, "content": 1, "time": 1}).sort("time", 1)][-limit:]
        else:
            return [message for message in self.collection.find({}, {"_id": 0, "role": 1, "content": 1}).sort("time", 1)][-limit:]