"""
Main workflow orchestrator for the Dashboard extension.

This module coordinates the multi-layered workflow execution system,
managing the interaction between Prefect flows, ControlFlow tasks,
and MCP-based agentic flows.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from .prefect_integration import PrefectFlowManager
from .controlflow_integration import ControlFlowManager
from .mcp_integration import MCPAgentManager
from ..models import WorkflowPlan, WorkflowTask, WorkflowExecution, WorkflowStatus

logger = logging.getLogger(__name__)


class OrchestrationLayer(str, Enum):
    """Workflow orchestration layers."""
    PREFECT = "prefect"
    CONTROLFLOW = "controlflow"
    MCP = "mcp"


class WorkflowOrchestrator:
    """
    Main orchestrator for multi-layered workflow execution.
    
    Coordinates between:
    - Prefect flows (top layer): High-level workflow management
    - ControlFlow (middle layer): Task orchestration and dependencies
    - MCP agents (bottom layer): Granular agentic task execution
    """
    
    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.prefect_manager = PrefectFlowManager()
        self.controlflow_manager = ControlFlowManager()
        self.mcp_manager = MCPAgentManager()
        
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_callbacks: Dict[str, List[callable]] = {}
        
        logger.info("Workflow orchestrator initialized")
    
    async def initialize(self):
        """Initialize all workflow managers."""
        try:
            await self.prefect_manager.initialize()
            await self.controlflow_manager.initialize()
            await self.mcp_manager.initialize()
            
            logger.info("All workflow managers initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize workflow managers: {e}")
            return False
    
    async def execute_workflow(
        self, 
        plan: WorkflowPlan, 
        execution_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute a workflow plan through the multi-layered orchestration system.
        
        Args:
            plan: Workflow plan to execute
            execution_config: Optional execution configuration
            
        Returns:
            Execution ID for tracking
        """
        execution_id = f"exec_{plan.id}_{datetime.utcnow().timestamp()}"
        
        try:
            logger.info(f"Starting workflow execution: {execution_id} for plan {plan.id}")
            
            # Create execution record
            execution = WorkflowExecution(
                id=execution_id,
                plan_id=plan.id,
                execution_layer=OrchestrationLayer.PREFECT.value,
                status=WorkflowStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            
            self.active_executions[execution_id] = execution
            
            # Start top-level Prefect flow
            prefect_flow_id = await self.prefect_manager.start_workflow_flow(
                plan=plan,
                execution_id=execution_id,
                config=execution_config or {}
            )
            
            # Update execution with Prefect flow ID
            execution.metadata = {"prefect_flow_id": prefect_flow_id}
            
            # Register progress callback
            await self._register_execution_callbacks(execution_id)
            
            logger.info(f"Workflow execution started: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to start workflow execution: {e}")
            
            # Update execution status to failed
            if execution_id in self.active_executions:
                self.active_executions[execution_id].status = WorkflowStatus.FAILED
                self.active_executions[execution_id].error_message = str(e)
            
            raise
    
    async def _register_execution_callbacks(self, execution_id: str):
        """Register callbacks for execution progress tracking."""
        callbacks = [
            self._on_task_started,
            self._on_task_completed,
            self._on_task_failed,
            self._on_workflow_progress
        ]
        
        self.execution_callbacks[execution_id] = callbacks
    
    async def execute_task_layer(
        self, 
        task: WorkflowTask, 
        execution_id: str,
        layer: OrchestrationLayer = OrchestrationLayer.CONTROLFLOW
    ) -> bool:
        """Execute a specific task through the appropriate orchestration layer.
        
        Args:
            task: Task to execute
            execution_id: Parent execution ID
            layer: Orchestration layer to use
            
        Returns:
            True if task execution started successfully
        """
        try:
            logger.info(f"Executing task {task.id} via {layer.value} layer")
            
            if layer == OrchestrationLayer.CONTROLFLOW:
                return await self.controlflow_manager.execute_task(task, execution_id)
            elif layer == OrchestrationLayer.MCP:
                return await self.mcp_manager.execute_task(task, execution_id)
            else:
                logger.error(f"Unsupported execution layer: {layer}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to execute task {task.id}: {e}")
            return False
    
    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get the current status of a workflow execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution status or None if not found
        """
        return self.active_executions.get(execution_id)
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution.
        
        Args:
            execution_id: Execution ID to cancel
            
        Returns:
            True if cancellation was successful
        """
        try:
            if execution_id not in self.active_executions:
                logger.warning(f"Execution not found: {execution_id}")
                return False
            
            execution = self.active_executions[execution_id]
            
            # Cancel at all layers
            prefect_flow_id = execution.metadata.get("prefect_flow_id")
            if prefect_flow_id:
                await self.prefect_manager.cancel_flow(prefect_flow_id)
            
            await self.controlflow_manager.cancel_execution(execution_id)
            await self.mcp_manager.cancel_execution(execution_id)
            
            # Update execution status
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            
            logger.info(f"Workflow execution cancelled: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
    
    async def pause_execution(self, execution_id: str) -> bool:
        """Pause a running workflow execution.
        
        Args:
            execution_id: Execution ID to pause
            
        Returns:
            True if pause was successful
        """
        try:
            if execution_id not in self.active_executions:
                return False
            
            # Pause at all layers
            await self.prefect_manager.pause_flow(execution_id)
            await self.controlflow_manager.pause_execution(execution_id)
            await self.mcp_manager.pause_execution(execution_id)
            
            logger.info(f"Workflow execution paused: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause execution {execution_id}: {e}")
            return False
    
    async def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused workflow execution.
        
        Args:
            execution_id: Execution ID to resume
            
        Returns:
            True if resume was successful
        """
        try:
            if execution_id not in self.active_executions:
                return False
            
            # Resume at all layers
            await self.prefect_manager.resume_flow(execution_id)
            await self.controlflow_manager.resume_execution(execution_id)
            await self.mcp_manager.resume_execution(execution_id)
            
            logger.info(f"Workflow execution resumed: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume execution {execution_id}: {e}")
            return False
    
    async def get_execution_logs(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get execution logs from all layers.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            List of log entries
        """
        try:
            logs = []
            
            # Get logs from all layers
            prefect_logs = await self.prefect_manager.get_execution_logs(execution_id)
            controlflow_logs = await self.controlflow_manager.get_execution_logs(execution_id)
            mcp_logs = await self.mcp_manager.get_execution_logs(execution_id)
            
            # Combine and sort logs by timestamp
            all_logs = prefect_logs + controlflow_logs + mcp_logs
            all_logs.sort(key=lambda x: x.get("timestamp", ""))
            
            return all_logs
            
        except Exception as e:
            logger.error(f"Failed to get execution logs: {e}")
            return []
    
    async def get_execution_metrics(self, execution_id: str) -> Dict[str, Any]:
        """Get execution metrics from all layers.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Metrics dictionary
        """
        try:
            metrics = {
                "execution_id": execution_id,
                "timestamp": datetime.utcnow().isoformat(),
                "layers": {}
            }
            
            # Get metrics from each layer
            metrics["layers"]["prefect"] = await self.prefect_manager.get_metrics(execution_id)
            metrics["layers"]["controlflow"] = await self.controlflow_manager.get_metrics(execution_id)
            metrics["layers"]["mcp"] = await self.mcp_manager.get_metrics(execution_id)
            
            # Calculate aggregate metrics
            total_tasks = sum(
                layer_metrics.get("total_tasks", 0) 
                for layer_metrics in metrics["layers"].values()
            )
            completed_tasks = sum(
                layer_metrics.get("completed_tasks", 0)
                for layer_metrics in metrics["layers"].values()
            )
            
            metrics["aggregate"] = {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "progress_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "execution_time": self._calculate_execution_time(execution_id)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get execution metrics: {e}")
            return {}
    
    def _calculate_execution_time(self, execution_id: str) -> float:
        """Calculate execution time in seconds."""
        if execution_id not in self.active_executions:
            return 0.0
        
        execution = self.active_executions[execution_id]
        if not execution.started_at:
            return 0.0
        
        end_time = execution.completed_at or datetime.utcnow()
        return (end_time - execution.started_at).total_seconds()
    
    # Callback methods for execution events
    async def _on_task_started(self, execution_id: str, task_id: str, layer: str):
        """Handle task started event."""
        logger.info(f"Task started: {task_id} in execution {execution_id} ({layer})")
        
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.current_task_id = task_id
            
            # Add to execution logs
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": f"Task started: {task_id}",
                "layer": layer,
                "task_id": task_id
            }
            execution.execution_logs.append(log_entry)
    
    async def _on_task_completed(self, execution_id: str, task_id: str, layer: str, result: Any):
        """Handle task completed event."""
        logger.info(f"Task completed: {task_id} in execution {execution_id} ({layer})")
        
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            
            # Add to execution logs
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": f"Task completed: {task_id}",
                "layer": layer,
                "task_id": task_id,
                "result": str(result) if result else None
            }
            execution.execution_logs.append(log_entry)
    
    async def _on_task_failed(self, execution_id: str, task_id: str, layer: str, error: str):
        """Handle task failed event."""
        logger.error(f"Task failed: {task_id} in execution {execution_id} ({layer}): {error}")
        
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            
            # Add to execution logs
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "ERROR",
                "message": f"Task failed: {task_id}",
                "layer": layer,
                "task_id": task_id,
                "error": error
            }
            execution.execution_logs.append(log_entry)
    
    async def _on_workflow_progress(self, execution_id: str, progress: float):
        """Handle workflow progress update."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.progress_percentage = progress
            
            logger.debug(f"Workflow progress: {execution_id} - {progress}%")
    
    async def cleanup_completed_executions(self, max_age_hours: int = 24):
        """Clean up old completed executions.
        
        Args:
            max_age_hours: Maximum age in hours for completed executions
        """
        try:
            cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
            
            to_remove = []
            for execution_id, execution in self.active_executions.items():
                if (execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                    execution.completed_at and 
                    execution.completed_at.timestamp() < cutoff_time):
                    to_remove.append(execution_id)
            
            for execution_id in to_remove:
                del self.active_executions[execution_id]
                if execution_id in self.execution_callbacks:
                    del self.execution_callbacks[execution_id]
            
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old executions")
                
        except Exception as e:
            logger.error(f"Failed to cleanup executions: {e}")
    
    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            stats = {
                "active_executions": len(self.active_executions),
                "execution_status_breakdown": {},
                "layer_stats": {
                    "prefect": await self.prefect_manager.get_stats(),
                    "controlflow": await self.controlflow_manager.get_stats(),
                    "mcp": await self.mcp_manager.get_stats()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Calculate status breakdown
            for execution in self.active_executions.values():
                status = execution.status.value
                stats["execution_status_breakdown"][status] = stats["execution_status_breakdown"].get(status, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get orchestrator stats: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup orchestrator resources."""
        try:
            # Cancel all active executions
            for execution_id in list(self.active_executions.keys()):
                await self.cancel_execution(execution_id)
            
            # Cleanup managers
            await self.prefect_manager.cleanup()
            await self.controlflow_manager.cleanup()
            await self.mcp_manager.cleanup()
            
            logger.info("Workflow orchestrator cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup orchestrator: {e}")

