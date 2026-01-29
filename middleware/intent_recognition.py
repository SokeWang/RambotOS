from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from typing import Callable, List, Dict
from loguru import logger
from core.intent import IntentManager

class IntentRecognitionMiddleware(AgentMiddleware):
    """
    意图识别与查询重写中间件
    
    作为中间件链的第一环，负责根据对话历史提炼用户的真实查询意图，
    并将结果存入 request.state 供后续检索中间件（工具/记忆）使用。
    """
    
    def __init__(
        self,
        intent_manager: IntentManager,
        enable_logging: bool = True
    ):
        self.intent_manager = intent_manager
        self.enable_logging = enable_logging
    
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """不支持同步调用，因为 IntentManager 是异步的"""
        logger.warning("IntentRecognitionMiddleware: Synchronous wrap_model_call is not optimized for async intent manager.")
        return handler(request)
    
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """异步版本：执行意图识别并增强请求状态"""
        
        # 核心优化：如果在这个 invoke 周期内已经识别过意图了，直接传递，不重复调用 LLM
        if "refined_query" in request.state:
            return await handler(request)
        
        # 1. 提取消息历史和当前 raw_query
        messages = request.state.get("messages", [])
        raw_query = self._extract_raw_query(messages)
        
        if not raw_query:
            return await handler(request)
            
        # 2. 调用 IntentManager 进行查询精炼
        # IntentManager 内部会处理历史记录的切片
        intent_response = await self.intent_manager.get_refined_query(
            history=[{"role": m.get("role") if isinstance(m, dict) else getattr(m, 'type', 'human'), 
                      "content": m.get("content") if isinstance(m, dict) else getattr(m, 'content', '')} 
                     for m in messages],
            current_query=raw_query
        )
        
        # 3. 将精炼后的查询存入 state，供后续中间件使用
        # 即使没有精炼成功，也会返回原始 raw_query
        request.state["refined_query"] = intent_response.refined_query
        request.state["need_memory"] = intent_response.need_long_term_memory
        
        if self.enable_logging:
            logger.info(f"Intent Middleware | Refined Query: '{intent_response.refined_query}'")
            
        return await handler(request)

    def _extract_raw_query(self, messages: List) -> str:
        """从最新的消息中提取原始查询文本"""
        if not messages:
            return ""
            
        last_msg = messages[-1]
        content = last_msg.get("content") if isinstance(last_msg, dict) else getattr(last_msg, 'content', '')
        
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # 处理多模态格式 [{"type": "text", "text": "..."}]
            return " ".join([item.get("text", "") for item in content if item.get("type") == "text"])
            
        return str(content)
