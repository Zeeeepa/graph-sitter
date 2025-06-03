"""
Task Manager for automated task orchestration and workflow management.

This module provides comprehensive task management capabilities including
scheduling, dependency resolution, and workflow automation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import defaultdict, deque

from .codegen_client import CodegenClient, TaskConfig, TaskResult

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 3
    NORMAL = 5
    LOW = 7
    BACKGROUND = 9


@dataclass
class ManagedTask:
    """Enhanced task with management metadata."""
    id: str
    config: TaskConfig
    status: TaskStatus = TaskStatus.PENDING
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None
    retry_count: int = 0
    max_retries: int = 3
    error_history: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Definition of a workflow with multiple tasks."""
    id: str
    name: str
    description: str
    tasks: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class TaskManager:
    """
    Comprehensive task manager for automated task orchestration.
    
    Features:
    - Task scheduling and dependency resolution
    - Workflow management
    - Retry logic and error handling
    - Concurrent execution with limits
    - Progress tracking and monitoring
    """
    
    def __init__(self, codegen_client: CodegenClient, max_concurrent_tasks: int = 5):
        """
        Initialize the task manager.
        
        Args:
            codegen_client: Configured CodegenClient instance
            max_concurrent_tasks: Maximum number of concurrent tasks
        """
        self.client = codegen_client
        self.max_concurrent_tasks = max_concurrent_tasks
        
        self.tasks: Dict[str, ManagedTask] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.running_tasks: Set[str] = set()
        self.task_queue: deque = deque()
        
        self._shutdown_event = asyncio.Event()
        self._executor_task: Optional[asyncio.Task] = None
        
        # Event handlers
        self.task_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        logger.info(f"TaskManager initialized with max_concurrent_tasks={max_concurrent_tasks}")
    
    async def start(self):
        """Start the task manager executor."""
        if self._executor_task is None or self._executor_task.done():
            self._shutdown_event.clear()
            self._executor_task = asyncio.create_task(self._executor_loop())
            logger.info("TaskManager executor started")
    
    async def stop(self):
        """Stop the task manager executor."""
        self._shutdown_event.set()
        if self._executor_task:
            await self._executor_task
        logger.info("TaskManager executor stopped")
    
    def add_task(self, task_id: str, config: TaskConfig, 
                 dependencies: Optional[List[str]] = None,
                 scheduled_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> ManagedTask:
        """
        Add a new task to the manager.
        
        Args:
            task_id: Unique task identifier
            config: Task configuration
            dependencies: List of task IDs this task depends on
            scheduled_at: Optional scheduled execution time
            metadata: Additional task metadata
            
        Returns:
            ManagedTask instance
        """
        if task_id in self.tasks:
            raise ValueError(f"Task {task_id} already exists")
        
        task = ManagedTask(
            id=task_id,
            config=config,
            dependencies=set(dependencies or []),
            scheduled_at=scheduled_at,
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        
        # Update dependent tasks
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                self.tasks[dep_id].dependents.add(task_id)
        
        # Check if task is ready to run
        self._update_task_status(task_id)
        
        logger.info(f"Added task {task_id} with {len(task.dependencies)} dependencies")
        return task
    
    def add_workflow(self, workflow: WorkflowDefinition) -> List[str]:
        """
        Add a workflow with multiple tasks.
        
        Args:
            workflow: Workflow definition
            
        Returns:
            List of created task IDs
        """
        self.workflows[workflow.id] = workflow
        created_task_ids = []
        
        # Create tasks from workflow definition
        for task_def in workflow.tasks:
            task_id = f"{workflow.id}_{task_def['id']}"
            config = TaskConfig(
                prompt=task_def['prompt'],
                context=task_def.get('context', {}),
                priority=task_def.get('priority', 5),
                timeout=task_def.get('timeout', 300),
                metadata=task_def.get('metadata', {})
            )
            
            dependencies = workflow.dependencies.get(task_def['id'], [])
            # Convert relative task IDs to absolute task IDs
            abs_dependencies = [f"{workflow.id}_{dep}" for dep in dependencies]
            
            task = self.add_task(
                task_id=task_id,
                config=config,
                dependencies=abs_dependencies,
                metadata={'workflow_id': workflow.id, **config.metadata}
            )
            created_task_ids.append(task_id)
        
        logger.info(f"Added workflow {workflow.id} with {len(created_task_ids)} tasks")
        return created_task_ids
    
    def get_task(self, task_id: str) -> Optional[ManagedTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_workflow_tasks(self, workflow_id: str) -> List[ManagedTask]:
        """Get all tasks belonging to a workflow."""
        return [
            task for task in self.tasks.values()
            if task.metadata.get('workflow_id') == workflow_id
        ]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[ManagedTask]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks.values() if task.status == status]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            True if cancelled successfully
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING, TaskStatus.READY, TaskStatus.BLOCKED]:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            self._emit_event('task_cancelled', task)
            logger.info(f"Task {task_id} cancelled")
            return True
        
        return False
    
    def cancel_workflow(self, workflow_id: str) -> int:
        """
        Cancel all tasks in a workflow.
        
        Args:
            workflow_id: ID of workflow to cancel
            
        Returns:
            Number of tasks cancelled
        """
        workflow_tasks = self.get_workflow_tasks(workflow_id)
        cancelled_count = 0
        
        for task in workflow_tasks:
            if self.cancel_task(task.id):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} tasks in workflow {workflow_id}")
        return cancelled_count
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler for task events."""
        self.task_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: str, task: ManagedTask):
        """Emit a task event to registered handlers."""
        for handler in self.task_handlers[event_type]:
            try:
                handler(task)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    def _update_task_status(self, task_id: str):
        """Update task status based on dependencies and scheduling."""
        task = self.tasks.get(task_id)
        if not task or task.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED, 
                                       TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return
        
        # Check if all dependencies are completed
        dependencies_completed = all(
            self.tasks.get(dep_id, ManagedTask("", TaskConfig(""))).status == TaskStatus.COMPLETED
            for dep_id in task.dependencies
        )
        
        # Check if any dependency failed
        dependencies_failed = any(
            self.tasks.get(dep_id, ManagedTask("", TaskConfig(""))).status == TaskStatus.FAILED
            for dep_id in task.dependencies
        )
        
        if dependencies_failed:
            task.status = TaskStatus.BLOCKED
        elif dependencies_completed:
            # Check scheduling
            if task.scheduled_at is None or task.scheduled_at <= datetime.now():
                task.status = TaskStatus.READY
                if task_id not in [t for t in self.task_queue]:
                    self.task_queue.append(task_id)
            else:
                task.status = TaskStatus.PENDING
        else:
            task.status = TaskStatus.BLOCKED
    
    async def _executor_loop(self):
        """Main executor loop for processing tasks."""
        logger.info("Task executor loop started")
        
        while not self._shutdown_event.is_set():
            try:
                # Update task statuses
                for task_id in list(self.tasks.keys()):
                    self._update_task_status(task_id)
                
                # Process ready tasks
                while (len(self.running_tasks) < self.max_concurrent_tasks and 
                       self.task_queue and not self._shutdown_event.is_set()):
                    
                    task_id = self.task_queue.popleft()
                    task = self.tasks.get(task_id)
                    
                    if task and task.status == TaskStatus.READY:
                        asyncio.create_task(self._execute_task(task))
                
                # Wait before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in executor loop: {e}")
                await asyncio.sleep(5)
        
        logger.info("Task executor loop stopped")
    
    async def _execute_task(self, task: ManagedTask):
        """Execute a single task."""
        task_id = task.id
        self.running_tasks.add(task_id)
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        self._emit_event('task_started', task)
        logger.info(f"Executing task {task_id}")
        
        try:
            # Execute the task using the Codegen client
            result = await self.client.run_task(task.config)
            
            if result.status == "completed":
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.now()
                self._emit_event('task_completed', task)
                logger.info(f"Task {task_id} completed successfully")
                
                # Update dependent tasks
                for dependent_id in task.dependents:
                    self._update_task_status(dependent_id)
                    
            else:
                raise Exception(result.error or "Task failed")
                
        except Exception as e:
            error_msg = str(e)
            task.error_history.append(error_msg)
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.READY
                self.task_queue.append(task_id)
                logger.warning(f"Task {task_id} failed, retrying ({task.retry_count}/{task.max_retries}): {error_msg}")
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                self._emit_event('task_failed', task)
                logger.error(f"Task {task_id} failed permanently: {error_msg}")
        
        finally:
            self.running_tasks.discard(task_id)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of task manager status."""
        status_counts = defaultdict(int)
        for task in self.tasks.values():
            status_counts[task.status.value] += 1
        
        return {
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "queued_tasks": len(self.task_queue),
            "workflows": len(self.workflows),
            "status_breakdown": dict(status_counts),
            "max_concurrent_tasks": self.max_concurrent_tasks
        }


