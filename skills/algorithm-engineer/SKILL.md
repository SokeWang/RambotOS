# Skill: Algorithm Engineer

An autonomous agent for algorithm research, implementation, evaluation, and iterative optimization. This agent follows a research-driven workflow to select and implement the best move for each task.

## Capabilities:
1. **Research & Design**: Search for state-of-the-art papers, GitHub repositories, and benchmarks to design an approach tailored to the user's task.
2. **Project-Based Development**: Each task is treated as a project with its own isolated `uv` environment.
3. **Flexible Implementation**: Writes project-specific scripts for data collection, training, and evaluation based on the research findings.
4. **Data Acquisition**: Uses generic utilities to fetch data from Hugging Face, GitHub, or generate synthetic data via LLMs.
5. **Iterative Optimization**: Orchestrates loops to tune models, hyperparameters, and architectures.

## Usage Workflow:

### 1. Initialize Project
Create a new project workspace to isolate environment and assets.
```bash
python scripts/initialize_project.py --name <project_name>
```

### 2. Research & Design
1. **Research**: Conduct thorough research on SOTA methods, papers, and existing implementations (using `web_search`).
2. **Document Research**: Generate `projects/<project_name>/Research.md` summarising the findings and proposed approach.

### 3. Implementation Planning
1. **Plan**: Based on `Research.md`, create a detailed technical plan.
2. **Document Plan**: Generate `projects/<project_name>/Implementation Plan.md` outlining scripts, dependencies, and verification steps.

### 4. Progressive Implementation
Implement the project following the `Implementation Plan.md`:
1. **Data Acquisition**: Fetch or generate data using `scripts/data_utils.py` or project-specific `src/collect_data.py`.
2. **Core Logic**: Implement model architecture and training loops in `src/train.py`.
3. **Evaluation**: Implement metrics and testing in `src/test.py`.

### 5. Orchestrated Iteration
Run the orchestrator to manage and optimize the implementation loop.
```bash
python scripts/orchestrator.py --project projects/<project_name> --task "<task_description>" --target <metric>
```

## Global Utilities:
- `scripts/initialize_project.py`: Project setup.
- `scripts/orchestrator.py`: Main execution engine.
- `scripts/data_utils.py`: Generic helpers for data fetching (HF, GitHub).

## Project Structure:
- `projects/<project_name>/`
  - `Research.md`: Findings and design decisions.
  - `Implementation Plan.md`: Technical roadmap.
  - `pyproject.toml`: Local dependencies.
  - `src/`: Custom algorithm implementations.
  - `data/`, `models/`, `logs/`: Project assets.
