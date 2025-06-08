#!/usr/bin/env python3
"""
ControlFlow Orchestrator Module
Handles orchestration and coordination of multiple agents and workflows.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import uuid
from datetime import datetime

from ..base.interfaces import BaseOrchestrator

logger = logging.getLogger(__name__)


class ControlFlowOrchestrator(BaseOrchestrator):
    """Orchestrator for ControlFlow workflows."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.active_workflows: Dict[str, Any] = {}
        self.agents: Dict[str, Any] = {}
        self.scheduled_tasks: Dict[str, Any] = {}
    
    async def _initialize_impl(self) -> None:
        """Initialize the ControlFlow orchestrator."""
        self.logger.info("Initializing ControlFlow orchestrator")
        # Initialize any required resources
        pass
    
    async def _handle_impl(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Handle orchestration requests."""
        action = payload.get("action")
        
        if action == "start_workflow":
            return await self.orchestrate_flow(payload.get("workflow_config", {}))
        elif action == "schedule_task":
            return await self.schedule_task(payload.get("task_config", {}))
        elif action == "get_status":
            return await self.get_flow_status(payload.get("flow_id"))
        else:
            return {"error": f"Unknown action: {action}", "status": "failed"}
    
    async def orchestrate_flow(self, flow_config: Dict[str, Any]) -> str:
        """Orchestrate a flow execution."""
        flow_id = str(uuid.uuid4())
        
        workflow = {
            "workflow_id": flow_id,
            "config": flow_config,
            "status": "running",
            "tasks": flow_config.get("tasks", []),
            "assigned_agents": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.active_workflows[flow_id] = workflow
        
        # Assign agents to tasks
        await self._assign_agents_to_workflow(workflow)
        
        self.logger.info(f"Started workflow: {flow_id}")
        return flow_id
    
    async def schedule_task(self, task_config: Dict[str, Any]) -> str:
        """Schedule a task for execution."""
        task_id = str(uuid.uuid4())
        
        task = {
            "task_id": task_id,
            "config": task_config,
            "status": "scheduled",
            "scheduled_at": datetime.utcnow().isoformat(),
            "agent_id": None
        }
        
        self.scheduled_tasks[task_id] = task
        
        # Try to assign an available agent
        await self._assign_agent_to_task(task)
        
        self.logger.info(f"Scheduled task: {task_id}")
        return task_id
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get flow execution status."""
        if flow_id not in self.active_workflows:
            return {"error": f"Workflow {flow_id} not found", "status": "not_found"}
        
        workflow = self.active_workflows[flow_id]
        return {
            "workflow_id": flow_id,
            "status": workflow["status"],
            "tasks": workflow["tasks"],
            "assigned_agents": workflow["assigned_agents"],
            "created_at": workflow["created_at"],
            "updated_at": workflow["updated_at"]
        }
    
    async def register_agent(self, agent_id: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register an agent with the orchestrator."""
        logger.info(f"Registering agent: {agent_id}")
        
        agent = {
            "agent_id": agent_id,
            "config": agent_config,
            "status": "available",
            "capabilities": agent_config.get("capabilities", [])
        }
        
        self.agents[agent_id] = agent
        return agent
    
    async def start_workflow(self, workflow_id: str, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new workflow."""
        logger.info(f"Starting workflow: {workflow_id}")
        
        workflow = {
            "workflow_id": workflow_id,
            "config": workflow_config,
            "status": "running",
            "tasks": workflow_config.get("tasks", []),
            "assigned_agents": []
        }
        
        self.active_workflows[workflow_id] = workflow
        
        # Assign agents to tasks
        await self._assign_agents_to_workflow(workflow)
        
        return workflow
    
    async def _assign_agents_to_workflow(self, workflow: Dict[str, Any]) -> None:
        """Assign available agents to workflow tasks."""
        available_agents = [agent for agent in self.agents.values() 
                          if agent["status"] == "available"]
        
        for task in workflow["tasks"]:
            required_capabilities = task.get("required_capabilities", [])
            
            # Find suitable agent
            for agent in available_agents:
                agent_capabilities = agent["capabilities"]
                if all(cap in agent_capabilities for cap in required_capabilities):
                    workflow["assigned_agents"].append(agent["agent_id"])
                    agent["status"] = "busy"
                    break
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow."""
        return self.active_workflows.get(workflow_id)


# Alias for backward compatibility and expected import name
FlowOrchestrator = ControlFlowOrchestrator
