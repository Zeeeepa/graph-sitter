"""Workflow Orchestrator for the unified extension system.

This module provides workflow orchestration capabilities that enable
complex multi-extension workflows with parallel and sequential execution,
error handling, and state management.
"""

import asyncio
import logging
import json
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
import uuid

from pydantic import BaseModel, Field

from .extension_base import ExtensionEvent, ExtensionMessage, ExtensionResponse
from .event_bus import EventBus
from .registry import ExtensionRegistry

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskType(str, Enum):
    """Types of tasks in a workflow."""
    EXTENSION_CALL = "extension_call"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    DELAY = "delay"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class TaskDefinition(BaseModel):
    """Definition of a workflow task."""
    id: str
    name: str
    type: TaskType
    extension: Optional[str] = None  # Extension to call
    method: Optional[str] = None     # Method to call on extension
    parameters: Dict[str, Any] = Field(default_factory=dict)
    condition: Optional[str] = None  # Condition for conditional tasks
    retry_count: int = 0
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    depends_on: List[str] = Field(default_factory=list)  # Task dependencies
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """Definition of a workflow."""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    tasks: List[TaskDefinition]
    variables: Dict[str, Any] = Field(default_factory=dict)
    triggers: List[str] = Field(default_factory=list)  # Event types that trigger this workflow
    timeout: Optional[float] = None
    max_retries: int = 0
    on_failure: Optional[str] = None  # Action on workflow failure
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskExecution(BaseModel):
    """Runtime information for task execution."""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    execution_time_ms: Optional[float] = None


class WorkflowExecution(BaseModel):
    """Runtime information for workflow execution."""
    id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.CREATED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    triggered_by: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    task_executions: Dict[str, TaskExecution] = Field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0


