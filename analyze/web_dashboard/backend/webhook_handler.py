"""
Webhook Handler for Web-Eval-Agent Dashboard

Processes GitHub webhook events and triggers appropriate actions.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from models import Project, WebhookEventCreate
from database import Database
from github_integration import GitHubIntegration
from websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handles GitHub webhook events and triggers appropriate actions."""
    
    def __init__(self):
        """Initialize webhook handler."""
        self.database = None
        self.github_integration = None
        self.websocket_manager = None
        
        # Event handlers mapping
        self.event_handlers = {
            "push": self._handle_push_event,
            "pull_request": self._handle_pull_request_event,
            "pull_request_review": self._handle_pull_request_review_event,
            "issues": self._handle_issues_event,
            "issue_comment": self._handle_issue_comment_event,
            "release": self._handle_release_event,
            "workflow_run": self._handle_workflow_run_event
        }
    
    async def initialize(self, database: Database, github_integration: GitHubIntegration, websocket_manager: WebSocketManager):
        """Initialize webhook handler with dependencies."""
        self.database = database
        self.github_integration = github_integration
        self.websocket_manager = websocket_manager
        logger.info("Webhook handler initialized")
    
    async def process_event(self, project: Project, event_type: str, payload: Dict[str, Any]) -> bool:
        """Process a webhook event."""
        try:
            # Store webhook event in database
            webhook_event = await self.database.create_webhook_event(
                WebhookEventCreate(
                    project_id=project.id,
                    event_type=event_type,
                    payload=payload
                )
            )
            
            logger.info(f"Processing webhook event {event_type} for project {project.name}")
            
            # Get event handler
            handler = self.event_handlers.get(event_type)
            if not handler:
                logger.warning(f"No handler for event type: {event_type}")
                await self.database.mark_webhook_event_processed(
                    webhook_event.id, 
                    f"No handler for event type: {event_type}"
                )
                return False
            
            # Process event
            try:
                await handler(project, payload)
                
                # Mark as processed
                await self.database.mark_webhook_event_processed(webhook_event.id)
                
                logger.info(f"Successfully processed webhook event {event_type} for project {project.name}")
                return True
                
            except Exception as e:
                error_message = f"Error processing {event_type} event: {str(e)}"
                logger.error(error_message)
                
                # Mark as processed with error
                await self.database.mark_webhook_event_processed(webhook_event.id, error_message)
                
                # Send error notification to user
                await self._send_error_notification(project, event_type, str(e))
                
                return False
                
        except Exception as e:
            logger.error(f"Error storing webhook event: {e}")
            return False
    
    async def _handle_push_event(self, project: Project, payload: Dict[str, Any]):
        """Handle push event."""
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])
        pusher = payload.get("pusher", {})
        
        # Check if push is to the project's branch
        project_branch = project.settings.get("branch", "main")
        if not ref.endswith(f"/{project_branch}"):
            logger.info(f"Push to {ref} ignored, project tracks {project_branch}")
            return
        
        # Send notification to user
        await self._send_project_notification(
            project,
            "push",
            {
                "message": f"New push to {project_branch}",
                "commits": len(commits),
                "pusher": pusher.get("name", "Unknown"),
                "ref": ref,
                "commit_messages": [commit.get("message", "") for commit in commits[:3]]
            }
        )
        
        # Update project last activity
        await self.database.update_project(project.id, {"last_activity": datetime.utcnow()})
    
    async def _handle_pull_request_event(self, project: Project, payload: Dict[str, Any]):
        """Handle pull request event."""
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        pr_title = pr.get("title", "")
        pr_state = pr.get("state")
        pr_user = pr.get("user", {}).get("login", "Unknown")
        
        logger.info(f"PR {action} event for #{pr_number}: {pr_title}")
        
        # Handle different PR actions
        if action == "opened":
            await self._handle_pr_opened(project, pr)
        elif action == "closed":
            await self._handle_pr_closed(project, pr)
        elif action == "synchronize":
            await self._handle_pr_synchronized(project, pr)
        elif action == "ready_for_review":
            await self._handle_pr_ready_for_review(project, pr)
        
        # Send notification to user
        await self._send_project_notification(
            project,
            "pull_request",
            {
                "action": action,
                "pr_number": pr_number,
                "pr_title": pr_title,
                "pr_state": pr_state,
                "pr_user": pr_user,
                "pr_url": pr.get("html_url")
            }
        )
        
        # Update project last activity
        await self.database.update_project(project.id, {"last_activity": datetime.utcnow()})
    
    async def _handle_pr_opened(self, project: Project, pr: Dict[str, Any]):
        """Handle PR opened event."""
        pr_number = pr.get("number")
        pr_title = pr.get("title", "")
        pr_body = pr.get("body", "")
        
        # Check if this PR was created by Codegen (based on title or body patterns)
        is_codegen_pr = (
            "codegen-bot/" in pr.get("head", {}).get("ref", "") or
            "[Codegen]" in pr_title or
            "Created by Codegen" in pr_body
        )
        
        if is_codegen_pr:
            logger.info(f"Detected Codegen-created PR #{pr_number}")
            
            # Check if project has auto-validation enabled
            if project.settings.get("auto_validate_pr", False):
                # Start validation pipeline
                await self._trigger_validation_pipeline(project, pr_number)
        
        logger.info(f"PR #{pr_number} opened: {pr_title}")
    
    async def _handle_pr_closed(self, project: Project, pr: Dict[str, Any]):
        """Handle PR closed event."""
        pr_number = pr.get("number")
        merged = pr.get("merged", False)
        
        if merged:
            logger.info(f"PR #{pr_number} merged")
            
            # Send success notification
            await self._send_project_notification(
                project,
                "pr_merged",
                {
                    "pr_number": pr_number,
                    "pr_title": pr.get("title", ""),
                    "message": f"PR #{pr_number} successfully merged"
                }
            )
        else:
            logger.info(f"PR #{pr_number} closed without merging")
    
    async def _handle_pr_synchronized(self, project: Project, pr: Dict[str, Any]):
        """Handle PR synchronized (new commits) event."""
        pr_number = pr.get("number")
        
        # Check if this is a Codegen PR and auto-validation is enabled
        is_codegen_pr = "codegen-bot/" in pr.get("head", {}).get("ref", "")
        
        if is_codegen_pr and project.settings.get("auto_validate_pr", False):
            logger.info(f"Re-validating updated Codegen PR #{pr_number}")
            await self._trigger_validation_pipeline(project, pr_number)
    
    async def _handle_pr_ready_for_review(self, project: Project, pr: Dict[str, Any]):
        """Handle PR ready for review event."""
        pr_number = pr.get("number")
        
        # Check if this is a Codegen PR and auto-validation is enabled
        is_codegen_pr = "codegen-bot/" in pr.get("head", {}).get("ref", "")
        
        if is_codegen_pr and project.settings.get("auto_validate_pr", False):
            logger.info(f"Validating PR #{pr_number} now ready for review")
            await self._trigger_validation_pipeline(project, pr_number)
    
    async def _handle_pull_request_review_event(self, project: Project, payload: Dict[str, Any]):
        """Handle pull request review event."""
        action = payload.get("action")
        review = payload.get("review", {})
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        review_state = review.get("state")
        reviewer = review.get("user", {}).get("login", "Unknown")
        
        logger.info(f"PR review {action} for #{pr_number}: {review_state} by {reviewer}")
        
        # Send notification to user
        await self._send_project_notification(
            project,
            "pull_request_review",
            {
                "action": action,
                "pr_number": pr_number,
                "review_state": review_state,
                "reviewer": reviewer,
                "pr_title": pr.get("title", "")
            }
        )
    
    async def _handle_issues_event(self, project: Project, payload: Dict[str, Any]):
        """Handle issues event."""
        action = payload.get("action")
        issue = payload.get("issue", {})
        issue_number = issue.get("number")
        issue_title = issue.get("title", "")
        issue_user = issue.get("user", {}).get("login", "Unknown")
        
        logger.info(f"Issue {action} event for #{issue_number}: {issue_title}")
        
        # Send notification to user
        await self._send_project_notification(
            project,
            "issues",
            {
                "action": action,
                "issue_number": issue_number,
                "issue_title": issue_title,
                "issue_user": issue_user,
                "issue_url": issue.get("html_url")
            }
        )
    
    async def _handle_issue_comment_event(self, project: Project, payload: Dict[str, Any]):
        """Handle issue comment event."""
        action = payload.get("action")
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})
        issue_number = issue.get("number")
        commenter = comment.get("user", {}).get("login", "Unknown")
        comment_body = comment.get("body", "")
        
        logger.info(f"Issue comment {action} on #{issue_number} by {commenter}")
        
        # Check if comment mentions the bot or contains trigger words
        trigger_words = ["@codegen", "codegen:", "/codegen"]
        is_trigger_comment = any(trigger in comment_body.lower() for trigger in trigger_words)
        
        if is_trigger_comment and action == "created":
            logger.info(f"Trigger comment detected on issue #{issue_number}")
            
            # Extract command from comment
            command = self._extract_command_from_comment(comment_body)
            if command:
                await self._handle_comment_command(project, issue_number, command, commenter)
        
        # Send notification to user
        await self._send_project_notification(
            project,
            "issue_comment",
            {
                "action": action,
                "issue_number": issue_number,
                "commenter": commenter,
                "comment_preview": comment_body[:100] + "..." if len(comment_body) > 100 else comment_body,
                "is_trigger": is_trigger_comment
            }
        )
    
    async def _handle_release_event(self, project: Project, payload: Dict[str, Any]):
        """Handle release event."""
        action = payload.get("action")
        release = payload.get("release", {})
        tag_name = release.get("tag_name", "")
        release_name = release.get("name", "")
        
        logger.info(f"Release {action} event: {tag_name} - {release_name}")
        
        # Send notification to user
        await self._send_project_notification(
            project,
            "release",
            {
                "action": action,
                "tag_name": tag_name,
                "release_name": release_name,
                "release_url": release.get("html_url")
            }
        )
    
    async def _handle_workflow_run_event(self, project: Project, payload: Dict[str, Any]):
        """Handle workflow run event."""
        action = payload.get("action")
        workflow_run = payload.get("workflow_run", {})
        workflow_name = workflow_run.get("name", "")
        status = workflow_run.get("status")
        conclusion = workflow_run.get("conclusion")
        
        logger.info(f"Workflow run {action}: {workflow_name} - {status}/{conclusion}")
        
        # Send notification to user for completed workflows
        if action == "completed":
            await self._send_project_notification(
                project,
                "workflow_run",
                {
                    "action": action,
                    "workflow_name": workflow_name,
                    "status": status,
                    "conclusion": conclusion,
                    "workflow_url": workflow_run.get("html_url")
                }
            )
    
    async def _trigger_validation_pipeline(self, project: Project, pr_number: int):
        """Trigger validation pipeline for a PR."""
        try:
            # Import here to avoid circular imports
            from validation_pipeline import ValidationPipeline
            
            validation_pipeline = ValidationPipeline()
            await validation_pipeline.initialize()
            
            # Start validation asynchronously
            asyncio.create_task(
                validation_pipeline.validate_pr(
                    project=project,
                    pr_number=pr_number,
                    progress_callback=lambda msg: self._send_validation_progress(project, pr_number, msg)
                )
            )
            
            logger.info(f"Triggered validation pipeline for PR #{pr_number}")
            
        except Exception as e:
            logger.error(f"Error triggering validation pipeline: {e}")
    
    async def _send_validation_progress(self, project: Project, pr_number: int, message: str):
        """Send validation progress update."""
        if self.websocket_manager:
            await self.websocket_manager.send_to_user(
                project.user_id,
                {
                    "type": "validation_progress",
                    "data": {
                        "project_id": project.id,
                        "pr_number": pr_number,
                        "message": message
                    }
                }
            )
    
    def _extract_command_from_comment(self, comment_body: str) -> Optional[str]:
        """Extract command from comment body."""
        lines = comment_body.strip().split('\n')
        
        for line in lines:
            line = line.strip().lower()
            
            # Look for command patterns
            if line.startswith('@codegen '):
                return line[9:].strip()  # Remove '@codegen '
            elif line.startswith('codegen:'):
                return line[8:].strip()  # Remove 'codegen:'
            elif line.startswith('/codegen '):
                return line[9:].strip()  # Remove '/codegen '
        
        return None
    
    async def _handle_comment_command(self, project: Project, issue_number: int, command: str, commenter: str):
        """Handle command from issue comment."""
        logger.info(f"Processing command '{command}' from {commenter} on issue #{issue_number}")
        
        # Simple command processing
        if command.startswith("fix"):
            # Extract the issue description and create an agent run
            target_text = f"Fix issue #{issue_number}: {command[3:].strip()}"
            
            # Create agent run
            agent_run = await self.database.create_agent_run(
                project_id=project.id,
                target_text=target_text,
                auto_confirm_plan=project.settings.get("auto_confirm_plan", False)
            )
            
            # Send notification
            await self._send_project_notification(
                project,
                "agent_run_triggered",
                {
                    "trigger": "comment_command",
                    "issue_number": issue_number,
                    "command": command,
                    "commenter": commenter,
                    "run_id": agent_run.id
                }
            )
            
            # Comment on the issue
            await self.github_integration.create_issue_comment(
                project.github_owner,
                project.github_repo,
                issue_number,
                f"🤖 Codegen agent run started to address this issue.\n\nRun ID: `{agent_run.id}`\nTarget: {target_text}"
            )
        
        else:
            logger.warning(f"Unknown command: {command}")
    
    async def _send_project_notification(self, project: Project, event_type: str, data: Dict[str, Any]):
        """Send project notification to user."""
        if self.websocket_manager:
            await self.websocket_manager.send_to_user(
                project.user_id,
                {
                    "type": "project_notification",
                    "data": {
                        "project_id": project.id,
                        "project_name": project.name,
                        "event_type": event_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        **data
                    }
                }
            )
    
    async def _send_error_notification(self, project: Project, event_type: str, error_message: str):
        """Send error notification to user."""
        if self.websocket_manager:
            await self.websocket_manager.send_to_user(
                project.user_id,
                {
                    "type": "webhook_error",
                    "data": {
                        "project_id": project.id,
                        "project_name": project.name,
                        "event_type": event_type,
                        "error_message": error_message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
    
    async def process_queued_events(self):
        """Process queued webhook events (for background processing)."""
        if not self.database:
            return
        
        try:
            # Get unprocessed events
            events = await self.database.get_unprocessed_webhook_events()
            
            for event in events:
                try:
                    # Get project
                    project = await self.database.get_project_by_id(event.project_id)
                    if not project:
                        await self.database.mark_webhook_event_processed(
                            event.id, 
                            "Project not found"
                        )
                        continue
                    
                    # Process event
                    await self.process_event(project, event.event_type, event.payload)
                    
                except Exception as e:
                    logger.error(f"Error processing queued event {event.id}: {e}")
                    await self.database.mark_webhook_event_processed(event.id, str(e))
        
        except Exception as e:
            logger.error(f"Error processing queued events: {e}")
    
    async def start_background_processor(self):
        """Start background event processor."""
        while True:
            try:
                await self.process_queued_events()
                await asyncio.sleep(30)  # Process every 30 seconds
            except asyncio.CancelledError:
                logger.info("Background webhook processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background webhook processor: {e}")
                await asyncio.sleep(60)  # Wait longer on error
