"""
Task Manager for Autogenlib
Automated task creation and execution management
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from .codegen_client import CodegenClient, CodegenConfig

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class Task:
    """Task definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    prompt: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """
    Advanced task management system for Autogenlib
    
    Provides:
    - Task queue management with priorities
    - Dependency resolution
    - Concurrent execution
    - Retry logic and error handling
    - Task scheduling and automation
    - Performance monitoring
    """
    
    def __init__(self, codegen_client: CodegenClient, max_concurrent_tasks: int = 10):
        self.codegen_client = codegen_client
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.is_running = False
        self.task_handlers: Dict[str, Callable] = {}
        
        # Performance metrics
        self.metrics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        
        logger.info("Task Manager initialized")
    
    async def start(self):
        """Start the task manager"""
        if self.is_running:
            logger.warning("Task Manager is already running")
            return
        
        self.is_running = True
        
        # Start task processor
        asyncio.create_task(self._process_task_queue())
        
        logger.info("Task Manager started")
    
    async def stop(self):
        """Stop the task manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel running tasks
        for task_id, task in self.running_tasks.items():
            task.cancel()
            logger.info(f"Cancelled task: {task_id}")
        
        self.running_tasks.clear()
        
        logger.info("Task Manager stopped")
    
    def create_task(
        self,
        name: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_seconds: int = 300,
        max_retries: int = 3,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new task
        
        Args:
            name: Task name
            prompt: Codegen prompt
            context: Optional context for prompt enhancement
            priority: Task priority
            timeout_seconds: Task timeout
            max_retries: Maximum retry attempts
            dependencies: List of task IDs this task depends on
            tags: Task tags for categorization
            metadata: Additional task metadata
        
        Returns:
            Task ID
        """
        task = Task(
            name=name,
            prompt=prompt,
            context=context or {},
            priority=priority,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            dependencies=dependencies or [],
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.tasks[task.id] = task
        self.metrics["total_tasks"] += 1
        
        logger.info(f"Created task: {task.id} - {name}")
        return task.id
    
    async def submit_task(self, task_id: str) -> bool:
        """
        Submit a task for execution
        
        Args:
            task_id: Task ID to submit
        
        Returns:
            True if task was submitted successfully
        """
        if task_id not in self.tasks:
            logger.error(f"Task not found: {task_id}")
            return False
        
        task = self.tasks[task_id]
        
        # Check dependencies
        if not self._are_dependencies_satisfied(task):
            logger.warning(f"Dependencies not satisfied for task: {task_id}")
            return False
        
        # Add to queue with priority
        priority_value = -task.priority.value  # Negative for high priority first
        await self.task_queue.put((priority_value, task.created_at, task_id))
        
        logger.info(f"Submitted task to queue: {task_id}")
        return True
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a task immediately (bypassing queue)
        
        Args:
            task_id: Task ID to execute
        
        Returns:
            Task execution result
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        
        # Check dependencies
        if not self._are_dependencies_satisfied(task):
            raise RuntimeError(f"Dependencies not satisfied for task: {task_id}")
        
        return await self._execute_single_task(task)
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for a task to complete
        
        Args:
            task_id: Task ID to wait for
            timeout: Optional timeout in seconds
        
        Returns:
            Task result
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        start_time = datetime.now()
        
        while task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
            
            await asyncio.sleep(0.1)
        
        if task.status == TaskStatus.COMPLETED:
            return task.result
        elif task.status == TaskStatus.FAILED:
            raise RuntimeError(f"Task failed: {task.error}")
        else:
            raise RuntimeError(f"Task was cancelled: {task_id}")
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task
        
        Args:
            task_id: Task ID to cancel
        
        Returns:
            True if task was cancelled successfully
        """
        if task_id not in self.tasks:
            logger.error(f"Task not found: {task_id}")
            return False
        
        task = self.tasks[task_id]
        
        # Cancel if running
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        logger.info(f"Cancelled task: {task_id}")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""
        if task_id not in self.tasks:
            return None
        return self.tasks[task_id].status
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result"""
        if task_id not in self.tasks:
            return None
        return self.tasks[task_id].result
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering
        
        Args:
            status: Filter by task status
            tags: Filter by tags (tasks must have all specified tags)
        
        Returns:
            List of task information
        """
        filtered_tasks = []
        
        for task in self.tasks.values():
            # Filter by status
            if status and task.status != status:
                continue
            
            # Filter by tags
            if tags and not all(tag in task.tags for tag in tags):
                continue
            
            filtered_tasks.append({
                "id": task.id,
                "name": task.name,
                "status": task.status.value,
                "priority": task.priority.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "tags": task.tags,
                "dependencies": task.dependencies
            })
        
        return filtered_tasks
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get task manager metrics"""
        return {
            **self.metrics,
            "queue_size": self.task_queue.qsize(),
            "running_tasks": len(self.running_tasks),
            "total_tasks_in_system": len(self.tasks),
            "success_rate": (
                self.metrics["completed_tasks"] / max(self.metrics["total_tasks"], 1)
            ) * 100,
            "failure_rate": (
                self.metrics["failed_tasks"] / max(self.metrics["total_tasks"], 1)
            ) * 100,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_task_queue(self):
        """Process tasks from the queue"""
        while self.is_running:
            try:
                # Wait for available slot
                while len(self.running_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                
                # Get next task from queue
                try:
                    priority, created_at, task_id = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Execute task
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    self.running_tasks[task_id] = asyncio.create_task(
                        self._execute_single_task(task)
                    )
                
            except Exception as e:
                logger.error(f"Error in task queue processor: {e}")
    
    async def _execute_single_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task"""
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            logger.info(f"Executing task: {task.id} - {task.name}")
            
            # Execute with Codegen client
            result = await self.codegen_client.generate_code(
                prompt=task.prompt,
                context=task.context,
                timeout_seconds=task.timeout_seconds
            )
            
            # Update task with result
            if result.get("status") == "success":
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.now()
                
                # Update metrics
                self.metrics["completed_tasks"] += 1
                self.completed_tasks.append(task.id)
                
                execution_time = (task.completed_at - task.started_at).total_seconds()
                self.metrics["total_execution_time"] += execution_time
                self.metrics["average_execution_time"] = (
                    self.metrics["total_execution_time"] / self.metrics["completed_tasks"]
                )
                
                logger.info(f"Task completed: {task.id}")
            else:
                raise RuntimeError(result.get("error", "Unknown error"))
            
            return result
            
        except Exception as e:
            # Handle task failure
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count <= task.max_retries:
                # Retry task
                logger.warning(f"Task failed, retrying ({task.retry_count}/{task.max_retries}): {task.id}")
                await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
                return await self._execute_single_task(task)
            else:
                # Mark as failed
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                
                # Update metrics
                self.metrics["failed_tasks"] += 1
                self.failed_tasks.append(task.id)
                
                logger.error(f"Task failed permanently: {task.id} - {e}")
                
                return {
                    "status": "failed",
                    "error": str(e),
                    "task_id": task.id,
                    "retry_count": task.retry_count
                }
        
        finally:
            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    def _are_dependencies_satisfied(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                logger.warning(f"Dependency task not found: {dep_id}")
                return False
            
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """Register a custom task handler"""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered task handler: {task_type}")
    
    async def create_and_submit_task(
        self,
        name: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs
    ) -> str:
        """Create and immediately submit a task"""
        task_id = self.create_task(name, prompt, context, priority, **kwargs)
        await self.submit_task(task_id)
        return task_id
    
    async def execute_batch_tasks(
        self,
        tasks: List[Dict[str, Any]],
        wait_for_completion: bool = True
    ) -> List[str]:
        """
        Execute multiple tasks as a batch
        
        Args:
            tasks: List of task definitions
            wait_for_completion: Whether to wait for all tasks to complete
        
        Returns:
            List of task IDs
        """
        task_ids = []
        
        # Create and submit all tasks
        for task_def in tasks:
            task_id = await self.create_and_submit_task(**task_def)
            task_ids.append(task_id)
        
        # Wait for completion if requested
        if wait_for_completion:
            for task_id in task_ids:
                try:
                    await self.wait_for_task(task_id)
                except Exception as e:
                    logger.error(f"Batch task failed: {task_id} - {e}")
        
        return task_ids