class WorkflowOrchestrator:
    """Orchestrator for managing workflow execution."""

    def __init__(
        self,
        event_bus: EventBus,
        extension_registry: ExtensionRegistry
    ):
        """Initialize workflow orchestrator.
        
        Args:
            event_bus: Event bus for communication
            extension_registry: Extension registry for extension access
        """
        self.event_bus = event_bus
        self.extension_registry = extension_registry
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._running = False
        self._execution_tasks: Dict[str, asyncio.Task] = {}
        
        # Subscribe to events that might trigger workflows
        self.event_bus.subscribe(
            "orchestrator",
            self._handle_trigger_event,
            event_filter=None  # Listen to all events
        )

    async def start(self) -> None:
        """Start the orchestrator."""
        self._running = True
        logger.info("Workflow orchestrator started")

    async def stop(self) -> None:
        """Stop the orchestrator."""
        self._running = False
        
        # Cancel all running executions
        for execution_id, task in self._execution_tasks.items():
            task.cancel()
            logger.info(f"Cancelled workflow execution: {execution_id}")
            
        # Wait for tasks to complete
        if self._execution_tasks:
            await asyncio.gather(*self._execution_tasks.values(), return_exceptions=True)
            
        self._execution_tasks.clear()
        logger.info("Workflow orchestrator stopped")

    def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Register a workflow definition.
        
        Args:
            workflow: Workflow definition to register
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate workflow
            if not self._validate_workflow(workflow):
                return False
                
            self._workflows[workflow.id] = workflow
            logger.info(f"Registered workflow: {workflow.name} ({workflow.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register workflow {workflow.id}: {e}")
            return False

    def unregister_workflow(self, workflow_id: str) -> bool:
        """Unregister a workflow definition.
        
        Args:
            workflow_id: Workflow ID to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        if workflow_id not in self._workflows:
            return False
            
        # Check if workflow has running executions
        running_executions = [
            exec_id for exec_id, execution in self._executions.items()
            if execution.workflow_id == workflow_id and execution.status == WorkflowStatus.RUNNING
        ]
        
        if running_executions:
            logger.error(f"Cannot unregister workflow {workflow_id}, has running executions")
            return False
            
        del self._workflows[workflow_id]
        logger.info(f"Unregistered workflow: {workflow_id}")
        return True

    async def execute_workflow(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
        triggered_by: Optional[str] = None
    ) -> str:
        """Execute a workflow.
        
        Args:
            workflow_id: Workflow ID to execute
            context: Initial context variables
            triggered_by: What triggered this execution
            
        Returns:
            Execution ID
        """
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
            
        workflow = self._workflows[workflow_id]
        execution_id = str(uuid.uuid4())
        
        # Create execution
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            triggered_by=triggered_by,
            context=context or {}
        )
        
        # Initialize task executions
        for task in workflow.tasks:
            execution.task_executions[task.id] = TaskExecution(task_id=task.id)
            
        self._executions[execution_id] = execution
        
        # Start execution task
        task = asyncio.create_task(self._execute_workflow_async(execution_id))
        self._execution_tasks[execution_id] = task
        
        logger.info(f"Started workflow execution: {execution_id} for workflow {workflow_id}")
        return execution_id

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a workflow execution.
        
        Args:
            execution_id: Execution ID to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        if execution_id not in self._executions:
            return False
            
        execution = self._executions[execution_id]
        if execution.status not in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            return False
            
        # Cancel execution task
        if execution_id in self._execution_tasks:
            self._execution_tasks[execution_id].cancel()
            
        # Update status
        execution.status = WorkflowStatus.CANCELLED
        execution.completed_at = datetime.now(UTC)
        
        logger.info(f"Cancelled workflow execution: {execution_id}")
        return True

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Workflow execution if found, None otherwise
        """
        return self._executions.get(execution_id)

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None
    ) -> List[WorkflowExecution]:
        """List workflow executions.
        
        Args:
            workflow_id: Optional workflow ID filter
            status: Optional status filter
            
        Returns:
            List of workflow executions
        """
        executions = list(self._executions.values())
        
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
            
        if status:
            executions = [e for e in executions if e.status == status]
            
        return executions

    def list_workflows(self) -> List[WorkflowDefinition]:
        """List registered workflows.
        
        Returns:
            List of workflow definitions
        """
        return list(self._workflows.values())

    async def _handle_trigger_event(self, event: ExtensionEvent) -> None:
        """Handle events that might trigger workflows.
        
        Args:
            event: Event to handle
        """
        # Find workflows that should be triggered by this event
        for workflow in self._workflows.values():
            if event.type in workflow.triggers:
                try:
                    await self.execute_workflow(
                        workflow.id,
                        context={"trigger_event": event.dict()},
                        triggered_by=f"event:{event.type}"
                    )
                except Exception as e:
                    logger.error(f"Failed to trigger workflow {workflow.id}: {e}")

    async def _execute_workflow_async(self, execution_id: str) -> None:
        """Execute workflow asynchronously.
        
        Args:
            execution_id: Execution ID
        """
        execution = self._executions[execution_id]
        workflow = self._workflows[execution.workflow_id]
        
        try:
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.now(UTC)
            
            # Execute tasks based on dependencies
            await self._execute_tasks(workflow, execution)
            
            # Check if all tasks completed successfully
            failed_tasks = [
                task_exec for task_exec in execution.task_executions.values()
                if task_exec.status == TaskStatus.FAILED
            ]
            
            if failed_tasks:
                execution.status = WorkflowStatus.FAILED
                execution.error = f"Failed tasks: {[t.task_id for t in failed_tasks]}"
            else:
                execution.status = WorkflowStatus.COMPLETED
                
        except asyncio.CancelledError:
            execution.status = WorkflowStatus.CANCELLED
            logger.info(f"Workflow execution cancelled: {execution_id}")
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            logger.error(f"Workflow execution failed: {execution_id}: {e}")
        finally:
            execution.completed_at = datetime.now(UTC)
            
            # Clean up execution task
            if execution_id in self._execution_tasks:
                del self._execution_tasks[execution_id]
                
            # Emit completion event
            await self.event_bus.publish(ExtensionEvent(
                type="workflow.completed",
                source="orchestrator",
                data={
                    "execution_id": execution_id,
                    "workflow_id": execution.workflow_id,
                    "status": execution.status.value,
                    "error": execution.error
                }
            ))

    async def _execute_tasks(self, workflow: WorkflowDefinition, execution: WorkflowExecution) -> None:
        """Execute workflow tasks.
        
        Args:
            workflow: Workflow definition
            execution: Workflow execution
        """
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(workflow.tasks)
        
        # Execute tasks in dependency order
        completed_tasks = set()
        
        while len(completed_tasks) < len(workflow.tasks):
            # Find tasks that can be executed (dependencies satisfied)
            ready_tasks = []
            for task in workflow.tasks:
                if (task.id not in completed_tasks and
                    all(dep in completed_tasks for dep in task.depends_on)):
                    ready_tasks.append(task)
                    
            if not ready_tasks:
                # Check for circular dependencies or failed dependencies
                remaining_tasks = [t for t in workflow.tasks if t.id not in completed_tasks]
                failed_deps = []
                
                for task in remaining_tasks:
                    for dep in task.depends_on:
                        dep_execution = execution.task_executions.get(dep)
                        if dep_execution and dep_execution.status == TaskStatus.FAILED:
                            failed_deps.append(dep)
                            
                if failed_deps:
                    # Skip tasks with failed dependencies
                    for task in remaining_tasks:
                        if any(dep in failed_deps for dep in task.depends_on):
                            task_exec = execution.task_executions[task.id]
                            task_exec.status = TaskStatus.SKIPPED
                            task_exec.error = f"Dependency failed: {failed_deps}"
                            completed_tasks.add(task.id)
                else:
                    raise RuntimeError("Circular dependency detected or no ready tasks")
                continue
                
            # Execute ready tasks in parallel
            task_futures = []
            for task in ready_tasks:
                future = asyncio.create_task(self._execute_task(task, execution))
                task_futures.append((task.id, future))
                
            # Wait for tasks to complete
            for task_id, future in task_futures:
                try:
                    await future
                    completed_tasks.add(task_id)
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    completed_tasks.add(task_id)  # Mark as completed even if failed

    async def _execute_task(self, task: TaskDefinition, execution: WorkflowExecution) -> None:
        """Execute a single task.
        
        Args:
            task: Task definition
            execution: Workflow execution
        """
        task_exec = execution.task_executions[task.id]
        
        try:
            task_exec.status = TaskStatus.RUNNING
            task_exec.started_at = datetime.now(UTC)
            
            # Execute based on task type
            if task.type == TaskType.EXTENSION_CALL:
                result = await self._execute_extension_call(task, execution)
            elif task.type == TaskType.CONDITION:
                result = await self._execute_condition(task, execution)
            elif task.type == TaskType.DELAY:
                result = await self._execute_delay(task, execution)
            elif task.type == TaskType.WEBHOOK:
                result = await self._execute_webhook(task, execution)
            else:
                raise ValueError(f"Unsupported task type: {task.type}")
                
            task_exec.result = result
            task_exec.status = TaskStatus.COMPLETED
            
        except Exception as e:
            task_exec.error = str(e)
            task_exec.status = TaskStatus.FAILED
            
            # Retry if configured
            if task_exec.retry_count < task.retry_count:
                task_exec.retry_count += 1
                await asyncio.sleep(task.retry_delay)
                await self._execute_task(task, execution)  # Recursive retry
                
        finally:
            task_exec.completed_at = datetime.now(UTC)
            if task_exec.started_at:
                duration = (task_exec.completed_at - task_exec.started_at).total_seconds() * 1000
                task_exec.execution_time_ms = duration

    async def _execute_extension_call(self, task: TaskDefinition, execution: WorkflowExecution) -> Any:
        """Execute extension call task.
        
        Args:
            task: Task definition
            execution: Workflow execution
            
        Returns:
            Task result
        """
        if not task.extension or not task.method:
            raise ValueError("Extension and method required for extension_call task")
            
        # Get extension
        extension_reg = self.extension_registry.get_extension(task.extension)
        if not extension_reg or not extension_reg.instance:
            raise ValueError(f"Extension not found or not running: {task.extension}")
            
        extension = extension_reg.instance
        
        # Get method
        if not hasattr(extension, task.method):
            raise ValueError(f"Method not found: {task.method}")
            
        method = getattr(extension, task.method)
        
        # Prepare parameters (substitute variables from context)
        parameters = self._substitute_variables(task.parameters, execution.context)
        
        # Call method
        if asyncio.iscoroutinefunction(method):
            result = await method(**parameters)
        else:
            result = method(**parameters)
            
        # Update context with result
        execution.context[f"task_{task.id}_result"] = result
        
        return result

    async def _execute_condition(self, task: TaskDefinition, execution: WorkflowExecution) -> bool:
        """Execute condition task.
        
        Args:
            task: Task definition
            execution: Workflow execution
            
        Returns:
            Condition result
        """
        if not task.condition:
            raise ValueError("Condition required for condition task")
            
        # Simple condition evaluation (could be enhanced with a proper expression parser)
        condition = self._substitute_variables({"condition": task.condition}, execution.context)["condition"]
        
        # For now, just evaluate simple boolean expressions
        try:
            result = eval(condition, {"__builtins__": {}}, execution.context)
            return bool(result)
        except Exception as e:
            raise ValueError(f"Failed to evaluate condition: {e}")

    async def _execute_delay(self, task: TaskDefinition, execution: WorkflowExecution) -> None:
        """Execute delay task.
        
        Args:
            task: Task definition
            execution: Workflow execution
        """
        delay_seconds = task.parameters.get("seconds", 1.0)
        await asyncio.sleep(delay_seconds)

    async def _execute_webhook(self, task: TaskDefinition, execution: WorkflowExecution) -> Any:
        """Execute webhook task.
        
        Args:
            task: Task definition
            execution: Workflow execution
            
        Returns:
            Webhook response
        """
        # This would implement webhook calling
        # For now, return a placeholder
        return {"webhook": "called", "task_id": task.id}

    def _build_dependency_graph(self, tasks: List[TaskDefinition]) -> Dict[str, List[str]]:
        """Build task dependency graph.
        
        Args:
            tasks: List of task definitions
            
        Returns:
            Dependency graph
        """
        graph = {}
        for task in tasks:
            graph[task.id] = task.depends_on.copy()
        return graph

    def _substitute_variables(self, data: Any, context: Dict[str, Any]) -> Any:
        """Substitute variables in data using context.
        
        Args:
            data: Data to substitute variables in
            context: Context variables
            
        Returns:
            Data with variables substituted
        """
        if isinstance(data, dict):
            return {k: self._substitute_variables(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_variables(item, context) for item in data]
        elif isinstance(data, str):
            # Simple variable substitution
            for key, value in context.items():
                data = data.replace(f"${{{key}}}", str(value))
            return data
        else:
            return data

    def _validate_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Validate workflow definition.
        
        Args:
            workflow: Workflow to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check for duplicate task IDs
        task_ids = [task.id for task in workflow.tasks]
        if len(task_ids) != len(set(task_ids)):
            logger.error(f"Duplicate task IDs in workflow {workflow.id}")
            return False
            
        # Check dependencies exist
        for task in workflow.tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    logger.error(f"Task {task.id} depends on non-existent task {dep}")
                    return False
                    
        # Check for circular dependencies
        if self._has_circular_dependencies(workflow.tasks):
            logger.error(f"Circular dependencies detected in workflow {workflow.id}")
            return False
            
        return True

    def _has_circular_dependencies(self, tasks: List[TaskDefinition]) -> bool:
        """Check for circular dependencies in tasks.
        
        Args:
            tasks: List of task definitions
            
        Returns:
            True if circular dependencies exist, False otherwise
        """
        # Simple cycle detection using DFS
        graph = self._build_dependency_graph(tasks)
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
                    
            rec_stack.remove(node)
            return False
            
        for task_id in graph:
            if task_id not in visited:
                if has_cycle(task_id):
                    return True
                    
        return False

