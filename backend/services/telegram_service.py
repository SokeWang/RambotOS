import asyncio
import httpx
from loguru import logger
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from config.config import CFG

class TelegramService:
    def __init__(self, notification_callback=None):
        self.notification_callback = notification_callback
        self.running = False
        self.application = None
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message and Chat ID instruction."""
        chat_id = update.message.chat_id
        await update.message.reply_text(
            f"Hello! I am Rambot. To link your account, please enter your Chat ID in the OS Settings panel.\n\n"
            f"Your Chat ID: `{chat_id}`",
            parse_mode='Markdown'
        )

    async def handle_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Simple command to get Chat ID."""
        await update.message.reply_text(f"Your Chat ID is: `{update.message.chat_id}`", parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        chat_id = str(update.message.chat_id)
        text = update.message.text
        sender_name = update.message.from_user.full_name or "Telegram User"

        logger.info(f"TelegramService: Received message from {sender_name} ({chat_id}): {text}")

        # 1. Identity Mapping
        try:
            # Check gateway for profile using the new /user/profile endpoint
            params = {"user_id": f"telegram_{chat_id}"}
            resp = await self.http_client.get("http://127.0.0.1:8000/user/profile", params=params)
            if resp.status_code == 200:
                profile = resp.json()
                if profile.get("is_master"):
                    logger.info(f"TelegramService: User {chat_id} identified as Master.")
        except Exception as e:
            logger.error(f"TelegramService: Identity check failed: {e}")

        # 2. Relay to Gateway
        chat_payload = {
            "message": text,
            "sender": f"telegram_{chat_id}",
            "attachment_base64": None
        }

        try:
            resp = await self.http_client.post("http://127.0.0.1:8000/chat", json=chat_payload)
            if resp.status_code == 200:
                import json
                lines = [line.strip() for line in resp.text.split('\n') if line.strip()]
                if not lines:
                    return
                
                # Get the last complete JSON update for the final reply
                last_response = json.loads(lines[-1])
                reply_text = last_response.get("reply", "")
                
                if reply_text:
                    await update.message.reply_text(reply_text)
            else:
                logger.error(f"TelegramService: Gateway error {resp.status_code}")
                await update.message.reply_text("I'm sorry, I'm having trouble connecting to my central brain.")
        except Exception as e:
            logger.error(f"TelegramService: Failed to contact Gateway: {e}")
            await update.message.reply_text("Internal communication error.")

    async def run(self):
        if not CFG.TELEGRAM_TOKEN or "YOUR_TELEGRAM_BOT_TOKEN" in CFG.TELEGRAM_TOKEN:
            logger.warning("TelegramService: No valid token found. Skipping...")
            return

        self.application = ApplicationBuilder().token(CFG.TELEGRAM_TOKEN).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("id", self.handle_id))
        self.application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))
        
        self.running = True
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("TelegramService: Bot is polling for messages.")
        
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        self.running = False
        await self.http_client.aclose()
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
