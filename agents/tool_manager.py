import os
from typing import List, Any
from loguru import logger

# Static imports for core tools (classes)
from tools.skill_tools import (
    ReadFileTool, WriteFileTool, ExecCommandTool, 
    WebSearchTool, EditFileTool, RetrieveSkillsTool
)
from tools.monitor_tools import ControlMonitorTool, ListMonitorsTool
from tools.memory_tools import SearchMemoryTool

class ToolManager:
    def __init__(self):
        # Unified core system tools (instantiated)
        self._core_tools = [
            ReadFileTool(),
            ExecCommandTool(),
            WriteFileTool(),
            WebSearchTool(),
            EditFileTool(),
            RetrieveSkillsTool(),
            ControlMonitorTool(),
            ListMonitorsTool()
        ]

    def get_tools(self, session_id: str = "global", skills: List[str] = None) -> List[Any]:
        """
        Unified tool getter for the BrainAgent.
        """
        all_tools = []
        
        # 1. Core System Tools (Unified list)
        all_tools.extend(self._core_tools)
        
        # 2. Memory Tool (bound to session)
        all_tools.append(SearchMemoryTool(session_id=session_id))
            
        # 3. Dynamic Skill Tools (Placeholder)
        if skills:
            # Future integration for dynamic skill-based tool loading
            pass
            
        return all_tools

# Export a single instance to be used across the application
tool_manager = ToolManager()
