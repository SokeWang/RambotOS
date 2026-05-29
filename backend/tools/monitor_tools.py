from langchain_core.tools import BaseTool
from services.monitor_manager import monitor_manager
from loguru import logger
import json
from typing import Any

class ControlMonitorTool(BaseTool):
    """Control background heartbeat monitors."""
    name: str = "control_monitor"
    description: str = ("Control background heartbeat monitors. "
                        "service_name: 'email' (WhatsApp coming soon). "
                        "action: 'start', 'stop', or 'status'.")

    def _run(self, service_name: str, action: str) -> str:
        logger.info(f"Tool call: control_monitor({service_name}, {action})")
        
        if action == 'status':
            statuses = monitor_manager.get_all_statuses()
            if service_name != 'all' and service_name in statuses:
                return f"{service_name} monitor is {'running' if statuses[service_name] else 'stopped'}."
            return f"Current monitor statuses: {json.dumps(statuses)}"
        
        enable = (action == 'start')
        success = monitor_manager.toggle_monitor(service_name, enable)
        
        if success:
            return f"Monitor '{service_name}' has been {action}ed successfully."
        else:
            return f"Failed to {action} monitor '{service_name}'. Is it registered?"

class ListMonitorsTool(BaseTool):
    """List all available heartbeat monitors and their current status."""
    name: str = "list_monitors"
    description: str = "List all available heartbeat monitors and their current status."

    def _run(self) -> str:
        statuses = monitor_manager.get_all_statuses()
        return f"Registered monitors: {json.dumps(statuses)}"
