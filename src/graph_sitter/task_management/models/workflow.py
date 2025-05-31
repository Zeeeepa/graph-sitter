"""
Workflow models for complex workflow orchestration
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .task import Task, TaskStatus


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepType(str, Enum):
    """Types of workflow steps"""
    TASK = "task"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    WAIT = "wait"


class ConditionOperator(str, Enum):
    """Conditional operators for workflow steps"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    EXISTS = "exists"


class WorkflowCondition(BaseModel):
    """Condition for conditional workflow steps"""
    field: str = Field(..., description="Field to evaluate")
    operator: ConditionOperator = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")
    source: str = Field(default="result", description="Source of data (result, metadata, etc.)")


class WorkflowStep(BaseModel):
    """
    Individual step in a workflow
    
    Supports:
    - Task execution steps
    - Parallel and sequential processing
    - Conditional execution
    - Loop constructs
    """
    
    # Core identifiers
    id: str = Field(..., description="Unique step identifier within workflow")
    name: str = Field(..., description="Human-readable step name")
    description: Optional[str] = Field(None, description="Step description")
    
    # Step configuration
    step_type: StepType = Field(..., description="Type of workflow step")
    
    # Task reference (for TASK steps)
    task_template: Optional[Dict[str, Any]] = Field(None, description="Task template for TASK steps")
    task_id: Optional[UUID] = Field(None, description="Created task ID")
    
    # Parallel/Sequential steps (for PARALLEL/SEQUENTIAL steps)
    sub_steps: List["WorkflowStep"] = Field(default_factory=list, description="Sub-steps for parallel/sequential execution")
    
    # Conditional execution (for CONDITIONAL steps)
    condition: Optional[WorkflowCondition] = Field(None, description="Condition for conditional steps")
    true_steps: List["WorkflowStep"] = Field(default_factory=list, description="Steps to execute if condition is true")
    false_steps: List["WorkflowStep"] = Field(default_factory=list, description="Steps to execute if condition is false")
    
    # Loop configuration (for LOOP steps)
    loop_condition: Optional[WorkflowCondition] = Field(None, description="Loop continuation condition")
    loop_steps: List["WorkflowStep"] = Field(default_factory=list, description="Steps to execute in loop")
    max_iterations: int = Field(default=100, description="Maximum loop iterations")
    
    # Wait configuration (for WAIT steps)
    wait_seconds: Optional[int] = Field(None, description="Seconds to wait")
    wait_condition: Optional[WorkflowCondition] = Field(None, description="Condition to wait for")
    
    # Dependencies and ordering
    depends_on: Set[str] = Field(default_factory=set, description="Step dependencies")
    
    # Status and execution
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Step execution status")
    started_at: Optional[datetime] = Field(None, description="Step start time")
    completed_at: Optional[datetime] = Field(None, description="Step completion time")
    
    # Results and context
    result: Optional[Dict[str, Any]] = Field(None, description="Step execution result")
    error_message: Optional[str] = Field(None, description="Error message if step failed")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Step metadata")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            set: lambda v: list(v),
        }
    
    def is_ready_to_execute(self, completed_steps: Set[str]) -> bool:
        """Check if step is ready to execute based on dependencies"""
        if self.status != TaskStatus.PENDING:
            return False
        return self.depends_on.issubset(completed_steps)
    
    def start_execution(self) -> None:
        """Mark step as started"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete_execution(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark step as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if result:
            self.result = result
    
    def fail_execution(self, error_message: str) -> None:
        """Mark step as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message


