from db.db_pool import get_db_pool
import time
from typing import List, Dict, Any
from loguru import logger
import json
import sqlite3

class ToolRetrievalLogger:
    """
    Logger for tool retrieval/selection data.
    Records inputs and outputs for future deep learning model training.
    """
    
    def __init__(self):
        pass

    async def _get_conn(self):
        pool = await get_db_pool()
        return pool.get_db()

    async def log_retrieval(
        self,
        query: str,
        all_tool_names: List[str],
        selected_tool_names: List[str],
        retrieval_scores: Dict[str, float] = None
    ) -> None:
        """
        Log a tool retrieval/selection event.
        """
        try:
            sql = """
                INSERT INTO tool_retrievals (
                    timestamp, query, all_tools, selected_tools, 
                    num_all_tools, num_selected_tools, retrieval_scores
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            all_tools_json = json.dumps(all_tool_names, ensure_ascii=False)
            selected_tools_json = json.dumps(selected_tool_names, ensure_ascii=False)
            retrieval_scores_json = json.dumps(retrieval_scores or {}, ensure_ascii=False)
            
            async with await self._get_conn() as db:
                await db.execute(sql, (
                    time.time(), query, all_tools_json, selected_tools_json,
                    len(all_tool_names), len(selected_tool_names), retrieval_scores_json
                ))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log tool retrieval: {e}")
    
    async def get_training_data(
        self,
        limit: int = None,
        start_time: float = None,
        end_time: float = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logged retrievals for model training.
        """
        query = "SELECT timestamp, query, all_tools, selected_tools, num_all_tools, num_selected_tools, retrieval_scores FROM tool_retrievals"
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
                    record["all_tools"] = json.loads(record["all_tools"])
                    record["selected_tools"] = json.loads(record["selected_tools"])
                    record["retrieval_scores"] = json.loads(record["retrieval_scores"])
                    results.append(record)
                return results
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about logged retrievals.
        """
        async with await self._get_conn() as db:
            # Get total count
            async with db.execute("SELECT COUNT(*) FROM tool_retrievals") as cursor:
                total_count = (await cursor.fetchone())[0]
            
            if total_count == 0:
                return {
                    "total_retrievals": 0,
                    "avg_tools_selected": 0,
                    "avg_selection_rate": 0
                }
            
            # Aggregate statistics
            async with db.execute("SELECT AVG(num_selected_tools), AVG(num_all_tools) FROM tool_retrievals") as cursor:
                avg_selected, avg_total = await cursor.fetchone()
            
            selection_rate = (avg_selected / avg_total * 100) if avg_total > 0 else 0
            
            stats = {
                "total_retrievals": total_count,
                "avg_tools_selected": round(avg_selected, 2),
                "avg_selection_rate": round(selection_rate, 2)
            }
            return stats
    
    async def export_for_training(self, output_file: str = "tool_retrieval_training_data.json") -> None:
        """
        Export all data to a JSON file for model training.
        """
        data = await self.get_training_data()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(data)} records to {output_file}")


async def test():
    # Test the logger
    logger_instance = ToolRetrievalLogger()
    
    # Log a test retrieval
    await logger_instance.log_retrieval(
        query="calculate the square root of 16",
        all_tool_names=["math_tool", "weather_tool", "search_tool", "file_tool"],
        selected_tool_names=["math_tool"],
        retrieval_scores={"math_tool": 0.95, "search_tool": 0.3}
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
