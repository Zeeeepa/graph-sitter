"""
Flow Manager - Central orchestration for all flow operations

Provides unified interface for managing flows across different frameworks:
- ControlFlow orchestration
- Prefect monitoring
- Strands agent execution
"""

from typing import Dict, List, Any, Optional, Union
import asyncio
import logging
from datetime import datetime

from .controlflow import FlowOrchestrator as ControlFlowOrchestrator
from .prefect import PrefectFlow, PrefectMonitor
from .strands import StrandAgent, StrandWorkflow

logger = logging.getLogger(__name__)


class FlowManager:
    """Central manager for all flow orchestration operations."""
    
    def __init__(
        self,
        agents: Optional[List[StrandAgent]] = None,
        enable_prefect: bool = True,
        enable_controlflow: bool = True,
        **kwargs
    ):
        """
        Initialize flow manager with available frameworks.
        
        Args:
            agents: List of available strand agents
            enable_prefect: Whether to enable Prefect monitoring
            enable_controlflow: Whether to enable ControlFlow orchestration
            **kwargs: Additional configuration
        """
        self.agents = agents or []
        self.enable_prefect = enable_prefect
        self.enable_controlflow = enable_controlflow
        
        # Initialize orchestrators
        self.controlflow_orchestrator = None
        if enable_controlflow:
            try:
                self.controlflow_orchestrator = ControlFlowOrchestrator(agents=self.agents)
            except Exception as e:
                logger.warning(f"Failed to initialize ControlFlow orchestrator: {e}")
                
        # Initialize Prefect monitor
        self.prefect_monitor = None
        if enable_prefect:
            try:
                self.prefect_monitor = PrefectMonitor()
            except Exception as e:
                logger.warning(f"Failed to initialize Prefect monitor: {e}")
                
        # Flow registry
        self.active_flows = {}
        self.flow_history = []
        
    async def create_flow(
        self,
        name: str,
        workflow_def: Dict[str, Any],
        framework: str = "auto"
    ) -> Dict[str, Any]:
        """
        Create and register a new flow.
        
        Args:
            name: Flow name
            workflow_def: Workflow definition
            framework: Framework to use ("auto", "controlflow", "prefect", "strands")
            
        Returns:
            Dict containing flow creation result
        """
        flow_id = f"{name}_{datetime.now().isoformat()}"
        
        try:
            # Select framework
            selected_framework = self._select_framework(framework, workflow_def)
            
            # Create workflow
            workflow = StrandWorkflow(
                name=name,
                agents=self.agents,
                context=workflow_def.get("context", {})
            )
            
            # Register flow
            flow_info = {
                "id": flow_id,
                "name": name,
                "framework": selected_framework,
                "workflow": workflow,
                "workflow_def": workflow_def,
                "status": "created",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            self.active_flows[flow_id] = flow_info
            
            logger.info(f"Created flow {flow_id} using {selected_framework}")
            
            return {
                "status": "success",
                "flow_id": flow_id,
                "framework": selected_framework,
                "message": f"Flow {name} created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create flow {name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Failed to create flow {name}"
            }
            
    async def execute_flow(
        self,
        flow_id: str,
        execution_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a registered flow.
        
        Args:
            flow_id: Flow identifier
            execution_params: Optional execution parameters
            
        Returns:
            Dict containing execution results
        """
        if flow_id not in self.active_flows:
            return {
                "status": "failed",
                "error": "Flow not found",
                "message": f"Flow {flow_id} not found"
            }
            
        flow_info = self.active_flows[flow_id]
        
        try:
            # Update status
            flow_info["status"] = "executing"
            flow_info["updated_at"] = datetime.now()
            
            # Execute based on framework
            framework = flow_info["framework"]
            workflow = flow_info["workflow"]
            workflow_def = flow_info["workflow_def"]
            
            if execution_params:
                workflow_def.update(execution_params)
            
            if framework == "controlflow" and self.controlflow_orchestrator:
                result = await self.controlflow_orchestrator.execute_workflow(
                    workflow=workflow,
                    workflow_def=workflow_def
                )
            elif framework == "prefect" and self.prefect_monitor:
                prefect_flow = PrefectFlow(workflow=workflow)
                result = await prefect_flow.execute(workflow_def)
            else:
                # Default to strands execution
                result = await workflow.execute(workflow_def)
                
            # Update flow status
            flow_info["status"] = result.get("status", "completed")
            flow_info["result"] = result
            flow_info["updated_at"] = datetime.now()
            
            # Move to history if completed
            if flow_info["status"] in ["completed", "failed"]:
                self.flow_history.append(flow_info)
                del self.active_flows[flow_id]
                
            logger.info(f"Flow {flow_id} execution completed with status: {flow_info['status']}")
            
            return {
                "status": "success",
                "flow_id": flow_id,
                "execution_result": result,
                "message": f"Flow {flow_id} executed successfully"
            }
            
        except Exception as e:
            # Update flow status on error
            flow_info["status"] = "failed"
            flow_info["error"] = str(e)
            flow_info["updated_at"] = datetime.now()
            
            logger.error(f"Flow {flow_id} execution failed: {e}")
            
            return {
                "status": "failed",
                "flow_id": flow_id,
                "error": str(e),
                "message": f"Flow {flow_id} execution failed"
            }
            
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get current status of a flow."""
        if flow_id in self.active_flows:
            flow_info = self.active_flows[flow_id]
        else:
            # Check history
            flow_info = next(
                (f for f in self.flow_history if f["id"] == flow_id),
                None
            )
            
        if not flow_info:
            return {
                "status": "not_found",
                "message": f"Flow {flow_id} not found"
            }
            
        return {
            "status": "success",
            "flow_info": {
                "id": flow_info["id"],
                "name": flow_info["name"],
                "framework": flow_info["framework"],
                "status": flow_info["status"],
                "created_at": flow_info["created_at"].isoformat(),
                "updated_at": flow_info["updated_at"].isoformat(),
                "result": flow_info.get("result"),
                "error": flow_info.get("error")
            }
        }
        
    async def list_flows(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List flows with optional filtering."""
        all_flows = list(self.active_flows.values()) + self.flow_history
        
        if status_filter:
            all_flows = [f for f in all_flows if f["status"] == status_filter]
            
        # Sort by updated_at descending
        all_flows.sort(key=lambda x: x["updated_at"], reverse=True)
        
        # Apply limit
        all_flows = all_flows[:limit]
        
        return {
            "status": "success",
            "flows": [
                {
                    "id": f["id"],
                    "name": f["name"],
                    "framework": f["framework"],
                    "status": f["status"],
                    "created_at": f["created_at"].isoformat(),
                    "updated_at": f["updated_at"].isoformat()
                }
                for f in all_flows
            ],
            "total": len(all_flows)
        }
        
    def _select_framework(
        self,
        framework: str,
        workflow_def: Dict[str, Any]
    ) -> str:
        """Select appropriate framework for workflow execution."""
        if framework != "auto":
            return framework
            
        # Auto-select based on workflow characteristics
        if workflow_def.get("monitoring_required") and self.prefect_monitor:
            return "prefect"
        elif workflow_def.get("complex_orchestration") and self.controlflow_orchestrator:
            return "controlflow"
        else:
            return "strands"
            
    async def stop_flow(self, flow_id: str) -> Dict[str, Any]:
        """Stop a running flow."""
        if flow_id not in self.active_flows:
            return {
                "status": "failed",
                "error": "Flow not found",
                "message": f"Flow {flow_id} not found"
            }
            
        flow_info = self.active_flows[flow_id]
        
        try:
            # Update status
            flow_info["status"] = "stopped"
            flow_info["updated_at"] = datetime.now()
            
            # Move to history
            self.flow_history.append(flow_info)
            del self.active_flows[flow_id]
            
            logger.info(f"Flow {flow_id} stopped")
            
            return {
                "status": "success",
                "flow_id": flow_id,
                "message": f"Flow {flow_id} stopped successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop flow {flow_id}: {e}")
            return {
                "status": "failed",
                "flow_id": flow_id,
                "error": str(e),
                "message": f"Failed to stop flow {flow_id}"
            }

