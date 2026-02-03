import asyncio
from loguru import logger
from tools.mail_tools import search_mail, get_mail_thread, send_mail_message, update_mail_state
from core.chat_prompt import Email_Replier_Prompt
from core.memory import MemoryManager

class EmailService:
    def __init__(self, ultron_brain, notification_callback=None):
        self.brain = ultron_brain
        self.notification_callback = notification_callback
        self.memory = MemoryManager()
        
        # Use Generic Mail Tools
        self.search_tool = search_mail
        self.thread_tool = get_mail_thread
        self.send_tool = send_mail_message
        self.mark_read_tool = update_mail_state
        
        if not all([self.search_tool, self.thread_tool, self.send_tool]):
             logger.warning("EmailService: Some essential 163 Mail tools are missing!")

    async def check_and_reply(self):
        """
        Background task to scan for unread replies and handle them.
        """
        try:
            logger.info("EmailService: Checking for unread emails...")
            # 1. Search for unread messages
            unread_query = "is:unread label:inbox"
            search_results = await self.search_tool.ainvoke({"query": unread_query})
            
            if not search_results or "No messages found" in str(search_results):
                logger.debug("EmailService: No unread emails found.")
                return

            messages = search_results if isinstance(search_results, list) else []
            
            for msg in messages:
                # IMAP uses 'id' for the message/thread reference
                msg_id = msg.get("id")
                subject = msg.get("subject", "No Subject")
                sender = msg.get("sender", "Unknown Sender")
                
                if not msg_id:
                    continue
                
                # 2. Get Thread History
                thread = await self.thread_tool.ainvoke({"thread_id": msg_id})
                if not thread or "messages" not in thread:
                    logger.warning(f"EmailService: Could not fetch thread for {msg_id}")
                    continue
                
                # 3. Verify if this is a thread RAMBOT should handle
                # Rule: RAMBOT signature is present OR subject/body contains 'rambot' (for testing)
                is_rambot_thread = False
                all_msgs = thread.get("messages", [])
                
                # Check if subject says Rambot (Direct hit)
                if "rambot" in subject.lower():
                    is_rambot_thread = True
                
                if not is_rambot_thread:
                    for t_msg in all_msgs:
                        body = (t_msg.get("body") or "").lower()
                        # Signature match OR just mentioning Rambot in a reply
                        if "rambot" in body:
                            is_rambot_thread = True
                            break
                
                if not is_rambot_thread:
                    logger.info(f"EmailService: New human email from {sender}. Notifying user.")
                    if self.notification_callback:
                        self.notification_callback(f"Sir, you have a new email from {sender}: \"{subject}\".")
                    continue

                logger.info(f"EmailService: Processing RAMBOT-active thread {msg_id}...")
                
                # 4. Retrieve Original Intent from Memory
                snippet = all_msgs[0].get("snippet", "")
                semantic_query = f"Email subject: {subject}. Content: {snippet}"
                original_intent_results = self.memory.retrieve_memories(semantic_query, k=1)
                original_intent = original_intent_results[0]["content"] if original_intent_results else "Maintain professional communication on behalf of the user."

                # 5. Generate Reply using BrainAgent
                history_text = "\n".join([f"{m.get('sender', 'Unknown')}: {m.get('body', '')}" for m in all_msgs])
                
                replier_messages = [
                    {"role": "system", "content": Email_Replier_Prompt},
                    {"role": "user", "content": f"## ORIGINAL INTENT:\n{original_intent}\n\n## EMAIL THREAD HISTORY:\n{history_text}\n\nHow should RAMBOT respond to the latest message?"}
                ]
                
                agent = self.brain.brain_manager
                response = await agent.ainvoke({"messages": replier_messages})
                
                # Robustly get the structured response
                structured_response = response.get("structured_response")
                if not structured_response:
                    logger.warning(f"EmailService: Agent failed to provide a structured response for {msg_id}")
                    continue

                # Support both Pydantic object and dict
                def get_val(obj, key, default=None):
                    if hasattr(obj, key): return getattr(obj, key)
                    if isinstance(obj, dict): return obj.get(key, default)
                    return default

                reply_body = get_val(structured_response, 'reply')
                need_ui = get_val(structured_response, 'need_ui', False)

                if not reply_body:
                    logger.warning(f"EmailService: Empty reply generated for {msg_id}")
                    continue
                
                # 6. Send Reply
                last_msg = all_msgs[-1]
                await self.send_tool.ainvoke({
                    "message": reply_body,
                    "to": last_msg.get("sender"),
                    "subject": f"Re: {subject}",
                    "thread_id": msg_id
                })
                
                # 7. Mark as Read
                if self.mark_read_tool:
                    await self.mark_read_tool.ainvoke({
                        "message_id": msg_id,
                        "remove_label_ids": ["UNREAD"]
                    })
                
                logger.info(f"EmailService: Replied to thread {msg_id} and marked as read.")

                # 8. Always Notify user on auto-reply
                if self.notification_callback:
                    notify_msg = f"RAMBOT: Auto-replied to {sender} regarding '{subject}'."
                    if need_ui:
                        notify_msg += " Action required."
                    self.notification_callback(notify_msg)

        except Exception as e:
            logger.error(f"EmailService: Error in check_and_reply: {e}")
