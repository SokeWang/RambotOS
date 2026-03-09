from typing import List, Dict, Optional
from db.db_pool import get_mongo_pool
from loguru import logger
from fastapi import HTTPException

class UserService:
    def __init__(self):
        self.db_pool = get_mongo_pool()
        self.collection = self.db_pool.get_async_collection("users")

    async def get_user_profile(self, user_id: str) -> Dict:
        """Fetch a specific user profile."""
        query = {
            "$or": [
                {"user_id": user_id}, 
                {"email": user_id}, 
                {"telegram_chat_id": user_id.replace("telegram_", "")}
            ]
        }
        user = await self.collection.find_one(query, {"_id": 0})
        if not user:
            return None
        
        user["is_master"] = (user.get("user_id") == "master")
        return user

    async def bind_user(self, user_id: str, profile_data: Dict) -> bool:
        """Create or update a user profile."""
        try:
            await self.collection.update_one(
                {"user_id": user_id},
                {"$set": profile_data},
                upsert=True
            )
            logger.info(f"UserService: User {user_id} updated.")
            return True
        except Exception as e:
            logger.error(f"UserService: Failed to bind user {user_id}: {e}")
            return False

    async def list_guests(self) -> List[Dict]:
        """Fetch all guest profiles."""
        cursor = self.collection.find({"user_id": {"$ne": "master"}}, {"_id": 0})
        return await cursor.to_list(length=100)

user_service = UserService()
