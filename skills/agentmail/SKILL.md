---
name: agentmail
description: Specialized skill for managing AI-native email inboxes using AgentMail. Use this skill when you need to (1) Search or list messages, (2) Read email threads, (3) Send new emails or replies (with or without attachments), or (4) Mark emails as read/unread.
---

# AgentMail Skill

This skill allows you to manage emails through the AgentMail API, including support for attachments.

## Usage Guide

To use this skill, you MUST run the Python scripts located in `scripts/`. 

### 1. Send Message (with optional attachments)
Run `scripts/send_message.py` to send a message.
- **Arguments**: 
    - `--inbox_id` (The sending inbox)
    - `--to` (Recipient email)
    - `--subject` (Subject line)
    - `--text` (Body text)
    - `--attachments` (Optional: JSON-encoded list of attachments `[{"content": "base64...", "filename": "file.png", "content_type": "image/png"}]`)

### 2. Search/List Messages
Run `scripts/search_messages.py` to find emails.
- **Example**: `python skills/agentmail/scripts/search_messages.py --query "is:unread"`

### 3. Get Thread History
Run `scripts/get_thread.py` to retrieve the full history of a conversation.
- **Example**: `python skills/agentmail/scripts/get_thread.py --thread_id "thd_123"`

### 4. Update Status
Run `scripts/update_status.py` to change message state.
- **Example**: `python skills/agentmail/scripts/update_status.py --message_id "msg_123" --status "read"`
