from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import CFG
from core.history import History
from loguru import logger
from agents.brain import BrainAgent
from tools.tool_manager import tool_manager
from tools.skill_index import skill_index
from core.chat_prompt import build_system_prompt  # Updated import
from core.memory import MemoryManager
import asyncio
import re

class UltronBrain:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model=CFG.chat_model,
            api_key=CFG.api_key
        )

        self.short_memory_manager = History()
        self.long_term_memory = MemoryManager()
        
        self.brain_manager = None
        self._init_lock = asyncio.Lock()
        
        # Skill management
        self._current_skills = set()  # Skills loaded in current session
        self._last_tool_signature = None
        self._cached_tools = None
        self._cached_prompt = None

    async def initialize(self):
        async with self._init_lock:
            if self.brain_manager:
                return
            
            logger.info("Initializing Agent Components (Explicit Architecture)...")
            
            # Initialize ToolManager and perform first discovery
            await tool_manager.initialize()
            
            # Initialize SkillIndex
            skill_index.initialize()
            
            # Create initial brain_manager with base tools only
            initial_tools = self._get_base_tool_set()
            self.brain_manager = BrainAgent(self.model, initial_tools)
            self._last_tool_signature = self._get_tool_signature(initial_tools)
            
            logger.info("Agent Components initialized successfully.")

    async def run(self, content: list):
        if not self.brain_manager:
            await self.initialize()

        # 1. Extract raw query and check for media
        raw_query = self._extract_raw_query(content)
        has_image = any(isinstance(item, dict) and item.get("type") == "image_url" and item.get("media_source") == "attachment" for item in content)
        has_webcam = any(isinstance(item, dict) and item.get("type") == "image_url" and item.get("media_source") == "webcam" for item in content)
        
        # 2. Add to short term history
        self.short_memory_manager.add("user", content)
        raw_history = self.short_memory_manager.get()
        
        # Sanitize messages aggressively: remove unrecognized types
        messages = []
        for msg in raw_history:
            role = msg.get("role", "user")
            content_val = msg.get("content", [])
            
            if isinstance(content_val, list):
                # Filter to only keep supported types
                sanitized_content = [
                    part for part in content_val 
                    if isinstance(part, dict) and part.get("type") in ("text", "image_url", "image")
                ]
                messages.append({"role": role, "content": sanitized_content})
            elif isinstance(content_val, str):
                messages.append({"role": role, "content": [{"type": "text", "text": content_val}]})
            else:
                messages.append({"role": role, "content": []})
        
        # 3. Use raw query as refined query
        refined_query = raw_query
        
        # 4. Refresh skill index if needed
        skill_index.refresh_if_needed()
        
        # 5. Build system prompt with cached skills summary
        extended_system_prompt = self._get_cached_system_prompt()
        
        brain_response = None
        reply_text = ""
        max_retries = 2  # Allow one agent rebuild
        retry_count = 0

        while retry_count < max_retries:
            try:
                brain_response = await self.brain_manager.ainvoke(
                    {"messages": [{"role": "system", "content": extended_system_prompt}] + messages}
                )
                reply_text = brain_response["structured_response"].reply
                
                # Check if agent requested skill reload
                if self._should_reload_skills(reply_text):
                    new_skills = self._extract_skills_from_response(reply_text)
                    if new_skills:
                        logger.info(f"Agent requested skills: {new_skills}")
                        self._rebuild_agent_with_skills(new_skills)
                        retry_count += 1
                        # Clean up the RELOAD_AGENT marker from reply
                        reply_text = "Loading relevant skills..."
                        continue
                
                # Success - break the loop
                break
                
            except Exception as e:
                error_str = str(e)
                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    logger.warning(f"Gemini API Quota Exceeded (429): {error_str}")
                    
                    # Try to extract retry delay (e.g., "Please retry in 25.795275017s.")
                    retry_wait = 30  # Default wait
                    match = re.search(r"retry in (\d+\.?\d*)s", error_str)
                    if match:
                        retry_wait = float(match.group(1)) + 1  # Add a 1s buffer
                    
                    logger.info(f"Waiting {retry_wait:.2f}s before retrying...")
                    await asyncio.sleep(retry_wait)
                    continue  # Retry same loop iteration
                
                logger.error(f"Brain Agent failed: {e}")
                reply_text = f"I encountered an error while processing your request: {e}."
                break

        extracted_tool_calls = self._extract_tool_calls_from_response(brain_response)
        yield {"reply": reply_text, "tool_calls": extracted_tool_calls}

        # 6. Explicit Step: Memory Storage (Post-call)
        if brain_response and brain_response["structured_response"].save_to_long_term_memory:
            logger.info("AI Decision: Saving interaction to long-term memory...")
            self.long_term_memory.add_memory("user", refined_query)
            self.long_term_memory.add_memory("assistant", reply_text)

        ai_content = [{"type": "text", "text": reply_text}]
        if extracted_tool_calls:
            # We use a special prefix so the frontend can identify tool calls from history,
            # but keep it as type 'text' to avoid 'Unrecognized message part type' error in LangChain.
            import json
            metadata = f"__TOOL_CALLS_METADATA__: {json.dumps(extracted_tool_calls)}"
            ai_content.append({"type": "text", "text": metadata})
            
        self.short_memory_manager.add("ai", ai_content)

    def _extract_tool_calls_from_response(self, brain_response: dict) -> list:
        """Extract tool calls and results from messages in the response."""
        extracted = []
        if not brain_response or "messages" not in brain_response:
            return extracted
            
        messages = brain_response["messages"]
        # Tool calls usually come in pairs: AIMessage (call) followed by ToolMessage (result)
        for i, msg in enumerate(messages):
            # Check for tool calls in message attributes (LangChain style)
            tool_calls = getattr(msg, "tool_calls", [])
            if tool_calls:
                for tc in tool_calls:
                    call_id = tc.get("id")
                    tool_name = tc.get("name", "Tool")
                    tool_input = str(tc.get("args", ""))
                    
                    tc_record = {
                        "name": tool_name,
                        "input": tool_input,
                        "status": "success",
                        "output": ""
                    }
                    
                    # Look for corresponding ToolMessage in subsequent messages
                    if call_id:
                        for next_msg in messages[i+1:]:
                            if getattr(next_msg, "tool_call_id", None) == call_id:
                                tc_record["output"] = str(getattr(next_msg, "content", ""))
                                break
                    
                    extracted.append(tc_record)
        return extracted

    def _extract_raw_query(self, content: list) -> str:
        """Extracts text from message content list."""
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return item["text"]
            if hasattr(item, "text"):
                return item.text
        return str(content)
    
    def _get_base_tool_set(self):
        """Get base tools that are always available"""
        base_tools = tool_manager.get_base_tools()
        base_tools.append(self.long_term_memory.get_tool())
        base_tools.append(skill_index.get_retrieve_tool())
        return base_tools
    
    def _get_tool_signature(self, tools):
        """Generate signature for tool set"""
        return hash(tuple(sorted(t.name for t in tools)))
    
    def _get_cached_system_prompt(self) -> str:
        """
        Build optimized system prompt dynamically based on context.
        Only includes relevant sections to reduce token usage.
        """
        has_skills = len(self._current_skills) > 0
        skills_summary = skill_index.get_all_skills_summary() if has_skills else ""
        
        # Build optimized prompt (30-40% fewer tokens than before)
        prompt = build_system_prompt(
            has_skills=has_skills,
            has_memory=True,  # Memory tools always available
            extended=False,  # Only use extended for complex scenarios
            skills_summary=skills_summary
        )
        
        logger.debug(f"Built prompt with {len(prompt.split())} words (skills: {has_skills})")
        return prompt
    
    def _should_reload_skills(self, reply_text: str) -> bool:
        """Check if agent requested skill reload"""
        return "RELOAD_AGENT:" in reply_text
    
    def _extract_skills_from_response(self, reply_text: str) -> list:
        """Extract skill names from RELOAD_AGENT marker"""
        try:
            marker = "RELOAD_AGENT:"
            if marker in reply_text:
                skills_str = reply_text.split(marker)[1].split()[0]  # Get first word after marker
                skills = [s.strip() for s in skills_str.split(",")]
                return skills
        except Exception as e:
            logger.error(f"Failed to extract skills from response: {e}")
        return []
    
    def _rebuild_agent_with_skills(self, new_skills: list):
        """Rebuild agent with additional skills"""
        self._current_skills.update(new_skills)
        
        # Build complete tool set
        base_tools = self._get_base_tool_set()
        skill_tools = tool_manager.get_tools_for_skills(list(self._current_skills))
        all_tools = base_tools + skill_tools
        
        # Rebuild agent
        self.brain_manager = BrainAgent(self.model, all_tools)
        self._last_tool_signature = self._get_tool_signature(all_tools)
        
        # Invalidate prompt cache (prompt will be rebuilt with new skills)
        self._cached_prompt = None
        
        logger.info(f"Agent rebuilt with {len(all_tools)} tools (skills: {self._current_skills})")
