---
name: agentmail
description: Give AI agents their own email inboxes using the AgentMail API. Use when building email agents, sending/receiving emails programmatically, managing inboxes, handling attachments, organizing with labels, creating drafts for human approval, or setting up real-time notifications via webhooks/websockets. Supports multi-tenant isolation with pods.
---

# AgentMail SDK

AgentMail is an API-first email platform for AI agents. Install the SDK and initialize the client.

## Installation

```bash

# Python
pip install agentmail
```

## Setup

```python
from agentmail import AgentMail
client = AgentMail(api_key="YOUR_API_KEY")
```

## Inboxes

Create scalable inboxes on-demand. Each inbox has a unique email address.

```python
# Create inbox (auto-generated address)
inbox = client.inboxes.create()

# Create with custom username and domain
inbox = client.inboxes.create(username="support", domain="yourdomain.com")

# List, get, delete
inboxes = client.inboxes.list()
inbox = client.inboxes.get(inbox_id="inbox@agentmail.to")
client.inboxes.delete(inbox_id="inbox@agentmail.to")
```

## Messages

Always send both `text` and `html` for best deliverability.

```python
# Send message
client.inboxes.messages.send(
    inbox_id="agent@agentmail.to",
    to="recipient@example.com",
    subject="Hello",
    text="Plain text version",
    html="<p>HTML version</p>",
    labels=["outreach"]
)

# Reply to message
client.inboxes.messages.reply(
    inbox_id="agent@agentmail.to",
    message_id="msg_123",
    text="Thanks for your email!"
)

# List and get messages
messages = client.inboxes.messages.list(inbox_id="agent@agentmail.to")
message = client.inboxes.messages.get(inbox_id="agent@agentmail.to", message_id="msg_123")

# Update labels
client.inboxes.messages.update(
    inbox_id="agent@agentmail.to",
    message_id="msg_123",
    add_labels=["replied"],
    remove_labels=["unreplied"]
)
```

## Threads

Threads group related messages in a conversation.

```python
# List threads (with optional label filter)
threads = client.inboxes.threads.list(inbox_id="agent@agentmail.to", labels=["unreplied"])

# Get thread details
thread = client.inboxes.threads.get(inbox_id="agent@agentmail.to", thread_id="thd_123")

# Org-wide thread listing
all_threads = client.threads.list()
```

## Attachments

Send attachments with Base64 encoding. Retrieve from messages or threads.

```python
import base64

# Send with attachment
content = base64.b64encode(file_bytes).decode()
client.inboxes.messages.send(
    inbox_id="agent@agentmail.to",
    to="recipient@example.com",
    subject="Report",
    text="See attached.",
    attachments=[{"content": content, "filename": "report.pdf", "content_type": "application/pdf"}]
)

# Get attachment
file_data = client.inboxes.messages.get_attachment(
    inbox_id="agent@agentmail.to",
    message_id="msg_123",
    attachment_id="att_456"
)
```

## Drafts

Create drafts for human-in-the-loop approval before sending.

```python
# Create draft
draft = client.inboxes.drafts.create(
    inbox_id="agent@agentmail.to",
    to="recipient@example.com",
    subject="Pending approval",
    text="Draft content"
)

# Send draft (converts to message)
client.inboxes.drafts.send(inbox_id="agent@agentmail.to", draft_id=draft.draft_id)
```

## Pods

Multi-tenant isolation for SaaS platforms. Each customer gets isolated inboxes.

```python
# Create pod for a customer
pod = client.pods.create(client_id="customer_123")

# Create inbox within pod
inbox = client.inboxes.create(pod_id=pod.pod_id)

# List resources scoped to pod
inboxes = client.inboxes.list(pod_id=pod.pod_id)
```

## Idempotency

Use `clientId` for safe retries on create operations.

```python
inbox = client.inboxes.create(client_id="unique-idempotency-key")
# Retrying with same client_id returns the original inbox, not a duplicate
```

## Real-Time Events

For real-time notifications, see the reference files:

- [webhooks.md](references/webhooks.md) - HTTP-based notifications (requires public URL)
- [websockets.md](references/websockets.md) - Persistent connection (no public URL needed)
