"""
StrandsOrchestrator - Main orchestration component integrating ControlFlow with Prefect monitoring.
"""

from typing import Dict, List, Optional, Any
from prefect import flow, task
from controlflow import Orchestrator, AgentConfig
from zeeeepa.tools import ToolRegistry
from zeeeepa.sdk import Agent

class StrandsOrchestrator:
    def __init__(
        self,
        tools_config: Dict[str, Any],
        agent_config: Dict[str, Any],
        prefect_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the StrandsOrchestrator with configuration for tools, agents, and monitoring.
        
        Args:
            tools_config: Configuration for Zeeeepa tools
            agent_config: Configuration for agent behavior and capabilities
            prefect_config: Optional configuration for Prefect monitoring
        """
        self.tool_registry = ToolRegistry(**tools_config)
        self.orchestrator = Orchestrator(AgentConfig(**agent_config))
        self.prefect_config = prefect_config or {}
        
    @flow(name="strands_orchestration_flow")
    def orchestrate(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main orchestration flow monitored by Prefect.
        
        Args:
            tasks: List of task definitions to be executed by agents
            
        Returns:
            Dict containing execution results and metrics
        """
        results = []
        for task_def in tasks:
            result = self._execute_task.submit(task_def)
            results.append(result)
        
        return self._aggregate_results(results)
    
    @task(name="execute_single_task")
    def _execute_task(self, task_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task using appropriate agent and tools.
        
        Args:
            task_def: Task definition including requirements and constraints
            
        Returns:
            Dict containing task execution results
        """
        agent = Agent(
            tools=self.tool_registry.get_tools(task_def.get("required_tools", [])),
            **task_def.get("agent_config", {})
        )
        
        return self.orchestrator.execute_agent_task(agent, task_def)
    
    @task(name="aggregate_results")
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from multiple task executions.
        
        Args:
            results: List of individual task results
            
        Returns:
            Dict containing aggregated results and metrics
        """
        return {
            "results": results,
            "metrics": self._calculate_metrics(results),
            "status": "completed"
        }
    
    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance and execution metrics."""
        return {
            "total_tasks": len(results),
            "successful_tasks": sum(1 for r in results if r.get("status") == "success"),
            "failed_tasks": sum(1 for r in results if r.get("status") == "failed"),
            "average_duration": sum(r.get("duration", 0) for r in results) / len(results)
        }

