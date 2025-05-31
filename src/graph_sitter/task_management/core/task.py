"""
Core Task Definition and Management

Defines the fundamental Task class and related enums for the task management system.
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class TaskStatus(Enum):
    """Task execution status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class TaskType(Enum):
    """Types of tasks supported by the system."""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REFACTORING = "code_refactoring"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    INTEGRATION_TASK = "integration_task"
    EVALUATION_TASK = "evaluation_task"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CUSTOM = "custom"


@dataclass
class TaskMetadata:
    """Metadata associated with a task."""
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: Set[str] = field(default_factory=set)
    labels: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDependency:
    """Represents a dependency between tasks."""
    task_id: str
    dependency_type: str = "completion"  # completion, data, resource
    condition: Optional[str] = None


@dataclass
class TaskResource:
    """Resource requirements for task execution."""
    cpu_cores: Optional[int] = None
    memory_mb: Optional[int] = None
    gpu_required: bool = False
    disk_space_mb: Optional[int] = None
    network_bandwidth: Optional[str] = None
    custom_resources: Dict[str, Any] = field(default_factory=dict)


class Task(BaseModel):
    """
    Core Task class representing a unit of work in the task management system.
    
    This class encapsulates all information needed to define, schedule, execute,
    and monitor a task within the advanced task management system.
    """
    
    # Core identification
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    task_type: TaskType
    
    # Status and lifecycle
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # Timing and scheduling
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    estimated_duration: Optional[timedelta] = None
    
    # Dependencies and relationships
    dependencies: List[TaskDependency] = Field(default_factory=list)
    parent_task_id: Optional[str] = None
    child_task_ids: List[str] = Field(default_factory=list)
    
    # Execution configuration
    max_retries: int = 3
    retry_count: int = 0
    timeout: Optional[timedelta] = None
    resource_requirements: TaskResource = Field(default_factory=TaskResource)
    
    # Task payload and results
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None
    
    # Metadata and context
    metadata: TaskMetadata = Field(default_factory=lambda: TaskMetadata(created_by="system"))
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Integration-specific fields
    codegen_agent_id: Optional[str] = None
    graph_sitter_config: Dict[str, Any] = Field(default_factory=dict)
    contexten_workflow_id: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            timedelta: lambda v: v.total_seconds(),
        }
    
    def add_dependency(self, task_id: str, dependency_type: str = "completion", condition: Optional[str] = None) -> None:
        """Add a dependency to this task."""
        dependency = TaskDependency(
            task_id=task_id,
            dependency_type=dependency_type,
            condition=condition
        )
        self.dependencies.append(dependency)
        self.updated_at = datetime.utcnow()
    
    def remove_dependency(self, task_id: str) -> bool:
        """Remove a dependency from this task."""
        original_count = len(self.dependencies)
        self.dependencies = [dep for dep in self.dependencies if dep.task_id != task_id]
        if len(self.dependencies) < original_count:
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def update_status(self, new_status: TaskStatus, error_info: Optional[Dict[str, Any]] = None) -> None:
        """Update the task status with appropriate timestamp tracking."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Update lifecycle timestamps
        if new_status == TaskStatus.RUNNING and old_status != TaskStatus.RUNNING:
            self.started_at = self.updated_at
        elif new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self.completed_at = self.updated_at
        
        # Handle error information
        if error_info:
            self.error_info = error_info
        elif new_status == TaskStatus.COMPLETED:
            self.error_info = None
    
    def can_execute(self, available_tasks: Set[str]) -> bool:
        """Check if this task can be executed based on its dependencies."""
        if self.status != TaskStatus.PENDING:
            return False
        
        # Check if all dependencies are satisfied
        for dependency in self.dependencies:
            if dependency.task_id not in available_tasks:
                return False
        
        # Check if scheduled time has arrived
        if self.scheduled_at and self.scheduled_at > datetime.utcnow():
            return False
        
        return True
    
    def is_overdue(self) -> bool:
        """Check if the task is overdue based on its deadline."""
        if not self.deadline:
            return False
        return datetime.utcnow() > self.deadline
    
    def get_execution_duration(self) -> Optional[timedelta]:
        """Get the actual execution duration if the task has completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def should_retry(self) -> bool:
        """Determine if the task should be retried after failure."""
        return (
            self.status == TaskStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def increment_retry(self) -> None:
        """Increment the retry counter and update status."""
        self.retry_count += 1
        self.update_status(TaskStatus.RETRYING)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the task metadata."""
        self.metadata.tags.add(tag)
        self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the task metadata."""
        if tag in self.metadata.tags:
            self.metadata.tags.remove(tag)
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def set_label(self, key: str, value: str) -> None:
        """Set a label in the task metadata."""
        self.metadata.labels[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_label(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a label value from the task metadata."""
        return self.metadata.labels.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary representation."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a task instance from a dictionary."""
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation of the task."""
        return f"Task(id={self.id[:8]}, name='{self.name}', status={self.status.value}, priority={self.priority.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the task."""
        return (
            f"Task(id='{self.id}', name='{self.name}', type={self.task_type.value}, "
            f"status={self.status.value}, priority={self.priority.value}, "
            f"created_at={self.created_at.isoformat()})"
        )

