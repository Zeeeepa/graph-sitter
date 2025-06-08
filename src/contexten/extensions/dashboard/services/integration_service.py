"""Integration service for dashboard.

This module provides comprehensive integration with various services
including GitHub, Linear, Codegen, and Flow management.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Tuple

from ..models import Project, ProjectPlan, ProjectRequirements, ProjectStatus, WorkflowEvent
from .codegen_service import CodegenService
from .monitoring_service import MonitoringService
from .project_service import ProjectService
from .quality_service import QualityService
from .strands_orchestrator import StrandsOrchestrator
from .workflow_service import WorkflowService

logger = logging.getLogger(__name__)

class IntegrationService:
    """Main integration service for dashboard functionality."""

    def __init__(self) -> None:
        """Initialize integration service."""
        self.project_service = ProjectService()
        self.codegen_service = CodegenService()
        self.workflow_service = WorkflowService()
        self.quality_service = QualityService()
        self.monitoring_service = MonitoringService()
        self.strands_orchestrator = StrandsOrchestrator()
        self._event_handlers: Dict[str, List[Any]] = {}
        self._active_flows: Dict[str, Dict[str, Any]] = {}

    async def initialize_project(
        self,
        project_name: str,
        repository: str,
        requirements: Optional[ProjectRequirements] = None
    ) -> Project:
        """Initialize a new project with requirements."""
        try:
            # Create project
            project = await self.project_service.create_project(
                name=project_name,
                repository=repository
            )

            # Add requirements if provided
            if requirements:
                await self.project_service.update_requirements(
                    project_id=project.id,
                    requirements=requirements
                )

                # Generate initial plan
                plan = await self.generate_project_plan(
                    project_id=project.id,
                    requirements=requirements
                )
                project.plan = plan

            # Initialize monitoring
            await self.monitoring_service.initialize_project_monitoring(project.id)

            return project

        except Exception as e:
            logger.error(f"Failed to initialize project: {e}")
            raise

    async def generate_project_plan(
        self,
        project_id: str,
        requirements: ProjectRequirements
    ) -> ProjectPlan:
        """Generate project plan using Codegen."""
        try:
            # Get project context
            project = await self.project_service.get_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            # Generate plan using Codegen
            plan = await self.codegen_service.generate_plan(
                project_name=project.name,
                repository=project.repository,
                requirements=requirements
            )

            # Save plan
            await self.project_service.update_plan(
                project_id=project_id,
                plan=plan
            )

            return plan

        except Exception as e:
            logger.error(f"Failed to generate project plan: {e}")
            raise

    async def start_project_flow(
        self,
        project_id: str,
        plan_id: Optional[str] = None
    ) -> None:
        """Start project workflow execution."""
        try:
            # Get project and plan
            project = await self.project_service.get_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            plan = project.plan if not plan_id else await self.project_service.get_plan(plan_id)
            if not plan:
                raise ValueError("No plan available")

            # Initialize workflow
            workflow = await self.workflow_service.create_workflow(
                project_id=project_id,
                plan=plan
            )

            # Start Strands orchestration
            orchestration = await self.strands_orchestrator.start_orchestration(
                project_id=project_id,
                workflow_id=workflow.id,
                plan=plan
            )

            # Track active flow
            self._active_flows[project_id] = {
                "workflow_id": workflow.id,
                "orchestration_id": orchestration.id,
                "started_at": datetime.now(UTC),
                "status": "running"
            }

            # Update project status
            await self.project_service.update_status(
                project_id=project_id,
                status=ProjectStatus.ACTIVE,
                flow_enabled=True
            )

            # Start monitoring
            await self.monitoring_service.start_flow_monitoring(
                project_id=project_id,
                workflow_id=workflow.id
            )

        except Exception as e:
            logger.error(f"Failed to start project flow: {e}")
            raise

    async def stop_project_flow(self, project_id: str) -> None:
        """Stop project workflow execution."""
        try:
            if project_id not in self._active_flows:
                return

            flow_info = self._active_flows[project_id]
            workflow_id = flow_info["workflow_id"]
            orchestration_id = flow_info["orchestration_id"]

            # Stop orchestration
            await self.strands_orchestrator.stop_orchestration(orchestration_id)

            # Stop workflow
            await self.workflow_service.stop_workflow(workflow_id)

            # Update project status
            await self.project_service.update_status(
                project_id=project_id,
                flow_enabled=False
            )

            # Stop monitoring
            await self.monitoring_service.stop_flow_monitoring(project_id)

            # Remove from active flows
            self._active_flows.pop(project_id)

        except Exception as e:
            logger.error(f"Failed to stop project flow: {e}")
            raise

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project status."""
        try:
            # Get project
            project = await self.project_service.get_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            # Get workflow status
            workflow_status = "stopped"
            workflow_progress = 0.0
            if project_id in self._active_flows:
                workflow_id = self._active_flows[project_id]["workflow_id"]
                workflow = await self.workflow_service.get_workflow(workflow_id)
                if workflow:
                    workflow_status = workflow.status
                    workflow_progress = workflow.progress

            # Get quality metrics
            quality_metrics = await self.quality_service.get_project_metrics(project_id)

            # Get monitoring metrics
            monitoring_metrics = await self.monitoring_service.get_project_metrics(project_id)

            return {
                "project_status": project.status,
                "workflow_status": workflow_status,
                "workflow_progress": workflow_progress,
                "quality_metrics": quality_metrics,
                "monitoring_metrics": monitoring_metrics,
                "last_updated": datetime.now(UTC).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get project status: {e}")
            raise

    async def get_project_events(
        self,
        project_id: str,
        limit: int = 100
    ) -> List[WorkflowEvent]:
        """Get recent project events."""
        try:
            # Get workflow events
            workflow_events = []
            if project_id in self._active_flows:
                workflow_id = self._active_flows[project_id]["workflow_id"]
                workflow_events = await self.workflow_service.get_workflow_events(
                    workflow_id,
                    limit=limit
                )

            # Get quality events
            quality_events = await self.quality_service.get_project_events(
                project_id,
                limit=limit
            )

            # Combine and sort events
            all_events = workflow_events + quality_events
            all_events.sort(key=lambda x: x.timestamp, reverse=True)

            return all_events[:limit]

        except Exception as e:
            logger.error(f"Failed to get project events: {e}")
            raise

    def register_event_handler(
        self,
        event_type: str,
        handler: Any
    ) -> None:
        """Register event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def handle_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Handle incoming event."""
        try:
            handlers = self._event_handlers.get(event_type, [])
            for handler in handlers:
                try:
                    await handler(event_data)
                except Exception as e:
                    logger.error(f"Event handler failed: {e}")

        except Exception as e:
            logger.error(f"Failed to handle event: {e}")
            raise

