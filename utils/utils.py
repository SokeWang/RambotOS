from core.history import History
from langchain.chat_models import init_chat_model
from config.config import CFG
from models.schema import RequireWebcam
from langchain.agents import create_agent
from loguru import logger
from services.webcam_logger import WebcamDecisionLogger
from utils.exceptions import ErrorHandler

# Removed check_require_webcam - merged into IntentManager

if __name__ == "__main__":
    print(check_require_webcam("what can you see"))