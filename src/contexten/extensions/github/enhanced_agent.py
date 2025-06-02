"""
Enhanced GitHub Integration Agent

This module provides a comprehensive GitHub integration agent with advanced
features for repository management, webhook processing, and automation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import logging

from ...shared.logging.get_logger import get_logger
from .enhanced_client import EnhancedGitHubClient
from .events.manager import GitHubEventManager
from .types import GitHubRepository, GitHubPullRequest, GitHubIssue, GitHubUser
from .webhook.processor import GitHubWebhookProcessor
from .workflow.automation import GitHubWorkflowAutomation

logger = get_logger(__name__)

@dataclass
class GitHubAgentConfig:
    """Configuration for GitHub Integration Agent"""
    token: str
    webhook_secret: Optional[str] = None
    auto_assignment: bool = True
    workflow_automation: bool = True
    event_processing: bool = True
    sync_interval: int = 300  # 5 minutes
    max_retries: int = 3
    timeout: int = 30

class EnhancedGitHubAgent:
    """
    Enhanced GitHub Integration Agent with comprehensive capabilities:
    - REST API integration
    - Webhook processing
    - Workflow automation
    - Event management
    - Real-time synchronization
    """
    
    def __init__(self, config: GitHubAgentConfig):
        self.config = config
        self.client = EnhancedGitHubClient(config.token)
        self.webhook_processor = GitHubWebhookProcessor(config.webhook_secret)
        self.workflow_automation = GitHubWorkflowAutomation(self.client)
        self.event_manager = GitHubEventManager()
        
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
        
        logger.info("Enhanced GitHub Agent initialized")
    
    async def start(self) -> None:
        """Start the GitHub agent and all its components"""
        try:
            self._running = True
            
            # Initialize client connection
            await self.client.initialize()
            
            # Start event manager
            await self.event_manager.start()
            
            # Start workflow automation if enabled
            if self.config.workflow_automation:
                await self.workflow_automation.start()
            
            # Start periodic sync if enabled
            if self.config.sync_interval > 0:
                self._sync_task = asyncio.create_task(self._periodic_sync())
            
            logger.info("Enhanced GitHub Agent started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start GitHub agent: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the GitHub agent and cleanup resources"""
        self._running = False
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        await self.workflow_automation.stop()
        await self.event_manager.stop()
        await self.client.close()
        
        logger.info("Enhanced GitHub Agent stopped")
    
    async def _periodic_sync(self) -> None:
        """Periodic synchronization with GitHub"""
        while self._running:
            try:
                await self.sync_data()
                await asyncio.sleep(self.config.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def sync_data(self) -> None:
        """Synchronize data with GitHub"""
        try:
            # Sync repositories and pull requests
            repos = await self.client.get_repositories()
            
            # Process any pending events
            await self.event_manager.process_pending_events()
            
            logger.debug(f"Synced {len(repos)} repositories")
            
        except Exception as e:
            logger.error(f"Error syncing data: {e}")
            raise
    
    # Repository Management
    async def get_repositories(
        self,
        org: Optional[str] = None,
        type: str = "all",
        sort: str = "updated",
        per_page: int = 100
    ) -> List[GitHubRepository]:
        """Get GitHub repositories"""
        try:
            return await self.client.get_repositories(
                org=org,
                type=type,
                sort=sort,
                per_page=per_page
            )
        except Exception as e:
            logger.error(f"Error getting repositories: {e}")
            return []
    
    async def get_repository(self, owner: str, repo: str) -> Optional[GitHubRepository]:
        """Get a specific GitHub repository"""
        try:
            return await self.client.get_repository(owner, repo)
        except Exception as e:
            logger.error(f"Error getting repository {owner}/{repo}: {e}")
            return None
    
    async def create_repository(
        self,
        name: str,
        description: Optional[str] = None,
        private: bool = False,
        org: Optional[str] = None,
        **kwargs
    ) -> GitHubRepository:
        """Create a new GitHub repository"""
        try:
            repo = await self.client.create_repository(
                name=name,
                description=description,
                private=private,
                org=org,
                **kwargs
            )
            
            # Trigger workflow automation
            if self.config.workflow_automation:
                await self.workflow_automation.process_repository_created(repo)
            
            # Emit event
            await self.event_manager.emit_event("repository_created", {"repository": repo})
            
            logger.info(f"Created repository: {repo.full_name}")
            return repo
            
        except Exception as e:
            logger.error(f"Error creating repository: {e}")
            raise
    
    # Issue Management
    async def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        per_page: int = 100
    ) -> List[GitHubIssue]:
        """Get GitHub issues"""
        try:
            return await self.client.get_issues(
                owner=owner,
                repo=repo,
                state=state,
                labels=labels,
                assignee=assignee,
                per_page=per_page
            )
        except Exception as e:
            logger.error(f"Error getting issues for {owner}/{repo}: {e}")
            return []
    
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        milestone: Optional[int] = None
    ) -> GitHubIssue:
        """Create a new GitHub issue"""
        try:
            issue = await self.client.create_issue(
                owner=owner,
                repo=repo,
                title=title,
                body=body,
                assignees=assignees,
                labels=labels,
                milestone=milestone
            )
            
            # Trigger workflow automation
            if self.config.workflow_automation:
                await self.workflow_automation.process_issue_created(issue)
            
            # Emit event
            await self.event_manager.emit_event("issue_created", {"issue": issue})
            
            logger.info(f"Created issue: {issue.title} (#{issue.number})")
            return issue
            
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            raise
    
    async def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        **updates
    ) -> GitHubIssue:
        """Update an existing GitHub issue"""
        try:
            issue = await self.client.update_issue(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                **updates
            )
            
            # Trigger workflow automation
            if self.config.workflow_automation:
                await self.workflow_automation.process_issue_updated(issue)
            
            # Emit event
            await self.event_manager.emit_event("issue_updated", {"issue": issue})
            
            logger.info(f"Updated issue: {issue.title} (#{issue.number})")
            return issue
            
        except Exception as e:
            logger.error(f"Error updating issue {owner}/{repo}#{issue_number}: {e}")
            raise
    
    # Pull Request Management
    async def get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        base: Optional[str] = None,
        head: Optional[str] = None,
        per_page: int = 100
    ) -> List[GitHubPullRequest]:
        """Get GitHub pull requests"""
        try:
            return await self.client.get_pull_requests(
                owner=owner,
                repo=repo,
                state=state,
                base=base,
                head=head,
                per_page=per_page
            )
        except Exception as e:
            logger.error(f"Error getting pull requests for {owner}/{repo}: {e}")
            return []
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False
    ) -> GitHubPullRequest:
        """Create a new GitHub pull request"""
        try:
            pr = await self.client.create_pull_request(
                owner=owner,
                repo=repo,
                title=title,
                head=head,
                base=base,
                body=body,
                draft=draft
            )
            
            # Trigger workflow automation
            if self.config.workflow_automation:
                await self.workflow_automation.process_pull_request_created(pr)
            
            # Emit event
            await self.event_manager.emit_event("pull_request_created", {"pull_request": pr})
            
            logger.info(f"Created pull request: {pr.title} (#{pr.number})")
            return pr
            
        except Exception as e:
            logger.error(f"Error creating pull request: {e}")
            raise
    
    async def update_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        **updates
    ) -> GitHubPullRequest:
        """Update an existing GitHub pull request"""
        try:
            pr = await self.client.update_pull_request(
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                **updates
            )
            
            # Trigger workflow automation
            if self.config.workflow_automation:
                await self.workflow_automation.process_pull_request_updated(pr)
            
            # Emit event
            await self.event_manager.emit_event("pull_request_updated", {"pull_request": pr})
            
            logger.info(f"Updated pull request: {pr.title} (#{pr.number})")
            return pr
            
        except Exception as e:
            logger.error(f"Error updating pull request {owner}/{repo}#{pr_number}: {e}")
            raise
    
    # Comment Management
    async def create_issue_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str
    ) -> Dict[str, Any]:
        """Create a comment on an issue"""
        try:
            comment = await self.client.create_issue_comment(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                body=body
            )
            
            # Emit event
            await self.event_manager.emit_event("comment_created", {"comment": comment})
            
            logger.info(f"Created comment on issue {owner}/{repo}#{issue_number}")
            return comment
            
        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            raise
    
    async def create_pr_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str
    ) -> Dict[str, Any]:
        """Create a comment on a pull request"""
        try:
            comment = await self.client.create_pr_comment(
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                body=body
            )
            
            # Emit event
            await self.event_manager.emit_event("pr_comment_created", {"comment": comment})
            
            logger.info(f"Created comment on PR {owner}/{repo}#{pr_number}")
            return comment
            
        except Exception as e:
            logger.error(f"Error creating PR comment: {e}")
            raise
    
    # Webhook Processing
    async def process_webhook(self, payload: Dict[str, Any], signature: Optional[str] = None) -> bool:
        """Process incoming GitHub webhook"""
        try:
            # Validate webhook signature
            if not self.webhook_processor.validate_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return False
            
            # Process the webhook
            result = await self.webhook_processor.process(payload)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return False
    
    # Workflow Automation
    async def trigger_workflow(self, workflow_name: str, context: Dict[str, Any]) -> bool:
        """Trigger a workflow automation"""
        try:
            return await self.workflow_automation.trigger_workflow(workflow_name, context)
        except Exception as e:
            logger.error(f"Error triggering workflow {workflow_name}: {e}")
            return False
    
    # User Management
    async def get_current_user(self) -> Optional[GitHubUser]:
        """Get current authenticated user"""
        try:
            return await self.client.get_current_user()
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    async def get_user(self, username: str) -> Optional[GitHubUser]:
        """Get a GitHub user by username"""
        try:
            return await self.client.get_user(username)
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            return None
    
    # Organization Management
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Get user's organizations"""
        try:
            return await self.client.get_organizations()
        except Exception as e:
            logger.error(f"Error getting organizations: {e}")
            return []
    
    async def get_organization_repositories(self, org: str) -> List[GitHubRepository]:
        """Get repositories for an organization"""
        try:
            return await self.client.get_organization_repositories(org)
        except Exception as e:
            logger.error(f"Error getting organization repositories for {org}: {e}")
            return []
    
    # Branch Management
    async def get_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository branches"""
        try:
            return await self.client.get_branches(owner, repo)
        except Exception as e:
            logger.error(f"Error getting branches for {owner}/{repo}: {e}")
            return []
    
    async def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        from_branch: str = "main"
    ) -> Dict[str, Any]:
        """Create a new branch"""
        try:
            branch = await self.client.create_branch(
                owner=owner,
                repo=repo,
                branch_name=branch_name,
                from_branch=from_branch
            )
            
            # Emit event
            await self.event_manager.emit_event("branch_created", {"branch": branch})
            
            logger.info(f"Created branch: {branch_name} in {owner}/{repo}")
            return branch
            
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            raise
    
    # File Management
    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str = "main"
    ) -> Optional[Dict[str, Any]]:
        """Get file content from repository"""
        try:
            return await self.client.get_file_content(owner, repo, path, ref)
        except Exception as e:
            logger.error(f"Error getting file content {owner}/{repo}/{path}: {e}")
            return None
    
    async def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
        sha: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update a file in repository"""
        try:
            result = await self.client.create_or_update_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=message,
                branch=branch,
                sha=sha
            )
            
            # Emit event
            await self.event_manager.emit_event("file_updated", {"file": result})
            
            logger.info(f"Updated file: {path} in {owner}/{repo}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating file: {e}")
            raise
    
    # Health and Status
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Check client connection
            client_healthy = await self.client.health_check()
            
            # Check component status
            status = {
                "status": "healthy" if client_healthy else "unhealthy",
                "client": client_healthy,
                "webhook_processor": self.webhook_processor.is_healthy(),
                "workflow_automation": self.workflow_automation.is_healthy(),
                "event_manager": self.event_manager.is_healthy(),
                "running": self._running,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Integration with Codegen SDK
    async def create_codegen_task(
        self,
        prompt: str,
        repository: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a task using Codegen SDK and link it to GitHub repository"""
        try:
            # This will be implemented when integrating with the dashboard
            # For now, return a placeholder
            task_data = {
                "prompt": prompt,
                "repository": repository,
                "context": context or {},
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # If linked to a repository, create an issue
            if repository:
                owner, repo = repository.split("/")
                await self.create_issue(
                    owner=owner,
                    repo=repo,
                    title=f"🤖 Codegen Task: {prompt[:50]}...",
                    body=f"**Codegen Task Created**\n\n{prompt}\n\n---\n*This issue was automatically created by Contexten*"
                )
            
            logger.info(f"Created Codegen task for repository {repository}")
            return task_data
            
        except Exception as e:
            logger.error(f"Error creating Codegen task: {e}")
            raise

