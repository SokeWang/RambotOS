from db.db_pool import get_mongo_pool
import time
from typing import List, Dict, Any
from loguru import logger


class ToolRetrievalLogger:
    """
    Logger for tool retrieval/selection data.
    Records inputs and outputs for future deep learning model training.
    """
    
    def __init__(self):
        # 使用连接池
        self.pool = get_mongo_pool()
        self.collection = self.pool.get_collection("tool_retrievals")
        
        # Create index on timestamp for efficient querying
        self.collection.create_index("timestamp")
    
    def log_retrieval(
        self,
        query: str,
        all_tool_names: List[str],
        selected_tool_names: List[str],
        retrieval_scores: Dict[str, float] = None
    ) -> None:
        """
        Log a tool retrieval/selection event.
        
        Args:
            query: The user query used for retrieval
            all_tool_names: List of all available tool names
            selected_tool_names: List of selected tool names
            retrieval_scores: Optional dict mapping tool names to similarity scores
        """
        record = {
            "timestamp": time.time(),
            "query": query,
            "all_tools": all_tool_names,
            "selected_tools": selected_tool_names,
            "num_all_tools": len(all_tool_names),
            "num_selected_tools": len(selected_tool_names),
            "retrieval_scores": retrieval_scores or {}
        }
        
        try:
            self.collection.insert_one(record)
        except Exception as e:
            logger.error(f"Failed to log tool retrieval: {e}")
    
    def get_training_data(
        self,
        limit: int = None,
        start_time: float = None,
        end_time: float = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logged retrievals for model training.
        
        Args:
            limit: Maximum number of records to return
            start_time: Unix timestamp to start from
            end_time: Unix timestamp to end at
            
        Returns:
            List of retrieval records
        """
        query = {}
        
        if start_time or end_time:
            query["timestamp"] = {}
            if start_time:
                query["timestamp"]["$gte"] = start_time
            if end_time:
                query["timestamp"]["$lte"] = end_time
        
        cursor = self.collection.find(query, {"_id": 0}).sort("timestamp", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about logged retrievals.
        
        Returns:
            Dictionary with statistics
        """
        total_count = self.collection.count_documents({})
        
        if total_count == 0:
            return {
                "total_retrievals": 0,
                "avg_tools_selected": 0,
                "avg_selection_rate": 0
            }
        
        # Aggregate statistics
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_selected": {"$avg": "$num_selected_tools"},
                    "avg_total": {"$avg": "$num_all_tools"}
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        
        if result:
            avg_selected = result[0]["avg_selected"]
            avg_total = result[0]["avg_total"]
            selection_rate = (avg_selected / avg_total * 100) if avg_total > 0 else 0
        else:
            avg_selected = 0
            selection_rate = 0
        
        stats = {
            "total_retrievals": total_count,
            "avg_tools_selected": round(avg_selected, 2),
            "avg_selection_rate": round(selection_rate, 2)
        }
        
        return stats
    
    def export_for_training(self, output_file: str = "tool_retrieval_training_data.json") -> None:
        """
        Export all data to a JSON file for model training.
        
        Args:
            output_file: Path to output JSON file
        """
        import json
        
        data = self.get_training_data()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(data)} records to {output_file}")


if __name__ == "__main__":
    # Test the logger
    logger_instance = ToolRetrievalLogger()
    
    # Log a test retrieval
    logger_instance.log_retrieval(
        query="calculate the square root of 16",
        all_tool_names=["math_tool", "weather_tool", "search_tool", "file_tool"],
        selected_tool_names=["math_tool"],
        retrieval_scores={"math_tool": 0.95, "search_tool": 0.3}
    )
    
    # Get statistics
    stats = logger_instance.get_statistics()
    print(f"Statistics: {stats}")
    
    # Get training data
    data = logger_instance.get_training_data(limit=10)
    print(f"Retrieved {len(data)} records")
