import time
import asyncio
from PySide6.QtCore import QThread, Signal
from loguru import logger
from services.email_service import EmailService

class EmailMonitorThread(QThread):
    notificationReceived = Signal(str)

    def __init__(self, ultron_brain, interval=300): # Default check every 5 mins
        super().__init__()
        self.brain = ultron_brain
        self.interval = interval
        self.running = True
        self.email_service = None

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

    def run(self):
        logger.info("EmailMonitorThread: Background monitoring started.")
        
        # We need to create a new event loop for this thread if we want to run async code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize service with a callback that emits a signal to the main thread
        self.email_service = EmailService(
            self.brain, 
            notification_callback=lambda msg: self.notificationReceived.emit(msg)
        )

        while self.running:
            try:
                # Run the async check
                loop.run_until_complete(self.email_service.check_and_reply())
            except Exception as e:
                logger.error(f"EmailMonitorThread Error: {e}")
            
            # Sleep for the interval, checking for stop signal every second
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

        loop.close()
        logger.info("EmailMonitorThread: Background monitoring stopped.")
