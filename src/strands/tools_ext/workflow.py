"""
Strands Workflow Tools

Advanced workflow management and execution for Strands agents.
Based on: https://github.com/strands-agents/tools/blob/main/src/strands_tools/workflow.py
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import json

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskStatus(Enum):
    """Individual task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class WorkflowTask:
    """Represents a single task in a workflow."""
    id: str
    name: str
    func: Callable[..., Any]
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution."""
    max_concurrent_tasks: int = 5
    default_task_timeout: float = 300.0  # 5 minutes
    enable_checkpoints: bool = True
    checkpoint_interval: float = 60.0  # 1 minute
    enable_recovery: bool = True
    max_workflow_retries: int = 3
    workflow_timeout: Optional[float] = None


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    task_results: Dict[str, Any] = field(default_factory=dict)
    task_errors: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Workflow:
    """Advanced workflow management system."""
    
    def __init__(self, 
                 workflow_id: str,
                 name: str,
                 config: Optional[WorkflowConfig] = None):
        """Initialize workflow.
        
        Args:
            workflow_id: Unique workflow identifier
            name: Human-readable workflow name
            config: Optional workflow configuration
        """
        self.workflow_id = workflow_id
        self.name = name
        self.config = config or WorkflowConfig()
        
        self.tasks: Dict[str, WorkflowTask] = {}
        self.task_graph: Dict[str, List[str]] = {}  # task_id -> dependent_task_ids
        self.status = WorkflowStatus.PENDING
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Execution state
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        
        # Checkpointing
        self.checkpoints: List[Dict[str, Any]] = []
        self.last_checkpoint_time: Optional[float] = None
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "task_started": [],
            "task_completed": [],
            "task_failed": [],
            "workflow_started": [],
            "workflow_completed": [],
            "workflow_failed": []
        }
        
        logger.info(f"Initialized workflow: {self.name} ({self.workflow_id})")
    
    def add_task(self, task: WorkflowTask) -> 'Workflow':
        """Add a task to the workflow.
        
        Args:
            task: Task to add
            
        Returns:
            Self for method chaining
        """
        self.tasks[task.id] = task
        self.task_graph[task.id] = []
        
        # Build dependency graph
        for dep_id in task.dependencies:
            if dep_id in self.task_graph:
                self.task_graph[dep_id].append(task.id)
        
        logger.debug(f"Added task: {task.name} ({task.id})")
        return self
    
    def create_task(self,
                   task_id: str,
                   name: str,
                   func: Callable[..., Any],
                   args: tuple = (),
                   kwargs: Optional[Dict[str, Any]] = None,
                   dependencies: Optional[List[str]] = None,
                   **task_kwargs) -> 'Workflow':
        """Create and add a task to the workflow.
        
        Args:
            task_id: Unique task identifier
            name: Human-readable task name
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            dependencies: List of task IDs this task depends on
            **task_kwargs: Additional task configuration
            
        Returns:
            Self for method chaining
        """
        task = WorkflowTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            dependencies=dependencies or [],
            **task_kwargs
        )
        
        return self.add_task(task)
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
            logger.debug(f"Added {event_type} handler")
    
    async def execute(self) -> WorkflowResult:
        """Execute the workflow.
        
        Returns:
            Workflow execution result
        """
        if self.status != WorkflowStatus.PENDING:
            raise RuntimeError(f"Workflow is not in pending state: {self.status}")
        
        logger.info(f"Starting workflow execution: {self.name}")
        
        self.status = WorkflowStatus.RUNNING
        self.start_time = time.time()
        
        # Emit workflow started event
        await self._emit_event("workflow_started", self)
        
        try:
            # Validate workflow
            self._validate_workflow()
            
            # Execute tasks
            await self._execute_tasks()
            
            # Check final status
            if self.failed_tasks:
                self.status = WorkflowStatus.FAILED
                await self._emit_event("workflow_failed", self)
            else:
                self.status = WorkflowStatus.COMPLETED
                await self._emit_event("workflow_completed", self)
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            logger.error(f"Workflow execution failed: {e}")
            await self._emit_event("workflow_failed", self)
            raise
        
        finally:
            self.end_time = time.time()
        
        return self._create_result()
    
    async def cancel(self):
        """Cancel workflow execution."""
        if self.status != WorkflowStatus.RUNNING:
            return
        
        logger.info(f"Cancelling workflow: {self.name}")
        
        self.status = WorkflowStatus.CANCELLED
        
        # Cancel running tasks
        for task_id, task_future in self.running_tasks.items():
            if not task_future.done():
                task_future.cancel()
                self.tasks[task_id].status = TaskStatus.SKIPPED
        
        self.end_time = time.time()
    
    async def pause(self):
        """Pause workflow execution."""
        if self.status != WorkflowStatus.RUNNING:
            return
        
        logger.info(f"Pausing workflow: {self.name}")
        self.status = WorkflowStatus.PAUSED
        
        # Create checkpoint
        await self._create_checkpoint()
    
    async def resume(self):
        """Resume workflow execution."""
        if self.status != WorkflowStatus.PAUSED:
            return
        
        logger.info(f"Resuming workflow: {self.name}")
        self.status = WorkflowStatus.RUNNING
        
        # Continue execution
        await self._execute_tasks()
    
    def _validate_workflow(self):
        """Validate workflow structure."""
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id):
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for dependent_id in self.task_graph.get(task_id, []):
                if dependent_id not in visited:
                    if has_cycle(dependent_id):
                        return True
                elif dependent_id in rec_stack:
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        for task_id in self.tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    raise ValueError("Circular dependency detected in workflow")
        
        # Check that all dependencies exist
        for task in self.tasks.values():
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    raise ValueError(f"Task {task.id} depends on non-existent task: {dep_id}")
    
    async def _execute_tasks(self):
        """Execute workflow tasks."""
        while self.status == WorkflowStatus.RUNNING:
            # Find ready tasks
            ready_tasks = self._get_ready_tasks()
            
            if not ready_tasks and not self.running_tasks:
                # No more tasks to run
                break
            
            # Start ready tasks (up to concurrency limit)
            available_slots = self.config.max_concurrent_tasks - len(self.running_tasks)
            tasks_to_start = ready_tasks[:available_slots]
            
            for task_id in tasks_to_start:
                await self._start_task(task_id)
            
            # Wait for at least one task to complete
            if self.running_tasks:
                done, pending = await asyncio.wait(
                    self.running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task_future in done:
                    await self._handle_task_completion(task_future)
            
            # Create checkpoint if needed
            if (self.config.enable_checkpoints and 
                self.last_checkpoint_time is None or 
                time.time() - self.last_checkpoint_time > self.config.checkpoint_interval):
                await self._create_checkpoint()
            
            # Small delay to prevent tight loop
            await asyncio.sleep(0.01)
    
    def _get_ready_tasks(self) -> List[str]:
        """Get tasks that are ready to execute.
        
        Returns:
            List of task IDs ready for execution
        """
        ready_tasks = []
        
        for task_id, task in self.tasks.items():
            if (task.status == TaskStatus.PENDING and
                task_id not in self.running_tasks and
                all(dep_id in self.completed_tasks for dep_id in task.dependencies)):
                ready_tasks.append(task_id)
        
        return ready_tasks
    
    async def _start_task(self, task_id: str):
        """Start executing a task.
        
        Args:
            task_id: ID of task to start
        """
        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.start_time = time.time()
        
        logger.debug(f"Starting task: {task.name} ({task_id})")
        
        # Create task future
        task_future = asyncio.create_task(self._execute_task(task))
        self.running_tasks[task_id] = task_future
        
        # Emit task started event
        await self._emit_event("task_started", task)
    
    async def _execute_task(self, task: WorkflowTask) -> Any:
        """Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        try:
            # Apply timeout
            timeout = task.timeout or self.config.default_task_timeout
            
            if asyncio.iscoroutinefunction(task.func):
                result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=timeout
                )
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, task.func, *task.args, **task.kwargs),
                    timeout=timeout
                )
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = time.time()
            
            return result
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            task.end_time = time.time()
            
            # Retry if configured
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                
                logger.warning(f"Task {task.name} failed, retrying ({task.retry_count}/{task.max_retries})")
                
                # Wait before retry
                await asyncio.sleep(task.retry_delay)
                
                # Reset for retry
                task.status = TaskStatus.PENDING
                task.error = None
                
                return await self._execute_task(task)
            
            raise
    
    async def _handle_task_completion(self, task_future: asyncio.Task):
        """Handle completion of a task.
        
        Args:
            task_future: Completed task future
        """
        # Find which task this future belongs to
        task_id = None
        for tid, future in self.running_tasks.items():
            if future == task_future:
                task_id = tid
                break
        
        if task_id is None:
            return
        
        task = self.tasks[task_id]
        
        # Remove from running tasks
        del self.running_tasks[task_id]
        
        try:
            result = await task_future
            self.completed_tasks.add(task_id)
            await self._emit_event("task_completed", task)
            logger.debug(f"Task completed: {task.name} ({task_id})")
            
        except Exception as e:
            self.failed_tasks.add(task_id)
            await self._emit_event("task_failed", task)
            logger.error(f"Task failed: {task.name} ({task_id}) - {e}")
    
    async def _create_checkpoint(self):
        """Create a workflow checkpoint."""
        if not self.config.enable_checkpoints:
            return
        
        checkpoint = {
            "timestamp": time.time(),
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "completed_tasks": list(self.completed_tasks),
            "failed_tasks": list(self.failed_tasks),
            "task_states": {
                task_id: {
                    "status": task.status.value,
                    "result": task.result,
                    "error": task.error,
                    "retry_count": task.retry_count
                }
                for task_id, task in self.tasks.items()
            }
        }
        
        self.checkpoints.append(checkpoint)
        self.last_checkpoint_time = time.time()
        
        logger.debug(f"Created checkpoint for workflow: {self.workflow_id}")
    
    async def _emit_event(self, event_type: str, data: Any):
        """Emit an event to handlers.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        for handler in self.event_handlers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    def _create_result(self) -> WorkflowResult:
        """Create workflow result.
        
        Returns:
            Workflow execution result
        """
        duration = None
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
        
        task_results = {}
        task_errors = {}
        
        for task_id, task in self.tasks.items():
            if task.result is not None:
                task_results[task_id] = task.result
            if task.error:
                task_errors[task_id] = task.error
        
        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=self.status,
            start_time=self.start_time or 0,
            end_time=self.end_time,
            duration=duration,
            task_results=task_results,
            task_errors=task_errors,
            metadata={
                "task_count": len(self.tasks),
                "completed_count": len(self.completed_tasks),
                "failed_count": len(self.failed_tasks),
                "checkpoints_count": len(self.checkpoints)
            }
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get workflow status.
        
        Returns:
            Status information
        """
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "task_count": len(self.tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "running_tasks": len(self.running_tasks),
            "checkpoints": len(self.checkpoints)
        }


