import sys
import subprocess
import time
import os

# Inject backend path for compatibility with existing imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")
if os.path.exists(BACKEND_PATH) and BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)
import signal
import requests
import multiprocessing
from loguru import logger

def start_core():
    """Start the Rambot Core (FastAPI) service."""
    logger.info("Starting Rambot Core Service...")
    try:
        # In frozen mode (PyInstaller), we MUST call ourselves with a flag
        # Instead of calling python3 rambot_core.py
        if getattr(sys, 'frozen', False):
            # Pass --core flag to the bundled executable
            cmd = [sys.executable, "--core"]
            logger.debug(f"Executing: {cmd}")
        else:
            cmd = [sys.executable, "rambot_core.py"]
            
        proc = subprocess.Popen(
            cmd,
            stdout=None,
            stderr=None,
            text=True,
            bufsize=1,
            close_fds=True if os.name != "nt" else False
        )
        return proc
    except Exception as e:
        logger.error(f"Failed to start Rambot Core: {e}")
        return None

def start_telegram():
    """Start the Telegram Monitor service."""
    logger.info("Starting Telegram Monitor Service...")
    try:
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, "--telegram"]
        else:
            cmd = [sys.executable, "standalone_telegram.py"]
            
        proc = subprocess.Popen(
            cmd,
            stdout=None,
            stderr=None,
            text=True,
            bufsize=1,
            close_fds=True if os.name != "nt" else False
        )
        return proc
    except Exception as e:
        logger.error(f"Failed to start Telegram Monitor: {e}")
        return None

def start_email():
    """Start the Email Monitor service."""
    logger.info("Starting Email Monitor Service...")
    try:
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, "--email"]
        else:
            cmd = [sys.executable, "standalone_monitor.py"]
            
        proc = subprocess.Popen(
            cmd,
            stdout=None,
            stderr=None,
            text=True,
            bufsize=1,
            close_fds=True if os.name != "nt" else False
        )
        return proc
    except Exception as e:
        logger.error(f"Failed to start Email Monitor: {e}")
        return None

def wait_for_core():
    """Wait for Rambot Core to be ready."""
    logger.info("Waiting for Core to initialize...")
    max_retries = 15
    for i in range(max_retries):
        try:
            resp = requests.get("http://127.0.0.1:8000/", timeout=1)
            if resp.status_code == 200:
                logger.info("Rambot Core is UP.")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    
    logger.error("Rambot Core failed to start within timeout.")
    return False

def main():
    # 0. Set environment variables for packaging
    if getattr(sys, 'frozen', False):
        # If running as a bundle (PyInstaller)
        os.chdir(sys._MEIPASS)
        logger.info(f"Running in frozen mode. MEIPASS: {sys._MEIPASS}")
    
    # 1. Start Core
    core_proc = start_core()
    if not core_proc:
        sys.exit(1)

    # 2. Wait for Core
    if not wait_for_core():
        core_proc.terminate()
        sys.exit(1)

    # 2.5 Start Standalone Monitors
    tg_proc = start_telegram()
    email_proc = start_email()

    # 3. Wait in foreground and maintain backend service suite
    try:
        logger.info("=============================================================")
        logger.info("🌌 Rambot Backend Services are running in Headless Dev Mode.")
        logger.info("👉 Direct console logs will output above.")
        logger.info("👉 You can now run 'npm run dev' inside the 'frontend/' folder.")
        logger.info("👉 Press Ctrl+C in this terminal to gracefully terminate all services.")
        logger.info("=============================================================")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt detected. Terminating backend services...")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
    finally:
        # 4. Cleanup all services safely
        logger.info("Cleaning up backend services...")
        
        if core_proc and core_proc.poll() is None:
            logger.info("Stopping Rambot Core Service...")
            core_proc.terminate()
            try:
                core_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                core_proc.kill()
        
        if tg_proc and tg_proc.poll() is None:
            logger.info("Stopping Telegram Monitor...")
            tg_proc.terminate()
            try:
                tg_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tg_proc.kill()

        if email_proc and email_proc.poll() is None:
            logger.info("Stopping Email Monitor...")
            email_proc.terminate()
            try:
                email_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                email_proc.kill()
                
        logger.info("All services cleaned up. Done.")

if __name__ == "__main__":
    # Prevent multiprocessing issues on Windows when frozen
    multiprocessing.freeze_support()
    
    # 0. Set environment variables for packaging
    if getattr(sys, 'frozen', False):
        os.chdir(sys._MEIPASS)
        sys.path.append(sys._MEIPASS)
        logger.info(f"Running in frozen mode. MEIPASS: {sys._MEIPASS}")
    
    # Check command line arguments for dispatcher
    if len(sys.argv) > 1:
        try:
            if sys.argv[1] == "--core":
                logger.info("Starting Core Service分身...")
                import uvicorn
                from rambot_core import app, HOST, PORT
                uvicorn.run(app, host=HOST, port=PORT, log_level="debug")
                sys.exit(0)
            elif sys.argv[1] == "--telegram":
                logger.info("Starting Telegram Monitor分身...")
                from standalone_telegram import main as tg_main
                tg_main()
                sys.exit(0)
            elif sys.argv[1] == "--email":
                logger.info("Starting Email Monitor分身...")
                from standalone_monitor import StandaloneMonitor
                import asyncio
                monitor = StandaloneMonitor()
                asyncio.run(monitor.run())
                sys.exit(0)
        except Exception as e:
            logger.critical(f"分身启动失败! Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
    main()
