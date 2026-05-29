import sys
import os
from loguru import logger
from config.config import CFG
from services.email_service import EmailService

# 每天17:30触发
TRIGGER_ARGS = {
    "trigger": "cron",
    "hour": 18,
    "minute": 24
}

async def fetch_news():
    try:
        from duckduckgo_search import DDGS
        logger.info("Task: Fetching real news via DuckDuckGo...")
        results = DDGS().news("top headlines global news", max_results=10)
        if not results:
            return [{"title": "No news found today.", "url": ""}]
        return results
    except Exception as e:
        logger.error(f"Task: Failed to fetch news: {e}")
        return [{"title": f"Failed to fetch news: {e}", "url": ""}]

async def execute():
    logger.info("Executing news_brief!")
    articles = await fetch_news()
    
    email_body = "<h1>Top 10 News Today</h1><ul>"
    for art in articles:
        email_body += f"<li><a href='{art['url']}'>{art['title']}</a></li>"
    email_body += "</ul>"
    
    email_svc = EmailService(None)
    await email_svc.send_email(
        to=CFG.USER_EMAIL,
        subject="Your Daily News Brief",
        text="Here is your top 10 news digest.",
        html=email_body
    )
