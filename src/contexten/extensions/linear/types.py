from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class LinearUser(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    active: bool = True


class LinearTeam(BaseModel):
    id: str
    name: str
    key: str
    description: Optional[str] = None
    private: bool = False


class LinearLabel(BaseModel):
    id: str
    name: str
    color: str
    description: Optional[str] = None


class LinearProject(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    url: Optional[str] = None


class LinearState(BaseModel):
    id: str
    name: str
    type: str
    color: str
    position: float


class LinearComment(BaseModel):
    id: str
    body: str
    user: Optional[LinearUser] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    url: Optional[str] = None


class LinearIssue(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    number: Optional[int] = None
    url: Optional[str] = None
    assignee: Optional[LinearUser] = None
    assignee_id: Optional[str] = None
    creator: Optional[LinearUser] = None
    team: Optional[LinearTeam] = None
    state: Optional[LinearState] = None
    labels: List[LinearLabel] = []
    project: Optional[LinearProject] = None
    priority: Optional[int] = None
    estimate: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None


class LinearEventType(str, Enum):
    """Linear webhook event types"""
    ISSUE_CREATE = "Issue"
    ISSUE_UPDATE = "IssueUpdate"
    ISSUE_REMOVE = "IssueRemove"
    COMMENT_CREATE = "Comment"
    COMMENT_UPDATE = "CommentUpdate"
    COMMENT_REMOVE = "CommentRemove"
    PROJECT_UPDATE = "ProjectUpdate"
    CYCLE_UPDATE = "CycleUpdate"


class LinearEventAction(str, Enum):
    """Linear event actions"""
    CREATE = "create"
    UPDATE = "update"
    REMOVE = "remove"


class AssignmentAction(str, Enum):
    """Assignment actions"""
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    REASSIGNED = "reassigned"


class AssignmentEvent(BaseModel):
    """Assignment event for tracking bot assignments"""
    issue_id: str
    action: AssignmentAction
    assignee_id: Optional[str] = None
    previous_assignee_id: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskProgress(BaseModel):
    """Task progress information"""
    status: TaskStatus
    progress_percentage: float = 0.0
    current_step: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class WorkflowTask(BaseModel):
    """Workflow task representation"""
    id: str
    issue_id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: TaskProgress
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    metadata: Dict[str, Any] = {}


class WebhookEvent(BaseModel):
    """Webhook event wrapper"""
    event_id: str
    event_type: LinearEventType
    payload: Dict[str, Any]
    signature: Optional[str] = None
    timestamp: datetime
    processed: bool = False
    retry_count: int = 0
    error_message: Optional[str] = None


class IntegrationStatus(BaseModel):
    """Integration status information"""
    initialized: bool = False
    monitoring_active: bool = False
    last_sync: Optional[datetime] = None
    webhook_processor_status: str = "stopped"
    assignment_detector_status: str = "stopped"
    workflow_automation_status: str = "stopped"
    event_manager_status: str = "stopped"
    active_tasks: int = 0
    processed_events: int = 0
    failed_events: int = 0
    last_error: Optional[str] = None


class ComponentStats(BaseModel):
    """Component statistics"""
    requests_made: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_request: Optional[datetime] = None
    last_error: Optional[str] = None
    uptime_seconds: float = 0.0


class LinearIntegrationMetrics(BaseModel):
    """Comprehensive integration metrics"""
    status: IntegrationStatus
    client_stats: ComponentStats
    webhook_stats: ComponentStats
    assignment_stats: ComponentStats
    workflow_stats: ComponentStats
    event_stats: ComponentStats
    collected_at: datetime


class LinearEvent(BaseModel):
    """Represents a Linear webhook event."""
    type: str
    action: str
    data: Dict[str, Any]
    timestamp: datetime
    webhook_id: Optional[str] = None
    organization_id: Optional[str] = None


@dataclass
class LinearComment:
    """Linear comment"""
    id: str
    body: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    issue_id: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LinearComment':
        return cls(
            id=data['id'],
            body=data['body'],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')),
            user_id=data['user']['id'],
            issue_id=data['issue']['id']
        )
