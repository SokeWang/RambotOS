from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional, Any

class BaseAgent(ABC):
    """
    Abstract base class for all agents in RambotOS.
    Ensures a consistent interface for different agent implementations.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Perform any necessary asynchronous initialization for the agent.
        """
        pass

    @abstractmethod
    async def run(
        self, 
        content: List[Any], 
        is_master: bool = True, 
        session_id: str = "global", 
        user_name: str = "User"
    ) -> AsyncGenerator[dict, None]:
        """
        Process user input and yield responses.
        
        Args:
            content: Multimodal input content.
            is_master: Whether the user is the master user.
            session_id: Unique session identifier.
            user_name: Name of the user.
            
        Yields:
            A dictionary containing the agent's response, tool calls, and GenUI content.
        """
        yield {}
