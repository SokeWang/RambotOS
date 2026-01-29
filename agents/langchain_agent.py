from langchain_google_genai import ChatGoogleGenerativeAI
from utils.tool_retriever import ToolRetriever
from config.config import CFG
from core.history import History
from loguru import logger
from agents.brain import BrainAgent
from agents.designer import DesignerAgent
from tools.tool_manager import tool_manager
from core.chat_prompt import Brain_Agent_Prompt, Designer_Agent_Prompt
from core.memory import MemoryManager
from core.intent import IntentManager
import asyncio

class UltronBrain:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model=CFG.chat_model,
            api_key=CFG.api_key
        )

        self.short_memory_manager = History()
        self.long_term_memory = MemoryManager()
        self.retriever = ToolRetriever()
        self.intent_manager = IntentManager()
        
        self.brain_manager = None
        self.designer_manager = None
        self._init_lock = asyncio.Lock()

    async def initialize(self):
        async with self._init_lock:
            if self.brain_manager:
                return
            
            logger.info("Initializing Agent Components (Explicit Architecture)...")
            
            # Initialize ToolManager and perform first discovery
            await tool_manager.initialize()
            
            # Index tools for retrieval
            all_mcp_tools = tool_manager.mcp_tools
            if all_mcp_tools:
                self.retriever.index_tools(all_mcp_tools)
            
            # We no longer create middlewares here.
            # Initial brain_manager is created with default tools.
            # It will be updated/re-created per-run if tools change significantly.
            self.brain_manager = BrainAgent(self.model, tool_manager.get_all_tools())
            self.designer_manager = DesignerAgent(self.model)
            logger.info("Agent Components initialized successfully.")

    async def run(self, content: list):
        if not self.brain_manager:
            await self.initialize()

        # 1. Extract raw query and check for media
        raw_query = self._extract_raw_query(content)
        has_image = any(isinstance(item, dict) and item.get("type") == "image_url" and item.get("media_source") == "attachment" for item in content)
        has_webcam = any(isinstance(item, dict) and item.get("type") == "image_url" and item.get("media_source") == "webcam" for item in content)
        
        # 2. 获取之前的历史记录用于意图识别 (不包含当前 Turn)
        history_for_intent = self.short_memory_manager.get()
        
        # 3. Explicit Step: Intent Refinement (Execute ONCE per turn)
        # This converts "ok" -> "diagnose network" based on history
        intent_response = await self.intent_manager.get_refined_query(
            history=[{"role": m.get("role") if isinstance(m, dict) else getattr(m, 'type', 'human'), 
                      "content": m.get("content") if isinstance(m, dict) else getattr(m, 'content', '')} 
                     for m in history_for_intent],
            current_query=raw_query,
            has_image=has_image,
            has_webcam=has_webcam
        )
        refined_query = intent_response.refined_query
        require_webcam = intent_response.require_webcam
        logger.info(f"Explicit Intent Refinement: '{raw_query}' -> '{refined_query}' (Webcam Needed: {require_webcam})")

        # 4. Handle Message Filtering based on Intent
        # We only filter out WEBCAM images if not required. Attachments are ALWAYS kept.
        if has_webcam and not require_webcam:
            content = [item for item in content if not (isinstance(item, dict) and item.get("type") == "image_url" and item.get("media_source") == "webcam")]
            logger.info("Filtering out webcam images as intent doesn't require them.")
        
        # 5. Add to short term history (After filtering)
        self.short_memory_manager.add("user", content)
        
        # 6. 获取包含当前 Turn 的完整历史，并过滤历史中多余的 WEBCAM 图像
        # 策略：如果当前不需要 WEBCAM，则完全移除历史中的 WEBCAM 图像块以节省 Token
        messages = self.short_memory_manager.get()
        cleaned_messages = []
        for m in messages:
            msg_content = getattr(m, 'content', []) if not isinstance(m, dict) else m.get("content", [])
            # 只有当这是当前轮次 (最后一轮) 且需要摄像头，或者是附件图像时，才保留图像块
            # 这里简化逻辑：如果 require_webcam=False，移除所有非 attachment 的 image_url
            if not require_webcam:
                if isinstance(msg_content, list):
                    filtered_content = [
                        item for item in msg_content 
                        if not (isinstance(item, dict) and item.get("type") == "image_url" and item.get("media_source") == "webcam")
                    ]
                    # 如果过滤后内容为空，保留原始文本部分（如果有）
                    if not filtered_content and msg_content:
                        filtered_content = [item for item in msg_content if isinstance(item, dict) and item.get("type") == "text"]
                    
                    if isinstance(m, dict):
                        m["content"] = filtered_content
                    else:
                        m.content = filtered_content
            cleaned_messages.append(m)
        
        messages = cleaned_messages
        
        # 7. Inject Refined Query as the text part if it changed significantly
        if refined_query != raw_query:
            # Access the last message's content, handling both dict and object types
            last_msg = messages[-1]
            last_msg_content = last_msg.content if not isinstance(last_msg, dict) else last_msg.get("content", [])
            
            # Ensure last_msg_content is a list for iteration
            if not isinstance(last_msg_content, list):
                last_msg_content = [last_msg_content] # Wrap in list if it's a single item

            for item in last_msg_content:
                if isinstance(item, dict) and item.get("type") == "text":
                    item["text"] = f"[Refined Query: {refined_query}]\n{item['text']}"
                    break

        # 8. Explicit Step: Tool Selection
        await tool_manager.refresh_if_needed()
        all_tools = tool_manager.get_all_tools()
        
        # Retrieve names of relevant tools
        # We always include skill-manager tools and the new search_memory tool
        always_include = {"propose_skill", "acquire_skill", "enhance_skill"}
        retrieved_names = set(self.retriever.retrieve(refined_query, k=5)) | always_include
        
        # Construct actual tool list
        selected_tools = [t for t in all_tools if t.name in retrieved_names]
        # Append the Memory Search Tool explicitly
        selected_tools.append(self.long_term_memory.get_tool())
        
        logger.debug(f"Explicit Tool Selection: {len(selected_tools)} tools selected for this turn.")

        # 5. Create a turn-specific BrainAgent with selected tools
        # This is where the ReAct loop happens
        brain_agent_instance = BrainAgent(self.model, selected_tools)
        
        max_retries = 2
        last_error = None
        brain_response = None
        system_prompt = Brain_Agent_Prompt

        for attempt in range(max_retries):
            try:
                current_messages = messages
                if last_error:
                    current_messages = messages + [
                        {"role": "user", "content": f"The previous attempt failed with error: {last_error}. Please correct your approach and try again or use another tool."}
                    ]
                
                brain_response = await brain_agent_instance.ainvoke(
                    {"messages": [{"role": "system", "content": system_prompt}] + current_messages}
                )
                reply_text = brain_response["structured_response"].reply
                
                # Reflection heuristic
                if "I cannot" in reply_text or "I don't have" in reply_text:
                    logger.debug("Agent admitted defeat, triggering reflection...")
                    last_error = "You mentioned you couldn't do something. Remember you can use 'propose_skill' to acquire new capabilities."
                    continue
                
                break # Success
            except Exception as e:
                logger.error(f"Brain Agent attempt {attempt+1}/{max_retries} failed: {e}")
                last_error = str(e)
                if attempt == max_retries - 1:
                    reply_text = f"I encountered an error while processing your request: {e}."

        yield {"reply": reply_text, "ui_component": None}

        # 6. Explicit Step: Memory Storage (Post-call)
        if intent_response.need_long_term_memory and brain_response:
            logger.info("Explicit Memory Storage: Saving interaction...")
            # We save the refined query and the assistant reply
            self.long_term_memory.add_memory("user", refined_query)
            self.long_term_memory.add_memory("assistant", reply_text)

        # 7. Designer Agent (UI)
        if brain_response and brain_response["structured_response"].need_ui:
            # Prepare UI Instructions for Designer
            ui_instruction = brain_response["structured_response"].ui_instruction or "Create a useful visualization based on the response."
            reply_text = brain_response["structured_response"].reply
            
            designer_agent = self.designer_manager.get_agent()
            designer_system_prompt = f"{Designer_Agent_Prompt}\n\n## UI INSTRUCTION:\n{ui_instruction}"
            
            designer_messages = [{"role": "system", "content": designer_system_prompt}] + messages + [{"role": "ai", "content": reply_text}]
            designer_response = await designer_agent.ainvoke({"messages": designer_messages})
            designer_data = designer_response["structured_response"].model_dump()
            yield {"reply": reply_text, "ui_component": designer_data}

        self.short_memory_manager.add("ai", [{"type": "text", "text": reply_text}])

    def _extract_raw_query(self, content: list) -> str:
        """Extracts text from message content list."""
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return item["text"]
            if hasattr(item, "text"):
                return item.text
        return str(content)
