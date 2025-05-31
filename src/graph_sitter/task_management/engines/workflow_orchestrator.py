"""
Workflow orchestration engine for complex workflow execution
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from ..models.task import Task, TaskStatus, TaskType
from ..models.workflow import Workflow, WorkflowStep, WorkflowStatus, StepType, WorkflowCondition
from ..monitoring.logger import TaskLogger
from .executor import TaskExecutor
from .scheduler import TaskScheduler


class WorkflowOrchestrator:
    """
    Complex workflow orchestration engine
    
    Features:
    - Complex workflow definition and execution
    - Conditional task execution based on results
    - Parallel and sequential task processing
    - Workflow state persistence and recovery
    """
    
    def __init__(self, 
                 task_executor: TaskExecutor,
                 task_scheduler: TaskScheduler,
                 logger: Optional[TaskLogger] = None):
        self.task_executor = task_executor
        self.task_scheduler = task_scheduler
        self.logger = logger or TaskLogger()
        
        # Workflow tracking
        self.active_workflows: Dict[UUID, Workflow] = {}
        self.workflow_tasks: Dict[UUID, Set[UUID]] = {}  # workflow_id -> set of task_ids
        
        # Execution control
        self.shutdown_event = asyncio.Event()
    
    async def execute_workflow(self, workflow: Workflow) -> Workflow:
        """
        Execute a complete workflow
        
        Args:
            workflow: Workflow to execute
        
        Returns:
            Updated workflow with execution results
        """
        self.logger.log_info(f"Starting workflow execution: {workflow.id} - {workflow.name}")
        
        # Add to active workflows
        self.active_workflows[workflow.id] = workflow
        self.workflow_tasks[workflow.id] = set()
        
        try:
            # Start workflow
            workflow.start_workflow()
            
            # Execute workflow steps
            await self._execute_workflow_steps(workflow)
            
            # Check final status
            if workflow.is_completed():
                workflow.complete_workflow()
                self.logger.log_info(f"Workflow {workflow.id} completed successfully")
            elif workflow.has_failed_steps():
                workflow.fail_workflow("One or more workflow steps failed")
                self.logger.log_error(f"Workflow {workflow.id} failed")
            
        except Exception as e:
            workflow.fail_workflow(f"Workflow execution error: {str(e)}")
            self.logger.log_error(f"Workflow {workflow.id} failed with error: {e}")
        
        finally:
            # Cleanup
            if workflow.id in self.active_workflows:
                del self.active_workflows[workflow.id]
            if workflow.id in self.workflow_tasks:
                del self.workflow_tasks[workflow.id]
        
        return workflow
    
    async def pause_workflow(self, workflow_id: UUID) -> bool:
        """
        Pause workflow execution
        
        Args:
            workflow_id: Workflow to pause
        
        Returns:
            True if workflow was paused
        """
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        workflow.pause_workflow()
        
        # Cancel running tasks for this workflow
        if workflow_id in self.workflow_tasks:
            for task_id in self.workflow_tasks[workflow_id]:
                self.task_executor.cancel_task_execution(task_id, "Workflow paused")
        
        self.logger.log_info(f"Paused workflow {workflow_id}")
        return True
    
    async def resume_workflow(self, workflow_id: UUID) -> bool:
        """
        Resume paused workflow execution
        
        Args:
            workflow_id: Workflow to resume
        
        Returns:
            True if workflow was resumed
        """
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        if workflow.status != WorkflowStatus.PAUSED:
            return False
        
        workflow.resume_workflow()
        
        # Continue execution
        asyncio.create_task(self._execute_workflow_steps(workflow))
        
        self.logger.log_info(f"Resumed workflow {workflow_id}")
        return True
    
    async def cancel_workflow(self, workflow_id: UUID) -> bool:
        """
        Cancel workflow execution
        
        Args:
            workflow_id: Workflow to cancel
        
        Returns:
            True if workflow was cancelled
        """
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        workflow.cancel_workflow()
        
        # Cancel all running tasks for this workflow
        if workflow_id in self.workflow_tasks:
            for task_id in self.workflow_tasks[workflow_id]:
                self.task_executor.cancel_task_execution(task_id, "Workflow cancelled")
        
        self.logger.log_info(f"Cancelled workflow {workflow_id}")
        return True
    
    def get_workflow_status(self, workflow_id: UUID) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        if workflow_id not in self.active_workflows:
            return None
        
        workflow = self.active_workflows[workflow_id]
        
        return {
            "id": str(workflow.id),
            "name": workflow.name,
            "status": workflow.status,
            "progress_percentage": workflow.get_progress_percentage(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "step_count": len(workflow.steps),
            "completed_steps": sum(1 for step in workflow.steps if step.status == TaskStatus.COMPLETED),
            "failed_steps": sum(1 for step in workflow.steps if step.status == TaskStatus.FAILED),
            "running_steps": sum(1 for step in workflow.steps if step.status == TaskStatus.RUNNING),
        }
    
    async def _execute_workflow_steps(self, workflow: Workflow) -> None:
        """Execute workflow steps"""
        while (workflow.status == WorkflowStatus.RUNNING and 
               not workflow.is_completed() and 
               not workflow.has_failed_steps()):
            
            # Get ready steps
            ready_steps = workflow.get_ready_steps()
            
            if not ready_steps:
                # No ready steps, check if we're waiting for something
                running_steps = [step for step in workflow.steps if step.status == TaskStatus.RUNNING]
                if not running_steps:
                    # No running steps either, workflow might be stuck
                    break
                
                # Wait for running steps to complete
                await asyncio.sleep(1.0)
                continue
            
            # Execute ready steps
            step_tasks = []
            for step in ready_steps:
                if len(step_tasks) >= workflow.max_parallel_tasks:
                    break
                
                step_task = asyncio.create_task(
                    self._execute_workflow_step(workflow, step)
                )
                step_tasks.append(step_task)
            
            if step_tasks:
                # Wait for at least one step to complete
                done, pending = await asyncio.wait(
                    step_tasks, 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel remaining tasks if workflow is no longer running
                if workflow.status != WorkflowStatus.RUNNING:
                    for task in pending:
                        task.cancel()
    
    async def _execute_workflow_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Execute a single workflow step"""
        self.logger.log_info(f"Executing workflow step: {step.id} - {step.name}")
        
        try:
            step.start_execution()
            
            if step.step_type == StepType.TASK:
                await self._execute_task_step(workflow, step)
            elif step.step_type == StepType.PARALLEL:
                await self._execute_parallel_step(workflow, step)
            elif step.step_type == StepType.SEQUENTIAL:
                await self._execute_sequential_step(workflow, step)
            elif step.step_type == StepType.CONDITIONAL:
                await self._execute_conditional_step(workflow, step)
            elif step.step_type == StepType.LOOP:
                await self._execute_loop_step(workflow, step)
            elif step.step_type == StepType.WAIT:
                await self._execute_wait_step(workflow, step)
            else:
                raise ValueError(f"Unknown step type: {step.step_type}")
            
            if step.status != TaskStatus.FAILED:
                step.complete_execution()
                self.logger.log_info(f"Completed workflow step: {step.id}")
        
        except Exception as e:
            step.fail_execution(str(e))
            self.logger.log_error(f"Failed workflow step {step.id}: {e}")
    
    async def _execute_task_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Execute a task step"""
        if not step.task_template:
            raise ValueError(f"Task step {step.id} missing task template")
        
        # Create task from template
        task_data = step.task_template.copy()
        task_data.update({
            "workflow_id": workflow.id,
            "workflow_step_id": step.id,
            "metadata": {
                **task_data.get("metadata", {}),
                "workflow_context": workflow.context,
                "workflow_variables": workflow.variables,
            }
        })
        
        task = Task.from_dict(task_data)
        step.task_id = task.id
        
        # Track task for this workflow
        self.workflow_tasks[workflow.id].add(task.id)
        
        # Execute task
        execution = await self.task_executor.execute_task(task)
        
        # Update step with task results
        if execution.is_successful():
            step.result = execution.result
            # Update workflow variables with task results
            if execution.result:
                workflow.variables.update(execution.result.get("variables", {}))
        else:
            step.fail_execution(execution.error_details.get("error_message", "Task execution failed"))
    
    async def _execute_parallel_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Execute parallel sub-steps"""
        if not step.sub_steps:
            return
        
        # Execute all sub-steps in parallel
        sub_step_tasks = []
        for sub_step in step.sub_steps:
            sub_step_task = asyncio.create_task(
                self._execute_workflow_step(workflow, sub_step)
            )
            sub_step_tasks.append(sub_step_task)
        
        # Wait for all sub-steps to complete
        await asyncio.gather(*sub_step_tasks, return_exceptions=True)
        
        # Collect results
        results = []
        for sub_step in step.sub_steps:
            if sub_step.result:
                results.append(sub_step.result)
            if sub_step.status == TaskStatus.FAILED:
                step.fail_execution(f"Sub-step {sub_step.id} failed: {sub_step.error_message}")
                return
        
        step.result = {"sub_step_results": results}
    
    async def _execute_sequential_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Execute sequential sub-steps"""
        if not step.sub_steps:
            return
        
        results = []
        
        # Execute sub-steps sequentially
        for sub_step in step.sub_steps:
            await self._execute_workflow_step(workflow, sub_step)
            
            if sub_step.status == TaskStatus.FAILED:
                step.fail_execution(f"Sub-step {sub_step.id} failed: {sub_step.error_message}")
                return
            
            if sub_step.result:
                results.append(sub_step.result)
        
        step.result = {"sub_step_results": results}
    
    async def _execute_conditional_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Execute conditional step"""
        if not step.condition:
            raise ValueError(f"Conditional step {step.id} missing condition")
        
        # Evaluate condition
        condition_result = self._evaluate_condition(step.condition, workflow)
        
        # Execute appropriate branch
        if condition_result:
            if step.true_steps:
                for true_step in step.true_steps:
                    await self._execute_workflow_step(workflow, true_step)
        else:
            if step.false_steps:
                for false_step in step.false_steps:
                    await self._execute_workflow_step(workflow, false_step)
        
        step.result = {"condition_result": condition_result}
    
    async def _execute_loop_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Execute loop step"""
        if not step.loop_condition or not step.loop_steps:
            raise ValueError(f"Loop step {step.id} missing loop condition or steps")
        
        iteration = 0
        results = []
        
        while (iteration < step.max_iterations and 
               self._evaluate_condition(step.loop_condition, workflow)):
            
            iteration += 1
            iteration_results = []
            
            # Execute loop steps
            for loop_step in step.loop_steps:
                await self._execute_workflow_step(workflow, loop_step)
                
                if loop_step.status == TaskStatus.FAILED:
                    step.fail_execution(f"Loop step {loop_step.id} failed in iteration {iteration}")
                    return
                
                if loop_step.result:
                    iteration_results.append(loop_step.result)
            
            results.append({
                "iteration": iteration,
                "results": iteration_results
            })
        
        step.result = {
            "iterations": iteration,
            "loop_results": results
        }
    
    async def _execute_wait_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Execute wait step"""
        if step.wait_seconds:
            # Simple time-based wait
            await asyncio.sleep(step.wait_seconds)
        elif step.wait_condition:
            # Condition-based wait
            while not self._evaluate_condition(step.wait_condition, workflow):
                await asyncio.sleep(1.0)  # Check every second
        
        step.result = {"wait_completed": True}
    
    def _evaluate_condition(self, condition: WorkflowCondition, workflow: Workflow) -> bool:
        """Evaluate a workflow condition"""
        # Get value from specified source
        if condition.source == "result":
            # Get from workflow result
            source_data = workflow.result or {}
        elif condition.source == "variables":
            # Get from workflow variables
            source_data = workflow.variables
        elif condition.source == "context":
            # Get from workflow context
            source_data = workflow.context
        else:
            # Default to variables
            source_data = workflow.variables
        
        # Get field value
        field_value = source_data.get(condition.field)
        
        # Evaluate condition
        if condition.operator.value == "equals":
            return field_value == condition.value
        elif condition.operator.value == "not_equals":
            return field_value != condition.value
        elif condition.operator.value == "greater_than":
            return field_value > condition.value
        elif condition.operator.value == "less_than":
            return field_value < condition.value
        elif condition.operator.value == "contains":
            return condition.value in (field_value or "")
        elif condition.operator.value == "exists":
            return field_value is not None
        else:
            return False

