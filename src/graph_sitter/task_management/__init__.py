"""
Task Management Module

This module provides comprehensive task management capabilities including:
- Task creation, execution, and lifecycle management
- Workflow orchestration and step execution
- Dependency resolution and circular dependency detection
- Resource monitoring and performance tracking
- Retry logic with exponential backoff
"""

from .core.models import (
    # Core models
    Task,
    TaskExecution,
    TaskDependency,
    Workflow,
    WorkflowStep,
    
    # Enums
    TaskStatus,
    TaskType,
    Priority,
    WorkflowStepType,
    
    # Factory
    TaskFactory
)

__all__ = [
    # Core models
    'Task',
    'TaskExecution', 
    'TaskDependency',
    'Workflow',
    'WorkflowStep',
    
    # Enums
    'TaskStatus',
    'TaskType',
    'Priority',
    'WorkflowStepType',
    
    # Factory
    'TaskFactory'
]

__version__ = '1.0.0'

