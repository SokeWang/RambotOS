import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import asyncio
import time
import json
from collections import deque
from loguru import logger

from agents.langchain_agent import LangchainBrain
from services.media_processor import MediaProcessor
from core.history import History
from core.memory import MemoryManager, memory_manager
from services.user_service import user_service, UserService
from services.session_service import session_service, SessionService

# Configuration
PORT = 8000
HOST = "127.0.0.1"

app = FastAPI(title="Rambot Core Service")

# Dependency Injection Helpers
def get_user_service():
    return user_service

def get_session_service():
    return session_service

def get_memory_manager():
    return memory_manager

# Models
class MonitorRegister(BaseModel):
    name: str
    pid: int
    interval: Optional[int] = 300
    label: Optional[str] = None
    sublabel: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

class MonitorStatus(BaseModel):
    name: str
    status: str  # "running", "stopped", "error"
    pid: Optional[int] = None
    last_ping: float
    uptime: float
    label: Optional[str] = None
    sublabel: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

class Notification(BaseModel):
    source: str
    message: str
    level: str = "info" # info, warning, error

class ChatRequest(BaseModel):
    message: Optional[str] = None
    sender: Optional[str] = None # e.g. email address or "os_user"
    attachment_base64: Optional[str] = None
    webcam_base64: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str = "master"
    email: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    name: Optional[str] = "Master"

# In-memory State
monitors: Dict[str, dict] = {}
notifications: deque = deque(maxlen=50)  # Auto-capped at 50, O(1) append

# Central Gateway Brain
brain = LangchainBrain()

@app.on_event("startup")
async def startup_event():
    logger.info("Core: Initializing central LangchainBrain...")
    await brain.initialize()
    logger.info("Core: Central brain is ready.")

@app.get("/")
async def root():
    return {"status": "Rambot Core is active", "time": time.time()}

# --- Monitor Management ---

@app.post("/monitor/register")
async def register_monitor(reg: MonitorRegister):
    monitors[reg.name] = {
        "pid": reg.pid,
        "interval": reg.interval,
        "last_ping": time.time(),
        "start_time": time.time(),
        "status": "running",
        "label": reg.label,
        "sublabel": reg.sublabel,
        "icon": reg.icon,
        "color": reg.color
    }
    logger.info(f"Core: Registered monitor '{reg.name}' (PID: {reg.pid}) with label '{reg.label}'")
    return {"status": "success", "monitor": reg.name}

