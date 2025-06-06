"""
Prefect integration for top-layer workflow orchestration.

This module provides integration with Prefect for high-level workflow management,
handling the orchestration of complex development workflows with proper error
handling, retries, and monitoring.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import prefect
    from prefect import flow, task, get_run_logger
    from prefect.client.orchestration import PrefectClient
    from prefect.deployments import Deployment
    from prefect.server.schemas.states import StateType
    PREFECT_AVAILABLE = True
except ImportError:
    PREFECT_AVAILABLE = False
    prefect = None
    flow = None
    task = None
    get_run_logger = None
    PrefectClient = None
    Deployment = None
    StateType = None

from ..models import WorkflowPlan, WorkflowTask, WorkflowStatus

logger = logging.getLogger(__name__)


class PrefectFlowManager:
    """Prefect flow manager for top-layer workflow orchestration."""
    
    def __init__(self):
        """Initialize Prefect flow manager."""
        self.client = None
        self.active_flows: Dict[str, str] = {}  # execution_id -> flow_run_id
        self.flow_configs: Dict[str, Dict[str, Any]] = {}
        
        if not PREFECT_AVAILABLE:
            logger.warning("Prefect not available. Top-layer orchestration disabled.")
    
    async def initialize(self):
        """Initialize Prefect client and flows."""
        if not PREFECT_AVAILABLE:
            logger.warning("Prefect not available for initialization")
            return False
        
        try:
            self.client = PrefectClient()
            
            # Register workflow flows
            await self._register_workflow_flows()
            
            logger.info("Prefect flow manager initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Prefect flow manager: {e}")
            return False
    
    async def _register_workflow_flows(self):
        """Register Prefect flows for workflow orchestration."""
        if not PREFECT_AVAILABLE:
            return
        
        # Register main workflow flow
        @flow(name="contexten-workflow", log_prints=True)
        async def contexten_workflow_flow(
            plan_data: Dict[str, Any],
            execution_id: str,
            config: Dict[str, Any]
        ):
            """Main Prefect flow for Contexten workflow execution."""
            flow_logger = get_run_logger()
            flow_logger.info(f"Starting Contexten workflow: {execution_id}")
            
            try:
                # Execute workflow phases
                await setup_phase(plan_data, execution_id, config)
                await execution_phase(plan_data, execution_id, config)
                await validation_phase(plan_data, execution_id, config)
                await completion_phase(plan_data, execution_id, config)
                
                flow_logger.info(f"Workflow completed successfully: {execution_id}")
                return {"status": "completed", "execution_id": execution_id}
                
            except Exception as e:
                flow_logger.error(f"Workflow failed: {execution_id} - {e}")
                raise
        
        @task(name="setup-phase", retries=2)
        async def setup_phase(plan_data: Dict[str, Any], execution_id: str, config: Dict[str, Any]):
            """Setup phase for workflow execution."""
            task_logger = get_run_logger()
            task_logger.info(f"Setting up workflow: {execution_id}")
            
            # TODO: Implement setup logic
            # - Validate plan data
            # - Initialize resources
            # - Setup monitoring
            
            return {"phase": "setup", "status": "completed"}
        
        @task(name="execution-phase", retries=1)
        async def execution_phase(plan_data: Dict[str, Any], execution_id: str, config: Dict[str, Any]):
            """Main execution phase for workflow tasks."""
            task_logger = get_run_logger()
            task_logger.info(f"Executing workflow tasks: {execution_id}")
            
            # TODO: Implement execution logic
            # - Coordinate with ControlFlow layer
            # - Monitor task progress
            # - Handle failures and retries
            
            return {"phase": "execution", "status": "completed"}
        
        @task(name="validation-phase", retries=2)
        async def validation_phase(plan_data: Dict[str, Any], execution_id: str, config: Dict[str, Any]):
            """Validation phase for quality gates."""
            task_logger = get_run_logger()
            task_logger.info(f"Validating workflow results: {execution_id}")
            
            # TODO: Implement validation logic
            # - Run quality gates
            # - Validate deliverables
            # - Check acceptance criteria
            
            return {"phase": "validation", "status": "completed"}
        
        @task(name="completion-phase")
        async def completion_phase(plan_data: Dict[str, Any], execution_id: str, config: Dict[str, Any]):
            """Completion phase for workflow cleanup."""
            task_logger = get_run_logger()
            task_logger.info(f"Completing workflow: {execution_id}")
            
            # TODO: Implement completion logic
            # - Cleanup resources
            # - Generate reports
            # - Send notifications
            
            return {"phase": "completion", "status": "completed"}
        
        # Store flow reference
        self.contexten_workflow_flow = contexten_workflow_flow
        
        logger.info("Prefect workflow flows registered")
    
    async def start_workflow_flow(
        self, 
        plan: WorkflowPlan, 
        execution_id: str, 
        config: Dict[str, Any]
    ) -> str:
        """Start a Prefect workflow flow.
        
        Args:
            plan: Workflow plan to execute
            execution_id: Execution ID for tracking
            config: Execution configuration
            
        Returns:
            Prefect flow run ID
        """
        if not PREFECT_AVAILABLE or not self.client:
            logger.warning("Prefect not available, cannot start workflow flow")
            return f"mock_flow_{execution_id}"
        
        try:
            # Prepare plan data for Prefect
            plan_data = {
                "id": plan.id,
                "project_id": plan.project_id,
                "title": plan.title,
                "description": plan.description,
                "requirements": plan.requirements,
                "generated_plan": plan.generated_plan,
                "tasks": plan.tasks,
                "estimated_duration": plan.estimated_duration,
                "complexity_score": plan.complexity_score
            }
            
            # Start the flow
            flow_run = await self.contexten_workflow_flow.with_options(
                name=f"workflow-{execution_id}"
            )(
                plan_data=plan_data,
                execution_id=execution_id,
                config=config
            )
            
            flow_run_id = str(flow_run.id) if hasattr(flow_run, 'id') else f"flow_{execution_id}"
            self.active_flows[execution_id] = flow_run_id
            
            logger.info(f"Started Prefect workflow flow: {flow_run_id} for execution {execution_id}")
            return flow_run_id
            
        except Exception as e:
            logger.error(f"Failed to start Prefect workflow flow: {e}")
            raise
    
    async def get_flow_status(self, flow_run_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a Prefect flow run.
        
        Args:
            flow_run_id: Prefect flow run ID
            
        Returns:
            Flow status dictionary or None if not found
        """
        if not PREFECT_AVAILABLE or not self.client:
            return None
        
        try:
            flow_run = await self.client.read_flow_run(flow_run_id)
            
            if flow_run:
                return {
                    "id": str(flow_run.id),
                    "name": flow_run.name,
                    "state": flow_run.state.type.value if flow_run.state else "unknown",
                    "state_name": flow_run.state.name if flow_run.state else "unknown",
                    "start_time": flow_run.start_time.isoformat() if flow_run.start_time else None,
                    "end_time": flow_run.end_time.isoformat() if flow_run.end_time else None,
                    "total_run_time": flow_run.total_run_time.total_seconds() if flow_run.total_run_time else 0,
                    "parameters": flow_run.parameters or {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get flow status: {e}")
            return None
    
    async def cancel_flow(self, flow_run_id: str) -> bool:
        """Cancel a Prefect flow run.
        
        Args:
            flow_run_id: Prefect flow run ID
            
        Returns:
            True if cancellation was successful
        """
        if not PREFECT_AVAILABLE or not self.client:
            return False
        
        try:
            await self.client.set_flow_run_state(
                flow_run_id=flow_run_id,
                state=prefect.states.Cancelled()
            )
            
            logger.info(f"Cancelled Prefect flow: {flow_run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel Prefect flow: {e}")
            return False
    
    async def pause_flow(self, execution_id: str) -> bool:
        """Pause a workflow flow.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if pause was successful
        """
        if execution_id not in self.active_flows:
            return False
        
        flow_run_id = self.active_flows[execution_id]
        
        if not PREFECT_AVAILABLE or not self.client:
            return False
        
        try:
            await self.client.set_flow_run_state(
                flow_run_id=flow_run_id,
                state=prefect.states.Paused()
            )
            
            logger.info(f"Paused Prefect flow: {flow_run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause Prefect flow: {e}")
            return False
    
    async def resume_flow(self, execution_id: str) -> bool:
        """Resume a paused workflow flow.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if resume was successful
        """
        if execution_id not in self.active_flows:
            return False
        
        flow_run_id = self.active_flows[execution_id]
        
        if not PREFECT_AVAILABLE or not self.client:
            return False
        
        try:
            await self.client.set_flow_run_state(
                flow_run_id=flow_run_id,
                state=prefect.states.Running()
            )
            
            logger.info(f"Resumed Prefect flow: {flow_run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume Prefect flow: {e}")
            return False
    
    async def get_execution_logs(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get execution logs from Prefect.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            List of log entries
        """
        if execution_id not in self.active_flows or not PREFECT_AVAILABLE or not self.client:
            return []
        
        try:
            flow_run_id = self.active_flows[execution_id]
            logs = await self.client.read_logs(flow_run_filter={"id": {"any_": [flow_run_id]}})
            
            log_entries = []
            for log in logs:
                log_entries.append({
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "message": log.message,
                    "layer": "prefect",
                    "flow_run_id": flow_run_id,
                    "task_run_id": getattr(log, 'task_run_id', None)
                })
            
            return log_entries
            
        except Exception as e:
            logger.error(f"Failed to get Prefect execution logs: {e}")
            return []
    
    async def get_metrics(self, execution_id: str) -> Dict[str, Any]:
        """Get Prefect metrics for an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Metrics dictionary
        """
        if execution_id not in self.active_flows:
            return {}
        
        try:
            flow_run_id = self.active_flows[execution_id]
            flow_status = await self.get_flow_status(flow_run_id)
            
            if flow_status:
                return {
                    "layer": "prefect",
                    "flow_run_id": flow_run_id,
                    "state": flow_status["state"],
                    "start_time": flow_status["start_time"],
                    "end_time": flow_status["end_time"],
                    "total_run_time": flow_status["total_run_time"],
                    "total_tasks": 4,  # setup, execution, validation, completion
                    "completed_tasks": self._count_completed_tasks(flow_status["state"])
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get Prefect metrics: {e}")
            return {}
    
    def _count_completed_tasks(self, state: str) -> int:
        """Count completed tasks based on flow state."""
        if state in ["COMPLETED"]:
            return 4
        elif state in ["RUNNING"]:
            return 2  # Assume halfway through
        elif state in ["FAILED", "CANCELLED"]:
            return 1  # Assume failed during execution
        else:
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Prefect manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "layer": "prefect",
            "available": PREFECT_AVAILABLE,
            "active_flows": len(self.active_flows),
            "client_connected": self.client is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup Prefect manager resources."""
        try:
            # Cancel all active flows
            for execution_id in list(self.active_flows.keys()):
                flow_run_id = self.active_flows[execution_id]
                await self.cancel_flow(flow_run_id)
            
            # Close client connection
            if self.client:
                await self.client.close()
            
            self.active_flows.clear()
            self.flow_configs.clear()
            
            logger.info("Prefect flow manager cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup Prefect manager: {e}")

