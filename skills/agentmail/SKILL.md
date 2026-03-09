---
name: agentmail
description: Specialized skill for managing AI-native email inboxes using AgentMail. Use this skill when you need to (1) Search or list messages, (2) Read email threads, (3) Send new emails or replies, or (4) Mark emails as read/unread.
---

# AgentMail Skill

This skill allows you to manage emails through the AgentMail API.

## Usage Guide

To use this skill, you MUST run the Python scripts located in `scripts/`. These scripts handle interaction with the AgentMail SDK using the credentials configured in `config/config.py`.

### 1. Search/List Messages
Run `scripts/search_messages.py` to find emails.
- **Arguments**: `--query` (e.g., "is:unread", "ALL")
- **Example**: `python skills/agentmail/scripts/search_messages.py --query "is:unread"`

### 2. Get Thread History
Run `scripts/get_thread.py` to retrieve the full history of a conversation.
- **Arguments**: `--thread_id` (The ID returned from search)
- **Example**: `python skills/agentmail/scripts/get_thread.py --thread_id "msg_123"`

### 3. Send/Reply to Email
Run `scripts/send_message.py` to send a message.
- **Arguments**: 
    - `--to` (Recipient email)
    - `--subject` (Subject line)
    - `--message` (Body text)
    - `--thread_id` (Optional: specify to reply to an existing thread)
- **Example**: `python skills/agentmail/scripts/send_message.py --to "user@example.com" --subject "Hello" --message "This is Rambot"`

### 4. Update Status
Run `scripts/update_status.py` to change message state.
- **Arguments**:
    - `--message_id` (The message ID)
    - `--status` (e.g., "read", "unread")
- **Example**: `python skills/agentmail/scripts/update_status.py --message_id "msg_123" --status "read"`
