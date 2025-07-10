"""
GitHub API client for fetching user pull requests
"""
import os
import requests
import json
from datetime import datetime
from typing import List, Dict


class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        self.base_url = "https://api.github.com"
        self.cache_file = ".github_cache.json"
        self._cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def _get_cache_key(self, repo_name: str, start_date: datetime, end_date: datetime) -> str:
        """Generate cache key for repository and date range"""
        return f"{repo_name}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
    
    def get_all_pull_requests(self, repo_name: str, start_date: datetime, end_date: datetime, verbose: bool = False) -> List[Dict]:
        """Get all pull requests from repository within date range (with caching)"""
        
        cache_key = self._get_cache_key(repo_name, start_date, end_date)
        
        # Check cache first
        if cache_key in self._cache:
            if verbose:
                print(f"\033[92m[CACHE] Using cached data for {repo_name}\033[0m")
            return self._cache[cache_key]
        
        # Extract owner from repo URL structure (assuming aziontech organization)
        owner = "aziontech"
        
        url = f"{self.base_url}/repos/{owner}/{repo_name}/pulls"
        params = {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100
        }
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        if verbose:
            print(f"\033[93m[API] GET {url}\033[0m")
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
        
        prs_data = response.json()
        all_prs = []
        
        for pr in prs_data:
            pr_date = datetime.fromisoformat(pr["updated_at"].replace('Z', '+00:00')).replace(tzinfo=None)
            if start_date <= pr_date <= end_date:
                all_prs.append({
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "created_at": pr["created_at"],
                    "updated_at": pr["updated_at"],
                    "repo": repo_name,
                    "author": pr["user"]["login"]
                })
        
        # Cache the results
        self._cache[cache_key] = all_prs
        self._save_cache()
        
        return all_prs
    
    def get_user_pull_requests(self, repo_name: str, username: str, start_date: datetime, end_date: datetime, verbose: bool = False) -> List[Dict]:
        """Get pull requests created by user in repository within date range (uses cache)"""
        
        # Get all PRs from cache or API
        all_prs = self.get_all_pull_requests(repo_name, start_date, end_date, verbose)
        
        # Filter by username
        user_prs = [pr for pr in all_prs if pr["author"] == username]
        
        return user_prs
