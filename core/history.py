from db.db_pool import get_mongo_pool
import time

class History:
    def __init__(self, session_id="global"):
        self.pool = get_mongo_pool()
        self.collection = self.pool.get_async_collection("history")
        self.session_id = session_id

    async def add(self, role, content):
        await self.collection.insert_one({
            "session_id": self.session_id,
            "role": role, 
            "content": content, 
            "time": time.time()
        })

    async def get(self, limit=20, skip=0, with_time=False):
        query = {"session_id": self.session_id}
        
        cursor = self.collection.find(query, {"_id": 1, "role": 1, "content": 1, "time": 1, "session_id": 1}).sort("time", -1).skip(skip)
        raw_messages = await cursor.to_list(length=limit)
        # Reverse to restore chronological order
        raw_messages.reverse()
        
        sanitized_messages = []
        for msg in raw_messages:
            content = msg.get("content")
            if isinstance(content, list):
                original_len = len(content)
                new_content = [part for part in content if part.get("type") in ("text", "image_url", "image")]
                
                if len(new_content) != original_len:
                    await self.collection.update_one({"_id": msg["_id"]}, {"$set": {"content": new_content}})
                content = new_content
            
            sanitized_msg = {"role": msg["role"], "content": content}
            if with_time:
                sanitized_msg["time"] = msg.get("time")
            sanitized_messages.append(sanitized_msg)
            
        return sanitized_messages