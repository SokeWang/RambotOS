import os
import re
import glob
import subprocess
import base64
from typing import List, Optional, Any, Dict
from langchain_core.tools import BaseTool
from loguru import logger
from config.config import CFG

BASE_SKILLS_PATH = CFG.SKILLS_PATH

class ReadFileTool(BaseTool):
    """Read contents of a file (manuals, documentation, or relevant data). 
    IMPORTANT: Do NOT use this tool to study script source code under `scripts/`. 
    You MUST rely on `SKILL.md` to understand how to call skills.
    Supports text files and images (jpg, png, gif, webp). 
    """
    name: str = "read"
    description: str = ("Read the contents of a file (manuals, documentation, or relevant data). "
                        "Supports text files and images.")

    def _run(self, path: str, offset: int = 0, limit: int = 2000) -> str:
        if not os.path.exists(path):
            return f"Error: File '{path}' not found."
        
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            try:
                with open(path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    return f"[ATTACHMENT: {path}]\n[MIME: image/{ext[1:]}]\n[BASE64: {encoded_string[:100]}... (truncated)]"
            except Exception as e:
                return f"Error reading image: {str(e)}"
        
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                content = "".join(lines[offset : offset + limit])
                total = len(lines)
                status = f"Read {len(lines[offset : offset + limit])} lines from {path}. (Total lines: {total})"
                return f"{status}\n\n{content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

class WebSearchTool(BaseTool):
    """Search the web for real-time information (news, stock prices, facts). 
    Returns a summary of search results.
    """
    name: str = "web_search"
    description: str = "Search the web for real-time information (news, stock prices, facts). Returns a summary of search results."

    def _run(self, query: str, max_results: int = 5) -> str:
        try:
            # Try to use DDGS from ddgs package
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if not results:
                    return "No search results found."
                
                output = []
                for r in results:
                    output.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nLink: {r.get('href')}\n")
                return "\n".join(output)
        except ImportError:
            logger.warning("SkillTools: duckduckgo_search not installed, using placeholder.")
            return f"Web search results for: {query}\n- Placeholder result: Rambot is an advanced AI assistant."
        except Exception as e:
            logger.error(f"SkillTools: Search error: {e}")
            return f"Error performing web search: {str(e)}"

class ExecCommandTool(BaseTool):
    """Execute shell commands for system tasks.
    Returns stdout and stderr.
    """
    name: str = "exec"
    description: str = ("Execute shell commands for system tasks. "
                        "Returns stdout and stderr.")

    def _run(self, command: str, background: bool = False) -> str:
        try:
            logger.info(f"SkillTools: Executing command: {command}")
            if background:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                return f"Command started in background. PID: {process.pid}"
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            output = f"Stdout:\n{result.stdout}\nStderr:\n{result.stderr}"
            return output
        except Exception as e:
            return f"Error executing command: {str(e)}"

class WriteFileTool(BaseTool):
    """Write content to a file. Creates the file if it doesn't exist, overwrites if it does. 
    Automatically creates parent directories.
    """
    name: str = "write"
    description: str = ("Write content to a file. Creates the file if it doesn't exist, overwrites if it does. "
                        "Automatically creates parent directories.")

    def _run(self, path: str, content: str) -> str:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"

class EditFileTool(BaseTool):
    """Edit a file by replacing old_str with new_str.
    The old_str MUST exist exactly in the file and MUST be unique to avoid ambiguous edits.
    """
    name: str = "edit_file"
    description: str = ("Edit a file by replacing old_str with new_str. "
                        "The old_str MUST exist exactly in the file and MUST be unique to avoid ambiguous edits.")

    def _run(self, path: str, old_str: str, new_str: str) -> str:
        try:
            if not os.path.exists(path):
                return f"Error: File '{path}' not found."
            
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            if old_str not in content:
                return f"Error: old_str not found in {path}. Make sure it matches exactly."
            
            count = content.count(old_str)
            if count > 1:
                return f"Error: old_str appears {count} times in {path}. Please provide more context to make it unique."
            
            new_content = content.replace(old_str, new_str, 1)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return f"Successfully edited {path}."
        except Exception as e:
            return f"Error editing file: {str(e)}"

class RetrieveSkillsTool(BaseTool):
    """
    Search and load skills relevant to the task.
    Call this ONLY when you need capabilities beyond your current tools.
    After calling this, your tool set will be expanded with the relevant skills.
    """
    name: str = "retrieve_skills"
    description: str = ("Search and load skills relevant to the task. "
                        "Call this ONLY when you need capabilities beyond your current tools. "
                        "After calling this, your tool set will be expanded with the relevant skills.")

    def _run(self, task_description: str) -> str:
        from core.skill_index import skill_index, SkillMetadata
        relevant_skills = skill_index.search_skills_by_intent(task_description, top_k=3)
        
        if not relevant_skills:
            return "No relevant skills found."
        
        results = []
        for name in relevant_skills:
            meta = skill_index.get_skill_metadata(name)
            if meta:
                results.append(f"- **{meta.name}**: {meta.description} (Path: {meta.path})")
        
        summary = "\n".join(results)
        return (f"Found {len(results)} relevant skills:\n{summary}\n\n"
                "Protocol: If a skill applies, use `read` to study its SKILL.md. "
                "DO NOT read files in `scripts/`. You can use `exec` for both skill procedures and general system tasks.")


