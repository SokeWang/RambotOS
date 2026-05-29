from typing import List, Dict, Optional
from db.db_pool import get_db_pool
from loguru import logger
from fastapi import HTTPException
import sqlite3

class UserService:
    def __init__(self):
        # We'll get the pool dynamically to handle the async initialization
        pass

    async def _get_conn(self):
        pool = await get_db_pool()
        return pool.get_db()

    async def get_user_profile(self, user_id: str) -> Dict:
        """Fetch a specific user profile."""
        query = """
            SELECT user_id, email, telegram_chat_id, name, is_master 
            FROM users 
            WHERE user_id = ? OR email = ? OR telegram_chat_id = ?
        """
        clean_tg_id = user_id.replace("telegram_", "")
        async with await self._get_conn() as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query, (user_id, user_id, clean_tg_id)) as cursor:
                user = await cursor.fetchone()
                if not user:
                    return None
                
                profile = dict(user)
                # Ensure is_master is boolean
                profile["is_master"] = bool(profile["is_master"]) or (profile.get("user_id") == "master")
                return profile

    async def bind_user(self, user_id: str, profile_data: Dict) -> bool:
        """Create or update a user profile."""
        try:
            email = profile_data.get("email")
            telegram_chat_id = profile_data.get("telegram_chat_id")
            name = profile_data.get("name")
            is_master = profile_data.get("is_master", False)

            query = """
                INSERT INTO users (user_id, email, telegram_chat_id, name, is_master)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    email = excluded.email,
                    telegram_chat_id = excluded.telegram_chat_id,
                    name = excluded.name,
                    is_master = excluded.is_master
            """
            async with await self._get_conn() as db:
                await db.execute(query, (user_id, email, telegram_chat_id, name, is_master))
                await db.commit()
            
            logger.info(f"UserService: User {user_id} updated.")
            return True
        except Exception as e:
            logger.error(f"UserService: Failed to bind user {user_id}: {e}")
            return False

    async def list_guests(self) -> List[Dict]:
        """Fetch all guest profiles."""
        query = "SELECT user_id, email, telegram_chat_id, name, is_master FROM users WHERE user_id != 'master'"
        async with await self._get_conn() as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

user_service = UserService()
