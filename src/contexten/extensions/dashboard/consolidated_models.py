"""
Consolidated data models for the dashboard extension.
Combines the best elements from all three PRs into a unified model system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


# Enums for status tracking
class FlowStatus(str, Enum):
    """Flow execution status."""
    IDLE = "idle"
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Individual task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ServiceStatus(str, Enum):
    """Service connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"


class ProjectStatus(str, Enum):
    """Project status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    ERROR = "error"


class QualityGateStatus(str, Enum):
    """Quality gate validation status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"


# Core Data Models
@dataclass
class Project:
    """Enhanced project model combining all PR features."""
    id: str
    name: str
    repo_url: str
    owner: str
    repo_name: str
    full_name: str
    description: str = ""
    default_branch: str = "main"
    language: str = ""
    is_pinned: bool = False
    requirements: str = ""
    flow_status: FlowStatus = FlowStatus.IDLE
    project_status: ProjectStatus = ProjectStatus.ACTIVE
    progress_percentage: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Strands integration fields
    strands_workflow_id: Optional[str] = None
    mcp_session_id: Optional[str] = None
    controlflow_agent_id: Optional[str] = None
    prefect_flow_id: Optional[str] = None
    
    # Quality metrics
    quality_score: float = 0.0
    test_coverage: float = 0.0
    complexity_score: float = 0.0
    security_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "repo_url": self.repo_url,
            "owner": self.owner,
            "repo_name": self.repo_name,
            "full_name": self.full_name,
            "description": self.description,
            "default_branch": self.default_branch,
            "language": self.language,
            "is_pinned": self.is_pinned,
            "requirements": self.requirements,
            "flow_status": self.flow_status.value,
            "project_status": self.project_status.value,
            "progress_percentage": self.progress_percentage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "metadata": self.metadata,
            "strands_workflow_id": self.strands_workflow_id,
            "mcp_session_id": self.mcp_session_id,
            "controlflow_agent_id": self.controlflow_agent_id,
            "prefect_flow_id": self.prefect_flow_id,
            "quality_score": self.quality_score,
            "test_coverage": self.test_coverage,
            "complexity_score": self.complexity_score,
            "security_score": self.security_score
        }


@dataclass
class Task:
    """Enhanced task model for workflow execution."""
    id: str
    flow_id: str
    project_id: str
    title: str
    description: str
    task_type: str = "general"  # codegen, linear, github, slack, validation
    status: TaskStatus = TaskStatus.PENDING
    assignee: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    
    # Strands integration
    strands_task_id: Optional[str] = None
    mcp_task_id: Optional[str] = None
    controlflow_task_id: Optional[str] = None
    
    # Progress tracking
    progress_percentage: float = 0.0
    estimated_duration: Optional[int] = None  # seconds
    actual_duration: Optional[int] = None  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "flow_id": self.flow_id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status.value,
            "assignee": self.assignee,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "result": self.result,
            "dependencies": self.dependencies,
            "strands_task_id": self.strands_task_id,
            "mcp_task_id": self.mcp_task_id,
            "controlflow_task_id": self.controlflow_task_id,
            "progress_percentage": self.progress_percentage,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration
        }


