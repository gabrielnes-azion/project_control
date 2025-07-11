#!/usr/bin/env python3
"""
CLI tool to fetch team activities from Jira and GitHub
"""
import argparse
import os
from datetime import datetime, timedelta
from typing import List, Dict
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from teams import teams
from jira_client import JiraClient
from github_client import GitHubClient


def get_team_by_slug(slug: str) -> Dict:
    """Get team configuration by slug"""
    for team in teams:
        if team["slug"] == slug:
            return team
    return None


def debug_print(message, verbose=False):
    """Print debug messages in cyan color"""
    if verbose:
        print(f"\033[96m[DEBUG] {message}\033[0m")


def main():
    parser = argparse.ArgumentParser(description="Fetch team activities from Jira and GitHub")
    parser.add_argument("--team", required=True, help="Team slug (e.g., api)")
    parser.add_argument("--days", type=int, default=1, help="Number of days to look back (default: 1)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug output")
    parser.add_argument("--only-title", action="store_true", help="Show only Jira issue titles without changes")
    
    args = parser.parse_args()
    verbose = args.verbose
    
    # Get team configuration
    debug_print(f"Looking for team with slug: {args.team}", verbose)
    team = get_team_by_slug(args.team)
    if not team:
        print(f"Team '{args.team}' not found")
        sys.exit(1)
    
    debug_print(f"Found team: {team['team_name']} with {len(team['members'])} members and {len(team['projects'])} projects", verbose)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    print(f"Fetching activities for team '{team['team_name']}' from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("-" * 80)
    
    # Initialize clients
    debug_print("Initializing Jira client...", verbose)
    jira_client = JiraClient()
    debug_print("Initializing GitHub client...", verbose)
    github_client = GitHubClient()
    
    # Initialize GitHub client
    known_github_users = {member["github_user"] for member in team["members"]}
    
    # Pre-load GitHub cache for all repositories
    debug_print("Pre-loading GitHub cache for all repositories...", verbose)
    for project in team["projects"]:
        repo_name = project["url"].split("/")[-1]
        try:
            debug_print(f"Caching PRs for repository: {repo_name}", verbose)
            github_client.get_all_pull_requests(repo_name, start_date, end_date, verbose)
        except Exception as e:
            debug_print(f"Error caching {repo_name}: {e}", verbose)
            print(f"⚠️ Warning: Could not cache {repo_name}: {e}")
    
    debug_print("Cache pre-loading completed!", verbose)
    
    # Fetch activities for each team member
    debug_print(f"Starting to process {len(team['members'])} team members...", verbose)
    for i, member in enumerate(team["members"], 1):
        email = member["email"]
        github_user = member["github_user"]
        
        print(f"\n👤 {email}")
        print("-" * 40)
        debug_print(f"Processing member {i}/{len(team['members'])}: {email} (@{github_user})", verbose)
        
        # Fetch Jira activities
        debug_print(f"Fetching Jira activities for {email}...", verbose)
        try:
            jira_issues = jira_client.get_user_activities(email, start_date, end_date, verbose)
            debug_print(f"Found {len(jira_issues)} Jira issues for {email}", verbose)
            if jira_issues:
                print("📋 Jira Activities:")
                for issue in jira_issues:
                    print(f"  • {issue['key']}: {issue['summary']}")
                    if not args.only_title and issue.get('changes'):
                        for change in issue['changes']:
                            print(f"    └─ {change}")
            else:
                print("📋 No Jira activities found")
        except Exception as e:
            print(f"❌ Error fetching Jira activities: {e}")
        
        # Fetch GitHub activities (Pull Requests only)
        debug_print(f"Fetching GitHub Pull Requests for {github_user}...", verbose)
        debug_print(f"Will check {len(team['projects'])} repositories...", verbose)
        try:
            all_prs = []
            
            for j, project in enumerate(team["projects"], 1):
                repo_name = project["url"].split("/")[-1]
                debug_print(f"Checking repo {j}/{len(team['projects'])}: {repo_name}", verbose)
                try:
                    # Get PRs created by user
                    debug_print(f"Fetching PRs from {repo_name} for {github_user}...", verbose)
                    prs = github_client.get_user_pull_requests(repo_name, github_user, start_date, end_date, verbose)
                    debug_print(f"Found {len(prs)} PRs in {repo_name}", verbose)
                    all_prs.extend(prs)
                except Exception as e:
                    debug_print(f"Error in {repo_name}: {e}", verbose)
                    print(f"❌ Error fetching from {repo_name}: {e}")
            
            # Show Pull Requests
            debug_print(f"Total PRs found for {github_user}: {len(all_prs)}", verbose)
            if all_prs:
                print("🔄 Pull Requests:")
                for pr in all_prs:
                    print(f"  • [{pr['repo']}] PR #{pr['number']}: {pr['title'][:50]}... ({pr['state']})")
            else:
                print("🔄 No Pull Requests found")
                
        except Exception as e:
            debug_print(f"GitHub API error for {github_user}: {e}", verbose)
            print(f"❌ Error fetching GitHub activities: {e}")
        
        debug_print(f"Completed processing member {i}/{len(team['members'])}: {email}", verbose)


if __name__ == "__main__":
    main()
