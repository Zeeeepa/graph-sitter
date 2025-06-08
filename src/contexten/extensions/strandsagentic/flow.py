"""
StrandsFlow - Flow management integrating ControlFlow with Prefect monitoring.
"""

from typing import Dict, List, Any, Optional
from prefect import flow, task
from controlflow import Flow as BaseFlow
from .agent import StrandsAgent

class StrandsFlow(BaseFlow):
    def __init__(
        self,
        name: str,
        agents: List[StrandsAgent],
        prefect_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a StrandsFlow with agents and monitoring configuration.
        
        Args:
            name: Name of the flow
            agents: List of StrandsAgents to use in the flow
            prefect_config: Optional Prefect-specific configuration
            **kwargs: Additional flow configuration
        """
        super().__init__(name=name, **kwargs)
        self.agents = agents
        self.prefect_config = prefect_config or {}
        
    @flow(name="strands_execution_flow")
    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow using configured agents with Prefect monitoring.
        
        Args:
            workflow: Workflow definition including tasks and dependencies
            
        Returns:
            Dict containing workflow execution results
        """
        # Initialize workflow context
        context = self._initialize_context(workflow)
        
        # Execute workflow stages
        results = []
        for stage in workflow.get("stages", []):
            stage_result = self._execute_stage.submit(stage, context)
            results.append(stage_result)
            
            # Update context with stage results
            context = self._update_context.submit(context, stage_result)
            
            # Check for workflow termination conditions
            if stage_result.get("status") == "failed" and not workflow.get("continue_on_failure"):
                break
        
        return self._finalize_workflow(results, context)
    
    @task(name="execute_workflow_stage")
    def _execute_stage(
        self,
        stage: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single workflow stage using appropriate agents.
        
        Args:
            stage: Stage definition and tasks
            context: Current workflow context
            
        Returns:
            Dict containing stage execution results
        """
        stage_results = []
        
        # Execute parallel tasks in the stage
        for task_def in stage.get("tasks", []):
            agent = self._select_agent(task_def)
            if agent:
                task_result = agent.execute({
                    **task_def,
                    "context": context
                })
                stage_results.append(task_result)
            else:
                stage_results.append({
                    "status": "failed",
                    "error": "No suitable agent found"
                })
        
        return {
            "status": "success" if all(r.get("status") == "success" for r in stage_results) else "failed",
            "results": stage_results
        }
    
    @task(name="update_workflow_context")
    def _update_context(
        self,
        context: Dict[str, Any],
        stage_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update workflow context with stage execution results.
        
        Args:
            context: Current workflow context
            stage_result: Results from stage execution
            
        Returns:
            Updated workflow context
        """
        return {
            **context,
            "last_stage_result": stage_result,
            "stage_results": context.get("stage_results", []) + [stage_result]
        }
    
    def _select_agent(self, task_def: Dict[str, Any]) -> Optional[StrandsAgent]:
        """
        Select the most suitable agent for a task.
        
        Args:
            task_def: Task definition and requirements
            
        Returns:
            Selected agent or None if no suitable agent found
        """
        required_tools = task_def.get("required_tools", [])
        
        # Find agent with all required tools
        for agent in self.agents:
            agent_tools = {tool.name for tool in agent.tools}
            if all(tool in agent_tools for tool in required_tools):
                return agent
        
        return None
    
    def _initialize_context(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize workflow context with configuration and metadata.
        
        Args:
            workflow: Workflow definition
            
        Returns:
            Initialized workflow context
        """
        return {
            "workflow_id": workflow.get("id"),
            "workflow_config": workflow.get("config", {}),
            "stage_results": [],
            "start_time": workflow.get("start_time")
        }
    
    def _finalize_workflow(
        self,
        results: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Finalize workflow execution and prepare results.
        
        Args:
            results: List of stage execution results
            context: Final workflow context
            
        Returns:
            Dict containing final workflow results and metrics
        """
        return {
            "status": "success" if all(r.get("status") == "success" for r in results) else "failed",
            "results": results,
            "context": context,
            "metrics": self._calculate_metrics(results)
        }
    
    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate workflow performance and execution metrics."""
        return {
            "total_stages": len(results),
            "successful_stages": sum(1 for r in results if r.get("status") == "success"),
            "failed_stages": sum(1 for r in results if r.get("status") == "failed"),
            "total_tasks": sum(len(r.get("results", [])) for r in results),
            "successful_tasks": sum(
                sum(1 for t in r.get("results", []) if t.get("status") == "success")
                for r in results
            )
        }

