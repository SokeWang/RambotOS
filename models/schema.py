from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Any

class AIResponse(BaseModel):
    reply: str = Field(description="The reply to the user's message. Keep it very brief if generating UI.")
    # webcam_needed: bool = Field(False, description="Set strictly to True if the task fundamentally requires visual confirmation")
    tool_calls: Optional[List[dict]] = Field(None, description="Optional tool calls")
    gen_ui: Optional[Any] = Field(None, description="Optional UI component tree following the flat JSON-render spec (root + elements) for visual requests")
    save_to_long_term_memory: bool = Field(default=False, description="Whether this interaction (user query and your reply) should be saved to long-term memory. Only set this for meaningful information, preferences, or facts about the user.")

# class RequireWebcam(BaseModel):
#     require_webcam: bool = Field(default=False, strict=True,description="Whether the user requires webcam")

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

class MemoryFact(BaseModel):
    subject: str = Field(description="The main entity (e.g., 'User', 'Rambot', 'Bristol', 'Work')")
    predicate: str = Field(description="The relationship or attribute (e.g., 'lives in', 'prefers to be called', 'is a', 'location')")
    object: str = Field(description="The value or target entity (e.g., 'Bristol', 'Boss', 'Personal Assistant')")

class MemoryExtraction(BaseModel):
    facts: List[MemoryFact] = Field(description="A list of newly learned facts from this conversation snippet.")