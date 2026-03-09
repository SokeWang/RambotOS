import asyncio
import requests
import json
import os
import shlex
from loguru import logger
from config.config import CFG

class EmailService:
    def __init__(self, brain=None, notification_callback=None):
        self.brain = brain
        self.notification_callback = notification_callback
        self.scripts_path = os.path.join(CFG.SKILLS_PATH, "agentmail/scripts")

    async def _call_script(self, script_name: str, args_dict: dict = None) -> Any:
        """
        Execute a skill script via CLI and return parsed JSON or raw output.
        """
        script_path = os.path.join(self.scripts_path, script_name)
        if not os.path.exists(script_path):
            logger.error(f"EmailService: Script not found at {script_path}")
            return None

        cmd = ["python3", script_path]
        if args_dict:
            for key, value in args_dict.items():
                if value is not None:
                    cmd.append(f"--{key}")
                    cmd.append(str(value))

        try:
            logger.debug(f"EmailService: Executing {' '.join(cmd)}")
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(f"EmailService: Script {script_name} failed with code {proc.returncode}\nStderr: {stderr.decode()}")
                return None

            output = stdout.decode().strip()
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return output
        except Exception as e:
            logger.error(f"EmailService: Error executing script {script_name}: {e}")
            return None

    async def check_and_reply(self):
        """
        Background task to scan for unread replies and handle them by calling scripts.
        """
        try:
            logger.info("EmailService: Checking for unread emails via scripts...")
            
            # 1. Search for unread messages
            search_results = await self._call_script("search_messages.py", {"query": "is:unread label:inbox"})
            
            if not search_results or not isinstance(search_results, list):
                logger.debug("EmailService: No unread emails found or invalid response.")
                return

            for msg in search_results:
                msg_id = msg.get("id")
                subject = msg.get("subject", "No Subject")
                sender = msg.get("sender", "Unknown Sender")
                
                if not msg_id:
                    continue
                
                # 2. Get Thread History
                thread = await self._call_script("get_thread.py", {"thread_id": msg_id})
                if not thread or "messages" not in thread:
                    logger.warning(f"EmailService: Could not fetch thread for {msg_id}")
                    continue
                
                # 3. Verify if this is a thread RAMBOT should handle
                is_rambot_thread = False
                all_msgs = thread.get("messages", [])
                
                master_email = CFG.USER_EMAIL
                try:
                    p_resp = requests.get("http://127.0.0.1:8000/user/profile", timeout=5)
                    if p_resp.status_code == 200:
                        master_email = p_resp.json().get("email", CFG.USER_EMAIL)
                except:
                    pass

                if sender == master_email:
                    is_rambot_thread = True
                
                if not is_rambot_thread and "rambot" in subject.lower():
                    is_rambot_thread = True
                
                if not is_rambot_thread:
                    for t_msg in all_msgs:
                        if "rambot" in (t_msg.get("body") or "").lower():
                            is_rambot_thread = True
                            break
                
                if CFG.MAIL_PROVIDER == "agentmail":
                    is_rambot_thread = True
                
                if not is_rambot_thread:
                    logger.info(f"EmailService: New human email from {sender}. Notifying user.")
                    if self.notification_callback:
                        self.notification_callback(f"Sir, you have a new email from {sender}: \"{subject}\".")
                    continue

                # 4. Delegate to Message Gateway
                logger.info(f"EmailService: Sending thread {msg_id} to Gateway...")
                history_text = "\n".join([f"{m.get('sender', 'Unknown')}: {m.get('body', '')}" for m in all_msgs])
                
                chat_payload = {
                    "message": f"## EMAIL THREAD HISTORY:\n{history_text}\n\nSubject: {subject}",
                    "sender": sender
                }
                
                try:
                    resp = requests.post("http://127.0.0.1:8000/chat", json=chat_payload, timeout=60)
                    if resp.status_code != 200:
                        logger.error(f"EmailService: Gateway error {resp.status_code}")
                        continue
                        
                    brain_response = resp.json()
                    reply_body = brain_response.get("reply")
                except Exception as e:
                    logger.error(f"EmailService: Failed to contact Gateway: {e}")
                    # Special error message if gateway is down
                    reply_body = "I'm sorry, I'm having trouble connecting to my central brain right now."
                    continue

                if not reply_body:
                    logger.warning(f"EmailService: No reply from Gateway for {msg_id}")
                    continue
                
                # 6. Send Reply
                await self._call_script("send_message.py", {
                    "message": reply_body,
                    "to": sender,
                    "subject": f"Re: {subject}",
                    "thread_id": msg_id
                })
                
                # 7. Mark as Read
                await self._call_script("update_status.py", {
                    "message_id": msg_id,
                    "status": "read"
                })
                
                logger.info(f"EmailService: Replied to thread {msg_id} and marked as read.")

                if self.notification_callback:
                    self.notification_callback(f"RAMBOT: Auto-replied to {sender} regarding '{subject}'.")

        except Exception as e:
            logger.error(f"EmailService: Error in check_and_reply: {e}")
