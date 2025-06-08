#!/usr/bin/env python3
"""
ControlFlow Scheduler Module
Handles scheduling and coordination of tasks within the ControlFlow system.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import uuid
from datetime import datetime, timedelta

from ..base.interfaces import BaseExtension

logger = logging.getLogger(__name__)


class ControlFlowScheduler(BaseExtension):
    """Scheduler for ControlFlow tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.scheduled_tasks: Dict[str, Any] = {}
        self.task_queue: List[Dict[str, Any]] = []
    
    async def _initialize_impl(self) -> None:
        """Initialize the ControlFlow scheduler."""
        self.logger.info("Initializing ControlFlow scheduler")
        # Initialize any required resources
        pass
    
    async def _handle_impl(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Handle scheduling requests."""
        action = payload.get("action")
        
        if action == "schedule_task":
            return await self.schedule_task(
                payload.get("task_id", str(uuid.uuid4())),
                payload.get("task_config", {}),
                payload.get("schedule_time")
            )
        elif action == "get_scheduled_tasks":
            return {"scheduled_tasks": list(self.scheduled_tasks.values())}
        elif action == "cancel_task":
            return await self.cancel_task(payload.get("task_id"))
        else:
            return {"error": f"Unknown action: {action}", "status": "failed"}
        
    async def schedule_task(self, task_id: str, task_config: Dict[str, Any], 
                           schedule_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Schedule a task for execution."""
        logger.info(f"Scheduling task: {task_id}")
        
        if schedule_time is None:
            schedule_time = datetime.now()
        elif isinstance(schedule_time, str):
            schedule_time = datetime.fromisoformat(schedule_time)
            
        scheduled_task = {
            "task_id": task_id,
            "config": task_config,
            "schedule_time": schedule_time.isoformat(),
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.scheduled_tasks[task_id] = scheduled_task
        self.task_queue.append(scheduled_task)
        
        # Sort queue by schedule time
        self.task_queue.sort(key=lambda x: x["schedule_time"])
        
        return scheduled_task
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a scheduled task."""
        if task_id not in self.scheduled_tasks:
            return {"error": f"Task {task_id} not found", "status": "not_found"}
        
        # Remove from scheduled tasks
        task = self.scheduled_tasks.pop(task_id)
        
        # Remove from queue
        self.task_queue = [t for t in self.task_queue if t["task_id"] != task_id]
        
        task["status"] = "cancelled"
        task["cancelled_at"] = datetime.utcnow().isoformat()
        
        self.logger.info(f"Cancelled task: {task_id}")
        return task
    
    async def get_ready_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks that are ready for execution."""
        now = datetime.now()
        ready_tasks = []
        
        for task in self.task_queue:
            if task["scheduled_time"] <= now and task["status"] == "scheduled":
                ready_tasks.append(task)
                task["status"] = "ready"
                
        return ready_tasks


# Alias for backward compatibility and expected import name
FlowScheduler = ControlFlowScheduler
