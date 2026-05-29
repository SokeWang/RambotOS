from loguru import logger
from config.config import CFG

# 每天18:05触发
TRIGGER_ARGS = {
    "trigger": "cron",
    "hour": 18,
    "minute": 24
}

async def send_notification(message: str):
    import requests
    try:
        requests.post("http://127.0.0.1:8000/notify", json={
            "source": "水份提醒",
            "message": message,
            "level": "info"
        })
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

async def execute():
    logger.info("提醒喝水任务触发")
    await send_notification("⏰ 该喝水了，保持健康！")
