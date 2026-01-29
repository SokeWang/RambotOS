from langchain.agents import create_agent
from models.schema import AIResponse
from loguru import logger

class BrainAgent:
    def __init__(self, model, tools):
        self.model = model
        self.tools = tools
        
        # Create the agent with the provided tools
        # No more middleware here, we handle logic explicitly in the run loop
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            response_format=AIResponse
        )

    async def ainvoke(self, input_dict):
        """Simple wrapper for agent invocation."""
        return await self.agent.ainvoke(input_dict)