class WorkflowBuilder:
    """Builder for creating workflows."""
    
    def __init__(self, name: str, workflow_id: Optional[str] = None):
        """Initialize workflow builder.
        
        Args:
            name: Workflow name
            workflow_id: Optional workflow ID (generated if not provided)
        """
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.name = name
        self.config = WorkflowConfig()
        self.tasks: List[WorkflowTask] = []
    
    def with_config(self, config: WorkflowConfig) -> 'WorkflowBuilder':
        """Set workflow configuration.
        
        Args:
            config: Workflow configuration
            
        Returns:
            Self for method chaining
        """
        self.config = config
        return self
    
    def add_task(self, 
                task_id: str,
                name: str,
                func: Callable[..., Any],
                args: tuple = (),
                kwargs: Optional[Dict[str, Any]] = None,
                dependencies: Optional[List[str]] = None,
                **task_kwargs) -> 'WorkflowBuilder':
        """Add a task to the workflow.
        
        Args:
            task_id: Unique task identifier
            name: Human-readable task name
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            dependencies: List of task IDs this task depends on
            **task_kwargs: Additional task configuration
            
        Returns:
            Self for method chaining
        """
        task = WorkflowTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            dependencies=dependencies or [],
            **task_kwargs
        )
        
        self.tasks.append(task)
        return self
    
    def build(self) -> Workflow:
        """Build the workflow.
        
        Returns:
            Configured workflow
        """
        workflow = Workflow(self.workflow_id, self.name, self.config)
        
        for task in self.tasks:
            workflow.add_task(task)
        
        return workflow