class Workflow(BaseModel):
    """
    Complex workflow definition and execution
    
    Features:
    - Complex workflow definition and execution
    - Conditional task execution based on results
    - Parallel and sequential task processing
    - Workflow state persistence and recovery
    """
    
    # Core identifiers
    id: UUID = Field(default_factory=uuid4, description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    version: str = Field(default="1.0", description="Workflow version")
    
    # Workflow definition
    steps: List[WorkflowStep] = Field(..., description="Workflow steps")
    
    # Status and lifecycle
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    
    # Execution context
    context: Dict[str, Any] = Field(default_factory=dict, description="Workflow execution context")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Workflow variables")
    
    # Results and output
    result: Optional[Dict[str, Any]] = Field(None, description="Workflow execution result")
    error_message: Optional[str] = Field(None, description="Error message if workflow failed")
    
    # Configuration
    max_parallel_tasks: int = Field(default=10, description="Maximum parallel task execution")
    timeout_seconds: Optional[int] = Field(None, description="Workflow timeout")
    
    # Recovery and persistence
    checkpoint_data: Dict[str, Any] = Field(default_factory=dict, description="Checkpoint data for recovery")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Workflow metadata")
    tags: Set[str] = Field(default_factory=set, description="Workflow tags")
    
    # Ownership
    created_by: str = Field(..., description="Workflow creator")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            set: lambda v: list(v),
        }
    
    def start_workflow(self) -> None:
        """Start workflow execution"""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_workflow(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Complete workflow execution"""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if result:
            self.result = result
    
    def fail_workflow(self, error_message: str) -> None:
        """Fail workflow execution"""
        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error_message = error_message
    
    def pause_workflow(self) -> None:
        """Pause workflow execution"""
        self.status = WorkflowStatus.PAUSED
        self.updated_at = datetime.utcnow()
    
    def resume_workflow(self) -> None:
        """Resume workflow execution"""
        self.status = WorkflowStatus.RUNNING
        self.updated_at = datetime.utcnow()
    
    def cancel_workflow(self) -> None:
        """Cancel workflow execution"""
        self.status = WorkflowStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute"""
        completed_step_ids = {
            step.id for step in self.steps 
            if step.status == TaskStatus.COMPLETED
        }
        
        return [
            step for step in self.steps
            if step.is_ready_to_execute(completed_step_ids)
        ]
    
    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def update_step_status(self, step_id: str, status: TaskStatus, result: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> None:
        """Update step status"""
        step = self.get_step_by_id(step_id)
        if step:
            step.status = status
            if result:
                step.result = result
            if error_message:
                step.error_message = error_message
            self.updated_at = datetime.utcnow()
    
    def is_completed(self) -> bool:
        """Check if workflow is completed"""
        return all(step.status == TaskStatus.COMPLETED for step in self.steps)
    
    def has_failed_steps(self) -> bool:
        """Check if workflow has failed steps"""
        return any(step.status == TaskStatus.FAILED for step in self.steps)
    
    def get_progress_percentage(self) -> float:
        """Get workflow progress percentage"""
        if not self.steps:
            return 0.0
        
        completed_steps = sum(1 for step in self.steps if step.status == TaskStatus.COMPLETED)
        return (completed_steps / len(self.steps)) * 100.0
    
    def create_checkpoint(self) -> Dict[str, Any]:
        """Create checkpoint for workflow recovery"""
        checkpoint = {
            "workflow_id": str(self.id),
            "status": self.status,
            "step_statuses": {
                step.id: {
                    "status": step.status,
                    "result": step.result,
                    "error_message": step.error_message,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                }
                for step in self.steps
            },
            "context": self.context,
            "variables": self.variables,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.checkpoint_data = checkpoint
        return checkpoint
    
    def restore_from_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        """Restore workflow from checkpoint"""
        self.status = WorkflowStatus(checkpoint["status"])
        self.context = checkpoint.get("context", {})
        self.variables = checkpoint.get("variables", {})
        
        step_statuses = checkpoint.get("step_statuses", {})
        for step in self.steps:
            if step.id in step_statuses:
                step_data = step_statuses[step.id]
                step.status = TaskStatus(step_data["status"])
                step.result = step_data.get("result")
                step.error_message = step_data.get("error_message")
                if step_data.get("started_at"):
                    step.started_at = datetime.fromisoformat(step_data["started_at"])
                if step_data.get("completed_at"):
                    step.completed_at = datetime.fromisoformat(step_data["completed_at"])
        
        self.checkpoint_data = checkpoint
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create workflow from dictionary"""
        return cls.model_validate(data)


# Update forward references
WorkflowStep.model_rebuild()

