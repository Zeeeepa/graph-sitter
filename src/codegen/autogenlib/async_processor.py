"""Asynchronous task processing and queue management."""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from .client import AutogenClient
from .config import AutogenConfig
from .context import ContextEnhancer
from .models import TaskRequest, TaskResponse, TaskStatus

logger = logging.getLogger(__name__)


class AsyncTaskProcessor:
    """Handles asynchronous task processing with queue management."""
    
    def __init__(self, config: AutogenConfig, client: AutogenClient, context_enhancer: ContextEnhancer):
        """Initialize the async task processor.
        
        Args:
            config: Configuration object.
            client: AutogenClient instance.
            context_enhancer: ContextEnhancer instance.
        """
        self.config = config
        self.client = client
        self.context_enhancer = context_enhancer
        
        # Task storage
        self._tasks: Dict[str, TaskResponse] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        
        # Queue and semaphore for concurrency control
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
        
        # Worker tasks
        self._workers: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self._stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "queue_size": 0,
            "active_workers": 0,
        }
        
        # Start worker tasks
        self._start_workers()
        
        logger.info(f"AsyncTaskProcessor initialized with {config.max_concurrent_tasks} workers")
    
    def _start_workers(self) -> None:
        """Start worker tasks for processing the queue."""
        for i in range(self.config.max_concurrent_tasks):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
    
    async def _worker(self, worker_name: str) -> None:
        """Worker task that processes items from the queue.
        
        Args:
            worker_name: Name of the worker for logging.
        """
        logger.info(f"Worker {worker_name} started")
        
        while not self._shutdown_event.is_set():
            try:
                # Wait for a task with timeout to allow periodic shutdown checks
                try:
                    task_id, request = await asyncio.wait_for(
                        self._task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Acquire semaphore to limit concurrency
                async with self._semaphore:
                    self._stats["active_workers"] += 1
                    
                    try:
                        await self._process_task(task_id, request)
                    finally:
                        self._stats["active_workers"] -= 1
                        self._task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {worker_name} encountered error: {e}")
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _process_task(self, task_id: str, request: TaskRequest) -> None:
        """Process a single task.
        
        Args:
            task_id: Task identifier.
            request: Task request.
        """
        logger.info(f"Processing task {task_id}")
        
        # Update task status to running
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.RUNNING
            self._tasks[task_id].updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Run the task
            response = await self.client.run_task_async(request)
            
            # Update stored task with result
            if task_id in self._tasks:
                self._tasks[task_id].status = response.status
                self._tasks[task_id].result = response.result
                self._tasks[task_id].error = response.error
                self._tasks[task_id].updated_at = response.updated_at
                self._tasks[task_id].metadata = response.metadata
            
            if response.status == TaskStatus.COMPLETED:
                self._stats["tasks_completed"] += 1
                logger.info(f"Task {task_id} completed successfully")
            else:
                self._stats["tasks_failed"] += 1
                logger.error(f"Task {task_id} failed: {response.error}")
        
        except asyncio.CancelledError:
            # Task was cancelled
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.CANCELLED
                self._tasks[task_id].updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
            
            self._stats["tasks_cancelled"] += 1
            logger.info(f"Task {task_id} was cancelled")
            raise
        
        except Exception as e:
            # Task failed with exception
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.FAILED
                self._tasks[task_id].error = str(e)
                self._tasks[task_id].updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
            
            self._stats["tasks_failed"] += 1
            logger.error(f"Task {task_id} failed with exception: {e}")
        
        finally:
            # Remove from running tasks
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
    
    async def submit_task(self, request: TaskRequest) -> TaskResponse:
        """Submit a task for asynchronous processing.
        
        Args:
            request: Task request.
            
        Returns:
            TaskResponse with initial task details.
        """
        task_id = str(uuid.uuid4())
        
        # Create initial task response
        response = TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={"queue_position": self._task_queue.qsize()}
        )
        
        # Store task
        self._tasks[task_id] = response
        
        # Add to queue
        await self._task_queue.put((task_id, request))
        
        self._stats["tasks_submitted"] += 1
        self._stats["queue_size"] = self._task_queue.qsize()
        
        logger.info(f"Task {task_id} submitted to queue (position: {response.metadata['queue_position']})")
        
        return response
    
    async def get_task_status(self, task_id: str) -> Optional[TaskResponse]:
        """Get the status of a task.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            TaskResponse if task exists, None otherwise.
        """
        return self._tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            True if task was cancelled, False otherwise.
        """
        if task_id in self._running_tasks:
            # Cancel running task
            self._running_tasks[task_id].cancel()
            logger.info(f"Cancelled running task {task_id}")
            return True
        
        elif task_id in self._tasks and self._tasks[task_id].status == TaskStatus.PENDING:
            # Mark pending task as cancelled
            self._tasks[task_id].status = TaskStatus.CANCELLED
            self._tasks[task_id].updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
            self._stats["tasks_cancelled"] += 1
            logger.info(f"Cancelled pending task {task_id}")
            return True
        
        return False
    
    async def list_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskResponse]:
        """List tasks, optionally filtered by status.
        
        Args:
            status: Optional status filter.
            
        Returns:
            List of TaskResponse objects.
        """
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [task for task in tasks if task.status == status]
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics.
        
        Returns:
            Dictionary containing statistics.
        """
        self._stats["queue_size"] = self._task_queue.qsize()
        return self._stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check.
        
        Returns:
            Dictionary containing health status.
        """
        alive_workers = sum(1 for worker in self._workers if not worker.done())
        
        return {
            "status": "healthy" if alive_workers > 0 else "unhealthy",
            "workers_alive": alive_workers,
            "workers_total": len(self._workers),
            "queue_size": self._task_queue.qsize(),
            "active_tasks": len(self._running_tasks),
            "total_tasks": len(self._tasks),
            "shutdown_requested": self._shutdown_event.is_set(),
        }
    
    async def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "queue_size": self._task_queue.qsize(),
            "active_workers": 0,
        }
        logger.info("Async processor statistics reset")
    
    async def shutdown(self) -> None:
        """Shutdown the processor and cleanup resources."""
        logger.info("Shutting down async task processor...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel all running tasks
        for task_id, task in self._running_tasks.items():
            task.cancel()
            logger.info(f"Cancelled running task {task_id}")
        
        # Wait for workers to finish
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        # Wait for queue to be empty
        await self._task_queue.join()
        
        logger.info("Async task processor shutdown complete")

