"""Enhanced Slack Client with intelligent notifications and workflow coordination."""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from contexten.extensions.slack.types import SlackEvent, SlackMessage
from contexten.extensions.slack.notification_router import NotificationRouter
from contexten.extensions.slack.block_kit_builder import BlockKitBuilder
from contexten.extensions.slack.analytics_engine import AnalyticsEngine
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class SlackConfig:
    """Configuration for enhanced Slack integration."""
    
    bot_token: str
    signing_secret: str
    app_token: Optional[str] = None
    
    # Performance settings
    notification_timeout: float = 1.0  # <1 second requirement
    interactive_timeout: float = 0.5   # <500ms requirement
    
    # Feature flags
    enable_analytics: bool = True
    enable_intelligent_routing: bool = True
    enable_cross_platform: bool = True
    enable_interactive_workflows: bool = True
    
    # Notification settings
    max_notifications_per_minute: int = 60
    enable_notification_aggregation: bool = True
    aggregation_window_seconds: int = 30
    
    # Analytics settings
    analytics_retention_days: int = 90
    enable_team_insights: bool = True
    enable_productivity_metrics: bool = True


@dataclass
class NotificationContext:
    """Context information for intelligent notification routing."""
    
    event_type: str
    priority: str = "normal"  # low, normal, high, urgent
    source_platform: str = "slack"  # slack, github, linear
    target_channels: List[str] = field(default_factory=list)
    target_users: List[str] = field(default_factory=list)
    thread_ts: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowContext:
    """Context for workflow coordination and automation."""
    
    workflow_type: str
    workflow_id: str
    step: str
    data: Dict[str, Any] = field(default_factory=dict)
    approvers: List[str] = field(default_factory=list)
    deadline: Optional[datetime] = None
    escalation_rules: Dict[str, Any] = field(default_factory=dict)


