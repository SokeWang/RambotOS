from db.db_pool import get_mongo_pool
import time
from typing import List, Dict, Any
from loguru import logger


class WebcamDecisionLogger:
    """
    Logger for webcam decision-making data.
    Records inputs and outputs for future deep learning model training.
    """
    
    def __init__(self):
        # 使用连接池
        self.pool = get_mongo_pool()
        self.collection = self.pool.get_collection("webcam_decisions")
        
        # Create index on timestamp for efficient querying
        self.collection.create_index("timestamp")
    
    def log_decision(
        self,
        user_message: str,
        context_messages: List[Dict[str, Any]],
        decision: bool,
        model_used: str
    ) -> None:
        """
        Log a webcam decision with all relevant context.
        
        Args:
            user_message: The current user input
            context_messages: Previous messages for context (list of dicts with role/content)
            decision: True if webcam is needed, False otherwise
            model_used: Name of the model used for decision
        """
        record = {
            "timestamp": time.time(),
            "user_message": user_message,
            "context_messages": context_messages,
            "decision": decision,
            "model_used": model_used
        }
        
        try:
            self.collection.insert_one(record)
        except Exception as e:
            logger.error(f"Failed to log webcam decision: {e}")
    
    def get_training_data(
        self,
        limit: int = None,
        start_time: float = None,
        end_time: float = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logged decisions for model training.
        
        Args:
            limit: Maximum number of records to return
            start_time: Unix timestamp to start from
            end_time: Unix timestamp to end at
            
        Returns:
            List of decision records
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
        Get statistics about logged decisions.
        
        Returns:
            Dictionary with statistics
        """
        total_count = self.collection.count_documents({})
        webcam_needed_count = self.collection.count_documents({"decision": True})
        webcam_not_needed_count = self.collection.count_documents({"decision": False})
        
        stats = {
            "total_decisions": total_count,
            "webcam_needed": webcam_needed_count,
            "webcam_not_needed": webcam_not_needed_count,
            "webcam_needed_percentage": (webcam_needed_count / total_count * 100) if total_count > 0 else 0
        }
        
        return stats
    
    def export_for_training(self, output_file: str = "webcam_training_data.json") -> None:
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
    logger_instance = WebcamDecisionLogger()
    
    # Log a test decision
    logger_instance.log_decision(
        user_message="what can you see?",
        context_messages=[
            {"role": "user", "content": "hello"},
            {"role": "ai", "content": "Hi! How can I help you?"}
        ],
        decision=True,
        model_used="gemini-3-flash-preview"
    )
    
    # Get statistics
    stats = logger_instance.get_statistics()
    print(f"Statistics: {stats}")
    
    # Get training data
    data = logger_instance.get_training_data(limit=10)
    print(f"Retrieved {len(data)} records")
