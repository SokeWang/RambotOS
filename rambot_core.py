import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
import time
import logging
from loguru import logger

# Configuration
PORT = 8000
HOST = "127.0.0.1"

app = FastAPI(title="Rambot Core Service")

# Models
class MonitorRegister(BaseModel):
    name: str
    pid: int
    interval: Optional[int] = 300

class MonitorStatus(BaseModel):
    name: str
    status: str  # "running", "stopped", "error"
    pid: Optional[int] = None
    last_ping: float
    uptime: float

class Notification(BaseModel):
    source: str
    message: str
    level: str = "info" # info, warning, error

# In-memory State
monitors: Dict[str, dict] = {}
notifications: List[dict] = []

@app.get("/")
async def root():
    return {"status": "Rambot Core is active", "time": time.time()}

@app.post("/monitor/register")
async def register_monitor(reg: MonitorRegister):
    monitors[reg.name] = {
        "pid": reg.pid,
        "interval": reg.interval,
        "last_ping": time.time(),
        "start_time": time.time(),
        "status": "running"
    }
    logger.info(f"Core: Registered monitor '{reg.name}' (PID: {reg.pid})")
    return {"status": "success", "monitor": reg.name}

@app.get("/monitor/status")
async def get_all_status():
    status_list = []
    now = time.time()
    for name, data in monitors.items():
        # Auto-timeout monitors that haven't pinged in 2x their interval
        timeout = (data.get("interval") or 300) * 2
        if now - data["last_ping"] > timeout:
            data["status"] = "stopped"
            
        status_list.append(MonitorStatus(
            name=name,
            status=data["status"],
            pid=data.get("pid"),
            last_ping=data["last_ping"],
            uptime=now - data["start_time"] if data["status"] == "running" else 0
        ))
    return status_list

@app.post("/monitor/ping/{name}")
async def ping_monitor(name: str):
    if name in monitors:
        monitors[name]["last_ping"] = time.time()
        monitors[name]["status"] = "running"
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Monitor not found")

@app.post("/monitor/unregister/{name}")
async def unregister_monitor(name: str):
    if name in monitors:
        monitors[name]["status"] = "stopped"
        monitors[name]["last_ping"] = 0 # Force immediate timeout in UI
        logger.info(f"Core: Unregistered monitor '{name}'")
        return {"status": "success"}
    return {"status": "not_found"}

@app.post("/notify")
async def push_notification(notif: Notification):
    logger.info(f"Core: Received notification from {notif.source}: {notif.message}")
    notif_data = notif.dict()
    notif_data["timestamp"] = time.time()
    notifications.append(notif_data)
    # Keep only last 50 notifications
    if len(notifications) > 50:
        notifications.pop(0)
    return {"status": "received"}

@app.get("/notifications")
async def get_notifications(since: float = 0):
    """Get new notifications since a specific timestamp."""
    return [n for n in notifications if n["timestamp"] > since]

if __name__ == "__main__":
    import sys
    import os
    if getattr(sys, 'frozen', False):
        os.chdir(sys._MEIPASS)
        
    logger.info(f"Starting Rambot Core on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
