"""
Prefect Client Integration for Autonomous Orchestration

This module provides the Prefect-specific implementation for workflow
orchestration, integrating with the broader autonomous CI/CD system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from prefect import flow, task, get_run_logger
from prefect.client.orchestration import PrefectClient
from prefect.deployments import Deployment
from prefect.server.schemas.core import FlowRun
from prefect.server.schemas.states import StateType

from .autonomous_orchestrator import AutonomousOrchestrator, OperationResult, OperationStatus
from .workflow_types import AutonomousWorkflowType, get_workflow_metadata
from .config import OrchestrationConfig
from .monitoring import SystemMonitor


class PrefectOrchestrator:
    """
    Prefect-based orchestration client for autonomous CI/CD operations.
    
    This class provides the Prefect-specific implementation of workflow
    orchestration, managing flow deployments, executions, and monitoring.
    """
    
    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client: Optional[PrefectClient] = None
        self.autonomous_orchestrator = AutonomousOrchestrator(config)
        self.deployments: Dict[str, str] = {}  # workflow_type -> deployment_id
        
    async def initialize(self) -> None:
        """Initialize the Prefect orchestrator"""
        self.logger.info("Initializing Prefect Orchestrator...")
        
        # Initialize Prefect client
        self.client = PrefectClient(api=self.config.prefect_api_url)
        
        # Initialize autonomous orchestrator
        await self.autonomous_orchestrator.initialize()
        
        # Create and deploy workflows
        await self._create_deployments()
        
        self.logger.info("Prefect Orchestrator initialized successfully")
    
    async def _create_deployments(self) -> None:
        """Create Prefect deployments for all workflow types"""
        self.logger.info("Creating Prefect deployments...")
        
        for workflow_type in AutonomousWorkflowType:
            try:
                deployment_id = await self._create_workflow_deployment(workflow_type)
                self.deployments[workflow_type.value] = deployment_id
                self.logger.info(f"Created deployment for {workflow_type.value}: {deployment_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to create deployment for {workflow_type.value}: {e}")
    
    async def _create_workflow_deployment(self, workflow_type: AutonomousWorkflowType) -> str:
        """Create a Prefect deployment for a specific workflow type"""
        metadata = get_workflow_metadata(workflow_type)
        
        # Create the flow function dynamically
        flow_func = self._create_flow_function(workflow_type)
        
        # Create deployment
        deployment = Deployment.build_from_flow(
            flow=flow_func,
            name=f"autonomous-{workflow_type.value}",
            description=metadata.get("description", f"Autonomous {workflow_type.value} workflow"),
            tags=["autonomous", "cicd", workflow_type.value, metadata.get("category", "").value],
            work_pool_name=self.config.prefect_work_pool,
            parameters={"workflow_type": workflow_type.value}
        )
        
        # Deploy
        deployment_id = await deployment.apply()
        return deployment_id
    
    def _create_flow_function(self, workflow_type: AutonomousWorkflowType):
        """Create a Prefect flow function for a specific workflow type"""
        
        @flow(name=f"autonomous-{workflow_type.value}")
        async def autonomous_workflow(
            workflow_type: str,
            context: Optional[Dict[str, Any]] = None,
            priority: int = 5
        ):
            """Autonomous workflow execution"""
            logger = get_run_logger()
            logger.info(f"Starting autonomous workflow: {workflow_type}")
            
            try:
                # Convert string back to enum
                workflow_enum = AutonomousWorkflowType(workflow_type)
                
                # Trigger operation via autonomous orchestrator
                operation_id = await self.autonomous_orchestrator.trigger_autonomous_operation(
                    workflow_enum, context, priority
                )
                
                # Wait for completion
                result = await self._wait_for_operation_completion(operation_id)
                
                logger.info(f"Workflow {workflow_type} completed: {result.status.value}")
                return result.__dict__
                
            except Exception as e:
                logger.error(f"Workflow {workflow_type} failed: {e}")
                raise
        
        return autonomous_workflow
    
    async def _wait_for_operation_completion(
        self, 
        operation_id: str, 
        timeout_minutes: int = 30
    ) -> OperationResult:
        """Wait for an autonomous operation to complete"""
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.now() - start_time < timeout:
            operation = await self.autonomous_orchestrator.get_operation_status(operation_id)
            
            if operation and operation.status in [
                OperationStatus.COMPLETED, 
                OperationStatus.FAILED, 
                OperationStatus.CANCELLED
            ]:
                return operation
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        # Timeout - cancel the operation
        await self.autonomous_orchestrator.cancel_operation(operation_id)
        
        # Return timeout result
        operation = await self.autonomous_orchestrator.get_operation_status(operation_id)
        if operation:
            operation.status = OperationStatus.FAILED
            operation.error = "Operation timed out"
        
        return operation
    
    async def trigger_workflow(
        self,
        workflow_type: AutonomousWorkflowType,
        parameters: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ) -> str:
        """
        Trigger a workflow execution.
        
        Args:
            workflow_type: Type of workflow to trigger
            parameters: Parameters for the workflow
            priority: Execution priority (1-10)
            
        Returns:
            Flow run ID
        """
        if not self.client:
            raise RuntimeError("Prefect client not initialized")
        
        deployment_id = self.deployments.get(workflow_type.value)
        if not deployment_id:
            raise ValueError(f"No deployment found for workflow type: {workflow_type.value}")
        
        # Prepare flow parameters
        flow_parameters = {
            "workflow_type": workflow_type.value,
            "context": parameters or {},
            "priority": priority
        }
        
        # Create flow run
        flow_run = await self.client.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=flow_parameters,
            name=f"{workflow_type.value}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        self.logger.info(f"Triggered workflow {workflow_type.value}: {flow_run.id}")
        return str(flow_run.id)
    
    async def get_workflow_status(self, flow_run_id: str) -> Optional[FlowRun]:
        """Get the status of a workflow execution"""
        if not self.client:
            raise RuntimeError("Prefect client not initialized")
        
        try:
            flow_run = await self.client.read_flow_run(flow_run_id)
            return flow_run
        except Exception as e:
            self.logger.error(f"Error getting workflow status for {flow_run_id}: {e}")
            return None
    
    async def cancel_workflow(self, flow_run_id: str) -> bool:
        """Cancel a workflow execution"""
        if not self.client:
            raise RuntimeError("Prefect client not initialized")
        
        try:
            await self.client.set_flow_run_state(
                flow_run_id=flow_run_id,
                state=StateType.CANCELLED
            )
            self.logger.info(f"Cancelled workflow: {flow_run_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling workflow {flow_run_id}: {e}")
            return False
    
    async def list_active_workflows(self) -> List[FlowRun]:
        """List all active workflow executions"""
        if not self.client:
            raise RuntimeError("Prefect client not initialized")
        
        try:
            flow_runs = await self.client.read_flow_runs(
                flow_run_filter={
                    "state": {"type": {"any_": [StateType.RUNNING, StateType.PENDING]}}
                },
                limit=100
            )
            return flow_runs
        except Exception as e:
            self.logger.error(f"Error listing active workflows: {e}")
            return []
    
    async def get_workflow_history(
        self, 
        workflow_type: Optional[AutonomousWorkflowType] = None,
        limit: int = 50
    ) -> List[FlowRun]:
        """Get workflow execution history"""
        if not self.client:
            raise RuntimeError("Prefect client not initialized")
        
        try:
            flow_filter = {}
            if workflow_type:
                deployment_id = self.deployments.get(workflow_type.value)
                if deployment_id:
                    flow_filter["deployment_id"] = {"any_": [deployment_id]}
            
            flow_runs = await self.client.read_flow_runs(
                flow_run_filter=flow_filter,
                limit=limit,
                sort="CREATED_DESC"
            )
            return flow_runs
        except Exception as e:
            self.logger.error(f"Error getting workflow history: {e}")
            return []
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get orchestration metrics"""
        try:
            # Get autonomous orchestrator metrics
            autonomous_metrics = await self.autonomous_orchestrator.get_system_metrics()
            
            # Get Prefect-specific metrics
            active_workflows = await self.list_active_workflows()
            recent_workflows = await self.get_workflow_history(limit=100)
            
            # Calculate success rate
            completed_workflows = [
                run for run in recent_workflows 
                if run.state_type == StateType.COMPLETED
            ]
            failed_workflows = [
                run for run in recent_workflows 
                if run.state_type == StateType.FAILED
            ]
            
            total_workflows = len(recent_workflows)
            success_rate = (len(completed_workflows) / max(total_workflows, 1)) * 100
            
            return {
                "active_workflows": len(active_workflows),
                "total_workflows_executed": total_workflows,
                "successful_workflows": len(completed_workflows),
                "failed_workflows": len(failed_workflows),
                "success_rate_percent": success_rate,
                "error_rate_percent": 100 - success_rate,
                "system_health_score": autonomous_metrics.get("system_metrics", {}).get("system_health_score", 0),
                "autonomous_metrics": autonomous_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return {}
    
    async def trigger_health_check(self) -> str:
        """Trigger a comprehensive health check workflow"""
        return await self.trigger_workflow(
            AutonomousWorkflowType.HEALTH_CHECK,
            parameters={"comprehensive": True},
            priority=8
        )
    
    async def trigger_component_analysis(
        self, 
        component: str, 
        linear_issue_id: Optional[str] = None
    ) -> str:
        """Trigger component analysis workflow"""
        return await self.trigger_workflow(
            AutonomousWorkflowType.COMPONENT_ANALYSIS,
            parameters={
                "component": component,
                "linear_issue_id": linear_issue_id
            },
            priority=6
        )
    
    async def trigger_failure_analysis(
        self, 
        workflow_run_id: str, 
        failure_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Trigger failure analysis and recovery workflow"""
        return await self.trigger_workflow(
            AutonomousWorkflowType.FAILURE_ANALYSIS,
            parameters={
                "workflow_run_id": workflow_run_id,
                "failure_context": failure_context or {}
            },
            priority=9
        )
    
    async def trigger_performance_monitoring(self) -> str:
        """Trigger performance monitoring workflow"""
        return await self.trigger_workflow(
            AutonomousWorkflowType.PERFORMANCE_MONITORING,
            priority=5
        )
    
    async def trigger_dependency_management(self) -> str:
        """Trigger dependency management workflow"""
        return await self.trigger_workflow(
            AutonomousWorkflowType.DEPENDENCY_MANAGEMENT,
            priority=4
        )
    
    async def trigger_security_audit(self) -> str:
        """Trigger security audit workflow"""
        return await self.trigger_workflow(
            AutonomousWorkflowType.SECURITY_AUDIT,
            priority=7
        )
    
    async def schedule_recurring_workflows(self) -> None:
        """Schedule recurring workflows based on configuration"""
        self.logger.info("Scheduling recurring workflows...")
        
        # Schedule health checks
        if self.config.health_check_interval_minutes > 0:
            await self._schedule_workflow(
                AutonomousWorkflowType.HEALTH_CHECK,
                interval_minutes=self.config.health_check_interval_minutes
            )
        
        # Schedule performance monitoring
        if self.config.performance_monitoring_interval_minutes > 0:
            await self._schedule_workflow(
                AutonomousWorkflowType.PERFORMANCE_MONITORING,
                interval_minutes=self.config.performance_monitoring_interval_minutes
            )
        
        # Schedule dependency checks
        if self.config.dependency_check_interval_hours > 0:
            await self._schedule_workflow(
                AutonomousWorkflowType.DEPENDENCY_MANAGEMENT,
                interval_minutes=self.config.dependency_check_interval_hours * 60
            )
    
    async def _schedule_workflow(
        self, 
        workflow_type: AutonomousWorkflowType, 
        interval_minutes: int
    ) -> None:
        """Schedule a workflow to run at regular intervals"""
        # This would typically use Prefect's scheduling capabilities
        # For now, we'll implement a simple background task
        
        async def recurring_task():
            while True:
                try:
                    await self.trigger_workflow(workflow_type, priority=3)
                    await asyncio.sleep(interval_minutes * 60)
                except Exception as e:
                    self.logger.error(f"Error in recurring {workflow_type.value} task: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        # Start the recurring task
        asyncio.create_task(recurring_task())
        self.logger.info(f"Scheduled {workflow_type.value} to run every {interval_minutes} minutes")
    
    async def shutdown(self) -> None:
        """Shutdown the Prefect orchestrator"""
        self.logger.info("Shutting down Prefect Orchestrator...")
        
        # Cancel all active workflows
        active_workflows = await self.list_active_workflows()
        for workflow in active_workflows:
            await self.cancel_workflow(str(workflow.id))
        
        # Shutdown autonomous orchestrator
        await self.autonomous_orchestrator.shutdown()
        
        # Close Prefect client
        if self.client:
            await self.client.close()
        
        self.logger.info("Prefect Orchestrator shutdown complete")


# Prefect Tasks for Integration
@task
async def execute_codegen_task(prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Prefect task for executing Codegen SDK operations"""
    logger = get_run_logger()
    
    try:
        from codegen import Agent as CodegenAgent
        import os
        
        # Initialize agent
        org_id = os.getenv("CODEGEN_ORG_ID")
        token = os.getenv("CODEGEN_TOKEN")
        
        if not org_id or not token:
            raise ValueError("Codegen SDK credentials not found")
        
        agent = CodegenAgent(org_id=org_id, token=token)
        
        # Add context to prompt if provided
        if context:
            enhanced_prompt = f"{prompt}\n\nContext: {context}"
        else:
            enhanced_prompt = prompt
        
        # Execute task
        task = agent.run(prompt=enhanced_prompt)
        
        # Wait for completion
        max_attempts = 30  # 5 minutes with 10-second intervals
        attempts = 0
        
        while attempts < max_attempts:
            task.refresh()
            if task.status == "completed":
                logger.info("Codegen task completed successfully")
                return {"status": "success", "result": task.result}
            elif task.status == "failed":
                logger.error(f"Codegen task failed: {task.error}")
                return {"status": "failed", "error": task.error}
            
            attempts += 1
            await asyncio.sleep(10)
        
        logger.warning("Codegen task timed out")
        return {"status": "timeout", "error": "Task timed out"}
        
    except Exception as e:
        logger.error(f"Error executing Codegen task: {e}")
        return {"status": "error", "error": str(e)}


@task
async def sync_with_linear(issue_id: Optional[str] = None) -> Dict[str, Any]:
    """Prefect task for Linear synchronization"""
    logger = get_run_logger()
    
    try:
        # TODO: Implement Linear API integration
        logger.info(f"Syncing with Linear (issue: {issue_id})")
        
        return {"status": "success", "synced_issues": []}
        
    except Exception as e:
        logger.error(f"Error syncing with Linear: {e}")
        return {"status": "error", "error": str(e)}


@task
async def process_github_event(event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prefect task for GitHub event processing"""
    logger = get_run_logger()
    
    try:
        # TODO: Implement GitHub event processing
        logger.info(f"Processing GitHub event: {event_type}")
        
        return {"status": "success", "processed_event": event_type}
        
    except Exception as e:
        logger.error(f"Error processing GitHub event: {e}")
        return {"status": "error", "error": str(e)}

