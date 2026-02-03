"""
Quick test to verify ToolManager initialization fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_manager import tool_manager

print("Testing ToolManager initialization...")

# Test 1: Check if _base_tools attribute exists
try:
    assert hasattr(tool_manager, '_base_tools'), "_base_tools attribute missing"
    print("✓ _base_tools attribute exists")
except AssertionError as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 2: Check if get_base_tools() works
try:
    base_tools = tool_manager.get_base_tools()
    print(f"✓ get_base_tools() returned {len(base_tools)} tools")
    print(f"  Tools: {[t.name for t in base_tools]}")
except Exception as e:
    print(f"✗ get_base_tools() failed: {e}")
    sys.exit(1)

# Test 3: Check singleton behavior
try:
    from tools.tool_manager import ToolManager
    instance1 = ToolManager()
    instance2 = ToolManager()
    assert instance1 is instance2, "Singleton pattern broken"
    print("✓ Singleton pattern working correctly")
except AssertionError as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

print("\n✅ All ToolManager tests passed!")
