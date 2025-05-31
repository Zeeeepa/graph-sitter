"""
Event Models

Data models for event correlation and analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4


class EventType(Enum):
    """Types of platform events"""
    # GitHub events
    GITHUB_PR_OPENED = "github.pr.opened"
    GITHUB_PR_CLOSED = "github.pr.closed"
    GITHUB_PR_MERGED = "github.pr.merged"
    GITHUB_ISSUE_OPENED = "github.issue.opened"
    GITHUB_ISSUE_CLOSED = "github.issue.closed"
    GITHUB_PUSH = "github.push"
    GITHUB_RELEASE = "github.release"
    
    # Linear events
    LINEAR_ISSUE_CREATED = "linear.issue.created"
    LINEAR_ISSUE_UPDATED = "linear.issue.updated"
    LINEAR_ISSUE_COMPLETED = "linear.issue.completed"
    LINEAR_COMMENT_ADDED = "linear.comment.added"
    
    # Slack events
    SLACK_MESSAGE = "slack.message"
    SLACK_REACTION = "slack.reaction"
    SLACK_THREAD_REPLY = "slack.thread.reply"
    
    # Codegen events
    CODEGEN_TASK_STARTED = "codegen.task.started"
    CODEGEN_TASK_COMPLETED = "codegen.task.completed"
    CODEGEN_TASK_FAILED = "codegen.task.failed"
    
    # Custom events
    CUSTOM = "custom"


class CorrelationType(Enum):
    """Types of event correlations"""
    TEMPORAL = "temporal"  # Events close in time
    CAUSAL = "causal"      # One event caused another
    RELATED = "related"    # Events share common attributes
    SEQUENCE = "sequence"  # Events in a specific sequence


@dataclass
class Event:
    """Represents a platform event"""
    id: str = field(default_factory=lambda: str(uuid4()))
    platform: str = ""
    event_type: EventType = EventType.CUSTOM
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    source: Optional[str] = None
    user_id: Optional[str] = None
    repository: Optional[str] = None
    issue_id: Optional[str] = None
    pr_id: Optional[str] = None
    
    # Correlation hints
    correlation_keys: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def get_correlation_key(self, key_type: str) -> Optional[str]:
        """Get a specific correlation key"""
        for key in self.correlation_keys:
            if key.startswith(f"{key_type}:"):
                return key.split(":", 1)[1]
        return None
    
    def add_correlation_key(self, key_type: str, value: str):
        """Add a correlation key"""
        key = f"{key_type}:{value}"
        if key not in self.correlation_keys:
            self.correlation_keys.append(key)


@dataclass
class EventCorrelation:
    """Represents a correlation between events"""
    id: str = field(default_factory=lambda: str(uuid4()))
    correlation_type: CorrelationType = CorrelationType.RELATED
    events: List[Event] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    
    # Correlation details
    common_attributes: Dict[str, Any] = field(default_factory=dict)
    time_window: Optional[timedelta] = None
    description: str = ""
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    
    def add_event(self, event: Event):
        """Add an event to this correlation"""
        if event not in self.events:
            self.events.append(event)
    
    def get_time_span(self) -> Optional[timedelta]:
        """Get the time span of all events in this correlation"""
        if len(self.events) < 2:
            return None
        
        timestamps = [event.timestamp for event in self.events]
        return max(timestamps) - min(timestamps)
    
    def get_platforms(self) -> List[str]:
        """Get all platforms involved in this correlation"""
        return list(set(event.platform for event in self.events))


@dataclass
class CorrelationRule:
    """Rule for automatic event correlation"""
    id: str
    name: str
    description: str
    
    # Matching criteria
    event_types: List[EventType] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    time_window: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    
    # Correlation logic
    correlation_type: CorrelationType = CorrelationType.RELATED
    required_attributes: List[str] = field(default_factory=list)
    attribute_matchers: Dict[str, str] = field(default_factory=dict)  # attribute -> regex pattern
    
    # Scoring
    base_confidence: float = 0.5
    confidence_modifiers: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def matches_event(self, event: Event) -> bool:
        """Check if an event matches this rule's criteria"""
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Check platform
        if self.platforms and event.platform not in self.platforms:
            return False
        
        # Check required attributes
        for attr in self.required_attributes:
            if attr not in event.data:
                return False
        
        # Check attribute patterns
        for attr, pattern in self.attribute_matchers.items():
            if attr in event.data:
                import re
                if not re.match(pattern, str(event.data[attr])):
                    return False
        
        return True
    
    def calculate_confidence(self, events: List[Event]) -> float:
        """Calculate correlation confidence for a set of events"""
        confidence = self.base_confidence
        
        # Apply confidence modifiers
        for modifier, value in self.confidence_modifiers.items():
            if modifier == "same_user":
                user_ids = [e.user_id for e in events if e.user_id]
                if len(set(user_ids)) == 1:
                    confidence += value
            elif modifier == "same_repository":
                repos = [e.repository for e in events if e.repository]
                if len(set(repos)) == 1:
                    confidence += value
            elif modifier == "time_proximity":
                if len(events) >= 2:
                    timestamps = [e.timestamp for e in events]
                    time_span = max(timestamps) - min(timestamps)
                    if time_span < self.time_window / 2:
                        confidence += value
        
        return min(confidence, 1.0)


# Predefined correlation rules
DEFAULT_CORRELATION_RULES = [
    CorrelationRule(
        id="github_pr_linear_issue",
        name="GitHub PR to Linear Issue",
        description="Correlate GitHub PRs with related Linear issues",
        event_types=[EventType.GITHUB_PR_OPENED, EventType.LINEAR_ISSUE_CREATED],
        time_window=timedelta(hours=1),
        correlation_type=CorrelationType.RELATED,
        required_attributes=["title"],
        base_confidence=0.7,
        confidence_modifiers={
            "same_user": 0.2,
            "time_proximity": 0.1
        }
    ),
    
    CorrelationRule(
        id="codegen_task_github_pr",
        name="Codegen Task to GitHub PR",
        description="Correlate Codegen tasks with resulting GitHub PRs",
        event_types=[EventType.CODEGEN_TASK_COMPLETED, EventType.GITHUB_PR_OPENED],
        time_window=timedelta(minutes=30),
        correlation_type=CorrelationType.CAUSAL,
        base_confidence=0.8,
        confidence_modifiers={
            "same_repository": 0.2
        }
    ),
    
    CorrelationRule(
        id="slack_mention_linear_update",
        name="Slack Mention to Linear Update",
        description="Correlate Slack mentions with Linear issue updates",
        event_types=[EventType.SLACK_MESSAGE, EventType.LINEAR_ISSUE_UPDATED],
        time_window=timedelta(minutes=15),
        correlation_type=CorrelationType.TEMPORAL,
        base_confidence=0.6,
        confidence_modifiers={
            "same_user": 0.3,
            "time_proximity": 0.1
        }
    ),
    
    CorrelationRule(
        id="github_push_sequence",
        name="GitHub Push Sequence",
        description="Correlate sequential GitHub pushes",
        event_types=[EventType.GITHUB_PUSH],
        time_window=timedelta(minutes=10),
        correlation_type=CorrelationType.SEQUENCE,
        required_attributes=["repository", "branch"],
        base_confidence=0.9,
        confidence_modifiers={
            "same_user": 0.1
        }
    )
]

