"""
Task scheduling and prioritization engine
"""

import heapq
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import UUID

from ..models.task import Task, TaskPriority, TaskStatus
from .dependency_resolver import DependencyResolver


class TaskScheduler:
    """
    Priority-based task scheduling engine
    
    Features:
    - Priority-based task scheduling
    - Resource-aware scheduling
    - Load balancing across agents
    - Deadline-aware scheduling
    - Fair scheduling algorithms
    """
    
    def __init__(self, dependency_resolver: DependencyResolver):
        self.dependency_resolver = dependency_resolver
        self.task_queue: List[tuple] = []  # Priority queue: (priority, timestamp, task_id)
        self.scheduled_tasks: Dict[UUID, Task] = {}
        self.agent_workloads: Dict[str, int] = {}  # agent_id -> current task count
        self.agent_capabilities: Dict[str, Set[str]] = {}  # agent_id -> set of task types
        
    def add_task(self, task: Task) -> None:
        """Add task to scheduler"""
        self.dependency_resolver.add_task(task)
        self.scheduled_tasks[task.id] = task
        
        # Add to priority queue if ready to run
        if task.status == TaskStatus.PENDING:
            self._enqueue_task(task)
    
    def remove_task(self, task_id: UUID) -> None:
        """Remove task from scheduler"""
        self.dependency_resolver.remove_task(task_id)
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
        
        # Remove from queue (will be filtered out during dequeue)
    
    def update_task_status(self, task_id: UUID, status: TaskStatus) -> None:
        """Update task status and reschedule if needed"""
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            old_status = task.status
            task.update_status(status)
            
            # Update dependency resolver
            self.dependency_resolver.update_task(task)
            
            # If task completed, check for newly ready tasks
            if status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
                self._check_and_enqueue_ready_tasks()
            
            # Update agent workload
            if task.assigned_to and status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                self._decrease_agent_workload(task.assigned_to)
    
    def register_agent(self, agent_id: str, capabilities: Set[str]) -> None:
        """Register an agent with its capabilities"""
        self.agent_capabilities[agent_id] = capabilities
        if agent_id not in self.agent_workloads:
            self.agent_workloads[agent_id] = 0
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.agent_capabilities:
            del self.agent_capabilities[agent_id]
        if agent_id in self.agent_workloads:
            del self.agent_workloads[agent_id]
    
    def get_next_task(self, agent_id: Optional[str] = None) -> Optional[Task]:
        """
        Get next task to execute
        
        Args:
            agent_id: Specific agent requesting task (for capability matching)
        
        Returns:
            Next task to execute or None if no tasks available
        """
        while self.task_queue:
            priority, timestamp, task_id = heapq.heappop(self.task_queue)
            
            # Check if task still exists and is pending
            if task_id not in self.scheduled_tasks:
                continue
            
            task = self.scheduled_tasks[task_id]
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if task is ready to run (dependencies satisfied)
            completed_tasks = self._get_completed_tasks()
            if not task.is_ready_to_run(completed_tasks):
                # Re-enqueue for later
                self._enqueue_task(task)
                continue
            
            # Check agent capabilities if agent specified
            if agent_id and not self._can_agent_execute_task(agent_id, task):
                # Re-enqueue for other agents
                self._enqueue_task(task)
                continue
            
            # Assign task to agent if specified
            if agent_id:
                task.assigned_to = agent_id
                self._increase_agent_workload(agent_id)
            
            return task
        
        return None
    
    def get_tasks_for_agent(self, agent_id: str, max_tasks: int = 1) -> List[Task]:
        """
        Get multiple tasks for an agent (for batch processing)
        
        Args:
            agent_id: Agent requesting tasks
            max_tasks: Maximum number of tasks to return
        
        Returns:
            List of tasks for the agent
        """
        tasks = []
        for _ in range(max_tasks):
            task = self.get_next_task(agent_id)
            if task:
                tasks.append(task)
            else:
                break
        return tasks
    
    def schedule_task_at(self, task_id: UUID, scheduled_time: datetime) -> bool:
        """
        Schedule task for specific time
        
        Args:
            task_id: Task to schedule
            scheduled_time: When to schedule the task
        
        Returns:
            True if successfully scheduled
        """
        if task_id not in self.scheduled_tasks:
            return False
        
        task = self.scheduled_tasks[task_id]
        task.scheduled_at = scheduled_time
        
        # If scheduled time is in the future, don't enqueue yet
        if scheduled_time > datetime.utcnow():
            return True
        
        # If scheduled time is now or past, enqueue immediately
        if task.status == TaskStatus.PENDING:
            self._enqueue_task(task)
        
        return True
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get tasks that are overdue"""
        overdue_tasks = []
        for task in self.scheduled_tasks.values():
            if task.is_overdue():
                overdue_tasks.append(task)
        return overdue_tasks
    
    def get_scheduled_tasks(self) -> List[Task]:
        """Get tasks scheduled for future execution"""
        now = datetime.utcnow()
        scheduled_tasks = []
        for task in self.scheduled_tasks.values():
            if (task.scheduled_at and 
                task.scheduled_at > now and 
                task.status == TaskStatus.PENDING):
                scheduled_tasks.append(task)
        return scheduled_tasks
    
    def get_agent_workload(self, agent_id: str) -> int:
        """Get current workload for an agent"""
        return self.agent_workloads.get(agent_id, 0)
    
    def get_least_loaded_agent(self, task_type: Optional[str] = None) -> Optional[str]:
        """
        Get the least loaded agent capable of handling the task type
        
        Args:
            task_type: Type of task (for capability matching)
        
        Returns:
            Agent ID of least loaded capable agent
        """
        capable_agents = []
        
        for agent_id, capabilities in self.agent_capabilities.items():
            if task_type is None or task_type in capabilities:
                workload = self.agent_workloads.get(agent_id, 0)
                capable_agents.append((workload, agent_id))
        
        if not capable_agents:
            return None
        
        # Return agent with minimum workload
        capable_agents.sort()
        return capable_agents[0][1]
    
    def rebalance_tasks(self) -> Dict[str, List[UUID]]:
        """
        Rebalance tasks across agents for optimal load distribution
        
        Returns:
            Dictionary mapping agent_id to list of task_ids to reassign
        """
        reassignments = {}
        
        # Get all pending tasks
        pending_tasks = [
            task for task in self.scheduled_tasks.values()
            if task.status == TaskStatus.PENDING and task.assigned_to
        ]
        
        if not pending_tasks:
            return reassignments
        
        # Calculate target workload per agent
        total_tasks = len(pending_tasks)
        num_agents = len(self.agent_capabilities)
        
        if num_agents == 0:
            return reassignments
        
        target_workload = total_tasks // num_agents
        
        # Find overloaded and underloaded agents
        overloaded_agents = []
        underloaded_agents = []
        
        for agent_id in self.agent_capabilities:
            workload = self.agent_workloads.get(agent_id, 0)
            if workload > target_workload:
                overloaded_agents.append((workload - target_workload, agent_id))
            elif workload < target_workload:
                underloaded_agents.append((target_workload - workload, agent_id))
        
        # Sort by excess/deficit
        overloaded_agents.sort(reverse=True)
        underloaded_agents.sort(reverse=True)
        
        # Reassign tasks from overloaded to underloaded agents
        for excess, overloaded_agent in overloaded_agents:
            agent_tasks = [
                task for task in pending_tasks
                if task.assigned_to == overloaded_agent
            ]
            
            # Sort by priority (lower priority tasks reassigned first)
            agent_tasks.sort(key=lambda t: t.priority.value)
            
            tasks_to_reassign = agent_tasks[:excess]
            
            for task in tasks_to_reassign:
                # Find suitable underloaded agent
                suitable_agent = None
                for deficit, underloaded_agent in underloaded_agents:
                    if (deficit > 0 and 
                        self._can_agent_execute_task(underloaded_agent, task)):
                        suitable_agent = underloaded_agent
                        break
                
                if suitable_agent:
                    if suitable_agent not in reassignments:
                        reassignments[suitable_agent] = []
                    reassignments[suitable_agent].append(task.id)
                    
                    # Update workloads
                    self._decrease_agent_workload(overloaded_agent)
                    self._increase_agent_workload(suitable_agent)
                    
                    # Update deficit
                    for i, (deficit, agent) in enumerate(underloaded_agents):
                        if agent == suitable_agent:
                            underloaded_agents[i] = (deficit - 1, agent)
                            break
        
        return reassignments
    
    def get_queue_statistics(self) -> Dict[str, any]:
        """Get queue statistics"""
        total_tasks = len(self.scheduled_tasks)
        pending_tasks = sum(1 for t in self.scheduled_tasks.values() if t.status == TaskStatus.PENDING)
        running_tasks = sum(1 for t in self.scheduled_tasks.values() if t.status == TaskStatus.RUNNING)
        completed_tasks = sum(1 for t in self.scheduled_tasks.values() if t.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for t in self.scheduled_tasks.values() if t.status == TaskStatus.FAILED)
        
        # Priority distribution
        priority_dist = {}
        for priority in TaskPriority:
            priority_dist[priority.name] = sum(
                1 for t in self.scheduled_tasks.values() 
                if t.priority == priority and t.status == TaskStatus.PENDING
            )
        
        return {
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "running_tasks": running_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "queue_length": len(self.task_queue),
            "priority_distribution": priority_dist,
            "agent_workloads": dict(self.agent_workloads),
            "overdue_tasks": len(self.get_overdue_tasks()),
        }
    
    def _enqueue_task(self, task: Task) -> None:
        """Add task to priority queue"""
        # Priority is negative for min-heap (higher priority = lower number)
        priority = -task.priority.value
        
        # Add deadline urgency
        if task.deadline:
            time_to_deadline = (task.deadline - datetime.utcnow()).total_seconds()
            if time_to_deadline < 3600:  # Less than 1 hour
                priority -= 10  # Boost priority
            elif time_to_deadline < 86400:  # Less than 1 day
                priority -= 5
        
        # Use creation time as tiebreaker
        timestamp = task.created_at.timestamp()
        
        heapq.heappush(self.task_queue, (priority, timestamp, task.id))
    
    def _check_and_enqueue_ready_tasks(self) -> None:
        """Check for newly ready tasks and enqueue them"""
        completed_tasks = self._get_completed_tasks()
        
        for task in self.scheduled_tasks.values():
            if (task.status == TaskStatus.PENDING and 
                task.is_ready_to_run(completed_tasks)):
                # Check if already in queue
                if not any(task_id == task.id for _, _, task_id in self.task_queue):
                    self._enqueue_task(task)
    
    def _get_completed_tasks(self) -> Set[UUID]:
        """Get set of completed task IDs"""
        return {
            task_id for task_id, task in self.scheduled_tasks.items()
            if task.status == TaskStatus.COMPLETED
        }
    
    def _can_agent_execute_task(self, agent_id: str, task: Task) -> bool:
        """Check if agent can execute the task based on capabilities"""
        if agent_id not in self.agent_capabilities:
            return False
        
        agent_caps = self.agent_capabilities[agent_id]
        
        # If no specific task type, any agent can handle it
        if not task.task_type:
            return True
        
        return task.task_type in agent_caps
    
    def _increase_agent_workload(self, agent_id: str) -> None:
        """Increase agent workload"""
        self.agent_workloads[agent_id] = self.agent_workloads.get(agent_id, 0) + 1
    
    def _decrease_agent_workload(self, agent_id: str) -> None:
        """Decrease agent workload"""
        if agent_id in self.agent_workloads:
            self.agent_workloads[agent_id] = max(0, self.agent_workloads[agent_id] - 1)

