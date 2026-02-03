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
        cursor = self.collection.find({}, {"_id": 1, "role": 1, "content": 1, "time": 1}).sort("time", 1)
        raw_messages = list(cursor)[-limit:]
        
        sanitized_messages = []
        for msg in raw_messages:
            content = msg.get("content")
            if isinstance(content, list):
                # Filter out unrecognized message part types like 'tool_calls'
                original_len = len(content)
                new_content = [part for part in content if part.get("type") in ("text", "image_url", "image")]
                
                if len(new_content) != original_len:
                    # Fix the data in DB if corruption found
                    self.collection.update_one({"_id": msg["_id"]}, {"$set": {"content": new_content}})
                content = new_content
            
            sanitized_msg = {"role": msg["role"], "content": content}
            if with_time:
                sanitized_msg["time"] = msg.get("time")
            sanitized_messages.append(sanitized_msg)
            
        return sanitized_messages