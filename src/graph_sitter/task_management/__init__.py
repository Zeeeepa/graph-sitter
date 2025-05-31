"""
Task Management Engine for Graph-Sitter

This module provides comprehensive task management capabilities including:
- Task lifecycle management with dependencies
- Workflow orchestration and execution
- Resource monitoring and optimization
- Multi-agent task execution
- Real-time metrics and analytics

The system supports various task types and execution patterns:
- Code analysis tasks
- Code generation tasks
- Testing and validation tasks
- Deployment operations
- Custom workflow tasks
"""

from .core.models import (
    Task, TaskType, TaskStatus, TaskPriority,
    TaskExecution, ExecutionStatus,
    Workflow, WorkflowStep, WorkflowStatus,
    ResourceUsage, ExecutionLog
)

from .core.task_api import TaskAPI
from .core.task_factory import TaskFactory
from .core.workflow_builder import WorkflowBuilder
from .core.dependency_resolver import DependencyResolver
from .core.task_executor import TaskExecutor
from .core.task_scheduler import TaskScheduler
from .core.task_metrics import TaskMetrics
from .core.task_logger import TaskLogger

from .utils.conditions import WorkflowCondition, ConditionOperator

__all__ = [
    # Core models
    "Task", "TaskType", "TaskStatus", "TaskPriority",
    "TaskExecution", "ExecutionStatus", 
    "Workflow", "WorkflowStep", "WorkflowStatus",
    "ResourceUsage", "ExecutionLog",
    
    # Core components
    "TaskAPI", "TaskFactory", "WorkflowBuilder",
    "DependencyResolver", "TaskExecutor", "TaskScheduler",
    "TaskMetrics", "TaskLogger",
    
    # Utilities
    "WorkflowCondition", "ConditionOperator"
]

__version__ = "1.0.0"

