"""
Event Coordinator for Single-User Dashboard

Coordinates events between all extensions and manages event flow.
Handles event routing, filtering, and integration with external services.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from graph_sitter.shared.logging.get_logger import get_logger
from .models import WorkflowEvent
from .event_bus import EventBus
from ..slack.slack import Slack

logger = get_logger(__name__)


class EventCoordinator:
    """
    Coordinates events across all dashboard components.
    
    Features:
    - Event creation and routing
    - Integration with Slack for notifications
    - Event filtering and processing
    - System health monitoring
    - Automated responses to events
    """
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.event_bus = EventBus()
        self.slack: Optional[Slack] = None
        self.notification_settings = {
            "workflow_started": True,
            "workflow_completed": True,
            "workflow_failed": True,
            "task_completed": False,
            "task_failed": True,
            "analysis_completed": True,
            "deployment_completed": True,
            "project_pinned": False,
            "project_unpinned": False
        }
        
    async def initialize(self):
        """Initialize the event coordinator"""
        logger.info("Initializing EventCoordinator...")
        
        # Initialize event bus
        await self.event_bus.initialize()
        
        # Initialize Slack integration
        if self.dashboard.settings_manager.is_extension_enabled("slack"):
            slack_webhook = self.dashboard.settings_manager.get_api_credential("slack")
            if slack_webhook:
                self.slack = Slack({"webhook_url": slack_webhook})
                await self.slack.initialize()
                logger.info("Slack integration initialized")
            else:
                logger.warning("Slack webhook not configured")
                
        # Set up event handlers
        await self._setup_event_handlers()
        
    async def _setup_event_handlers(self):
        """Set up event handlers for different event types"""
        
        # Workflow events
        await self.event_bus.subscribe("workflow_started", self._handle_workflow_started)
        await self.event_bus.subscribe("workflow_completed", self._handle_workflow_completed)
        await self.event_bus.subscribe("workflow_failed", self._handle_workflow_failed)
        
        # Task events
        await self.event_bus.subscribe("task_completed", self._handle_task_completed)
        await self.event_bus.subscribe("task_failed", self._handle_task_failed)
        
        # Analysis events
        await self.event_bus.subscribe("analysis_completed", self._handle_analysis_completed)
        
        # Deployment events
        await self.event_bus.subscribe("deployment_completed", self._handle_deployment_completed)
        
        # Project events
        await self.event_bus.subscribe("project_pinned", self._handle_project_pinned)
        
        logger.info("Event handlers set up")
        
    async def emit_event(self, event_type: str, source: str, project_id: Optional[str] = None,
                        task_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        """
        Emit an event to the event bus
        
        Args:
            event_type: Type of event
            source: Source component that generated the event
            project_id: Optional project ID
            task_id: Optional task ID
            data: Optional event data
        """
        try:
            event = WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                source=source,
                project_id=project_id,
                task_id=task_id,
                data=data or {},
                timestamp=datetime.now()
            )
            
            await self.event_bus.publish(event)
            
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
            
    async def _handle_workflow_started(self, event: WorkflowEvent):
        """Handle workflow started event"""
        try:
            if self.notification_settings.get("workflow_started", True):
                await self._send_slack_notification(
                    f"🚀 Workflow started for project {event.project_id}",
                    event.data
                )
                
        except Exception as e:
            logger.error(f"Failed to handle workflow_started event: {e}")
            
    async def _handle_workflow_completed(self, event: WorkflowEvent):
        """Handle workflow completed event"""
        try:
            data = event.data
            completed_tasks = data.get("completed_tasks", 0)
            failed_tasks = data.get("failed_tasks", 0)
            
            if self.notification_settings.get("workflow_completed", True):
                message = f"✅ Workflow completed for project {event.project_id}\n"
                message += f"Tasks completed: {completed_tasks}, Failed: {failed_tasks}"
                
                await self._send_slack_notification(message, data)
                
        except Exception as e:
            logger.error(f"Failed to handle workflow_completed event: {e}")
            
    async def _handle_workflow_failed(self, event: WorkflowEvent):
        """Handle workflow failed event"""
        try:
            if self.notification_settings.get("workflow_failed", True):
                await self._send_slack_notification(
                    f"❌ Workflow failed for project {event.project_id}",
                    event.data
                )
                
        except Exception as e:
            logger.error(f"Failed to handle workflow_failed event: {e}")
            
    async def _handle_task_completed(self, event: WorkflowEvent):
        """Handle task completed event"""
        try:
            if self.notification_settings.get("task_completed", False):
                task_title = event.data.get("task_title", "Unknown task")
                await self._send_slack_notification(
                    f"✅ Task completed: {task_title}",
                    event.data
                )
                
        except Exception as e:
            logger.error(f"Failed to handle task_completed event: {e}")
            
    async def _handle_task_failed(self, event: WorkflowEvent):
        """Handle task failed event"""
        try:
            if self.notification_settings.get("task_failed", True):
                task_title = event.data.get("task_title", "Unknown task")
                await self._send_slack_notification(
                    f"❌ Task failed: {task_title}",
                    event.data
                )
                
        except Exception as e:
            logger.error(f"Failed to handle task_failed event: {e}")
            
    async def _handle_analysis_completed(self, event: WorkflowEvent):
        """Handle analysis completed event"""
        try:
            if self.notification_settings.get("analysis_completed", True):
                data = event.data
                quality_score = data.get("quality_score", 0.0)
                error_count = data.get("error_count", 0)
                
                message = f"🔍 Code analysis completed for project {event.project_id}\n"
                message += f"Quality Score: {quality_score:.1f}/10, Errors: {error_count}"
                
                await self._send_slack_notification(message, data)
                
        except Exception as e:
            logger.error(f"Failed to handle analysis_completed event: {e}")
            
    async def _handle_deployment_completed(self, event: WorkflowEvent):
        """Handle deployment completed event"""
        try:
            if self.notification_settings.get("deployment_completed", True):
                data = event.data
                sandbox_id = data.get("sandbox_id", "unknown")
                
                message = f"🚀 Deployment completed for project {event.project_id}\n"
                message += f"Sandbox: {sandbox_id}"
                
                await self._send_slack_notification(message, data)
                
        except Exception as e:
            logger.error(f"Failed to handle deployment_completed event: {e}")
            
    async def _handle_project_pinned(self, event: WorkflowEvent):
        """Handle project pinned event"""
        try:
            if self.notification_settings.get("project_pinned", False):
                repo_url = event.data.get("repo_url", "unknown")
                await self._send_slack_notification(
                    f"📌 Project pinned: {repo_url}",
                    event.data
                )
                
        except Exception as e:
            logger.error(f"Failed to handle project_pinned event: {e}")
            
    async def _send_slack_notification(self, message: str, data: Dict[str, Any]):
        """Send notification to Slack"""
        try:
            if not self.slack:
                logger.debug("Slack not configured, skipping notification")
                return
                
            # Get notification level setting
            notification_level = self.dashboard.settings_manager.get_extension_setting(
                "slack", "notification_level", "normal"
            )
            
            if notification_level == "minimal":
                # Only send critical notifications
                if "failed" not in message.lower() and "error" not in message.lower():
                    return
                    
            await self.slack.send_message(message)
            logger.debug(f"Sent Slack notification: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            
    async def add_websocket_connection(self, websocket):
        """Add WebSocket connection for real-time updates"""
        await self.event_bus.add_websocket(websocket)
        
    async def remove_websocket_connection(self, websocket):
        """Remove WebSocket connection"""
        await self.event_bus.remove_websocket(websocket)
        
    async def get_recent_events(self, limit: int = 50, event_type: Optional[str] = None,
                               project_id: Optional[str] = None):
        """Get recent events with filtering"""
        return self.event_bus.get_recent_events(limit, event_type, project_id)
        
    async def get_event_statistics(self):
        """Get event statistics"""
        return self.event_bus.get_event_statistics()
        
    async def update_notification_settings(self, settings: Dict[str, bool]):
        """Update notification settings"""
        self.notification_settings.update(settings)
        logger.info(f"Updated notification settings: {settings}")
        
    async def get_notification_settings(self):
        """Get current notification settings"""
        return self.notification_settings.copy()
        
    async def test_slack_integration(self) -> bool:
        """Test Slack integration"""
        try:
            if not self.slack:
                return False
                
            await self.slack.send_message("🧪 Dashboard test message - Slack integration working!")
            return True
            
        except Exception as e:
            logger.error(f"Slack test failed: {e}")
            return False
            
    async def shutdown(self):
        """Shutdown the event coordinator"""
        logger.info("Shutting down EventCoordinator...")
        await self.event_bus.shutdown()
        logger.info("EventCoordinator shutdown complete")

