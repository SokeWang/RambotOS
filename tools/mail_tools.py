import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
from typing import List, Dict, Any, Optional
from langchain.tools import tool
from config.config import CFG
from loguru import logger

def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value

def get_imap_conn():
    try:
        mail = imaplib.IMAP4_SSL(CFG.IMAP_SERVER, CFG.IMAP_PORT)
        mail.login(CFG.MAIL_163_USER, CFG.MAIL_163_PASS)
        # Netease often requires the ID command to avoid "Unsafe Login" error
        try:
            mail.xatom('ID', '("name" "RAMBOT" "version" "1.0.0" "vendor" "test")')
        except Exception as e_id:
            logger.warning(f"IMAP ID command failed: {e_id}")
        return mail
    except Exception as e:
        logger.error(f"IMAP Login Failed: {e}")
        return None

def get_smtp_conn():
    try:
        smtp = smtplib.SMTP_SSL(CFG.SMTP_SERVER, CFG.SMTP_PORT)
        smtp.login(CFG.MAIL_163_USER, CFG.MAIL_163_PASS)
        return smtp
    except Exception as e:
        logger.error(f"SMTP Login Failed: {e}")
        return None

@tool
def search_163_mail(query: str) -> List[Dict[str, Any]]:
    """
    Search for emails in 163 Mail. 
    Query can be 'UNSEEN' to find unread emails.
    Returns a list of message summaries.
    """
    mail = get_imap_conn()
    if not mail:
        return []
    
    try:
        res, _ = mail.select("INBOX")
        if res != "OK":
            logger.error(f"Failed to select INBOX: {res}")
            return []
        
        # Map some common Gmail-style queries to IMAP
        imap_query = "ALL"
        if "is:unread" in query.lower() or "UNSEEN" in query.upper():
            imap_query = "UNSEEN"
        
        status, response = mail.search(None, imap_query)
        if status != "OK":
            return []
        
        messages = []
        msg_ids = response[0].split()
        # Limit to last 10 for performance if needed
        for msg_id in msg_ids[-10:]:
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = decode_str(msg.get("Subject", "No Subject"))
            sender = decode_str(msg.get("From", "Unknown Sender"))
            
            messages.append({
                "id": msg_id.decode(),
                "threadId": msg_id.decode(), # IMAP doesn't have threadId, use msg_id
                "snippet": subject,
                "subject": subject,
                "sender": sender
            })
        
        return messages
    finally:
        mail.logout()

@tool
def get_163_mail_thread(thread_id: str) -> Dict[str, Any]:
    """
    Retrieve an email thread (or single message for IMAP) from 163 Mail.
    """
    mail = get_imap_conn()
    if not mail:
        return {}
    
    try:
        res, _ = mail.select("INBOX")
        if res != "OK":
            logger.error(f"Failed to select INBOX: {res}")
            return {}
        
        status, msg_data = mail.fetch(thread_id, "(RFC822)")
        if status != "OK":
            return {}
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
            
        subject = decode_str(msg.get("Subject", "No Subject"))
        sender = decode_str(msg.get("From", "Unknown Sender"))
        
        return {
            "messages": [{
                "id": thread_id,
                "body": body,
                "sender": sender,
                "subject": subject,
                "snippet": body[:100],
                "headers": [{"name": "Subject", "value": subject}]
            }]
        }
    finally:
        mail.logout()

@tool
def send_163_mail_message(message: str, to: str, subject: str, thread_id: Optional[str] = None) -> str:
    """
    Send an email via 163 Mail.
    """
    smtp = get_smtp_conn()
    if not smtp:
        return "Failed to connect to SMTP server"
    
    try:
        msg = MIMEText(message, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = CFG.MAIL_163_USER
        msg['To'] = to
        
        # If thread_id is provided, we could try to add In-Reply-To header
        # but for now we keep it simple.
        
        smtp.send_message(msg)
        return "Email sent successfully"
    finally:
        smtp.quit()

@tool
def update_163_mail_state(message_id: str, add_label_ids: List[str] = [], remove_label_ids: List[str] = []) -> str:
    """
    Update email state (e.g., mark as read).
    """
    mail = get_imap_conn()
    if not mail:
        return "Failed to connect to IMAP server"
    
    try:
        res, _ = mail.select("INBOX")
        if res != "OK":
            logger.error(f"Failed to select INBOX: {res}")
            return "Failed to select INBOX"
            
        if "UNREAD" in remove_label_ids:
            mail.store(message_id, '+FLAGS', r'\Seen')
        return "State updated"
    finally:
        mail.logout()
