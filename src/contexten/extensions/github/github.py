"""GitHub Extension for Contexten.

This extension provides comprehensive GitHub integration including:
- Repository management
- Pull request handling
- Issue tracking
- Webhook processing
- Code analysis integration
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.Issue import Issue

from ...core.extension import EventHandlerExtension, ExtensionMetadata
from ...core.events.bus import Event

logger = logging.getLogger(__name__)

class GitHubExtension(EventHandlerExtension):
    """GitHub integration extension."""

    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app, config)
        self.github_client: Optional[Github] = None
        self._repositories: Dict[str, Repository] = {}
        self._webhook_secret = config.get('webhook_secret') if config else None

    @property
    def metadata(self) -> ExtensionMetadata:
        return ExtensionMetadata(
            name="github",
            version="1.0.0",
            description="GitHub integration for repository and PR management",
            author="Contexten",
            dependencies=[],
            required=False,
            config_schema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "GitHub API token"},
                    "webhook_secret": {"type": "string", "description": "Webhook secret"},
                    "base_url": {"type": "string", "description": "GitHub API base URL"},
                },
                "required": ["token"]
            },
            tags={"integration", "git", "repository"}
        )

    async def initialize(self) -> None:
        """Initialize GitHub client and services."""
        token = self.config.get('token')
        if not token:
            raise ValueError("GitHub token is required")

        base_url = self.config.get('base_url', 'https://api.github.com')
        self.github_client = Github(token, base_url=base_url)

        # Register event handlers
        self.register_event_handler("github.webhook", self._handle_webhook)
        self.register_event_handler("project.pin", self._handle_project_pin)
        self.register_event_handler("pr.create", self._handle_pr_create)

        logger.info("GitHub extension initialized")

    async def start(self) -> None:
        """Start GitHub extension services."""
        # Verify GitHub connection
        try:
            user = self.github_client.get_user()
            logger.info(f"Connected to GitHub as: {user.login}")
        except Exception as e:
            logger.error(f"Failed to connect to GitHub: {e}")
            raise

        # Start background tasks
        asyncio.create_task(self._sync_repositories())

    async def stop(self) -> None:
        """Stop GitHub extension services."""
        logger.info("GitHub extension stopped")

    async def get_repositories(self, org: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get repositories for user or organization.
        
        Args:
            org: Optional organization name
            
        Returns:
            List of repository information
        """
        try:
            if org:
                repos = self.github_client.get_organization(org).get_repos()
            else:
                repos = self.github_client.get_user().get_repos()

            result = []
            for repo in repos:
                repo_data = {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "ssh_url": repo.ssh_url,
                    "default_branch": repo.default_branch,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "open_issues": repo.open_issues_count,
                    "created_at": repo.created_at.isoformat(),
                    "updated_at": repo.updated_at.isoformat(),
                    "private": repo.private,
                    "archived": repo.archived,
                }
                result.append(repo_data)
                
                # Cache repository
                self._repositories[repo.full_name] = repo

            return result

        except Exception as e:
            logger.error(f"Failed to get repositories: {e}")
            raise

    async def get_repository(self, full_name: str) -> Dict[str, Any]:
        """Get repository details.
        
        Args:
            full_name: Repository full name (owner/repo)
            
        Returns:
            Repository information
        """
        try:
            if full_name in self._repositories:
                repo = self._repositories[full_name]
            else:
                repo = self.github_client.get_repo(full_name)
                self._repositories[full_name] = repo

            return {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "default_branch": repo.default_branch,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "private": repo.private,
                "archived": repo.archived,
            }

        except Exception as e:
            logger.error(f"Failed to get repository {full_name}: {e}")
            raise

    async def get_pull_requests(
        self,
        full_name: str,
        state: str = "open"
    ) -> List[Dict[str, Any]]:
        """Get pull requests for repository.
        
        Args:
            full_name: Repository full name
            state: PR state (open, closed, all)
            
        Returns:
            List of pull request information
        """
        try:
            repo = await self._get_repo(full_name)
            prs = repo.get_pulls(state=state)

            result = []
            for pr in prs:
                pr_data = {
                    "id": pr.id,
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body,
                    "state": pr.state,
                    "url": pr.html_url,
                    "user": pr.user.login,
                    "created_at": pr.created_at.isoformat(),
                    "updated_at": pr.updated_at.isoformat(),
                    "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                    "head": {
                        "ref": pr.head.ref,
                        "sha": pr.head.sha,
                    },
                    "base": {
                        "ref": pr.base.ref,
                        "sha": pr.base.sha,
                    },
                    "mergeable": pr.mergeable,
                    "merged": pr.merged,
                    "draft": pr.draft,
                }
                result.append(pr_data)

            return result

        except Exception as e:
            logger.error(f"Failed to get pull requests for {full_name}: {e}")
            raise

    async def create_pull_request(
        self,
        full_name: str,
        title: str,
        body: str,
        head: str,
        base: str
    ) -> Dict[str, Any]:
        """Create a pull request.
        
        Args:
            full_name: Repository full name
            title: PR title
            body: PR body
            head: Head branch
            base: Base branch
            
        Returns:
            Created pull request information
        """
        try:
            repo = await self._get_repo(full_name)
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )

            # Publish event
            await self.app.event_bus.publish(Event(
                type="github.pr.created",
                source="github",
                data={
                    "repository": full_name,
                    "pr_number": pr.number,
                    "title": title,
                    "user": pr.user.login,
                }
            ))

            return {
                "id": pr.id,
                "number": pr.number,
                "title": pr.title,
                "url": pr.html_url,
                "state": pr.state,
            }

        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            raise

    async def get_issues(
        self,
        full_name: str,
        state: str = "open"
    ) -> List[Dict[str, Any]]:
        """Get issues for repository.
        
        Args:
            full_name: Repository full name
            state: Issue state (open, closed, all)
            
        Returns:
            List of issue information
        """
        try:
            repo = await self._get_repo(full_name)
            issues = repo.get_issues(state=state)

            result = []
            for issue in issues:
                if issue.pull_request:  # Skip PRs
                    continue

                issue_data = {
                    "id": issue.id,
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "url": issue.html_url,
                    "user": issue.user.login,
                    "labels": [label.name for label in issue.labels],
                    "assignees": [assignee.login for assignee in issue.assignees],
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                }
                result.append(issue_data)

            return result

        except Exception as e:
            logger.error(f"Failed to get issues for {full_name}: {e}")
            raise

    async def _get_repo(self, full_name: str) -> Repository:
        """Get repository object."""
        if full_name not in self._repositories:
            self._repositories[full_name] = self.github_client.get_repo(full_name)
        return self._repositories[full_name]

    async def _handle_webhook(self, event_data: Dict[str, Any]) -> None:
        """Handle GitHub webhook events."""
        event_type = event_data.get("event_type")
        payload = event_data.get("payload", {})

        if event_type == "push":
            await self._handle_push_event(payload)
        elif event_type == "pull_request":
            await self._handle_pr_event(payload)
        elif event_type == "issues":
            await self._handle_issue_event(payload)

    async def _handle_push_event(self, payload: Dict[str, Any]) -> None:
        """Handle push events."""
        repo_name = payload.get("repository", {}).get("full_name")
        ref = payload.get("ref")
        commits = payload.get("commits", [])

        await self.app.event_bus.publish(Event(
            type="github.push",
            source="github",
            data={
                "repository": repo_name,
                "ref": ref,
                "commits": len(commits),
                "head_commit": payload.get("head_commit"),
            }
        ))

    async def _handle_pr_event(self, payload: Dict[str, Any]) -> None:
        """Handle pull request events."""
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        repo_name = payload.get("repository", {}).get("full_name")

        await self.app.event_bus.publish(Event(
            type=f"github.pr.{action}",
            source="github",
            data={
                "repository": repo_name,
                "pr_number": pr.get("number"),
                "title": pr.get("title"),
                "state": pr.get("state"),
                "user": pr.get("user", {}).get("login"),
            }
        ))

    async def _handle_issue_event(self, payload: Dict[str, Any]) -> None:
        """Handle issue events."""
        action = payload.get("action")
        issue = payload.get("issue", {})
        repo_name = payload.get("repository", {}).get("full_name")

        await self.app.event_bus.publish(Event(
            type=f"github.issue.{action}",
            source="github",
            data={
                "repository": repo_name,
                "issue_number": issue.get("number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "user": issue.get("user", {}).get("login"),
            }
        ))

    async def _handle_project_pin(self, event_data: Dict[str, Any]) -> None:
        """Handle project pinning."""
        repo_name = event_data.get("repository")
        if repo_name:
            # Ensure repository is cached
            await self.get_repository(repo_name)

    async def _handle_pr_create(self, event_data: Dict[str, Any]) -> None:
        """Handle PR creation requests."""
        await self.create_pull_request(
            full_name=event_data["repository"],
            title=event_data["title"],
            body=event_data["body"],
            head=event_data["head"],
            base=event_data["base"]
        )

    async def _sync_repositories(self) -> None:
        """Background task to sync repositories."""
        while True:
            try:
                await asyncio.sleep(300)  # Sync every 5 minutes
                await self.get_repositories()
            except Exception as e:
                logger.error(f"Repository sync failed: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check GitHub extension health."""
        try:
            user = self.github_client.get_user()
            rate_limit = self.github_client.get_rate_limit()
            
            return {
                "status": "healthy",
                "user": user.login,
                "rate_limit": {
                    "core": {
                        "remaining": rate_limit.core.remaining,
                        "limit": rate_limit.core.limit,
                        "reset": rate_limit.core.reset.isoformat(),
                    }
                },
                "cached_repos": len(self._repositories),
                "timestamp": self.app.current_time.isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
                "timestamp": self.app.current_time.isoformat(),
            }

