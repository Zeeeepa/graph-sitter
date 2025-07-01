"""
StrandWorkflow - Workflow implementation using strands-agents workflow system
"""

from typing import Dict, List, Any, Optional
from strands_agents.workflow import (
    Workflow,
    WorkflowContext,
    WorkflowStep,
    WorkflowStage
)
from .agent import StrandAgent

class StrandWorkflow(Workflow):
    def __init__(
        self,
        name: str,
        agents: List[StrandAgent],
        context: Optional[WorkflowContext] = None,
        **kwargs
    ):
        """
        Initialize a StrandWorkflow with agents and context.
        
        Args:
            name: Name of the workflow
            agents: List of StrandAgents to use in the workflow
            context: Optional workflow context
            **kwargs: Additional workflow configuration
        """
        super().__init__(name=name, **kwargs)
        self.agents = agents
        self.context = context or WorkflowContext()
        
    async def execute(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow using configured agents.
        
        Args:
            workflow_def: Workflow definition including stages and tasks
            
        Returns:
            Dict containing workflow execution results
        """
        # Initialize workflow context
        self.context.update(workflow_def.get("context", {}))
        
        # Create workflow stages
        stages = [
            WorkflowStage(
                name=stage.get("name"),
                tasks=stage.get("tasks", []),
                dependencies=stage.get("dependencies", [])
            )
            for stage in workflow_def.get("stages", [])
        ]
        
        # Execute stages in dependency order
        results = []
        for stage in self._order_stages(stages):
            stage_result = await self._execute_stage(stage)
            results.append(stage_result)
            
            # Update context with stage results
            self.context.update_stage_results(stage_result)
            
            # Check for workflow termination conditions
            if stage_result.get("status") == "failed" and not workflow_def.get("continue_on_failure"):
                break
        
        return self._finalize_workflow(results)
    
    def _order_stages(self, stages: List[WorkflowStage]) -> List[WorkflowStage]:
        """
        Order stages based on their dependencies.
        
        Args:
            stages: List of workflow stages
            
        Returns:
            Ordered list of stages
        """
        # Implementation of topological sort for stage ordering
        ordered = []
        visited = set()
        temp_visited = set()
        
        def visit(stage: WorkflowStage):
            if stage.name in temp_visited:
                raise ValueError(f"Circular dependency detected at stage {stage.name}")
            if stage.name in visited:
                return
                
            temp_visited.add(stage.name)
            
            # Visit all dependencies first
            for dep in stage.dependencies:
                dep_stage = next(s for s in stages if s.name == dep)
                visit(dep_stage)
                
            temp_visited.remove(stage.name)
            visited.add(stage.name)
            ordered.append(stage)
            
        for stage in stages:
            if stage.name not in visited:
                visit(stage)
                
        return ordered
    
    async def _execute_stage(self, stage: WorkflowStage) -> Dict[str, Any]:
        """
        Execute a single workflow stage using appropriate agents.
        
        Args:
            stage: Stage definition and tasks
            
        Returns:
            Dict containing stage execution results
        """
        stage_results = []
        
        # Execute parallel tasks in the stage
        for task in stage.tasks:
            agent = self._select_agent(task)
            if agent:
                task_result = await agent.execute({
                    **task,
                    "context": self.context.get_task_context(task)
                })
                stage_results.append(task_result)
            else:
                stage_results.append({
                    "status": "failed",
                    "error": "No suitable agent found"
                })
        
        return {
            "name": stage.name,
            "status": "success" if all(r.get("status") == "success" for r in stage_results) else "failed",
            "results": stage_results
        }
    
    def _select_agent(self, task: Dict[str, Any]) -> Optional[StrandAgent]:
        """
        Select the most suitable agent for a task.
        
        Args:
            task: Task definition and requirements
            
        Returns:
            Selected agent or None if no suitable agent found
        """
        required_tools = task.get("required_tools", [])
        
        # Find agent with all required tools
        for agent in self.agents:
            agent_tools = {tool.name for tool in agent.tools}
            if all(tool in agent_tools for tool in required_tools):
                return agent
        
        return None
    
    def _finalize_workflow(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Finalize workflow execution and prepare results.
        
        Args:
            results: List of stage execution results
            
        Returns:
            Dict containing final workflow results and metrics
        """
        return {
            "status": "success" if all(r.get("status") == "success" for r in results) else "failed",
            "results": results,
            "context": self.context.get_final_context(),
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

