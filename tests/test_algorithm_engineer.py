import os
import sys
import shutil
import subprocess
from loguru import logger

# Inject root paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if os.path.exists(PROJECT_ROOT) and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_algo_engineer_test():
    logger.info("=============================================================")
    logger.info("🧪 STARTING RAMBOTOS ALGORITHM ENGINEER FUNCTIONAL TEST")
    logger.info("=============================================================")

    # 1. Verify files exist
    logger.info("🧪 Step 1: Locating Algorithm Engineer skill utilities...")
    algo_skill_dir = os.path.join(PROJECT_ROOT, "skills", "algorithm-engineer")
    init_script_path = os.path.join(algo_skill_dir, "scripts", "initialize_project.py")
    
    if not os.path.exists(init_script_path):
        logger.error(f"❌ Failed: initialize_project.py not found at {init_script_path}")
        return False
    logger.info("✅ Core initialization script located successfully.")

    # 2. Run initialize_project.py
    logger.info("🧪 Step 2: Running initialize_project.py to bootstrap sandbox workspace...")
    test_project_name = "test_algo_sandbox"
    python_exec = sys.executable
    
    cmd = f"{python_exec} {init_script_path} --name {test_project_name} --description 'E2E integration test workspace'"
    logger.info(f"👉 Executing command: {cmd}")
    
    try:
        result = subprocess.run(
            [python_exec, init_script_path, "--name", test_project_name, "--description", "E2E integration test workspace"],
            capture_output=True,
            text=True,
            check=False
        )
        logger.info("👉 Script Output:")
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(f"Script Warning/Error: {result.stderr}")
            
    except Exception as exec_err:
        logger.error(f"❌ Execution failed: {exec_err}")
        return False

    # 3. Verify folders were created
    logger.info("🧪 Step 3: Verifying workspace file structure creation...")
    project_path = os.path.join(algo_skill_dir, "projects", test_project_name)
    
    if not os.path.exists(project_path):
        logger.error(f"❌ Failed: Project workspace folder not created at {project_path}")
        return False
        
    # Check standard folders
    expected_subdirs = ["data", "logs", "src", "models"]
    for sd in expected_subdirs:
        sd_path = os.path.join(project_path, sd)
        if not os.path.exists(sd_path):
            logger.error(f"❌ Failed: Expected workspace subdirectory '{sd}' not found at {sd_path}")
            return False
            
    logger.info("✅ Standard subdirectories (data, logs, src, models) verified successfully.")

    # 4. Clean up test assets
    logger.info("🧪 Step 4: Cleaning up sandbox project folder...")
    try:
        shutil.rmtree(project_path)
        logger.info("✅ Sandbox project deleted cleanly. Repository is clean.")
    except Exception as cleanup_err:
        logger.warning(f"⚠️ Cleanup warning (could not delete test project): {cleanup_err}")

    return True

if __name__ == "__main__":
    success = run_algo_engineer_test()
    logger.info("=============================================================")
    logger.info("📊 ALGORITHM ENGINEER FUNCTIONAL TEST SUMMARY:")
    logger.info("=============================================================")
    logger.info(f"Overall Result: {'✅ PASSED' if success else '❌ FAILED'}")
    logger.info("=============================================================")
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
