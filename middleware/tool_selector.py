from langchain_core.messages import SystemMessage
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from typing import Callable, List, Set
from loguru import logger
from utils.tool_retrieval_logger import ToolRetrievalLogger


PROTOCOLS = {
    "gmail": """## EMAIL PROTOCOL:
- **Identity**: Clearly identify yourself as "RAMBOT (AI Assistant)".
- **Perspective**: Use third-person or collaborative phrasing (e.g., "on behalf of my user...").
- **Signature**: Always include: "— RAMBOT, AI Operating System".
- **Formatting**: Use Markdown and structured layouts for professional message quality.""",
    
    "evolution": """## OPERATIONAL PROTOCOL (EVOLUTION):
- **Evolution**: Use "propose_skill" when current capabilities are insufficient. You have the power to acquire new skills or enhance existing ones through the skill-manager tools."""
}


class SmartToolSelectorMiddleware(AgentMiddleware):
    """
    智能工具选择中间件
    
    使用 embedding-based 语义检索动态选择最相关的工具，
    同时保证核心工具始终可用。
    
    Args:
        retriever: ToolRetriever 实例，用于语义检索
        max_tools: 最大工具数量限制
        always_include: 始终包含的核心工具名称集合
        enable_logging: 是否启用日志记录
    """
    
    def __init__(
        self,
        tool_manager,
        retriever,
        max_tools: int = 5,
        enable_logging: bool = True
    ):
        self.tool_manager = tool_manager
        self.retriever = retriever
        self.max_tools = max_tools
        self.enable_logging = enable_logging
    
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """在每次模型调用前动态选择工具（同步版本）"""
        # 1. 提取用户查询 (优先使用 refined_query)
        user_query = request.state.get("refined_query")
        if not user_query:
            user_query = self._extract_query(request.state.get("messages", []))

        
        # 2. Refresh tools if disk state changed
        # Note: In synchronous wrap_model_call, we run the async refresh in a loop if needed
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
            refresh_occurred = asyncio.run(self.tool_manager.refresh_if_needed())
        except Exception as e:
            logger.warning(f"Middleware (Sync): Failed to check/refresh tools: {e}")
            refresh_occurred = False

        current_tools = self.tool_manager.get_filtered_tools()
        
        if refresh_occurred:
            logger.info("Middleware: Tools refreshed, updating retriever index...")
            self.retriever.index_tools(self.tool_manager.mcp_tools)
        
        # 3. 使用 retriever 检索相关工具
        retrieved_tool_names = self._retrieve_tools(user_query, current_tools)
        
        # 4. 过滤工具列表
        selected_tools = self._filter_tools(current_tools, retrieved_tool_names)
        
        # 4. 日志记录
        if self.enable_logging:
            logger.info(
                f"Tool Selection | Query: '{user_query[:50]}...' | "
                f"Selected {len(selected_tools)}/{len(current_tools)} tools: "
                f"{[t.name for t in selected_tools]}"
            )
        
        # 5. 记录到MongoDB用于训练
        try:
            retrieval_logger = ToolRetrievalLogger()
            retrieval_logger.log_retrieval(
                query=user_query,
                all_tool_names=[t.name for t in current_tools],
                selected_tool_names=[t.name for t in selected_tools]
            )
        except Exception as e:
            logger.warning(f"Failed to log tool retrieval: {e}")
        
        # 6. Inject Protocols dynamically
        active_protocols = []
        
        # Check for Gmail
        if any(t.name.startswith("gmail") or "gmail" in t.name.lower() for t in selected_tools):
            active_protocols.append(PROTOCOLS["gmail"])
            
        # Check for Evolution
        if any(t.name in {"propose_skill", "acquire_skill", "enhance_skill"} for t in selected_tools):
            active_protocols.append(PROTOCOLS["evolution"])

        orig_system_msg = request.system_message
        new_content = orig_system_msg.content if orig_system_msg else ""
        if active_protocols:
            new_content += "\n\n" + "\n\n".join(active_protocols)
            
        new_system_msg = SystemMessage(content=new_content)

        return handler(request.override(tools=selected_tools, system_message=new_system_msg))
    
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """在每次模型调用前动态选择工具（异步版本）"""
        
        # 核心优化：如果在这个 invoke 周期内已经选择过工具了，直接复用
        if "selected_tools" in request.state:
            return await self._handle_model_call(request, handler, request.state["selected_tools"])

        # 1. 提取用户查询
        user_query = self._extract_query(request.state.get("messages", []))
        
        # 2. Refresh tools if disk state changed
        try:
            refresh_occurred = await self.tool_manager.refresh_if_needed()
        except Exception as e:
            logger.warning(f"Middleware (Async): Failed to check/refresh tools: {e}")
            refresh_occurred = False
            
        current_tools = self.tool_manager.get_filtered_tools()
        
        if refresh_occurred:
            logger.info("Middleware: Tools refreshed, updating retriever index...")
            self.retriever.index_tools(self.tool_manager.mcp_tools)
        
        # 3. 使用 retriever 检索相关工具
        retrieved_tool_names = self._retrieve_tools(user_query, current_tools)
        
        # 4. 过滤工具列表
        selected_tools = self._filter_tools(current_tools, retrieved_tool_names)
        
        # 4. 日志记录
        if self.enable_logging:
            logger.info(
                f"Tool Selection | Query: '{user_query[:50]}...' | "
                f"Selected {len(selected_tools)}/{len(current_tools)} tools: "
                f"{[t.name for t in selected_tools]}"
            )
        
        # 5. 记录到MongoDB用于训练
        try:
            retrieval_logger = ToolRetrievalLogger()
            retrieval_logger.log_retrieval(
                query=user_query,
                all_tool_names=[t.name for t in current_tools],
                selected_tool_names=[t.name for t in selected_tools]
            )
        except Exception as e:
            logger.warning(f"Failed to log tool retrieval: {e}")
        
        # 6. Inject Protocols dynamically (Async)
        active_protocols = []
        
        if any(t.name.startswith("gmail") or "gmail" in t.name.lower() for t in selected_tools):
            active_protocols.append(PROTOCOLS["gmail"])
            
        if any(t.name in {"propose_skill", "acquire_skill", "enhance_skill"} for t in selected_tools):
            active_protocols.append(PROTOCOLS["evolution"])

        orig_system_msg = request.system_message
        new_content = orig_system_msg.content if orig_system_msg else ""
        if active_protocols:
            new_content += "\n\n" + "\n\n".join(active_protocols)
            
        new_system_msg = SystemMessage(content=new_content)
        
        # 存入 state 供以后在这个 invoke 周期内复用
        request.state["selected_tools"] = selected_tools

        return await handler(request.override(tools=selected_tools, system_message=new_system_msg))

    async def _handle_model_call(self, request, handler, selected_tools):
        """处理协议注入并执行模型调用"""
        active_protocols = []
        if any(t.name.startswith("gmail") or "gmail" in t.name.lower() for t in selected_tools):
            active_protocols.append(PROTOCOLS["gmail"])
        if any(t.name in {"propose_skill", "acquire_skill", "enhance_skill"} for t in selected_tools):
            active_protocols.append(PROTOCOLS["evolution"])

        orig_system_msg = request.system_message
        new_content = orig_system_msg.content if orig_system_msg else ""
        if active_protocols:
            new_content += "\n\n" + "\n\n".join(active_protocols)
            
        new_system_msg = SystemMessage(content=new_content)
        return await handler(request.override(tools=selected_tools, system_message=new_system_msg))
    
    def _extract_query(self, messages: List) -> str:
        """从消息历史中提取用户查询"""
        query_parts = []
        
        # 从最近的消息开始查找用户输入
        for msg in reversed(messages):
            # 处理不同类型的消息对象
            if hasattr(msg, 'type') and msg.type == 'human':
                # LangChain HumanMessage 对象
                content = msg.content if hasattr(msg, 'content') else str(msg)
                if isinstance(content, str):
                    query_parts.append(content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            query_parts.append(item["text"])
                        elif hasattr(item, 'text'):
                            query_parts.append(item.text)
                break
            elif isinstance(msg, dict):
                # 字典格式的消息
                role = msg.get("role")
                if role == "user":
                    content = msg.get("content")
                    if isinstance(content, str):
                        query_parts.append(content)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                query_parts.append(item["text"])
                    break
            else:
                # 其他对象类型
                role = getattr(msg, "role", None)
                if role == "user":
                    content = getattr(msg, "content", None)
                    if isinstance(content, str):
                        query_parts.append(content)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                query_parts.append(item["text"])
                    break
        
        query = " ".join(query_parts)
        
        # Debug logging
        if self.enable_logging and not query.strip():
            logger.warning(f"Empty query extracted from {len(messages)} messages")
            if messages:
                logger.debug(f"Last message type: {type(messages[-1])}, content: {messages[-1]}")
        
        return query
    
    def _retrieve_tools(self, query: str, all_tools: List) -> Set[str]:
        """使用 retriever 检索相关工具"""
        always_include = {"propose_skill", "acquire_skill", "enhance_skill"}

        if not query.strip():
            # 如果没有查询，只返回必选工具
            return always_include
        
        # 计算需要检索的工具数量（排除必选工具）
        k = max(1, self.max_tools - len(always_include))
        
        # 执行检索
        try:
            retrieved = set(self.retriever.retrieve(query, k=k))
        except Exception as e:
            logger.warning(f"Tool retrieval failed: {e}, using always_include only")
            retrieved = set()
        
        # 合并必选工具
        return retrieved | always_include
    
    def _filter_tools(self, all_tools: List, selected_names: Set[str]) -> List:
        """根据名称过滤工具列表"""
        return [tool for tool in all_tools if tool.name in selected_names]
