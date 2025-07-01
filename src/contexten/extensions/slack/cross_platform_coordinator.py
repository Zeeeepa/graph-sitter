"""Cross-platform coordinator for integrating Slack with Linear and GitHub."""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from contexten.extensions.slack.enhanced_client import NotificationContext
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PlatformType(Enum):
    """Supported platform types."""
    SLACK = "slack"
    LINEAR = "linear"
    GITHUB = "github"


class EventCorrelationType(Enum):
    """Types of event correlations."""
    ISSUE_TO_PR = "issue_to_pr"
    PR_TO_DEPLOYMENT = "pr_to_deployment"
    ISSUE_TO_SLACK_THREAD = "issue_to_slack_thread"
    PR_TO_SLACK_THREAD = "pr_to_slack_thread"
    WORKFLOW_CHAIN = "workflow_chain"


@dataclass
class PlatformEvent:
    """Represents an event from any platform."""
    
    platform: PlatformType
    event_type: str
    event_id: str
    timestamp: datetime
    
    # Common fields
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    assignee: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None
    
    # Platform-specific data
    platform_data: Dict[str, Any] = field(default_factory=dict)
    
    # Correlation data
    correlation_id: Optional[str] = None
    related_events: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventCorrelation:
    """Represents a correlation between events across platforms."""
    
    correlation_id: str
    correlation_type: EventCorrelationType
    primary_event: PlatformEvent
    related_events: List[PlatformEvent] = field(default_factory=list)
    
    # Correlation metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, completed, cancelled
    
    # Workflow data
    workflow_steps: List[str] = field(default_factory=list)
    current_step: Optional[str] = None
    completion_percentage: float = 0.0