# Example workflow definitions
def create_code_analysis_workflow(repository_url: str, branch: str = "main") -> WorkflowDefinition:
    """Create a workflow for comprehensive code analysis."""
    return WorkflowDefinition(
        id=f"code_analysis_{hash(repository_url) % 10000}",
        name="Code Analysis Workflow",
        description=f"Comprehensive analysis of {repository_url}",
        tasks=[
            {
                "id": "checkout",
                "prompt": f"Checkout repository {repository_url} on branch {branch}",
                "context": {"repository_url": repository_url, "branch": branch},
                "priority": 5
            },
            {
                "id": "analyze_structure",
                "prompt": "Analyze the codebase structure and generate a summary",
                "context": {"analysis_type": "structure"},
                "priority": 5
            },
            {
                "id": "analyze_quality",
                "prompt": "Analyze code quality metrics and identify issues",
                "context": {"analysis_type": "quality"},
                "priority": 5
            },
            {
                "id": "generate_report",
                "prompt": "Generate a comprehensive analysis report",
                "context": {"analysis_type": "report"},
                "priority": 3
            }
        ],
        dependencies={
            "analyze_structure": ["checkout"],
            "analyze_quality": ["checkout"],
            "generate_report": ["analyze_structure", "analyze_quality"]
        }
    )


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the TaskManager."""
        from .codegen_client import CodegenClient
        
        # Initialize client and manager
        client = CodegenClient("example-org", "example-token")
        manager = TaskManager(client, max_concurrent_tasks=3)
        
        # Add event handlers
        def on_task_completed(task: ManagedTask):
            print(f"Task {task.id} completed!")
        
        manager.add_event_handler('task_completed', on_task_completed)
        
        # Start the manager
        await manager.start()
        
        # Add a workflow
        workflow = create_code_analysis_workflow("https://github.com/example/repo")
        task_ids = manager.add_workflow(workflow)
        
        # Wait for completion
        await asyncio.sleep(10)
        
        # Get status
        status = manager.get_status_summary()
        print(f"Manager status: {status}")
        
        # Stop the manager
        await manager.stop()
    
    asyncio.run(example_usage())

