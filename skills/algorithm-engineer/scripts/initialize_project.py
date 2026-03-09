import os
import subprocess
import argparse
import sys

def run_command(command, cwd=None):
    print(f"Executing: {command} in {cwd or '.'}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    return process.returncode

def initialize_project(name, description):
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    projects_dir = os.path.join(skill_dir, "projects")
    project_path = os.path.join(projects_dir, name)

    if os.path.exists(project_path):
        print(f"Error: Project '{name}' already exists at {project_path}")
        sys.exit(1)

    os.makedirs(project_path, exist_ok=True)
    
    print(f"Initializing uv project in {project_path}...")
    run_command("uv init", cwd=project_path)

    # Standard directories
    for d in ["data", "logs", "src", "models"]:
        os.makedirs(os.path.join(project_path, d), exist_ok=True)

    print(f"Project '{name}' initialized successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a new algorithm project.")
    parser.add_argument("--name", type=str, required=True, help="Name of the project")
    parser.add_argument("--description", type=str, default="New algorithm project", help="Project description")
    args = parser.parse_args()
    initialize_project(args.name, args.description)
