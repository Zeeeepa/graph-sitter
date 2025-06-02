"""
Enhanced Linear Integration Agent

This module provides a comprehensive Linear integration agent based on the
OpenAlpha_Evolve reference implementation, adapted for the contexten framework.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

from .enhanced_client import EnhancedLinearClient
from .webhook.processor import WebhookProcessor
from .workflow.automation import WorkflowAutomation
from .assignment.detector import AssignmentDetector
from .events.manager import EventManager
from .types import LinearIssue, LinearProject, LinearTeam, LinearUser
from ...shared.logging.get_logger import get_logger

logger = get_logger(__name__)

@dataclass
class LinearAgentConfig:
    """Configuration for Linear Integration Agent"""
    api_key: str
    webhook_secret: Optional[str] = None
    auto_assignment: bool = True
    workflow_automation: bool = True
    event_processing: bool = True
    sync_interval: int = 300  # 5 minutes
    max_retries: int = 3
    timeout: int = 30

class EnhancedLinearAgent:
    """
    Enhanced Linear Integration Agent with comprehensive capabilities:
    - GraphQL API integration
    - Webhook processing
    - Workflow automation
    - Assignment detection
    - Event management
    - Real-time synchronization
    """
    
    def __init__(self, config: LinearAgentConfig):
        self.config = config
        self.client = EnhancedLinearClient(config.api_key)
        self.webhook_processor = WebhookProcessor(config.webhook_secret)
        self.workflow_automation = WorkflowAutomation(self.client)
        self.assignment_detector = AssignmentDetector(self.client)
        self.event_manager = EventManager()
        
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
        
        logger.info("Enhanced Linear Agent initialized")
    
    async def start(self) -> None:
        """Start the Linear agent and all its components"""
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
            
            logger.info("Enhanced Linear Agent started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Linear agent: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the Linear agent and cleanup resources"""
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
        
        logger.info("Enhanced Linear Agent stopped")
    
    async def _periodic_sync(self) -> None:
        """Periodic synchronization with Linear"""
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
        """Synchronize data with Linear"""
        try:
            # Sync teams, projects, and issues
            teams = await self.client.get_teams()
            projects = await self.client.get_projects()
            
            # Process any pending events
            await self.event_manager.process_pending_events()
            
            logger.debug(f"Synced {len(teams)} teams and {len(projects)} projects")
            
        except Exception as e:
            logger.error(f"Error syncing data: {e}")
            raise
    
    # Issue Management
    async def create_issue(
        self,
        title: str,
        description: Optional[str] = None,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[int] = None,
        labels: Optional[List[str]] = None,
        parent_id: Optional[str] = None
    ) -> LinearIssue:
        """Create a new Linear issue"""
        try:
            issue = await self.client.create_issue(
                title=title,
                description=description,
                team_id=team_id,
                project_id=project_id,
                assignee_id=assignee_id,
                priority=priority,
                labels=labels,
                parent_id=parent_id
            )
            
            # Trigger workflow automation
            if self.config.workflow_automation:
                await self.workflow_automation.process_issue_created(issue)
            
            # Emit event
            await self.event_manager.emit_event("issue_created", {"issue": issue})
            
            logger.info(f"Created issue: {issue.title} ({issue.id})")
            return issue
            
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            raise
    
    async def update_issue(
        self,
        issue_id: str,
        **updates
    ) -> LinearIssue:
        """Update an existing Linear issue"""
        try:
            issue = await self.client.update_issue(issue_id, **updates)
            
            # Trigger workflow automation
            if self.config.workflow_automation:
                await self.workflow_automation.process_issue_updated(issue)
            
            # Emit event
            await self.event_manager.emit_event("issue_updated", {"issue": issue})
            
            logger.info(f"Updated issue: {issue.title} ({issue.id})")
            return issue
            
        except Exception as e:
            logger.error(f"Error updating issue {issue_id}: {e}")
            raise
    
    async def get_issue(self, issue_id: str) -> Optional[LinearIssue]:
        """Get a Linear issue by ID"""
        try:
            return await self.client.get_issue(issue_id)
        except Exception as e:
            logger.error(f"Error getting issue {issue_id}: {e}")
            return None
    
    async def search_issues(
        self,
        query: Optional[str] = None,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50
    ) -> List[LinearIssue]:
        """Search for Linear issues"""
        try:
            return await self.client.search_issues(
                query=query,
                team_id=team_id,
                project_id=project_id,
                assignee_id=assignee_id,
                state=state,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error searching issues: {e}")
            return []
    
    # Project Management
    async def get_projects(self, team_id: Optional[str] = None) -> List[LinearProject]:
        """Get Linear projects"""
        try:
            return await self.client.get_projects(team_id=team_id)
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []
    
    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        team_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        target_date: Optional[datetime] = None
    ) -> LinearProject:
        """Create a new Linear project"""
        try:
            project = await self.client.create_project(
                name=name,
                description=description,
                team_id=team_id,
                lead_id=lead_id,
                target_date=target_date
            )
            
            # Emit event
            await self.event_manager.emit_event("project_created", {"project": project})
            
            logger.info(f"Created project: {project.name} ({project.id})")
            return project
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    # Team Management
    async def get_teams(self) -> List[LinearTeam]:
        """Get Linear teams"""
        try:
            return await self.client.get_teams()
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            return []
    
    async def get_team_members(self, team_id: str) -> List[LinearUser]:
        """Get members of a Linear team"""
        try:
            return await self.client.get_team_members(team_id)
        except Exception as e:
            logger.error(f"Error getting team members for {team_id}: {e}")
            return []
    
    # Webhook Processing
    async def process_webhook(self, payload: Dict[str, Any], signature: Optional[str] = None) -> bool:
        """Process incoming Linear webhook"""
        try:
            # Validate webhook signature
            if not self.webhook_processor.validate_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return False
            
            # Process the webhook
            result = await self.webhook_processor.process(payload)
            
            # Handle assignment detection
            if self.config.auto_assignment:
                await self.assignment_detector.process_webhook(payload)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return False
    
    # Assignment Detection
    async def detect_assignments(self, text: str) -> List[str]:
        """Detect user assignments in text"""
        try:
            return await self.assignment_detector.detect_assignments(text)
        except Exception as e:
            logger.error(f"Error detecting assignments: {e}")
            return []
    
    # Workflow Automation
    async def trigger_workflow(self, workflow_name: str, context: Dict[str, Any]) -> bool:
        """Trigger a workflow automation"""
        try:
            return await self.workflow_automation.trigger_workflow(workflow_name, context)
        except Exception as e:
            logger.error(f"Error triggering workflow {workflow_name}: {e}")
            return False
    
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
        issue_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a task using Codegen SDK and link it to Linear issue"""
        try:
            # This will be implemented when integrating with the dashboard
            # For now, return a placeholder
            task_data = {
                "prompt": prompt,
                "issue_id": issue_id,
                "context": context or {},
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # If linked to an issue, add a comment
            if issue_id:
                await self.client.add_comment(
                    issue_id,
                    f"🤖 Codegen task created: {prompt[:100]}..."
                )
            
            logger.info(f"Created Codegen task for issue {issue_id}")
            return task_data
            
        except Exception as e:
            logger.error(f"Error creating Codegen task: {e}")
            raise