@dataclass
class Flow:
    """Enhanced flow model for project execution."""
    id: str
    project_id: str
    name: str
    description: str = ""
    status: FlowStatus = FlowStatus.IDLE
    tasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Multi-layer orchestration IDs
    strands_workflow_id: Optional[str] = None
    prefect_flow_run_id: Optional[str] = None
    controlflow_flow_id: Optional[str] = None
    
    # Plan and requirements
    original_requirements: str = ""
    generated_plan: Optional[Dict[str, Any]] = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress based on completed tasks."""
        if not self.tasks:
            return 0.0
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        return (completed / len(self.tasks)) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "tasks": [task.to_dict() for task in self.tasks],
            "progress_percentage": self.progress_percentage,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "strands_workflow_id": self.strands_workflow_id,
            "prefect_flow_run_id": self.prefect_flow_run_id,
            "controlflow_flow_id": self.controlflow_flow_id,
            "original_requirements": self.original_requirements,
            "generated_plan": self.generated_plan
        }


@dataclass
class QualityGate:
    """Quality gate for validation."""
    id: str
    name: str
    metric: str
    threshold: Union[float, int]
    operator: str  # >=, <=, ==, !=, >, <
    severity: str  # critical, high, medium, low
    status: QualityGateStatus = QualityGateStatus.PENDING
    current_value: Optional[Union[float, int]] = None
    message: str = ""
    adaptive: bool = True
    historical_data: List[Union[float, int]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "metric": self.metric,
            "threshold": self.threshold,
            "operator": self.operator,
            "severity": self.severity,
            "status": self.status.value,
            "current_value": self.current_value,
            "message": self.message,
            "adaptive": self.adaptive,
            "historical_data": self.historical_data
        }


@dataclass
class UserSettings:
    """Enhanced user settings for dashboard configuration."""
    # API Keys and tokens (stored securely)
    github_token: Optional[str] = None
    linear_token: Optional[str] = None
    slack_token: Optional[str] = None
    codegen_org_id: Optional[str] = None
    codegen_token: Optional[str] = None
    
    # Database and infrastructure
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # Strands configuration
    strands_workflow_enabled: bool = True
    strands_mcp_enabled: bool = True
    controlflow_enabled: bool = True
    prefect_enabled: bool = True
    
    # Notification preferences
    slack_notifications: bool = True
    email_notifications: bool = False
    webhook_notifications: bool = False
    
    # Quality gate settings
    quality_gates_enabled: bool = True
    auto_validation: bool = True
    validation_timeout: int = 300  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization (excluding sensitive data)."""
        return {
            "github_token": "***" if self.github_token else None,
            "linear_token": "***" if self.linear_token else None,
            "slack_token": "***" if self.slack_token else None,
            "codegen_org_id": self.codegen_org_id,
            "codegen_token": "***" if self.codegen_token else None,
            "database_url": "***" if self.database_url else None,
            "redis_url": "***" if self.redis_url else None,
            "strands_workflow_enabled": self.strands_workflow_enabled,
            "strands_mcp_enabled": self.strands_mcp_enabled,
            "controlflow_enabled": self.controlflow_enabled,
            "prefect_enabled": self.prefect_enabled,
            "slack_notifications": self.slack_notifications,
            "email_notifications": self.email_notifications,
            "webhook_notifications": self.webhook_notifications,
            "quality_gates_enabled": self.quality_gates_enabled,
            "auto_validation": self.auto_validation,
            "validation_timeout": self.validation_timeout
        }


# Pydantic Request/Response Models
class ServiceStatusResponse(BaseModel):
    """Response model for service status."""
    github: ServiceStatus
    linear: ServiceStatus
    slack: ServiceStatus
    codegen: ServiceStatus
    database: ServiceStatus
    strands_workflow: ServiceStatus = ServiceStatus.UNKNOWN
    strands_mcp: ServiceStatus = ServiceStatus.UNKNOWN
    controlflow: ServiceStatus = ServiceStatus.UNKNOWN
    prefect: ServiceStatus = ServiceStatus.UNKNOWN


class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    repo_url: str
    requirements: Optional[str] = ""
    auto_pin: bool = True


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""
    requirements: Optional[str] = None
    is_pinned: Optional[bool] = None
    flow_status: Optional[FlowStatus] = None


class FlowStartRequest(BaseModel):
    """Request model for starting a flow."""
    project_id: str
    requirements: str
    flow_name: Optional[str] = None
    auto_execute: bool = True


class PlanGenerateRequest(BaseModel):
    """Request model for generating a plan."""
    project_id: str
    requirements: str
    include_quality_gates: bool = True


class CodegenTaskRequest(BaseModel):
    """Request model for Codegen SDK tasks."""
    task_type: str  # "generate_plan", "generate_code", "review_pr"
    project_id: str
    prompt: str
    context: Optional[Dict[str, Any]] = None


class SystemHealthResponse(BaseModel):
    """Response model for system health."""
    status: str
    timestamp: str
    services: ServiceStatusResponse
    system_metrics: Dict[str, Any]
    active_workflows: int
    active_tasks: int
    error_count: int


class DashboardResponse(BaseModel):
    """Generic response model for dashboard API."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# WebSocket Event Models
class WebSocketEvent(BaseModel):
    """Base WebSocket event model."""
    type: str
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    project_id: Optional[str] = None
    flow_id: Optional[str] = None
    task_id: Optional[str] = None


class ProjectUpdateEvent(WebSocketEvent):
    """Project update WebSocket event."""
    type: str = "project_update"


class FlowUpdateEvent(WebSocketEvent):
    """Flow update WebSocket event."""
    type: str = "flow_update"


class TaskUpdateEvent(WebSocketEvent):
    """Task update WebSocket event."""
    type: str = "task_update"


class QualityGateEvent(WebSocketEvent):
    """Quality gate WebSocket event."""
    type: str = "quality_gate_update"


class SystemHealthEvent(WebSocketEvent):
    """System health WebSocket event."""
    type: str = "system_health_update"

