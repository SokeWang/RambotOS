import os
import sys
import importlib
import pkgutil
from typing import List, Dict, Any
from loguru import logger
from config.config import CFG

class ToolManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolManager, cls).__new__(cls)
            # Initialize instance attributes here
            cls._instance.initialized = False
            cls._instance.tools = []
            cls._instance.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cls._instance._last_state = {}  # path -> mtime
            cls._instance._base_tools = []  # Core tools always available
        return cls._instance

    async def initialize(self):
        """Initial load of all tools"""
        logger.info("ToolManager: Performing initial tool discovery...")
        await self.refresh()

    async def refresh(self):
        """Reload all tools from disk/MCP servers"""
        logger.info("ToolManager: Refreshing tools...")
        
        all_tools = []
        
        
        # 1. MCP Tools (Removed)

        # 2. Native Mail Tools
        try:
            from tools.mail_tools import search_mail, get_mail_thread, send_mail_message, update_mail_state
            mail_tools = [search_mail, get_mail_thread, send_mail_message, update_mail_state]
            all_tools.extend(mail_tools)
            logger.info(f"ToolManager: Loaded {len(mail_tools)} Mail tools.")
        except Exception as e:
            logger.error(f"ToolManager: Failed to load Mail tools: {e}")

        # 3. Skill Management Tools (System Tools)
        try:
            from tools.skill_tools import read, exec, write
            skill_tools = [read, exec, write]
            all_tools.extend(skill_tools)
            logger.info(f"ToolManager: Loaded {len(skill_tools)} System tools (for skill management).")
        except Exception as e:
            logger.error(f"ToolManager: Failed to load Skill tools: {e}")

        # 4. Monitor Control Tools
        try:
            from tools.monitor_tools import control_monitor, list_monitors
            monitor_tools = [control_monitor, list_monitors]
            all_tools.extend(monitor_tools)
            logger.info(f"ToolManager: Loaded {len(monitor_tools)} Monitor tools.")
        except Exception as e:
            logger.error(f"ToolManager: Failed to load Monitor tools: {e}")

        # Separate basic (always candidate) and mcp/skills
        # Store all tools
        self.tools = all_tools
        
        # Update directory state
        for path in self._get_watch_dirs():
            if os.path.exists(path):
                self._last_state[path] = os.path.getmtime(path)

    def _get_watch_dirs(self) -> List[str]:
        return []

    async def refresh_if_needed(self) -> bool:
        """Checks if tool directories have changed and refreshes if so."""
        changed = False
        for path in self._get_watch_dirs():
            if not os.path.exists(path):
                continue
            mtime = os.path.getmtime(path)
            if mtime > self._last_state.get(path, 0):
                changed = True
                break
        
        if changed:
            logger.info("ToolManager: Directory change detected, refreshing tools...")
            await self.refresh()
            return True
        return False

    def get_all_tools(self) -> List[Any]:
        """Returns all tools currently managed"""
        return self.tools

    def get_filtered_tools(self) -> List[Any]:
        """Returns all tools currently managed. Self-evolution tools are now always included."""
        return self.get_all_tools()
    
    def get_base_tools(self) -> List[Any]:
        """Returns base tools (system tools that are always available)"""
        if not self._base_tools:
            try:
                from tools.skill_tools import read, exec, write
                self._base_tools = [read, exec, write]
                logger.info(f"ToolManager: Loaded {len(self._base_tools)} base tools")
            except Exception as e:
                logger.error(f"ToolManager: Failed to load base tools: {e}")
                self._base_tools = []
        return self._base_tools
    
    def get_tools_for_skills(self, skill_names: List[str]) -> List[Any]:
        """Load tools for specific skills"""
        # For now, return all tools (mail tools)
        # In the future, this can be enhanced to load skill-specific tools
        tools = []
        
        # Add mail tools if needed
        try:
            from tools.mail_tools import search_mail, get_mail_thread, send_mail_message, update_mail_state
            mail_tools = [search_mail, get_mail_thread, send_mail_message, update_mail_state]
            tools.extend(mail_tools)
        except Exception as e:
            logger.error(f"ToolManager: Failed to load mail tools: {e}")
        
        logger.info(f"ToolManager: Loaded {len(tools)} tools for skills: {skill_names}")
        return tools

tool_manager = ToolManager()
