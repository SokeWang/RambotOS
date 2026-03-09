import time
from typing import Dict, List, Optional
from db.db_pool import get_mongo_pool
from loguru import logger
from config.config import CFG

class SessionService:
    def __init__(self):
        self.db_pool = get_mongo_pool()
        self.session_col = self.db_pool.get_async_collection("sessions")
        self.user_col = self.db_pool.get_async_collection("users")

    async def get_session_for_sender(self, sender_id: str) -> Dict:
        """
        Resolves a sender_id (e.g. telegram_123, email@abc.com) to a unified session record.
        """
        # 1. Check if sender_id is already linked to a session
        session = await self.session_col.find_one({"linked_ids": sender_id}, {"_id": 0})
        if session:
            return session
            
        # 2. Check if this is the Master
        master_profile = await self.user_col.find_one({"user_id": "master"})
        master_email = master_profile.get("email") if master_profile else CFG.USER_EMAIL
        master_tg_id = master_profile.get("telegram_chat_id") if master_profile else None
        
        is_master = (sender_id == "os_user" or 
                     (master_email and sender_id == master_email) or 
                     (master_tg_id and sender_id == f"telegram_{master_tg_id}"))
            
        if is_master:
            session_id = "master"
            name = master_profile.get("name", "Master") if master_profile else "Master"
        else:
            # 3. Handle Guest/New Session
            # Try to find if this identifier was previously registered as a guest profile
            tg_id_clean = sender_id.replace("telegram_", "") if sender_id.startswith("telegram_") else "???"
            guest_profile = await self.user_col.find_one({
                "$or": [{"email": sender_id}, {"telegram_chat_id": tg_id_clean}]
            })
            
            session_id = guest_profile.get("user_id") if guest_profile else f"session_{sender_id}"
            name = guest_profile.get("name", "Guest") if guest_profile else "Guest"

        # Upsert session record
        await self.session_col.update_one(
            {"session_id": session_id},
            {
                "$set": {"name": name}, 
                "$addToSet": {"linked_ids": sender_id}, 
                "$setOnInsert": {"created_at": time.time()}
            },
            upsert=True
        )
        return await self.session_col.find_one({"session_id": session_id}, {"_id": 0})

    async def list_sessions(self) -> List[Dict]:
        """Fetch all unified sessions."""
        cursor = self.session_col.find({}, {"_id": 0})
        return await cursor.to_list(length=100)

    async def link_identifier(self, session_id: str, identifier: str) -> bool:
        """Manually link an identifier to a session."""
        # Ensure identifier is not linked elsewhere
        await self.session_col.update_many({"linked_ids": identifier}, {"$pull": {"linked_ids": identifier}})
        
        result = await self.session_col.update_one(
            {"session_id": session_id},
            {"$addToSet": {"linked_ids": identifier}}
        )
        return result.matched_count > 0

session_service = SessionService()
