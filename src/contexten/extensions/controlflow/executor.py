"""
ControlFlow Executor Implementation
"""

from typing import Dict, List, Any
from controlflow import Executor as BaseExecutor
from ..strand_agents import StrandAgent, StrandWorkflow  # Fixed: replaced hyphen with underscore

class FlowExecutor(BaseExecutor):
    async def execute_workflow(
        self,
        workflow: StrandWorkflow,
        execution_plan: Dict[str, Any],
        available_agents: List[StrandAgent]
    ) -> Dict[str, Any]:
        """
        Execute workflow according to execution plan.
        
        Args:
            workflow: Workflow to execute
            execution_plan: Planned execution steps
            available_agents: List of available agents
            
        Returns:
            Dict containing execution results
        """
        results = []
        context = {}
        
        try:
            # Execute stages in planned order
            for stage in execution_plan["stages"]:
                stage_result = await self._execute_stage(
                    stage=stage,
                    available_agents=available_agents,
                    context=context
                )
                results.append(stage_result)
                
                # Update context with stage results
                context.update(stage_result.get("context", {}))
                
                # Check for termination conditions
                if stage_result["status"] == "failed" and not execution_plan.get("continue_on_failure"):
                    break
                    
            return {
                "status": "success" if all(r["status"] == "success" for r in results) else "failed",
                "results": results,
                "context": context
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "context": context
            }
            
    async def _execute_stage(
        self,
        stage: Dict[str, Any],
        available_agents: List[StrandAgent],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a workflow stage.
        
        Args:
            stage: Stage definition
            available_agents: List of available agents
            context: Current execution context
            
        Returns:
            Dict containing stage execution results
        """
        results = []
        stage_context = {}
        
        # Execute tasks in parallel where possible
        for task in stage["tasks"]:
            # Select appropriate agent
            agent = self._select_agent(task, available_agents)
            if not agent:
                results.append({
                    "status": "failed",
                    "error": "No suitable agent found"
                })
                continue
                
            # Execute task
            task_result = await agent.execute({
                **task,
                "context": {**context, **stage_context}
            })
            results.append(task_result)
            
            # Update stage context
            stage_context.update(task_result.get("context", {}))
            
        return {
            "status": "success" if all(r["status"] == "success" for r in results) else "failed",
            "results": results,
            "context": stage_context
        }
        
    def _select_agent(
        self,
        task: Dict[str, Any],
        available_agents: List[StrandAgent]
    ) -> StrandAgent:
        """
        Select most suitable agent for task.
        
        Args:
            task: Task definition
            available_agents: List of available agents
            
        Returns:
            Selected agent or None if no suitable agent found
        """
        required_tools = task.get("required_tools", [])
        
        # Find agent with all required tools
        for agent in available_agents:
            agent_tools = {tool.name for tool in agent.tools}
            if all(tool in agent_tools for tool in required_tools):
                return agent
                
        return None
