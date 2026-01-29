import asyncio
from loguru import logger
from tools.mail_tools import search_163_mail, get_163_mail_thread, send_163_mail_message, update_163_mail_state
from core.chat_prompt import Email_Replier_Prompt
from core.memory import MemoryManager

class EmailService:
    def __init__(self, ultron_brain, notification_callback=None):
        self.brain = ultron_brain
        self.notification_callback = notification_callback
        self.memory = MemoryManager()
        
        # Use 163 Mail Tools
        self.search_tool = search_163_mail
        self.thread_tool = get_163_mail_thread
        self.send_tool = send_163_mail_message
        self.mark_read_tool = update_163_mail_state
        
        if not all([self.search_tool, self.thread_tool, self.send_tool]):
             logger.warning("EmailService: Some essential 163 Mail tools are missing!")

    async def check_and_reply(self):
        """
        Background task to scan for unread replies and handle them.
        """
        try:
            logger.info("EmailService: Checking for unread emails...")
            # 1. Search for unread messages
            # We look for unread messages that are likely replies (not just new spam)
            # In a real scenario, we might want to filter more specifically
            unread_query = "is:unread label:inbox"
            search_results = await self.search_tool.ainvoke({"query": unread_query})
            
            if not search_results or "No messages found" in str(search_results):
                logger.debug("EmailService: No unread emails found.")
                return

            # search_results might be a string or list depending on the tool's output
            # Usually it's a list of dictionaries if successful
            messages = search_results if isinstance(search_results, list) else []
            
            for msg in messages:
                thread_id = msg.get("threadId")
                if not thread_id:
                    continue
                
                # 2. Get Thread History
                thread = await self.thread_tool.ainvoke({"thread_id": thread_id})
                if not thread or "messages" not in thread:
                    continue
                
                # 3. Verify if this is a thread RAMBOT should handle
                # Rule: RAMBOT signature must be present in at least ONE past msg in the thread
                is_rambot_thread = False
                for t_msg in thread["messages"]:
                    if "— RAMBOT, AI Operating System" in (t_msg.get("body") or ""):
                        is_rambot_thread = True
                        break
                
                if not is_rambot_thread:
                    logger.debug(f"EmailService: Thread {thread_id} is not initiated by RAMBOT, skipping.")
                    continue

                logger.info(f"EmailService: Processing RAMBOT-initiated thread {thread_id}...")
                
                # 4. Retrieve Original Intent from Memory
                # We query memory based on the snippet or thread subject to find WHY this thread exists
                subject = next((h.get("value") for h in thread["messages"][0].get("headers", []) if h.get("name") == "Subject"), "")
                snippet = thread["messages"][0].get("snippet", "")
                
                # Combine subject and first snippet to get a better semantic match for the original goal
                semantic_query = f"Email subject: {subject}. Content: {snippet}"
                original_intent_results = self.memory.retrieve_memories(semantic_query, k=1)
                original_intent = original_intent_results[0]["content"] if original_intent_results else "Maintain professional communication on behalf of the user."

                # 5. Generate Reply using BrainAgent
                # Construct messages for the LLM
                history_text = "\n".join([f"{m.get('sender', 'Unknown')}: {m.get('body', '')}" for m in thread["messages"]])
                
                replier_messages = [
                    {"role": "system", "content": Email_Replier_Prompt},
                    {"role": "user", "content": f"## ORIGINAL INTENT:\n{original_intent}\n\n## EMAIL THREAD HISTORY:\n{history_text}\n\nHow should RAMBOT respond to the latest message?"}
                ]
                
                # We use the agent directly to avoid UI generation
                agent = self.brain.brain_manager.agent
                response = await agent.ainvoke({"messages": replier_messages})
                
                structured_response = response.get("structured_response")
                if not structured_response:
                    continue

                reply_body = structured_response.reply
                
                # 6. Send Reply
                # We need to find the Message-ID of the last message to reply correctly
                last_msg = thread["messages"][-1]
                # In a real app we'd set In-Reply-To and References headers, 
                # but send_gmail_message tool usually handles thread_id for grouping.
                
                await self.send_tool.ainvoke({
                    "message": reply_body,
                    "to": last_msg.get("sender"),
                    "subject": f"Re: {subject}",
                    "thread_id": thread_id
                })
                
                # 7. Mark as Read
                if self.mark_read_tool:
                    await self.mark_read_tool.ainvoke({
                        "message_id": last_msg.get("id"),
                        "add_label_ids": [],
                        "remove_label_ids": ["UNREAD"]
                    })
                
                logger.info(f"EmailService: Replied to thread {thread_id} and marked as read.")

                # 8. Notify user if needed
                if structured_response.need_ui or "contact me directly" in reply_body.lower():
                    if self.notification_callback:
                        self.notification_callback(f"RAMBOT: Auto-replied to an email regarding your job search. Check {subject}.")

        except Exception as e:
            logger.error(f"EmailService: Error in check_and_reply: {e}")
