"""
Multi-agent task execution engine
"""

import asyncio
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID

from ..models.execution import ExecutionStatus, ResourceUsage, TaskExecution
from ..models.task import Task, TaskStatus
from ..monitoring.logger import TaskLogger
from ..monitoring.metrics import TaskMetrics


class TaskExecutor:
    """
    Multi-agent task execution engine
    
    Features:
    - Multi-agent task execution (Codegen, Claude, Task Manager)
    - Resource usage monitoring and optimization
    - Execution result storage and analysis
    - Error handling and retry mechanisms
    - Concurrent task execution
    """
    
    def __init__(self, 
                 max_concurrent_tasks: int = 10,
                 resource_monitor_interval: float = 1.0,
                 logger: Optional[TaskLogger] = None,
                 metrics: Optional[TaskMetrics] = None):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.resource_monitor_interval = resource_monitor_interval
        self.logger = logger or TaskLogger()
        self.metrics = metrics or TaskMetrics()
        
        # Execution tracking
        self.running_executions: Dict[UUID, TaskExecution] = {}
        self.execution_history: Dict[UUID, List[TaskExecution]] = {}
        
        # Agent registry
        self.agents: Dict[str, Dict[str, Any]] = {}  # agent_id -> agent_info
        self.agent_executors: Dict[str, Callable] = {}  # agent_id -> executor_function
        
        # Resource monitoring
        self.resource_monitor_active = False
        self.resource_monitor_thread: Optional[threading.Thread] = None
        
        # Execution control
        self.shutdown_event = threading.Event()
        self.execution_semaphore = threading.Semaphore(max_concurrent_tasks)
    
    def register_agent(self, 
                      agent_id: str, 
                      agent_type: str,
                      executor_function: Callable,
                      capabilities: Set[str] = None,
                      metadata: Dict[str, Any] = None) -> None:
        """
        Register an agent executor
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (codegen, claude, task_manager, etc.)
            executor_function: Function to execute tasks
            capabilities: Set of task types the agent can handle
            metadata: Additional agent metadata
        """
        self.agents[agent_id] = {
            "type": agent_type,
            "capabilities": capabilities or set(),
            "metadata": metadata or {},
            "registered_at": datetime.utcnow(),
            "active": True
        }
        self.agent_executors[agent_id] = executor_function
        
        self.logger.log_info(f"Registered agent {agent_id} of type {agent_type}")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.agents:
            self.agents[agent_id]["active"] = False
            del self.agents[agent_id]
        
        if agent_id in self.agent_executors:
            del self.agent_executors[agent_id]
        
        self.logger.log_info(f"Unregistered agent {agent_id}")
    
    def start_resource_monitoring(self) -> None:
        """Start resource monitoring thread"""
        if not self.resource_monitor_active:
            self.resource_monitor_active = True
            self.resource_monitor_thread = threading.Thread(
                target=self._resource_monitor_loop,
                daemon=True
            )
            self.resource_monitor_thread.start()
            self.logger.log_info("Started resource monitoring")
    
    def stop_resource_monitoring(self) -> None:
        """Stop resource monitoring"""
        self.resource_monitor_active = False
        if self.resource_monitor_thread:
            self.resource_monitor_thread.join(timeout=5.0)
        self.logger.log_info("Stopped resource monitoring")
    
    async def execute_task(self, task: Task, agent_id: Optional[str] = None) -> TaskExecution:
        """
        Execute a task
        
        Args:
            task: Task to execute
            agent_id: Specific agent to use (if None, selects best available)
        
        Returns:
            TaskExecution with results
        """
        # Select agent if not specified
        if not agent_id:
            agent_id = self._select_best_agent(task)
        
        if not agent_id or agent_id not in self.agent_executors:
            raise ValueError(f"No suitable agent available for task {task.id}")
        
        # Create execution record
        execution_number = len(self.execution_history.get(task.id, [])) + 1
        execution = TaskExecution(
            task_id=task.id,
            execution_number=execution_number,
            executor_id=agent_id,
            executor_type=self.agents[agent_id]["type"]
        )
        
        # Store execution
        self.running_executions[execution.id] = execution
        if task.id not in self.execution_history:
            self.execution_history[task.id] = []
        self.execution_history[task.id].append(execution)
        
        try:
            # Acquire execution semaphore
            await asyncio.get_event_loop().run_in_executor(
                None, self.execution_semaphore.acquire
            )
            
            # Start execution
            execution.start_execution()
            task.update_status(TaskStatus.RUNNING)
            
            self.logger.log_info(f"Starting execution {execution.id} for task {task.id} on agent {agent_id}")
            self.metrics.record_task_started(task.id, agent_id)
            
            # Execute task
            executor_func = self.agent_executors[agent_id]
            
            try:
                execution.mark_running()
                
                # Execute with timeout if specified
                if task.timeout_seconds:
                    result = await asyncio.wait_for(
                        self._execute_with_agent(executor_func, task, execution),
                        timeout=task.timeout_seconds
                    )
                else:
                    result = await self._execute_with_agent(executor_func, task, execution)
                
                # Complete execution
                execution.complete_execution(result)
                task.update_status(TaskStatus.COMPLETED)
                task.result = result
                
                self.logger.log_info(f"Completed execution {execution.id} for task {task.id}")
                self.metrics.record_task_completed(task.id, execution.execution_time_seconds or 0)
                
            except asyncio.TimeoutError:
                execution.timeout_execution()
                task.update_status(TaskStatus.FAILED, "Task execution timed out")
                
                self.logger.log_error(f"Execution {execution.id} timed out for task {task.id}")
                self.metrics.record_task_failed(task.id, "timeout")
                
            except Exception as e:
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                execution.fail_execution(error_details)
                task.update_status(TaskStatus.FAILED, str(e))
                
                self.logger.log_error(f"Execution {execution.id} failed for task {task.id}: {e}")
                self.metrics.record_task_failed(task.id, "execution_error")
                
                # Check if task can be retried
                if task.can_retry():
                    task.increment_retry()
                    execution.retry_reason = f"Retry {task.retry_count}/{task.max_retries}: {str(e)}"
                    self.logger.log_info(f"Task {task.id} will be retried ({task.retry_count}/{task.max_retries})")
        
        finally:
            # Release semaphore and cleanup
            self.execution_semaphore.release()
            if execution.id in self.running_executions:
                del self.running_executions[execution.id]
        
        return execution
    
    async def execute_tasks_batch(self, tasks: List[Task], agent_id: Optional[str] = None) -> List[TaskExecution]:
        """
        Execute multiple tasks concurrently
        
        Args:
            tasks: List of tasks to execute
            agent_id: Specific agent to use for all tasks
        
        Returns:
            List of TaskExecution results
        """
        execution_tasks = []
        
        for task in tasks:
            execution_task = asyncio.create_task(
                self.execute_task(task, agent_id)
            )
            execution_tasks.append(execution_task)
        
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        # Convert exceptions to failed executions
        executions = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create failed execution
                task = tasks[i]
                execution = TaskExecution(
                    task_id=task.id,
                    execution_number=len(self.execution_history.get(task.id, [])) + 1,
                    executor_id=agent_id or "unknown",
                    executor_type="unknown"
                )
                execution.fail_execution({
                    "error_type": type(result).__name__,
                    "error_message": str(result),
                    "timestamp": datetime.utcnow().isoformat()
                })
                executions.append(execution)
            else:
                executions.append(result)
        
        return executions
    
    def cancel_task_execution(self, task_id: UUID, reason: Optional[str] = None) -> bool:
        """
        Cancel running task execution
        
        Args:
            task_id: Task to cancel
            reason: Cancellation reason
        
        Returns:
            True if task was cancelled
        """
        # Find running execution for task
        execution = None
        for exec_id, exec_obj in self.running_executions.items():
            if exec_obj.task_id == task_id:
                execution = exec_obj
                break
        
        if not execution:
            return False
        
        execution.cancel_execution(reason)
        self.logger.log_info(f"Cancelled execution {execution.id} for task {task_id}: {reason}")
        self.metrics.record_task_cancelled(task_id)
        
        return True
    
    def get_execution_status(self, task_id: UUID) -> Optional[TaskExecution]:
        """Get current execution status for a task"""
        # Check running executions first
        for execution in self.running_executions.values():
            if execution.task_id == task_id:
                return execution
        
        # Check execution history
        if task_id in self.execution_history:
            executions = self.execution_history[task_id]
            if executions:
                return executions[-1]  # Return latest execution
        
        return None
    
    def get_agent_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all agents"""
        stats = {}
        
        for agent_id, agent_info in self.agents.items():
            # Count running tasks for this agent
            running_tasks = sum(
                1 for execution in self.running_executions.values()
                if execution.executor_id == agent_id
            )
            
            # Count total executions for this agent
            total_executions = sum(
                len([e for e in executions if e.executor_id == agent_id])
                for executions in self.execution_history.values()
            )
            
            # Calculate success rate
            successful_executions = sum(
                len([e for e in executions if e.executor_id == agent_id and e.is_successful()])
                for executions in self.execution_history.values()
            )
            
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            stats[agent_id] = {
                "type": agent_info["type"],
                "active": agent_info["active"],
                "running_tasks": running_tasks,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": round(success_rate, 2),
                "capabilities": list(agent_info["capabilities"]),
                "registered_at": agent_info["registered_at"].isoformat()
            }
        
        return stats
    
    def shutdown(self) -> None:
        """Shutdown executor and cleanup resources"""
        self.shutdown_event.set()
        self.stop_resource_monitoring()
        
        # Cancel all running executions
        for execution in list(self.running_executions.values()):
            execution.cancel_execution("Executor shutdown")
        
        self.logger.log_info("Task executor shutdown complete")
    
    def _select_best_agent(self, task: Task) -> Optional[str]:
        """Select best available agent for task"""
        suitable_agents = []
        
        for agent_id, agent_info in self.agents.items():
            if not agent_info["active"]:
                continue
            
            # Check capabilities
            if task.task_type and task.task_type not in agent_info["capabilities"]:
                continue
            
            # Count current workload
            running_tasks = sum(
                1 for execution in self.running_executions.values()
                if execution.executor_id == agent_id
            )
            
            suitable_agents.append((running_tasks, agent_id))
        
        if not suitable_agents:
            return None
        
        # Return agent with lowest workload
        suitable_agents.sort()
        return suitable_agents[0][1]
    
    async def _execute_with_agent(self, executor_func: Callable, task: Task, execution: TaskExecution) -> Any:
        """Execute task with specific agent"""
        # Add execution context
        context = {
            "execution_id": str(execution.id),
            "task_id": str(task.id),
            "agent_id": execution.executor_id,
            "metadata": task.metadata,
            "execution_context": task.execution_context
        }
        
        # Execute task
        if asyncio.iscoroutinefunction(executor_func):
            result = await executor_func(task, context)
        else:
            # Run synchronous function in thread pool
            result = await asyncio.get_event_loop().run_in_executor(
                None, executor_func, task, context
            )
        
        return result
    
    def _resource_monitor_loop(self) -> None:
        """Resource monitoring loop"""
        while self.resource_monitor_active and not self.shutdown_event.is_set():
            try:
                # Monitor resources for all running executions
                for execution in list(self.running_executions.values()):
                    if execution.status == ExecutionStatus.RUNNING:
                        usage = self._get_resource_usage(execution)
                        if usage:
                            execution.update_resource_usage(usage)
                
                time.sleep(self.resource_monitor_interval)
                
            except Exception as e:
                self.logger.log_error(f"Resource monitoring error: {e}")
                time.sleep(self.resource_monitor_interval)
    
    def _get_resource_usage(self, execution: TaskExecution) -> Optional[ResourceUsage]:
        """Get current resource usage for execution"""
        try:
            import psutil
            
            # This is a simplified implementation
            # In practice, you'd track the specific process/container for the execution
            process = psutil.Process()
            
            return ResourceUsage(
                cpu_percent=process.cpu_percent(),
                memory_mb=process.memory_info().rss / 1024 / 1024,
                # Add more resource metrics as needed
            )
        except ImportError:
            # psutil not available
            return None
        except Exception:
            # Error getting resource usage
            return None

