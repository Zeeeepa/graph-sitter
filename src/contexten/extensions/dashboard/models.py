"""
Dashboard Data Models

Comprehensive data models for the dashboard system that integrate with all Contexten extensions.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class FlowStatus(str, Enum):
    """Flow status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class PlanStatus(str, Enum):
    """Plan status enumeration"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QualityGateStatus(str, Enum):
    """Quality gate status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class DashboardProject(BaseModel):
    """Enhanced project model for dashboard"""
    id: str
    name: str
    description: str
    repository: str
    status: ProjectStatus = ProjectStatus.ACTIVE
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    flow_enabled: bool = False
    flow_status: FlowStatus = FlowStatus.STOPPED
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    
    # Metrics
    metrics: Optional[Dict[str, Any]] = None
    
    # Configuration
    requirements: Optional[str] = None
    plan_id: Optional[str] = None
    
    # GitHub integration
    github_owner: Optional[str] = None
    github_repo: Optional[str] = None
    default_branch: str = "main"
    
    # Linear integration
    linear_team_id: Optional[str] = None
    linear_project_id: Optional[str] = None
    
    # Quality settings
    quality_gates_enabled: bool = True
    auto_merge_enabled: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardTask(BaseModel):
    """Enhanced task model for dashboard"""
    id: str
    plan_id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    
    # Assignment
    assignee: Optional[str] = None
    assignee_type: Literal["human", "codegen", "agent"] = "codegen"
    
    # Estimation and tracking
    estimated_hours: float = 0.0
    actual_hours: Optional[float] = None
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list)
    blocks: List[str] = Field(default_factory=list)
    
    # Integration IDs
    linear_issue_id: Optional[str] = None
    github_pr_id: Optional[str] = None
    codegen_task_id: Optional[str] = None
    
    # Quality gates
    quality_checks: List[str] = Field(default_factory=list)
    quality_status: QualityGateStatus = QualityGateStatus.PENDING
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardPlan(BaseModel):
    """Enhanced plan model for dashboard"""
    id: str
    project_id: str
    title: str
    description: str
    status: PlanStatus = PlanStatus.DRAFT
    
    # Tasks
    tasks: List[DashboardTask] = Field(default_factory=list)
    
    # Generation metadata
    generated_by: Literal["codegen", "manual"] = "codegen"
    codegen_prompt: Optional[str] = None
    codegen_response: Optional[Dict[str, Any]] = None
    
    # Progress tracking
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: float = 0.0
    
    # Estimation
    estimated_total_hours: float = 0.0
    actual_total_hours: float = 0.0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowEvent(BaseModel):
    """Workflow event model for tracking system events"""
    id: str
    project_id: str
    task_id: Optional[str] = None
    plan_id: Optional[str] = None
    
    # Event details
    event_type: str
    source: str  # github, linear, codegen, grainchain, etc.
    message: str
    
    # Event data
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Severity
    severity: Literal["info", "warning", "error", "success"] = "info"
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QualityGateResult(BaseModel):
    """Quality gate result model"""
    id: str
    project_id: str
    task_id: Optional[str] = None
    pr_id: Optional[str] = None
    
    # Gate details
    gate_type: str  # grainchain, graph_sitter, circleci, etc.
    gate_name: str
    status: QualityGateStatus
    
    # Results
    score: Optional[float] = None
    max_score: Optional[float] = None
    passed: bool = False
    
    # Details
    details: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    
    # Execution info
    execution_time: Optional[float] = None
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardSettings(BaseModel):
    """Dashboard settings model"""
    # API Keys and tokens
    github_token: Optional[str] = None
    linear_token: Optional[str] = None
    codegen_org_id: Optional[str] = None
    codegen_token: Optional[str] = None
    slack_token: Optional[str] = None
    
    # Database
    postgresql_url: Optional[str] = None
    
    # Feature flags
    auto_start_flows: bool = False
    enable_notifications: bool = True
    enable_analytics: bool = True
    enable_quality_gates: bool = True
    
    # Quality gate settings
    quality_gate_timeout: int = 300  # seconds
    auto_merge_on_quality_pass: bool = False
    
    # Workflow settings
    max_concurrent_tasks: int = 5
    task_timeout: int = 3600  # seconds
    
    # Notification settings
    slack_notifications: bool = False
    email_notifications: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardStats(BaseModel):
    """Dashboard statistics model"""
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    
    total_plans: int = 0
    active_plans: int = 0
    completed_plans: int = 0
    
    total_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    
    running_flows: int = 0
    quality_gates_passed: int = 0
    quality_gates_failed: int = 0
    
    average_project_progress: float = 0.0
    average_quality_score: float = 0.0
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

