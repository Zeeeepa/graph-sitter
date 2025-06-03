"""Intelligent notification routing and filtering for enhanced Slack integration."""

import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RoutingRule(Enum):
    """Notification routing rules."""
    DIRECT_MENTION = "direct_mention"
    TEAM_ASSIGNMENT = "team_assignment"
    PROJECT_UPDATE = "project_update"
    CODE_REVIEW = "code_review"
    DEPLOYMENT = "deployment"
    SYSTEM_ALERT = "system_alert"
    WORKFLOW_APPROVAL = "workflow_approval"


@dataclass
class UserPreferences:
    """User notification preferences."""
    
    user_id: str
    
    # Notification channels
    enable_dm: bool = True
    enable_channel_mentions: bool = True
    enable_thread_replies: bool = True
    
    # Priority filtering
    min_priority: NotificationPriority = NotificationPriority.NORMAL
    urgent_only_hours: List[int] = field(default_factory=lambda: [22, 23, 0, 1, 2, 3, 4, 5, 6])  # Quiet hours
    
    # Content filtering
    enabled_event_types: Set[str] = field(default_factory=lambda: {
        "issue_assigned", "pr_review_requested", "deployment_approval",
        "system_alert", "workflow_approval"
    })
    disabled_keywords: Set[str] = field(default_factory=set)
    
    # Frequency limits
    max_notifications_per_hour: int = 20
    enable_aggregation: bool = True
    aggregation_window_minutes: int = 15
    
    # Platform preferences
    github_notifications: bool = True
    linear_notifications: bool = True
    slack_notifications: bool = True


@dataclass
class TeamConfiguration:
    """Team-level notification configuration."""
    
    team_id: str
    team_name: str
    
    # Default channels
    general_channel: Optional[str] = None
    alerts_channel: Optional[str] = None
    reviews_channel: Optional[str] = None
    deployments_channel: Optional[str] = None
    
    # Escalation rules
    escalation_enabled: bool = True
    escalation_delay_minutes: int = 30
    escalation_targets: List[str] = field(default_factory=list)
    
    # Working hours
    working_hours_start: int = 9  # 9 AM
    working_hours_end: int = 17   # 5 PM
    working_days: Set[int] = field(default_factory=lambda: {0, 1, 2, 3, 4})  # Mon-Fri
    timezone: str = "UTC"
    
    # Automation rules
    auto_assign_reviewers: bool = True
    auto_create_threads: bool = True
    auto_update_status: bool = True


@dataclass
class RoutingContext:
    """Context for notification routing decisions."""
    
    event_type: str
    source_platform: str
    priority: NotificationPriority
    
    # Event metadata
    repository: Optional[str] = None
    project: Optional[str] = None
    assignee: Optional[str] = None
    author: Optional[str] = None
    reviewers: List[str] = field(default_factory=list)
    
    # Timing context
    timestamp: datetime = field(default_factory=datetime.now)
    is_working_hours: bool = True
    is_urgent: bool = False
    
    # Content analysis
    keywords: Set[str] = field(default_factory=set)
    mentions: Set[str] = field(default_factory=set)
    
    # Cross-platform correlation
    correlation_id: Optional[str] = None
    related_events: List[str] = field(default_factory=list)


