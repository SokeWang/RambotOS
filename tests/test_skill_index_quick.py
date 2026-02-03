"""
Quick test script to verify skill index implementation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.skill_index import skill_index
from loguru import logger

print("=" * 60)
print("Testing Skill Index Implementation")
print("=" * 60)

# Test 1: Initialize
print("\n[Test 1] Initializing SkillIndex...")
try:
    skill_index.initialize()
    print(f"✓ Initialized successfully")
    print(f"  Found {len(skill_index.skills)} skills")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 2: Get all skills summary
print("\n[Test 2] Getting skills summary...")
try:
    summary = skill_index.get_all_skills_summary()
    print(f"✓ Summary generated ({len(summary)} chars)")
    print(f"\n{summary}\n")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 3: Get skill names
print("\n[Test 3] Getting skill names...")
try:
    names = skill_index.get_all_skill_names()
    print(f"✓ Retrieved {len(names)} skill names: {names}")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 4: Search skills by intent
print("\n[Test 4] Searching skills by intent...")
test_queries = [
    "查新闻",
    "get weather information",
    "create a new skill"
]

for query in test_queries:
    try:
        results = skill_index.search_skills_by_intent(query, top_k=2)
        print(f"✓ Query: '{query}' -> {results}")
    except Exception as e:
        print(f"✗ Query '{query}' failed: {e}")

# Test 5: Get retrieve tool
print("\n[Test 5] Getting retrieve_skills tool...")
try:
    tool = skill_index.get_retrieve_tool()
    print(f"✓ Tool created: {tool.name}")
    print(f"  Description: {tool.description[:100]}...")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 6: Test retrieve tool execution
print("\n[Test 6] Testing retrieve_skills tool execution...")
try:
    result = tool.invoke({"task_description": "fetch news articles"})
    print(f"✓ Tool result: {result}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
