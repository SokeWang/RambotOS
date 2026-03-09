import os
import argparse
import subprocess

def download_from_hf(repo_id, local_dir):
    """
    Download a dataset path from Hugging Face using huggingface-cli.
    """
    print(f"Downloading {repo_id} from Hugging Face to {local_dir}...")
    # This requires huggingface-cli to be installed in the environment
    cmd = f"uv run huggingface-cli download {repo_id} --local-dir {local_dir} --local-dir-use-symlinks False"
    subprocess.run(cmd, shell=True, check=True)

def download_from_github(repo_url, local_dir):
    """
    Clone a repository or download specific data from GitHub.
    """
    print(f"Cloning {repo_url} to {local_dir}...")
    cmd = f"git clone {repo_url} {local_dir}"
    subprocess.run(cmd, shell=True, check=True)

def generate_llm_data(prompt, output_file):
    """
    Hook for LLM-based data generation. 
    This would typically call an LLM API to generate synthetic data.
    """
    print(f"Generating LLM data based on prompt: {prompt}")
    # Placeholder for LLM integration
    with open(output_file, 'w') as f:
        f.write(f"Synthetic data generated for prompt: {prompt}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generic Data Utilities for Algorithm Engineering")
    parser.add_argument("--source", type=str, choices=["hf", "github", "llm"], required=True)
    parser.add_argument("--id", type=str, required=True, help="HF repo ID, GitHub URL, or LLM prompt")
    parser.add_argument("--output", type=str, required=True, help="Output directory or file")
    
    args = parser.parse_args()
    
    if args.source == "hf":
        download_from_hf(args.id, args.output)
    elif args.source == "github":
        download_from_github(args.id, args.output)
    elif args.source == "llm":
        generate_llm_data(args.id, args.output)
