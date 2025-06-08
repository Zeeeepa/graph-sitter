"""Main dashboard application.

This module provides the main dashboard application with real-time
project monitoring, workflow management, and integration features.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models import Project, ProjectPlan, ProjectRequirements, ProjectStatus
from .services.integration_service import IntegrationService
from .services.websocket_service import WebSocketService

logger = logging.getLogger(__name__)

class DashboardApp:
    """Main dashboard application."""

    def __init__(self) -> None:
        """Initialize dashboard application."""
        self.app = FastAPI(title="Contexten Dashboard")
        self.integration_service = IntegrationService()
        self.websocket_service = WebSocketService()
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Set up application middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self) -> None:
        """Set up application routes."""
        # Health check
        @self.app.get("/health")
        async def health_check() -> Dict[str, str]:
            return {
                "status": "healthy",
                "timestamp": datetime.now(UTC).isoformat()
            }

        # Project management
        @self.app.post("/projects")
        async def create_project(
            name: str,
            repository: str,
            requirements: Optional[ProjectRequirements] = None
        ) -> Dict[str, Any]:
            try:
                project = await self.integration_service.initialize_project(
                    project_name=name,
                    repository=repository,
                    requirements=requirements
                )
                return {
                    "success": True,
                    "data": {
                        "project_id": project.id,
                        "name": project.name,
                        "status": project.status
                    }
                }
            except Exception as e:
                logger.error(f"Failed to create project: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/projects/{project_id}/plan")
        async def generate_plan(
            project_id: str,
            requirements: ProjectRequirements
        ) -> Dict[str, Any]:
            try:
                plan = await self.integration_service.generate_project_plan(
                    project_id=project_id,
                    requirements=requirements
                )
                return {
                    "success": True,
                    "data": {
                        "plan_id": plan.id,
                        "tasks": plan.tasks
                    }
                }
            except Exception as e:
                logger.error(f"Failed to generate plan: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/projects/{project_id}/flow/start")
        async def start_flow(project_id: str) -> Dict[str, Any]:
            try:
                await self.integration_service.start_project_flow(project_id)
                return {
                    "success": True,
                    "message": "Flow started successfully"
                }
            except Exception as e:
                logger.error(f"Failed to start flow: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/projects/{project_id}/flow/stop")
        async def stop_flow(project_id: str) -> Dict[str, Any]:
            try:
                await self.integration_service.stop_project_flow(project_id)
                return {
                    "success": True,
                    "message": "Flow stopped successfully"
                }
            except Exception as e:
                logger.error(f"Failed to stop flow: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/projects/{project_id}/status")
        async def get_project_status(project_id: str) -> Dict[str, Any]:
            try:
                status = await self.integration_service.get_project_status(project_id)
                return {
                    "success": True,
                    "data": status
                }
            except Exception as e:
                logger.error(f"Failed to get project status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/projects/{project_id}/events")
        async def get_project_events(
            project_id: str,
            limit: int = 100
        ) -> Dict[str, Any]:
            try:
                events = await self.integration_service.get_project_events(
                    project_id=project_id,
                    limit=limit
                )
                return {
                    "success": True,
                    "data": {
                        "events": [event.dict() for event in events]
                    }
                }
            except Exception as e:
                logger.error(f"Failed to get project events: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # WebSocket connection
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            client_id = str(uuid.uuid4())
            try:
                await self.websocket_service.handle_connection(websocket, client_id)
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"WebSocket error: {e}")

    async def start(self) -> None:
        """Start dashboard application."""
        await self.websocket_service.start()

    async def stop(self) -> None:
        """Stop dashboard application."""
        await self.websocket_service.stop()

    def register_event_handler(
        self,
        event_type: str,
        handler: Any
    ) -> None:
        """Register event handler."""
        self.integration_service.register_event_handler(event_type, handler)

    async def broadcast_project_update(
        self,
        project_id: str,
        update_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Broadcast project update."""
        await self.websocket_service.broadcast_project_update(
            project_id=project_id,
            update_type=update_type,
            data=data
        )

    async def broadcast_workflow_event(
        self,
        project_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Broadcast workflow event."""
        await self.websocket_service.broadcast_workflow_event(
            project_id=project_id,
            event_type=event_type,
            event_data=event_data
        )

    async def broadcast_metrics_update(
        self,
        project_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Broadcast metrics update."""
        await self.websocket_service.broadcast_metrics_update(
            project_id=project_id,
            metrics=metrics
        )