@dataclass
class NotificationRule:
    """Rule for cross-platform notifications."""
    
    rule_id: str
    name: str
    description: str
    
    # Trigger conditions
    source_platform: PlatformType
    source_event_types: Set[str]
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Target configuration
    target_platforms: Set[PlatformType] = field(default_factory=set)
    notification_template: str = "default"
    priority: str = "normal"
    
    # Routing configuration
    target_channels: List[str] = field(default_factory=list)
    target_users: List[str] = field(default_factory=list)
    
    # Timing configuration
    delay_seconds: int = 0
    aggregation_window_seconds: int = 0
    
    # Status
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class CrossPlatformCoordinator:
    """Coordinates events and notifications across Slack, Linear, and GitHub."""
    
    def __init__(self, slack_client):
        self.slack_client = slack_client
        self._event_correlations: Dict[str, EventCorrelation] = {}
        self._notification_rules: Dict[str, NotificationRule] = {}
        self._platform_events: List[PlatformEvent] = []
        self._pending_notifications: List[Dict[str, Any]] = []
        
        # Initialize default rules
        self._initialize_default_rules()
        
        logger.info("Cross-platform coordinator initialized")
    
    async def process_platform_event(
        self, 
        platform: PlatformType, 
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an event from any platform and coordinate cross-platform actions.
        
        Args:
            platform: The source platform
            event_data: The event data from the platform
            
        Returns:
            Processing result with any triggered actions
        """
        try:
            # Create platform event
            platform_event = self._create_platform_event(platform, event_data)
            self._platform_events.append(platform_event)
            
            # Find or create correlations
            correlations = await self._find_or_create_correlations(platform_event)
            
            # Apply notification rules
            triggered_notifications = await self._apply_notification_rules(platform_event)
            
            # Update workflow status
            workflow_updates = await self._update_workflow_status(platform_event, correlations)
            
            # Send cross-platform notifications
            notification_results = []
            for notification in triggered_notifications:
                result = await self._send_cross_platform_notification(notification)
                notification_results.append(result)
            
            # Clean up old events
            await self._cleanup_old_events()
            
            return {
                "status": "success",
                "platform_event": self._serialize_platform_event(platform_event),
                "correlations": [corr.correlation_id for corr in correlations],
                "triggered_notifications": len(triggered_notifications),
                "notification_results": notification_results,
                "workflow_updates": workflow_updates
            }
            
        except Exception as e:
            logger.exception(f"Failed to process platform event: {e}")
            return {"status": "error", "error": str(e)}
    
    async def create_workflow_chain(
        self, 
        workflow_type: str, 
        initial_event: PlatformEvent,
        workflow_steps: List[str]
    ) -> str:
        """Create a workflow chain across platforms.
        
        Args:
            workflow_type: Type of workflow (e.g., "issue_to_deployment")
            initial_event: The initial event that starts the workflow
            workflow_steps: List of expected workflow steps
            
        Returns:
            Correlation ID for the workflow chain
        """
        try:
            correlation_id = f"workflow_{workflow_type}_{int(datetime.now().timestamp())}"
            
            correlation = EventCorrelation(
                correlation_id=correlation_id,
                correlation_type=EventCorrelationType.WORKFLOW_CHAIN,
                primary_event=initial_event,
                workflow_steps=workflow_steps,
                current_step=workflow_steps[0] if workflow_steps else None
            )
            
            self._event_correlations[correlation_id] = correlation
            
            # Send initial workflow notification
            await self._send_workflow_notification(correlation, "initiated")
            
            logger.info(f"Created workflow chain: {correlation_id}")
            return correlation_id
            
        except Exception as e:
            logger.exception(f"Failed to create workflow chain: {e}")
            raise
    
    async def update_workflow_step(
        self, 
        correlation_id: str, 
        step: str, 
        event: PlatformEvent
    ) -> bool:
        """Update a workflow step with a new event.
        
        Args:
            correlation_id: The workflow correlation ID
            step: The workflow step being updated
            event: The event that updates this step
            
        Returns:
            True if update was successful
        """
        try:
            if correlation_id not in self._event_correlations:
                logger.warning(f"Workflow correlation not found: {correlation_id}")
                return False
            
            correlation = self._event_correlations[correlation_id]
            correlation.related_events.append(event)
            correlation.current_step = step
            correlation.last_updated = datetime.now()
            
            # Calculate completion percentage
            if step in correlation.workflow_steps:
                step_index = correlation.workflow_steps.index(step)
                correlation.completion_percentage = (step_index + 1) / len(correlation.workflow_steps)
            
            # Check if workflow is complete
            if step == correlation.workflow_steps[-1]:
                correlation.status = "completed"
                await self._send_workflow_notification(correlation, "completed")
            else:
                await self._send_workflow_notification(correlation, "updated")
            
            logger.info(f"Updated workflow step: {correlation_id} -> {step}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to update workflow step: {e}")
            return False
    
    async def get_correlation_status(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a correlation/workflow.
        
        Args:
            correlation_id: The correlation ID to check
            
        Returns:
            Correlation status information or None if not found
        """
        if correlation_id not in self._event_correlations:
            return None
        
        correlation = self._event_correlations[correlation_id]
        
        return {
            "correlation_id": correlation_id,
            "type": correlation.correlation_type.value,
            "status": correlation.status,
            "current_step": correlation.current_step,
            "completion_percentage": correlation.completion_percentage,
            "created_at": correlation.created_at.isoformat(),
            "last_updated": correlation.last_updated.isoformat(),
            "primary_event": self._serialize_platform_event(correlation.primary_event),
            "related_events": [
                self._serialize_platform_event(event) 
                for event in correlation.related_events
            ]
        }
    
    def _create_platform_event(self, platform: PlatformType, event_data: Dict[str, Any]) -> PlatformEvent:
        """Create a PlatformEvent from raw event data."""
        # Extract common fields based on platform
        if platform == PlatformType.LINEAR:
            return self._create_linear_event(event_data)
        elif platform == PlatformType.GITHUB:
            return self._create_github_event(event_data)
        elif platform == PlatformType.SLACK:
            return self._create_slack_event(event_data)
        else:
            # Generic event
            return PlatformEvent(
                platform=platform,
                event_type=event_data.get("type", "unknown"),
                event_id=event_data.get("id", f"{platform.value}_{int(datetime.now().timestamp())}"),
                timestamp=datetime.now(),
                platform_data=event_data
            )
    
    def _create_linear_event(self, event_data: Dict[str, Any]) -> PlatformEvent:
        """Create a PlatformEvent from Linear event data."""
        return PlatformEvent(
            platform=PlatformType.LINEAR,
            event_type=event_data.get("type", "unknown"),
            event_id=event_data.get("data", {}).get("id", f"linear_{int(datetime.now().timestamp())}"),
            timestamp=datetime.now(),
            title=event_data.get("data", {}).get("title"),
            description=event_data.get("data", {}).get("description"),
            author=event_data.get("data", {}).get("creator", {}).get("id"),
            assignee=event_data.get("data", {}).get("assignee", {}).get("id"),
            status=event_data.get("data", {}).get("state", {}).get("name"),
            url=event_data.get("data", {}).get("url"),
            platform_data=event_data
        )
    
    def _create_github_event(self, event_data: Dict[str, Any]) -> PlatformEvent:
        """Create a PlatformEvent from GitHub event data."""
        # Handle different GitHub event types
        if "pull_request" in event_data:
            pr_data = event_data["pull_request"]
            return PlatformEvent(
                platform=PlatformType.GITHUB,
                event_type=f"pull_request_{event_data.get('action', 'unknown')}",
                event_id=str(pr_data.get("id", f"github_{int(datetime.now().timestamp())}")),
                timestamp=datetime.now(),
                title=pr_data.get("title"),
                description=pr_data.get("body"),
                author=pr_data.get("user", {}).get("login"),
                assignee=pr_data.get("assignee", {}).get("login") if pr_data.get("assignee") else None,
                status=pr_data.get("state"),
                url=pr_data.get("html_url"),
                platform_data=event_data
            )
        elif "issue" in event_data:
            issue_data = event_data["issue"]
            return PlatformEvent(
                platform=PlatformType.GITHUB,
                event_type=f"issue_{event_data.get('action', 'unknown')}",
                event_id=str(issue_data.get("id", f"github_{int(datetime.now().timestamp())}")),
                timestamp=datetime.now(),
                title=issue_data.get("title"),
                description=issue_data.get("body"),
                author=issue_data.get("user", {}).get("login"),
                assignee=issue_data.get("assignee", {}).get("login") if issue_data.get("assignee") else None,
                status=issue_data.get("state"),
                url=issue_data.get("html_url"),
                platform_data=event_data
            )
        else:
            return PlatformEvent(
                platform=PlatformType.GITHUB,
                event_type=event_data.get("action", "unknown"),
                event_id=f"github_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(),
                platform_data=event_data
            )
    
    def _create_slack_event(self, event_data: Dict[str, Any]) -> PlatformEvent:
        """Create a PlatformEvent from Slack event data."""
        return PlatformEvent(
            platform=PlatformType.SLACK,
            event_type=event_data.get("type", "unknown"),
            event_id=event_data.get("ts", f"slack_{int(datetime.now().timestamp())}"),
            timestamp=datetime.now(),
            title=event_data.get("text", "")[:100],  # First 100 chars as title
            description=event_data.get("text"),
            author=event_data.get("user"),
            url=f"slack://channel/{event_data.get('channel')}/{event_data.get('ts')}",
            platform_data=event_data
        )
    
    async def _find_or_create_correlations(self, event: PlatformEvent) -> List[EventCorrelation]:
        """Find existing correlations or create new ones for an event."""
        correlations = []
        
        # Look for existing correlations based on event content
        for correlation in self._event_correlations.values():
            if self._events_are_related(correlation.primary_event, event):
                correlation.related_events.append(event)
                correlation.last_updated = datetime.now()
                correlations.append(correlation)
        
        # Create new correlations based on patterns
        new_correlations = await self._detect_new_correlations(event)
        correlations.extend(new_correlations)
        
        return correlations
    
    def _events_are_related(self, event1: PlatformEvent, event2: PlatformEvent) -> bool:
        """Determine if two events are related."""
        # Check for explicit correlation ID
        if event1.correlation_id and event1.correlation_id == event2.correlation_id:
            return True
        
        # Check for title/description similarity
        if event1.title and event2.title:
            if event1.title.lower() in event2.title.lower() or event2.title.lower() in event1.title.lower():
                return True
        
        # Check for author/assignee relationships
        if event1.author == event2.author or event1.assignee == event2.assignee:
            return True
        
        # Platform-specific relationship detection
        if event1.platform == PlatformType.LINEAR and event2.platform == PlatformType.GITHUB:
            return self._linear_github_related(event1, event2)
        elif event1.platform == PlatformType.GITHUB and event2.platform == PlatformType.SLACK:
            return self._github_slack_related(event1, event2)
        
        return False
    
    def _linear_github_related(self, linear_event: PlatformEvent, github_event: PlatformEvent) -> bool:
        """Check if Linear and GitHub events are related."""
        # Look for Linear issue ID in GitHub PR description
        if linear_event.event_id and github_event.description:
            return linear_event.event_id in github_event.description
        
        # Look for similar titles
        if linear_event.title and github_event.title:
            return linear_event.title.lower() in github_event.title.lower()
        
        return False
    
    def _github_slack_related(self, github_event: PlatformEvent, slack_event: PlatformEvent) -> bool:
        """Check if GitHub and Slack events are related."""
        # Look for GitHub URL in Slack message
        if github_event.url and slack_event.description:
            return github_event.url in slack_event.description
        
        # Look for GitHub event ID in Slack message
        if github_event.event_id and slack_event.description:
            return github_event.event_id in slack_event.description
        
        return False
    
    async def _detect_new_correlations(self, event: PlatformEvent) -> List[EventCorrelation]:
        """Detect new correlation patterns for an event."""
        new_correlations = []
        
        # Look for recent events that might be related
        recent_events = [
            e for e in self._platform_events[-50:]  # Last 50 events
            if e.timestamp > datetime.now() - timedelta(hours=24)  # Last 24 hours
            and e.event_id != event.event_id
        ]
        
        for recent_event in recent_events:
            if self._events_are_related(recent_event, event):
                # Create new correlation
                correlation_id = f"auto_{recent_event.platform.value}_{event.platform.value}_{int(datetime.now().timestamp())}"
                
                correlation = EventCorrelation(
                    correlation_id=correlation_id,
                    correlation_type=self._determine_correlation_type(recent_event, event),
                    primary_event=recent_event,
                    related_events=[event]
                )
                
                self._event_correlations[correlation_id] = correlation
                new_correlations.append(correlation)
                
                logger.info(f"Created new correlation: {correlation_id}")
        
        return new_correlations
    
    def _determine_correlation_type(self, event1: PlatformEvent, event2: PlatformEvent) -> EventCorrelationType:
        """Determine the type of correlation between two events."""
        if event1.platform == PlatformType.LINEAR and event2.platform == PlatformType.GITHUB:
            return EventCorrelationType.ISSUE_TO_PR
        elif event1.platform == PlatformType.GITHUB and event2.platform == PlatformType.SLACK:
            return EventCorrelationType.PR_TO_SLACK_THREAD
        elif event1.platform == PlatformType.LINEAR and event2.platform == PlatformType.SLACK:
            return EventCorrelationType.ISSUE_TO_SLACK_THREAD
        else:
            return EventCorrelationType.WORKFLOW_CHAIN
    
    async def _apply_notification_rules(self, event: PlatformEvent) -> List[Dict[str, Any]]:
        """Apply notification rules to determine what notifications to send."""
        triggered_notifications = []
        
        for rule in self._notification_rules.values():
            if not rule.enabled:
                continue
            
            # Check if rule applies to this event
            if (rule.source_platform == event.platform and 
                event.event_type in rule.source_event_types):
                
                # Check additional conditions
                if self._rule_conditions_met(rule, event):
                    notification = {
                        "rule_id": rule.rule_id,
                        "event": event,
                        "target_platforms": rule.target_platforms,
                        "target_channels": rule.target_channels,
                        "target_users": rule.target_users,
                        "template": rule.notification_template,
                        "priority": rule.priority,
                        "delay_seconds": rule.delay_seconds
                    }
                    triggered_notifications.append(notification)
        
        return triggered_notifications
    
    def _rule_conditions_met(self, rule: NotificationRule, event: PlatformEvent) -> bool:
        """Check if rule conditions are met for an event."""
        # Check basic conditions
        for condition_key, condition_value in rule.conditions.items():
            event_value = getattr(event, condition_key, None)
            if event_value != condition_value:
                return False
        
        return True
    
    async def _send_cross_platform_notification(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send a cross-platform notification."""
        try:
            event = notification["event"]
            
            # Create notification context
            context = NotificationContext(
                event_type=event.event_type,
                priority=notification["priority"],
                source_platform=event.platform.value,
                target_channels=notification["target_channels"],
                target_users=notification["target_users"],
                correlation_id=event.correlation_id,
                metadata={
                    "title": event.title,
                    "description": event.description,
                    "author": event.author,
                    "url": event.url,
                    "platform_data": event.platform_data
                }
            )
            
            # Send to Slack if it's a target platform
            if PlatformType.SLACK in notification["target_platforms"]:
                result = await self.slack_client.send_intelligent_notification(
                    event_data={
                        "title": event.title or f"{event.platform.value.title()} Event",
                        "message": event.description or "No description available",
                        "url": event.url,
                        "author": event.author,
                        "platform": event.platform.value
                    },
                    context=context
                )
                return result
            
            return {"status": "success", "message": "Notification processed"}
            
        except Exception as e:
            logger.exception(f"Failed to send cross-platform notification: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _update_workflow_status(
        self, 
        event: PlatformEvent, 
        correlations: List[EventCorrelation]
    ) -> List[Dict[str, Any]]:
        """Update workflow status based on new event."""
        updates = []
        
        for correlation in correlations:
            if correlation.correlation_type == EventCorrelationType.WORKFLOW_CHAIN:
                # Determine if this event advances the workflow
                if event.event_type in correlation.workflow_steps:
                    step_index = correlation.workflow_steps.index(event.event_type)
                    correlation.current_step = event.event_type
                    correlation.completion_percentage = (step_index + 1) / len(correlation.workflow_steps)
                    
                    if step_index == len(correlation.workflow_steps) - 1:
                        correlation.status = "completed"
                    
                    updates.append({
                        "correlation_id": correlation.correlation_id,
                        "step": event.event_type,
                        "completion": correlation.completion_percentage,
                        "status": correlation.status
                    })
        
        return updates
    
    async def _send_workflow_notification(self, correlation: EventCorrelation, action: str):
        """Send a workflow status notification."""
        try:
            context = NotificationContext(
                event_type=f"workflow_{action}",
                priority="normal",
                source_platform="cross_platform",
                target_channels=["#general"],  # Default channel
                metadata={
                    "correlation_id": correlation.correlation_id,
                    "workflow_type": correlation.correlation_type.value,
                    "completion": correlation.completion_percentage,
                    "current_step": correlation.current_step
                }
            )
            
            await self.slack_client.send_intelligent_notification(
                event_data={
                    "title": f"Workflow {action.title()}",
                    "message": f"Workflow {correlation.correlation_id} has been {action}",
                    "completion": correlation.completion_percentage
                },
                context=context
            )
            
        except Exception as e:
            logger.exception(f"Failed to send workflow notification: {e}")
    
    def _initialize_default_rules(self):
        """Initialize default notification rules."""
        # Linear issue to Slack notification
        self._notification_rules["linear_issue_created"] = NotificationRule(
            rule_id="linear_issue_created",
            name="Linear Issue Created",
            description="Notify Slack when a Linear issue is created",
            source_platform=PlatformType.LINEAR,
            source_event_types={"Issue"},
            target_platforms={PlatformType.SLACK},
            target_channels=["#general"],
            priority="normal"
        )
        
        # GitHub PR to Slack notification
        self._notification_rules["github_pr_opened"] = NotificationRule(
            rule_id="github_pr_opened",
            name="GitHub PR Opened",
            description="Notify Slack when a GitHub PR is opened",
            source_platform=PlatformType.GITHUB,
            source_event_types={"pull_request_opened"},
            target_platforms={PlatformType.SLACK},
            target_channels=["#code-reviews"],
            priority="normal"
        )
        
        logger.info("Initialized default cross-platform notification rules")
    
    async def _cleanup_old_events(self):
        """Clean up old events and correlations."""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        # Clean old platform events
        self._platform_events = [
            event for event in self._platform_events
            if event.timestamp > cutoff_date
        ]
        
        # Clean old correlations
        old_correlations = [
            corr_id for corr_id, corr in self._event_correlations.items()
            if corr.created_at < cutoff_date and corr.status == "completed"
        ]
        
        for corr_id in old_correlations:
            del self._event_correlations[corr_id]
    
    def _serialize_platform_event(self, event: PlatformEvent) -> Dict[str, Any]:
        """Serialize a platform event to dict."""
        return {
            "platform": event.platform.value,
            "event_type": event.event_type,
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "title": event.title,
            "description": event.description,
            "author": event.author,
            "assignee": event.assignee,
            "status": event.status,
            "url": event.url,
            "correlation_id": event.correlation_id
        }

