import os
import subprocess
import requests
import time
import json
import signal
from loguru import logger
from PySide6.QtCore import QObject, Signal, QThread, QTimer

CORE_URL = "http://127.0.0.1:8000"

class NotificationBridge(QThread):
    """Polls FastAPI for notifications and emits them."""
    notificationReceived = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.last_sync = time.time()

    def run(self):
        while self.running:
            try:
                # Poll for notifications since last sync
                resp = requests.get(f"{CORE_URL}/notifications", params={"since": self.last_sync}, timeout=2)
                if resp.status_code == 200:
                    notifs = resp.json()
                    for n in notifs:
                        self.notificationReceived.emit(n["message"])
                        self.last_sync = max(self.last_sync, n.get("timestamp", 0))
            except Exception as e:
                # Silently ignore connection errors (core might be down)
                pass
            
            time.sleep(2) # Poll every 2 seconds

    def stop(self):
        self.running = False
        self.wait()

class MonitorManager(QObject):
    """
    Service Oriented Monitor Manager.
    Bridges GUI to Rambot Core and manages standalone processes.
    """
    statusChanged = Signal(str, bool)
    notificationReceived = Signal(str)

    def __init__(self):
        super().__init__()
        self.processes = {}  # name -> subprocess.Popen
        self.statuses = {}   # name -> bool
        
        # Start notification bridge
        self.bridge = NotificationBridge()
        self.bridge.notificationReceived.connect(self.notificationReceived.emit)
        self.bridge.start()
        
        # Sync timer for status
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sync_with_core)
        self.sync_timer.start(5000) # Every 5 seconds

    def sync_with_core(self):
        """Fetch status from FastAPI and update local state."""
        try:
            resp = requests.get(f"{CORE_URL}/monitor/status", timeout=1)
            if resp.status_code == 200:
                core_stats = resp.json()
                for stat in core_stats:
                    name = stat["name"]
                    is_running = stat["status"] == "running"
                    if self.statuses.get(name) != is_running:
                        self.statuses[name] = is_running
                        self.statusChanged.emit(name, is_running)
        except:
            pass

    def start_monitor(self, name):
        """Spawn the standalone monitor process."""
        if name == "email":
            script_path = os.path.join(os.getcwd(), "standalone_monitor.py")
            if name in self.processes and self.processes[name].poll() is None:
                logger.info(f"MonitorManager: {name} already has a managed process running.")
                return True
                
            logger.info(f"MonitorManager: Spawning standalone {name} monitor...")
            try:
                # Use sys.executable to ensure we use the same python environment
                import sys
                proc = subprocess.Popen([sys.executable, script_path], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
                self.processes[name] = proc
                return True
            except Exception as e:
                logger.error(f"MonitorManager: Failed to spawn {name}: {e}")
                return False
        return False

    def stop_monitor(self, name):
        """Terminate the standalone monitor process."""
        if name in self.processes:
            proc = self.processes[name]
            if proc.poll() is None:
                logger.info(f"MonitorManager: Terminating {name} process...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except:
                    proc.kill()
            del self.processes[name]
            self.statuses[name] = False
            
            # Notify Core immediately
            try:
                requests.post(f"{CORE_URL}/monitor/unregister/{name}", timeout=1)
            except:
                pass
                
            return True
        
        # Fallback: Check PID file if it was started externally
        pid_file = f"/tmp/rambot_{name}_monitor.pid"
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read())
                logger.info(f"MonitorManager: Killing external {name} monitor (PID: {pid})...")
                os.kill(pid, signal.SIGTERM)
                return True
            except Exception as e:
                logger.error(f"MonitorManager: Failed to kill external process {pid}: {e}")
        
        return False

    def toggle_monitor(self, name, enable):
        # Update local state immediately to prevent sync race
        self.statuses[name] = enable
        
        if enable:
            return self.start_monitor(name)
        else:
            return self.stop_monitor(name)

    def get_all_statuses(self):
        # Trigger an immediate sync for better UI responsiveness
        self.sync_with_core()
        return self.statuses

    def cleanup(self):
        """Stop all managed processes and the bridge."""
        self.bridge.stop()
        for name in list(self.processes.keys()):
            self.stop_monitor(name)

# Singleton
monitor_manager = MonitorManager()
