"""Dashboard API endpoints for the Contexten dashboard extension."""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    Project, Flow, Task, UserSettings, FlowStatus, TaskStatus, ServiceStatus,
    ServiceStatusResponse, ProjectCreateRequest, ProjectUpdateRequest,
    FlowStartRequest, PlanGenerateRequest
)
from .services.project_service import ProjectService
from .services.codegen_service import CodegenService
from .services.flow_engine import FlowEngine


class DashboardAPI:
    """Dashboard API class for handling REST endpoints and WebSocket connections."""
    
    def __init__(self, contexten_app=None):
        """Initialize the Dashboard API."""
        self.app = FastAPI(title="Contexten Dashboard API", version="1.0.0")
        self.contexten_app = contexten_app
        
        # Initialize services
        self.project_service = ProjectService()
        self.codegen_service = CodegenService()
        self.flow_engine = FlowEngine()
        
        # WebSocket connections for real-time updates
        self.active_connections: List[WebSocket] = []
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all API routes."""
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        # Service status
        @self.app.get("/api/status", response_model=ServiceStatusResponse)
        async def get_service_status():
            """Get status of all integrated services."""
            return ServiceStatusResponse(
                github=await self._check_github_status(),
                linear=await self._check_linear_status(),
                slack=await self._check_slack_status(),
                codegen=await self._check_codegen_status(),
                database=await self._check_database_status()
            )
        
        # Projects endpoints
        @self.app.get("/api/projects")
        async def get_projects():
            """Get all projects."""
            projects = await self.project_service.get_all_projects()
            return [project.to_dict() for project in projects]
        
        @self.app.get("/api/projects/pinned")
        async def get_pinned_projects():
            """Get pinned projects."""
            projects = await self.project_service.get_pinned_projects()
            return [project.to_dict() for project in projects]
        
        @self.app.post("/api/projects")
        async def create_project(request: ProjectCreateRequest):
            """Create a new project."""
            try:
                project = await self.project_service.create_project(
                    repo_url=request.repo_url,
                    requirements=request.requirements or ""
                )
                await self._broadcast_update("project_created", project.to_dict())
                return project.to_dict()
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/projects/{project_id}")
        async def get_project(project_id: str):
            """Get a specific project."""
            project = await self.project_service.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            return project.to_dict()
        
        @self.app.put("/api/projects/{project_id}")
        async def update_project(project_id: str, request: ProjectUpdateRequest):
            """Update a project."""
            try:
                project = await self.project_service.update_project(
                    project_id=project_id,
                    requirements=request.requirements,
                    is_pinned=request.is_pinned
                )
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found")
                await self._broadcast_update("project_updated", project.to_dict())
                return project.to_dict()
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.delete("/api/projects/{project_id}")
        async def delete_project(project_id: str):
            """Delete a project."""
            success = await self.project_service.delete_project(project_id)
            if not success:
                raise HTTPException(status_code=404, detail="Project not found")
            await self._broadcast_update("project_deleted", {"project_id": project_id})
            return {"message": "Project deleted successfully"}
        
        # GitHub repositories
        @self.app.get("/api/github/repositories")
        async def get_github_repositories():
            """Get available GitHub repositories."""
            try:
                repos = await self.project_service.get_github_repositories()
                return repos
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")
        
        # Plan generation
        @self.app.post("/api/projects/{project_id}/plan")
        async def generate_plan(project_id: str, request: PlanGenerateRequest):
            """Generate a plan for a project using Codegen SDK."""
            try:
                plan = await self.codegen_service.generate_plan(
                    project_id=project_id,
                    requirements=request.requirements
                )
                await self._broadcast_update("plan_generated", {
                    "project_id": project_id,
                    "plan": plan
                })
                return plan
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")
        
        # Flow management
        @self.app.post("/api/flows/start")
        async def start_flow(request: FlowStartRequest):
            """Start a flow for a project."""
            try:
                flow = await self.flow_engine.start_flow(
                    project_id=request.project_id,
                    requirements=request.requirements
                )
                await self._broadcast_update("flow_started", flow.to_dict())
                return flow.to_dict()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to start flow: {str(e)}")
        
        @self.app.get("/api/flows/{flow_id}")
        async def get_flow(flow_id: str):
            """Get flow details."""
            flow = await self.flow_engine.get_flow(flow_id)
            if not flow:
                raise HTTPException(status_code=404, detail="Flow not found")
            return flow.to_dict()
        
        @self.app.post("/api/flows/{flow_id}/pause")
        async def pause_flow(flow_id: str):
            """Pause a running flow."""
            try:
                flow = await self.flow_engine.pause_flow(flow_id)
                if not flow:
                    raise HTTPException(status_code=404, detail="Flow not found")
                await self._broadcast_update("flow_paused", flow.to_dict())
                return flow.to_dict()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to pause flow: {str(e)}")
        
        @self.app.post("/api/flows/{flow_id}/resume")
        async def resume_flow(flow_id: str):
            """Resume a paused flow."""
            try:
                flow = await self.flow_engine.resume_flow(flow_id)
                if not flow:
                    raise HTTPException(status_code=404, detail="Flow not found")
                await self._broadcast_update("flow_resumed", flow.to_dict())
                return flow.to_dict()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to resume flow: {str(e)}")
        
        @self.app.post("/api/flows/{flow_id}/stop")
        async def stop_flow(flow_id: str):
            """Stop a running flow."""
            try:
                flow = await self.flow_engine.stop_flow(flow_id)
                if not flow:
                    raise HTTPException(status_code=404, detail="Flow not found")
                await self._broadcast_update("flow_stopped", flow.to_dict())
                return flow.to_dict()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to stop flow: {str(e)}")
        
        # Settings
        @self.app.get("/api/settings")
        async def get_settings():
            """Get user settings (masked for security)."""
            settings = await self.project_service.get_user_settings()
            return settings.to_dict()
        
        @self.app.put("/api/settings")
        async def update_settings(settings: Dict[str, Any]):
            """Update user settings."""
            try:
                updated_settings = await self.project_service.update_user_settings(settings)
                return updated_settings.to_dict()
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await self.connect(websocket)
            try:
                while True:
                    # Keep connection alive and listen for client messages
                    data = await websocket.receive_text()
                    # Echo back for now (can be extended for client commands)
                    await websocket.send_text(f"Echo: {data}")
            except WebSocketDisconnect:
                self.disconnect(websocket)
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def _broadcast_update(self, event_type: str, data: Any):
        """Broadcast an update to all connected WebSocket clients."""
        if not self.active_connections:
            return
        
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                # Connection is broken, mark for removal
                disconnected.append(connection)
        
        # Remove broken connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def _check_github_status(self) -> ServiceStatus:
        """Check GitHub service status."""
        try:
            if self.contexten_app and hasattr(self.contexten_app, 'github'):
                # Check if GitHub integration is available and configured
                return ServiceStatus.CONNECTED
            return ServiceStatus.DISCONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_linear_status(self) -> ServiceStatus:
        """Check Linear service status."""
        try:
            if self.contexten_app and hasattr(self.contexten_app, 'linear'):
                # Check if Linear integration is available and configured
                return ServiceStatus.CONNECTED
            return ServiceStatus.DISCONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_slack_status(self) -> ServiceStatus:
        """Check Slack service status."""
        try:
            if self.contexten_app and hasattr(self.contexten_app, 'slack'):
                # Check if Slack integration is available and configured
                return ServiceStatus.CONNECTED
            return ServiceStatus.DISCONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_codegen_status(self) -> ServiceStatus:
        """Check Codegen SDK status."""
        try:
            return await self.codegen_service.check_status()
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_database_status(self) -> ServiceStatus:
        """Check database status."""
        try:
            # This would check database connectivity
            return ServiceStatus.CONNECTED
        except Exception:
            return ServiceStatus.ERROR

