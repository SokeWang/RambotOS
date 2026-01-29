import sys
import os
import subprocess
import importlib
import traceback
import json
import inspect
import ast
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from models.schema import CoderResponse

# Add project root to path for config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import CFG
from mcp_instance import mcp

# --- Agents ---
planner = create_agent(
    model=ChatGoogleGenerativeAI(
        api_key=CFG.api_key,
        model=CFG.chat_model,
    ),
    system_prompt = """You are a senior architect. Analyze the requirement and existing tools/skills.
Propose whether to ENHANCE an existing tool/skill or CREATE a new standalone tool.

### CRITICAL RULES:
1. **REUSE BEFORE CREATE**: If the requirement can logically be integrated into an existing tool or skill, you MUST propose ENHANCE.
2. **TOOL CONTEXT**: Evaluate the descriptions and function names of existing tools. If a tool already handles a similar domain (e.g., "search", "weather", "file management"), enhance it instead of creating a new one.
3. **NO DUPLICATION**: Do not propose CREATE if functionality already exists or is very similar to existing capabilities.
4. **STANDALONE PREFERENCE**: For entirely new and unrelated functionality, prefer creating a standalone tool in `tools/generated/`.

Return the decision in the specified format."""
)

coder = create_agent(
    model=ChatGoogleGenerativeAI(
        api_key=CFG.api_key,
        model=CFG.chat_model,
    ),
    system_prompt="""You are an expert Python developer specialized in creating MCP tools.
Your task is to generate a STANDALONE tool (single .py file).
### SCENARIOS:
1. **NEW TOOL**: Create a fresh .py file in the `tools/generated` directory.
2. **ENHANCEMENT**: Merge new requirements into existing code.

### CRITICAL REQUIREMENTS:
1. **Import MCP**: `from mcp_instance import mcp`
2. **Decorator**: You MUST decorate all exposed tools with `@mcp.tool()`. Use docstrings for descriptions.
3. **Paths**: `mcp_instance` is in `tools/` but accessible via `sys.path`. Import it directly.
4. **Structured Format**: Always return code suitable for a single python file. Avoid creating complex folder structures.""",
    response_format=CoderResponse
)

# --- Helpers ---

def install_dependencies(deps: List[str]):
    if not deps: return
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + deps, stdout=sys.stderr, stderr=sys.stderr)
    except Exception as e:
        print(f"Error installing with python -m pip: {e}", file=sys.stderr)
        try:
            print("Attempting to bootstrap pip with ensurepip...", file=sys.stderr)
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"], stdout=sys.stderr, stderr=sys.stderr)
            print("Retrying installation with python -m pip...", file=sys.stderr)
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + deps, stdout=sys.stderr, stderr=sys.stderr)
        except Exception as e3:
             print(f"Critical error: Could not install dependencies {deps}: {e3}", file=sys.stderr)
             raise e3

async def run_skill_loop(requirement: str, existing_py: str = None, existing_md: str = None, existing_skill_name: str = None):
    error = None
    for trial in range(3):
        try:
            prompt = f"Requirement: {requirement}"
            if existing_skill_name:
                prompt += f"\n\n### TARGET TOOL NAME: {existing_skill_name}"
            if existing_py:
                prompt += f"\n\n### EXISTING CONTEXT (ENHANCE THIS)\n#### code:\n{existing_py}"
            if error:
                prompt += f"\n\nPrevious attempt failed with error:\n{error}\nPlease fix the code."
            
            response = await coder.ainvoke({"messages": [{"role": "user", "content": prompt}]})
            data = response["structured_response"]
            
            # 2. Install Deps
            deps = data.dependencies
            install_dependencies(deps)
            
            # 3. Validate and Save
            name = data.tool_name
            code = data.py_code
            
            start_dir = os.path.dirname(os.path.abspath(__file__)) # skills/skill-manager
            skills_root = os.path.dirname(start_dir) # skills/
            project_root = os.path.dirname(skills_root)
            generated_dir = os.path.join(project_root, "tools", "generated")
            
            # If we are enhancing an existing skill package, we still write to its logic.py
            if existing_skill_name:
                skill_dir = os.path.join(skills_root, existing_skill_name)
                if os.path.exists(skill_dir):
                    logic_path = os.path.join(skill_dir, "logic.py")
                    with open(logic_path, "w", encoding="utf-8") as f:
                        f.write(code)
                    full_module_name = f"skills.{existing_skill_name}.logic"
                else:
                    os.makedirs(generated_dir, exist_ok=True)
                    file_path = os.path.join(generated_dir, f"{name}.py")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(code)
                    full_module_name = f"tools.generated.{name}"
            else:
                # DEFAULT: Create standalone tool
                os.makedirs(generated_dir, exist_ok=True)
                file_path = os.path.join(generated_dir, f"{name}.py")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                full_module_name = f"tools.generated.{name}"
                
            if full_module_name in sys.modules:
                del sys.modules[full_module_name]
            
            if project_root not in sys.path:
                sys.path.append(project_root)
                
            module = importlib.import_module(full_module_name)
            importlib.reload(module)
            
            func_name = data.function_name
            test_args = data.test_args
            
            if hasattr(module, func_name):
                func = getattr(module, func_name)
                if inspect.iscoroutinefunction(func):
                    res = await func(**test_args)
                else:
                    res = func(**test_args)
                return f"Tool '{name}' processed successfully. Verification: {str(res)}"
            else:
                raise ValueError(f"Function {func_name} not found")
                    
        except Exception as e:
            error = str(e)
            print(f"Trial {trial + 1} failed: {error}", file=sys.stderr)
            
    return f"Failed to process skill/tool after 3 trials. Last error: {error}"

