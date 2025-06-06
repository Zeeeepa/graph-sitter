"""
MCP (Model Context Protocol) integration for bottom-layer agentic flows.

This module provides integration with MCP for granular agentic task execution,
enabling fine-grained control over AI agents and their interactions with
various tools and services.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

try:
    # Import MCP client from the existing codebase
    from contexten.mcp.mcp_client import MCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MCPClient = None

from ..models import WorkflowTask, TaskStatus

logger = logging.getLogger(__name__)


class MCPAgentManager:
    """MCP agent manager for bottom-layer agentic flows."""
    
    def __init__(self):
        """Initialize MCP agent manager."""
        self.mcp_clients: Dict[str, Any] = {}  # execution_id -> MCPClient
        self.active_agents: Dict[str, Dict[str, Any]] = {}  # execution_id -> agents
        self.task_executions: Dict[str, Dict[str, Any]] = {}  # task_id -> execution_info
        self.agent_tools: Dict[str, List[str]] = {}  # agent_id -> available_tools
        
        if not MCP_AVAILABLE:
            logger.warning("MCP not available. Bottom-layer agentic flows disabled.")
    
    async def initialize(self):
        """Initialize MCP agent manager."""
        if not MCP_AVAILABLE:
            logger.warning("MCP not available for initialization")
            return False
        
        try:
            # Initialize default MCP tools and capabilities
            await self._setup_default_tools()
            
            logger.info("MCP agent manager initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP agent manager: {e}")
            return False
    
    async def _setup_default_tools(self):
        """Setup default MCP tools and capabilities."""
        if not MCP_AVAILABLE:
            return
        
        try:
            # Define available tools for different agent types
            self.default_tools = {
                "code_agent": [
                    "file_operations",
                    "git_operations", 
                    "code_analysis",
                    "syntax_checking",
                    "dependency_management"
                ],
                "review_agent": [
                    "code_analysis",
                    "quality_metrics",
                    "security_scanning",
                    "style_checking",
                    "documentation_review"
                ],
                "test_agent": [
                    "test_execution",
                    "coverage_analysis",
                    "test_generation",
                    "performance_testing",
                    "integration_testing"
                ],
                "deploy_agent": [
                    "deployment_tools",
                    "infrastructure_management",
                    "monitoring_setup",
                    "rollback_capabilities",
                    "health_checks"
                ]
            }
            
            logger.info("MCP default tools setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup MCP tools: {e}")
    
    async def execute_task(self, task: WorkflowTask, execution_id: str) -> bool:
        """Execute a task using MCP agents.
        
        Args:
            task: Task to execute
            execution_id: Parent execution ID
            
        Returns:
            True if task execution started successfully
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP not available, cannot execute task")
            return False
        
        try:
            logger.info(f"Executing task {task.id} via MCP agents")
            
            # Get or create MCP client for this execution
            mcp_client = await self._get_or_create_mcp_client(execution_id)
            
            # Create specialized agent for this task
            agent_config = await self._create_agent_config(task)
            agent_id = await self._create_agent(mcp_client, agent_config)
            
            # Execute task with the agent
            execution_info = {
                "task_id": task.id,
                "agent_id": agent_id,
                "execution_id": execution_id,
                "started_at": datetime.utcnow(),
                "status": "running",
                "progress": 0.0
            }
            
            self.task_executions[task.id] = execution_info
            
            # Start asynchronous task execution
            await self._execute_task_with_agent(task, agent_id, mcp_client)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute task {task.id} with MCP: {e}")
            return False
    
    async def _get_or_create_mcp_client(self, execution_id: str) -> Any:
        """Get or create MCP client for an execution."""
        if execution_id not in self.mcp_clients:
            if MCP_AVAILABLE:
                # Create new MCP client
                client = MCPClient()
                await client.initialize()
                self.mcp_clients[execution_id] = client
            else:
                # Mock client for when MCP is not available
                self.mcp_clients[execution_id] = {"type": "mock", "execution_id": execution_id}
        
        return self.mcp_clients[execution_id]
    
    async def _create_agent_config(self, task: WorkflowTask) -> Dict[str, Any]:
        """Create agent configuration based on task requirements."""
        task_type = task.task_type.lower()
        
        # Select appropriate tools based on task type
        if task_type in ["code", "implementation", "development"]:
            agent_type = "code_agent"
            capabilities = ["code_generation", "file_manipulation", "git_operations"]
        elif task_type in ["review", "validation", "quality"]:
            agent_type = "review_agent"
            capabilities = ["code_analysis", "quality_assessment", "security_review"]
        elif task_type in ["test", "testing", "qa"]:
            agent_type = "test_agent"
            capabilities = ["test_creation", "test_execution", "coverage_analysis"]
        elif task_type in ["deploy", "deployment", "release"]:
            agent_type = "deploy_agent"
            capabilities = ["deployment", "infrastructure", "monitoring"]
        else:
            agent_type = "general_agent"
            capabilities = ["general_purpose", "task_execution"]
        
        config = {
            "name": f"{agent_type}_{task.id}",
            "type": agent_type,
            "capabilities": capabilities,
            "tools": self.default_tools.get(agent_type, []),
            "task_context": {
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "requirements": task.metadata.get("acceptance_criteria", []),
                "estimated_hours": task.estimated_hours,
                "priority": task.priority
            },
            "execution_config": {
                "max_iterations": 10,
                "timeout_minutes": 60,
                "retry_attempts": 3,
                "quality_threshold": 0.8
            }
        }
        
        return config
    
    async def _create_agent(self, mcp_client: Any, agent_config: Dict[str, Any]) -> str:
        """Create an MCP agent with the specified configuration."""
        if not MCP_AVAILABLE:
            # Return mock agent ID
            return f"mock_agent_{agent_config['name']}"
        
        try:
            # Create agent using MCP client
            agent_id = await mcp_client.create_agent(agent_config)
            
            # Store agent tools
            self.agent_tools[agent_id] = agent_config["tools"]
            
            logger.info(f"Created MCP agent: {agent_id}")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create MCP agent: {e}")
            raise
    
    async def _execute_task_with_agent(self, task: WorkflowTask, agent_id: str, mcp_client: Any):
        """Execute a task using the specified MCP agent."""
        try:
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            
            if MCP_AVAILABLE:
                # Execute task with real MCP agent
                result = await self._run_agent_task(agent_id, task, mcp_client)
            else:
                # Mock execution
                await asyncio.sleep(2)  # Simulate work
                result = {
                    "status": "completed",
                    "output": f"Mock execution result for task {task.id}",
                    "artifacts": [],
                    "metrics": {"execution_time": 2.0, "quality_score": 0.85}
                }
            
            # Update task execution info
            if task.id in self.task_executions:
                self.task_executions[task.id].update({
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "result": result,
                    "progress": 100.0
                })
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            logger.info(f"MCP task {task.id} completed successfully")
            
        except Exception as e:
            logger.error(f"MCP task {task.id} failed: {e}")
            
            # Update task execution info
            if task.id in self.task_executions:
                self.task_executions[task.id].update({
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "error": str(e),
                    "progress": 0.0
                })
            
            task.status = TaskStatus.FAILED
    
    async def _run_agent_task(self, agent_id: str, task: WorkflowTask, mcp_client: Any) -> Dict[str, Any]:
        """Run a task with an MCP agent."""
        if not MCP_AVAILABLE:
            return {}
        
        try:
            # Prepare task prompt
            prompt = self._build_agent_prompt(task)
            
            # Execute with MCP agent
            response = await mcp_client.execute_with_agent(
                agent_id=agent_id,
                prompt=prompt,
                context=task.metadata
            )
            
            return {
                "status": "completed",
                "output": response.get("output", ""),
                "artifacts": response.get("artifacts", []),
                "metrics": response.get("metrics", {}),
                "tool_usage": response.get("tool_usage", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to run agent task: {e}")
            raise
    
    def _build_agent_prompt(self, task: WorkflowTask) -> str:
        """Build a detailed prompt for the MCP agent."""
        prompt = f"""
Task: {task.title}
Type: {task.task_type}
Priority: {task.priority}

Description:
{task.description}

Requirements:
"""
        
        # Add acceptance criteria
        acceptance_criteria = task.metadata.get("acceptance_criteria", [])
        for i, criteria in enumerate(acceptance_criteria, 1):
            prompt += f"{i}. {criteria}\n"
        
        prompt += f"""

Context:
- Estimated time: {task.estimated_hours} hours
- Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}
"""
        
        # Add integration context
        if task.github_pr_url:
            prompt += f"- GitHub PR: {task.github_pr_url}\n"
        if task.linear_issue_id:
            prompt += f"- Linear Issue: {task.linear_issue_id}\n"
        
        prompt += """

Instructions:
1. Analyze the task requirements carefully
2. Plan your approach step by step
3. Execute the task using available tools
4. Validate your work against the acceptance criteria
5. Provide a detailed summary of what was accomplished

Focus on quality, maintainability, and following best practices.
Use the available tools effectively to complete the task.
"""
        
        return prompt
    
    async def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the progress of an MCP task execution.
        
        Args:
            task_id: Task ID
            
        Returns:
            Progress information or None if not found
        """
        if task_id not in self.task_executions:
            return None
        
        execution_info = self.task_executions[task_id]
        
        return {
            "task_id": task_id,
            "agent_id": execution_info["agent_id"],
            "status": execution_info["status"],
            "progress": execution_info["progress"],
            "started_at": execution_info["started_at"].isoformat(),
            "completed_at": execution_info.get("completed_at", {}).isoformat() if execution_info.get("completed_at") else None,
            "result": execution_info.get("result"),
            "error": execution_info.get("error")
        }
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel all MCP agents in an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if cancellation was successful
        """
        try:
            # Cancel all tasks for this execution
            tasks_to_cancel = [
                task_id for task_id, info in self.task_executions.items()
                if info["execution_id"] == execution_id and info["status"] == "running"
            ]
            
            for task_id in tasks_to_cancel:
                execution_info = self.task_executions[task_id]
                agent_id = execution_info["agent_id"]
                
                if MCP_AVAILABLE and execution_id in self.mcp_clients:
                    mcp_client = self.mcp_clients[execution_id]
                    await mcp_client.cancel_agent(agent_id)
                
                # Update execution info
                execution_info.update({
                    "status": "cancelled",
                    "completed_at": datetime.utcnow(),
                    "progress": 0.0
                })
            
            # Cleanup MCP client
            if execution_id in self.mcp_clients:
                if MCP_AVAILABLE:
                    await self.mcp_clients[execution_id].cleanup()
                del self.mcp_clients[execution_id]
            
            logger.info(f"Cancelled MCP execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel MCP execution: {e}")
            return False
    
    async def pause_execution(self, execution_id: str) -> bool:
        """Pause MCP agents in an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if pause was successful
        """
        try:
            # Pause all running tasks for this execution
            for task_id, info in self.task_executions.items():
                if info["execution_id"] == execution_id and info["status"] == "running":
                    info["status"] = "paused"
            
            logger.info(f"Paused MCP execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause MCP execution: {e}")
            return False
    
    async def resume_execution(self, execution_id: str) -> bool:
        """Resume paused MCP agents in an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if resume was successful
        """
        try:
            # Resume all paused tasks for this execution
            for task_id, info in self.task_executions.items():
                if info["execution_id"] == execution_id and info["status"] == "paused":
                    info["status"] = "running"
            
            logger.info(f"Resumed MCP execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume MCP execution: {e}")
            return False
    
    async def get_execution_logs(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get execution logs from MCP agents.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            List of log entries
        """
        try:
            logs = []
            
            # Get logs from all tasks in this execution
            for task_id, info in self.task_executions.items():
                if info["execution_id"] == execution_id:
                    logs.append({
                        "timestamp": info["started_at"].isoformat(),
                        "level": "INFO",
                        "message": f"MCP agent task started: {task_id}",
                        "layer": "mcp",
                        "task_id": task_id,
                        "agent_id": info["agent_id"],
                        "execution_id": execution_id
                    })
                    
                    if info.get("completed_at"):
                        logs.append({
                            "timestamp": info["completed_at"].isoformat(),
                            "level": "INFO" if info["status"] == "completed" else "ERROR",
                            "message": f"MCP agent task {info['status']}: {task_id}",
                            "layer": "mcp",
                            "task_id": task_id,
                            "agent_id": info["agent_id"],
                            "execution_id": execution_id
                        })
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get MCP execution logs: {e}")
            return []
    
    async def get_metrics(self, execution_id: str) -> Dict[str, Any]:
        """Get MCP metrics for an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Metrics dictionary
        """
        try:
            # Count tasks by status for this execution
            execution_tasks = [
                info for info in self.task_executions.values()
                if info["execution_id"] == execution_id
            ]
            
            total_tasks = len(execution_tasks)
            completed_tasks = len([info for info in execution_tasks if info["status"] == "completed"])
            failed_tasks = len([info for info in execution_tasks if info["status"] == "failed"])
            running_tasks = len([info for info in execution_tasks if info["status"] == "running"])
            
            # Calculate average progress
            avg_progress = sum(info["progress"] for info in execution_tasks) / total_tasks if total_tasks > 0 else 0
            
            return {
                "layer": "mcp",
                "execution_id": execution_id,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "running_tasks": running_tasks,
                "progress_percentage": avg_progress,
                "active_agents": len(set(info["agent_id"] for info in execution_tasks if info["status"] == "running")),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get MCP metrics: {e}")
            return {}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get MCP manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "layer": "mcp",
            "available": MCP_AVAILABLE,
            "active_clients": len(self.mcp_clients),
            "active_executions": len(self.task_executions),
            "total_agents": len(self.agent_tools),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup MCP manager resources."""
        try:
            # Cancel all active executions
            for execution_id in list(self.mcp_clients.keys()):
                await self.cancel_execution(execution_id)
            
            # Clear all data structures
            self.mcp_clients.clear()
            self.active_agents.clear()
            self.task_executions.clear()
            self.agent_tools.clear()
            
            logger.info("MCP agent manager cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup MCP manager: {e}")

