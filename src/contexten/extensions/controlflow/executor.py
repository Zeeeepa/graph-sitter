#!/usr/bin/env python3
"""
ControlFlow Executor Module
Handles execution of tasks within the ControlFlow orchestration system.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import uuid
from datetime import datetime

from ..base.interfaces import BaseExtension

logger = logging.getLogger(__name__)


class ControlFlowExecutor(BaseExtension):
    """Executor for ControlFlow tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.running_tasks: Dict[str, Any] = {}
    
    async def _initialize_impl(self) -> None:
        """Initialize the ControlFlow executor."""
        self.logger.info("Initializing ControlFlow executor")
        # Initialize any required resources
        pass
    
    async def _handle_impl(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Handle execution requests."""
        action = payload.get("action")
        
        if action == "execute_task":
            return await self.execute_task(
                payload.get("task_id", str(uuid.uuid4())),
                payload.get("task_config", {})
            )
        elif action == "get_task_status":
            task_id = payload.get("task_id")
            if not task_id:
                return {"error": "task_id is required", "status": "failed"}
            return await self.get_task_status(task_id)
        else:
            return {"error": f"Unknown action: {action}", "status": "failed"}
        
    async def execute_task(self, task_id: str, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task."""
        logger.info(f"Executing task: {task_id}")
        
        try:
            # Store task as running
            self.running_tasks[task_id] = {
                "task_id": task_id,
                "config": task_config,
                "status": "running",
                "started_at": datetime.utcnow().isoformat()
            }
            
            # Task execution logic would go here
            result = {
                "task_id": task_id,
                "status": "completed",
                "result": "Task executed successfully",
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Update task status
            self.running_tasks[task_id].update(result)
            
            return result
            
        except Exception as e:
            error_result = {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
            
            if task_id in self.running_tasks:
                self.running_tasks[task_id].update(error_result)
            
            logger.error(f"Task {task_id} failed: {e}")
            return error_result
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a task."""
        if task_id not in self.running_tasks:
            return {"error": f"Task {task_id} not found", "status": "not_found"}
        
        return self.running_tasks[task_id]

    async def execute_batch(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple tasks."""
        results = []
        
        for task in tasks:
            task_id = task.get("id", "unknown")
            result = await self.execute_task(task_id, task)
            results.append(result)
            
        return results


# Alias for backward compatibility and expected import name
FlowExecutor = ControlFlowExecutor
