"""
GitHub integration for the Dashboard extension.

This module provides GitHub API integration for project discovery, repository
management, and PR/issue tracking within the dashboard system.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import aiohttp
    import asyncio
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

from .models import Project, PRInfo, PRStatus

logger = logging.getLogger(__name__)


class GitHubProjectManager:
    """GitHub project management for the dashboard."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub project manager.
        
        Args:
            token: GitHub access token. If None, uses environment variable.
        """
        self.token = token or os.getenv("GITHUB_ACCESS_TOKEN")
        self.base_url = "https://api.github.com"
        self.session = None
        
        if not self.token:
            logger.warning("GitHub token not provided. Some features may not work.")
    
    async def initialize(self):
        """Initialize the GitHub manager."""
        if AIOHTTP_AVAILABLE and self.token:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Contexten-Dashboard/1.0"
                }
            )
            logger.info("GitHub project manager initialized")
        else:
            logger.warning("GitHub project manager not fully initialized (missing dependencies or token)")
    
    async def get_user_repositories(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get all repositories for the authenticated user.
        
        Args:
            per_page: Number of repositories per page (max 100)
            
        Returns:
            List of repository data dictionaries
        """
        if not self.session:
            logger.error("GitHub session not initialized")
            return []
        
        try:
            repositories = []
            page = 1
            
            while True:
                url = f"{self.base_url}/user/repos"
                params = {
                    "per_page": per_page,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc"
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch repositories: {response.status}")
                        break
                    
                    repos = await response.json()
                    if not repos:
                        break
                    
                    for repo in repos:
                        repositories.append({
                            "id": repo["id"],
                            "name": repo["name"],
                            "full_name": repo["full_name"],
                            "description": repo.get("description"),
                            "url": repo["html_url"],
                            "clone_url": repo["clone_url"],
                            "default_branch": repo["default_branch"],
                            "language": repo.get("language"),
                            "private": repo["private"],
                            "fork": repo["fork"],
                            "archived": repo["archived"],
                            "disabled": repo["disabled"],
                            "created_at": repo["created_at"],
                            "updated_at": repo["updated_at"],
                            "pushed_at": repo.get("pushed_at"),
                            "size": repo["size"],
                            "stargazers_count": repo["stargazers_count"],
                            "watchers_count": repo["watchers_count"],
                            "forks_count": repo["forks_count"],
                            "open_issues_count": repo["open_issues_count"]
                        })
                    
                    page += 1
            
            logger.info(f"Retrieved {len(repositories)} repositories from GitHub")
            return repositories
            
        except Exception as e:
            logger.error(f"Failed to get user repositories: {e}")
            return []
    
    async def get_repository_details(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository details dictionary or None if not found
        """
        if not self.session:
            return None
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get repository details: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get repository details: {e}")
            return None
    
    async def get_repository_prs(self, owner: str, repo: str, state: str = "all") -> List[Dict[str, Any]]:
        """Get pull requests for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state ('open', 'closed', 'all')
            
        Returns:
            List of pull request data dictionaries
        """
        if not self.session:
            return []
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            params = {"state": state, "per_page": 100}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    prs = await response.json()
                    
                    pr_list = []
                    for pr in prs:
                        pr_list.append({
                            "id": pr["id"],
                            "number": pr["number"],
                            "title": pr["title"],
                            "description": pr.get("body", ""),
                            "state": pr["state"],
                            "url": pr["html_url"],
                            "branch_name": pr["head"]["ref"],
                            "base_branch": pr["base"]["ref"],
                            "author": pr["user"]["login"],
                            "created_at": pr["created_at"],
                            "updated_at": pr["updated_at"],
                            "merged_at": pr.get("merged_at"),
                            "draft": pr.get("draft", False),
                            "mergeable": pr.get("mergeable"),
                            "mergeable_state": pr.get("mergeable_state"),
                            "commits": pr.get("commits", 0),
                            "additions": pr.get("additions", 0),
                            "deletions": pr.get("deletions", 0),
                            "changed_files": pr.get("changed_files", 0)
                        })
                    
                    return pr_list
                else:
                    logger.error(f"Failed to get repository PRs: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to get repository PRs: {e}")
            return []
    
    async def create_pull_request(
        self, 
        owner: str, 
        repo: str, 
        title: str, 
        body: str, 
        head: str, 
        base: str = "main"
    ) -> Optional[Dict[str, Any]]:
        """Create a new pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head: Source branch
            base: Target branch
            
        Returns:
            Created PR data dictionary or None if failed
        """
        if not self.session:
            return None
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            data = {
                "title": title,
                "body": body,
                "head": head,
                "base": base
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 201:
                    pr = await response.json()
                    logger.info(f"Created PR #{pr['number']}: {title}")
                    return pr
                else:
                    error_data = await response.json()
                    logger.error(f"Failed to create PR: {response.status} - {error_data}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            return None
    
    async def create_issue(
        self, 
        owner: str, 
        repo: str, 
        title: str, 
        body: str, 
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue description
            labels: List of label names
            assignees: List of assignee usernames
            
        Returns:
            Created issue data dictionary or None if failed
        """
        if not self.session:
            return None
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues"
            data = {
                "title": title,
                "body": body
            }
            
            if labels:
                data["labels"] = labels
            if assignees:
                data["assignees"] = assignees
            
            async with self.session.post(url, json=data) as response:
                if response.status == 201:
                    issue = await response.json()
                    logger.info(f"Created issue #{issue['number']}: {title}")
                    return issue
                else:
                    error_data = await response.json()
                    logger.error(f"Failed to create issue: {response.status} - {error_data}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None
    
    async def get_repository_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get branches for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of branch data dictionaries
        """
        if not self.session:
            return []
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/branches"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    branches = await response.json()
                    return [
                        {
                            "name": branch["name"],
                            "sha": branch["commit"]["sha"],
                            "protected": branch.get("protected", False)
                        }
                        for branch in branches
                    ]
                else:
                    logger.error(f"Failed to get repository branches: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to get repository branches: {e}")
            return []
    
    async def handle_event(self, event_type: str, payload: Dict[str, Any]):
        """Handle GitHub webhook events.
        
        Args:
            event_type: Type of GitHub event
            payload: Event payload data
        """
        try:
            logger.info(f"Handling GitHub event: {event_type}")
            
            if event_type == "pull_request":
                await self._handle_pr_event(payload)
            elif event_type == "issues":
                await self._handle_issue_event(payload)
            elif event_type == "push":
                await self._handle_push_event(payload)
            else:
                logger.info(f"Unhandled GitHub event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Failed to handle GitHub event: {e}")
    
    async def _handle_pr_event(self, payload: Dict[str, Any]):
        """Handle pull request events."""
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        
        logger.info(f"PR event: {action} - #{pr.get('number')} {pr.get('title')}")
        
        # TODO: Update database with PR information
        # TODO: Trigger workflow updates if needed
    
    async def _handle_issue_event(self, payload: Dict[str, Any]):
        """Handle issue events."""
        action = payload.get("action")
        issue = payload.get("issue", {})
        
        logger.info(f"Issue event: {action} - #{issue.get('number')} {issue.get('title')}")
        
        # TODO: Update database with issue information
        # TODO: Trigger workflow updates if needed
    
    async def _handle_push_event(self, payload: Dict[str, Any]):
        """Handle push events."""
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])
        
        logger.info(f"Push event: {ref} - {len(commits)} commits")
        
        # TODO: Trigger code analysis if needed
        # TODO: Update workflow status
    
    async def cleanup(self):
        """Cleanup GitHub manager resources."""
        if self.session:
            await self.session.close()
            logger.info("GitHub project manager cleaned up")

