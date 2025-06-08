"""
ControlFlow Orchestrator Implementation
"""

from typing import Dict, List, Any, Optional
from controlflow import Orchestrator as BaseOrchestrator
from ..strand-agents import StrandAgent, StrandWorkflow
from .executor import FlowExecutor
from .scheduler import FlowScheduler

class FlowOrchestrator(BaseOrchestrator):
    def __init__(
        self,
        agents: List[StrandAgent],
        executor: Optional[FlowExecutor] = None,
        scheduler: Optional[FlowScheduler] = None,
        **kwargs
    ):
        """
        Initialize flow orchestrator.
        
        Args:
            agents: List of available agents
            executor: Optional custom flow executor
            scheduler: Optional custom flow scheduler
            **kwargs: Additional orchestrator configuration
        """
        super().__init__(**kwargs)
        self.agents = agents
        self.executor = executor or FlowExecutor()
        self.scheduler = scheduler or FlowScheduler()
        
    async def execute_workflow(
        self,
        workflow: StrandWorkflow,
        workflow_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a workflow using available agents.
        
        Args:
            workflow: Workflow to execute
            workflow_def: Workflow definition
            
        Returns:
            Dict containing execution results
        """
        # Schedule workflow execution
        execution_plan = await self.scheduler.schedule_workflow(
            workflow=workflow,
            workflow_def=workflow_def,
            available_agents=self.agents
        )
        
        # Execute workflow according to plan
        return await self.executor.execute_workflow(
            workflow=workflow,
            execution_plan=execution_plan,
            available_agents=self.agents
        )
        
    async def execute_task(
        self,
        task: Dict[str, Any],
        agent: Optional[StrandAgent] = None
    ) -> Dict[str, Any]:
        """
        Execute a single task using an appropriate agent.
        
        Args:
            task: Task definition
            agent: Optional specific agent to use
            
        Returns:
            Dict containing execution results
        """
        # Select agent if not specified
        if not agent:
            agent = self._select_agent(task)
            if not agent:
                return {
                    "status": "failed",
                    "error": "No suitable agent found"
                }
                
        # Execute task
        return await agent.execute(task)
        
    def _select_agent(
        self,
        task: Dict[str, Any]
    ) -> Optional[StrandAgent]:
        """
        Select most suitable agent for task.
        
        Args:
            task: Task definition
            
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

