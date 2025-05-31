"""
Task Executor Implementation

Provides task execution capabilities with resource management, timeout handling,
and performance monitoring.
"""

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Set
import psutil
import signal
import os

from .task import Task, TaskResource


logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context information for task execution."""
    task_id: str
    timeout: Optional[timedelta] = None
    resource_requirements: Optional[TaskResource] = None
    execution_environment: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.execution_environment is None:
            self.execution_environment = {}


class ResourceManager:
    """Manages system resources for task execution."""
    
    def __init__(self):
        self._allocated_resources: Dict[str, TaskResource] = {}
        self._lock = threading.RLock()
    
    def can_allocate(self, task_id: str, requirements: TaskResource) -> bool:
        """Check if the required resources can be allocated."""
        if not requirements:
            return True
        
        with self._lock:
            # Get current system resources
            cpu_count = psutil.cpu_count()
            memory_mb = psutil.virtual_memory().available // (1024 * 1024)
            
            # Calculate currently allocated resources
            allocated_cpu = sum(
                res.cpu_cores or 0 for res in self._allocated_resources.values()
            )
            allocated_memory = sum(
                res.memory_mb or 0 for res in self._allocated_resources.values()
            )
            
            # Check CPU availability
            if requirements.cpu_cores:
                if allocated_cpu + requirements.cpu_cores > cpu_count:
                    return False
            
            # Check memory availability
            if requirements.memory_mb:
                if allocated_memory + requirements.memory_mb > memory_mb:
                    return False
            
            # Check GPU requirement (simplified check)
            if requirements.gpu_required:
                try:
                    import GPUtil
                    gpus = GPUtil.getGPUs()
                    if not gpus or all(gpu.memoryUtil > 0.8 for gpu in gpus):
                        return False
                except ImportError:
                    # If GPUtil is not available, assume no GPU support
                    return False
            
            return True
    
    def allocate(self, task_id: str, requirements: TaskResource) -> bool:
        """Allocate resources for a task."""
        if not requirements:
            return True
        
        with self._lock:
            if not self.can_allocate(task_id, requirements):
                return False
            
            self._allocated_resources[task_id] = requirements
            logger.debug(f"Allocated resources for task {task_id}: {requirements}")
            return True
    
    def deallocate(self, task_id: str) -> None:
        """Deallocate resources for a task."""
        with self._lock:
            if task_id in self._allocated_resources:
                requirements = self._allocated_resources.pop(task_id)
                logger.debug(f"Deallocated resources for task {task_id}: {requirements}")
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        with self._lock:
            allocated_cpu = sum(
                res.cpu_cores or 0 for res in self._allocated_resources.values()
            )
            allocated_memory = sum(
                res.memory_mb or 0 for res in self._allocated_resources.values()
            )
            
            return {
                "allocated_cpu_cores": allocated_cpu,
                "allocated_memory_mb": allocated_memory,
                "total_cpu_cores": psutil.cpu_count(),
                "available_memory_mb": psutil.virtual_memory().available // (1024 * 1024),
                "active_tasks": len(self._allocated_resources),
            }


class TaskExecutor:
    """
    Advanced task executor with resource management and monitoring.
    
    Handles the actual execution of tasks with support for:
    - Resource allocation and management
    - Timeout handling
    - Performance monitoring
    - Error handling and recovery
    """
    
    def __init__(self, max_workers: int = 10):
        """Initialize the task executor."""
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="TaskExecutor"
        )
        self._resource_manager = ResourceManager()
        self._active_tasks: Dict[str, Future] = {}
        self._task_start_times: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        
        logger.info(f"TaskExecutor initialized with {max_workers} workers")
    
    def submit_task(
        self,
        task: Task,
        handler: Callable[[Task], Any],
        context: ExecutionContext
    ) -> Future:
        """
        Submit a task for execution.
        
        Args:
            task: The task to execute
            handler: The function to handle task execution
            context: Execution context and configuration
            
        Returns:
            Future representing the task execution
        """
        # Check resource requirements
        if context.resource_requirements:
            if not self._resource_manager.can_allocate(task.id, context.resource_requirements):
                raise RuntimeError(f"Insufficient resources for task {task.id}")
        
        # Allocate resources
        if context.resource_requirements:
            if not self._resource_manager.allocate(task.id, context.resource_requirements):
                raise RuntimeError(f"Failed to allocate resources for task {task.id}")
        
        # Create execution wrapper
        def execute_with_monitoring():
            return self._execute_task_with_monitoring(task, handler, context)
        
        # Submit to thread pool
        future = self._executor.submit(execute_with_monitoring)
        
        # Track active task
        with self._lock:
            self._active_tasks[task.id] = future
            self._task_start_times[task.id] = datetime.utcnow()
        
        # Add cleanup callback
        future.add_done_callback(lambda f: self._cleanup_task(task.id))
        
        logger.info(f"Submitted task {task.id} for execution")
        return future
    
    def _execute_task_with_monitoring(
        self,
        task: Task,
        handler: Callable[[Task], Any],
        context: ExecutionContext
    ) -> Any:
        """Execute a task with comprehensive monitoring and error handling."""
        start_time = time.time()
        
        try:
            # Set up execution environment
            self._setup_execution_environment(context)
            
            # Execute with timeout if specified
            if context.timeout:
                result = self._execute_with_timeout(
                    handler, task, context.timeout.total_seconds()
                )
            else:
                result = handler(task)
            
            execution_time = time.time() - start_time
            logger.info(f"Task {task.id} completed in {execution_time:.2f} seconds")
            
            return result
            
        except TimeoutError:
            logger.error(f"Task {task.id} timed out after {context.timeout}")
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Task {task.id} failed after {execution_time:.2f} seconds: {e}")
            raise
        finally:
            # Clean up execution environment
            self._cleanup_execution_environment(context)
    
    def _execute_with_timeout(
        self,
        handler: Callable[[Task], Any],
        task: Task,
        timeout_seconds: float
    ) -> Any:
        """Execute a task handler with timeout."""
        # For CPU-bound tasks, we use a separate process with timeout
        # For I/O-bound tasks, we could use asyncio with timeout
        
        import multiprocessing
        from multiprocessing import Process, Queue
        
        def target_function(queue: Queue, task_data: Dict[str, Any]):
            try:
                # Recreate task from data
                task_obj = Task.from_dict(task_data)
                result = handler(task_obj)
                queue.put({"success": True, "result": result})
            except Exception as e:
                queue.put({"success": False, "error": str(e), "error_type": type(e).__name__})
        
        # Create process and queue
        queue = Queue()
        process = Process(
            target=target_function,
            args=(queue, task.to_dict())
        )
        
        try:
            process.start()
            process.join(timeout=timeout_seconds)
            
            if process.is_alive():
                # Timeout occurred
                process.terminate()
                process.join(timeout=5)  # Give it 5 seconds to terminate gracefully
                if process.is_alive():
                    process.kill()  # Force kill if necessary
                raise TimeoutError(f"Task execution timed out after {timeout_seconds} seconds")
            
            # Get result from queue
            if not queue.empty():
                result_data = queue.get_nowait()
                if result_data["success"]:
                    return result_data["result"]
                else:
                    error_type = result_data.get("error_type", "Exception")
                    error_msg = result_data.get("error", "Unknown error")
                    # Recreate the exception
                    if error_type in globals():
                        exception_class = globals()[error_type]
                        raise exception_class(error_msg)
                    else:
                        raise RuntimeError(f"{error_type}: {error_msg}")
            else:
                raise RuntimeError("Task completed but no result was returned")
                
        finally:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
    
    def _setup_execution_environment(self, context: ExecutionContext) -> None:
        """Set up the execution environment for a task."""
        # Set environment variables if specified
        for key, value in context.execution_environment.items():
            os.environ[key] = str(value)
        
        # Set process priority if needed
        if context.resource_requirements and context.resource_requirements.cpu_cores:
            try:
                # Lower priority for resource-intensive tasks
                os.nice(5)
            except (OSError, AttributeError):
                pass  # Not supported on all platforms
    
    def _cleanup_execution_environment(self, context: ExecutionContext) -> None:
        """Clean up the execution environment after task completion."""
        # Remove environment variables that were set
        for key in context.execution_environment.keys():
            os.environ.pop(key, None)
    
    def _cleanup_task(self, task_id: str) -> None:
        """Clean up resources and tracking for a completed task."""
        with self._lock:
            self._active_tasks.pop(task_id, None)
            self._task_start_times.pop(task_id, None)
        
        # Deallocate resources
        self._resource_manager.deallocate(task_id)
        
        logger.debug(f"Cleaned up task {task_id}")
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        with self._lock:
            if task_id not in self._active_tasks:
                return False
            
            future = self._active_tasks[task_id]
            cancelled = future.cancel()
            
            if cancelled:
                self._cleanup_task(task_id)
                logger.info(f"Cancelled task {task_id}")
            
            return cancelled
    
    def get_active_tasks(self) -> Set[str]:
        """Get the set of currently active task IDs."""
        with self._lock:
            return set(self._active_tasks.keys())
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the execution status of a task."""
        with self._lock:
            if task_id not in self._active_tasks:
                return None
            
            future = self._active_tasks[task_id]
            if future.done():
                if future.cancelled():
                    return "cancelled"
                elif future.exception():
                    return "failed"
                else:
                    return "completed"
            else:
                return "running"
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        with self._lock:
            active_count = len(self._active_tasks)
            
            # Calculate average execution time for active tasks
            now = datetime.utcnow()
            execution_times = [
                (now - start_time).total_seconds()
                for start_time in self._task_start_times.values()
            ]
            
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            return {
                "active_tasks": active_count,
                "max_workers": self.max_workers,
                "utilization": active_count / self.max_workers,
                "average_execution_time_seconds": avg_execution_time,
                "resource_usage": self._resource_manager.get_resource_usage(),
            }
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """Shutdown the executor."""
        logger.info("Shutting down TaskExecutor...")
        
        # Cancel all active tasks
        with self._lock:
            active_task_ids = list(self._active_tasks.keys())
        
        for task_id in active_task_ids:
            self.cancel_task(task_id)
        
        # Shutdown thread pool
        self._executor.shutdown(wait=wait, timeout=timeout)
        
        logger.info("TaskExecutor shutdown complete")

