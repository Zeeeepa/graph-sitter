"""
ControlFlow Scheduler Implementation
"""

from typing import Dict, List, Any
from controlflow import Scheduler as BaseScheduler
from ..strands import StrandAgent, StrandWorkflow

class FlowScheduler(BaseScheduler):
    async def schedule_workflow(
        self,
        workflow: StrandWorkflow,
        workflow_def: Dict[str, Any],
        available_agents: List[StrandAgent]
    ) -> Dict[str, Any]:
        """
        Create execution plan for workflow.
        
        Args:
            workflow: Workflow to schedule
            workflow_def: Workflow definition
            available_agents: List of available agents
            
        Returns:
            Dict containing execution plan
        """
        # Analyze workflow structure
        stages = self._analyze_workflow(workflow_def)
        
        # Create execution plan
        return {
            "workflow_id": workflow_def.get("id"),
            "stages": self._plan_stages(stages, available_agents),
            "continue_on_failure": workflow_def.get("continue_on_failure", False)
        }
        
    def _analyze_workflow(
        self,
        workflow_def: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze workflow to determine stage dependencies.
        
        Args:
            workflow_def: Workflow definition
            
        Returns:
            List of analyzed stages
        """
        stages = workflow_def.get("stages", [])
        
        # Build dependency graph
        dependency_graph = {}
        for stage in stages:
            stage_name = stage["name"]
            dependencies = stage.get("dependencies", [])
            dependency_graph[stage_name] = dependencies
            
        # Detect cycles
        visited = set()
        temp_visited = set()
        
        def has_cycle(node: str) -> bool:
            if node in temp_visited:
                return True
            if node in visited:
                return False
                
            temp_visited.add(node)
            
            for dep in dependency_graph.get(node, []):
                if has_cycle(dep):
                    return True
                    
            temp_visited.remove(node)
            visited.add(node)
            return False
            
        # Check for cycles
        for stage_name in dependency_graph:
            if has_cycle(stage_name):
                raise ValueError(f"Circular dependency detected at stage {stage_name}")
                
        return stages
        
    def _plan_stages(
        self,
        stages: List[Dict[str, Any]],
        available_agents: List[StrandAgent]
    ) -> List[Dict[str, Any]]:
        """
        Plan execution order of stages.
        
        Args:
            stages: List of workflow stages
            available_agents: List of available agents
            
        Returns:
            List of stages with execution plan
        """
        # Create execution plan for each stage
        planned_stages = []
        for stage in stages:
            # Plan task execution
            tasks = self._plan_tasks(
                stage.get("tasks", []),
                available_agents
            )
            
            planned_stages.append({
                "name": stage["name"],
                "tasks": tasks,
                "dependencies": stage.get("dependencies", []),
                "estimated_duration": self._estimate_duration(tasks)
            })
            
        # Order stages based on dependencies
        return self._order_stages(planned_stages)
        
    def _plan_tasks(
        self,
        tasks: List[Dict[str, Any]],
        available_agents: List[StrandAgent]
    ) -> List[Dict[str, Any]]:
        """
        Plan execution of tasks within a stage.
        
        Args:
            tasks: List of tasks
            available_agents: List of available agents
            
        Returns:
            List of tasks with execution plan
        """
        planned_tasks = []
        for task in tasks:
            # Find suitable agent
            agent = self._select_agent(task, available_agents)
            if not agent:
                raise ValueError(f"No suitable agent found for task: {task.get('name')}")
                
            planned_tasks.append({
                **task,
                "assigned_agent_id": id(agent),
                "estimated_duration": self._estimate_task_duration(task)
            })
            
        return planned_tasks
        
    def _order_stages(
        self,
        stages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Order stages based on dependencies.
        
        Args:
            stages: List of stages with execution plan
            
        Returns:
            Ordered list of stages
        """
        # Build stage index
        stage_index = {stage["name"]: stage for stage in stages}
        
        # Topological sort
        ordered = []
        visited = set()
        temp_visited = set()
        
        def visit(stage_name: str) -> None:
            if stage_name in temp_visited:
                raise ValueError(f"Circular dependency detected at stage {stage_name}")
            if stage_name in visited:
                return
                
            temp_visited.add(stage_name)
            
            stage = stage_index[stage_name]
            for dep in stage["dependencies"]:
                visit(dep)
                
            temp_visited.remove(stage_name)
            visited.add(stage_name)
            ordered.append(stage)
            
        for stage in stages:
            if stage["name"] not in visited:
                visit(stage["name"])
                
        return ordered
        
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
        
    def _estimate_task_duration(
        self,
        task: Dict[str, Any]
    ) -> float:
        """
        Estimate duration of a task.
        
        Args:
            task: Task definition
            
        Returns:
            Estimated duration in seconds
        """
        # Simple estimation based on task type
        base_duration = 60  # Default 1 minute
        
        if task.get("type") == "long_running":
            base_duration = 300  # 5 minutes
        elif task.get("type") == "quick":
            base_duration = 10  # 10 seconds
            
        # Adjust for complexity
        complexity = task.get("complexity", 1)
        return base_duration * complexity
        
    def _estimate_duration(
        self,
        tasks: List[Dict[str, Any]]
    ) -> float:
        """
        Estimate total duration for a list of tasks.
        
        Args:
            tasks: List of tasks
            
        Returns:
            Estimated total duration in seconds
        """
        # Simple sum of task durations
        # Could be improved with parallel execution consideration
        return sum(
            task.get("estimated_duration", self._estimate_task_duration(task))
            for task in tasks
        )
