#!/usr/bin/env python3
"""
ControlFlow Scheduler Module
Handles scheduling and coordination of tasks within the ControlFlow system.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ControlFlowScheduler:
    """Scheduler for ControlFlow tasks."""
    
    def __init__(self):
        self.scheduled_tasks: Dict[str, Any] = {}
        self.task_queue: List[Dict[str, Any]] = []
        
    async def schedule_task(self, task_id: str, task_config: Dict[str, Any], 
                           schedule_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Schedule a task for execution."""
        logger.info(f"Scheduling task: {task_id}")
        
        if schedule_time is None:
            schedule_time = datetime.now()
            
        scheduled_task = {
            "task_id": task_id,
            "config": task_config,
            "scheduled_time": schedule_time,
            "status": "scheduled"
        }
        
        self.scheduled_tasks[task_id] = scheduled_task
        self.task_queue.append(scheduled_task)
        
        return scheduled_task
    
    async def get_ready_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks that are ready for execution."""
        now = datetime.now()
        ready_tasks = []
        
        for task in self.task_queue:
            if task["scheduled_time"] <= now and task["status"] == "scheduled":
                ready_tasks.append(task)
                task["status"] = "ready"
                
        return ready_tasks
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id]["status"] = "cancelled"
            logger.info(f"Task cancelled: {task_id}")
            return True
        return False

