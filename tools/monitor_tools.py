from langchain_core.tools import tool
from services.monitor_manager import monitor_manager
from loguru import logger
import json

@tool
def control_monitor(service_name: str, action: str) -> str:
    """
    Control background heartbeat monitors.
    service_name: 'email' (WhatsApp coming soon).
    action: 'start', 'stop', or 'status'.
    """
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

@tool
def list_monitors() -> str:
    """List all available heartbeat monitors and their current status."""
    statuses = monitor_manager.get_all_statuses()
    return f"Registered monitors: {json.dumps(statuses)}"
