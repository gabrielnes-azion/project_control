"""
Jira API client for fetching user activities
"""
import os
import requests
from datetime import datetime
from typing import List, Dict
from requests.auth import HTTPBasicAuth


class JiraClient:
    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL")
        self.username = os.getenv("JIRA_USERNAME") 
        self.api_token = os.getenv("JIRA_API_TOKEN")
        
        if not all([self.base_url, self.username, self.api_token]):
            raise ValueError("Missing Jira credentials. Set JIRA_BASE_URL, JIRA_USERNAME, and JIRA_API_TOKEN")
    
    def get_user_activities(self, email: str, start_date: datetime, end_date: datetime, verbose: bool = False) -> List[Dict]:
        """Get Jira issues assigned to or updated by user in date range"""
        
        # Format dates for JQL
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # JQL query to find issues assigned to user in date range
        jql = f'assignee = "{email}" AND updated >= "{start_str}" AND updated <= "{end_str}"'
        if verbose:
            print(f"\033[93m[API] Jira JQL: {jql}\033[0m")
        
        url = f"{self.base_url}/rest/api/3/search"
        params = {
            "jql": jql,
            "fields": "key,summary,status,assignee,updated",
            "expand": "changelog",
            "maxResults": 100
        }
        
        response = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(self.username, self.api_token),
            headers={"Accept": "application/json"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Jira API error: {response.status_code} - {response.text}")
        
        data = response.json()
        issues = []
        
        for issue in data.get("issues", []):
            # Get recent changes from changelog
            recent_changes = []
            if "changelog" in issue and "histories" in issue["changelog"]:
                for history in issue["changelog"]["histories"]:
                    history_date = datetime.fromisoformat(history["created"].replace('Z', '+00:00'))
                    if start_date <= history_date.replace(tzinfo=None) <= end_date:
                        for item in history.get("items", []):
                            # Skip description field and Bug Template changes
                            if item['field'] in ['description', 'Bug Template']:
                                continue
                            change_desc = f"{item['field']}: {item.get('fromString', 'None')} → {item.get('toString', 'None')}"
                            recent_changes.append(change_desc)
            
            issues.append({
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "status": issue["fields"]["status"]["name"],
                "updated": issue["fields"]["updated"],
                "changes": recent_changes
            })
        
        return issues