# --- Tools ---

@mcp.tool()
async def propose_skill(requirement: str) -> str:
    """
    Analyzes a requirement and proposes either ACQUIRING a new tool or ENHANCING an existing one.
    Call this FIRST when you lack a capability.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    skills_root = os.path.dirname(current_dir)
    project_root = os.path.dirname(skills_root)
    generated_tools_dir = os.path.join(project_root, "tools", "generated")
    
    existing_entities = {}
    
    def get_tool_info(name: str, code: str) -> str:
        """Extracts tool names and docstrings from code."""
        tools = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for mcp.tool decorator
                    is_tool = any(
                        (isinstance(decorator, ast.Call) and 
                         isinstance(decorator.func, ast.Attribute) and 
                         decorator.func.attr == 'tool') or 
                        (isinstance(decorator, ast.Attribute) and 
                         decorator.attr == 'tool')
                        for decorator in node.decorator_list
                    )
                    if is_tool:
                        docstring = ast.get_docstring(node) or "No description"
                        tools.append(f"- Function: {node.name}\n  Description: {docstring}")
        except Exception:
            return "Error parsing tool info"
        return "\n".join(tools) if tools else "No explicit tools found"

    # Discovery from skills/
    if os.path.exists(skills_root):
        for d in os.listdir(skills_root):
             skill_path = os.path.join(skills_root, d)
             if os.path.isdir(skill_path) and not d.startswith("__") and d != "skill-manager":
                  logic_path = os.path.join(skill_path, "logic.py")
                  if os.path.exists(logic_path):
                       with open(logic_path, 'r') as f:
                           code = f.read()
                           existing_entities[f"Skill: {d}"] = get_tool_info(d, code)
    
    # Discovery from tools/generated/
    if os.path.exists(generated_tools_dir):
        for f in os.listdir(generated_tools_dir):
            if f.endswith(".py"):
                name = f[:-3]
                file_path = os.path.join(generated_tools_dir, f)
                with open(file_path, 'r') as f_obj:
                    code = f_obj.read()
                    existing_entities[f"Tool: {name}"] = get_tool_info(name, code)
    
    plan_prompt = f"""
    Analyze this requirement: "{requirement}"
    
    Current expertise (Skills/Tools):
    {json.dumps(existing_entities, indent=2)}
    
    Task:
    1. Determine if this requirement fits an EXISTING tool or skill package by looking at their function names and descriptions.
    2. **MANDATORY**: If the requirement is even remotely related to an existing tool (e.g., both are about "search", "weather", "macos", etc.), propose ENHANCE.
    3. Only propose CREATE TOOL if the requirement is for a completely separate domain not covered by existing tools.
    
    Return a formal proposal:
    "Decision: [ENHANCE [name] / CREATE TOOL [name]]"
    "Logic: [Detailed reasoning why this should be an enhancement or a new tool]"
    "Shall I proceed?"
    """
    
    response = await planner.ainvoke({"messages": [{"role": "user", "content": plan_prompt}]})
    content = response["messages"][-1].content
    if isinstance(content, list):
        return "".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in content])
    return str(content)

@mcp.tool()
async def acquire_skill(requirement: str) -> str:
    """
    Generates and installs a FRESH new tool.
    Call ONLY after user approval.
    """
    sys.stderr.write(f"Creating new tool: {requirement}\n")
    return await run_skill_loop(requirement)

@mcp.tool()
async def enhance_skill(skill_name: str, requirement: str) -> str:
    """
    Updates an EXISTING tool or skill package with new capabilities.
    Call ONLY after the user has approved the update from `propose_skill`.
    """
    sys.stderr.write(f"Enhancing entity '{skill_name}': {requirement}\n")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    skills_root = os.path.dirname(current_dir)
    project_root = os.path.dirname(skills_root)
    skill_path = os.path.join(skills_root, skill_name)
    generated_tools_path = os.path.join(project_root, "tools", "generated", f"{skill_name}.py")
    
    try:
        if os.path.exists(os.path.join(skill_path, "logic.py")):
            with open(os.path.join(skill_path, "logic.py"), "r") as f:
                existing_py = f.read()
            with open(os.path.join(skill_path, "SKILL.md"), "r") as f:
                existing_md = f.read()
            return await run_skill_loop(requirement, existing_py, existing_md, skill_name)
        elif os.path.exists(generated_tools_path):
            with open(generated_tools_path, "r") as f:
                existing_py = f.read()
            return await run_skill_loop(requirement, existing_py, None, skill_name)
        else:
            return f"Error: Entity '{skill_name}' not found for enhancement."
    except Exception as e:
        return f"Error reading existing files: {e}"
