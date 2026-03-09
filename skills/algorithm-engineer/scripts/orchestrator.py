import os
import subprocess
import time
import argparse
import sys

def run_command(command, cwd=None):
    print(f"Executing: {command} in {cwd or '.'}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    return process.returncode

def get_success_rate(output):
    # Parse success rate from output
    for line in output.split('\n'):
        if "Final Success Rate:" in line:
            return float(line.split(":")[1].replace('%', '').strip()) / 100.0
    return 0.0

def orchestrate(project_path, task_name, target_success, max_iter):
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_path = os.path.abspath(project_path)
    
    if not os.path.exists(project_path):
        print(f"Error: Project path '{project_path}' does not exist.")
        sys.exit(1)

    print(f"Orchestrating task: {task_name} in project: {project_path}")
    
    current_success = 0.0
    iteration = 0
    
    while current_success < target_success and iteration < max_iter:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        
        # 1. Data Collection (if applicable)
        # Try to run collect_data.py if it exists in project src or skill scripts
        collect_script = os.path.join(project_path, "src", "collect_data.py")
        if not os.path.exists(collect_script):
            collect_script = os.path.join(skill_dir, "scripts", "collect_data.py")
        
        if os.path.exists(collect_script):
             run_command(f"uv run python {collect_script} --num_trajectories 500", cwd=project_path)
        
        # 2. Training
        train_script = os.path.join(project_path, "src", "train.py")
        if not os.path.exists(train_script):
             train_script = os.path.join(project_path, "train.py") # Legacy fallback
             
        if os.path.exists(train_script):
            run_command(f"uv run python {train_script}", cwd=project_path)
        else:
            print(f"Warning: No train script found in {project_path}")
        
        # 3. Evaluation
        test_script = os.path.join(project_path, "src", "test.py")
        if not os.path.exists(test_script):
            test_script = os.path.join(project_path, "test.py") # Legacy fallback

        if os.path.exists(test_script):
            print(f"Running evaluation...")
            try:
                result = subprocess.check_output(f"uv run python {test_script} --episodes 20", shell=True, text=True, cwd=project_path)
                print(result)
                current_success = get_success_rate(result)
            except subprocess.CalledProcessError as e:
                print(f"Evaluation failed: {e}")
                current_success = 0.0
        else:
            print(f"Warning: No test script found in {project_path}")
            iteration = max_iter # Stop if we can't evaluate
        
        print(f"Current Success Rate: {current_success*100:.2f}%")
        
        if current_success >= target_success:
            print(f"Target reached: {current_success*100:.2f}% >= {target_success*100:.2f}%")
            break
        else:
            print("Target not reached. Adjusting for next iteration...")
            # Automatically adjusting parameters could be implemented here
            
    print("Orchestration finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=str, required=True, help="Path to the project directory")
    parser.add_argument("--task", type=str, default="Algorithm Optimization")
    parser.add_argument("--target", type=float, default=0.98)
    parser.add_argument("--max_iter", type=int, default=5)
    args = parser.parse_args()
    orchestrate(args.project, args.task, args.target, args.max_iter)
