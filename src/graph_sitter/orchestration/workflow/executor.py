"""
Workflow Executor

Executes workflow steps with dependency management, retries, and error handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .models import Workflow, WorkflowExecution, WorkflowStep, StepStatus, WorkflowStatus


class WorkflowExecutor:
    """
    Executes workflows by managing step dependencies, retries, and error handling.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.active_executions: Dict[str, asyncio.Task] = {}
        
        # Action registry for step execution
        self.action_registry: Dict[str, callable] = {}
        self._register_default_actions()
    
    async def start(self):
        """Start the workflow executor"""
        self.running = True
        self.logger.info("Workflow executor started")
    
    async def stop(self):
        """Stop the workflow executor"""
        self.running = False
        
        # Cancel all active executions
        for execution_id, task in self.active_executions.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.active_executions.clear()
        self.logger.info("Workflow executor stopped")
    
    def register_action(self, action_name: str, action_func: callable):
        """Register a custom action for workflow steps"""
        self.action_registry[action_name] = action_func
        self.logger.info(f"Registered action: {action_name}")
    
    async def execute_workflow(
        self, 
        execution: WorkflowExecution, 
        workflow: Workflow,
        integrations: Dict[str, Any]
    ):
        """
        Execute a complete workflow
        
        Args:
            execution: Workflow execution instance
            workflow: Workflow definition
            integrations: Available platform integrations
        """
        try:
            self.logger.info(f"Executing workflow: {workflow.id}")
            
            # Reset step statuses
            for step in workflow.steps:
                step.status = StepStatus.PENDING
                step.started_at = None
                step.completed_at = None
                step.error = None
                step.result = None
                step.retry_count = 0
            
            completed_steps = []
            failed_steps = []
            
            # Execute steps in dependency order
            while len(completed_steps) + len(failed_steps) < len(workflow.steps):
                # Get ready steps (dependencies satisfied)
                ready_steps = workflow.get_ready_steps(completed_steps)
                
                if not ready_steps:
                    # Check if we're stuck due to failed dependencies
                    pending_steps = [s for s in workflow.steps if s.status == StepStatus.PENDING]
                    if pending_steps:
                        raise RuntimeError("Workflow stuck - no ready steps available")
                    break
                
                # Execute ready steps concurrently
                step_tasks = []
                for step in ready_steps:
                    task = asyncio.create_task(
                        self._execute_step(step, execution, integrations)
                    )
                    step_tasks.append((step, task))
                
                # Wait for steps to complete
                for step, task in step_tasks:
                    try:
                        await task
                        if step.status == StepStatus.COMPLETED:
                            completed_steps.append(step.id)
                            execution.step_results[step.id] = step.result
                        elif step.status == StepStatus.FAILED:
                            failed_steps.append(step.id)
                            if step.on_failure != 'skip':
                                raise RuntimeError(f"Step {step.id} failed: {step.error}")
                    except Exception as e:
                        step.status = StepStatus.FAILED
                        step.error = str(e)
                        failed_steps.append(step.id)
                        if step.on_failure != 'skip':
                            raise
            
            self.logger.info(f"Workflow execution completed: {workflow.id}")
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {workflow.id} - {e}")
            raise
    
    async def _execute_step(
        self, 
        step: WorkflowStep, 
        execution: WorkflowExecution,
        integrations: Dict[str, Any]
    ):
        """Execute a single workflow step"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        execution.current_step = step.id
        
        self.logger.info(f"Executing step: {step.id}")
        
        try:
            # Check condition if specified
            if step.condition and not self._evaluate_condition(step.condition, execution):
                step.status = StepStatus.SKIPPED
                step.completed_at = datetime.now()
                self.logger.info(f"Step skipped due to condition: {step.id}")
                return
            
            # Resolve parameters
            resolved_params = self._resolve_parameters(step.parameters, execution)
            
            # Execute action with timeout
            if step.timeout:
                result = await asyncio.wait_for(
                    self._execute_action(step.action, resolved_params, integrations),
                    timeout=step.timeout.total_seconds()
                )
            else:
                result = await self._execute_action(step.action, resolved_params, integrations)
            
            step.result = result
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            
            self.logger.info(f"Step completed: {step.id}")
            
        except asyncio.TimeoutError:
            step.error = "Step execution timed out"
            await self._handle_step_failure(step, execution, integrations)
        except Exception as e:
            step.error = str(e)
            await self._handle_step_failure(step, execution, integrations)
    
    async def _handle_step_failure(
        self, 
        step: WorkflowStep, 
        execution: WorkflowExecution,
        integrations: Dict[str, Any]
    ):
        """Handle step failure with retry logic"""
        self.logger.warning(f"Step failed: {step.id} - {step.error}")
        
        if step.retry_count < step.max_retries and step.on_failure != 'fail':
            step.retry_count += 1
            step.status = StepStatus.RETRYING
            
            # Exponential backoff
            delay = min(2 ** step.retry_count, 60)
            await asyncio.sleep(delay)
            
            self.logger.info(f"Retrying step: {step.id} (attempt {step.retry_count})")
            await self._execute_step(step, execution, integrations)
        else:
            step.status = StepStatus.FAILED
            step.completed_at = datetime.now()
            
            if step.on_failure == 'skip':
                self.logger.info(f"Step failed but marked as skippable: {step.id}")
            else:
                raise RuntimeError(f"Step failed: {step.id} - {step.error}")
    
    async def _execute_action(
        self, 
        action: str, 
        parameters: Dict[str, Any],
        integrations: Dict[str, Any]
    ) -> Any:
        """Execute a specific action"""
        # Parse action (e.g., 'github.create_pr', 'linear.update_issue')
        if '.' in action:
            platform, method = action.split('.', 1)
            
            # Use platform integration
            if platform in integrations:
                integration = integrations[platform]
                if hasattr(integration, method):
                    action_func = getattr(integration, method)
                    return await action_func(**parameters)
                else:
                    raise ValueError(f"Method {method} not found in {platform} integration")
            else:
                raise ValueError(f"Platform integration not found: {platform}")
        else:
            # Use registered action
            if action in self.action_registry:
                action_func = self.action_registry[action]
                return await action_func(**parameters)
            else:
                raise ValueError(f"Action not found: {action}")
    
    def _resolve_parameters(
        self, 
        parameters: Dict[str, Any], 
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Resolve parameter values with variable substitution"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Variable substitution
                var_path = value[2:-1]  # Remove ${ and }
                resolved_value = self._resolve_variable(var_path, execution)
                resolved[key] = resolved_value
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_variable(self, var_path: str, execution: WorkflowExecution) -> Any:
        """Resolve a variable path (e.g., 'step_id.result.field')"""
        parts = var_path.split('.')
        
        if parts[0] in execution.step_results:
            # Step result reference
            value = execution.step_results[parts[0]]
            for part in parts[1:]:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    raise ValueError(f"Cannot resolve variable path: {var_path}")
            return value
        elif parts[0] in execution.context:
            # Context reference
            value = execution.context[parts[0]]
            for part in parts[1:]:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    raise ValueError(f"Cannot resolve variable path: {var_path}")
            return value
        else:
            raise ValueError(f"Variable not found: {parts[0]}")
    
    def _evaluate_condition(self, condition: str, execution: WorkflowExecution) -> bool:
        """Evaluate a conditional expression"""
        # Simple condition evaluation (can be extended)
        # For now, support basic comparisons
        try:
            # Replace variables in condition
            resolved_condition = condition
            for var_name, value in execution.context.items():
                resolved_condition = resolved_condition.replace(f"${{{var_name}}}", str(value))
            
            # Evaluate the condition (basic implementation)
            return eval(resolved_condition)
        except Exception as e:
            self.logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        if execution_id in self.active_executions:
            task = self.active_executions[execution_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.active_executions[execution_id]
            return True
        return False
    
    def _register_default_actions(self):
        """Register default actions"""
        
        async def delay_action(seconds: int = 1):
            """Simple delay action for testing"""
            await asyncio.sleep(seconds)
            return f"Delayed for {seconds} seconds"
        
        async def log_action(message: str = "Log message", level: str = "info"):
            """Log a message"""
            logger = logging.getLogger("workflow.action")
            getattr(logger, level.lower())(message)
            return message
        
        async def set_variable(name: str, value: Any):
            """Set a variable in execution context"""
            return {name: value}
        
        self.action_registry.update({
            'delay': delay_action,
            'log': log_action,
            'set_variable': set_variable,
        })

