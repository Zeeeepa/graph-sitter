"""
Core models for the task management system.

This module defines the core data models for tasks, workflows, and execution tracking.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskType(str, Enum):
    """Types of tasks that can be executed."""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    WORKFLOW = "workflow"
    CUSTOM = "custom"


class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class WorkflowStepType(str, Enum):
    """Types of workflow steps."""
    ANALYSIS = "analysis"
    QUALITY_GATE = "quality_gate"
    TESTING = "testing"
    BUILD = "build"
    DEPLOYMENT = "deployment"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


class Task(BaseModel):
    """Core task model with execution tracking."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: TaskType = TaskType.CUSTOM
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.NORMAL
    
    # Execution details
    created_by: UUID
    assigned_to: Optional[UUID] = None
    organization_id: UUID
    
    # Scheduling
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Configuration and results
    configuration: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Retry logic
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    
    # Dependencies
    depends_on: List[UUID] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        """Ensure scheduled_at is not in the past."""
        if v and v < datetime.utcnow():
            raise ValueError("scheduled_at cannot be in the past")
        return v
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate task execution duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def is_ready(self) -> bool:
        """Check if task is ready to execute."""
        return (
            self.status == TaskStatus.PENDING and
            (self.scheduled_at is None or self.scheduled_at <= datetime.utcnow())
        )
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return (
            self.status == TaskStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def mark_started(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if result:
            self.result = result
    
    def mark_failed(self, error_message: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def schedule_retry(self) -> None:
        """Schedule task for retry."""
        if self.can_retry:
            self.retry_count += 1
            self.status = TaskStatus.PENDING
            self.scheduled_at = datetime.utcnow() + timedelta(seconds=self.retry_delay * (2 ** self.retry_count))
            self.error_message = None
            self.updated_at = datetime.utcnow()


class WorkflowStep(BaseModel):
    """Individual step in a workflow."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    step_type: WorkflowStepType = WorkflowStepType.CUSTOM
    order: int = Field(..., ge=0)
    
    # Configuration
    configuration: Dict[str, Any] = Field(default_factory=dict)
    
    # Dependencies within workflow
    depends_on_steps: List[UUID] = Field(default_factory=list)
    
    # Conditional execution
    condition: Optional[str] = None  # Expression to evaluate
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 30
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Workflow(BaseModel):
    """Workflow definition with multiple steps."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Steps
    steps: List[WorkflowStep] = Field(default_factory=list)
    
    # Execution details
    created_by: UUID
    organization_id: UUID
    
    # Configuration
    configuration: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('steps')
    def validate_steps_order(cls, v):
        """Ensure steps have unique orders."""
        orders = [step.order for step in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Workflow steps must have unique order values")
        return v
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        # Auto-assign order if not set
        if not hasattr(step, 'order') or step.order is None:
            step.order = len(self.steps)
        
        self.steps.append(step)
        self.steps.sort(key=lambda s: s.order)
        self.updated_at = datetime.utcnow()
    
    def get_ready_steps(self, completed_steps: List[UUID]) -> List[WorkflowStep]:
        """Get steps that are ready to execute."""
        ready_steps = []
        for step in self.steps:
            # Check if all dependencies are completed
            if all(dep_id in completed_steps for dep_id in step.depends_on_steps):
                ready_steps.append(step)
        return ready_steps


class TaskExecution(BaseModel):
    """Detailed execution tracking for tasks."""
    
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    execution_number: int = 1
    
    # Execution details
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Resource usage
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    disk_usage_mb: Optional[float] = None
    
    # Results and logs
    result: Optional[Dict[str, Any]] = None
    logs: List[str] = Field(default_factory=list)
    error_details: Optional[Dict[str, Any]] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate execution duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def add_log(self, message: str) -> None:
        """Add a log message."""
        timestamp = datetime.utcnow().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
        self.updated_at = datetime.utcnow()


class TaskDependency(BaseModel):
    """Task dependency relationship."""
    
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    depends_on_task_id: UUID
    dependency_type: str = "completion"  # completion, success, failure
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('dependency_type')
    def validate_dependency_type(cls, v):
        """Validate dependency type."""
        valid_types = ["completion", "success", "failure"]
        if v not in valid_types:
            raise ValueError(f"dependency_type must be one of {valid_types}")
        return v


# Factory functions for common task types
class TaskFactory:
    """Factory for creating common task types."""
    
    @staticmethod
    def create_code_analysis_task(
        name: str,
        repository_url: str,
        created_by: UUID,
        organization_id: UUID,
        analysis_type: str = "comprehensive",
        **kwargs
    ) -> Task:
        """Create a code analysis task."""
        configuration = {
            "repository_url": repository_url,
            "analysis_type": analysis_type,
            **kwargs.get("configuration", {})
        }
        
        return Task(
            name=name,
            task_type=TaskType.CODE_ANALYSIS,
            configuration=configuration,
            created_by=created_by,
            organization_id=organization_id,
            **{k: v for k, v in kwargs.items() if k != "configuration"}
        )
    
    @staticmethod
    def create_code_generation_task(
        name: str,
        prompt: str,
        target_language: str,
        created_by: UUID,
        organization_id: UUID,
        **kwargs
    ) -> Task:
        """Create a code generation task."""
        configuration = {
            "prompt": prompt,
            "target_language": target_language,
            **kwargs.get("configuration", {})
        }
        
        return Task(
            name=name,
            task_type=TaskType.CODE_GENERATION,
            configuration=configuration,
            created_by=created_by,
            organization_id=organization_id,
            **{k: v for k, v in kwargs.items() if k != "configuration"}
        )
    
    @staticmethod
    def create_workflow_task(
        name: str,
        workflow: Workflow,
        created_by: UUID,
        organization_id: UUID,
        **kwargs
    ) -> Task:
        """Create a workflow execution task."""
        configuration = {
            "workflow_id": str(workflow.id),
            "workflow_steps": len(workflow.steps),
            **kwargs.get("configuration", {})
        }
        
        return Task(
            name=name,
            task_type=TaskType.WORKFLOW,
            configuration=configuration,
            created_by=created_by,
            organization_id=organization_id,
            **{k: v for k, v in kwargs.items() if k != "configuration"}
        )
