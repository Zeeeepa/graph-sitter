"""
GitHub Integration Client

Integration client for GitHub API and webhook handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePlatformIntegration


class GitHubIntegration(BasePlatformIntegration):
    """
    GitHub platform integration for handling GitHub API operations
    and webhook events.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("github")
        self.config = config or {}
        self.api_token = self.config.get("api_token")
        self.webhook_secret = self.config.get("webhook_secret")
        self.base_url = self.config.get("base_url", "https://api.github.com")
        
        # State
        self.authenticated = False
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = None
        
        # Event handlers
        self.event_handlers: Dict[str, List[callable]] = {}
    
    async def start(self):
        """Start the GitHub integration"""
        if self.running:
            return
        
        self.logger.info("Starting GitHub integration")
        self.running = True
        
        # Authenticate if token provided
        if self.api_token:
            self.authenticated = await self.authenticate({"token": self.api_token})
        
        # Start health monitoring
        asyncio.create_task(self._periodic_health_check())
        
        self.logger.info("GitHub integration started")
    
    async def stop(self):
        """Stop the GitHub integration"""
        self.logger.info("Stopping GitHub integration")
        self.running = False
        self.logger.info("GitHub integration stopped")
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with GitHub API"""
        token = credentials.get("token")
        if not token:
            return False
        
        try:
            # Test authentication by getting user info
            user_info = await self._api_request("GET", "/user")
            if user_info:
                self.authenticated = True
                self.logger.info(f"Authenticated as GitHub user: {user_info.get('login')}")
                return True
        except Exception as e:
            self.logger.error(f"GitHub authentication failed: {e}")
        
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform GitHub API health check"""
        try:
            # Check API status
            response = await self._api_request("GET", "/rate_limit")
            
            if response:
                self.rate_limit_remaining = response.get("rate", {}).get("remaining", 0)
                self.rate_limit_reset = response.get("rate", {}).get("reset")
                
                healthy = self.rate_limit_remaining > 100  # Consider unhealthy if very low
                
                details = {
                    "rate_limit_remaining": self.rate_limit_remaining,
                    "rate_limit_reset": self.rate_limit_reset,
                    "authenticated": self.authenticated
                }
                
                self._update_health_status(healthy, details)
                return self.health_status
        
        except Exception as e:
            self.logger.error(f"GitHub health check failed: {e}")
            self._update_health_status(False, {"error": str(e)})
        
        return self.health_status
    
    async def get_status(self) -> Dict[str, Any]:
        """Get GitHub integration status"""
        return {
            "platform": self.platform_name,
            "running": self.running,
            "authenticated": self.authenticated,
            "rate_limit_remaining": self.rate_limit_remaining,
            "health": self.health_status,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None
        }
    
    # GitHub-specific methods
    
    async def get_pr(self, owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """Get pull request details"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        return await self._api_request("GET", endpoint)
    
    async def create_pr(self, owner: str, repo: str, title: str, body: str, 
                       head: str, base: str = "main") -> Optional[Dict[str, Any]]:
        """Create a pull request"""
        endpoint = f"/repos/{owner}/{repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        return await self._api_request("POST", endpoint, data)
    
    async def create_review(self, owner: str, repo: str, pr_number: int,
                           body: str, event: str = "COMMENT") -> Optional[Dict[str, Any]]:
        """Create a PR review"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        data = {
            "body": body,
            "event": event
        }
        return await self._api_request("POST", endpoint, data)
    
    async def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """Get issue details"""
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}"
        return await self._api_request("GET", endpoint)
    
    async def create_issue(self, owner: str, repo: str, title: str, 
                          body: str = "", labels: List[str] = None) -> Optional[Dict[str, Any]]:
        """Create an issue"""
        endpoint = f"/repos/{owner}/{repo}/issues"
        data = {
            "title": title,
            "body": body
        }
        if labels:
            data["labels"] = labels
        
        return await self._api_request("POST", endpoint, data)
    
    async def add_comment(self, owner: str, repo: str, issue_number: int, 
                         body: str) -> Optional[Dict[str, Any]]:
        """Add a comment to an issue or PR"""
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = {"body": body}
        return await self._api_request("POST", endpoint, data)
    
    async def get_repository(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository details"""
        endpoint = f"/repos/{owner}/{repo}"
        return await self._api_request("GET", endpoint)
    
    async def list_repositories(self, org: str = None) -> List[Dict[str, Any]]:
        """List repositories"""
        if org:
            endpoint = f"/orgs/{org}/repos"
        else:
            endpoint = "/user/repos"
        
        response = await self._api_request("GET", endpoint)
        return response if isinstance(response, list) else []
    
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Handle GitHub webhook events"""
        try:
            self.logger.info(f"Handling GitHub webhook: {event_type}")
            
            # Process common webhook events
            if event_type == "pull_request":
                await self._handle_pr_event(payload)
            elif event_type == "issues":
                await self._handle_issue_event(payload)
            elif event_type == "push":
                await self._handle_push_event(payload)
            elif event_type == "release":
                await self._handle_release_event(payload)
            
            # Call registered event handlers
            handlers = self.event_handlers.get(event_type, [])
            for handler in handlers:
                try:
                    await handler(payload)
                except Exception as e:
                    self.logger.error(f"Event handler error: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Webhook handling failed: {e}")
            return False
    
    def register_event_handler(self, event_type: str, handler: callable):
        """Register an event handler for specific GitHub events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _handle_pr_event(self, payload: Dict[str, Any]):
        """Handle pull request events"""
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        
        self.logger.info(f"PR {action}: #{pr.get('number')} - {pr.get('title')}")
    
    async def _handle_issue_event(self, payload: Dict[str, Any]):
        """Handle issue events"""
        action = payload.get("action")
        issue = payload.get("issue", {})
        
        self.logger.info(f"Issue {action}: #{issue.get('number')} - {issue.get('title')}")
    
    async def _handle_push_event(self, payload: Dict[str, Any]):
        """Handle push events"""
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])
        
        self.logger.info(f"Push to {ref}: {len(commits)} commits")
    
    async def _handle_release_event(self, payload: Dict[str, Any]):
        """Handle release events"""
        action = payload.get("action")
        release = payload.get("release", {})
        
        self.logger.info(f"Release {action}: {release.get('tag_name')}")
    
    async def _api_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make a request to the GitHub API"""
        if not self.api_token:
            self.logger.error("No GitHub API token configured")
            return None
        
        import aiohttp
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GraphSitter-Orchestrator/1.0"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, json=data) as response:
                    # Update rate limit info
                    self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                    self.rate_limit_reset = int(response.headers.get("X-RateLimit-Reset", 0))
                    
                    if response.status == 200 or response.status == 201:
                        return await response.json()
                    elif response.status == 204:
                        return {}  # No content
                    else:
                        error_text = await response.text()
                        self.logger.error(f"GitHub API error {response.status}: {error_text}")
                        return None
        
        except Exception as e:
            self.logger.error(f"GitHub API request failed: {e}")
            return None

