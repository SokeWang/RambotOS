from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import time
import json
from config.config import CFG
from loguru import logger
import os

class History:
    def __init__(self, session_id="global", checkpointer=None):
        self.db_path = CFG.SQLITE_DB_PATH
        self.session_id = session_id
        self.checkpointer = checkpointer
        # Ensure db directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def _get_checkpointer(self):
        if self.checkpointer:
            return self.checkpointer
        # Create a temporary one if none provided
        return AsyncSqliteSaver.from_conn_string(self.db_path)
        

    async def get(self, limit=20, skip=0, with_time=False):
        """
        Retrieves history directly from the checkpointer state.
        Ensures the data structure matches what the UI expects (list of content blocks).
        """
        checkpointer = await self._get_checkpointer()
        config = {"configurable": {"thread_id": self.session_id}}
        
        if not self.checkpointer:
            async with checkpointer as saver:
                state = await saver.aget(config)
        else:
            state = await checkpointer.aget(config)

        if not state:
            return []

        # Extract messages from checkpoint values
        messages = state.get("channel_values", {}).get("messages", [])
        
        sanitized_messages = []
        # Support pagination via slicing
        start_idx = max(0, len(messages) - limit - skip)
        end_idx = len(messages) - skip
        
        selected_messages = messages[start_idx:end_idx]

        for msg in selected_messages:
            role = None
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "ai"
            elif isinstance(msg, ToolMessage):
                # If it's a structured response tool, treat as AI reply
                if "Returning structured response" in str(msg.content):
                    role = "ai"
                else:
                    # Intermediate tool results: we don't show the text but we might want the role 
                    # if we were merging. For now, we skip but if we want to merge metadata 
                    # from AIMessage + ToolMessage result, we need to handle it.
                    continue
            elif isinstance(msg, SystemMessage):
                role = "system"
            
            if not role:
                continue

            content_blocks = []
            text_content = ""
            
            # 1. Extract raw text content
            if isinstance(msg.content, str):
                text_content = msg.content
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_content += block.get("text", "")
                    elif isinstance(block, str):
                        text_content += block

            # 2. Extract structured reply if it's an AIResponse tool result
            if isinstance(msg, ToolMessage) and "Returning structured response" in text_content:
                import re
                match = re.search(r"reply=['\"](.*?)['\"]", text_content, re.DOTALL)
                if match:
                    text_content = match.group(1).replace("\\n", "\n")
                else:
                    # Skip if it's just raw structured result with no reply
                    continue
            
            # 3. Handle tool calls (for AIMessages)
            tool_calls = getattr(msg, "tool_calls", [])
            clean_tool_calls = []
            if tool_calls and isinstance(msg, AIMessage):
                for tc in tool_calls:
                    if tc.get("name") == "AIResponse":
                        if not text_content and tc.get("args") and "reply" in tc["args"]:
                            text_content = tc["args"]["reply"]
                        continue
                    
                    clean_tool_calls.append({
                        "name": tc.get("name"),
                        "input": str(tc.get("args", "")),
                        "status": "success",
                        "output": ""
                    })
            
            # 4. Build content blocks for THIS message
            local_blocks = []
            if text_content:
                local_blocks.append({"type": "text", "text": text_content})
            if clean_tool_calls:
                local_blocks.append({"type": "text", "text": f"__TOOL_CALLS_METADATA__: {json.dumps(clean_tool_calls)}"})

            if not local_blocks:
                continue

            # 5. Merge logic: group consecutive same-role messages
            if sanitized_messages and sanitized_messages[-1]["role"] == role:
                existing_blocks = sanitized_messages[-1]["content"]
                for lb in local_blocks:
                    # Simple de-duplication: if this exact text block already exists in the turn, skip it
                    if any(eb.get("text") == lb.get("text") for eb in existing_blocks):
                        continue
                    existing_blocks.append(lb)
            else:
                sanitized_messages.append({
                    "role": role, 
                    "content": local_blocks,
                    "time": time.time()
                })
            
        return sanitized_messages