from langchain.agents import create_agent
from models.schema import DesignerResponse

class DesignerAgent:
    def __init__(self, model):
        self.model = model

    def get_agent(self):
        return create_agent(
            model=self.model,
            response_format=DesignerResponse
        )
