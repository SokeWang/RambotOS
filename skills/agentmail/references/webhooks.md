# Webhooks

Webhooks provide real-time HTTP notifications when email events occur. Use webhooks when you have a public URL endpoint.

## When to Use

- Production applications with public endpoints
- Event-driven architectures
- When you need to process events on your server

For local development without a public URL, use [websockets.md](websockets.md) instead.

## Setup

Register a webhook endpoint to receive events.

```python
from agentmail import AgentMail
client = AgentMail(api_key="YOUR_API_KEY")

# Create webhook
webhook = client.webhooks.create(url="https://your-server.com/webhooks")

# List webhooks
webhooks = client.webhooks.list()

# Delete webhook
client.webhooks.delete(webhook_id=webhook.webhook_id)
```

## Event Types

| Event                | Description                           |
| -------------------- | ------------------------------------- |
| `message.received`   | New email received in inbox           |
| `message.sent`       | Email successfully sent               |
| `message.delivered`  | Email delivered to recipient's server |
| `message.bounced`    | Email failed to deliver               |
| `message.complained` | Recipient marked email as spam        |
| `message.rejected`   | Email rejected before sending         |
| `domain.verified`    | Custom domain verification completed  |

## Event Filtering

Subscribe only to events you need:

```python
webhook = client.webhooks.create(
    url="https://your-server.com/webhooks",
    event_types=["message.received", "message.bounced"]
)
```

## Payload Structure

All webhook payloads follow this structure:

```json
{
  "type": "event",
  "event_type": "message.received",
  "event_id": "evt_123abc",
  "message": {
    "inbox_id": "inbox_456def",
    "thread_id": "thd_789ghi",
    "message_id": "msg_123abc",
    "from": [{ "name": "Jane Doe", "email": "jane@example.com" }],
    "to": [{ "name": "Agent", "email": "agent@agentmail.to" }],
    "subject": "Question about my account",
    "text": "Full text body",
    "html": "<html>...</html>",
    "labels": ["received"],
    "attachments": [
      {
        "attachment_id": "att_pqr678",
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "size": 123456
      }
    ],
    "created_at": "2023-10-27T10:00:00Z"
  },
  "thread": {}
}
```

## Handling Webhooks

Your endpoint should:

1. Return `200 OK` immediately
2. Process the payload asynchronously

### Flask (Python)

```python
from flask import Flask, request

app = Flask(__name__)

@app.route("/webhooks", methods=["POST"])
def handle_webhook():
    payload = request.json

    if payload["event_type"] == "message.received":
        # Queue for async processing
        process_email.delay(payload["message"])

    return "OK", 200  # Return immediately
```

## Webhook Verification

Verify webhook signatures to ensure requests are from AgentMail.

### Python

```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route("/webhooks", methods=["POST"])
def handle_webhook():
    signature = request.headers.get("X-AgentMail-Signature")
    if not verify_signature(request.data, signature, WEBHOOK_SECRET):
        return "Invalid signature", 401
    # Process payload...
```

## Local Development

Use ngrok to expose your local server:

```bash
ngrok http 5000
# Use the ngrok URL when creating the webhook
```
