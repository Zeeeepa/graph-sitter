"""
Task Scheduler Implementation

Provides intelligent task scheduling capabilities with support for different
scheduling strategies, priority management, and dependency resolution.
"""

import heapq
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
import threading

from .task import Task, TaskStatus, TaskPriority


logger = logging.getLogger(__name__)


class SchedulingStrategy(Enum):
    """Available task scheduling strategies."""
    FIFO = "fifo"  # First In, First Out
    PRIORITY_FIRST = "priority_first"  # Priority-based scheduling
    SHORTEST_JOB_FIRST = "shortest_job_first"  # Shortest estimated duration first
    DEADLINE_FIRST = "deadline_first"  # Earliest deadline first
    WEIGHTED_PRIORITY = "weighted_priority"  # Weighted combination of factors
    ROUND_ROBIN = "round_robin"  # Round-robin by task type


@dataclass
class ScheduledTask:
    """Wrapper for tasks in the scheduler queue."""
    task: Task
    priority_score: float
    scheduled_at: datetime = field(default_factory=datetime.utcnow)
    
    def __lt__(self, other: "ScheduledTask") -> bool:
        """Comparison for heap ordering (lower score = higher priority)."""
        return self.priority_score < other.priority_score


class TaskScheduler:
    """
    Advanced task scheduler with multiple scheduling strategies and optimization.
    
    The scheduler manages task queuing, priority calculation, and execution ordering
    based on configurable strategies and system constraints.
    """
    
    def __init__(self, strategy: SchedulingStrategy = SchedulingStrategy.PRIORITY_FIRST):
        """Initialize the scheduler with the specified strategy."""
        self.strategy = strategy
        self._queue: List[ScheduledTask] = []
        self._task_index: Dict[str, ScheduledTask] = {}
        self._lock = threading.RLock()
        
        # Strategy-specific state
        self._round_robin_index = 0
        self._task_type_counts: Dict[str, int] = {}
        
        logger.info(f"TaskScheduler initialized with strategy: {strategy.value}")
    
    def schedule_task(self, task: Task) -> bool:
        """
        Add a task to the scheduling queue.
        
        Args:
            task: The task to schedule
            
        Returns:
            True if the task was scheduled successfully
        """
        if task.status != TaskStatus.PENDING:
            logger.warning(f"Cannot schedule task {task.id} with status {task.status}")
            return False
        
        with self._lock:
            # Check if task is already scheduled
            if task.id in self._task_index:
                logger.warning(f"Task {task.id} is already scheduled")
                return False
            
            # Calculate priority score based on strategy
            priority_score = self._calculate_priority_score(task)
            
            # Create scheduled task wrapper
            scheduled_task = ScheduledTask(
                task=task,
                priority_score=priority_score
            )
            
            # Add to queue and index
            heapq.heappush(self._queue, scheduled_task)
            self._task_index[task.id] = scheduled_task
            
            # Update strategy-specific state
            self._update_strategy_state(task)
            
            logger.debug(f"Scheduled task {task.id} with priority score {priority_score}")
            return True
    
    def get_next_task(self) -> Optional[Task]:
        """
        Get the next task to execute based on the scheduling strategy.
        
        Returns:
            The next task to execute, or None if no tasks are available
        """
        with self._lock:
            while self._queue:
                scheduled_task = heapq.heappop(self._queue)
                task = scheduled_task.task
                
                # Remove from index
                self._task_index.pop(task.id, None)
                
                # Check if task is still valid for execution
                if task.status == TaskStatus.PENDING:
                    # Check if scheduled time has arrived
                    if task.scheduled_at and task.scheduled_at > datetime.utcnow():
                        # Reschedule for later
                        self.schedule_task(task)
                        continue
                    
                    logger.debug(f"Selected task {task.id} for execution")
                    return task
                else:
                    logger.debug(f"Skipping task {task.id} with status {task.status}")
            
            return None
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task from the scheduling queue.
        
        Args:
            task_id: ID of the task to remove
            
        Returns:
            True if the task was removed successfully
        """
        with self._lock:
            if task_id not in self._task_index:
                return False
            
            scheduled_task = self._task_index.pop(task_id)
            
            # Mark as removed (we can't efficiently remove from heap)
            scheduled_task.task.update_status(TaskStatus.CANCELLED)
            
            logger.debug(f"Removed task {task_id} from scheduler")
            return True
    
    def get_queue_size(self) -> int:
        """Get the current size of the scheduling queue."""
        with self._lock:
            return len(self._task_index)
    
    def get_queued_tasks(self) -> List[Task]:
        """Get all tasks currently in the queue."""
        with self._lock:
            return [st.task for st in self._task_index.values()]
    
    def update_task_priority(self, task_id: str, new_priority: TaskPriority) -> bool:
        """
        Update the priority of a queued task.
        
        Args:
            task_id: ID of the task to update
            new_priority: New priority level
            
        Returns:
            True if the priority was updated successfully
        """
        with self._lock:
            if task_id not in self._task_index:
                return False
            
            scheduled_task = self._task_index[task_id]
            old_priority = scheduled_task.task.priority
            
            # Update task priority
            scheduled_task.task.priority = new_priority
            
            # Recalculate priority score
            new_score = self._calculate_priority_score(scheduled_task.task)
            scheduled_task.priority_score = new_score
            
            # Rebuild heap to maintain order
            heapq.heapify(self._queue)
            
            logger.info(f"Updated task {task_id} priority from {old_priority} to {new_priority}")
            return True
    
    def _calculate_priority_score(self, task: Task) -> float:
        """
        Calculate the priority score for a task based on the scheduling strategy.
        
        Lower scores indicate higher priority.
        """
        if self.strategy == SchedulingStrategy.FIFO:
            return task.created_at.timestamp()
        
        elif self.strategy == SchedulingStrategy.PRIORITY_FIRST:
            # Lower priority enum value = higher priority
            return task.priority.value
        
        elif self.strategy == SchedulingStrategy.SHORTEST_JOB_FIRST:
            if task.estimated_duration:
                return task.estimated_duration.total_seconds()
            else:
                # Default duration for tasks without estimates
                return 3600.0  # 1 hour
        
        elif self.strategy == SchedulingStrategy.DEADLINE_FIRST:
            if task.deadline:
                return task.deadline.timestamp()
            else:
                # Tasks without deadlines get lower priority
                return datetime.max.timestamp()
        
        elif self.strategy == SchedulingStrategy.WEIGHTED_PRIORITY:
            return self._calculate_weighted_score(task)
        
        elif self.strategy == SchedulingStrategy.ROUND_ROBIN:
            return self._calculate_round_robin_score(task)
        
        else:
            # Default to priority-based
            return task.priority.value
    
    def _calculate_weighted_score(self, task: Task) -> float:
        """Calculate a weighted priority score considering multiple factors."""
        score = 0.0
        
        # Priority weight (40%)
        priority_weight = 0.4
        priority_score = task.priority.value / 5.0  # Normalize to 0-1
        score += priority_weight * priority_score
        
        # Deadline urgency weight (30%)
        deadline_weight = 0.3
        if task.deadline:
            time_to_deadline = (task.deadline - datetime.utcnow()).total_seconds()
            if time_to_deadline > 0:
                # Normalize based on 24 hours
                deadline_urgency = max(0, 1 - (time_to_deadline / 86400))
                score += deadline_weight * (1 - deadline_urgency)  # Invert for priority
            else:
                # Overdue tasks get highest priority
                score -= 1.0
        else:
            score += deadline_weight * 0.5  # Neutral score for no deadline
        
        # Duration weight (20%) - shorter tasks get higher priority
        duration_weight = 0.2
        if task.estimated_duration:
            # Normalize based on 4 hours
            duration_score = min(1.0, task.estimated_duration.total_seconds() / 14400)
            score += duration_weight * duration_score
        else:
            score += duration_weight * 0.5  # Neutral score for unknown duration
        
        # Age weight (10%) - older tasks get slightly higher priority
        age_weight = 0.1
        age_hours = (datetime.utcnow() - task.created_at).total_seconds() / 3600
        age_score = min(1.0, age_hours / 24)  # Normalize to 24 hours
        score += age_weight * (1 - age_score)  # Invert for priority
        
        return score
    
    def _calculate_round_robin_score(self, task: Task) -> float:
        """Calculate score for round-robin scheduling by task type."""
        task_type = task.task_type.value
        
        # Get current count for this task type
        current_count = self._task_type_counts.get(task_type, 0)
        
        # Base score on task type rotation and priority
        type_score = (current_count % 100) / 100.0  # Normalize type rotation
        priority_score = task.priority.value / 10.0  # Secondary priority factor
        
        return type_score + priority_score
    
    def _update_strategy_state(self, task: Task) -> None:
        """Update strategy-specific state when a task is scheduled."""
        if self.strategy == SchedulingStrategy.ROUND_ROBIN:
            task_type = task.task_type.value
            self._task_type_counts[task_type] = self._task_type_counts.get(task_type, 0) + 1
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about the current scheduling strategy."""
        info = {
            "strategy": self.strategy.value,
            "queue_size": self.get_queue_size(),
        }
        
        if self.strategy == SchedulingStrategy.ROUND_ROBIN:
            info["task_type_counts"] = self._task_type_counts.copy()
        
        return info
    
    def optimize_queue(self) -> None:
        """Perform queue optimization based on current conditions."""
        with self._lock:
            if not self._queue:
                return
            
            # Recalculate all priority scores
            for scheduled_task in self._queue:
                if scheduled_task.task.id in self._task_index:
                    new_score = self._calculate_priority_score(scheduled_task.task)
                    scheduled_task.priority_score = new_score
            
            # Rebuild heap
            heapq.heapify(self._queue)
            
            logger.debug("Queue optimization completed")
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about the current queue."""
        with self._lock:
            if not self._queue:
                return {"total_tasks": 0}
            
            tasks = [st.task for st in self._task_index.values()]
            
            # Priority distribution
            priority_counts = {}
            for priority in TaskPriority:
                priority_counts[priority.value] = sum(1 for t in tasks if t.priority == priority)
            
            # Task type distribution
            type_counts = {}
            for task in tasks:
                task_type = task.task_type.value
                type_counts[task_type] = type_counts.get(task_type, 0) + 1
            
            # Timing statistics
            now = datetime.utcnow()
            ages = [(now - t.created_at).total_seconds() for t in tasks]
            
            stats = {
                "total_tasks": len(tasks),
                "priority_distribution": priority_counts,
                "task_type_distribution": type_counts,
                "average_age_seconds": sum(ages) / len(ages) if ages else 0,
                "oldest_task_age_seconds": max(ages) if ages else 0,
                "tasks_with_deadlines": sum(1 for t in tasks if t.deadline),
                "overdue_tasks": sum(1 for t in tasks if t.deadline and t.deadline < now),
            }
            
            return stats

