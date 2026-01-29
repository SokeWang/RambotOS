from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import CFG
from core.chat_prompt import Intent_Refiner_Prompt
from typing import List, Dict, Optional
from models.schema import IntentResponse
import asyncio
from loguru import logger

class IntentManager:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model=CFG.chat_model,
            api_key=CFG.api_key,
            temperature=0  # Deterministic for query rewriting
        ).with_structured_output(IntentResponse)

    async def get_refined_query(self, history: List[Dict], current_query: str, has_image: bool = False, has_webcam: bool = False) -> IntentResponse:
        """
        Refines the current query into a context-aware search query.
        """
        if not history and not has_image and not has_webcam:
            return IntentResponse(refined_query=current_query, need_long_term_memory=False, require_webcam=has_webcam)

        # Construct history string for context
        history_str = ""
        for msg in history[-5:]: # Only last 5 for context
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
                content = " ".join(text_parts)
            history_str += f"{role}: {content}\n"

        context_info = ""
        if has_image:
            context_info += "\n[System Note: User has provided an image attachment.]"
        if has_webcam:
            context_info += "\n[System Note: Webcam vision is available/active.]"

        prompt = f"{Intent_Refiner_Prompt}\n\nHistory:\n{history_str}\nLatest Query: {current_query}{context_info}\n\nRefined Query:"
        
        try:
            response = await self.model.ainvoke(prompt)
            # Response is already an IntentResponse object because of with_structured_output
            logger.debug(f"Intent Refiner: '{current_query}' -> '{response.refined_query}'")
            return response
        except Exception as e:
            logger.error(f"Intent Refiner failed: {e}")
            return IntentResponse(refined_query=current_query, need_long_term_memory=False)
