from db.db_pool import get_db_pool
import time
from typing import List, Dict, Any
from loguru import logger
import json
import sqlite3

class WebcamDecisionLogger:
    """
    Logger for webcam decision-making data.
    Records inputs and outputs for future deep learning model training.
    """
    
    def __init__(self):
        pass

    async def _get_conn(self):
        pool = await get_db_pool()
        return pool.get_db()

    async def log_decision(
        self,
        user_message: str,
        context_messages: List[Dict[str, Any]],
        decision: bool,
        model_used: str
    ) -> None:
        """
        Log a webcam decision with all relevant context.
        """
        try:
            query = """
                INSERT INTO webcam_decisions (timestamp, user_message, context_messages, decision, model_used)
                VALUES (?, ?, ?, ?, ?)
            """
            context_json = json.dumps(context_messages, ensure_ascii=False)
            async with await self._get_conn() as db:
                await db.execute(query, (time.time(), user_message, context_json, decision, model_used))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log webcam decision: {e}")
    
    async def get_training_data(
        self,
        limit: int = None,
        start_time: float = None,
        end_time: float = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logged decisions for model training.
        """
        query = "SELECT timestamp, user_message, context_messages, decision, model_used FROM webcam_decisions"
        params = []
        where_clauses = []
        
        if start_time:
            where_clauses.append("timestamp >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("timestamp <= ?")
            params.append(end_time)
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY timestamp ASC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        async with await self._get_conn() as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    record = dict(row)
                    record["context_messages"] = json.loads(record["context_messages"])
                    record["decision"] = bool(record["decision"])
                    results.append(record)
                return results
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about logged decisions.
        """
        async with await self._get_conn() as db:
            async with db.execute("SELECT COUNT(*) FROM webcam_decisions") as cursor:
                total_count = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COUNT(*) FROM webcam_decisions WHERE decision = 1") as cursor:
                webcam_needed_count = (await cursor.fetchone())[0]
                
            webcam_not_needed_count = total_count - webcam_needed_count
            
            stats = {
                "total_decisions": total_count,
                "webcam_needed": webcam_needed_count,
                "webcam_not_needed": webcam_not_needed_count,
                "webcam_needed_percentage": (webcam_needed_count / total_count * 100) if total_count > 0 else 0
            }
            return stats
    
    async def export_for_training(self, output_file: str = "webcam_training_data.json") -> None:
        """
        Export all data to a JSON file for model training.
        """
        data = await self.get_training_data()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(data)} records to {output_file}")


async def test():
    # Test the logger
    logger_instance = WebcamDecisionLogger()
    
    # Log a test decision
    await logger_instance.log_decision(
        user_message="what can you see?",
        context_messages=[
            {"role": "user", "content": "hello"},
            {"role": "ai", "content": "Hi! How can I help you?"}
        ],
        decision=True,
        model_used="gemini-3-flash-preview"
    )
    
    # Get statistics
    stats = await logger_instance.get_statistics()
    print(f"Statistics: {stats}")
    
    # Get training data
    data = await logger_instance.get_training_data(limit=10)
    print(f"Retrieved {len(data)} records")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
