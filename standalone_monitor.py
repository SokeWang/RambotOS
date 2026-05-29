import os
import sys

# Inject backend path for compatibility with existing imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")
if os.path.exists(BACKEND_PATH) and BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)
import time
import asyncio
import signal
import requests
from loguru import logger
from config.config import CFG
from agents.langchain_agent import LangchainBrain
from services.email_service import EmailService

# Configuration
CORE_URL = "http://127.0.0.1:8000"
MONITOR_NAME = "email"
PID_FILE = f"/tmp/rambot_{MONITOR_NAME}_monitor.pid"

class StandaloneMonitor:
    def __init__(self):
        self.running = True
        self.brain = None
        self.email_service = None
        self.interval = CFG.MAIL_CHECK_INTERVAL
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

    def handle_exit(self, signum, frame):
        logger.info(f"Monitor: Received signal {signum}, stopping...")
        self.running = False

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
                "label": "Email Heartbeat Monitoring",
                "sublabel": "Email Monitoring",
                "icon": "Mail",
                "color": "blue"
            })
            if resp.status_code == 200:
                logger.info("Monitor: Registered with Rambot Core.")
                return True
        except Exception as e:
            logger.error(f"Monitor: Failed to register with Core: {e}")
        return False

    def send_notification(self, message):
        try:
            requests.post(f"{CORE_URL}/notify", json={
                "source": MONITOR_NAME,
                "message": message,
                "level": "info"
            })
        except Exception as e:
            logger.error(f"Monitor: Failed to send notification to Core: {e}")

    def ping_core(self):
        try:
            requests.post(f"{CORE_URL}/monitor/ping/{MONITOR_NAME}")
        except:
            pass

    async def run(self):
        logger.info(f"Starting standalone Email Monitor (PID: {os.getpid()})")
        self.create_pid_file()
        
        # In Gateway Mode, the service will relay to Core
        self.email_service = EmailService(
            brain=None, # Not used in gateway mode
            notification_callback=self.send_notification
        )
        
        if not self.register_with_core():
            logger.warning("Monitor: Running in offline mode (Core not reachable).")

        while self.running:
            try:
                # 1. Ping core
                self.ping_core()
                
                # 2. Check emails
                logger.debug("Monitor: Checking emails...")
                await self.email_service.check_and_reply()
                
            except Exception as e:
                logger.error(f"Monitor Loop Error: {e}")
            
            # 3. Sleep with heartbeat pings every minute if interval is long
            sleep_time = self.interval
            while sleep_time > 0 and self.running:
                step = min(sleep_time, 1) # Check stop signal every second
                await asyncio.sleep(step)
                sleep_time -= step
        
        self.remove_pid_file()
        logger.info("Monitor: Standalone process exited.")

if __name__ == "__main__":
    monitor = StandaloneMonitor()
    asyncio.run(monitor.run())
