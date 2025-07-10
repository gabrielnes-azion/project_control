# Project Control - Team Activity CLI

CLI tool to fetch team activities from Jira and GitHub.

## Setup

1. Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure credentials:
```bash
cp .env.example .env
# Edit the .env file with your credentials

```

3. Configure environment variables:
- `JIRA_BASE_URL`: Your Jira base URL (e.g., https://company.atlassian.net)
- `JIRA_USERNAME`: Your Jira email
- `JIRA_API_TOKEN`: Jira API token
- `GITHUB_TOKEN`: GitHub Personal Access Token

## Usage

```bash
# Fetch activities from the last day for the API team
python main.py --team=api

# Fetch activities from the last 7 days
python main.py --team=api --days=7

# Enable verbose output for debugging
python main.py --team=api --verbose
```

## Parameters

- `--team`: Team slug (required)
- `--days`: Number of days to look back (default: 1)
- `--verbose`: Enable verbose debug output
