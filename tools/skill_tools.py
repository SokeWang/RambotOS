import os
import re
import glob
import subprocess
import base64
from typing import List, Optional, Any, Dict
from langchain_core.tools import tool
from loguru import logger

BASE_SKILLS_PATH = "/Users/wangpeidong/Documents/RambotOS/skills"

@tool
def read(path: str, offset: int = 0, limit: int = 2000) -> str:
    """Read the contents of a file. Supports text files and images (jpg, png, gif, webp). 
    Images are returned as base64 strings with metadata. 
    For text files, output is truncated to limit lines. 
    Use offset/limit for large files.
    """
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


@tool
def exec(command: str, background: bool = False) -> str:
    """Execute shell commands with background continuation. 
    Returns stdout and stderr.
    """
    try:
        if background:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return f"Command started in background. PID: {process.pid}"
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        output = f"Stdout:\n{result.stdout}\nStderr:\n{result.stderr}"
        return output
    except Exception as e:
        return f"Error executing command: {str(e)}"

@tool
def write(path: str, content: str) -> str:
    """Write content to a file. Creates the file if it doesn't exist, overwrites if it does. 
    Automatically creates parent directories.
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

def get_all_skills_info() -> str:
    """Aggregates name and description from all SKILL.md files in the skills directory."""
    if not os.path.exists(BASE_SKILLS_PATH):
        return "No skills directory found."
    
    skills_info = []
    for skill_dir_name in os.listdir(BASE_SKILLS_PATH):
        skill_dir = os.path.join(BASE_SKILLS_PATH, skill_dir_name)
        if not os.path.isdir(skill_dir):
            continue
            
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        if os.path.exists(skill_md_path):
            try:
                with open(skill_md_path, 'r') as f:
                    content = f.read()
                    # Simple frontmatter parsing
                    name_match = re.search(r'^name:\s*(.*)$', content, re.MULTILINE)
                    desc_match = re.search(r'^description:\s*(.*)$', content, re.MULTILINE)
                    
                    name = name_match.group(1).strip() if name_match else skill_dir_name
                    description = desc_match.group(1).strip() if desc_match else "No description provided."
                    
                    skills_info.append(f"- **{name}**: {description} (Path: {skill_md_path})")
            except Exception as e:
                logger.error(f"Error reading {skill_md_path}: {e}")
                
    if not skills_info:
        return "No skills found."
        
    return "\n".join(skills_info)
