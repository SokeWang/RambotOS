import os
import sys

# Inject backend path for compatibility with existing imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")
if os.path.exists(BACKEND_PATH) and BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)
import asyncio
import signal
import requests
from loguru import logger
from config.config import CFG
from services.telegram_service import TelegramService

# Configuration
CORE_URL = "http://127.0.0.1:8000"
MONITOR_NAME = "telegram"
PID_FILE = f"/tmp/rambot_{MONITOR_NAME}_monitor.pid"

class StandaloneTelegram:
    def __init__(self):
        self.running = True
        self.telegram_service = None
        self.interval = CFG.TELEGRAM_CHECK_INTERVAL
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

    def handle_exit(self, signum, frame):
        logger.info(f"TelegramMonitor: Received signal {signum}, stopping...")
        self.running = False
        if self.telegram_service:
            self.telegram_service.stop()

    def create_pid_file(self):
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

    def remove_pid_file(self):
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

    def register_with_core(self):
        try:
            resp = requests.post(f"{CORE_URL}/monitor/register", json={
                "name": MONITOR_NAME,
                "pid": os.getpid(),
                "interval": self.interval,
                "label": "Telegram Message Monitoring",
                "sublabel": "Telegram Monitoring (Bot API)",
                "icon": "MessageCircle",
                "color": "sky"
            })
            if resp.status_code == 200:
                logger.info("TelegramMonitor: Registered with Rambot Core.")
                return True
        except Exception as e:
            logger.error(f"TelegramMonitor: Failed to register with Core: {e}")
        return False

    def send_notification(self, message):
        try:
            requests.post(f"{CORE_URL}/notify", json={
                "source": MONITOR_NAME,
                "message": message,
                "level": "info"
            })
        except Exception as e:
            logger.error(f"TelegramMonitor: Failed to send notification to Core: {e}")

    def ping_core(self):
        try:
            requests.post(f"{CORE_URL}/monitor/ping/{MONITOR_NAME}")
        except:
            pass

    async def run(self):
        logger.info(f"Starting standalone Telegram Monitor (PID: {os.getpid()})")
        self.create_pid_file()
        
        self.telegram_service = TelegramService(
            notification_callback=self.send_notification
        )
        
        if not self.register_with_core():
            logger.warning("TelegramMonitor: Running in offline mode (Core not reachable).")

        # Start the telegram polling in a separate task
        service_task = asyncio.create_task(self.telegram_service.run())
        
        while self.running:
            try:
                self.ping_core()
            except Exception as e:
                logger.error(f"TelegramMonitor Loop Error: {e}")
            
            await asyncio.sleep(10) # Hearbeat ping every 10s
        
        service_task.cancel()
        try:
            await service_task
        except asyncio.CancelledError:
            pass
            
        self.remove_pid_file()
        logger.info("TelegramMonitor: Standalone process exited.")

def main():
    monitor = StandaloneTelegram()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
