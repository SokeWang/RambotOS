import asyncio
import requests
import json
import os
import shlex
from typing import Any
from loguru import logger
from config.config import CFG
from agentmail import AgentMail
from agentmail.core.api_error import ApiError

class EmailService:
    def __init__(self, brain=None, notification_callback=None):
        self.brain = brain
        self.notification_callback = notification_callback
        
        try:
            self.client = AgentMail(api_key=CFG.AGENTMAIL_API_KEY)
            self.inbox_id = CFG.AGENTMAIL_INBOX_ID
        except Exception as e:
            logger.error(f"EmailService: Failed to initialize AgentMail client: {e}")
            self.client = None

    async def check_and_reply(self):
        """
        Background task to scan for unread replies and handle them.
        """
        if not self.client or not self.inbox_id:
            logger.error("EmailService: Client or inbox_id not configured.")
            return

        try:
            logger.info("EmailService: Checking for unread emails via SDK...")
            
            # 1. Search for unread messages
            try:
                response = self.client.inboxes.messages.list(
                    inbox_id=self.inbox_id, 
                    labels=["unread"]
                )
                search_results = response.messages if hasattr(response, 'messages') else []
            except Exception as e:
                logger.error(f"EmailService: Failed to list expected messages: {e}")
                return
            
            if not search_results:
                logger.debug("EmailService: No unread emails found.")
                return

            for msg in search_results:
                msg_id = msg.message_id
                thread_id = msg.thread_id
                subject = msg.subject or "No Subject"
                sender = msg.from_ or "Unknown Sender"
                
                # 2. Verify if this is a thread RAMBOT should handle
                is_rambot_thread = False
                
                master_email = CFG.USER_EMAIL
                try:
                    p_resp = requests.get("http://127.0.0.1:8000/user/profile", timeout=5)
                    if p_resp.status_code == 200:
                        master_email = p_resp.json().get("email", CFG.USER_EMAIL)
                except Exception:
                    pass

                if sender == master_email:
                    is_rambot_thread = True
                
                if not is_rambot_thread and "rambot" in subject.lower():
                    is_rambot_thread = True
                
                if getattr(CFG, "MAIL_PROVIDER", "agentmail") == "agentmail":
                    is_rambot_thread = True
                
                if not is_rambot_thread:
                    logger.info(f"EmailService: New human email from {sender}. Notifying user.")
                    if self.notification_callback:
                        self.notification_callback(f"Sir, you have a new email from {sender}: \"{subject}\".")
                    
                    # Mark as handled so we don't process it again next loop
                    self.client.inboxes.messages.update(
                        inbox_id=self.inbox_id,
                        message_id=msg_id,
                        remove_labels=["unread"]
                    )
                    continue

                # 4. Fetch full thread history for context
                try:
                    thread_data = self.client.inboxes.threads.get(
                        inbox_id=self.inbox_id, 
                        thread_id=thread_id
                    )
                    all_msgs = thread_data.messages if hasattr(thread_data, 'messages') else [msg]
                except ApiError as e:
                    logger.warning(f"EmailService: Could not fetch thread details: {e}")
                    all_msgs = [msg]

                logger.info(f"EmailService: Sending thread {thread_id} to Gateway...")
                
                history_text_lines = []
                for m in all_msgs:
                    m_sender = m.from_ or 'Unknown'
                    m_body = m.text or ''
                    history_text_lines.append(f"{m_sender}: {m_body}")
                    
                history_text = "\n".join(history_text_lines)
                
                chat_payload = {
                    "message": f"## EMAIL THREAD HISTORY:\n{history_text}\n\nSubject: {subject}",
                    "sender": sender
                }
                
                try:
                    resp = requests.post("http://127.0.0.1:8000/chat", json=chat_payload, timeout=60)
                    if resp.status_code != 200:
                        logger.error(f"EmailService: Gateway error {resp.status_code}")
                        continue
                        
                    # Split NDJSON lines and parse the last complete JSON update
                    lines = [line.strip() for line in resp.text.split('\n') if line.strip()]
                    if not lines:
                        logger.warning(f"EmailService: Empty response from Gateway for {msg_id}")
                        continue
                    
                    brain_response = json.loads(lines[-1])
                    reply_body = brain_response.get("reply")
                except Exception as e:
                    logger.error(f"EmailService: Failed to contact Gateway or parse response: {e}")
                    reply_body = "I'm sorry, I'm having trouble connecting to my central brain right now."
                    continue

                if not reply_body:
                    logger.warning(f"EmailService: No reply from Gateway for {msg_id}")
                    continue
                
                # 6. Send Reply
                try:
                    self.client.inboxes.messages.reply(
                        inbox_id=self.inbox_id,
                        message_id=msg_id,
                        text=reply_body
                    )
                except Exception as e:
                    logger.error(f"EmailService: Failed to send reply: {e}")
                    continue
                
                # 7. Update status to remove from queue
                try:
                    self.client.inboxes.messages.update(
                        inbox_id=self.inbox_id,
                        message_id=msg_id,
                        add_labels=["replied"],
                        remove_labels=["unread"]
                    )
                except Exception as e:
                    logger.error(f"EmailService: Failed to update message labels: {e}")
                
                logger.info(f"EmailService: Replied to thread {thread_id} and marked as read.")

                if self.notification_callback:
                    self.notification_callback(f"RAMBOT: Auto-replied to {sender} regarding '{subject}'.")

        except Exception as e:
            logger.error(f"EmailService: Error in check_and_reply: {e}")

    async def send_email(self, to: str, subject: str, text: str, html: str = None):
        """
        Sends an email using AgentMail.
        """
        if not self.client or not self.inbox_id:
            logger.error("EmailService: Client or inbox_id not configured. Cannot send email.")
            return False

        try:
            logger.info(f"EmailService: Sending email to {to} with subject '{subject}'")
            self.client.inboxes.messages.send(
                inbox_id=self.inbox_id,
                to=[to],
                subject=subject,
                text=text,
                html=html
            )
            logger.info("EmailService: Email sent successfully.")
            return True
        except Exception as e:
            logger.error(f"EmailService: Failed to send email: {e}")
            return False
