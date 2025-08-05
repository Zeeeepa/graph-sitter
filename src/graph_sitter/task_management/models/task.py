"""
Core Task Model with JSONB metadata support
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task lifecycle status"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRYING = "retrying"


class TaskPriority(int, Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class TaskType(str, Enum):
    """Types of tasks that can be executed"""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    WORKFLOW = "workflow"
    CUSTOM = "custom"


class Task(BaseModel):
    """
    Core Task model with flexible metadata storage using JSONB-like structure
    
    Supports:
    - Task creation, assignment, and status tracking
    - Flexible metadata storage
    - Priority-based scheduling
    - Dependency tracking
    """
    
    # Core identifiers
    id: UUID = Field(default_factory=uuid4, description="Unique task identifier")
    name: str = Field(..., description="Human-readable task name")
    description: Optional[str] = Field(None, description="Detailed task description")
    
    # Task classification
    task_type: TaskType = Field(default=TaskType.CUSTOM, description="Type of task")
    tags: Set[str] = Field(default_factory=set, description="Task tags for categorization")
    
    # Status and lifecycle
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Task priority")
    
    # Assignment and ownership
    assigned_to: Optional[str] = Field(None, description="Agent or user assigned to task")
    created_by: str = Field(..., description="Creator of the task")
    
    # Dependencies
    depends_on: Set[UUID] = Field(default_factory=set, description="Task dependencies")
    blocks: Set[UUID] = Field(default_factory=set, description="Tasks blocked by this task")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    started_at: Optional[datetime] = Field(None, description="Actual start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    
    # Execution configuration
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_count: int = Field(default=0, description="Current retry count")
    timeout_seconds: Optional[int] = Field(None, description="Task timeout in seconds")
    
    # Flexible metadata storage (JSONB-like)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible task metadata")
    
    # Execution context
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="Context for task execution")
    
    # Results and output
    result: Optional[Dict[str, Any]] = Field(None, description="Task execution result")
    error_message: Optional[str] = Field(None, description="Error message if task failed")
    
    # Resource requirements
    resource_requirements: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Resource requirements (CPU, memory, etc.)"
    )
    
    # Workflow context
    workflow_id: Optional[UUID] = Field(None, description="Parent workflow ID")
    workflow_step_id: Optional[str] = Field(None, description="Step ID within workflow")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            set: lambda v: list(v),
        }
    
    def update_status(self, status: TaskStatus, message: Optional[str] = None) -> None:
        """Update task status with timestamp"""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if status == TaskStatus.RUNNING and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self.completed_at = datetime.utcnow()
        
        if message and status == TaskStatus.FAILED:
            self.error_message = message
    
    def add_dependency(self, task_id: UUID) -> None:
        """Add a task dependency"""
        self.depends_on.add(task_id)
        self.updated_at = datetime.utcnow()
    
    def remove_dependency(self, task_id: UUID) -> None:
        """Remove a task dependency"""
        self.depends_on.discard(task_id)
        self.updated_at = datetime.utcnow()
    
    def add_blocked_task(self, task_id: UUID) -> None:
        """Add a task that this task blocks"""
        self.blocks.add(task_id)
        self.updated_at = datetime.utcnow()
    
    def is_ready_to_run(self, completed_tasks: Set[UUID]) -> bool:
        """Check if task is ready to run based on dependencies"""
        if self.status != TaskStatus.PENDING:
            return False
        
        # All dependencies must be completed
        return self.depends_on.issubset(completed_tasks)
    
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return (
            self.status == TaskStatus.FAILED and 
            self.retry_count < self.max_retries
        )
    
    def increment_retry(self) -> None:
        """Increment retry count"""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()
    
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if not self.deadline:
            return False
        return datetime.utcnow() > self.deadline
    
    def get_duration(self) -> Optional[float]:
        """Get task execution duration in seconds"""
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        return cls.model_validate(data)

