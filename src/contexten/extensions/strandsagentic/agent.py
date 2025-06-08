"""
StrandsAgent - Agent implementation integrating strands-agents tools capabilities.
"""

from typing import Dict, List, Any, Optional
from strands_agents.tools import Tool, BaseAgent
from controlflow import AgentContext

class StrandsAgent(BaseAgent):
    def __init__(
        self,
        tools: List[Tool],
        context: Optional[AgentContext] = None,
        **kwargs
    ):
        """
        Initialize a StrandsAgent with tools and context.
        
        Args:
            tools: List of tools available to the agent
            context: Optional agent context for maintaining state
            **kwargs: Additional configuration parameters
        """
        super().__init__(tools=tools, **kwargs)
        self.context = context or AgentContext()
        
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using available tools and context.
        
        Args:
            task: Task definition and parameters
            
        Returns:
            Dict containing execution results
        """
        # Update context with task-specific information
        self.context.update(task.get("context", {}))
        
        # Prepare tools for task execution
        task_tools = self._prepare_tools(task)
        
        # Execute task with prepared tools
        result = self._execute_with_tools(task, task_tools)
        
        # Update context with execution results
        self.context.update_execution_history(result)
        
        return result
    
    def _prepare_tools(self, task: Dict[str, Any]) -> List[Tool]:
        """
        Prepare and configure tools for specific task requirements.
        
        Args:
            task: Task definition containing tool requirements
            
        Returns:
            List of configured tools
        """
        required_tools = task.get("required_tools", [])
        return [
            tool for tool in self.tools
            if tool.name in required_tools or not required_tools
        ]
    
    def _execute_with_tools(
        self,
        task: Dict[str, Any],
        tools: List[Tool]
    ) -> Dict[str, Any]:
        """
        Execute task using prepared tools.
        
        Args:
            task: Task definition and parameters
            tools: List of prepared tools
            
        Returns:
            Dict containing execution results
        """
        try:
            # Execute task steps using available tools
            results = []
            for step in task.get("steps", [{"action": task.get("action")}]):
                step_result = self._execute_step(step, tools)
                results.append(step_result)
                
                # Check for early termination conditions
                if step_result.get("status") == "failed":
                    break
            
            return {
                "status": "success" if all(r.get("status") == "success" for r in results) else "failed",
                "results": results,
                "context_updates": self.context.get_updates()
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "context_updates": self.context.get_updates()
            }
    
    def _execute_step(
        self,
        step: Dict[str, Any],
        tools: List[Tool]
    ) -> Dict[str, Any]:
        """
        Execute a single step of a task.
        
        Args:
            step: Step definition and parameters
            tools: Available tools for execution
            
        Returns:
            Dict containing step execution results
        """
        action = step.get("action")
        if not action:
            return {"status": "failed", "error": "No action specified"}
            
        for tool in tools:
            if tool.can_handle(action):
                return tool.execute(action, step.get("parameters", {}))
        
        return {
            "status": "failed",
            "error": f"No tool available for action: {action}"
        }
