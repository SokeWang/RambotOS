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
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from services.media_processor import MediaProcessor

class LangchainBrain(BaseAgent):
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model=CFG.chat_model,
            api_key=CFG.api_key,
            max_retries=10  # Integrated retry logic
        )
            
        self.long_term_memory = MemoryManager()
        
        self.long_term_memory = MemoryManager()
        self._init_lock = asyncio.Lock()
        self._cached_prompt: dict[str, str] = {}
        self._cached_name: str = ""
        self.checkpointer = None
        self.checkpointer_context = None

    async def initialize(self):
        async with self._init_lock:
            if self.checkpointer:
                return
            
            logger.info("Initializing Agent Components...")
            self.checkpointer_context = AsyncSqliteSaver.from_conn_string(CFG.SQLITE_DB_PATH)
            self.checkpointer = await self.checkpointer_context.__aenter__()
            
            # Initial discovery
            skill_index.initialize()

    def _create_agent(self, session_id: str, skills: list = None) -> Any:
        """Creates a fresh Agent instance with current skills and prompt."""
        logger.info(f"Creating fresh Agent for session: {session_id}")
        all_tools = tool_manager.get_tools(session_id=session_id, skills=skills)
        system_prompt = self._get_cached_system_prompt(is_master=(session_id == "master"))
        
        return create_agent(
            model=self.model,
            tools=all_tools,
            system_prompt=system_prompt,
            response_format=AIResponse,
            checkpointer=self.checkpointer
        )

    async def run(self, content: list, is_master: bool = True, session_id: str = "global", user_name: str = "User") -> AsyncGenerator[dict, None]:
        if not self.checkpointer:
            await self.initialize()

        # 1. Prepare history and messages
        # We only need the latest user message to pass to the agent; 
        # previous history is already in the checkpointer.
        formatted_messages = [HumanMessage(content=content)]
        
        # 2. Prepare environment
        skill_index.refresh_if_needed()
        system_prompt = self._get_cached_system_prompt(is_master=is_master, user_name=user_name)
        
        # 3. Execute agent loop with retries and streaming
        brain_response = None
        current_turn_messages = []
        async for chunk in self._execute_agent_loop(session_id, system_prompt, formatted_messages):
            if isinstance(chunk, dict):
                if "brain_response" in chunk:
                    brain_response = chunk["brain_response"]
                if "internal_turns" in chunk:
                    current_turn_messages.extend(chunk["internal_turns"])
                    continue # Don't yield internal turns to UI
            
            yield chunk

        if brain_response:
            # 4. Process response
            # Only extract tool calls from messages generated in this run
            reply_text, gen_ui = self._process_response_content(brain_response)
            tool_calls = self._extract_tool_calls_from_response(current_turn_messages)
            
            # 5. Yield final result
            yield {"reply": reply_text, "tool_calls": tool_calls, "gen_ui": gen_ui}

            # 6. Post-Processing (Long-term memory only)
            if brain_response["structured_response"].save_to_long_term_memory:
                raw_query = MediaProcessor.summarize_input(content)
                asyncio.create_task(self._extract_knowledge(raw_query, reply_text, session_id))

    async def _execute_agent_loop(self, session_id: str, system_prompt: str, formatted_messages: list):
        """Executes the agent loop with retry logic and yields progress updates."""
        internal_turns = []
        brain_response = None
        try:
            current_agent = self._create_agent(session_id)

            async for event in current_agent.astream_events(
                {"messages": formatted_messages},
                version="v2",
                config={
                    "recursion_limit": CFG.recursion_limit,
                    "configurable": {"thread_id": session_id}
                }
            ):
                if not isinstance(event, dict): 
                    continue
                
                kind = event.get("event")
                
                if kind == "on_chat_model_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, AIMessage) and output.tool_calls:
                        internal_turns.append(output)
                
                elif kind == "on_tool_start":
                    if event.get("name") != "AIResponse":
                        current_tools = self._extract_tool_calls_from_response(internal_turns)
                        current_tools.append({"name": event.get("name"), "status": "running", "input": ""})
                        yield {"reply": f"Processing with {event.get('name')}...", "tool_calls": current_tools}
                
                elif kind == "on_tool_end":
                    if event.get("name") != "AIResponse":
                        tool_output = event.get("data", {}).get("output", "")
                        call_id = event.get("data", {}).get("tool_call_id") or event.get("run_id")
                        internal_turns.append(ToolMessage(content=str(tool_output), tool_call_id=call_id))
                        current_tools = self._extract_tool_calls_from_response(internal_turns)
                        yield {"reply": f"Finished {event.get('name')}.", "tool_calls": current_tools}
                
                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict) and "structured_response" in output:
                        brain_response = output
            
            if brain_response:
                yield {"brain_response": brain_response, "internal_turns": internal_turns}
                
        except Exception as e:
            logger.error(f"Brain Agent execution failed: {e}")
            yield {"reply": f"Error: {e}", "tool_calls": []}

    def _process_response_content(self, brain_response: dict):
        """Extracts reply and GenUI content from brain_response."""
        sr = brain_response.get("structured_response")
        reply_text = getattr(sr, "reply", "")
        
        gen_ui = None
        if hasattr(sr, "gen_ui") and sr.gen_ui:
            if isinstance(sr.gen_ui, list):
                gen_ui = [c.model_dump() if hasattr(c, "model_dump") else c for c in sr.gen_ui]
            else:
                gen_ui = sr.gen_ui.model_dump() if hasattr(sr.gen_ui, "model_dump") else sr.gen_ui
        
        return reply_text, gen_ui


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

    def _extract_tool_calls_from_response(self, messages: list) -> list:
        """Extract tool calls and results from messages in the response."""
        extracted = []
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
