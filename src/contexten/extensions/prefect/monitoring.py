"""
Prefect Monitoring Integration
"""

from typing import Dict, List, Any, Optional
from prefect import get_client
from prefect.client.schemas import Flow, FlowRun, TaskRun

class PrefectMonitor:
    def __init__(self):
        """Initialize Prefect monitor."""
        self.client = get_client()
        
    async def get_flow_status(
        self,
        flow_run_id: str
    ) -> Dict[str, Any]:
        """
        Get flow run status and metrics.
        
        Args:
            flow_run_id: Flow run ID
            
        Returns:
            Dict containing flow status and metrics
        """
        flow_run = await self.client.read_flow_run(flow_run_id)
        
        return {
            "status": flow_run.state.type.value,
            "start_time": flow_run.start_time,
            "end_time": flow_run.end_time,
            "duration": flow_run.total_run_time,
            "metrics": await self._get_flow_metrics(flow_run_id)
        }
        
    async def get_task_status(
        self,
        task_run_id: str
    ) -> Dict[str, Any]:
        """
        Get task run status and metrics.
        
        Args:
            task_run_id: Task run ID
            
        Returns:
            Dict containing task status and metrics
        """
        task_run = await self.client.read_task_run(task_run_id)
        
        return {
            "status": task_run.state.type.value,
            "start_time": task_run.start_time,
            "end_time": task_run.end_time,
            "duration": task_run.total_run_time,
            "metrics": task_run.metrics
        }
        
    async def list_flow_runs(
        self,
        flow_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List flow runs with optional filtering.
        
        Args:
            flow_name: Optional flow name filter
            status: Optional status filter
            limit: Maximum number of runs to return
            
        Returns:
            List of flow run information
        """
        filters = {}
        if flow_name:
            filters["flow_name"] = {"any_": [flow_name]}
        if status:
            filters["state"] = {"type": {"any_": [status]}}
            
        flow_runs = await self.client.read_flow_runs(
            limit=limit,
            filters=filters
        )
        
        return [
            {
                "id": run.id,
                "flow_name": run.flow_name,
                "status": run.state.type.value,
                "start_time": run.start_time,
                "end_time": run.end_time,
                "duration": run.total_run_time
            }
            for run in flow_runs
        ]
        
    async def _get_flow_metrics(
        self,
        flow_run_id: str
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a flow run.
        
        Args:
            flow_run_id: Flow run ID
            
        Returns:
            Dict containing aggregated metrics
        """
        task_runs = await self.client.read_task_runs(
            filters={"flow_run_id": {"any_": [flow_run_id]}}
        )
        
        # Aggregate metrics from all task runs
        metrics = {}
        for task_run in task_runs:
            for key, value in task_run.metrics.items():
                if key not in metrics:
                    metrics[key] = []
                metrics[key].append(value)
                
        # Calculate statistics for each metric
        return {
            key: {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values)
            }
            for key, values in metrics.items()
        }

