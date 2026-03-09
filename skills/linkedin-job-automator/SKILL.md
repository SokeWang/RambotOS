---
name: linkedin-job-automator
description: "Automates job searching and application on LinkedIn for specific roles and locations using a provided resume. Use this skill when the user wants to: (1) Search for job postings on LinkedIn, (2) Automatically apply to 'Easy Apply' jobs, or (3) Generate LinkedIn search URLs for specific roles."
---

# LinkedIn Job Automator

This skill automates the process of finding and applying for jobs on LinkedIn.

## Setup

The automation uses Playwright and requires a logged-in LinkedIn session in your browser.

1. Ensure `playwright` is installed: `pip install playwright`
2. Install browser: `playwright install chromium`
3. The scripts will attempt to use your local Chrome profile to maintain your LinkedIn login state.

## Usage

### 1. Job Search

To search for jobs and list them:
```bash
python3 scripts/linkedin_search.py --keywords "Data Science, AI Engineer" --location "London, UK"
```

### 2. Automatic Application (Easy Apply)

To automatically apply to "Easy Apply" jobs:
```bash
python3 scripts/linkedin_apply.py --resume "~/Downloads/Peidong Wang CV.pdf" --limit 5
```

## Reference

User Preferences:
- **Roles**: Data Science, AI Engineer
- **Location**: London, UK
- **Resume Path**: ~/Downloads/Peidong Wang CV.pdf
