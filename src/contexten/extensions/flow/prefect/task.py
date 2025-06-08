"""
Prefect Task Integration
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from prefect import task
from prefect.context import get_run_context
from ..strands import StrandAgent

class PrefectTask:
    def __init__(
        self,
        agent: StrandAgent,
        name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Prefect task wrapper.
        
        Args:
            agent: StrandAgent instance to wrap
            name: Optional task name
            **kwargs: Additional task configuration
        """
        self.agent = agent
        self.name = name
        self.kwargs = kwargs
        
    @task
    async def execute(
        self,
        task_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute agent task with Prefect monitoring.
        
        Args:
            task_def: Task definition
            
        Returns:
            Dict containing execution results
        """
        context = get_run_context()
        
        # Execute task
        result = await self.agent.execute(task_def)
        
        # Log task-specific metrics
        self._log_metrics(result)
        
        return result
        
    def _log_metrics(self, result: Dict[str, Any]) -> None:
        """Log task metrics to Prefect."""
        context = get_run_context()
        
        # Log basic metrics
        if "duration" in result:
            context.task_run.metrics["duration"] = result["duration"]
            
        if "status" in result:
            context.task_run.metrics["status"] = result["status"]
            
        # Log custom metrics if available
        if "metrics" in result:
            for key, value in result["metrics"].items():
                context.task_run.metrics[key] = value
