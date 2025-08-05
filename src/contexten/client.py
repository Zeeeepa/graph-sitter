"""
Contexten Client - Unified Interface for Platform Integrations
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .core import ContextenOrchestrator, ContextenConfig

logger = logging.getLogger(__name__)


class ContextenClient:
    """
    Unified client interface for Contexten orchestrator
    
    Provides a simplified API for interacting with the comprehensive
    Graph-Sitter enhancement system including all platform integrations.
    """
    
    def __init__(self, config: Optional[ContextenConfig] = None):
        """
        Initialize Contexten client
        
        Args:
            config: Optional configuration. If not provided, will use environment variables.
        """
        self.config = config or ContextenConfig()
        self.orchestrator = ContextenOrchestrator(self.config)
        self._started = False
        
        logger.info("Contexten client initialized")
    
    async def start(self):
        """Start the client and orchestrator"""
        if not self._started:
            await self.orchestrator.start()
            self._started = True
            logger.info("Contexten client started")
    
    async def stop(self):
        """Stop the client and orchestrator"""
        if self._started:
            await self.orchestrator.stop()
            self._started = False
            logger.info("Contexten client stopped")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    # Linear Operations
    async def create_linear_issue(
        self, 
        title: str, 
        description: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Linear issue"""
        return await self.orchestrator.execute_task(
            "linear.create_issue",
            {
                "title": title,
                "description": description,
                "team_id": team_id
            }
        )
    
    async def comment_on_linear_issue(self, issue_id: str, body: str) -> Dict[str, Any]:
        """Add a comment to a Linear issue"""
        return await self.orchestrator.execute_task(
            "linear.comment_on_issue",
            {
                "issue_id": issue_id,
                "body": body
            }
        )
    
    async def analyze_repository_for_linear(
        self, 
        repository_url: str, 
        create_issues: bool = False
    ) -> Dict[str, Any]:
        """Analyze a repository and optionally create Linear issues"""
        return await self.orchestrator.execute_task(
            "linear.analyze_repository",
            {
                "repository_url": repository_url,
                "analysis_type": "comprehensive",
                "create_issues": create_issues
            }
        )
    
    # GitHub Operations
    async def create_github_pr(
        self,
        repository: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = ""
    ) -> Dict[str, Any]:
        """Create a GitHub pull request"""
        return await self.orchestrator.execute_task(
            "github.create_pr",
            {
                "repository": repository,
                "title": title,
                "head": head,
                "base": base,
                "body": body
            }
        )
    
    async def review_github_pr(
        self,
        repository: str,
        pr_number: int,
        review_type: str = "COMMENT"
    ) -> Dict[str, Any]:
        """Review a GitHub pull request"""
        return await self.orchestrator.execute_task(
            "github.review_pr",
            {
                "repository": repository,
                "pr_number": pr_number,
                "review_type": review_type
            }
        )
    
    async def analyze_github_repository(
        self,
        repository: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze a GitHub repository"""
        return await self.orchestrator.execute_task(
            "github.analyze_repository",
            {
                "repository": repository,
                "analysis_type": analysis_type
            }
        )
    
    # Slack Operations
    async def send_slack_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a Slack message"""
        return await self.orchestrator.execute_task(
            "slack.send_message",
            {
                "channel": channel,
                "text": text,
                "thread_ts": thread_ts
            }
        )
    
    async def notify_team(
        self,
        channel: str,
        title: str,
        message: str,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send a team notification via Slack"""
        return await self.orchestrator.execute_task(
            "slack.notify_team",
            {
                "channel": channel,
                "title": title,
                "message": message,
                "priority": priority
            }
        )
    
    async def send_daily_report(self, channel: str) -> Dict[str, Any]:
        """Send a daily system report via Slack"""
        return await self.orchestrator.execute_task(
            "slack.send_daily_report",
            {
                "channel": channel
            }
        )
    
    # Codegen Operations
    async def generate_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate code using Codegen SDK"""
        return await self.orchestrator.execute_task(
            "codegen.generate_code",
            {
                "prompt": prompt,
                "context": context
            }
        )
    
    async def create_pr_from_linear_issue(
        self,
        issue_id: str,
        repository_url: str
    ) -> Dict[str, Any]:
        """Create a PR to resolve a Linear issue"""
        return await self.orchestrator.execute_task(
            "linear.create_pr_from_issue",
            {
                "issue_id": issue_id,
                "repository_url": repository_url
            }
        )
    
    # Workflow Operations
    async def execute_comprehensive_workflow(
        self,
        repository_url: str,
        linear_team_id: Optional[str] = None,
        slack_channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a comprehensive end-to-end workflow:
        1. Analyze repository
        2. Create Linear issues for findings
        3. Generate code improvements
        4. Create PRs
        5. Notify team via Slack
        """
        workflow_results = []
        
        try:
            # Step 1: Analyze repository
            analysis_result = await self.analyze_github_repository(repository_url)
            workflow_results.append(("repository_analysis", analysis_result))
            
            # Step 2: Create Linear issues if analysis found issues
            if analysis_result.get("status") == "completed":
                linear_result = await self.analyze_repository_for_linear(
                    repository_url, 
                    create_issues=True
                )
                workflow_results.append(("linear_issues", linear_result))
            
            # Step 3: Notify team if Slack is configured
            if slack_channel:
                notification_result = await self.notify_team(
                    channel=slack_channel,
                    title="Repository Analysis Completed",
                    message=f"Comprehensive analysis completed for {repository_url}",
                    priority="normal"
                )
                workflow_results.append(("slack_notification", notification_result))
            
            return {
                "status": "completed",
                "workflow_results": workflow_results,
                "repository_url": repository_url,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "workflow_results": workflow_results,
                "repository_url": repository_url,
                "timestamp": datetime.now().isoformat()
            }
    
    # System Operations
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return self.orchestrator.get_system_status()
    
    async def queue_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 3
    ) -> str:
        """Queue a task for asynchronous execution"""
        return await self.orchestrator.queue_task(task_type, task_data, priority)
    
    def get_extension(self, name: str) -> Optional[Any]:
        """Get an extension by name"""
        return self.orchestrator.get_extension(name)
    
    @property
    def is_started(self) -> bool:
        """Check if the client is started"""
        return self._started

