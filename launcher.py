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

    # 2.5 Start Telegram Monitor
    tg_proc = start_telegram()

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
        
        if tg_proc and tg_proc.poll() is None:
            tg_proc.terminate()
            try:
                tg_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tg_proc.kill()
        logger.info("Done.")

if __name__ == "__main__":
    # Prevent multiprocessing issues on Windows when frozen
    multiprocessing.freeze_support()
    
    # 0. Set environment variables for packaging
    if getattr(sys, 'frozen', False):
        # If running as a bundle (PyInstaller)
        os.chdir(sys._MEIPASS)
        sys.path.append(sys._MEIPASS)
        logger.info(f"Running in frozen mode. MEIPASS: {sys._MEIPASS}")
        
        # QtWebEngine helper path configuration
        # Expected path in BUNDLE (macOS)
        # Search for QtWebEngineProcess in several potential bundle locations
        possible_helper_paths = [
            # Standard helper path in Mac bundle structure
            os.path.join(sys._MEIPASS, "PySide6", "Qt", "lib", "QtWebEngineCore.framework", "Helpers", "QtWebEngineProcess.app", "Contents", "MacOS", "QtWebEngineProcess"),
            # Common relocated path in PyInstaller/PySide6.5+ bundles
            os.path.join(sys._MEIPASS, "PySide6", "Qt", "lib", "QtWebEngineCore.framework", "Versions", "Resources", "Helpers", "QtWebEngineProcess.app", "Contents", "MacOS", "QtWebEngineProcess"),
            # Another common relocated path
            os.path.join(sys._MEIPASS, "PySide6", "Qt", "lib", "QtWebEngineCore.framework", "Versions", "Current", "Helpers", "QtWebEngineProcess.app", "Contents", "MacOS", "QtWebEngineProcess"),
            # Root MacOS folder fallback
            os.path.join(os.path.dirname(sys.executable), "QtWebEngineProcess")
        ]
        
        found_helper = False
        for helper_path in possible_helper_paths:
            if os.path.exists(helper_path):
                os.environ["QTWEBENGINEPROCESS_PATH"] = helper_path
                logger.info(f"Set QTWEBENGINEPROCESS_PATH to: {helper_path}")
                found_helper = True
                break
        
        if not found_helper:
            logger.warning("Could not locate QtWebEngineProcess in any of the standard bundle paths.")

        # QtWebEngine resources path configuration (pak files etc.)
        possible_resource_paths = [
            # Standard location (where it should be)
            os.path.join(sys._MEIPASS, "PySide6", "Qt", "lib", "QtWebEngineCore.framework", "Resources"),
            # Common relocated path found in previous build
            os.path.join(sys._MEIPASS, "PySide6", "Qt", "lib", "QtWebEngineCore.framework", "Versions", "Resources", "Resources"),
            # Another variation
            os.path.join(sys._MEIPASS, "PySide6", "Qt", "resources"),
            # Root MacOS folder fallback
            os.path.dirname(sys.executable)
        ]
        
        found_resources = False
        for res_path in possible_resource_paths:
            # Check for a signature file like qtwebengine_resources.pak
            if os.path.exists(os.path.join(res_path, "qtwebengine_resources.pak")):
                os.environ["QTWEBENGINE_RESOURCES_PATH"] = res_path
                logger.info(f"Set QTWEBENGINE_RESOURCES_PATH to: {res_path}")
                
                # Also set ICU data path if icudtl.dat is present
                if os.path.exists(os.path.join(res_path, "icudtl.dat")):
                    os.environ["QTWEBENGINE_ICU_DATA_DIR"] = res_path
                    logger.info(f"Set QTWEBENGINE_ICU_DATA_DIR to: {res_path}")
                
                found_resources = True
                break
        
        if not found_resources:
            logger.warning("Could not locate QtWebEngine resources in any of the standard bundle paths.")

        # Disable sandbox for dev/unsigned builds on macOS
        os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
        logger.info("Deactivated QtWebEngine Sandbox for development bundle.")
    
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
        except Exception as e:
            logger.critical(f"分身启动失败! Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
    main()
