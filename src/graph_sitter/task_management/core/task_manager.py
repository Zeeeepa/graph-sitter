"""
Core Task Manager Implementation

The TaskManager is the central orchestrator for all task-related operations,
providing a unified interface for task creation, scheduling, execution, and monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, Union
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, Future
import threading

from .task import Task, TaskStatus, TaskPriority, TaskType
from .scheduler import TaskScheduler, SchedulingStrategy
from .executor import TaskExecutor, ExecutionContext
from .monitor import TaskMonitor, MonitoringMetrics


logger = logging.getLogger(__name__)


class TaskManagerConfig:
    """Configuration for the TaskManager."""
    
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        default_timeout: timedelta = timedelta(hours=1),
        cleanup_interval: timedelta = timedelta(minutes=5),
        max_completed_tasks_history: int = 1000,
        enable_performance_monitoring: bool = True,
        enable_auto_retry: bool = True,
        scheduling_strategy: SchedulingStrategy = SchedulingStrategy.PRIORITY_FIRST,
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = default_timeout
        self.cleanup_interval = cleanup_interval
        self.max_completed_tasks_history = max_completed_tasks_history
        self.enable_performance_monitoring = enable_performance_monitoring
        self.enable_auto_retry = enable_auto_retry
        self.scheduling_strategy = scheduling_strategy


class TaskManager:
    """
    Advanced Task Manager for orchestrating task execution and lifecycle management.
    
    The TaskManager provides comprehensive task management capabilities including:
    - Task creation and lifecycle management
    - Dependency resolution and scheduling
    - Concurrent execution with resource management
    - Performance monitoring and optimization
    - Integration with external systems
    """
    
    def __init__(self, config: Optional[TaskManagerConfig] = None):
        """Initialize the TaskManager with the given configuration."""
        self.config = config or TaskManagerConfig()
        
        # Core components
        self.scheduler = TaskScheduler(self.config.scheduling_strategy)
        self.executor = TaskExecutor(max_workers=self.config.max_concurrent_tasks)
        self.monitor = TaskMonitor() if self.config.enable_performance_monitoring else None
        
        # Task storage and tracking
        self._tasks: Dict[str, Task] = {}
        self._running_tasks: Dict[str, Future] = {}
        self._completed_tasks: List[Task] = []
        self._task_handlers: Dict[TaskType, Callable] = {}
        
        # Synchronization
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        
        # Background services
        self._cleanup_thread: Optional[threading.Thread] = None
        self._start_background_services()
        
        logger.info(f"TaskManager initialized with config: {self.config.__dict__}")
    
    def _start_background_services(self) -> None:
        """Start background services for cleanup and monitoring."""
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True,
            name="TaskManager-Cleanup"
        )
        self._cleanup_thread.start()
    
    def _cleanup_worker(self) -> None:
        """Background worker for periodic cleanup tasks."""
        while not self._shutdown_event.is_set():
            try:
                self._cleanup_completed_tasks()
                self._check_timeouts()
                self._retry_failed_tasks()
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
            
            # Wait for cleanup interval or shutdown
            self._shutdown_event.wait(self.config.cleanup_interval.total_seconds())
    
    def register_task_handler(self, task_type: TaskType, handler: Callable[[Task], Any]) -> None:
        """Register a handler function for a specific task type."""
        with self._lock:
            self._task_handlers[task_type] = handler
            logger.info(f"Registered handler for task type: {task_type.value}")
    
    def create_task(
        self,
        name: str,
        task_type: TaskType,
        description: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        input_data: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        scheduled_at: Optional[datetime] = None,
        deadline: Optional[datetime] = None,
        timeout: Optional[timedelta] = None,
        **kwargs
    ) -> Task:
        """
        Create a new task and add it to the management system.
        
        Args:
            name: Human-readable name for the task
            task_type: Type of task to create
            description: Optional description of the task
            priority: Task priority level
            input_data: Input data for task execution
            dependencies: List of task IDs this task depends on
            scheduled_at: When to schedule the task for execution
            deadline: When the task must be completed by
            timeout: Maximum execution time for the task
            **kwargs: Additional task configuration
        
        Returns:
            The created Task instance
        """
        task = Task(
            name=name,
            task_type=task_type,
            description=description,
            priority=priority,
            input_data=input_data or {},
            scheduled_at=scheduled_at,
            deadline=deadline,
            timeout=timeout or self.config.default_timeout,
            **kwargs
        )
        
        # Add dependencies
        if dependencies:
            for dep_id in dependencies:
                task.add_dependency(dep_id)
        
        with self._lock:
            self._tasks[task.id] = task
            
        logger.info(f"Created task: {task}")
        
        # Schedule the task if it's ready
        if task.can_execute(set(self._get_completed_task_ids())):
            self.schedule_task(task.id)
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by its ID."""
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[TaskPriority] = None,
        tags: Optional[Set[str]] = None
    ) -> List[Task]:
        """
        Retrieve tasks based on filtering criteria.
        
        Args:
            status: Filter by task status
            task_type: Filter by task type
            priority: Filter by task priority
            tags: Filter by tags (task must have all specified tags)
        
        Returns:
            List of tasks matching the criteria
        """
        with self._lock:
            tasks = list(self._tasks.values())
        
        # Apply filters
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        if task_type is not None:
            tasks = [t for t in tasks if t.task_type == task_type]
        if priority is not None:
            tasks = [t for t in tasks if t.priority == priority]
        if tags is not None:
            tasks = [t for t in tasks if tags.issubset(t.metadata.tags)]
        
        return tasks
    
    def schedule_task(self, task_id: str) -> bool:
        """
        Schedule a task for execution.
        
        Args:
            task_id: ID of the task to schedule
        
        Returns:
            True if the task was scheduled, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return False
        
        if task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} is not in pending status: {task.status}")
            return False
        
        # Check dependencies
        completed_task_ids = set(self._get_completed_task_ids())
        if not task.can_execute(completed_task_ids):
            logger.info(f"Task {task_id} dependencies not satisfied, queuing for later")
            return False
        
        # Schedule with the scheduler
        if self.scheduler.schedule_task(task):
            task.update_status(TaskStatus.QUEUED)
            logger.info(f"Scheduled task: {task_id}")
            
            # Try to execute immediately if resources are available
            self._try_execute_queued_tasks()
            return True
        
        return False
    
    def execute_task(self, task_id: str) -> bool:
        """
        Execute a task immediately if possible.
        
        Args:
            task_id: ID of the task to execute
        
        Returns:
            True if execution started, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return False
        
        if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            logger.warning(f"Task {task_id} cannot be executed in status: {task.status}")
            return False
        
        # Check if we have capacity
        with self._lock:
            if len(self._running_tasks) >= self.config.max_concurrent_tasks:
                logger.info(f"Max concurrent tasks reached, cannot execute {task_id}")
                return False
        
        # Get task handler
        handler = self._task_handlers.get(task.task_type)
        if not handler:
            logger.error(f"No handler registered for task type: {task.task_type}")
            task.update_status(TaskStatus.FAILED, {"error": "No handler registered"})
            return False
        
        # Create execution context
        context = ExecutionContext(
            task_id=task.id,
            timeout=task.timeout,
            resource_requirements=task.resource_requirements
        )
        
        # Submit for execution
        future = self.executor.submit_task(task, handler, context)
        
        with self._lock:
            self._running_tasks[task.id] = future
        
        task.update_status(TaskStatus.RUNNING)
        
        # Add completion callback
        future.add_done_callback(lambda f: self._on_task_completed(task.id, f))
        
        logger.info(f"Started execution of task: {task_id}")
        
        if self.monitor:
            self.monitor.task_started(task)
        
        return True
    
    def cancel_task(self, task_id: str, reason: Optional[str] = None) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: ID of the task to cancel
            reason: Optional reason for cancellation
        
        Returns:
            True if the task was cancelled, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            logger.warning(f"Task {task_id} is already in final status: {task.status}")
            return False
        
        # Cancel running task
        with self._lock:
            if task.id in self._running_tasks:
                future = self._running_tasks[task.id]
                future.cancel()
                del self._running_tasks[task.id]
        
        # Remove from scheduler
        self.scheduler.remove_task(task.id)
        
        # Update task status
        error_info = {"reason": reason} if reason else None
        task.update_status(TaskStatus.CANCELLED, error_info)
        
        logger.info(f"Cancelled task: {task_id}")
        
        if self.monitor:
            self.monitor.task_cancelled(task)
        
        return True
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a running task (if supported by the executor)."""
        task = self.get_task(task_id)
        if not task or task.status != TaskStatus.RUNNING:
            return False
        
        # Implementation depends on executor capabilities
        # For now, we'll just update the status
        task.update_status(TaskStatus.PAUSED)
        logger.info(f"Paused task: {task_id}")
        return True
    
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        task = self.get_task(task_id)
        if not task or task.status != TaskStatus.PAUSED:
            return False
        
        task.update_status(TaskStatus.RUNNING)
        logger.info(f"Resumed task: {task_id}")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the current status of a task."""
        task = self.get_task(task_id)
        return task.status if task else None
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the result data of a completed task."""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.output_data
        return None
    
    def get_metrics(self) -> Optional[MonitoringMetrics]:
        """Get current performance metrics."""
        if self.monitor:
            return self.monitor.get_metrics()
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status and statistics."""
        with self._lock:
            status_counts = defaultdict(int)
            for task in self._tasks.values():
                status_counts[task.status.value] += 1
            
            return {
                "total_tasks": len(self._tasks),
                "running_tasks": len(self._running_tasks),
                "completed_tasks": len(self._completed_tasks),
                "status_breakdown": dict(status_counts),
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "scheduler_queue_size": self.scheduler.get_queue_size(),
                "uptime": datetime.utcnow() - getattr(self, '_start_time', datetime.utcnow()),
            }
    
    def _try_execute_queued_tasks(self) -> None:
        """Try to execute queued tasks if resources are available."""
        while True:
            with self._lock:
                if len(self._running_tasks) >= self.config.max_concurrent_tasks:
                    break
            
            next_task = self.scheduler.get_next_task()
            if not next_task:
                break
            
            if not self.execute_task(next_task.id):
                # If execution failed, put it back in the queue
                self.scheduler.schedule_task(next_task)
                break
    
    def _on_task_completed(self, task_id: str, future: Future) -> None:
        """Callback when a task execution completes."""
        task = self.get_task(task_id)
        if not task:
            return
        
        # Remove from running tasks
        with self._lock:
            self._running_tasks.pop(task_id, None)
        
        try:
            result = future.result()
            task.output_data = result if isinstance(result, dict) else {"result": result}
            task.update_status(TaskStatus.COMPLETED)
            logger.info(f"Task completed successfully: {task_id}")
            
            if self.monitor:
                self.monitor.task_completed(task)
                
        except Exception as e:
            error_info = {
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
            task.update_status(TaskStatus.FAILED, error_info)
            logger.error(f"Task failed: {task_id}, error: {e}")
            
            if self.monitor:
                self.monitor.task_failed(task, e)
        
        # Move to completed tasks
        with self._lock:
            self._completed_tasks.append(task)
        
        # Try to execute more queued tasks
        self._try_execute_queued_tasks()
        
        # Check for dependent tasks that can now be scheduled
        self._check_dependent_tasks(task_id)
    
    def _check_dependent_tasks(self, completed_task_id: str) -> None:
        """Check if any pending tasks can now be scheduled due to dependency completion."""
        pending_tasks = self.get_tasks(status=TaskStatus.PENDING)
        completed_task_ids = set(self._get_completed_task_ids())
        
        for task in pending_tasks:
            if any(dep.task_id == completed_task_id for dep in task.dependencies):
                if task.can_execute(completed_task_ids):
                    self.schedule_task(task.id)
    
    def _get_completed_task_ids(self) -> List[str]:
        """Get IDs of all completed tasks."""
        with self._lock:
            return [task.id for task in self._tasks.values() 
                   if task.status == TaskStatus.COMPLETED]
    
    def _cleanup_completed_tasks(self) -> None:
        """Clean up old completed tasks to prevent memory leaks."""
        with self._lock:
            if len(self._completed_tasks) > self.config.max_completed_tasks_history:
                # Keep only the most recent completed tasks
                self._completed_tasks = self._completed_tasks[-self.config.max_completed_tasks_history:]
                logger.debug("Cleaned up old completed tasks")
    
    def _check_timeouts(self) -> None:
        """Check for timed out tasks and handle them."""
        current_time = datetime.utcnow()
        
        for task in self.get_tasks(status=TaskStatus.RUNNING):
            if task.timeout and task.started_at:
                if current_time - task.started_at > task.timeout:
                    logger.warning(f"Task {task.id} timed out")
                    self.cancel_task(task.id, "Timeout")
    
    def _retry_failed_tasks(self) -> None:
        """Retry failed tasks that are eligible for retry."""
        if not self.config.enable_auto_retry:
            return
        
        failed_tasks = self.get_tasks(status=TaskStatus.FAILED)
        for task in failed_tasks:
            if task.should_retry():
                logger.info(f"Retrying failed task: {task.id}")
                task.increment_retry()
                self.schedule_task(task.id)
    
    def shutdown(self, timeout: Optional[float] = None) -> None:
        """
        Shutdown the TaskManager gracefully.
        
        Args:
            timeout: Maximum time to wait for shutdown in seconds
        """
        logger.info("Shutting down TaskManager...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel all running tasks
        with self._lock:
            running_task_ids = list(self._running_tasks.keys())
        
        for task_id in running_task_ids:
            self.cancel_task(task_id, "System shutdown")
        
        # Wait for cleanup thread
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=timeout)
        
        # Shutdown executor
        self.executor.shutdown(wait=True, timeout=timeout)
        
        logger.info("TaskManager shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()

