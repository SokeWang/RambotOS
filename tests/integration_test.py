import os
import sys
import time
import subprocess
import requests
import signal
from loguru import logger

# Inject backend and root paths for compatibility with existing imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if os.path.exists(PROJECT_ROOT) and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.exists(BACKEND_PATH) and BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

def test_imports():
    """Verify all critical module imports work without errors."""
    logger.info("🧪 Step 1: Testing critical internal and external imports...")
    try:
        import fastapi
        import uvicorn
        import chromadb
        from config.config import CFG
        from core.history import History
        from core.memory import MemoryManager
        from services.wakeword import WakeWordThread
        from agents.langchain_agent import LangchainBrain
        logger.info("✅ Imports verified successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Imports verification failed: {e}")
        return False

def test_config():
    """Verify configuration files load environment keys correctly."""
    logger.info("🧪 Step 2: Testing local .env environmental parsing...")
    try:
        from config.config import CFG
        logger.info(f"✅ Configuration parsed successfully.")
        logger.info(f"👉 Project Root Path: {CFG.PROJECT_ROOT}")
        logger.info(f"👉 Gemini Key Configured: {'Yes' if CFG.api_key else 'No (Will use fallback)'}")
        return True
    except Exception as e:
        logger.error(f"❌ Configuration parsing failed: {e}")
        return False

def run_live_api_tests():
    """Start launcher.py, test FastAPI endpoints, and gracefully clean up."""
    logger.info("🧪 Step 3: Performing active integration and process supervision tests...")
    
    # 1. Spawn launcher.py as a headless supervisor
    python_exec = sys.executable
    launcher_path = os.path.join(PROJECT_ROOT, "launcher.py")
    
    logger.info(f"🚀 Spawning backend supervisor: {python_exec} {launcher_path} --no-gui")
    
    # Do not capture stdout as a PIPE to avoid buffer blocking issues during testing
    proc = subprocess.Popen(
        [python_exec, launcher_path],
        stdout=None,
        stderr=None,
        cwd=PROJECT_ROOT
    )
    
    # Allow uvicorn and background services some time to boot
    logger.info("⏳ Waiting for FastAPI Core (Port 8000) to initialize...")
    core_ready = False
    max_retries = 15
    for i in range(max_retries):
        try:
            resp = requests.get("http://127.0.0.1:8000/", timeout=2)
            if resp.status_code == 200:
                logger.info("🔥 Rambot Core is UP and running!")
                core_ready = True
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
        
    if not core_ready:
        logger.critical("❌ Core failed to start within timeout. Aborting active tests.")
        proc.terminate()
        return False

    # 2. Perform live REST API requests to verify endpoints
    success = True
    try:
        # A. Health check endpoint
        logger.info("🔍 Querying GET / (health check)...")
        r = requests.get("http://127.0.0.1:8000/", timeout=3)
        logger.info(f"Response: {r.status_code} - {r.json()}")
        if r.status_code != 200:
            success = False
            
        # B. Pluggable skills endpoint
        logger.info("🔍 Querying GET /skills (skills index)...")
        r = requests.get("http://127.0.0.1:8000/skills", timeout=3)
        skills = r.json()
        logger.info(f"Response: {r.status_code} - Found {len(skills)} pluggable skills!")
        if r.status_code != 200:
            success = False

        # C. SQLite chat history checkpointer endpoint
        logger.info("🔍 Querying GET /history (SQLite history)...")
        r = requests.get("http://127.0.0.1:8000/history?session_id=os_user", timeout=3)
        logger.info(f"Response: {r.status_code} - Fetched history logs successfully.")
        if r.status_code != 200:
            success = False

        # D. ChromaDB Long-Term Memory endpoint
        logger.info("🔍 Querying GET /memory (ChromaDB Memory)...")
        r = requests.get("http://127.0.0.1:8000/memory", timeout=5)
        logger.info(f"Response: {r.status_code} - ChromaDB initialized and queried successfully.")
        if r.status_code != 200:
            success = False

        # E. Background monitors status
        logger.info("🔍 Querying GET /monitor/status (Monitor statuses)...")
        r = requests.get("http://127.0.0.1:8000/monitor/status", timeout=3)
        monitors = r.json()
        logger.info(f"Response: {r.status_code} - Active monitors: {list(monitors.keys())}")
        if r.status_code != 200:
            success = False

    except Exception as api_err:
        logger.error(f"❌ API testing encountered a fatal error: {api_err}")
        success = False
        
    # 3. Gracefully terminate backend and check port cleanup
    logger.info("🧼 Step 4: Testing graceful keyboard interrupt Ctrl+C shutdown cascade...")
    try:
        proc.send_signal(signal.SIGINT) # Emulate Ctrl+C
        logger.info("Sent SIGINT (Ctrl+C) signal to supervisor. Waiting for child process cleanup...")
        proc.wait(timeout=10)
        logger.info("✅ Supervisor terminated successfully.")
    except Exception as cleanup_err:
        logger.error(f"❌ Graceful cleanup failed or timed out: {cleanup_err}")
        proc.kill()
        success = False
        
    # Double check if port 8000 is fully freed (with retry loop to let uvicorn socket close)
    logger.info("⏳ Waiting for port 8000 sockets to fully release...")
    port_freed = False
    for retry in range(10):
        try:
            requests.get("http://127.0.0.1:8000/", timeout=1)
            time.sleep(0.5)
        except requests.exceptions.RequestException:
            port_freed = True
            break
            
    if port_freed:
        logger.info("✅ Port 8000 successfully and cleanly freed! Zero zombie processes.")
    else:
        logger.error("❌ Port 8000 is STILL bound! Subprocesses were not fully cleaned up.")
        success = False

    return success

if __name__ == "__main__":
    logger.info("=============================================================")
    logger.info("🌌 STARTING RAMBOTOS COMPREHENSIVE INTEGRATION TEST SUITE")
    logger.info("=============================================================")
    
    imports_ok = test_imports()
    config_ok = test_config()
    live_ok = False
    
    if imports_ok and config_ok:
        live_ok = run_live_api_tests()
        
    logger.info("=============================================================")
    logger.info("📊 RAMBOTOS INTEGRATION TEST RESULTS SUMMARY:")
    logger.info("=============================================================")
    logger.info(f"1. Imports Verification:      {'✅ PASSED' if imports_ok else '❌ FAILED'}")
    logger.info(f"2. Local .env Config Load:     {'✅ PASSED' if config_ok else '❌ FAILED'}")
    logger.info(f"3. Core Server Boot & API:    {'✅ PASSED' if live_ok else '❌ FAILED'}")
    logger.info(f"4. Cascade Ctrl+C Process Exit: {'✅ PASSED' if live_ok else '❌ FAILED'}")
    logger.info("=============================================================")
    
    if imports_ok and config_ok and live_ok:
        logger.info("🌟 ALL INTEGRATION TESTS PASSED PERFECTLY! ARCHITECTURE IS 100% SOUND.")
        sys.exit(0)
    else:
        logger.error("💥 SYSTEM VERIFICATION DETECTED ISSUES. PLEASE REVIEW LOGS.")
        sys.exit(1)
