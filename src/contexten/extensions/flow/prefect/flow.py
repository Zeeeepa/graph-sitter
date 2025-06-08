"""
Prefect Flow Integration
"""

from typing import Dict, List, Any, Optional
from prefect import flow, get_run_logger
from prefect.context import get_run_context
from ..strands import StrandWorkflow

class PrefectFlow:
    def __init__(
        self,
        workflow: StrandWorkflow,
        name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Prefect flow wrapper.
        
        Args:
            workflow: StrandWorkflow instance to wrap
            name: Optional flow name (defaults to workflow name)
            **kwargs: Additional flow configuration
        """
        self.workflow = workflow
        self.name = name or workflow.name
        self.kwargs = kwargs
        
    @flow
    async def execute(
        self,
        workflow_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute workflow with Prefect monitoring.
        
        Args:
            workflow_def: Workflow definition
            
        Returns:
            Dict containing execution results
        """
        logger = get_run_logger()
        context = get_run_context()
        
        logger.info(f"Starting workflow execution: {self.name}")
        
        try:
            # Execute workflow
            result = await self.workflow.execute(workflow_def)
            
            # Log metrics
            self._log_metrics(result.get("metrics", {}))
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            raise
            
    def _log_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log workflow metrics to Prefect."""
        logger = get_run_logger()
        
        for key, value in metrics.items():
            logger.info(f"Metric - {key}: {value}")
            # Could also use Prefect's metrics API when available
