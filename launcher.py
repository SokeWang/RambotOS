import sys
import subprocess
import time
import os
import signal
import requests
import multiprocessing
from loguru import logger

def start_core():
    """Start the Rambot Core (FastAPI) service."""
    logger.info("Starting Rambot Core Service...")
    # Use sys.executable to ensure the same interpreter is used
    try:
        proc = subprocess.Popen(
            [sys.executable, "rambot_core.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            close_fds=True if os.name != "nt" else False
        )
        return proc
    except Exception as e:
        logger.error(f"Failed to start Rambot Core: {e}")
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

    # 3. Start GUI
    logger.info("Launching Rambot OS GUI...")
    try:
        from gui import run_gui
        exit_code = run_gui()
    except KeyboardInterrupt:
        logger.info("User interrupted.")
    except Exception as e:
        logger.error(f"GUI crashed: {e}")
    finally:
        # 4. Cleanup
        logger.info("Cleaning up services...")
        if core_proc.poll() is None:
            core_proc.terminate()
            try:
                core_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                core_proc.kill()
        logger.info("Done.")

if __name__ == "__main__":
    # Prevent multiprocessing issues on Windows when frozen
    multiprocessing.freeze_support()
    main()
