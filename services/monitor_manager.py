import os
import subprocess
import time
import signal
from loguru import logger

class MonitorService:
    def __init__(self):
        self.processes = {}  # name -> subprocess.Popen
        
    def _discover_scripts(self):
        """Scans the base directory for standalone_*.py scripts."""
        scripts = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for f in os.listdir(base_dir):
            if f.startswith("standalone_") and f.endswith(".py"):
                if f == "standalone_monitor.py":
                    name = "email"
                else:
                    name = f.replace("standalone_", "").replace(".py", "")
                scripts[name] = os.path.join(base_dir, f)
        return scripts

    def start_monitor(self, name):
        scripts = self._discover_scripts()
        if name in scripts:
            script_path = scripts[name]
            
            if name in self.processes and self.processes[name].poll() is None:
                logger.info(f"MonitorService: {name} already running.")
                return True
                
            logger.info(f"MonitorService: Spawning standalone {name} monitor...")
            try:
                import sys
                proc = subprocess.Popen([sys.executable, script_path], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
                self.processes[name] = proc
                return True
            except Exception as e:
                logger.error(f"MonitorService: Failed to spawn {name}: {e}")
                return False
        return False

    def stop_monitor(self, name, unregister_callback=None):
        pid_file = f"/tmp/rambot_{name}_monitor.pid"
        success = False
        
        if name in self.processes:
            proc = self.processes[name]
            if proc.poll() is None:
                logger.info(f"MonitorService: Terminating {name} process...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except:
                    proc.kill()
            del self.processes[name]
            success = True
            
        elif os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read())
                os.kill(pid, signal.SIGTERM)
                success = True
            except Exception as e:
                pass
                
        if success and unregister_callback:
            unregister_callback(name)
            
        return success

    def toggle_monitor(self, name, enable, unregister_callback=None):
        if str(enable).lower() == 'true' or enable is True:
            return self.start_monitor(name)
        else:
            return self.stop_monitor(name, unregister_callback)

    def cleanup(self):
        for name in list(self.processes.keys()):
            self.stop_monitor(name)

monitor_manager = MonitorService()
