"""
Enhanced Linear Integration

This module provides advanced Linear integration capabilities including
automated issue management, workflow automation, and team coordination.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class LinearConfig:
    """Configuration for Linear integration."""
    api_key: str
    webhook_secret: Optional[str] = None
    base_url: str = "https://api.linear.app"
    auto_assignment_enabled: bool = True
    auto_status_updates: bool = True
    notification_channels: List[str] = None


class LinearIntegration:
    """
    Enhanced Linear integration with automation capabilities.
    
    Features:
    - Automated issue assignment and tracking
    - Workflow automation and status updates
    - Team coordination and notifications
    - Project management integration
    - Advanced reporting and analytics
    """
    
    def __init__(self, orchestrator):
        """
        Initialize Linear integration.
        
        Args:
            orchestrator: Reference to the main orchestrator
        """
        self.orchestrator = orchestrator
        self.config: Optional[LinearConfig] = None
        self.webhook_handlers: Dict[str, Callable] = {}
        
        logger.info("Linear integration initialized")
    
    async def initialize(self):
        """Initialize the Linear integration."""
        # Load configuration from environment or orchestrator config
        self.config = LinearConfig(
            api_key="placeholder-key",  # Would load from environment
            auto_assignment_enabled=True,
            auto_status_updates=True
        )
        
        # Setup webhook handlers
        self._setup_webhook_handlers()
        
        logger.info("Linear integration initialized successfully")
    
    async def close(self):
        """Close the Linear integration."""
        logger.info("Linear integration closed")
    
    def _setup_webhook_handlers(self):
        """Setup webhook event handlers."""
        self.webhook_handlers = {
            "Issue": self._handle_issue_event,
            "Comment": self._handle_comment_event,
            "Project": self._handle_project_event,
            "Team": self._handle_team_event
        }
    
    async def _handle_issue_event(self, event_data: Dict[str, Any]):
        """Handle issue events."""
        action = event_data.get("action")
        issue_data = event_data.get("data", {})
        
        logger.info(f"Handling Linear issue event: {action}")
        
        if action == "create":
            await self._process_new_issue(issue_data)
        elif action == "update":
            await self._process_issue_update(issue_data)
    
    async def _handle_comment_event(self, event_data: Dict[str, Any]):
        """Handle comment events."""
        action = event_data.get("action")
        comment_data = event_data.get("data", {})
        
        logger.info(f"Handling Linear comment event: {action}")
        
        if action == "create":
            await self._process_new_comment(comment_data)
    
    async def _handle_project_event(self, event_data: Dict[str, Any]):
        """Handle project events."""
        action = event_data.get("action")
        project_data = event_data.get("data", {})
        
        logger.info(f"Handling Linear project event: {action}")
    
    async def _handle_team_event(self, event_data: Dict[str, Any]):
        """Handle team events."""
        action = event_data.get("action")
        team_data = event_data.get("data", {})
        
        logger.info(f"Handling Linear team event: {action}")
    
    async def _process_new_issue(self, issue_data: Dict[str, Any]):
        """Process a new Linear issue."""
        issue_id = issue_data.get("id")
        title = issue_data.get("title")
        description = issue_data.get("description")
        
        logger.info(f"Processing new Linear issue: {title}")
        
        # Auto-assign based on issue content
        if self.config.auto_assignment_enabled:
            await self._auto_assign_issue(issue_data)
        
        # Create corresponding tasks if needed
        await self._create_tasks_from_issue(issue_data)
    
    async def _process_issue_update(self, issue_data: Dict[str, Any]):
        """Process Linear issue updates."""
        issue_id = issue_data.get("id")
        state = issue_data.get("state", {})
        
        logger.info(f"Processing Linear issue update: {issue_id}")
        
        # Update corresponding tasks
        await self._sync_issue_status(issue_data)
    
    async def _process_new_comment(self, comment_data: Dict[str, Any]):
        """Process new comments on Linear issues."""
        comment_id = comment_data.get("id")
        body = comment_data.get("body")
        issue = comment_data.get("issue", {})
        
        logger.info(f"Processing new Linear comment on issue {issue.get('id')}")
        
        # Check for automation triggers in comments
        await self._check_comment_triggers(comment_data)
    
    async def _auto_assign_issue(self, issue_data: Dict[str, Any]):
        """Automatically assign issues based on content and team capacity."""
        title = issue_data.get("title", "")
        description = issue_data.get("description", "")
        labels = issue_data.get("labels", [])
        
        # Simple assignment logic (would be more sophisticated in practice)
        if "bug" in title.lower() or "fix" in title.lower():
            assignee = "bug-team"
        elif "feature" in title.lower() or "enhancement" in title.lower():
            assignee = "feature-team"
        else:
            assignee = "general-team"
        
        logger.info(f"Auto-assigning issue to {assignee}")
    
    async def _create_tasks_from_issue(self, issue_data: Dict[str, Any]):
        """Create Codegen tasks from Linear issues."""
        issue_id = issue_data.get("id")
        title = issue_data.get("title")
        description = issue_data.get("description")
        
        # Create analysis task for code-related issues
        if any(keyword in title.lower() for keyword in ["code", "implementation", "bug", "feature"]):
            if self.orchestrator and self.orchestrator.codegen_client:
                from ...codegen.autogenlib import TaskConfig
                
                task_config = TaskConfig(
                    prompt=f"Analyze and provide implementation guidance for Linear issue: {title}",
                    context={
                        "linear_issue_id": issue_id,
                        "title": title,
                        "description": description,
                        "source": "linear_issue"
                    },
                    priority=5,
                    metadata={"linear_issue_id": issue_id, "source": "linear_automation"}
                )
                
                await self.orchestrator.codegen_client.run_task(task_config)
    
    async def _sync_issue_status(self, issue_data: Dict[str, Any]):
        """Sync Linear issue status with corresponding tasks."""
        issue_id = issue_data.get("id")
        state = issue_data.get("state", {})
        state_name = state.get("name", "")
        
        logger.info(f"Syncing status for Linear issue {issue_id}: {state_name}")
        
        # Update corresponding tasks in task manager
        if self.orchestrator and self.orchestrator.task_manager:
            # Find tasks related to this issue
            for task_id, task in self.orchestrator.task_manager.tasks.items():
                if task.metadata.get("linear_issue_id") == issue_id:
                    # Update task status based on Linear issue status
                    if state_name.lower() in ["done", "completed"]:
                        # Mark task as completed if not already
                        pass
                    elif state_name.lower() in ["cancelled", "rejected"]:
                        # Cancel the task
                        self.orchestrator.task_manager.cancel_task(task_id)
    
    async def _check_comment_triggers(self, comment_data: Dict[str, Any]):
        """Check for automation triggers in comments."""
        body = comment_data.get("body", "")
        issue = comment_data.get("issue", {})
        
        # Check for specific trigger phrases
        if "@codegen" in body.lower():
            await self._handle_codegen_mention(comment_data)
        elif "analyze" in body.lower():
            await self._trigger_analysis_from_comment(comment_data)
    
    async def _handle_codegen_mention(self, comment_data: Dict[str, Any]):
        """Handle @codegen mentions in comments."""
        body = comment_data.get("body", "")
        issue = comment_data.get("issue", {})
        
        logger.info("Handling @codegen mention in Linear comment")
        
        # Extract the request from the comment
        # This would parse the comment to understand what's being requested
        if self.orchestrator and self.orchestrator.codegen_client:
            from ...codegen.autogenlib import TaskConfig
            
            task_config = TaskConfig(
                prompt=f"Respond to Linear comment request: {body}",
                context={
                    "linear_issue_id": issue.get("id"),
                    "comment_body": body,
                    "source": "linear_mention"
                },
                priority=7,
                metadata={"linear_issue_id": issue.get("id"), "source": "linear_mention"}
            )
            
            await self.orchestrator.codegen_client.run_task(task_config)
    
    async def _trigger_analysis_from_comment(self, comment_data: Dict[str, Any]):
        """Trigger analysis based on comment content."""
        body = comment_data.get("body", "")
        issue = comment_data.get("issue", {})
        
        logger.info("Triggering analysis from Linear comment")
        
        # Extract repository URL or other analysis targets from comment
        # This would parse the comment to find what needs to be analyzed
    
    async def process_webhook(self, event_type: str, event_data: Dict[str, Any]):
        """Process incoming Linear webhook events."""
        handler = self.webhook_handlers.get(event_type)
        if handler:
            try:
                await handler(event_data)
            except Exception as e:
                logger.error(f"Error processing {event_type} webhook: {e}")
        else:
            logger.warning(f"No handler for Linear webhook event type: {event_type}")
    
    async def create_issue(self, title: str, description: str, team_id: str) -> Dict[str, Any]:
        """Create a new Linear issue."""
        logger.info(f"Creating Linear issue: {title}")
        
        # This would integrate with actual Linear API
        return {
            "id": f"issue_{hash(title) % 10000}",
            "title": title,
            "description": description,
            "team_id": team_id,
            "created_at": datetime.now().isoformat()
        }
    
    async def update_issue_status(self, issue_id: str, status: str) -> Dict[str, Any]:
        """Update Linear issue status."""
        logger.info(f"Updating Linear issue {issue_id} status to {status}")
        
        # This would integrate with actual Linear API
        return {
            "id": issue_id,
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
    
    async def add_comment(self, issue_id: str, comment: str) -> Dict[str, Any]:
        """Add a comment to a Linear issue."""
        logger.info(f"Adding comment to Linear issue {issue_id}")
        
        # This would integrate with actual Linear API
        return {
            "id": f"comment_{hash(comment) % 10000}",
            "issue_id": issue_id,
            "body": comment,
            "created_at": datetime.now().isoformat()
        }
    
    async def get_team_issues(self, team_id: str) -> List[Dict[str, Any]]:
        """Get issues for a specific team."""
        # This would integrate with actual Linear API
        return [
            {
                "id": "example-issue-1",
                "title": "Example Issue 1",
                "status": "In Progress",
                "team_id": team_id
            }
        ]

