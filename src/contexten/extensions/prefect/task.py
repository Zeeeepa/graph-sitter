#!/usr/bin/env python3
"""
Prefect Task Module
Handles task definitions and execution within the Prefect workflow system.
"""

from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
import logging

logger = logging.getLogger(__name__)


class PrefectTask:
    """Prefect task wrapper."""
    
    def __init__(self, name: str, func: Callable, **kwargs):
        self.name = name
        self.func = func
        self.kwargs = kwargs
        self.retries = kwargs.get('retries', 0)
        self.timeout = kwargs.get('timeout', None)
        
    async def run(self, *args, **kwargs) -> Any:
        """Execute the task."""
        logger.info(f"Running task: {self.name}")
        
        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(*args, **kwargs)
            else:
                result = self.func(*args, **kwargs)
                
            logger.info(f"Task completed: {self.name}")
            return result
            
        except Exception as e:
            logger.error(f"Task failed: {self.name} - {e}")
            raise


def task(name: Optional[str] = None, **kwargs):
    """Decorator to create a Prefect task."""
    def decorator(func):
        task_name = name or func.__name__
        return PrefectTask(task_name, func, **kwargs)
    return decorator


class TaskRunner:
    """Task execution runner."""
    
    def __init__(self):
        self.running_tasks: Dict[str, Any] = {}
        
    async def execute_task(self, task: PrefectTask, *args, **kwargs) -> Any:
        """Execute a task with error handling and retries."""
        task_id = f"{task.name}_{id(task)}"
        
        for attempt in range(task.retries + 1):
            try:
                self.running_tasks[task_id] = {
                    "task": task,
                    "attempt": attempt + 1,
                    "status": "running"
                }
                
                if task.timeout:
                    result = await asyncio.wait_for(
                        task.run(*args, **kwargs), 
                        timeout=task.timeout
                    )
                else:
                    result = await task.run(*args, **kwargs)
                
                self.running_tasks[task_id]["status"] = "completed"
                return result
                
            except Exception as e:
                if attempt < task.retries:
                    logger.warning(f"Task {task.name} failed, retrying... ({attempt + 1}/{task.retries})")
                    await asyncio.sleep(1)  # Brief delay before retry
                else:
                    self.running_tasks[task_id]["status"] = "failed"
                    raise
                    
        # Clean up after execution
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]

