import aiosqlite
import sqlite3
from loguru import logger
from config.config import CFG
import os
import json

class SQLitePool:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    async def initialize(self):
        """Initialize the database and create tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            # User table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    telegram_chat_id TEXT UNIQUE,
                    name TEXT,
                    is_master BOOLEAN
                )
            """)
            
            # Sessions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at REAL
                )
            """)
            
            # Session links table (for linking multiple identifiers to one session)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS session_links (
                    session_id TEXT,
                    identifier TEXT UNIQUE,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Webcam decisions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS webcam_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    user_message TEXT,
                    context_messages TEXT,
                    decision BOOLEAN,
                    model_used TEXT
                )
            """)
            
            # Tool retrieval logs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tool_retrievals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    query TEXT,
                    all_tools TEXT,
                    selected_tools TEXT,
                    num_all_tools INTEGER,
                    num_selected_tools INTEGER,
                    retrieval_scores TEXT
                )
            """)
            
            await db.commit()
            logger.info(f"SQLite database initialized at {self.db_path}")

    def get_db(self):
        """Context manager for obtaining a database connection."""
        return aiosqlite.connect(self.db_path)

_pool = None

async def get_db_pool():
    global _pool
    if _pool is None:
        _pool = SQLitePool(CFG.SQLITE_DB_PATH)
        await _pool.initialize()
    return _pool
