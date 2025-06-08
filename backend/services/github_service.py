"""
GitHub API integration service for repository management and PR operations
"""
import asyncio
import aiohttp
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class GitHubService:
    """GitHub API service for repository and PR management"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-CICD-Platform/1.0"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to GitHub API"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200 or response.status == 201:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"GitHub API error {response.status}: {error_text}")
                        raise Exception(f"GitHub API error {response.status}: {error_text}")
            except Exception as e:
                logger.error(f"GitHub API request failed: {e}")
                raise
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information"""
        return await self._make_request("GET", "/user")
    
    async def get_user_repositories(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get user's repositories"""
        repos = []
        page = 1
        
        while True:
            endpoint = f"/user/repos?per_page={per_page}&page={page}&sort=updated"
            page_repos = await self._make_request("GET", endpoint)
            
            if not page_repos:
                break
                
            repos.extend(page_repos)
            
            if len(page_repos) < per_page:
                break
                
            page += 1
        
        # Filter and format repositories
        formatted_repos = []
        for repo in repos:
            formatted_repos.append({
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo.get("description", ""),
                "private": repo["private"],
                "html_url": repo["html_url"],
                "clone_url": repo["clone_url"],
                "default_branch": repo["default_branch"],
                "language": repo.get("language"),
                "updated_at": repo["updated_at"],
                "owner": {
                    "login": repo["owner"]["login"],
                    "avatar_url": repo["owner"]["avatar_url"]
                }
            })
        
        return formatted_repos
    
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get specific repository information"""
        endpoint = f"/repos/{owner}/{repo}"
        return await self._make_request("GET", endpoint)
    
    async def get_repository_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository branches"""
        endpoint = f"/repos/{owner}/{repo}/branches"
        return await self._make_request("GET", endpoint)
    
    async def create_branch(self, owner: str, repo: str, branch_name: str, base_sha: str) -> Dict[str, Any]:
        """Create a new branch"""
        endpoint = f"/repos/{owner}/{repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        return await self._make_request("POST", endpoint, data)
    
    async def get_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """Get repository pull requests"""
        endpoint = f"/repos/{owner}/{repo}/pulls?state={state}"
        return await self._make_request("GET", endpoint)
    
    async def create_pull_request(
        self, 
        owner: str, 
        repo: str, 
        title: str, 
        body: str, 
        head: str, 
        base: str
    ) -> Dict[str, Any]:
        """Create a new pull request"""
        endpoint = f"/repos/{owner}/{repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        return await self._make_request("POST", endpoint, data)
    
    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Get specific pull request"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        return await self._make_request("GET", endpoint)
    
    async def update_pull_request(
        self, 
        owner: str, 
        repo: str, 
        pr_number: int, 
        title: str = None, 
        body: str = None, 
        state: str = None
    ) -> Dict[str, Any]:
        """Update pull request"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        data = {}
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if state:
            data["state"] = state
        
        return await self._make_request("PATCH", endpoint, data)
    
    async def get_pr_status_checks(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Get PR status checks"""
        # First get the PR to get the head SHA
        pr = await self.get_pull_request(owner, repo, pr_number)
        head_sha = pr["head"]["sha"]
        
        endpoint = f"/repos/{owner}/{repo}/commits/{head_sha}/status"
        return await self._make_request("GET", endpoint)
    
    async def get_pr_check_runs(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Get PR check runs"""
        pr = await self.get_pull_request(owner, repo, pr_number)
        head_sha = pr["head"]["sha"]
        
        endpoint = f"/repos/{owner}/{repo}/commits/{head_sha}/check-runs"
        return await self._make_request("GET", endpoint)
    
    async def create_pr_comment(
        self, 
        owner: str, 
        repo: str, 
        pr_number: int, 
        body: str
    ) -> Dict[str, Any]:
        """Create a comment on a pull request"""
        endpoint = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
        data = {"body": body}
        return await self._make_request("POST", endpoint, data)
    
    async def get_file_content(self, owner: str, repo: str, path: str, ref: str = None) -> Dict[str, Any]:
        """Get file content from repository"""
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        if ref:
            endpoint += f"?ref={ref}"
        
        response = await self._make_request("GET", endpoint)
        
        # Decode base64 content
        if response.get("content"):
            content = base64.b64decode(response["content"]).decode("utf-8")
            response["decoded_content"] = content
        
        return response
    
    async def create_or_update_file(
        self, 
        owner: str, 
        repo: str, 
        path: str, 
        content: str, 
        message: str, 
        branch: str = None,
        sha: str = None
    ) -> Dict[str, Any]:
        """Create or update a file in repository"""
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        
        # Encode content to base64
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        data = {
            "message": message,
            "content": encoded_content
        }
        
        if branch:
            data["branch"] = branch
        if sha:
            data["sha"] = sha
        
        return await self._make_request("PUT", endpoint, data)
    
    async def get_repository_commits(
        self, 
        owner: str, 
        repo: str, 
        sha: str = None, 
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """Get repository commits"""
        endpoint = f"/repos/{owner}/{repo}/commits?per_page={per_page}"
        if sha:
            endpoint += f"&sha={sha}"
        
        return await self._make_request("GET", endpoint)
    
    async def create_webhook(
        self, 
        owner: str, 
        repo: str, 
        webhook_url: str, 
        events: List[str] = None
    ) -> Dict[str, Any]:
        """Create a webhook for repository events"""
        if events is None:
            events = ["push", "pull_request", "issues"]
        
        endpoint = f"/repos/{owner}/{repo}/hooks"
        data = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": webhook_url,
                "content_type": "json"
            }
        }
        
        return await self._make_request("POST", endpoint, data)
    
    async def validate_token(self) -> bool:
        """Validate GitHub token"""
        try:
            await self.get_user_info()
            return True
        except Exception:
            return False
    
    async def get_repository_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get repository programming languages"""
        endpoint = f"/repos/{owner}/{repo}/languages"
        return await self._make_request("GET", endpoint)
    
    async def search_repositories(self, query: str, per_page: int = 30) -> Dict[str, Any]:
        """Search repositories"""
        endpoint = f"/search/repositories?q={query}&per_page={per_page}"
        return await self._make_request("GET", endpoint)


class GitHubWebhookHandler:
    """Handle GitHub webhook events"""
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
    
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook event"""
        logger.info(f"Received GitHub webhook: {event_type}")
        
        if event_type == "pull_request":
            return await self._handle_pull_request_event(payload)
        elif event_type == "push":
            return await self._handle_push_event(payload)
        elif event_type == "issues":
            return await self._handle_issues_event(payload)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return {"status": "ignored", "event_type": event_type}
    
    async def _handle_pull_request_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request webhook events"""
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        repository = payload.get("repository", {})
        
        pr_data = {
            "action": action,
            "pr_number": pr.get("number"),
            "pr_title": pr.get("title"),
            "pr_state": pr.get("state"),
            "repository": repository.get("full_name"),
            "author": pr.get("user", {}).get("login"),
            "head_sha": pr.get("head", {}).get("sha"),
            "base_branch": pr.get("base", {}).get("ref"),
            "head_branch": pr.get("head", {}).get("ref")
        }
        
        # Broadcast PR update if websocket manager is available
        if self.websocket_manager:
            await self.websocket_manager.broadcast({
                "type": "github_pr_event",
                "data": pr_data,
                "timestamp": datetime.now().isoformat()
            })
        
        return {"status": "processed", "event_type": "pull_request", "data": pr_data}
    
    async def _handle_push_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push webhook events"""
        repository = payload.get("repository", {})
        commits = payload.get("commits", [])
        
        push_data = {
            "repository": repository.get("full_name"),
            "branch": payload.get("ref", "").replace("refs/heads/", ""),
            "commits_count": len(commits),
            "pusher": payload.get("pusher", {}).get("name"),
            "head_commit": payload.get("head_commit", {})
        }
        
        # Broadcast push update if websocket manager is available
        if self.websocket_manager:
            await self.websocket_manager.broadcast({
                "type": "github_push_event",
                "data": push_data,
                "timestamp": datetime.now().isoformat()
            })
        
        return {"status": "processed", "event_type": "push", "data": push_data}
    
    async def _handle_issues_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issues webhook events"""
        action = payload.get("action")
        issue = payload.get("issue", {})
        repository = payload.get("repository", {})
        
        issue_data = {
            "action": action,
            "issue_number": issue.get("number"),
            "issue_title": issue.get("title"),
            "issue_state": issue.get("state"),
            "repository": repository.get("full_name"),
            "author": issue.get("user", {}).get("login")
        }
        
        # Broadcast issue update if websocket manager is available
        if self.websocket_manager:
            await self.websocket_manager.broadcast({
                "type": "github_issue_event",
                "data": issue_data,
                "timestamp": datetime.now().isoformat()
            })
        
        return {"status": "processed", "event_type": "issues", "data": issue_data}

