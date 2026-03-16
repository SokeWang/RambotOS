import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import asyncio
from fastapi.middleware.cors import CORSMiddleware
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
from services.monitor_manager import monitor_manager

# Configuration
PORT = 8000
HOST = "127.0.0.1"

app = FastAPI(title="Rambot Core Service")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class SkillCreate(BaseModel):
    name: str
    description: str

class SkillUpdate(BaseModel):
    name: str
    description: str

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
    status_dict = {}
    now = time.time()
    for name, data in monitors.items():
        # Calculate dynamic status
        timeout = (data.get("interval") or 300) * 2
        is_timeout = (now - data["last_ping"] > timeout)
        
        # Determine reported status
        current_status = data["status"]
        if is_timeout and current_status == "running":
            current_status = "stopped"
            
        status_dict[name] = {
            "name": name,
            "status": current_status,
            "pid": data.get("pid"),
            "last_ping": data["last_ping"],
            "uptime": now - data["start_time"] if current_status == "running" else 0,
            "label": data.get("label"),
            "sublabel": data.get("sublabel"),
            "icon": data.get("icon"),
            "color": data.get("color")
        }
        
    scripts = monitor_manager._discover_scripts()
    for script_name in scripts:
        if script_name not in status_dict:
            status_dict[script_name] = {
                "name": script_name,
                "status": "stopped",
                "label": script_name.capitalize(),
                "sublabel": f"{script_name.upper()} Service",
                "uptime": 0
            }
            
    return status_dict

@app.post("/monitor/toggle/{name}")
async def toggle_monitor_endpoint(name: str, enable: bool):
    def unregister_callback(n):
        if n in monitors:
            monitors[n]["status"] = "stopped"
            monitors[n]["last_ping"] = 0
            
    success = monitor_manager.toggle_monitor(name, enable, unregister_callback)
    if success:
        if enable:
            if name not in monitors:
                monitors[name] = {"status": "starting", "last_ping": time.time(), "start_time": time.time()}
            else:
                monitors[name]["status"] = "running"
        else:
            if name in monitors:
                monitors[name]["status"] = "stopped"
    return {"status": "success" if success else "failed"}

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

# --- Skill Management ---

def get_skills_dir():
    import sys, os
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "skills")

@app.get("/skills")
async def get_skills():
    import os, re
    skills_dir = get_skills_dir()
    if not os.path.exists(skills_dir):
        return []
    
    skills = []
    for item in os.listdir(skills_dir):
        path = os.path.join(skills_dir, item)
        if os.path.isdir(path):
            skill_md = os.path.join(path, "SKILL.md")
            skill_data = {"id": item, "name": item, "description": "", "path": path}
            if os.path.exists(skill_md):
                try:
                    with open(skill_md, 'r', encoding='utf-8') as f:
                        content = f.read()
                        name_match = re.search(r'^name:\s*(.*)$', content, re.MULTILINE)
                        desc_match = re.search(r'^description:\s*(.*)$', content, re.MULTILINE)
                        if name_match: skill_data["name"] = name_match.group(1).strip()
                        if desc_match: skill_data["description"] = desc_match.group(1).strip()
                except Exception as e:
                    logger.error(f"Error reading {skill_md}: {e}")
            skills.append(skill_data)
    return skills

@app.post("/skills")
async def create_skill(skill: SkillCreate):
    import os
    skills_dir = get_skills_dir()
    skill_id = skill.name.lower().replace(" ", "-")
    skill_path = os.path.join(skills_dir, skill_id)
    if os.path.exists(skill_path):
        raise HTTPException(status_code=400, detail="Skill already exists")
    
    try:
        os.makedirs(skill_path, exist_ok=True)
        skill_md_content = f"---\nname: {skill.name}\ndescription: {skill.description}\n---\n\n# {skill.name}\n\n{skill.description}\n"
        with open(os.path.join(skill_path, "SKILL.md"), 'w', encoding='utf-8') as f:
            f.write(skill_md_content)
        return {"status": "success", "id": skill_id}
    except Exception as e:
        logger.error(f"Error creating skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/skills/{skill_id}")
async def update_skill(skill_id: str, skill: SkillUpdate):
    import os, re
    skills_dir = get_skills_dir()
    skill_path = os.path.join(skills_dir, skill_id)
    skill_md = os.path.join(skill_path, "SKILL.md")
    
    if not os.path.exists(skill_md):
        raise HTTPException(status_code=404, detail="Skill not found")
    
    try:
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update frontmatter
        content = re.sub(r'^name:.*$', f'name: {skill.name}', content, flags=re.MULTILINE)
        content = re.sub(r'^description:.*$', f'description: {skill.description}', content, flags=re.MULTILINE)
        
        with open(skill_md, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error updating skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    import shutil, os
    skills_dir = get_skills_dir()
    skill_path = os.path.join(skills_dir, skill_id)
    
    if not os.path.exists(skill_path):
        raise HTTPException(status_code=404, detail="Skill not found")
    
    try:
        shutil.rmtree(skill_path)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import sys
    import os
    if getattr(sys, 'frozen', False):
        os.chdir(sys._MEIPASS)
        
    logger.info(f"Starting Rambot Core on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
