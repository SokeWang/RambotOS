import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header, Header
from email.utils import parseaddr, formataddr
from typing import List, Dict, Any, Optional
from langchain.tools import tool
from config.config import CFG
from loguru import logger

def decode_str(s):
    if s is None:
        return ""
    parts = decode_header(s)
    decoded_parts = []
    for value, charset in parts:
        if charset:
            if charset == 'gbk': charset = 'gb18030'
            try:
                decoded_parts.append(value.decode(charset))
            except:
                decoded_parts.append(str(value))
        elif isinstance(value, bytes):
            decoded_parts.append(value.decode('utf-8', errors='replace'))
        else:
            decoded_parts.append(str(value))
    return "".join(decoded_parts)

def get_imap_conn():
    """Generic IMAP connection based on config."""
    try:
        mail = imaplib.IMAP4_SSL(CFG.IMAP_SERVER, CFG.IMAP_PORT)
        mail.login(CFG.MAIL_USER, CFG.MAIL_PASS)
        
        # 163/Netease specific ID command
        if CFG.MAIL_PROVIDER == "163" or "163.com" in CFG.IMAP_SERVER:
            try:
                mail.xatom('ID', '("name" "RAMBOT" "version" "1.0.0" "vendor" "test")')
            except Exception as e_id:
                logger.warning(f"IMAP ID command failed: {e_id}")
        
        return mail
    except Exception as e:
        logger.error(f"IMAP Login Failed for {CFG.MAIL_USER} on {CFG.IMAP_SERVER}: {e}")
        return None

def get_smtp_conn():
    """Generic SMTP connection based on config."""
    try:
        smtp = smtplib.SMTP_SSL(CFG.SMTP_SERVER, CFG.SMTP_PORT)
        smtp.login(CFG.MAIL_USER, CFG.MAIL_PASS)
        return smtp
    except Exception as e:
        logger.error(f"SMTP Login Failed for {CFG.MAIL_USER} on {CFG.SMTP_SERVER}: {e}")
        return None

@tool
def search_mail(query: str) -> List[Dict[str, Any]]:
    """
    Search for emails in the configured mailbox. 
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
        
        imap_query = "ALL"
        if "is:unread" in query.lower() or "UNSEEN" in query.upper():
            imap_query = "UNSEEN"
        
        status, response = mail.search(None, imap_query)
        if status != "OK":
            return []
        
        messages = []
        msg_ids = response[0].split()
        # Limit to last 10 for performance
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
                "threadId": msg_id.decode(), 
                "snippet": subject,
                "subject": subject,
                "sender": sender
            })
        
        return messages
    finally:
        try:
            mail.logout()
        except:
            pass

@tool
def get_mail_thread(thread_id: str) -> Dict[str, Any]:
    """
    Retrieve an email thread (or single message) from the configured mailbox.
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
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                    except:
                        body = str(part.get_payload(decode=True))
                    break
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
            except:
                body = str(msg.get_payload(decode=True))
            
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
        try:
            mail.logout()
        except:
            pass

@tool
def send_mail_message(message: str, to: str, subject: str, thread_id: Optional[str] = None) -> str:
    """
    Send an email via the configured provider.
    Handles non-ASCII name encoding for servers without SMTPUTF8 support (like 163).
    """
    logger.info(f"MailTools: Attempting to send mail to '{to}' with subject '{subject}'")
    
    name, addr = parseaddr(to)
    # If parseaddr failed to find an '@', the whole thing might be an unquoted name
    if not addr or '@' not in addr:
        logger.warning(f"MailTools: No valid email address found in '{to}'. Attempting to extract from any bracketed text.")
        import re
        matches = re.findall(r'[\w\.-]+@[\w\.-]+', to)
        if matches:
            addr = matches[0]
            name = to.replace(addr, "").replace("<", "").replace(">", "").strip()
        else:
            return f"Error: Invalid recipient address '{to}'. No email address found."

    smtp = get_smtp_conn()
    if not smtp:
        return "Failed to connect to SMTP server"
    
    try:
        # 1. Prepare message body
        msg = MIMEText(message, 'plain', 'utf-8')
        
        # 2. Encode Headers explicitly to ASCII-safe format (RFC 2047)
        msg['Subject'] = Header(subject, 'utf-8').encode()
        msg['From'] = CFG.MAIL_USER
        
        logger.debug(f"MailTools: Final envelope addr='{addr}', name='{name}'")
        
        if name:
            encoded_name = Header(name, 'utf-8').encode()
            msg['To'] = formataddr((encoded_name, addr))
        else:
            msg['To'] = addr
        
        # 3. Use sendmail with ASCII-only envelope
        # We MUST ensure from_addr and to_addrs are strictly ASCII
        from_addr_ascii = str(CFG.MAIL_USER).encode('ascii', 'ignore').decode()
        to_addr_ascii = str(addr).encode('ascii', 'ignore').decode()
        
        payload = msg.as_string()
        
        try:
            smtp.sendmail(from_addr_ascii, [to_addr_ascii], payload)
        except Exception as e_send:
            logger.warning(f"MailTools: sendmail failed ({e_send}), trying reset and bytes...")
            smtp.ehlo() # Reset connection state
            smtp.sendmail(from_addr_ascii, [to_addr_ascii], msg.as_bytes())
            
        return f"Email sent successfully via {CFG.MAIL_PROVIDER}"
    except Exception as e:
        logger.error(f"MailTools: Send failed: {e}")
        return f"Error: SMTP Send failed: {str(e)}"
    finally:
        try:
            smtp.quit()
        except:
            pass

@tool
def update_mail_state(message_id: str, add_label_ids: List[str] = [], remove_label_ids: List[str] = []) -> str:
    """
    Update email state (e.g., mark as read).
    """
    mail = get_imap_conn()
    if not mail:
        return "Failed to connect to IMAP server"
    
    try:
        res, _ = mail.select("INBOX")
        if res != "OK":
            return "Failed to select INBOX"
            
        if "UNREAD" in (remove_label_ids or []):
            mail.store(message_id, '+FLAGS', r'\Seen')
        return "State updated successfully"
    finally:
        try:
            mail.logout()
        except:
            pass

# Aliases for backward compatibility if needed by hardcoded agents
search_163_mail = search_mail
get_163_mail_thread = get_mail_thread
send_163_mail_message = send_mail_message
update_163_mail_state = update_mail_state
