"""
Workflow Manager

Central manager for workflow lifecycle, execution, and monitoring.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .models import Workflow, WorkflowExecution, WorkflowStatus, WorkflowTemplate, COMMON_WORKFLOWS
from .executor import WorkflowExecutor
from .scheduler import WorkflowScheduler


class WorkflowManager:
    """
    Central manager for workflow operations including:
    - Workflow registration and management
    - Execution coordination
    - Scheduling and dependencies
    - Monitoring and metrics
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Storage
        self.workflows: Dict[str, Workflow] = {}
        self.templates: Dict[str, WorkflowTemplate] = COMMON_WORKFLOWS.copy()
        self.executions: Dict[str, WorkflowExecution] = {}
        
        # Components
        self.executor = WorkflowExecutor()
        self.scheduler = WorkflowScheduler()
        
        # State
        self.running = False
        self.monitoring_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the workflow manager"""
        if self.running:
            return
            
        self.logger.info("Starting workflow manager")
        self.running = True
        
        await self.executor.start()
        await self.scheduler.start()
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Workflow manager started")
    
    async def stop(self):
        """Stop the workflow manager"""
        self.logger.info("Stopping workflow manager")
        self.running = False
        
        # Stop monitoring
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        await self.executor.stop()
        await self.scheduler.stop()
        
        self.logger.info("Workflow manager stopped")
    
    def register_workflow(self, workflow: Workflow) -> bool:
        """
        Register a new workflow
        
        Args:
            workflow: Workflow to register
            
        Returns:
            True if successful, False if validation failed
        """
        # Validate workflow
        errors = workflow.validate()
        if errors:
            self.logger.error(f"Workflow validation failed: {errors}")
            return False
        
        self.workflows[workflow.id] = workflow
        
        # Register with scheduler if it has a schedule
        if workflow.schedule:
            self.scheduler.schedule_workflow(workflow.id, workflow.schedule)
        
        self.logger.info(f"Registered workflow: {workflow.id}")
        return True
    
    def register_template(self, template: WorkflowTemplate):
        """Register a workflow template"""
        self.templates[template.id] = template
        self.logger.info(f"Registered workflow template: {template.id}")
    
    def create_workflow_from_template(
        self, 
        template_id: str, 
        workflow_id: str, 
        parameters: Dict[str, Any]
    ) -> Optional[Workflow]:
        """Create a workflow from a template"""
        template = self.templates.get(template_id)
        if not template:
            self.logger.error(f"Template not found: {template_id}")
            return None
        
        workflow = template.create_workflow(workflow_id, parameters)
        
        if self.register_workflow(workflow):
            return workflow
        return None
    
    async def execute(
        self, 
        workflow_id: str, 
        context: Dict[str, Any],
        integrations: Dict[str, Any]
    ) -> WorkflowExecution:
        """
        Execute a workflow
        
        Args:
            workflow_id: ID of workflow to execute
            context: Execution context
            integrations: Available platform integrations
            
        Returns:
            WorkflowExecution instance
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Check concurrent execution limit
        active_executions = [
            exec for exec in self.executions.values()
            if exec.workflow_id == workflow_id and exec.status == WorkflowStatus.RUNNING
        ]
        
        if len(active_executions) >= workflow.max_concurrent_executions:
            raise RuntimeError(f"Max concurrent executions reached for workflow {workflow_id}")
        
        # Create execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            context=context,
            status=WorkflowStatus.PENDING
        )
        
        self.executions[execution.id] = execution
        
        # Start execution
        asyncio.create_task(self._execute_workflow(execution, workflow, integrations))
        
        return execution
    
    async def _execute_workflow(
        self, 
        execution: WorkflowExecution, 
        workflow: Workflow,
        integrations: Dict[str, Any]
    ):
        """Internal workflow execution logic"""
        try:
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.now()
            
            self.logger.info(f"Starting workflow execution: {execution.id}")
            
            # Execute workflow
            await self.executor.execute_workflow(execution, workflow, integrations)
            
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            
            self.logger.info(f"Workflow execution completed: {execution.id}")
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now()
            
            self.logger.error(f"Workflow execution failed: {execution.id} - {e}")
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return False
        
        if execution.status != WorkflowStatus.RUNNING:
            return False
        
        success = await self.executor.cancel_execution(execution_id)
        if success:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
        
        return success
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a workflow execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        workflow = self.workflows.get(execution.workflow_id)
        if not workflow:
            return None
        
        # Get step statuses
        step_statuses = {}
        for step in workflow.steps:
            step_statuses[step.id] = {
                'status': step.status.value,
                'started_at': step.started_at.isoformat() if step.started_at else None,
                'completed_at': step.completed_at.isoformat() if step.completed_at else None,
                'error': step.error,
                'retry_count': step.retry_count
            }
        
        return {
            'execution_id': execution.id,
            'workflow_id': execution.workflow_id,
            'status': execution.status.value,
            'created_at': execution.created_at.isoformat(),
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'current_step': execution.current_step,
            'error': execution.error,
            'steps': step_statuses,
            'completed': execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
        }
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all registered workflows"""
        return [
            {
                'id': workflow.id,
                'name': workflow.name,
                'description': workflow.description,
                'steps': len(workflow.steps),
                'created_at': workflow.created_at.isoformat(),
                'tags': workflow.tags
            }
            for workflow in self.workflows.values()
        ]
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available workflow templates"""
        return [
            {
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'parameters': list(template.parameters.keys()),
                'tags': template.tags
            }
            for template in self.templates.values()
        ]
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get workflow manager metrics"""
        total_executions = len(self.executions)
        running_executions = len([
            e for e in self.executions.values() 
            if e.status == WorkflowStatus.RUNNING
        ])
        completed_executions = len([
            e for e in self.executions.values() 
            if e.status == WorkflowStatus.COMPLETED
        ])
        failed_executions = len([
            e for e in self.executions.values() 
            if e.status == WorkflowStatus.FAILED
        ])
        
        return {
            'total_workflows': len(self.workflows),
            'total_templates': len(self.templates),
            'total_executions': total_executions,
            'running_executions': running_executions,
            'completed_executions': completed_executions,
            'failed_executions': failed_executions,
            'success_rate': completed_executions / total_executions if total_executions > 0 else 0
        }
    
    async def _monitoring_loop(self):
        """Monitor workflow executions and cleanup"""
        while self.running:
            try:
                # Clean up old completed executions (older than 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                to_remove = []
                
                for execution_id, execution in self.executions.items():
                    if (execution.completed_at and 
                        execution.completed_at < cutoff_time and
                        execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]):
                        to_remove.append(execution_id)
                
                for execution_id in to_remove:
                    del self.executions[execution_id]
                    self.logger.debug(f"Cleaned up old execution: {execution_id}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)

