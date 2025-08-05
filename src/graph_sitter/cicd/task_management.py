"""
Task Management System for Graph-Sitter CI/CD

Provides comprehensive task management with:
- Hierarchical task structure
- Dependency resolution
- Status tracking and execution
- Integration with Codegen SDK
- Performance monitoring
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Task types for categorization"""
    FEATURE = "feature"
    BUG = "bug"
    REFACTOR = "refactor"
    TEST = "test"
    DOCS = "docs"
    CI_CD = "ci_cd"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"


@dataclass
class Task:
    """Task definition with metadata and execution tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    task_type: TaskType = TaskType.FEATURE
    priority: int = 3  # 1=highest, 5=lowest
    status: TaskStatus = TaskStatus.PENDING
    
    # Relationships
    organization_id: str = ""
    project_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    
    # Timing
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Execution context
    metadata: Dict[str, Any] = field(default_factory=dict)
    codegen_task_id: Optional[str] = None
    
    def update_status(self, status: TaskStatus) -> None:
        """Update task status with timestamp"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc)
        if status == TaskStatus.COMPLETED:
            self.completed_at = datetime.now(timezone.utc)
    
    def add_dependency(self, task_id: str) -> None:
        """Add a task dependency"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
    
    def remove_dependency(self, task_id: str) -> None:
        """Remove a task dependency"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
    
    def is_ready_to_execute(self, completed_tasks: Set[str]) -> bool:
        """Check if all dependencies are completed"""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)


@dataclass
class TaskExecution:
    """Task execution tracking and results"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    codegen_execution_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    logs: str = ""
    
    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def start_execution(self) -> None:
        """Mark execution as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)
    
    def complete_execution(self, result: Dict[str, Any], metrics: Dict[str, Any] = None) -> None:
        """Mark execution as completed with results"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.result = result
        if metrics:
            self.metrics.update(metrics)
    
    def fail_execution(self, error_message: str) -> None:
        """Mark execution as failed with error"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message


