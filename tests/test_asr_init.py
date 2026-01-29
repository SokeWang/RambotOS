import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.asr import ASRFactory
from loguru import logger

def test_asr_initialization():
    try:
        logger.info("Testing Faster Whisper initialization...")
        ear = ASRFactory.get_asr_engine("fast-whisper")
        logger.success("Faster Whisper engine initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"Faster Whisper initialization failed: {e}")
        return False

if __name__ == "__main__":
    test_asr_initialization()