@app.get("/monitor/status")
async def get_all_status():
    status_list = []
    now = time.time()
    for name, data in monitors.items():
        # Calculate dynamic status
        timeout = (data.get("interval") or 300) * 2
        is_timeout = (now - data["last_ping"] > timeout)
        
        # Determine reported status
        current_status = data["status"]
        if is_timeout and current_status == "running":
            current_status = "stopped"
            
        status_list.append(MonitorStatus(
            name=name,
            status=current_status,
            pid=data.get("pid"),
            last_ping=data["last_ping"],
            uptime=now - data["start_time"] if current_status == "running" else 0,
            label=data.get("label"),
            sublabel=data.get("sublabel"),
            icon=data.get("icon"),
            color=data.get("color")
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

# --- Notifications ---

@app.post("/notify")
async def push_notification(notif: Notification):
    logger.info(f"Core: Received notification from {notif.source}: {notif.message}")
    notif_data = notif.dict()
    notif_data["timestamp"] = time.time()
    notifications.append(notif_data)  # deque auto-evicts oldest when full
    return {"status": "received"}

@app.get("/notifications")
async def get_notifications(since: float = 0):
    """Get new notifications since a specific timestamp."""
    return [n for n in notifications if n["timestamp"] > since]

# --- Chat Gateway ---

@app.post("/chat")
async def chat_with_gateway(req: ChatRequest, session_svc: SessionService = Depends(get_session_service)):
    """
    Centralized chat gateway with Unified Session Mapping.
    """
    sender_id = req.sender or "unknown"
    logger.info(f"Core: Received chat request from {sender_id}")
    
    # 1. Resolve Unified Session
    session_record = await session_svc.get_session_for_sender(sender_id)
    session_id = session_record.get("session_id", "global")
    user_name = session_record.get("name", "Guest")
    is_master = (session_id == "master")
    
    logger.info(f"Core: Mapped {sender_id} -> Session: {session_id} ({user_name})")
    
    # 2. Context Preparation
    inputs = MediaProcessor.parse_multimodal_input(
        req.message, 
        req.attachment_base64, 
        req.webcam_base64
    )
    
    if not inputs:
        return {"reply": "I couldn't hear you.", "tool_calls": []}

    async def event_generator():
        try:
            # Pass session_id and user_name to brain
            async for response in brain.run(inputs, is_master=is_master, session_id=session_id, user_name=user_name):
                if response.get("gen_ui"):
                    logger.info(f"Core: GenUI detected: {json.dumps(response.get('gen_ui'))}")
                yield json.dumps(response) + "\n"
        except Exception as e:
            logger.error(f"Core: Brain failed: {e}")
            yield json.dumps({"reply": f"Internal Error: {e}", "tool_calls": []}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

# --- Session Management ---

@app.get("/session/list")
async def list_sessions(session_svc: SessionService = Depends(get_session_service)):
    """Fetch all unified sessions and their linked identifiers."""
    return await session_svc.list_sessions()

@app.post("/session/link")
async def link_id_to_session(session_id: str, identifier: str, session_svc: SessionService = Depends(get_session_service)):
    """Manually link an identifier (Email/TG) to an existing session."""
    if await session_svc.link_identifier(session_id, identifier):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Session not found")

# --- History & Memory ---

@app.get("/history")
async def get_chat_history(session_id: str = "os_user", limit: int = 20, offset: int = 0, session_svc: SessionService = Depends(get_session_service)):
    """Fetch chat history from the central store for a specific session."""
    # Resolve unified session if sender_id is provided as session_id
    session_record = await session_svc.get_session_for_sender(session_id)
    actual_session_id = session_record.get("session_id", session_id)
    
    logger.debug(f"Core: Fetching history for {session_id} -> Actual Session: {actual_session_id}, Offset: {offset}")
    history_manager = History(session_id=actual_session_id, checkpointer=brain.checkpointer)
    return await history_manager.get(limit=limit, skip=offset, with_time=True)

@app.get("/memory")
async def get_long_term_memory(limit: int = 100, mem: MemoryManager = Depends(get_memory_manager)):
    """Fetch all memories from the central store."""
    return mem.get_all_memories()

@app.delete("/memory/{memory_id}")
async def delete_memory_item(memory_id: str, mem: MemoryManager = Depends(get_memory_manager)):
    """Delete a memory item by ID."""
    try:
        mem.collection.delete(ids=[memory_id])
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Core: Failed to delete memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- User Profile Management ---

@app.post("/user/bind")
async def bind_user_profile(profile: UserProfile, user_svc: UserService = Depends(get_user_service)):
    """Save or update user identity binding."""
    update_data = profile.dict(exclude_unset=True, exclude={"user_id"})
    if await user_svc.bind_user(profile.user_id, update_data):
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to bind user")

@app.get("/user/profile")
async def get_user_profile(user_id: str, user_svc: UserService = Depends(get_user_service)):
    """Fetch a specific user profile and identify if it's the master."""
    user = await user_svc.get_user_profile(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/user/guests")
async def list_guest_profiles(user_svc: UserService = Depends(get_user_service)):
    """Fetch all guest profiles (everyone except 'master')."""
    return await user_svc.list_guests()

if __name__ == "__main__":
    import sys
    import os
    if getattr(sys, 'frozen', False):
        os.chdir(sys._MEIPASS)
        
    logger.info(f"Starting Rambot Core on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
