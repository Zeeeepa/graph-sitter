"""
Workflow Engine

Orchestrates task execution using ControlFlow, Prefect, and Codegen SDK.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from graph_sitter.shared.logging.get_logger import get_logger
from .models import FlowStatus, TaskStatus, WorkflowEvent

logger = get_logger(__name__)


class WorkflowEngine:
    """Handles workflow execution and monitoring"""
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize the workflow engine"""
        logger.info("Initializing WorkflowEngine...")
        
    async def start_workflow(self, project_id: str):
        """Start workflow for a project"""
        project = await self.dashboard.project_manager.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Update project flow status
        await self.dashboard.project_manager.update_project(project_id, {
            "flow_enabled": True,
            "flow_status": FlowStatus.RUNNING
        })
        
        # Track active workflow
        self.active_workflows[project_id] = {
            "started_at": datetime.utcnow(),
            "status": "running"
        }
        
        # Create workflow event
        event = WorkflowEvent(
            id=f"workflow-start-{project_id}-{int(datetime.utcnow().timestamp())}",
            project_id=project_id,
            event_type="flow_started",
            source="workflow_engine",
            message=f"Workflow started for project {project.name}",
            severity="success"
        )
        
        # Broadcast event
        await self.dashboard.broadcast_event(event)
        
        logger.info(f"Started workflow for project {project_id}")
    
    async def stop_workflow(self, project_id: str):
        """Stop workflow for a project"""
        project = await self.dashboard.project_manager.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Update project flow status
        await self.dashboard.project_manager.update_project(project_id, {
            "flow_status": FlowStatus.STOPPED
        })
        
        # Remove from active workflows
        if project_id in self.active_workflows:
            del self.active_workflows[project_id]
        
        # Create workflow event
        event = WorkflowEvent(
            id=f"workflow-stop-{project_id}-{int(datetime.utcnow().timestamp())}",
            project_id=project_id,
            event_type="flow_stopped",
            source="workflow_engine",
            message=f"Workflow stopped for project {project.name}",
            severity="info"
        )
        
        # Broadcast event
        await self.dashboard.broadcast_event(event)
        
        logger.info(f"Stopped workflow for project {project_id}")
    
    async def execute_task(self, task_id: str):
        """Execute a specific task"""
        # This would integrate with Codegen SDK, ControlFlow, and Prefect
        # For testing, we'll simulate task execution
        logger.info(f"Executing task {task_id}")
        
        # Create task execution event
        event = WorkflowEvent(
            id=f"task-execute-{task_id}-{int(datetime.utcnow().timestamp())}",
            project_id="unknown",  # Would be determined from task
            task_id=task_id,
            event_type="task_started",
            source="workflow_engine",
            message=f"Task {task_id} execution started",
            severity="info"
        )
        
        await self.dashboard.broadcast_event(event)
    
    async def stop(self):
        """Stop the workflow engine"""
        logger.info("Stopping WorkflowEngine...")
        # Stop all active workflows
        for project_id in list(self.active_workflows.keys()):
            await self.stop_workflow(project_id)

