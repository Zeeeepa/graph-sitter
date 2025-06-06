"""Data models for the dashboard extension."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel


class FlowStatus(str, Enum):
    """Flow execution status."""
    IDLE = "idle"
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Individual task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ServiceStatus(str, Enum):
    """Service connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class Project:
    """Project model for dashboard."""
    id: str
    name: str
    repo_url: str
    owner: str
    repo_name: str
    is_pinned: bool = False
    requirements: str = ""
    flow_status: FlowStatus = FlowStatus.IDLE
    progress_percentage: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "repo_url": self.repo_url,
            "owner": self.owner,
            "repo_name": self.repo_name,
            "is_pinned": self.is_pinned,
            "requirements": self.requirements,
            "flow_status": self.flow_status.value,
            "progress_percentage": self.progress_percentage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }


@dataclass
class Task:
    """Task model for flow execution."""
    id: str
    flow_id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assignee: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "flow_id": self.flow_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "assignee": self.assignee,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "result": self.result,
            "dependencies": self.dependencies
        }


@dataclass
class Flow:
    """Flow model for project execution."""
    id: str
    project_id: str
    name: str
    status: FlowStatus = FlowStatus.IDLE
    tasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
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
            "status": self.status.value,
            "tasks": [task.to_dict() for task in self.tasks],
            "progress_percentage": self.progress_percentage,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }


@dataclass
class UserSettings:
    """User settings for dashboard configuration."""
    github_token: Optional[str] = None
    linear_token: Optional[str] = None
    slack_token: Optional[str] = None
    codegen_org_id: Optional[str] = None
    codegen_token: Optional[str] = None
    database_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization (excluding sensitive data)."""
        return {
            "github_token": "***" if self.github_token else None,
            "linear_token": "***" if self.linear_token else None,
            "slack_token": "***" if self.slack_token else None,
            "codegen_org_id": self.codegen_org_id,
            "codegen_token": "***" if self.codegen_token else None,
            "database_url": "***" if self.database_url else None
        }


class ServiceStatusResponse(BaseModel):
    """Response model for service status."""
    github: ServiceStatus
    linear: ServiceStatus
    slack: ServiceStatus
    codegen: ServiceStatus
    database: ServiceStatus


class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    repo_url: str
    requirements: Optional[str] = ""


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""
    requirements: Optional[str] = None
    is_pinned: Optional[bool] = None


class FlowStartRequest(BaseModel):
    """Request model for starting a flow."""
    project_id: str
    requirements: str


class PlanGenerateRequest(BaseModel):
    """Request model for generating a plan."""
    project_id: str
    requirements: str

