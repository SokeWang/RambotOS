import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.getcwd())

from agents.langchain_agent import UltronBrain
from loguru import logger

async def test_explicit_flow():
    try:
        logger.info("Starting Explicit Flow Verification...")
        brain = UltronBrain()
        await brain.initialize()
        
        # Mock a user query that requires history and memory
        # 1. First interaction to set history
        logger.info("--- Step 1: Setting History ---")
        async for res in brain.run([{"type": "text", "text": "I love eating pizza in Shanghai."}]):
            logger.info(f"AI Reply 1: {res['reply']}")
            
        # 2. Second interaction requiring intent refinement
        logger.info("--- Step 2: Testing Intent Refinement ('What is the weather there?') ---")
        async for res in brain.run([{"type": "text", "text": "What is the weather there?"}]):
            logger.info(f"AI Reply 2: {res['reply']}")
            
        # 3. Third interaction requiring memory search tool
        # (Assuming step 1 was saved to memory)
        logger.info("--- Step 3: Testing Memory Tool ('What food did I say I liked?') ---")
        async for res in brain.run([{"type": "text", "text": "What food did I say I liked?"}]):
            logger.info(f"AI Reply 3: {res['reply']}")

        logger.info("Verification Complete. Please check logs for 'Explicit Intent Refinement' and 'Explicit Tool Selection'.")
        
    except Exception as e:
        logger.error(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_explicit_flow())
