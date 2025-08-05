"""
Core data models for the Task Management Engine

This module defines the fundamental data structures used throughout
the task management system, including tasks, executions, workflows,
and related entities.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator
import json


class TaskType(str, Enum):
    """Types of tasks supported by the system."""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    WORKFLOW = "workflow"
    CUSTOM = "custom"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRYING = "retrying"


class TaskPriority(int, Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class ExecutionStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ResourceUsage(BaseModel):
    """Resource usage metrics for task execution."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    disk_mb: float = 0.0
    network_kb: float = 0.0
    gpu_memory_mb: float = 0.0
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class ExecutionLog(BaseModel):
    """Log entry for task execution."""
    id: UUID = Field(default_factory=uuid4)
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    """Core task model with comprehensive metadata and execution tracking."""
    
    # Core identification
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    task_type: TaskType
    
    # Status and lifecycle
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Assignment and ownership
    created_by: str
    assigned_to: Optional[str] = None
    
    # Dependencies and relationships
    depends_on: Set[UUID] = Field(default_factory=set)
    blocks: Set[UUID] = Field(default_factory=set)
    parent_task_id: Optional[UUID] = None
    
    # Execution configuration
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)
    
    # Retry and timeout configuration
    max_retries: int = 0
    retry_count: int = 0
    timeout_seconds: Optional[int] = None
    
    # Results and error handling
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Tags and categorization
    tags: Set[str] = Field(default_factory=set)
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            set: list
        }
    
    def add_dependency(self, task_id: UUID) -> None:
        """Add a task dependency."""
        self.depends_on.add(task_id)
        self.updated_at = datetime.utcnow()
    
    def remove_dependency(self, task_id: UUID) -> None:
        """Remove a task dependency."""
        self.depends_on.discard(task_id)
        self.updated_at = datetime.utcnow()
    
    def can_retry(self) -> bool:
        """Check if the task can be retried."""
        return (self.status == TaskStatus.FAILED and 
                self.retry_count < self.max_retries)
    
    def increment_retry(self) -> None:
        """Increment the retry count."""
        self.retry_count += 1
        self.status = TaskStatus.RETRYING
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark the task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if result:
            self.result = result
    
    def mark_failed(self, error_message: str) -> None:
        """Mark the task as failed."""
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def get_duration(self) -> Optional[timedelta]:
        """Get the task execution duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class TaskExecution(BaseModel):
    """Task execution tracking with detailed metrics."""
    
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    executor_id: str
    
    # Execution status and timing
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Resource usage tracking
    resource_usage: Optional[ResourceUsage] = None
    
    # Results and logs
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List[ExecutionLog] = Field(default_factory=list)
    
    # Execution metadata
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
    
    def add_log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a log entry to the execution."""
        log_entry = ExecutionLog(
            level=level,
            message=message,
            metadata=metadata or {}
        )
        self.logs.append(log_entry)
    
    def get_duration(self) -> Optional[timedelta]:
        """Get the execution duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class WorkflowStep(BaseModel):
    """Individual step in a workflow."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    step_type: str  # task, parallel, sequential, conditional, loop, wait
    
    # Step configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # For task steps
    task_template: Optional[Dict[str, Any]] = None
    
    # For composite steps (parallel, sequential)
    sub_steps: List['WorkflowStep'] = Field(default_factory=list)
    
    # For conditional steps
    condition: Optional[Dict[str, Any]] = None
    true_steps: List['WorkflowStep'] = Field(default_factory=list)
    false_steps: List['WorkflowStep'] = Field(default_factory=list)
    
    # For loop steps
    loop_condition: Optional[Dict[str, Any]] = None
    loop_steps: List['WorkflowStep'] = Field(default_factory=list)
    max_iterations: int = 10
    
    # For wait steps
    wait_seconds: Optional[int] = None
    wait_condition: Optional[Dict[str, Any]] = None
    
    # Execution tracking
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# Forward reference resolution
WorkflowStep.model_rebuild()


class Workflow(BaseModel):
    """Workflow definition with steps and execution tracking."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    
    # Workflow structure
    steps: List[WorkflowStep] = Field(default_factory=list)
    
    # Execution state
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Workflow context and variables
    context: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    
    # Ownership and metadata
    created_by: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Results and error handling
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps.append(step)
    
    def get_duration(self) -> Optional[timedelta]:
        """Get the workflow execution duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class TaskCreateRequest(BaseModel):
    """Request model for creating a new task."""
    name: str
    description: Optional[str] = None
    task_type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    created_by: str
    assigned_to: Optional[str] = None
    depends_on: Set[UUID] = Field(default_factory=set)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = 0
    timeout_seconds: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    tags: Set[str] = Field(default_factory=set)


class TaskUpdateRequest(BaseModel):
    """Request model for updating a task."""
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_context: Optional[Dict[str, Any]] = None
    resource_requirements: Optional[Dict[str, Any]] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    tags: Optional[Set[str]] = None


class TaskResponse(BaseModel):
    """Response model for task operations."""
    id: UUID
    name: str
    description: Optional[str]
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    created_by: str
    assigned_to: Optional[str]
    depends_on: Set[UUID]
    metadata: Dict[str, Any]
    tags: Set[str]
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            set: list
        }

