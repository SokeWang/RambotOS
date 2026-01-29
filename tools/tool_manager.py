import os
import sys
import importlib
import pkgutil
from typing import List, Dict, Any
from loguru import logger
from langchain_mcp_adapters.client import MultiServerMCPClient
from config.config import CFG

class ToolManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.basic_tools = []
        self.mcp_tools = []
        self.initialized = True
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._last_state = {} # path -> mtime

    async def initialize(self):
        """Initial load of all tools"""
        logger.info("ToolManager: Performing initial tool discovery...")
        await self.refresh()

    async def refresh(self):
        """Reload all tools from disk/MCP servers"""
        logger.info("ToolManager: Refreshing tools...")
        
        all_tools = []
        
        # 1. MCP Tools
        try:
            mcp_client = MultiServerMCPClient(
                {
                    "math": {
                        "transport": "stdio",
                        "command": sys.executable if ".venv" in sys.executable else os.path.join(self.project_root, ".venv", "bin", "python"),
                        "args": [os.path.join(self.project_root, "tools", "mcp_app.py")],
                    }
                }
            )
            mcp_tools = await mcp_client.get_tools()
            all_tools.extend(mcp_tools)
            logger.info(f"ToolManager: Loaded {len(mcp_tools)} tools from MCP servers.")
        except Exception as e:
            logger.error(f"ToolManager: Failed to load MCP tools: {e}")

        # 2. Native 163 Mail Tools
        try:
            from tools.mail_tools import search_163_mail, get_163_mail_thread, send_163_mail_message, update_163_mail_state
            mail_tools = [search_163_mail, get_163_mail_thread, send_163_mail_message, update_163_mail_state]
            all_tools.extend(mail_tools)
            logger.info(f"ToolManager: Loaded {len(mail_tools)} 163 Mail tools.")
        except Exception as e:
            logger.error(f"ToolManager: Failed to load 163 Mail tools: {e}")

        # Separate basic (always candidate) and mcp/skills
        self.basic_tools = []
        self.mcp_tools = []
        
        skill_manager_tools = {"propose_skill", "acquire_skill", "enhance_skill"}
        
        for tool in all_tools:
            if tool.name in skill_manager_tools:
                # These are handled specifically by middleware based on develop_mode
                self.basic_tools.append(tool)
            else:
                self.mcp_tools.append(tool)
        
        # Update directory state
        for path in self._get_watch_dirs():
            if os.path.exists(path):
                self._last_state[path] = os.path.getmtime(path)

    def _get_watch_dirs(self) -> List[str]:
        return [
            os.path.join(self.project_root, "skills"),
            os.path.join(self.project_root, "tools", "generated")
        ]

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
        return self.basic_tools + self.mcp_tools

    def get_filtered_tools(self) -> List[Any]:
        """Returns all tools currently managed. Self-evolution tools are now always included."""
        return self.get_all_tools()

tool_manager = ToolManager()
