"""
Test script to verify skill hot-reload functionality
Simulates creating a new skill and checking if it's detected
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.skill_index import skill_index
from loguru import logger

print("=" * 60)
print("Testing Skill Hot-Reload")
print("=" * 60)

# Step 1: Initialize
print("\n[Step 1] Initializing SkillIndex...")
skill_index.initialize()
initial_count = len(skill_index.skills)
print(f"✓ Found {initial_count} skills initially")

# Step 2: Create a test skill
print("\n[Step 2] Creating a test skill...")
test_skill_dir = "/Users/wangpeidong/Documents/RambotOS/skills/test-hot-reload"
os.makedirs(test_skill_dir, exist_ok=True)

test_skill_content = """---
name: test-hot-reload
description: Test skill for hot-reload verification
---

# Test Hot Reload Skill

This is a temporary test skill to verify hot-reload functionality.
"""

skill_md_path = os.path.join(test_skill_dir, "SKILL.md")
with open(skill_md_path, 'w') as f:
    f.write(test_skill_content)

print(f"✓ Created test skill at {test_skill_dir}")

# Step 3: Wait a moment for filesystem
time.sleep(0.5)

# Step 4: Check if refresh detects the new skill
print("\n[Step 3] Checking if refresh_if_needed() detects the change...")
refreshed = skill_index.refresh_if_needed()

if refreshed:
    print("✓ Refresh triggered successfully!")
    new_count = len(skill_index.skills)
    print(f"  Skill count: {initial_count} → {new_count}")
    
    if "test-hot-reload" in skill_index.skills:
        print("✓ New skill 'test-hot-reload' found in index!")
    else:
        print("✗ New skill NOT found in index")
else:
    print("✗ Refresh was NOT triggered")

# Step 5: Test search
print("\n[Step 4] Testing vector search for new skill...")
time.sleep(1)  # Wait for embeddings
results = skill_index.search_skills_by_intent("test hot reload", top_k=3)
print(f"Search results: {results}")

if "test-hot-reload" in results:
    print("✓ New skill is searchable!")
else:
    print("⚠ New skill not in search results (embeddings may still be generating)")

# Step 6: Test modifying existing skill
print("\n[Step 5] Testing SKILL.md modification detection...")
time.sleep(1)

# Modify the skill content
modified_content = test_skill_content.replace(
    "Test skill for hot-reload verification",
    "MODIFIED: Updated description for testing"
)
with open(skill_md_path, 'w') as f:
    f.write(modified_content)

print("✓ Modified SKILL.md content")
time.sleep(0.5)

# Check if modification is detected
refreshed_again = skill_index.refresh_if_needed()
if refreshed_again:
    print("✓ File modification detected!")
    metadata = skill_index.get_skill_metadata("test-hot-reload")
    if metadata and "MODIFIED" in metadata.description:
        print("✓ Updated description loaded correctly!")
    else:
        print("⚠ Description not updated (may need to check parsing)")
else:
    print("✗ File modification NOT detected")

# Cleanup
print("\n[Cleanup] Removing test skill...")
import shutil
shutil.rmtree(test_skill_dir)
print("✓ Test skill removed")

# Final refresh to remove from index
skill_index.refresh_if_needed()
final_count = len(skill_index.skills)
print(f"✓ Final skill count: {final_count} (should be {initial_count})")

print("\n" + "=" * 60)
print("Hot-reload test completed!")
print("=" * 60)
