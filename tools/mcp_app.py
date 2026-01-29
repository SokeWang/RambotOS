import sys
import os

# Add project root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

import importlib
import pkgutil
from mcp_instance import mcp
import skills

# 1. Load standalone skills from root directory (e.g., code_generator.py)
package = skills
for _, module_name, _ in pkgutil.iter_modules(package.__path__):
    if module_name not in ["__init__"]:
        try:
            importlib.import_module(f"skills.{module_name}")
            sys.stderr.write(f"Loaded standalone skill: {module_name}\n")
        except Exception as e:
            sys.stderr.write(f"Failed to load standalone skill {module_name}: {e}\n")

# 2. Load Claude-standard skills from subdirectories (e.g., skills/crypto-price/logic.py)
skills_root = os.path.dirname(skills.__file__)
for item in os.listdir(skills_root):
    item_path = os.path.join(skills_root, item)
    if os.path.isdir(item_path) and not item.startswith("__"):
        logic_file = os.path.join(item_path, "logic.py")
        if os.path.exists(logic_file):
            try:
                # Dynamic import skills.[item].logic
                importlib.import_module(f"skills.{item}.logic")
                sys.stderr.write(f"Loaded standard skill package: {item}\n")
            except Exception as e:
                sys.stderr.write(f"Failed to load skill package {item}: {e}\n")

# 3. Load generated simple tools from tools/generated/
generated_dir = os.path.join(root_dir, "tools", "generated")
if os.path.exists(generated_dir):
    for item in os.listdir(generated_dir):
        if item.endswith(".py") and not item.startswith("__"):
            module_name = item[:-3]
            try:
                importlib.import_module(f"tools.generated.{module_name}")
                sys.stderr.write(f"Loaded generated simple tool: {module_name}\n")
            except Exception as e:
                sys.stderr.write(f"Failed to load generated tool {module_name}: {e}\n")

if __name__ == "__main__":
    mcp.run(transport="stdio")
