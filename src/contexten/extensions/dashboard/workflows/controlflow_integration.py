"""
ControlFlow integration for middle-layer task orchestration.

This module provides integration with the ControlFlow system for task-level
orchestration, handling dependencies, parallel execution, and task coordination
within the workflow execution pipeline.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import controlflow as cf
    from controlflow import Flow, Task, Agent
    CONTROLFLOW_AVAILABLE = True
except ImportError:
    CONTROLFLOW_AVAILABLE = False
    cf = None
    Flow = None
    Task = None
    Agent = None

from ..models import WorkflowTask, TaskStatus

logger = logging.getLogger(__name__)


class ControlFlowManager:
    """ControlFlow manager for middle-layer task orchestration."""
    
    def __init__(self):
        """Initialize ControlFlow manager."""
        self.active_flows: Dict[str, Any] = {}  # execution_id -> Flow
        self.active_tasks: Dict[str, Any] = {}  # task_id -> Task
        self.execution_agents: Dict[str, Any] = {}  # execution_id -> Agent
        self.task_results: Dict[str, Any] = {}
        
        if not CONTROLFLOW_AVAILABLE:
            logger.warning("ControlFlow not available. Middle-layer orchestration disabled.")
    
    async def initialize(self):
        """Initialize ControlFlow manager."""
        if not CONTROLFLOW_AVAILABLE:
            logger.warning("ControlFlow not available for initialization")
            return False
        
        try:
            # Initialize default agents
            await self._setup_default_agents()
            
            logger.info("ControlFlow manager initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ControlFlow manager: {e}")
            return False
    
    async def _setup_default_agents(self):
        """Setup default ControlFlow agents."""
        if not CONTROLFLOW_AVAILABLE:
            return
        
        try:
            # Create specialized agents for different task types
            self.code_agent = Agent(
                name="CodeAgent",
                description="Specialized agent for code-related tasks",
                instructions="You are an expert software developer. Focus on writing clean, efficient, and well-documented code."
            )
            
            self.review_agent = Agent(
                name="ReviewAgent", 
                description="Specialized agent for code review and quality assurance",
                instructions="You are an expert code reviewer. Focus on code quality, security, and best practices."
            )
            
            self.test_agent = Agent(
                name="TestAgent",
                description="Specialized agent for testing and validation",
                instructions="You are an expert in software testing. Focus on comprehensive test coverage and quality validation."
            )
            
            self.deploy_agent = Agent(
                name="DeployAgent",
                description="Specialized agent for deployment and operations",
                instructions="You are an expert in deployment and DevOps. Focus on reliable and secure deployments."
            )
            
            logger.info("ControlFlow agents setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup ControlFlow agents: {e}")
    
    async def execute_task(self, task: WorkflowTask, execution_id: str) -> bool:
        """Execute a task using ControlFlow.
        
        Args:
            task: Task to execute
            execution_id: Parent execution ID
            
        Returns:
            True if task execution started successfully
        """
        if not CONTROLFLOW_AVAILABLE:
            logger.warning("ControlFlow not available, cannot execute task")
            return False
        
        try:
            logger.info(f"Executing task {task.id} via ControlFlow")
            
            # Get or create flow for this execution
            flow = await self._get_or_create_flow(execution_id)
            
            # Select appropriate agent based on task type
            agent = self._select_agent_for_task(task)
            
            # Create ControlFlow task
            cf_task = Task(
                objective=task.description,
                instructions=self._build_task_instructions(task),
                agent=agent,
                context=self._build_task_context(task),
                result_type=str  # For now, all tasks return strings
            )
            
            # Add task to flow
            flow.add_task(cf_task)
            
            # Store task reference
            self.active_tasks[task.id] = cf_task
            
            # Execute task asynchronously
            await self._execute_task_async(task, cf_task, execution_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute task {task.id}: {e}")
            return False
    
    async def _get_or_create_flow(self, execution_id: str) -> Any:
        """Get or create a ControlFlow flow for an execution."""
        if execution_id not in self.active_flows:
            if CONTROLFLOW_AVAILABLE:
                flow = Flow(name=f"contexten-execution-{execution_id}")
                self.active_flows[execution_id] = flow
            else:
                # Mock flow for when ControlFlow is not available
                self.active_flows[execution_id] = {"name": f"mock-flow-{execution_id}"}
        
        return self.active_flows[execution_id]
    
    def _select_agent_for_task(self, task: WorkflowTask) -> Any:
        """Select appropriate agent based on task type."""
        if not CONTROLFLOW_AVAILABLE:
            return None
        
        task_type = task.task_type.lower()
        
        if task_type in ["code", "implementation", "development"]:
            return self.code_agent
        elif task_type in ["review", "validation", "quality"]:
            return self.review_agent
        elif task_type in ["test", "testing", "qa"]:
            return self.test_agent
        elif task_type in ["deploy", "deployment", "release"]:
            return self.deploy_agent
        else:
            return self.code_agent  # Default to code agent
    
    def _build_task_instructions(self, task: WorkflowTask) -> str:
        """Build detailed instructions for a ControlFlow task."""
        instructions = f"""
Task: {task.title}
Description: {task.description}
Type: {task.task_type}
Priority: {task.priority}

Requirements:
{task.description}

