---
name: task-scheduler
description: Create and manage background scheduled tasks that trigger actions at specific times.
---

# Task Scheduler Skill

This skill allows you (Rambot) to create and manage background scheduled tasks. RambotOS features a central `SchedulerService` built on APScheduler that dynamically loads tasks from the `tasks/` directory in the project root.

## How Scheduled Tasks Work in RambotOS

When the user asks you to schedule a recurring task (e.g., "每天早上 10 点为我播报早间新闻" or "每天下午 3 点提醒我喝水"):
1. **Discuss the Architecture**: Confirm the task logic, the scheduled time, and what action should happen (email vs local notification).
2. **Write the Script**: You MUST use the `write_to_file` tool to create a new python module inside the `tasks/` folder in the project root (`/Users/wangpeidong/Documents/RambotOS/tasks/{task_name}.py`).
3. **Execution**: The Core `SchedulerService` scans the `tasks/` folder and schedules them automatically. The user can go to the Frontend -> Settings -> Monitors panel to start, stop, or view its status.

## Task Module Template

Every file you create in `tasks/` MUST follow this exact structure to ensure it registers correctly:

```python
from loguru import logger
from config.config import CFG

# APScheduler Trigger arguments
# Common triggers:
# 1. cron: run at specific times (e.g., daily at 10:30 AM)
#    {"trigger": "cron", "hour": 10, "minute": 30}
# 2. interval: run every X seconds/minutes/hours
#    {"trigger": "interval", "minutes": 30}
TRIGGER_ARGS = {
    "trigger": "cron",
    "hour": 10,
    "minute": 0
}

# Optional helper to send UI notification
async def send_notification(message: str):
    import requests
    try:
        requests.post("http://127.0.0.1:8000/notify", json={
            "source": "Scheduled Task",
            "message": message,
            "level": "info"
        })
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

async def execute():
    \"\"\"
    ================================================================
    TODO: IMPLEMENT THE ACTUAL TASK LOGIC HERE
    ================================================================
    \"\"\"
    logger.info("Executing scheduled action!")
    await send_notification("⏰ 任务触发: " + __name__)
    
    # Example to send email:
    # from services.email_service import EmailService
    # email_svc = EmailService(None)
    # await email_svc.send_email(CFG.USER_EMAIL, "Subject", "Body", "<h1>HTML Body</h1>")
```

## How to Delete a Task
To delete a task, you (the AI) can use `run_command` (e.g., `rm tasks/your_task_name_here.py`) to permanently delete it. No additional API calls are needed, it will disappear upon next restart.

## Good Practices
- **NEVER LEAVE THE TASK LOGIC BLANK OR USE PLACEHOLDERS**: You must fully write the implementation code for `execute`.
- Use real libraries to fulfill the user's intent within the `execute` function.
- Catch exceptions securely in `execute` so you can log exactly what failed.
