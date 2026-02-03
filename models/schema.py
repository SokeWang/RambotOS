from pydantic import BaseModel, Field
from typing import Optional, Literal

class AIResponse(BaseModel):
    reply: str = Field(description="The reply to the user's message.")
    save_to_long_term_memory: bool = Field(default=False, description="Whether this interaction (user query and your reply) should be saved to long-term memory. Only set this for meaningful information, preferences, or facts about the user.")
    need_ui: bool = Field(default=False, description="Specifically for Email Agent: Whether a critical decision is needed from the user.")

class RequireWebcam(BaseModel):
    require_webcam: bool = Field(default=False, strict=True,description="Whether the user requires webcam")

class CoderResponse(BaseModel):
    tool_name: str = Field(description="The name of the tool.")
    py_code: str = Field(description="The Python code of the tool.")
    dependencies: list = Field(description="The dependencies of the tool.")
    function_name: str = Field(description="The name of the main function.")
    test_args: dict = Field(description="The test arguments for the main function.")

class IntentResponse(BaseModel):
    refined_query: str = Field(description="The refined, context-aware query for search.")
    need_long_term_memory: bool = Field(description="Whether the query requires long-term memory retrieval (e.g., personal facts, past events).")
    require_webcam: bool = Field(default=False, description="Whether the current request requires visual context from the webcam (e.g., asking about things in view, objects, etc.)")
    