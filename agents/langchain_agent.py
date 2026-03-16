from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import CFG
from loguru import logger
from agents.tool_manager import tool_manager
from core.skill_index import skill_index
from langchain.agents import create_agent
from core.chat_prompt import build_system_prompt
from core.memory import MemoryManager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from models.schema import AIResponse, MemoryExtraction
import asyncio
from agents.base_agent import BaseAgent
from typing import Any, List, AsyncGenerator
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model

from services.media_processor import MediaProcessor

# Trimming middleware: Keep system/first message + last 5 rounds (Human -> AI)
@before_model
def trim_memory(state: AgentState, runtime) -> dict | None:
    messages = state["messages"]
    num_rounds = 5
    
    # Identify indices of all HumanMessages
    human_indices = [i for i, m in enumerate(messages) if isinstance(m, HumanMessage)]
    
    # If we have 5 or fewer rounds, no need to trim
    if len(human_indices) <= num_rounds:
        return None
    
    # Find the index of the 5th most recent human message
    tail_start = human_indices[-num_rounds]
    
    # Preserve the first message (System/Protocol) and everything from the target turn onwards
    # We use max(1, tail_start) to avoid duplicating the first message if it happens to be the start of the tail.
    new_messages = [messages[0]] + messages[max(1, tail_start):]
    
    logger.debug(f"Trimming memory: {len(messages)} -> {len(new_messages)} messages (Preserving last {num_rounds} rounds)")
    
    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }

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
            checkpointer=self.checkpointer,
            middleware=[trim_memory]
        )

    async def run(self, content: list, is_master: bool = True, session_id: str = "global", user_name: str = "User") -> AsyncGenerator[dict, None]:
        if not self.checkpointer:
            await self.initialize()

        # 1. Prepare history and messages
        # We only need the latest user message to pass to the agent; 
        # previous history is already in the checkpointer.
        formatted_messages = [HumanMessage(content=content)]
        
        # 2. Prepare environment
        if skill_index.refresh_if_needed():
            if "master" in self._cached_prompt:
                del self._cached_prompt["master"]

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
                        call_id = self._get_tool_call_id(event)
                        current_tools = self._extract_tool_calls_from_response(internal_turns, running_id=call_id)
                        yield {"reply": f"Processing with {event.get('name')}...", "tool_calls": current_tools}
                
                elif kind == "on_tool_end":
                    if event.get("name") != "AIResponse":
                        call_id = self._get_tool_call_id(event)
                        tool_output = event.get("data", {}).get("output", "")
                        
                        internal_turns.append(ToolMessage(content=str(tool_output), tool_call_id=str(call_id)))
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
        if not sr:
            return "", None
            
        # Handle both dict and object types
        if isinstance(sr, dict):
            reply_text = sr.get("reply", "")
            gen_ui = sr.get("gen_ui")
        else:
            reply_text = getattr(sr, "reply", "")
            gen_ui = getattr(sr, "gen_ui", None)
        
        # Format GenUI if needed
        if gen_ui:
            if isinstance(gen_ui, list):
                gen_ui = [c.model_dump() if hasattr(c, "model_dump") else c for c in gen_ui]
            else:
                gen_ui = gen_ui.model_dump() if hasattr(gen_ui, "model_dump") else gen_ui
        
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

    def _get_tool_call_id(self, event: dict) -> str:
        """Centralized helper to scavenge tool_call_id from various event fields."""
        data = event.get("data", {})
        metadata = event.get("metadata", {})
        
        # Priority order for ID extraction
        call_id = (
            metadata.get("langchain_tool_call_id") or
            data.get("tool_call_id") or
            (data.get("input", {}) if isinstance(data.get("input"), dict) else {}).get("tool_call_id") or
            event.get("run_id")
        )
        
        if not call_id:
            logger.warning(f"No tool_call_id found for {event.get('name')}. Fallback to run_id.")
            call_id = f"unknown_{event.get('run_id', 'no_id')}"
            
        return str(call_id)

    def _extract_tool_calls_from_response(self, messages: list, running_id: str = None) -> list:
        """Extract tool calls and results from messages in the response."""
        tool_map = {} # call_id -> {name, input, output, status}
        
        for msg in messages:
            # Handle AI messages (Tool Calls)
            tool_calls = getattr(msg, "tool_calls", [])
            for tc in tool_calls:
                if tc.get("name") == "AIResponse":
                    continue
                    
                call_id = tc.get("id")
                tool_map[call_id] = {
                    "name": tc.get("name"),
                    "input": str(tc.get("args", "")),
                    "status": "success",
                    "output": ""
                }
                # logger.debug(f"DEBUG: Found call in history: {tc.get('name')} ID: {call_id}")
            
            # Handle Tool messages (Results)
            if isinstance(msg, ToolMessage):
                call_id = msg.tool_call_id
                if call_id in tool_map:
                    tool_map[call_id]["output"] = str(msg.content)
                    tool_map[call_id]["status"] = "success"
                else:
                    # If ID doesn't match exactly, try to find by name if there's only one candidate
                    # This handles cases where ID formats differ between model and runner
                    candidates = [k for k, v in tool_map.items() if not v["output"]]
                    if len(candidates) == 1:
                        target_id = candidates[0]
                        tool_map[target_id]["output"] = str(msg.content)
                        tool_map[target_id]["status"] = "success"
                        logger.debug(f"Fuzzy matched tool result for {tool_map[target_id]['name']} using ID {target_id}")
                    else:
                        logger.debug(f"ID Mismatch: Tool result {call_id} not found in {list(tool_map.keys())}")
        
        # If we know a specific tool is running, overwrite its status
        if running_id and running_id in tool_map:
            tool_map[running_id]["status"] = "running"
        elif running_id:
            # Fallback if AI message hasn't appeared yet in internal_turns (rare)
            pass

        return list(tool_map.values())

    
    def _get_cached_system_prompt(self, is_master: bool = True, user_name: str = "User") -> str:
        """
        Build optimized system prompt dynamically based on context.
        Master prompt is cached after first build; guest prompt is not cached (varies by user_name).
        """
        if not is_master:
            from core.chat_prompt import Email_Replier_Prompt
            return f"The current user is: {user_name}.\n\n" + Email_Replier_Prompt

        if "master" not in self._cached_prompt:
            skills_list = skill_index.get_all_skill_names()
            skills_names_str = ", ".join(skills_list) if skills_list else "None"

            self._cached_prompt["master"] = build_system_prompt(
                has_skills=True,  # Always include skill protocol to enforce discovery
                has_memory=True,
                extended=True,
                skills_summary=f"[{skills_names_str}]"
            )
        return self._cached_prompt["master"]
