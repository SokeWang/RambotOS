from langchain_core.tools import BaseTool
from typing import Any, Dict
from core.memory import memory_manager

class SearchMemoryTool(BaseTool):
    """
    Search your long-term memory for personal facts and knowledge about the user.
    """
    name: str = "search_memory"
    description: str = "Search your long-term memory for personal facts and knowledge about the user."
    
    # Session ID still injected at initialization as it is per-agent
    session_id: str

    def _run(self, query: str) -> str:
        """Execute the search logic."""
        memories = memory_manager.retrieve_memories(query, session_id=self.session_id, k=10)
        
        if not memories:
            return "No relevant past knowledge found."
        
        res = "Relevant knowledge retrieved:\n"
        for m in memories:
            res += f"- {m['text']}\n"
        return res