class EnhancedSlackClient:
    """Enhanced Slack client with intelligent communication and workflow coordination."""
    
    def __init__(self, config: SlackConfig):
        self.config = config
        self._client = WebClient(token=config.bot_token)
        
        # Initialize enhanced components
        self.notification_router = NotificationRouter(self)
        self.block_kit_builder = BlockKitBuilder()
        self.analytics_engine = AnalyticsEngine(config) if config.enable_analytics else None
        
        # Internal state
        self._notification_cache: Dict[str, List[Dict]] = {}
        self._workflow_states: Dict[str, WorkflowContext] = {}
        self._user_preferences: Dict[str, Dict] = {}
        
        logger.info("Enhanced Slack client initialized with advanced features")
    
    @property
    def client(self) -> WebClient:
        """Access to underlying Slack WebClient."""
        return self._client
    
    async def send_intelligent_notification(
        self, 
        event_data: Dict[str, Any], 
        context: NotificationContext
    ) -> Dict[str, Any]:
        """Send intelligent notification with routing, filtering, and aggregation.
        
        Args:
            event_data: The event data to send
            context: Notification context for intelligent routing
            
        Returns:
            Response from Slack API with delivery metadata
        """
        start_time = datetime.now()
        
        try:
            # Route notification intelligently
            if self.config.enable_intelligent_routing:
                context = await self.notification_router.route_notification(context)
            
            # Check for aggregation opportunities
            if self.config.enable_notification_aggregation:
                aggregated = await self._check_aggregation(event_data, context)
                if aggregated:
                    return aggregated
            
            # Build enhanced message with Block Kit
            message_blocks = await self.block_kit_builder.build_notification_blocks(
                event_data, context
            )
            
            # Send to target channels/users
            responses = []
            
            for channel in context.target_channels:
                response = await self._send_to_channel(
                    channel=channel,
                    blocks=message_blocks,
                    thread_ts=context.thread_ts,
                    metadata=context.metadata
                )
                responses.append(response)
            
            for user in context.target_users:
                response = await self._send_to_user(
                    user=user,
                    blocks=message_blocks,
                    metadata=context.metadata
                )
                responses.append(response)
            
            # Record analytics
            if self.analytics_engine:
                await self.analytics_engine.record_notification(
                    event_data, context, responses
                )
            
            # Validate performance requirement
            duration = (datetime.now() - start_time).total_seconds()
            if duration > self.config.notification_timeout:
                logger.warning(
                    f"Notification delivery took {duration:.3f}s, "
                    f"exceeding {self.config.notification_timeout}s target"
                )
            
            return {
                "status": "success",
                "responses": responses,
                "duration_seconds": duration,
                "context": context
            }
            
        except Exception as e:
            logger.exception(f"Failed to send intelligent notification: {e}")
            return {
                "status": "error",
                "error": str(e),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    async def coordinate_team_workflow(
        self, 
        workflow_type: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Coordinate interactive team workflow with approvals and automation.
        
        Args:
            workflow_type: Type of workflow (approval, review, deployment, etc.)
            data: Workflow data and parameters
            
        Returns:
            Workflow coordination response
        """
        start_time = datetime.now()
        
        try:
            # Create workflow context
            workflow_context = WorkflowContext(
                workflow_type=workflow_type,
                workflow_id=data.get("workflow_id", f"{workflow_type}_{int(datetime.now().timestamp())}"),
                step=data.get("step", "initiated"),
                data=data,
                approvers=data.get("approvers", []),
                deadline=data.get("deadline"),
                escalation_rules=data.get("escalation_rules", {})
            )
            
            # Store workflow state
            self._workflow_states[workflow_context.workflow_id] = workflow_context
            
            # Build interactive workflow components
            workflow_blocks = await self.block_kit_builder.build_workflow_blocks(
                workflow_context
            )
            
            # Send workflow initiation
            responses = []
            
            # Send to approvers
            for approver in workflow_context.approvers:
                response = await self._send_workflow_request(
                    user=approver,
                    workflow_context=workflow_context,
                    blocks=workflow_blocks
                )
                responses.append(response)
            
            # Send to notification channels if specified
            if "notification_channels" in data:
                for channel in data["notification_channels"]:
                    response = await self._send_workflow_notification(
                        channel=channel,
                        workflow_context=workflow_context,
                        blocks=workflow_blocks
                    )
                    responses.append(response)
            
            # Set up escalation if needed
            if workflow_context.deadline:
                await self._schedule_workflow_escalation(workflow_context)
            
            # Record analytics
            if self.analytics_engine:
                await self.analytics_engine.record_workflow_initiation(workflow_context)
            
            # Validate performance requirement
            duration = (datetime.now() - start_time).total_seconds()
            if duration > self.config.interactive_timeout:
                logger.warning(
                    f"Workflow coordination took {duration:.3f}s, "
                    f"exceeding {self.config.interactive_timeout}s target"
                )
            
            return {
                "status": "success",
                "workflow_id": workflow_context.workflow_id,
                "responses": responses,
                "duration_seconds": duration
            }
            
        except Exception as e:
            logger.exception(f"Failed to coordinate team workflow: {e}")
            return {
                "status": "error",
                "error": str(e),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    async def analyze_team_communication(self, timeframe: str) -> Dict[str, Any]:
        """Analyze team communication patterns and generate insights.
        
        Args:
            timeframe: Analysis timeframe (day, week, month, quarter)
            
        Returns:
            Communication analysis and insights
        """
        if not self.analytics_engine:
            return {"error": "Analytics not enabled"}
        
        try:
            return await self.analytics_engine.analyze_communication_patterns(timeframe)
        except Exception as e:
            logger.exception(f"Failed to analyze team communication: {e}")
            return {"error": str(e)}
    
    async def handle_interactive_component(
        self, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle interactive component interactions (buttons, modals, etc.).
        
        Args:
            payload: Slack interactive component payload
            
        Returns:
            Response for the interactive component
        """
        start_time = datetime.now()
        
        try:
            action_type = payload.get("type")
            action_id = payload.get("actions", [{}])[0].get("action_id", "")
            
            if action_type == "block_actions":
                response = await self._handle_block_action(payload)
            elif action_type == "view_submission":
                response = await self._handle_modal_submission(payload)
            elif action_type == "view_closed":
                response = await self._handle_modal_closed(payload)
            else:
                response = {"error": f"Unknown action type: {action_type}"}
            
            # Validate performance requirement
            duration = (datetime.now() - start_time).total_seconds()
            if duration > self.config.interactive_timeout:
                logger.warning(
                    f"Interactive component handling took {duration:.3f}s, "
                    f"exceeding {self.config.interactive_timeout}s target"
                )
            
            response["duration_seconds"] = duration
            return response
            
        except Exception as e:
            logger.exception(f"Failed to handle interactive component: {e}")
            return {
                "error": str(e),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    async def _check_aggregation(
        self, 
        event_data: Dict[str, Any], 
        context: NotificationContext
    ) -> Optional[Dict[str, Any]]:
        """Check if notification should be aggregated with recent similar notifications."""
        if not self.config.enable_notification_aggregation:
            return None
        
        # Implementation for notification aggregation logic
        # This would check recent notifications and potentially aggregate them
        return None
    
    async def _send_to_channel(
        self, 
        channel: str, 
        blocks: List[Dict], 
        thread_ts: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send message to a Slack channel."""
        try:
            response = self._client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                thread_ts=thread_ts,
                metadata=metadata or {}
            )
            return {"status": "success", "channel": channel, "ts": response["ts"]}
        except SlackApiError as e:
            logger.error(f"Failed to send to channel {channel}: {e}")
            return {"status": "error", "channel": channel, "error": str(e)}
    
    async def _send_to_user(
        self, 
        user: str, 
        blocks: List[Dict],
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send direct message to a user."""
        try:
            # Open DM channel
            dm_response = self._client.conversations_open(users=[user])
            channel = dm_response["channel"]["id"]
            
            # Send message
            response = self._client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                metadata=metadata or {}
            )
            return {"status": "success", "user": user, "ts": response["ts"]}
        except SlackApiError as e:
            logger.error(f"Failed to send to user {user}: {e}")
            return {"status": "error", "user": user, "error": str(e)}
    
    async def _send_workflow_request(
        self, 
        user: str, 
        workflow_context: WorkflowContext,
        blocks: List[Dict]
    ) -> Dict[str, Any]:
        """Send workflow request to an approver."""
        # Implementation for sending workflow approval requests
        return await self._send_to_user(user, blocks)
    
    async def _send_workflow_notification(
        self, 
        channel: str, 
        workflow_context: WorkflowContext,
        blocks: List[Dict]
    ) -> Dict[str, Any]:
        """Send workflow notification to a channel."""
        # Implementation for sending workflow notifications
        return await self._send_to_channel(channel, blocks)
    
    async def _schedule_workflow_escalation(self, workflow_context: WorkflowContext):
        """Schedule workflow escalation if deadline is approaching."""
        # Implementation for scheduling escalation
        pass
    
    async def _handle_block_action(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle block action (button clicks, etc.)."""
        # Implementation for handling block actions
        return {"status": "handled"}
    
    async def _handle_modal_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle modal form submissions."""
        # Implementation for handling modal submissions
        return {"status": "handled"}
    
    async def _handle_modal_closed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle modal close events."""
        # Implementation for handling modal closures
        return {"status": "handled"}