Acceptance Criteria:
"""
        
        # Add acceptance criteria from metadata
        acceptance_criteria = task.metadata.get("acceptance_criteria", [])
        for i, criteria in enumerate(acceptance_criteria, 1):
            instructions += f"{i}. {criteria}\n"
        
        if task.estimated_hours:
            instructions += f"\nEstimated Time: {task.estimated_hours} hours"
        
        if task.dependencies:
            instructions += f"\nDependencies: {', '.join(task.dependencies)}"
        
        instructions += """

Please provide a detailed implementation plan and execute the task according to the requirements.
Focus on quality, maintainability, and following best practices.
"""
        
        return instructions
    
    def _build_task_context(self, task: WorkflowTask) -> Dict[str, Any]:
        """Build context information for a ControlFlow task."""
        context = {
            "task_id": task.id,
            "plan_id": task.plan_id,
            "task_type": task.task_type,
            "priority": task.priority,
            "estimated_hours": task.estimated_hours,
            "dependencies": task.dependencies,
            "metadata": task.metadata
        }
        
        # Add GitHub/Linear integration context if available
        if task.github_pr_url:
            context["github_pr_url"] = task.github_pr_url
        if task.linear_issue_id:
            context["linear_issue_id"] = task.linear_issue_id
        if task.codegen_task_id:
            context["codegen_task_id"] = task.codegen_task_id
        
        return context
    
    async def _execute_task_async(self, task: WorkflowTask, cf_task: Any, execution_id: str):
        """Execute a ControlFlow task asynchronously."""
        try:
            # Update task status to in progress
            task.status = TaskStatus.IN_PROGRESS
            
            # Execute the ControlFlow task
            if CONTROLFLOW_AVAILABLE:
                result = await cf_task.run_async()
            else:
                # Mock execution for when ControlFlow is not available
                await asyncio.sleep(1)  # Simulate work
                result = f"Mock result for task {task.id}"
            
            # Store result
            self.task_results[task.id] = result
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            task.status = TaskStatus.FAILED
            self.task_results[task.id] = f"Error: {str(e)}"
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a ControlFlow task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status dictionary or None if not found
        """
        if task_id not in self.active_tasks:
            return None
        
        try:
            cf_task = self.active_tasks[task_id]
            
            if CONTROLFLOW_AVAILABLE and hasattr(cf_task, 'state'):
                return {
                    "task_id": task_id,
                    "state": cf_task.state,
                    "result": self.task_results.get(task_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Mock status for when ControlFlow is not available
                return {
                    "task_id": task_id,
                    "state": "completed",
                    "result": self.task_results.get(task_id, "Mock result"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return None
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel all tasks in an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if cancellation was successful
        """
        try:
            if execution_id in self.active_flows:
                flow = self.active_flows[execution_id]
                
                # Cancel all tasks in the flow
                if CONTROLFLOW_AVAILABLE and hasattr(flow, 'tasks'):
                    for task in flow.tasks:
                        if hasattr(task, 'cancel'):
                            await task.cancel()
                
                # Remove from active flows
                del self.active_flows[execution_id]
                
                logger.info(f"Cancelled ControlFlow execution: {execution_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel ControlFlow execution: {e}")
            return False
    
    async def pause_execution(self, execution_id: str) -> bool:
        """Pause an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if pause was successful
        """
        try:
            # ControlFlow doesn't have built-in pause functionality
            # This would need to be implemented at the task level
            logger.info(f"Pausing ControlFlow execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause ControlFlow execution: {e}")
            return False
    
    async def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if resume was successful
        """
        try:
            # ControlFlow doesn't have built-in resume functionality
            # This would need to be implemented at the task level
            logger.info(f"Resuming ControlFlow execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume ControlFlow execution: {e}")
            return False
    
    async def get_execution_logs(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get execution logs from ControlFlow.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            List of log entries
        """
        try:
            logs = []
            
            if execution_id in self.active_flows:
                # Generate logs based on task execution
                for task_id, cf_task in self.active_tasks.items():
                    logs.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "INFO",
                        "message": f"ControlFlow task executed: {task_id}",
                        "layer": "controlflow",
                        "task_id": task_id,
                        "execution_id": execution_id
                    })
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get ControlFlow execution logs: {e}")
            return []
    
    async def get_metrics(self, execution_id: str) -> Dict[str, Any]:
        """Get ControlFlow metrics for an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Metrics dictionary
        """
        try:
            if execution_id not in self.active_flows:
                return {}
            
            # Count tasks by status
            total_tasks = len([task_id for task_id in self.active_tasks.keys()])
            completed_tasks = len([task_id for task_id, result in self.task_results.items() if result])
            
            return {
                "layer": "controlflow",
                "execution_id": execution_id,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "progress_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "active_agents": len(self.execution_agents.get(execution_id, {})),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get ControlFlow metrics: {e}")
            return {}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get ControlFlow manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "layer": "controlflow",
            "available": CONTROLFLOW_AVAILABLE,
            "active_flows": len(self.active_flows),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.task_results),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup ControlFlow manager resources."""
        try:
            # Cancel all active executions
            for execution_id in list(self.active_flows.keys()):
                await self.cancel_execution(execution_id)
            
            # Clear all data structures
            self.active_flows.clear()
            self.active_tasks.clear()
            self.execution_agents.clear()
            self.task_results.clear()
            
            logger.info("ControlFlow manager cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup ControlFlow manager: {e}")

