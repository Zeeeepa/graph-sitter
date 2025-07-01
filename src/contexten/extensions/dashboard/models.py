"""
Data models for the Dashboard extension.

This module defines the core data structures used throughout the dashboard system
for project management, workflow orchestration, and progress tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    ERROR = "error"


class FlowStatus(str, Enum):
    """Workflow flow status enumeration."""
    ON = "on"
    OFF = "off"
    PAUSED = "paused"
    ERROR = "error"


class WorkflowStatus(str, Enum):
    """Workflow execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class QualityGateStatus(str, Enum):
    """Quality gate status enumeration."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PRStatus(str, Enum):
    """Pull request status enumeration."""
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"
    DRAFT = "draft"


@dataclass
class Project:
    """Project data model."""
    id: str
    name: str
    full_name: str  # owner/repo format
    description: Optional[str] = None
    url: str = ""
    default_branch: str = "main"
    language: Optional[str] = None
    status: ProjectStatus = ProjectStatus.INACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectPin:
    """Project pin data model for dashboard."""
    id: str
    project_id: str
    user_id: str
    position: int = 0
    flow_status: FlowStatus = FlowStatus.OFF
    pinned_at: datetime = field(default_factory=datetime.utcnow)
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectSettings:
    """Project-specific settings and configuration."""
    project_id: str
    github_enabled: bool = True
    linear_enabled: bool = True
    slack_enabled: bool = True
    codegen_enabled: bool = True
    auto_pr_creation: bool = True
    auto_issue_creation: bool = True
    quality_gates_enabled: bool = True
    notification_preferences: Dict[str, bool] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowPlan:
    """Workflow plan generated from requirements."""
    id: str
    project_id: str
    title: str
    description: str
    requirements: str
    generated_plan: Dict[str, Any]
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    estimated_duration: Optional[int] = None  # in hours
    complexity_score: float = 0.0
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowTask:
    """Individual task within a workflow plan."""
    id: str
    plan_id: str
    title: str
    description: str
    task_type: str  # 'code', 'review', 'test', 'deploy', etc.
    dependencies: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: int = 1  # 1-5 scale
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    github_pr_url: Optional[str] = None
    linear_issue_id: Optional[str] = None
    codegen_task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Workflow execution tracking."""
    id: str
    plan_id: str
    execution_layer: str  # 'prefect', 'controlflow', 'mcp'
    status: WorkflowStatus = WorkflowStatus.PENDING
    progress_percentage: float = 0.0
    current_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_logs: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityGate:
    """Quality gate for code validation."""
    id: str
    task_id: str
    gate_type: str  # 'code_analysis', 'test_coverage', 'security_scan', etc.
    status: QualityGateStatus = QualityGateStatus.PENDING
    score: Optional[float] = None
    threshold: float = 0.8
    issues_found: List[Dict[str, Any]] = field(default_factory=list)
    auto_fix_applied: bool = False
    manual_review_required: bool = False
    executed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PRInfo:
    """Pull request information."""
    id: str
    project_id: str
    task_id: Optional[str] = None
    pr_number: int = 0
    title: str = ""
    description: str = ""
    status: PRStatus = PRStatus.OPEN
    url: str = ""
    branch_name: str = ""
    base_branch: str = "main"
    author: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    merged_at: Optional[datetime] = None
    quality_gates: List[QualityGate] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventLog:
    """Event log for tracking dashboard activities."""
    id: str
    project_id: str
    event_type: str
    event_source: str  # 'github', 'linear', 'slack', 'codegen', 'dashboard'
    event_data: Dict[str, Any]
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Pydantic models for API requests/responses
class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""
    name: str = Field(..., description="Project name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: Optional[str] = Field(None, description="Project description")
    url: str = Field(..., description="Repository URL")
    default_branch: str = Field("main", description="Default branch name")
    language: Optional[str] = Field(None, description="Primary programming language")


class ProjectPinRequest(BaseModel):
    """Request model for pinning a project."""
    project_id: str = Field(..., description="Project ID to pin")
    position: int = Field(0, description="Position in the dashboard")


class WorkflowPlanRequest(BaseModel):
    """Request model for creating a workflow plan."""
    project_id: str = Field(..., description="Project ID")
    title: str = Field(..., description="Plan title")
    description: str = Field(..., description="Plan description")
    requirements: str = Field(..., description="Requirements text for plan generation")


class SettingsUpdateRequest(BaseModel):
    """Request model for updating project settings."""
    github_enabled: Optional[bool] = None
    linear_enabled: Optional[bool] = None
    slack_enabled: Optional[bool] = None
    codegen_enabled: Optional[bool] = None
    auto_pr_creation: Optional[bool] = None
    auto_issue_creation: Optional[bool] = None
    quality_gates_enabled: Optional[bool] = None
    notification_preferences: Optional[Dict[str, bool]] = None
    custom_settings: Optional[Dict[str, Any]] = None


class EnvironmentVariablesRequest(BaseModel):
    """Request model for updating environment variables."""
    github_token: Optional[str] = Field(None, description="GitHub access token")
    linear_api_key: Optional[str] = Field(None, description="Linear API key")
    slack_token: Optional[str] = Field(None, description="Slack bot token")
    codegen_org_id: Optional[str] = Field(None, description="Codegen organization ID")
    codegen_token: Optional[str] = Field(None, description="Codegen API token")
    postgresql_url: Optional[str] = Field(None, description="PostgreSQL connection URL")


class DashboardResponse(BaseModel):
    """Base response model for dashboard API."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field("", description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    errors: Optional[List[str]] = Field(None, description="Error messages")

