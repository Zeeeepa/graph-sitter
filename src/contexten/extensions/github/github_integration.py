#!/usr/bin/env python3
"""
GitHub Integration Module
Handles GitHub API interactions, repository management, PR operations, and issue tracking.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import aiohttp
from datetime import datetime

from ..base.interfaces import BaseExtension

logger = logging.getLogger(__name__)


class GitHubIntegration(BaseExtension):
    """GitHub integration for repository and project management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.github_token = self.config.get("github_token") if self.config else None
        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _initialize_impl(self) -> None:
        """Initialize GitHub integration."""
        self.logger.info("Initializing GitHub integration")
        
        if not self.github_token:
            self.logger.warning("No GitHub token provided - some features may be limited")
            
        # Initialize HTTP session
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Contexten-GitHub-Integration"
        }
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
            
        self.session = aiohttp.ClientSession(headers=headers)
        
    async def _handle_impl(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Handle GitHub integration requests."""
        action = payload.get("action")
        
        if action == "list_repositories":
            return await self.list_repositories(
                payload.get("org"),
                payload.get("user")
            )
        elif action == "get_repository":
            repo_name = payload.get("repository")
            if not repo_name:
                return {"error": "repository name is required", "status": "failed"}
            return await self.get_repository(repo_name)
        elif action == "create_pr":
            return await self.create_pull_request(payload)
        elif action == "list_prs":
            repo_name = payload.get("repository")
            if not repo_name:
                return {"error": "repository name is required", "status": "failed"}
            return await self.list_pull_requests(repo_name, payload.get("state", "open"))
        elif action == "get_pr":
            repo_name = payload.get("repository")
            pr_number = payload.get("pr_number")
            if not repo_name or not pr_number:
                return {"error": "repository and pr_number are required", "status": "failed"}
            return await self.get_pull_request(repo_name, pr_number)
        elif action == "create_issue":
            return await self.create_issue(payload)
        elif action == "list_issues":
            repo_name = payload.get("repository")
            if not repo_name:
                return {"error": "repository name is required", "status": "failed"}
            return await self.list_issues(repo_name, payload.get("state", "open"))
        elif action == "get_commits":
            repo_name = payload.get("repository")
            if not repo_name:
                return {"error": "repository name is required", "status": "failed"}
            return await self.get_commits(repo_name, payload.get("branch", "main"))
        else:
            return {"error": f"Unknown action: {action}", "status": "failed"}
    
    async def list_repositories(self, org: Optional[str] = None, user: Optional[str] = None) -> Dict[str, Any]:
        """List repositories for an organization or user."""
        try:
            if org:
                url = f"{self.base_url}/orgs/{org}/repos"
            elif user:
                url = f"{self.base_url}/users/{user}/repos"
            else:
                url = f"{self.base_url}/user/repos"
                
            async with self.session.get(url) as response:
                if response.status == 200:
                    repos = await response.json()
                    return {
                        "repositories": [
                            {
                                "name": repo["name"],
                                "full_name": repo["full_name"],
                                "description": repo.get("description"),
                                "private": repo["private"],
                                "default_branch": repo["default_branch"],
                                "url": repo["html_url"],
                                "clone_url": repo["clone_url"],
                                "created_at": repo["created_at"],
                                "updated_at": repo["updated_at"],
                                "language": repo.get("language"),
                                "stars": repo["stargazers_count"],
                                "forks": repo["forks_count"]
                            }
                            for repo in repos
                        ],
                        "status": "success"
                    }
                else:
                    error_data = await response.json()
                    return {"error": error_data.get("message", "Failed to fetch repositories"), "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error listing repositories: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def get_repository(self, repo_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific repository."""
        try:
            url = f"{self.base_url}/repos/{repo_name}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    repo = await response.json()
                    return {
                        "repository": {
                            "name": repo["name"],
                            "full_name": repo["full_name"],
                            "description": repo.get("description"),
                            "private": repo["private"],
                            "default_branch": repo["default_branch"],
                            "url": repo["html_url"],
                            "clone_url": repo["clone_url"],
                            "created_at": repo["created_at"],
                            "updated_at": repo["updated_at"],
                            "language": repo.get("language"),
                            "stars": repo["stargazers_count"],
                            "forks": repo["forks_count"],
                            "open_issues": repo["open_issues_count"],
                            "size": repo["size"],
                            "topics": repo.get("topics", [])
                        },
                        "status": "success"
                    }
                else:
                    error_data = await response.json()
                    return {"error": error_data.get("message", "Repository not found"), "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error getting repository {repo_name}: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def create_pull_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pull request."""
        try:
            repo_name = payload.get("repository")
            title = payload.get("title")
            body = payload.get("body", "")
            head = payload.get("head")  # source branch
            base = payload.get("base", "main")  # target branch
            
            if not all([repo_name, title, head]):
                return {"error": "repository, title, and head branch are required", "status": "failed"}
            
            url = f"{self.base_url}/repos/{repo_name}/pulls"
            data = {
                "title": title,
                "body": body,
                "head": head,
                "base": base
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 201:
                    pr = await response.json()
                    return {
                        "pull_request": {
                            "number": pr["number"],
                            "title": pr["title"],
                            "body": pr["body"],
                            "state": pr["state"],
                            "url": pr["html_url"],
                            "head": pr["head"]["ref"],
                            "base": pr["base"]["ref"],
                            "created_at": pr["created_at"],
                            "user": pr["user"]["login"]
                        },
                        "status": "success"
                    }
                else:
                    error_data = await response.json()
                    return {"error": error_data.get("message", "Failed to create PR"), "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error creating pull request: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def list_pull_requests(self, repo_name: str, state: str = "open") -> Dict[str, Any]:
        """List pull requests for a repository."""
        try:
            url = f"{self.base_url}/repos/{repo_name}/pulls"
            params = {"state": state}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    prs = await response.json()
                    return {
                        "pull_requests": [
                            {
                                "number": pr["number"],
                                "title": pr["title"],
                                "state": pr["state"],
                                "url": pr["html_url"],
                                "head": pr["head"]["ref"],
                                "base": pr["base"]["ref"],
                                "created_at": pr["created_at"],
                                "updated_at": pr["updated_at"],
                                "user": pr["user"]["login"],
                                "mergeable": pr.get("mergeable"),
                                "draft": pr.get("draft", False)
                            }
                            for pr in prs
                        ],
                        "status": "success"
                    }
                else:
                    error_data = await response.json()
                    return {"error": error_data.get("message", "Failed to fetch PRs"), "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error listing pull requests: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def get_pull_request(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Get detailed information about a specific pull request."""
        try:
            url = f"{self.base_url}/repos/{repo_name}/pulls/{pr_number}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    pr = await response.json()
                    return {
                        "pull_request": {
                            "number": pr["number"],
                            "title": pr["title"],
                            "body": pr["body"],
                            "state": pr["state"],
                            "url": pr["html_url"],
                            "head": pr["head"]["ref"],
                            "base": pr["base"]["ref"],
                            "created_at": pr["created_at"],
                            "updated_at": pr["updated_at"],
                            "user": pr["user"]["login"],
                            "mergeable": pr.get("mergeable"),
                            "draft": pr.get("draft", False),
                            "additions": pr.get("additions", 0),
                            "deletions": pr.get("deletions", 0),
                            "changed_files": pr.get("changed_files", 0),
                            "commits": pr.get("commits", 0)
                        },
                        "status": "success"
                    }
                else:
                    error_data = await response.json()
                    return {"error": error_data.get("message", "PR not found"), "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error getting pull request: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def create_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue."""
        try:
            repo_name = payload.get("repository")
            title = payload.get("title")
            body = payload.get("body", "")
            labels = payload.get("labels", [])
            assignees = payload.get("assignees", [])
            
            if not all([repo_name, title]):
                return {"error": "repository and title are required", "status": "failed"}
            
            url = f"{self.base_url}/repos/{repo_name}/issues"
            data = {
                "title": title,
                "body": body,
                "labels": labels,
                "assignees": assignees
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 201:
                    issue = await response.json()
                    return {
                        "issue": {
                            "number": issue["number"],
                            "title": issue["title"],
                            "body": issue["body"],
                            "state": issue["state"],
                            "url": issue["html_url"],
                            "created_at": issue["created_at"],
                            "user": issue["user"]["login"],
                            "labels": [label["name"] for label in issue.get("labels", [])],
                            "assignees": [assignee["login"] for assignee in issue.get("assignees", [])]
                        },
                        "status": "success"
                    }
                else:
                    error_data = await response.json()
                    return {"error": error_data.get("message", "Failed to create issue"), "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error creating issue: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def list_issues(self, repo_name: str, state: str = "open") -> Dict[str, Any]:
        """List issues for a repository."""
        try:
            url = f"{self.base_url}/repos/{repo_name}/issues"
            params = {"state": state}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    issues = await response.json()
                    return {
                        "issues": [
                            {
                                "number": issue["number"],
                                "title": issue["title"],
                                "state": issue["state"],
                                "url": issue["html_url"],
                                "created_at": issue["created_at"],
                                "updated_at": issue["updated_at"],
                                "user": issue["user"]["login"],
                                "labels": [label["name"] for label in issue.get("labels", [])],
                                "assignees": [assignee["login"] for assignee in issue.get("assignees", [])],
                                "comments": issue.get("comments", 0)
                            }
                            for issue in issues
                            if not issue.get("pull_request")  # Filter out PRs
                        ],
                        "status": "success"
                    }
                else:
                    error_data = await response.json()
                    return {"error": error_data.get("message", "Failed to fetch issues"), "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error listing issues: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def get_commits(self, repo_name: str, branch: str = "main") -> Dict[str, Any]:
        """Get recent commits for a repository branch."""
        try:
            url = f"{self.base_url}/repos/{repo_name}/commits"
            params = {"sha": branch, "per_page": 20}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    commits = await response.json()
                    return {
                        "commits": [
                            {
                                "sha": commit["sha"],
                                "message": commit["commit"]["message"],
                                "author": commit["commit"]["author"]["name"],
                                "date": commit["commit"]["author"]["date"],
                                "url": commit["html_url"]
                            }
                            for commit in commits
                        ],
                        "status": "success"
                    }
                else:
                    error_data = await response.json()
                    return {"error": error_data.get("message", "Failed to fetch commits"), "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error getting commits: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def _cleanup_impl(self) -> None:
        """Cleanup GitHub integration resources."""
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info("GitHub integration cleaned up")

