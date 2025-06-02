"""
Linear API Type Definitions

Shared type definitions for Linear integration components.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class LinearIssueState(Enum):
    """Linear issue states"""
    BACKLOG = "backlog"
    UNSTARTED = "unstarted"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELED = "canceled"


class LinearIssuePriority(Enum):
    """Linear issue priorities"""
    NO_PRIORITY = 0
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class LinearProjectState(Enum):
    """Linear project states"""
    PLANNED = "planned"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELED = "canceled"
    PAUSED = "paused"


@dataclass
class LinearUser:
    """Linear user representation"""
    id: str
    name: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    active: bool = True
    admin: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class LinearTeam:
    """Linear team representation"""
    id: str
    name: str
    key: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    private: bool = False
    archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class LinearLabel:
    """Linear label representation"""
    id: str
    name: str
    color: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class LinearProject:
    """Linear project representation"""
    id: str
    name: str
    description: Optional[str] = None
    state: LinearProjectState = LinearProjectState.PLANNED
    progress: float = 0.0
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator: Optional[LinearUser] = None
    lead: Optional[LinearUser] = None
    members: List[LinearUser] = field(default_factory=list)
    teams: List[LinearTeam] = field(default_factory=list)


@dataclass
class LinearIssue:
    """Linear issue representation"""
    id: str
    identifier: str  # e.g., "ENG-123"
    title: str
    description: Optional[str] = None
    state: LinearIssueState = LinearIssueState.BACKLOG
    priority: LinearIssuePriority = LinearIssuePriority.NO_PRIORITY
    estimate: Optional[float] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Relationships
    creator: Optional[LinearUser] = None
    assignee: Optional[LinearUser] = None
    team: Optional[LinearTeam] = None
    project: Optional[LinearProject] = None
    labels: List[LinearLabel] = field(default_factory=list)
    
    # Additional metadata
    cycle_id: Optional[str] = None
    parent_id: Optional[str] = None
    sub_issue_ids: List[str] = field(default_factory=list)
    
    @property
    def is_completed(self) -> bool:
        """Check if issue is completed"""
        return self.state == LinearIssueState.COMPLETED
    
    @property
    def is_active(self) -> bool:
        """Check if issue is active (not completed or canceled)"""
        return self.state not in [LinearIssueState.COMPLETED, LinearIssueState.CANCELED]


@dataclass
class LinearComment:
    """Linear comment representation"""
    id: str
    body: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[LinearUser] = None
    issue_id: str = ""


@dataclass
class LinearWebhookEvent:
    """Linear webhook event representation"""
    type: str
    action: str
    data: Dict[str, Any]
    created_at: datetime
    webhook_id: str
    organization_id: str
    
    @property
    def is_issue_event(self) -> bool:
        """Check if this is an issue-related event"""
        return self.type == "Issue"
    
    @property
    def is_comment_event(self) -> bool:
        """Check if this is a comment-related event"""
        return self.type == "Comment"
    
    @property
    def is_project_event(self) -> bool:
        """Check if this is a project-related event"""
        return self.type == "Project"


@dataclass
class LinearAPIResponse:
    """Linear API response wrapper"""
    success: bool
    data: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    
    @classmethod
    def success_response(cls, data: Any) -> "LinearAPIResponse":
        """Create a successful response"""
        return cls(success=True, data=data)
    
    @classmethod
    def error_response(cls, errors: Union[str, List[str]]) -> "LinearAPIResponse":
        """Create an error response"""
        if isinstance(errors, str):
            errors = [errors]
        return cls(success=False, errors=errors)


@dataclass
class LinearIntegrationConfig:
    """Configuration for Linear integration"""
    api_key: str
    team_id: Optional[str] = None
    webhook_secret: Optional[str] = None
    auto_create_issues: bool = True
    auto_assign_issues: bool = False
    sync_with_github: bool = False
    default_project_id: Optional[str] = None
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []
        
        if not self.api_key:
            errors.append("Linear API key is required")
        
        if self.rate_limit_requests <= 0:
            errors.append("Rate limit requests must be positive")
        
        if self.rate_limit_window <= 0:
            errors.append("Rate limit window must be positive")
        
        return errors


# Type aliases for convenience
LinearIssueDict = Dict[str, Any]
LinearProjectDict = Dict[str, Any]
LinearUserDict = Dict[str, Any]
LinearTeamDict = Dict[str, Any]

# API response types
IssueListResponse = List[LinearIssue]
ProjectListResponse = List[LinearProject]
UserListResponse = List[LinearUser]
TeamListResponse = List[LinearTeam]