class TaskManager:
    """
    Comprehensive task management system with dependency resolution,
    execution tracking, and integration with Codegen SDK
    """
    
    def __init__(self, organization_id: str, database_connection=None):
        self.organization_id = organization_id
        self.db = database_connection
        self.tasks: Dict[str, Task] = {}
        self.executions: Dict[str, TaskExecution] = {}
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.running_tasks: Set[str] = set()
        self.completed_tasks: Set[str] = set()
        
    async def create_task(self, task: Task) -> str:
        """Create a new task"""
        task.organization_id = self.organization_id
        self.tasks[task.id] = task
        
        # Store in database if available
        if self.db:
            await self._store_task_in_db(task)
        
        logger.info(f"Created task {task.id}: {task.title}")
        return task.id
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.now(timezone.utc)
        
        # Update in database if available
        if self.db:
            await self._update_task_in_db(task)
        
        logger.info(f"Updated task {task_id}")
        return True
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    async def list_tasks(self, 
                        project_id: Optional[str] = None,
                        status: Optional[TaskStatus] = None,
                        assigned_to: Optional[str] = None) -> List[Task]:
        """List tasks with optional filters"""
        tasks = list(self.tasks.values())
        
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]
        
        return tasks
    
    async def execute_task(self, task_id: str, executor_func=None) -> TaskExecution:
        """Execute a task with optional custom executor"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        
        # Check if dependencies are satisfied
        if not task.is_ready_to_execute(self.completed_tasks):
            raise ValueError(f"Task {task_id} dependencies not satisfied")
        
        # Create execution record
        execution = TaskExecution(task_id=task_id)
        self.executions[execution.id] = execution
        
        # Start execution
        execution.start_execution()
        task.update_status(TaskStatus.IN_PROGRESS)
        self.running_tasks.add(task_id)
        
        try:
            # Execute task (use custom executor or default)
            if executor_func:
                result = await executor_func(task)
            else:
                result = await self._default_task_executor(task)
            
            # Complete execution
            execution.complete_execution(result)
            task.update_status(TaskStatus.COMPLETED)
            self.completed_tasks.add(task_id)
            
            logger.info(f"Completed task {task_id}")
            
        except Exception as e:
            # Handle execution failure
            execution.fail_execution(str(e))
            task.update_status(TaskStatus.FAILED)
            logger.error(f"Failed to execute task {task_id}: {e}")
            
        finally:
            self.running_tasks.discard(task_id)
            
            # Store execution in database
            if self.db:
                await self._store_execution_in_db(execution)
        
        return execution
    
    async def resolve_dependencies(self, task_id: str) -> List[str]:
        """Get the execution order for a task and its dependencies"""
        if task_id not in self.tasks:
            return []
        
        visited = set()
        execution_order = []
        
        def dfs(current_task_id: str):
            if current_task_id in visited:
                return
            
            visited.add(current_task_id)
            task = self.tasks.get(current_task_id)
            
            if task:
                # Visit dependencies first
                for dep_id in task.dependencies:
                    if dep_id in self.tasks:
                        dfs(dep_id)
                
                execution_order.append(current_task_id)
        
        dfs(task_id)
        return execution_order
    
    async def execute_workflow(self, task_ids: List[str], parallel: bool = False) -> Dict[str, TaskExecution]:
        """Execute multiple tasks with dependency resolution"""
        executions = {}
        
        if parallel:
            # Execute tasks in parallel where possible
            tasks = []
            for task_id in task_ids:
                if task_id in self.tasks:
                    tasks.append(self.execute_task(task_id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, TaskExecution):
                    executions[task_ids[i]] = result
        else:
            # Execute tasks sequentially with dependency resolution
            for task_id in task_ids:
                execution_order = await self.resolve_dependencies(task_id)
                for exec_task_id in execution_order:
                    if exec_task_id not in executions:
                        execution = await self.execute_task(exec_task_id)
                        executions[exec_task_id] = execution
        
        return executions
    
    async def get_task_metrics(self, task_id: str) -> Dict[str, Any]:
        """Get performance metrics for a task"""
        task = self.tasks.get(task_id)
        if not task:
            return {}
        
        executions = [e for e in self.executions.values() if e.task_id == task_id]
        
        if not executions:
            return {"task_id": task_id, "execution_count": 0}
        
        # Calculate metrics
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == TaskStatus.COMPLETED])
        failed_executions = len([e for e in executions if e.status == TaskStatus.FAILED])
        
        # Calculate average execution time
        completed_executions = [e for e in executions if e.completed_at and e.started_at]
        avg_execution_time = 0
        if completed_executions:
            total_time = sum((e.completed_at - e.started_at).total_seconds() for e in completed_executions)
            avg_execution_time = total_time / len(completed_executions)
        
        return {
            "task_id": task_id,
            "execution_count": total_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "failure_rate": failed_executions / total_executions if total_executions > 0 else 0,
            "average_execution_time_seconds": avg_execution_time,
            "last_execution": max(executions, key=lambda e: e.started_at or datetime.min).id if executions else None
        }
    
    async def _default_task_executor(self, task: Task) -> Dict[str, Any]:
        """Default task executor - can be overridden"""
        # Simulate task execution
        await asyncio.sleep(0.1)
        
        return {
            "status": "completed",
            "message": f"Task {task.title} executed successfully",
            "execution_time": 0.1
        }
    
    async def _store_task_in_db(self, task: Task) -> None:
        """Store task in database"""
        # Implementation would depend on database connection
        pass
    
    async def _update_task_in_db(self, task: Task) -> None:
        """Update task in database"""
        # Implementation would depend on database connection
        pass
    
    async def _store_execution_in_db(self, execution: TaskExecution) -> None:
        """Store task execution in database"""
        # Implementation would depend on database connection
        pass


# Utility functions for task management
def create_task_from_dict(data: Dict[str, Any]) -> Task:
    """Create a Task object from dictionary data"""
    task = Task()
    for key, value in data.items():
        if hasattr(task, key):
            if key == "task_type" and isinstance(value, str):
                task.task_type = TaskType(value)
            elif key == "status" and isinstance(value, str):
                task.status = TaskStatus(value)
            else:
                setattr(task, key, value)
    return task


def validate_task_dependencies(tasks: Dict[str, Task]) -> List[str]:
    """Validate task dependencies for circular references"""
    errors = []
    
    def has_cycle(task_id: str, visited: Set[str], rec_stack: Set[str]) -> bool:
        visited.add(task_id)
        rec_stack.add(task_id)
        
        task = tasks.get(task_id)
        if task:
            for dep_id in task.dependencies:
                if dep_id not in visited:
                    if has_cycle(dep_id, visited, rec_stack):
                        return True
                elif dep_id in rec_stack:
                    return True
        
        rec_stack.remove(task_id)
        return False
    
    visited = set()
    for task_id in tasks:
        if task_id not in visited:
            if has_cycle(task_id, visited, set()):
                errors.append(f"Circular dependency detected involving task {task_id}")
    
    return errors

