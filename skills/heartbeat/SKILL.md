---
name: Heartbeat Monitoring
description: Control background heartbeat monitors for Email, WhatsApp, etc.
---

# Heartbeat Monitoring Skill

This skill allows Rambot to monitor external platforms in the background.

## Capabilities
- Start/Stop monitoring for specific services.
- Check the status of current monitors.
- Auto-reply to messages (if the specific service supports it, like Email).

## How to use
When the user asks to "monitor my email" or "check if the heartbeats are running", use the following tools:
1. `list_monitors`: To see what services are available and their state.
2. `control_monitor(service_name, action)`:
   - `action='start'`: To begin background monitoring.
   - `action='stop'`: To halt monitoring.
   - `action='status'`: To get details of a specific service.

## Currently Supported Services
- `email`: Scans for replies to Rambot-initiated threads and auto-replies using the Brain's intelligence.

> [!TIP]
> You can ask: "Rambot, 开启邮件心跳监测" or "现在有哪些监控在运行？"
