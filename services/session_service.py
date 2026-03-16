import time
from typing import Dict, List, Optional
from db.db_pool import get_db_pool
from loguru import logger
from config.config import CFG
import sqlite3

class SessionService:
    def __init__(self):
        pass

    async def _get_conn(self):
        pool = await get_db_pool()
        return pool.get_db()

    async def get_session_for_sender(self, sender_id: str) -> Dict:
        """
        Resolves a sender_id (e.g. telegram_123, email@abc.com) to a unified session record.
        """
        # 1. Check if sender_id is already linked to a session
        query = """
            SELECT s.session_id, s.name, s.created_at
            FROM sessions s
            JOIN session_links sl ON s.session_id = sl.session_id
            WHERE sl.identifier = ?
        """
        async with await self._get_conn() as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query, (sender_id,)) as cursor:
                session = await cursor.fetchone()
                if session:
                    return dict(session)
            
            # 2. Check if this is the Master
            # Try to fetch master profile from users table
            user_query = "SELECT email, telegram_chat_id, name FROM users WHERE user_id = 'master'"
            async with db.execute(user_query) as cursor:
                master_profile = await cursor.fetchone()
            
            master_email = master_profile["email"] if master_profile else CFG.USER_EMAIL
            master_tg_id = master_profile["telegram_chat_id"] if master_profile else None
            
            is_master = (sender_id == "os_user" or 
                         (master_email and sender_id == master_email) or 
                         (master_tg_id and sender_id == f"telegram_{master_tg_id}"))
                
            if is_master:
                session_id = "master"
                name = master_profile["name"] if master_profile else "Master"
            else:
                # 3. Handle Guest/New Session
                # Try to find if this identifier was previously registered as a guest profile
                tg_id_clean = sender_id.replace("telegram_", "") if sender_id.startswith("telegram_") else "???"
                guest_query = "SELECT user_id, name FROM users WHERE email = ? OR telegram_chat_id = ?"
                async with db.execute(guest_query, (sender_id, tg_id_clean)) as cursor:
                    guest_profile = await cursor.fetchone()
                
                session_id = guest_profile["user_id"] if guest_profile else f"session_{sender_id}"
                name = guest_profile["name"] if guest_profile else "Guest"

            # 4. Upsert session record
            await db.execute("""
                INSERT INTO sessions (session_id, name, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET name = excluded.name
            """, (session_id, name, time.time()))
            
            # 5. Link identifier
            await db.execute("""
                INSERT OR IGNORE INTO session_links (session_id, identifier)
                VALUES (?, ?)
            """, (session_id, sender_id))
            
            await db.commit()
            
            # Return final session
            async with db.execute("SELECT session_id, name, created_at FROM sessions WHERE session_id = ?", (session_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row)

    async def list_sessions(self) -> List[Dict]:
        """Fetch all unified sessions."""
        query = "SELECT session_id, name, created_at FROM sessions"
        async with await self._get_conn() as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def link_identifier(self, session_id: str, identifier: str) -> bool:
        """Manually link an identifier to a session."""
        async with await self._get_conn() as db:
            # Ensure identifier is not linked elsewhere (SQLite doesn't have multi-table update pull, so we delete)
            await db.execute("DELETE FROM session_links WHERE identifier = ?", (identifier,))
            
            await db.execute("""
                INSERT OR REPLACE INTO session_links (session_id, identifier)
                VALUES (?, ?)
            """, (session_id, identifier))
            await db.commit()
            return True

session_service = SessionService()