class NotificationRouter:
    """Intelligent notification routing and filtering system."""
    
    def __init__(self, slack_client):
        self.slack_client = slack_client
        self._user_preferences: Dict[str, UserPreferences] = {}
        self._team_configurations: Dict[str, TeamConfiguration] = {}
        self._notification_history: Dict[str, List[Dict]] = {}
        self._routing_rules: Dict[str, List[RoutingRule]] = {}
        
        # Load default configurations
        self._load_default_configurations()
        
        logger.info("Notification router initialized with intelligent routing")
    
    async def route_notification(self, context) -> Any:
        """Route notification intelligently based on context and preferences.
        
        Args:
            context: NotificationContext from enhanced_client
            
        Returns:
            Updated context with intelligent routing decisions
        """
        try:
            # Create routing context
            routing_context = self._create_routing_context(context)
            
            # Apply intelligent routing rules
            target_channels = await self._determine_target_channels(routing_context)
            target_users = await self._determine_target_users(routing_context)
            
            # Apply filtering rules
            filtered_channels = await self._filter_channels(target_channels, routing_context)
            filtered_users = await self._filter_users(target_users, routing_context)
            
            # Apply rate limiting
            rate_limited_users = await self._apply_rate_limiting(filtered_users, routing_context)
            
            # Update context with routing decisions
            context.target_channels = filtered_channels
            context.target_users = rate_limited_users
            context.priority = routing_context.priority.value
            
            # Record routing decision
            await self._record_routing_decision(context, routing_context)
            
            logger.debug(
                f"Routed notification: {len(filtered_channels)} channels, "
                f"{len(rate_limited_users)} users"
            )
            
            return context
            
        except Exception as e:
            logger.exception(f"Failed to route notification: {e}")
            return context
    
    def _create_routing_context(self, context) -> RoutingContext:
        """Create routing context from notification context."""
        # Extract priority from context
        priority_map = {
            "low": NotificationPriority.LOW,
            "normal": NotificationPriority.NORMAL,
            "high": NotificationPriority.HIGH,
            "urgent": NotificationPriority.URGENT
        }
        priority = priority_map.get(context.priority, NotificationPriority.NORMAL)
        
        # Analyze event type and metadata
        routing_context = RoutingContext(
            event_type=context.event_type,
            source_platform=context.source_platform,
            priority=priority,
            timestamp=datetime.now()
        )
        
        # Extract metadata
        if context.metadata:
            routing_context.repository = context.metadata.get("repository")
            routing_context.project = context.metadata.get("project")
            routing_context.assignee = context.metadata.get("assignee")
            routing_context.author = context.metadata.get("author")
            routing_context.reviewers = context.metadata.get("reviewers", [])
            routing_context.correlation_id = context.correlation_id
        
        # Determine if this is working hours
        routing_context.is_working_hours = self._is_working_hours(routing_context.timestamp)
        routing_context.is_urgent = priority == NotificationPriority.URGENT
        
        return routing_context
    
    async def _determine_target_channels(self, context: RoutingContext) -> List[str]:
        """Determine target channels based on routing context."""
        channels = []
        
        # Get team configuration
        team_config = self._get_team_configuration(context)
        
        # Route based on event type
        if context.event_type in ["issue_created", "issue_assigned", "issue_updated"]:
            if team_config and team_config.general_channel:
                channels.append(team_config.general_channel)
        
        elif context.event_type in ["pr_opened", "pr_review_requested", "pr_approved"]:
            if team_config and team_config.reviews_channel:
                channels.append(team_config.reviews_channel)
        
        elif context.event_type in ["deployment_started", "deployment_completed", "deployment_failed"]:
            if team_config and team_config.deployments_channel:
                channels.append(team_config.deployments_channel)
        
        elif context.event_type in ["system_alert", "error_rate_high", "performance_degraded"]:
            if team_config and team_config.alerts_channel:
                channels.append(team_config.alerts_channel)
        
        # Add project-specific channels
        if context.project:
            project_channel = f"#{context.project.lower().replace(' ', '-')}"
            channels.append(project_channel)
        
        return list(set(channels))  # Remove duplicates
    
    async def _determine_target_users(self, context: RoutingContext) -> List[str]:
        """Determine target users based on routing context."""
        users = []
        
        # Direct assignment
        if context.assignee:
            users.append(context.assignee)
        
        # Code review requests
        if context.event_type in ["pr_review_requested", "review_requested"]:
            users.extend(context.reviewers)
        
        # Author notifications
        if context.event_type in ["pr_approved", "pr_merged", "issue_closed"]:
            if context.author:
                users.append(context.author)
        
        # Urgent notifications to on-call
        if context.is_urgent:
            on_call_users = await self._get_on_call_users()
            users.extend(on_call_users)
        
        return list(set(users))  # Remove duplicates
    
    async def _filter_channels(self, channels: List[str], context: RoutingContext) -> List[str]:
        """Filter channels based on team configuration and context."""
        filtered = []
        
        for channel in channels:
            # Check if channel exists and bot has access
            if await self._can_post_to_channel(channel):
                filtered.append(channel)
            else:
                logger.warning(f"Cannot post to channel {channel}")
        
        return filtered
    
    async def _filter_users(self, users: List[str], context: RoutingContext) -> List[str]:
        """Filter users based on preferences and context."""
        filtered = []
        
        for user in users:
            user_prefs = self._get_user_preferences(user)
            
            # Check if user wants this type of notification
            if context.event_type not in user_prefs.enabled_event_types:
                continue
            
            # Check priority filtering
            if context.priority.value < user_prefs.min_priority.value:
                continue
            
            # Check quiet hours
            if not context.is_urgent and self._is_quiet_hours(user_prefs, context.timestamp):
                continue
            
            # Check platform preferences
            if context.source_platform == "github" and not user_prefs.github_notifications:
                continue
            elif context.source_platform == "linear" and not user_prefs.linear_notifications:
                continue
            elif context.source_platform == "slack" and not user_prefs.slack_notifications:
                continue
            
            filtered.append(user)
        
        return filtered
    
    async def _apply_rate_limiting(self, users: List[str], context: RoutingContext) -> List[str]:
        """Apply rate limiting to prevent notification spam."""
        rate_limited = []
        
        for user in users:
            user_prefs = self._get_user_preferences(user)
            
            # Check hourly rate limit
            if self._check_hourly_rate_limit(user, user_prefs):
                rate_limited.append(user)
            else:
                logger.debug(f"Rate limiting user {user} - too many notifications")
        
        return rate_limited
    
    def _get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user notification preferences."""
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = UserPreferences(user_id=user_id)
        return self._user_preferences[user_id]
    
    def _get_team_configuration(self, context: RoutingContext) -> Optional[TeamConfiguration]:
        """Get team configuration for routing context."""
        # This would typically look up team based on repository/project
        # For now, return default team config
        if "default" not in self._team_configurations:
            return None
        return self._team_configurations["default"]
    
    def _is_working_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is within working hours."""
        # Simple implementation - would be enhanced with timezone support
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # Monday = 0, Sunday = 6
        is_weekday = weekday < 5
        is_work_hour = 9 <= hour <= 17
        
        return is_weekday and is_work_hour
    
    def _is_quiet_hours(self, user_prefs: UserPreferences, timestamp: datetime) -> bool:
        """Check if timestamp is within user's quiet hours."""
        return timestamp.hour in user_prefs.urgent_only_hours
    
    def _check_hourly_rate_limit(self, user_id: str, user_prefs: UserPreferences) -> bool:
        """Check if user is within hourly rate limit."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Count notifications in the last hour
        user_history = self._notification_history.get(user_id, [])
        recent_notifications = [
            n for n in user_history 
            if n["timestamp"] > hour_ago
        ]
        
        return len(recent_notifications) < user_prefs.max_notifications_per_hour
    
    async def _can_post_to_channel(self, channel: str) -> bool:
        """Check if bot can post to the specified channel."""
        try:
            # This would check channel permissions
            # For now, assume all channels are accessible
            return True
        except Exception:
            return False
    
    async def _get_on_call_users(self) -> List[str]:
        """Get list of users currently on-call."""
        # This would integrate with on-call scheduling systems
        return []
    
    async def _record_routing_decision(self, context, routing_context: RoutingContext):
        """Record routing decision for analytics and learning."""
        decision = {
            "timestamp": datetime.now(),
            "event_type": context.event_type,
            "priority": context.priority,
            "target_channels": context.target_channels,
            "target_users": context.target_users,
            "routing_context": routing_context
        }
        
        # Record for each target user
        for user in context.target_users:
            if user not in self._notification_history:
                self._notification_history[user] = []
            self._notification_history[user].append(decision)
            
            # Keep only recent history
            cutoff = datetime.now() - timedelta(days=7)
            self._notification_history[user] = [
                n for n in self._notification_history[user]
                if n["timestamp"] > cutoff
            ]
    
    def _load_default_configurations(self):
        """Load default team and user configurations."""
        # Default team configuration
        self._team_configurations["default"] = TeamConfiguration(
            team_id="default",
            team_name="Default Team",
            general_channel="#general",
            alerts_channel="#alerts",
            reviews_channel="#code-reviews",
            deployments_channel="#deployments"
        )
        
        logger.info("Loaded default notification routing configurations")
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user notification preferences."""
        user_prefs = self._get_user_preferences(user_id)
        
        # Update preferences from dict
        for key, value in preferences.items():
            if hasattr(user_prefs, key):
                setattr(user_prefs, key, value)
        
        logger.info(f"Updated notification preferences for user {user_id}")
    
    async def update_team_configuration(self, team_id: str, config: Dict[str, Any]):
        """Update team notification configuration."""
        if team_id not in self._team_configurations:
            self._team_configurations[team_id] = TeamConfiguration(
                team_id=team_id,
                team_name=config.get("team_name", team_id)
            )
        
        team_config = self._team_configurations[team_id]
        
        # Update configuration from dict
        for key, value in config.items():
            if hasattr(team_config, key):
                setattr(team_config, key, value)
        
        logger.info(f"Updated team configuration for {team_id}")

