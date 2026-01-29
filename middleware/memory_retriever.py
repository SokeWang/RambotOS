from langchain_core.messages import SystemMessage
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from typing import Callable, List
from loguru import logger
from core.memory import MemoryManager

class LongTermMemoryMiddleware(AgentMiddleware):
    """
    长期记忆检索中间件
    
    动态检索与当前查询相关的长期记忆，并将其注入到系统提示词中。
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        k: int = 3,
        enable_logging: bool = True
    ):
        self.memory_manager = memory_manager
        self.k = k
        self.enable_logging = enable_logging
    
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """同步版本：在模型调用前注入记忆上下文"""
        
        # 1. 检查是否需要检索记忆
        need_memory = request.state.get("need_memory", False)
        if not need_memory:
            return handler(request)
            
        # 2. 提取检索用的查询 (优先使用 refined_query)
        query = request.state.get("refined_query")
        if not query:
            return handler(request)
            
        # 3. 检索相关记忆
        memories = self.memory_manager.retrieve_memories(query, k=self.k)
        
        # 4. 构建记忆上下文
        memory_context = ""
        if memories:
            memory_context = "\n\n## RELEVANT PAST INTERACTIONS:\n"
            for mem in memories:
                memory_context += f"- {mem['role']}: {mem['content']}\n"
                
            if self.enable_logging:
                logger.info(f"Memory Retrieval | Query: '{query[:50]}...' | Retrieved {len(memories)} memories")
        
        # 5. 注入到系统消息
        if memory_context:
            orig_system_msg = request.system_message
            new_content = (orig_system_msg.content if orig_system_msg else "") + memory_context
            new_system_msg = SystemMessage(content=new_content)
            return handler(request.override(system_message=new_system_msg))
            
        return handler(request)
    
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """异步版本：在模型调用前注入记忆上下文，调用后自动存入记忆"""
        
        # --- PRE-CALL: 检索逻辑 ---
        # 核心优化：如果在这个 invoke 周期内已经检索过记忆了，直接复用
        if "memory_context" in request.state:
            memory_context = request.state["memory_context"]
            if memory_context:
                orig_system_msg = request.system_message
                new_content = (orig_system_msg.content if orig_system_msg else "") + memory_context
                request = request.override(system_message=SystemMessage(content=new_content))
            
            response = await handler(request)
            return await self._handle_post_call(request, response)

        need_memory = request.state.get("need_memory", False)
        refined_query = request.state.get("refined_query")
        
        if need_memory and refined_query:
            # 检索相关记忆 (MemoryManager.retrieve_memories 暂为同步)
            import asyncio
            memories = await asyncio.to_thread(self.memory_manager.retrieve_memories, refined_query, k=self.k)
            
            if memories:
                memory_context = "\n\n## RELEVANT PAST INTERACTIONS:\n"
                for mem in memories:
                    memory_context += f"- {mem['role']}: {mem['content']}\n"
                
                orig_system_msg = request.system_message
                new_content = (orig_system_msg.content if orig_system_msg else "") + memory_context
                request = request.override(system_message=SystemMessage(content=new_content))
                
                if self.enable_logging:
                    logger.info(f"Memory Retrieval | Query: '{refined_query[:50]}...' | Loaded {len(memories)} memories")
            else:
                memory_context = ""
            
            # 存入 state 供以后在这个 invoke 周期内复用
            request.state["memory_context"] = memory_context

        # --- EXECUTE: 调用模型 ---
        response = await handler(request)
        return await self._handle_post_call(request, response)

    async def _handle_post_call(self, request, response):
        # 遵循原逻辑：只有在 IntentManager 标记需要长期记忆时才存入
        try:
            res_data = getattr(response, "structured_response", None)
            if res_data and hasattr(res_data, "reply") and res_data.reply and refined_query:
                # 关键：检查 need_memory 标志
                if request.state.get("need_memory", False):
                    import asyncio
                    loop = asyncio.get_event_loop()
                    loop.run_in_executor(None, self.memory_manager.add_memory, "user", refined_query)
                    loop.run_in_executor(None, self.memory_manager.add_memory, "assistant", res_data.reply)
                    
                    if self.enable_logging:
                        logger.info(f"Memory Storage | Saved interaction for query: '{refined_query[:50]}...'")
                else:
                    if self.enable_logging:
                        logger.debug("Memory Storage | Skipped (need_memory is False)")
        except Exception as e:
            logger.warning(f"Memory Storage Middleware failed: {e}")

        return response
