#!/usr/bin/env python3
"""
ControlFlow Orchestrator Module
Handles orchestration and coordination of multiple agents and workflows.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class ControlFlowOrchestrator:
    """Orchestrator for ControlFlow workflows."""
    
    def __init__(self):
        self.active_workflows: Dict[str, Any] = {}
        self.agents: Dict[str, Any] = {}
        
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

