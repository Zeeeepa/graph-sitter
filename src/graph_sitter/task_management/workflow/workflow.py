"""
Core Workflow Definition and Management

Defines the fundamental workflow structures and management capabilities
for complex task orchestration.
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from ..core.task import Task, TaskType, TaskPriority, TaskStatus


class WorkflowStatus(Enum):
    """Workflow execution status."""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(Enum):
    """Types of workflow steps."""
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    LOOP = "loop"
    WAIT = "wait"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class ConditionOperator(Enum):
    """Operators for workflow conditions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    EXISTS = "exists"
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class WorkflowCondition:
    """Represents a condition for workflow execution."""
    field: str
    operator: ConditionOperator
    value: Any
    description: Optional[str] = None
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against the given context."""
        field_value = self._get_field_value(context, self.field)
        
        if self.operator == ConditionOperator.EQUALS:
            return field_value == self.value
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == ConditionOperator.GREATER_THAN:
            return field_value > self.value
        elif self.operator == ConditionOperator.LESS_THAN:
            return field_value < self.value
        elif self.operator == ConditionOperator.CONTAINS:
            return self.value in field_value if field_value else False
        elif self.operator == ConditionOperator.EXISTS:
            return field_value is not None
        else:
            return False
    
    def _get_field_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """Get a nested field value from context using dot notation."""
        keys = field_path.split('.')
        value = context
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value


class WorkflowStep(BaseModel):
    """Represents a single step in a workflow."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    step_type: StepType
    description: Optional[str] = None
    
    # Task configuration (for TASK steps)
    task_type: Optional[TaskType] = None
    task_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Condition configuration (for CONDITION steps)
    condition: Optional[WorkflowCondition] = None
    true_path: List[str] = Field(default_factory=list)  # Step IDs to execute if true
    false_path: List[str] = Field(default_factory=list)  # Step IDs to execute if false
    
    # Parallel/Sequential configuration
    child_steps: List[str] = Field(default_factory=list)  # Child step IDs
    
    # Loop configuration
    loop_condition: Optional[WorkflowCondition] = None
    max_iterations: Optional[int] = None
    
    # Wait configuration
    wait_duration: Optional[timedelta] = None
    wait_condition: Optional[WorkflowCondition] = None
    
    # Dependencies and flow control
    depends_on: List[str] = Field(default_factory=list)  # Step IDs this step depends on
    timeout: Optional[timedelta] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Execution state
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_info: Optional[Dict[str, Any]] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    tags: Set[str] = Field(default_factory=set)
    labels: Dict[str, str] = Field(default_factory=dict)
    
    def can_execute(self, completed_steps: Set[str], context: Dict[str, Any]) -> bool:
        """Check if this step can be executed."""
        # Check dependencies
        if not all(dep in completed_steps for dep in self.depends_on):
            return False
        
        # Check condition if it's a conditional step
        if self.condition and not self.condition.evaluate(context):
            return False
        
        return True
    
    def create_task(self, workflow_context: Dict[str, Any]) -> Optional[Task]:
        """Create a task from this workflow step."""
        if self.step_type != StepType.TASK or not self.task_type:
            return None
        
        # Merge workflow context with step configuration
        input_data = {**workflow_context, **self.task_config}
        
        task = Task(
            name=f"{self.name} (Workflow Step)",
            task_type=self.task_type,
            description=self.description,
            input_data=input_data,
            timeout=self.timeout,
        )
        
        # Add workflow metadata
        task.metadata.labels["workflow_step_id"] = self.id
        task.metadata.labels["step_name"] = self.name
        
        return task


