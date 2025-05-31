"""
RESTful API for task operations
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field

from ..engines.dependency_resolver import DependencyResolver
from ..engines.executor import TaskExecutor
from ..engines.scheduler import TaskScheduler
from ..engines.workflow_orchestrator import WorkflowOrchestrator
from ..models.execution import TaskExecution
from ..models.task import Task, TaskPriority, TaskStatus, TaskType
from ..models.workflow import Workflow
from ..monitoring.logger import TaskLogger
from ..monitoring.metrics import TaskMetrics


class CreateTaskRequest(BaseModel):
    """Request model for creating a task"""
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    task_type: TaskType = Field(default=TaskType.CUSTOM, description="Task type")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Task priority")
    created_by: str = Field(..., description="Task creator")
    depends_on: Set[UUID] = Field(default_factory=set, description="Task dependencies")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Task metadata")
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: Optional[int] = Field(None, description="Task timeout")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    tags: Set[str] = Field(default_factory=set, description="Task tags")


class UpdateTaskRequest(BaseModel):
    """Request model for updating a task"""
    name: Optional[str] = Field(None, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    assigned_to: Optional[str] = Field(None, description="Assigned agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Task metadata")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    tags: Optional[Set[str]] = Field(None, description="Task tags")


class TaskResponse(BaseModel):
    """Response model for task operations"""
    id: UUID
    name: str
    description: Optional[str]
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    created_by: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    deadline: Optional[datetime]
    depends_on: Set[UUID]
    blocks: Set[UUID]
    metadata: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    tags: Set[str]


class ExecutionResponse(BaseModel):
    """Response model for task execution"""
    id: UUID
    task_id: UUID
    execution_number: int
    executor_id: str
    executor_type: str
    status: str
    queued_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time_seconds: Optional[float]
    result: Optional[Dict[str, Any]]
    error_details: Optional[Dict[str, Any]]


class TaskAPI:
    """
    RESTful API for task operations
    
    Features:
    - Complete task CRUD operations
    - Task execution management
    - Workflow operations
    - Performance monitoring
    - Agent management
    """
    
    def __init__(self):
        # Initialize core components
        self.dependency_resolver = DependencyResolver()
        self.task_scheduler = TaskScheduler(self.dependency_resolver)
        self.task_executor = TaskExecutor()
        self.workflow_orchestrator = WorkflowOrchestrator(
            self.task_executor, 
            self.task_scheduler
        )
        self.logger = TaskLogger()
        self.metrics = TaskMetrics()
        
        # Start monitoring
        self.task_executor.start_resource_monitoring()
    
    # Task Management Operations
    
    async def create_task(self, request: CreateTaskRequest) -> TaskResponse:
        """Create a new task"""
        # Create task
        task = Task(
            name=request.name,
            description=request.description,
            task_type=request.task_type,
            priority=request.priority,
            created_by=request.created_by,
            depends_on=request.depends_on,
            metadata=request.metadata,
            execution_context=request.execution_context,
            resource_requirements=request.resource_requirements,
            max_retries=request.max_retries,
            timeout_seconds=request.timeout_seconds,
            deadline=request.deadline,
            tags=request.tags,
        )
        
        # Validate dependencies
        validation_errors = self.dependency_resolver.validate_dependencies(task)
        if validation_errors:
            raise ValueError(f"Dependency validation failed: {validation_errors}")
        
        # Add to scheduler
        self.task_scheduler.add_task(task)
        
        # Log task creation
        self.logger.log_task_created(task.id, task.name, task.created_by, task.metadata)
        
        return self._task_to_response(task)
    
    async def get_task(self, task_id: UUID) -> Optional[TaskResponse]:
        """Get task by ID"""
        if task_id in self.task_scheduler.scheduled_tasks:
            task = self.task_scheduler.scheduled_tasks[task_id]
            return self._task_to_response(task)
        return None
    
    async def update_task(self, task_id: UUID, request: UpdateTaskRequest) -> Optional[TaskResponse]:
        """Update task"""
        if task_id not in self.task_scheduler.scheduled_tasks:
            return None
        
        task = self.task_scheduler.scheduled_tasks[task_id]
        
        # Update fields
        if request.name is not None:
            task.name = request.name
        if request.description is not None:
            task.description = request.description
        if request.priority is not None:
            task.priority = request.priority
        if request.assigned_to is not None:
            task.assigned_to = request.assigned_to
        if request.metadata is not None:
            task.metadata.update(request.metadata)
        if request.deadline is not None:
            task.deadline = request.deadline
        if request.tags is not None:
            task.tags = request.tags
        
        task.updated_at = datetime.utcnow()
        
        # Update in scheduler
        self.dependency_resolver.update_task(task)
        
        return self._task_to_response(task)
    
    async def delete_task(self, task_id: UUID) -> bool:
        """Delete task"""
        if task_id not in self.task_scheduler.scheduled_tasks:
            return False
        
        # Cancel if running
        self.task_executor.cancel_task_execution(task_id, "Task deleted")
        
        # Remove from scheduler
        self.task_scheduler.remove_task(task_id)
        
        return True
    
    async def list_tasks(self, 
                        status: Optional[TaskStatus] = None,
                        assigned_to: Optional[str] = None,
                        task_type: Optional[TaskType] = None,
                        priority: Optional[TaskPriority] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[TaskResponse]:
        """List tasks with filtering"""
        tasks = list(self.task_scheduler.scheduled_tasks.values())
        
        # Apply filters
        if status:
            tasks = [t for t in tasks if t.status == status]
        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        
        # Apply pagination
        tasks = tasks[offset:offset + limit]
        
        return [self._task_to_response(task) for task in tasks]
    
    # Task Execution Operations
    
    async def execute_task(self, task_id: UUID, agent_id: Optional[str] = None) -> ExecutionResponse:
        """Execute a task"""
        if task_id not in self.task_scheduler.scheduled_tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.task_scheduler.scheduled_tasks[task_id]
        
        # Execute task
        execution = await self.task_executor.execute_task(task, agent_id)
        
        # Update task status in scheduler
        if execution.is_successful():
            self.task_scheduler.update_task_status(task_id, TaskStatus.COMPLETED)
        else:
            self.task_scheduler.update_task_status(task_id, TaskStatus.FAILED)
        
        return self._execution_to_response(execution)
    
    async def cancel_task_execution(self, task_id: UUID, reason: Optional[str] = None) -> bool:
        """Cancel task execution"""
        success = self.task_executor.cancel_task_execution(task_id, reason)
        if success:
            self.task_scheduler.update_task_status(task_id, TaskStatus.CANCELLED)
        return success
    
    async def get_task_execution(self, task_id: UUID) -> Optional[ExecutionResponse]:
        """Get task execution status"""
        execution = self.task_executor.get_execution_status(task_id)
        if execution:
            return self._execution_to_response(execution)
        return None
    
    async def retry_task(self, task_id: UUID) -> Optional[ExecutionResponse]:
        """Retry a failed task"""
        if task_id not in self.task_scheduler.scheduled_tasks:
            return None
        
        task = self.task_scheduler.scheduled_tasks[task_id]
        
        if not task.can_retry():
            raise ValueError(f"Task {task_id} cannot be retried")
        
        # Reset task status and increment retry count
        task.increment_retry()
        task.update_status(TaskStatus.PENDING)
        
        # Re-add to scheduler
        self.task_scheduler.add_task(task)
        
        # Execute task
        return await self.execute_task(task_id)
    
    # Workflow Operations
    
    async def execute_workflow(self, workflow: Workflow) -> Workflow:
        """Execute a workflow"""
        return await self.workflow_orchestrator.execute_workflow(workflow)
    
    async def pause_workflow(self, workflow_id: UUID) -> bool:
        """Pause workflow execution"""
        return await self.workflow_orchestrator.pause_workflow(workflow_id)
    
    async def resume_workflow(self, workflow_id: UUID) -> bool:
        """Resume workflow execution"""
        return await self.workflow_orchestrator.resume_workflow(workflow_id)
    
    async def cancel_workflow(self, workflow_id: UUID) -> bool:
        """Cancel workflow execution"""
        return await self.workflow_orchestrator.cancel_workflow(workflow_id)
    
    async def get_workflow_status(self, workflow_id: UUID) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        return self.workflow_orchestrator.get_workflow_status(workflow_id)
    
    # Agent Management Operations
    
    async def register_agent(self, 
                           agent_id: str, 
                           agent_type: str,
                           capabilities: Set[str] = None) -> bool:
        """Register an agent"""
        # This would need to be implemented with actual agent executor functions
        # For now, just register with scheduler
        self.task_scheduler.register_agent(agent_id, capabilities or set())
        self.logger.log_agent_registered(agent_id, agent_type, list(capabilities or []))
        return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        self.task_scheduler.unregister_agent(agent_id)
        self.task_executor.unregister_agent(agent_id)
        self.logger.log_agent_unregistered(agent_id)
        return True
    
    async def get_agent_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get agent statistics"""
        return self.task_executor.get_agent_statistics()
    
    # Monitoring and Analytics Operations
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return self.metrics.get_current_metrics()
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return self.metrics.generate_performance_report()
    
    async def get_queue_statistics(self) -> Dict[str, Any]:
        """Get task queue statistics"""
        return self.task_scheduler.get_queue_statistics()
    
    async def get_dependency_graph(self) -> Dict[str, Any]:
        """Get task dependency graph"""
        return self.dependency_resolver.get_dependency_graph()
    
    async def get_execution_plan(self, task_ids: Optional[Set[UUID]] = None) -> Dict[str, Any]:
        """Get optimized execution plan"""
        return self.dependency_resolver.optimize_execution_plan(task_ids)
    
    # Utility Operations
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "dependency_resolver": "healthy",
                "task_scheduler": "healthy", 
                "task_executor": "healthy",
                "workflow_orchestrator": "healthy",
            },
            "metrics": await self.get_system_metrics()
        }
    
    async def shutdown(self) -> None:
        """Shutdown API and cleanup resources"""
        self.task_executor.shutdown()
        self.logger.log_info("Task Management API shutdown complete")
    
    # Helper Methods
    
    def _task_to_response(self, task: Task) -> TaskResponse:
        """Convert Task to TaskResponse"""
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type,
            status=task.status,
            priority=task.priority,
            created_by=task.created_by,
            assigned_to=task.assigned_to,
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            deadline=task.deadline,
            depends_on=task.depends_on,
            blocks=task.blocks,
            metadata=task.metadata,
            result=task.result,
            error_message=task.error_message,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            tags=task.tags,
        )
    
    def _execution_to_response(self, execution: TaskExecution) -> ExecutionResponse:
        """Convert TaskExecution to ExecutionResponse"""
        return ExecutionResponse(
            id=execution.id,
            task_id=execution.task_id,
            execution_number=execution.execution_number,
            executor_id=execution.executor_id,
            executor_type=execution.executor_type,
            status=execution.status,
            queued_at=execution.queued_at,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            execution_time_seconds=execution.execution_time_seconds,
            result=execution.result,
            error_details=execution.error_details,
        )

