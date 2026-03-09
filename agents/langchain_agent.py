from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import CFG
from core.history import History
from loguru import logger
from agents.tool_manager import tool_manager
from core.skill_index import skill_index
from langchain.agents import create_agent
from core.chat_prompt import build_system_prompt
from core.memory import MemoryManager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from models.schema import AIResponse, MemoryExtraction
import asyncio
import re
from collections import OrderedDict
from agents.base_agent import BaseAgent
from typing import Any, List, AsyncGenerator

class LangchainBrain(BaseAgent):
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model=CFG.chat_model,
            api_key=CFG.api_key,
            max_retries=10  # Integrated retry logic
        )

        self.histories: dict[str, History] = {}
        self.long_term_memory = MemoryManager()
        
        self._AGENT_CACHE_MAX = 100
        self.agent_managers: OrderedDict[str, Any] = OrderedDict()
        self._init_lock = asyncio.Lock()
        self._cached_prompt: dict[str, str] = {}

    def get_history(self, session_id: str) -> History:
        """Get or create History manager for a session."""
        if session_id not in self.histories:
            self.histories[session_id] = History(session_id=session_id)
        return self.histories[session_id]

    async def initialize(self):
        async with self._init_lock:
            if self.agent_managers:
                return
            
            logger.info("Initializing Agent Components...")
            
            # Initial discovery
            skill_index.initialize()

    def get_agent(self, session_id: str, skills: list = None) -> Any:
        """Get or create an Agent (LRU-bounded cache)."""
        skills_tuple = tuple(sorted(skills)) if skills else ()
        agent_key = f"{session_id}_{hash(skills_tuple)}"
        
        if agent_key in self.agent_managers:
            # Move to end to mark as recently used
            self.agent_managers.move_to_end(agent_key)
        else:
            logger.info(f"Creating Agent for session: {session_id}")
            all_tools = tool_manager.get_tools(session_id=session_id, skills=skills)
            self.agent_managers[agent_key] = create_agent(
                model=self.model,
                tools=all_tools,
                response_format=AIResponse
            )
            # Evict least-recently-used entry if over limit
            if len(self.agent_managers) > self._AGENT_CACHE_MAX:
                self.agent_managers.popitem(last=False)
        
        return self.agent_managers[agent_key]

    async def run(self, content: list, is_master: bool = True, session_id: str = "global", user_name: str = "User") -> AsyncGenerator[dict, None]:
        if not self.agent_managers:
            await self.initialize()

        # 1. Prepare history and messages
        raw_query = self._extract_raw_query(content)
        history_manager = self.get_history(session_id)
        await history_manager.add("user", content)
        raw_history = await history_manager.get()
        formatted_messages = self._prepare_messages(raw_history)
        
        # 2. Prepare environment
        skill_index.refresh_if_needed()
        system_prompt = self._get_cached_system_prompt(is_master=is_master, user_name=user_name)
        
        # 3. Execute agent loop with retries and streaming
        brain_response = None
        async for chunk in self._execute_agent_loop(session_id, system_prompt, formatted_messages):
            if isinstance(chunk, dict) and "brain_response" in chunk:
                brain_response = chunk["brain_response"]
            else:
                yield chunk

        if brain_response:
            # 4. Process response
            reply_text, tool_calls, gen_ui = self._process_response_content(brain_response)
            
            # 5. Yield final result
            yield {"reply": reply_text, "tool_calls": tool_calls, "gen_ui": gen_ui}

            # 6. Post-Processing
            await self._save_history_and_memory(session_id, history_manager, raw_query, reply_text, tool_calls, brain_response)

    def _prepare_messages(self, raw_history: list) -> list:
        """Converts raw history into LangChain message objects."""
        formatted_messages = []
        for msg in raw_history:
            role = msg.get("role", "user")
            content = msg.get("content", [])
            
            # LangChain HumanMessage handles dict-based multimodal content natively
            if role in ("ai", "assistant"):
                formatted_messages.append(AIMessage(content=content if isinstance(content, str) else str(content)))
            else:
                formatted_messages.append(HumanMessage(content=content))
        return formatted_messages

    async def _execute_agent_loop(self, session_id: str, system_prompt: str, formatted_messages: list):
        """Executes the agent loop with retry logic and yields progress updates."""
        internal_turns = []
        brain_response = None
        # Simplified loop: Model-level retries handle transient errors; high-level loop for tool execution
        try:
            current_agent = self.get_agent(session_id)
            current_messages = [SystemMessage(content=system_prompt)] + formatted_messages + internal_turns

            async for event in current_agent.astream_events(
                {"messages": current_messages},
                version="v2",
                config={"recursion_limit": CFG.recursion_limit}
            ):
                if not isinstance(event, dict): continue
                kind = event.get("event")
                
                if kind == "on_chat_model_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, AIMessage) and output.tool_calls:
                        internal_turns.append(output)
                
                elif kind == "on_tool_start":
                    if event.get("name") != "AIResponse":
                        yield {"reply": f"Processing with {event.get('name')}...", "tool_calls": [{"name": event.get("name"), "status": "running"}]}
                
                elif kind == "on_tool_end":
                    if event.get("name") != "AIResponse":
                        tool_output = event.get("data", {}).get("output", "")
                        call_id = event.get("data", {}).get("tool_call_id") or event.get("run_id")
                        internal_turns.append(ToolMessage(content=str(tool_output), tool_call_id=call_id))
                        yield {"reply": f"Finished {event.get('name')}.", "tool_calls": [{"name": event.get('name'), "status": "success", "output": str(tool_output)}]}
                
                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict) and "structured_response" in output:
                        brain_response = output
            
            if brain_response:
                yield {"brain_response": brain_response}
                
        except Exception as e:
            logger.error(f"Brain Agent execution failed: {e}")
            yield {"reply": f"Error: {e}", "tool_calls": []}

    def _process_response_content(self, brain_response: dict):
        """Extracts reply, tool calls, and GenUI content from brain_response."""
        sr = brain_response.get("structured_response")
        reply_text = getattr(sr, "reply", "")
        tool_calls = self._extract_tool_calls_from_response(brain_response)
        
        gen_ui = None
        if hasattr(sr, "gen_ui") and sr.gen_ui:
            if isinstance(sr.gen_ui, list):
                gen_ui = [c.model_dump() if hasattr(c, "model_dump") else c for c in sr.gen_ui]
            else:
                gen_ui = sr.gen_ui.model_dump() if hasattr(sr.gen_ui, "model_dump") else sr.gen_ui
        
        return reply_text, tool_calls, gen_ui

    async def _save_history_and_memory(self, session_id, history_manager, raw_query, reply_text, tool_calls, brain_response):
        """Saves interaction to history and potentially to long-term memory."""
        ai_content = [{"type": "text", "text": reply_text}]
        if tool_calls:
            import json
            ai_content.append({"type": "text", "text": f"__TOOL_CALLS_METADATA__: {json.dumps(tool_calls)}"})
            
        await history_manager.add("ai", ai_content)

        if brain_response["structured_response"].save_to_long_term_memory:
            asyncio.create_task(self._extract_knowledge(raw_query, reply_text, session_id))

    async def _extract_knowledge(self, user_query: str, ai_reply: str, session_id: str):
        """
        Autonomous extraction of facts from a specific interaction.
        Uses structured output directly (no agent overhead needed).
        """
        
        extraction_prompt = f"Extract meaningful facts about the user from this interaction:\nUser: {user_query}\nAI: {ai_reply}"
        
        try:
            # Direct structured output call — no agent/tool overhead needed
            structured_model = self.model.with_structured_output(MemoryExtraction)
            extracted = await structured_model.ainvoke([HumanMessage(content=extraction_prompt)])
            
            if extracted and hasattr(extracted, "facts"):
                for fact in extracted.facts:
                    self.long_term_memory.add_fact(fact.dict(), session_id=session_id)
        except Exception as e:
            logger.error(f"Knowledge extraction failed: {e}")

    def _extract_tool_calls_from_response(self, brain_response: dict) -> list:
        """Extract tool calls and results from messages in the response."""
        extracted = []
        messages = brain_response.get("messages", [])
        # Tool calls usually come in pairs: AIMessage (call) followed by ToolMessage (result)
        for i, msg in enumerate(messages):
            # Check for tool calls in message attributes (LangChain style)
            tool_calls = getattr(msg, "tool_calls", [])
            if tool_calls:
                for tc in tool_calls:
                    if tc.get("name") == "AIResponse":
                        continue
                        
                    call_id = tc.get("id")
                    tc_record = {
                        "name": tc.get("name"),
                        "input": str(tc.get("args", "")),
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
            if isinstance(item, dict) and item.get("type") == "text": return item["text"]
            if hasattr(item, "text"): return item.text
        return str(content)
    
    def _get_cached_system_prompt(self, is_master: bool = True, user_name: str = "User") -> str:
        """
        Build optimized system prompt dynamically based on context.
        Master prompt is cached after first build; guest prompt is not cached (varies by user_name).
        """
        if not is_master:
            from core.chat_prompt import Email_Replier_Prompt
            return f"The current user is: {user_name}.\n\n" + Email_Replier_Prompt

        if "master" not in self._cached_prompt:
            self._cached_prompt["master"] = build_system_prompt(
                has_skills=True,  # Always include skill protocol to enforce discovery
                has_memory=True,
                extended=True
            )
        return self._cached_prompt["master"]