class Workflow(BaseModel):
    """
    Represents a complete workflow with steps, dependencies, and execution logic.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Workflow structure
    steps: Dict[str, WorkflowStep] = Field(default_factory=dict)
    entry_points: List[str] = Field(default_factory=list)  # Step IDs to start with
    
    # Execution configuration
    max_parallel_steps: int = 10
    timeout: Optional[timedelta] = None
    retry_failed_steps: bool = True
    
    # State and lifecycle
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Execution context and results
    context: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None
    
    # Metadata
    tags: Set[str] = Field(default_factory=set)
    labels: Dict[str, str] = Field(default_factory=dict)
    created_by: str = "system"
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            timedelta: lambda v: v.total_seconds(),
        }
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps[step.id] = step
        self.updated_at = datetime.utcnow()
    
    def remove_step(self, step_id: str) -> bool:
        """Remove a step from the workflow."""
        if step_id in self.steps:
            del self.steps[step_id]
            
            # Remove from entry points
            if step_id in self.entry_points:
                self.entry_points.remove(step_id)
            
            # Remove dependencies on this step
            for step in self.steps.values():
                if step_id in step.depends_on:
                    step.depends_on.remove(step_id)
                if step_id in step.child_steps:
                    step.child_steps.remove(step_id)
                if step_id in step.true_path:
                    step.true_path.remove(step_id)
                if step_id in step.false_path:
                    step.false_path.remove(step_id)
            
            self.updated_at = datetime.utcnow()
            return True
        
        return False
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID."""
        return self.steps.get(step_id)
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute."""
        completed_steps = {
            step_id for step_id, step in self.steps.items()
            if step.status == TaskStatus.COMPLETED
        }
        
        ready_steps = []
        for step in self.steps.values():
            if (step.status == TaskStatus.PENDING and 
                step.can_execute(completed_steps, self.context)):
                ready_steps.append(step)
        
        return ready_steps
    
    def get_running_steps(self) -> List[WorkflowStep]:
        """Get currently running steps."""
        return [step for step in self.steps.values() if step.status == TaskStatus.RUNNING]
    
    def get_failed_steps(self) -> List[WorkflowStep]:
        """Get failed steps."""
        return [step for step in self.steps.values() if step.status == TaskStatus.FAILED]
    
    def is_complete(self) -> bool:
        """Check if the workflow is complete."""
        if not self.steps:
            return True
        
        # All steps must be completed or some terminal status
        terminal_statuses = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
        return all(step.status in terminal_statuses for step in self.steps.values())
    
    def is_failed(self) -> bool:
        """Check if the workflow has failed."""
        # Workflow fails if any critical step fails and retry is not enabled
        failed_steps = self.get_failed_steps()
        if not failed_steps:
            return False
        
        # Check if any failed step can be retried
        if self.retry_failed_steps:
            for step in failed_steps:
                if step.retry_count < step.max_retries:
                    return False  # Can still retry
        
        return True
    
    def update_status(self, new_status: WorkflowStatus) -> None:
        """Update the workflow status."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Update lifecycle timestamps
        if new_status == WorkflowStatus.RUNNING and old_status != WorkflowStatus.RUNNING:
            self.started_at = self.updated_at
        elif new_status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            self.completed_at = self.updated_at
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the workflow execution context."""
        self.context.update(updates)
        self.updated_at = datetime.utcnow()
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of workflow execution."""
        step_counts = {
            "total": len(self.steps),
            "pending": len([s for s in self.steps.values() if s.status == TaskStatus.PENDING]),
            "running": len([s for s in self.steps.values() if s.status == TaskStatus.RUNNING]),
            "completed": len([s for s in self.steps.values() if s.status == TaskStatus.COMPLETED]),
            "failed": len([s for s in self.steps.values() if s.status == TaskStatus.FAILED]),
            "cancelled": len([s for s in self.steps.values() if s.status == TaskStatus.CANCELLED]),
        }
        
        duration = None
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            duration = (end_time - self.started_at).total_seconds()
        
        return {
            "workflow_id": self.id,
            "name": self.name,
            "status": self.status.value,
            "step_counts": step_counts,
            "duration_seconds": duration,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def validate_workflow(self) -> List[str]:
        """Validate the workflow structure and return any errors."""
        errors = []
        
        # Check for entry points
        if not self.entry_points:
            errors.append("Workflow must have at least one entry point")
        
        # Check that entry points exist
        for entry_id in self.entry_points:
            if entry_id not in self.steps:
                errors.append(f"Entry point step '{entry_id}' does not exist")
        
        # Check step dependencies
        for step_id, step in self.steps.items():
            for dep_id in step.depends_on:
                if dep_id not in self.steps:
                    errors.append(f"Step '{step_id}' depends on non-existent step '{dep_id}'")
        
        # Check for circular dependencies
        if self._has_circular_dependencies():
            errors.append("Workflow contains circular dependencies")
        
        # Validate step configurations
        for step_id, step in self.steps.items():
            step_errors = self._validate_step(step)
            errors.extend([f"Step '{step_id}': {error}" for error in step_errors])
        
        return errors
    
    def _has_circular_dependencies(self) -> bool:
        """Check for circular dependencies in the workflow."""
        def has_cycle(step_id: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = self.steps.get(step_id)
            if step:
                for dep_id in step.depends_on:
                    if dep_id not in visited:
                        if has_cycle(dep_id, visited, rec_stack):
                            return True
                    elif dep_id in rec_stack:
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        visited = set()
        for step_id in self.steps:
            if step_id not in visited:
                if has_cycle(step_id, visited, set()):
                    return True
        
        return False
    
    def _validate_step(self, step: WorkflowStep) -> List[str]:
        """Validate a single workflow step."""
        errors = []
        
        if step.step_type == StepType.TASK:
            if not step.task_type:
                errors.append("Task step must have a task_type")
        
        elif step.step_type == StepType.CONDITION:
            if not step.condition:
                errors.append("Condition step must have a condition")
        
        elif step.step_type == StepType.PARALLEL:
            if not step.child_steps:
                errors.append("Parallel step must have child steps")
        
        elif step.step_type == StepType.SEQUENTIAL:
            if not step.child_steps:
                errors.append("Sequential step must have child steps")
        
        elif step.step_type == StepType.LOOP:
            if not step.loop_condition and not step.max_iterations:
                errors.append("Loop step must have either a condition or max iterations")
        
        elif step.step_type == StepType.WAIT:
            if not step.wait_duration and not step.wait_condition:
                errors.append("Wait step must have either a duration or condition")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create workflow from dictionary."""
        return cls(**data)
    
    def clone(self, new_name: Optional[str] = None) -> "Workflow":
        """Create a copy of this workflow."""
        workflow_data = self.to_dict()
        
        # Generate new IDs
        workflow_data["id"] = str(uuid.uuid4())
        if new_name:
            workflow_data["name"] = new_name
        
        # Reset state
        workflow_data["status"] = WorkflowStatus.DRAFT.value
        workflow_data["created_at"] = datetime.utcnow().isoformat()
        workflow_data["updated_at"] = datetime.utcnow().isoformat()
        workflow_data["started_at"] = None
        workflow_data["completed_at"] = None
        workflow_data["results"] = {}
        workflow_data["error_info"] = None
        
        # Reset step states
        for step_data in workflow_data["steps"].values():
            step_data["status"] = TaskStatus.PENDING.value
            step_data["started_at"] = None
            step_data["completed_at"] = None
            step_data["error_info"] = None
            step_data["output_data"] = {}
            step_data["retry_count"] = 0
        
        return cls.from_dict(workflow_data)

