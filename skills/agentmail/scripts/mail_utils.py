from typing import List, Dict, Any, Optional
import sys
import os

# Add project root to path to access config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from config.config import CFG
from loguru import logger
from email.utils import parseaddr
import asyncio

try:
    from agentmail import AgentMail
except ImportError:
    AgentMail = None

def get_agentmail_client():
    """Initialize AgentMail client."""
    if not AgentMail or not getattr(CFG, 'AGENTMAIL_API_KEY', None):
        return None
    try:
        return AgentMail(api_key=CFG.AGENTMAIL_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize AgentMail client: {e}")
        return None

async def search_mail(query: str) -> List[Dict[str, Any]]:
    client = get_agentmail_client()
    if not client:
        return []
    try:
        inbox_id = getattr(CFG, 'AGENTMAIL_INBOX_ID', None)
        if inbox_id:
            response = client.inboxes.messages.list(inbox_id=inbox_id)
        else:
            inboxes_resp = client.inboxes.list()
            inboxes_list = getattr(inboxes_resp, 'inboxes', [])
            if not inboxes_list:
                return []
            response = client.inboxes.messages.list(inbox_id=inboxes_list[0].id)
        
        messages = []
        msg_list = getattr(response, 'messages', [])
        for msg in msg_list:
            if "is:unread" in query.lower() and msg.status != "unread":
                continue
            messages.append({
                "id": msg.id,
                "threadId": msg.thread_id or msg.id,
                "snippet": msg.snippet or (msg.body[:100] if msg.body else ""),
                "subject": msg.subject or "No Subject",
                "sender": msg.sender_email
            })
        return messages
    except Exception as e:
        logger.error(f"AgentMail search failed: {e}")
        return []

async def get_mail_thread(thread_id: str) -> Dict[str, Any]:
    client = get_agentmail_client()
    if not client:
        return {}
    try:
        # First try to get it as a thread if the user passed a thread_id
        try:
            thread = client.threads.get(thread_id=thread_id)
            msg_list = getattr(thread, 'messages', [])
        except Exception:
            # If that fails, maybe it's a message_id. Use search or list to find its thread.
            inbox_id = getattr(CFG, 'AGENTMAIL_INBOX_ID', None)
            if not inbox_id:
                inboxes_resp = client.inboxes.list()
                inboxes_list = getattr(inboxes_resp, 'inboxes', [])
                if inboxes_list:
                    inbox_id = inboxes_list[0].id
            
            if not inbox_id:
                return {}
            
            msg = client.inboxes.messages.get(inbox_id=inbox_id, message_id=thread_id)
            if msg.thread_id:
                thread = client.threads.get(thread_id=msg.thread_id)
                msg_list = getattr(thread, 'messages', [])
            else:
                msg_list = [msg]

        messages = []
        for t_msg in msg_list:
            messages.append({
                "id": getattr(t_msg, 'message_id', t_msg.id),
                "body": t_msg.text or t_msg.html,
                "sender": getattr(t_msg, 'from_', t_msg.sender_email if hasattr(t_msg, 'sender_email') else "Unknown"),
                "subject": t_msg.subject,
                "snippet": t_msg.preview or t_msg.snippet or ((t_msg.text or t_msg.html)[:100] if (t_msg.text or t_msg.html) else "")
            })
        return {"messages": messages}
    except Exception as e:
        logger.error(f"AgentMail get_thread failed: {e}")
        return {}

async def send_mail_message(message: str, to: str, subject: str, thread_id: Optional[str] = None) -> str:
    name, addr = parseaddr(to)
    if not addr or '@' not in addr:
        import re
        matches = re.findall(r'[\w\.-]+@[\w\.-]+', to)
        if matches:
            addr = matches[0]
        else:
            return f"Error: Invalid recipient address '{to}'."

    client = get_agentmail_client()
    if not client:
        return "Error: AgentMail client not initialized. Please check AGENTMAIL_API_KEY."
    
    try:
        inbox_id = getattr(CFG, 'AGENTMAIL_INBOX_ID', None)
        if not inbox_id:
            inboxes_resp = client.inboxes.list()
            inboxes_list = getattr(inboxes_resp, 'inboxes', [])
            if inboxes_list:
                inbox_id = inboxes_list[0].id
        if not inbox_id:
            return "No AgentMail inbox found."

        if thread_id:
            client.inboxes.messages.reply(
                inbox_id=inbox_id,
                message_id=thread_id,
                text=message
            )
        else:
            client.inboxes.messages.send(
                inbox_id=inbox_id,
                to=addr,
                subject=subject,
                text=message
            )
        return "Email sent successfully via AgentMail"
    except Exception as e:
        logger.error(f"AgentMail send failed: {e}")
        return f"Error: {str(e)}"

async def update_mail_state(message_id: str, add_label_ids: List[str] = [], remove_label_ids: List[str] = []) -> str:
    client = get_agentmail_client()
    if not client:
        return "Failed to connect to AgentMail"
    try:
        inbox_id = getattr(CFG, 'AGENTMAIL_INBOX_ID', None)
        if not inbox_id:
            inboxes_resp = client.inboxes.list()
            inboxes_list = getattr(inboxes_resp, 'inboxes', [])
            if inboxes_list:
                inbox_id = inboxes_list[0].id
        
        if not inbox_id:
            return "No inbox found"

        if "UNREAD" in (remove_label_ids or []):
            client.inboxes.messages.update(inbox_id=inbox_id, message_id=message_id, status="read")
        return "State updated successfully"
    except Exception as e:
        logger.error(f"AgentMail update error: {e}")
        return f"Error: {e}"
