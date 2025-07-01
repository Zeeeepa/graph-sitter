"""
Autogenlib - Enhanced Codegen SDK Integration

This module provides comprehensive integration with the Codegen SDK,
including client management, task orchestration, and batch processing.
"""

from .codegen_client import CodegenClient, TaskConfig, TaskResult, run_codegen_task
from .task_manager import TaskManager, ManagedTask, WorkflowDefinition, TaskStatus, TaskPriority
from .batch_processor import BatchProcessor, BatchConfig, BatchResult, BatchStatus

__version__ = "1.0.0"
__all__ = [
    # Client
    "CodegenClient",
    "TaskConfig", 
    "TaskResult",
    "run_codegen_task",
    
    # Task Management
    "TaskManager",
    "ManagedTask",
    "WorkflowDefinition", 
    "TaskStatus",
    "TaskPriority",
    
    # Batch Processing
    "BatchProcessor",
    "BatchConfig",
    "BatchResult", 
    "BatchStatus"
]

