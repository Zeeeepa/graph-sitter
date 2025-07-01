"""
Enhanced GitHub REST API Client

This module provides a comprehensive REST API client for GitHub with
advanced features like connection pooling, retry logic, and caching.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import asyncio
import base64
import json
import logging
import time

import aiohttp

from ...shared.logging.get_logger import get_logger
from .types import GitHubRepository, GitHubIssue, GitHubPullRequest, GitHubUser

logger = get_logger(__name__)

class EnhancedGitHubClient:
    """Enhanced GitHub REST API Client"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, max_retries: int = 3, timeout: int = 30):
        self.token = token
        self.max_retries = max_retries
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Contexten-GitHub-Client/1.0"
        }
    
    async def initialize(self) -> None:
        """Initialize the HTTP session"""
        if not self._session:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._headers
            )
            
            logger.info("GitHub REST client initialized")
    
    async def close(self) -> None:
        """Close the HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("GitHub REST client closed")
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retries"""
        if not self._session:
            await self.initialize()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self._session.request(method, url, **kwargs) as response:
                    if response.status == 200 or response.status == 201:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        response.raise_for_status()
            except Exception as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    raise
    
    # Repository methods
    async def get_repositories(self, org: Optional[str] = None, **params) -> List[GitHubRepository]:
        """Get repositories"""
        if org:
            endpoint = f"/orgs/{org}/repos"
        else:
            endpoint = "/user/repos"
        
        data = await self._request("GET", endpoint, params=params)
        return [GitHubRepository.from_dict(repo) for repo in data or []]
    
    async def get_repository(self, owner: str, repo: str) -> Optional[GitHubRepository]:
        """Get a specific repository"""
        data = await self._request("GET", f"/repos/{owner}/{repo}")
        return GitHubRepository.from_dict(data) if data else None
    
    async def create_repository(self, name: str, **kwargs) -> GitHubRepository:
        """Create a new repository"""
        data = {"name": name, **kwargs}
        result = await self._request("POST", "/user/repos", json=data)
        return GitHubRepository.from_dict(result)
    
    # Issue methods
    async def get_issues(self, owner: str, repo: str, **params) -> List[GitHubIssue]:
        """Get issues"""
        data = await self._request("GET", f"/repos/{owner}/{repo}/issues", params=params)
        return [GitHubIssue.from_dict(issue) for issue in data or []]
    
    async def create_issue(self, owner: str, repo: str, title: str, **kwargs) -> GitHubIssue:
        """Create an issue"""
        data = {"title": title, **kwargs}
        result = await self._request("POST", f"/repos/{owner}/{repo}/issues", json=data)
        return GitHubIssue.from_dict(result)
    
    async def update_issue(self, owner: str, repo: str, issue_number: int, **kwargs) -> GitHubIssue:
        """Update an issue"""
        result = await self._request("PATCH", f"/repos/{owner}/{repo}/issues/{issue_number}", json=kwargs)
        return GitHubIssue.from_dict(result)
    
    # Pull request methods
    async def get_pull_requests(self, owner: str, repo: str, **params) -> List[GitHubPullRequest]:
        """Get pull requests"""
        data = await self._request("GET", f"/repos/{owner}/{repo}/pulls", params=params)
        return [GitHubPullRequest.from_dict(pr) for pr in data or []]
    
    async def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, **kwargs) -> GitHubPullRequest:
        """Create a pull request"""
        data = {"title": title, "head": head, "base": base, **kwargs}
        result = await self._request("POST", f"/repos/{owner}/{repo}/pulls", json=data)
        return GitHubPullRequest.from_dict(result)
    
    async def update_pull_request(self, owner: str, repo: str, pr_number: int, **kwargs) -> GitHubPullRequest:
        """Update a pull request"""
        result = await self._request("PATCH", f"/repos/{owner}/{repo}/pulls/{pr_number}", json=kwargs)
        return GitHubPullRequest.from_dict(result)
    
    # Comment methods
    async def create_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> Dict[str, Any]:
        """Create an issue comment"""
        data = {"body": body}
        return await self._request("POST", f"/repos/{owner}/{repo}/issues/{issue_number}/comments", json=data)
    
    async def create_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        """Create a PR comment"""
        data = {"body": body}
        return await self._request("POST", f"/repos/{owner}/{repo}/issues/{pr_number}/comments", json=data)
    
    # User methods
    async def get_current_user(self) -> Optional[GitHubUser]:
        """Get current user"""
        data = await self._request("GET", "/user")
        return GitHubUser.from_dict(data) if data else None
    
    async def get_user(self, username: str) -> Optional[GitHubUser]:
        """Get a user"""
        data = await self._request("GET", f"/users/{username}")
        return GitHubUser.from_dict(data) if data else None
    
    # Organization methods
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Get user organizations"""
        return await self._request("GET", "/user/orgs") or []
    
    async def get_organization_repositories(self, org: str) -> List[GitHubRepository]:
        """Get organization repositories"""
        return await self.get_repositories(org=org)
    
    # Branch methods
    async def get_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository branches"""
        return await self._request("GET", f"/repos/{owner}/{repo}/branches") or []
    
    async def create_branch(self, owner: str, repo: str, branch_name: str, from_branch: str = "main") -> Dict[str, Any]:
        """Create a new branch"""
        # Get the SHA of the source branch
        ref_data = await self._request("GET", f"/repos/{owner}/{repo}/git/refs/heads/{from_branch}")
        sha = ref_data["object"]["sha"]
        
        # Create the new branch
        data = {"ref": f"refs/heads/{branch_name}", "sha": sha}
        return await self._request("POST", f"/repos/{owner}/{repo}/git/refs", json=data)
    
    # File methods
    async def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> Optional[Dict[str, Any]]:
        """Get file content"""
        params = {"ref": ref}
        return await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)
    
    async def create_or_update_file(self, owner: str, repo: str, path: str, content: str, message: str, branch: str = "main", sha: Optional[str] = None) -> Dict[str, Any]:
        """Create or update a file"""
        encoded_content = base64.b64encode(content.encode()).decode()
        data = {
            "message": message,
            "content": encoded_content,
            "branch": branch
        }
        if sha:
            data["sha"] = sha
        
        return await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=data)
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            await self.get_current_user()
            return True
        except Exception:
            return False

