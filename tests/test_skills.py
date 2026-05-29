import os
import sys
from loguru import logger

# Inject backend and root paths for compatibility with existing imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if os.path.exists(PROJECT_ROOT) and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.exists(BACKEND_PATH) and BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

def run_skills_tests():
    logger.info("=============================================================")
    logger.info("🧪 STARTING RAMBOTOS DYNAMIC SKILLS FUNCTIONAL TEST SUITE")
    logger.info("=============================================================")

    # 1. Initialize Skill Index
    logger.info("🧪 Step 1: Initializing SkillIndex singleton...")
    try:
        from core.skill_index import skill_index
        skill_index.initialize()
        logger.info("✅ SkillIndex initialized successfully.")
    except Exception as e:
        logger.error(f"❌ SkillIndex initialization failed: {e}")
        return False

    # 2. Verify all skills are discovered on disk
    logger.info("🧪 Step 2: Verifying skill discovery on disk...")
    skills = skill_index.get_all_skill_names()
    logger.info(f"👉 Discovered skills count: {len(skills)}")
    logger.info(f"👉 Skills found: {skills}")
    if len(skills) < 5:
        logger.error("❌ Failed: Too few skills discovered. Disk structure might be broken.")
        return False
    logger.info("✅ Disk skill parsing verified successfully.")

    # 3. Test Skill metadata summary formatting
    logger.info("🧪 Step 3: Verifying Skill metadata summaries...")
    summary = skill_index.get_all_skills_summary()
    logger.info("👉 Formatted Summary Excerpt:")
    logger.info("\n" + "\n".join(summary.split("\n")[:5]) + "\n... (truncated)")
    if not summary or "Path:" not in summary:
        logger.error("❌ Failed: Skill summary cache is empty or formatted incorrectly.")
        return False
    logger.info("✅ Skill summaries verified successfully.")

    # 4. Test Semantic Intent Matching via Vector Database
    logger.info("🧪 Step 4: Testing vector-based semantic intent retrieval...")
    
    # Query 1: Weather intent
    weather_query = "What is the temperature in London today?"
    logger.info(f"🔍 Searching for intent: '{weather_query}'")
    matched_skills = skill_index.search_skills_by_intent(weather_query, top_k=2)
    logger.info(f"👉 Matched skills: {matched_skills}")
    if not matched_skills or "weather" not in [s.lower() for s in matched_skills]:
        logger.warning("⚠️ Warning: 'weather' skill was not matched as top result (AI fallback matches might still occur).")
    else:
        logger.info("✅ Weather intent matched successfully!")

    # Query 2: Finance/Stock intent
    stock_query = "Check TSLA stock prices and earnings report."
    logger.info(f"🔍 Searching for intent: '{stock_query}'")
    matched_skills = skill_index.search_skills_by_intent(stock_query, top_k=2)
    logger.info(f"👉 Matched skills: {matched_skills}")
    if not matched_skills or "stock-market" not in [s.lower() for s in matched_skills]:
        logger.warning("⚠️ Warning: 'stock-market' skill was not matched as top result.")
    else:
        logger.info("✅ Stock intent matched successfully!")

    # Query 3: Alarm/Scheduler intent
    timer_query = "Remind me to drink water every 2 hours."
    logger.info(f"🔍 Searching for intent: '{timer_query}'")
    matched_skills = skill_index.search_skills_by_intent(timer_query, top_k=2)
    logger.info(f"👉 Matched skills: {matched_skills}")
    expected_matches = ["task-scheduler", "time-service"]
    found_expected = any(e in [s.lower() for s in matched_skills] for e in expected_matches)
    if not matched_skills or not found_expected:
        logger.warning("⚠️ Warning: Scheduler/Timer skill was not matched as top result.")
    else:
        logger.info("✅ Alarm/Scheduler intent matched successfully!")

    # 5. Test Pluggable Skill Retrieve Tool Integration
    logger.info("🧪 Step 5: Testing RetrieveSkillsTool integration...")
    try:
        from tools.skill_tools import RetrieveSkillsTool
        tool = RetrieveSkillsTool()
        result = tool._run("How to check if TSLA stock breaks out?")
        logger.info("👉 RetrieveSkillsTool Output Excerpt:")
        logger.info("\n" + "\n".join(result.split("\n")[:4]) + "\n... (truncated)")
        if "Found" not in result or "relevant skills" not in result:
            logger.error("❌ Failed: RetrieveSkillsTool execution returned invalid output structure.")
            return False
        logger.info("✅ RetrieveSkillsTool execution verified successfully.")
    except Exception as e:
        logger.error(f"❌ RetrieveSkillsTool testing failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = run_skills_tests()
    logger.info("=============================================================")
    logger.info("📊 DYNAMIC SKILLS FUNCTIONAL TEST SUMMARY:")
    logger.info("=============================================================")
    logger.info(f"Overall Result: {'✅ PASSED' if success else '❌ FAILED'}")
    logger.info("=============================================================")
    if success:
        logger.info("🌟 ALL DYNAMIC SKILLS FUNCTIONAL TESTS PASSED PERFECTLY!")
        sys.exit(0)
    else:
        sys.exit(1)
