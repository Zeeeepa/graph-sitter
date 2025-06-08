"""
Dashboard Extension Main Class

Central orchestration class that integrates all Contexten extensions into a unified dashboard system.
"""

import logging
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from contexten.extensions.contexten_app.contexten_app import ContextenApp

from contexten.extensions.modal.interface import EventHandlerManagerProtocol
from graph_sitter.shared.logging.get_logger import get_logger

from .models import (
    DashboardProject, DashboardPlan, DashboardTask, WorkflowEvent, 
    QualityGateResult, DashboardSettings, DashboardStats
)
from .project_manager import ProjectManager
from .planning_engine import PlanningEngine
from .workflow_engine import WorkflowEngine
from .quality_manager import QualityManager
from .event_coordinator import EventCoordinator
from .settings_manager import SettingsManager

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


class DashboardEventHandler(EventHandlerManagerProtocol):
    """Event handler for dashboard-specific events"""
    
    def __init__(self, dashboard: 'Dashboard'):
        self.dashboard = dashboard
        self.registered_handlers = {}
    
    def register_handler(self, event_type: str, handler):
        """Register an event handler"""
        if event_type not in self.registered_handlers:
            self.registered_handlers[event_type] = []
        self.registered_handlers[event_type].append(handler)
    
    async def handle_event(self, event_type: str, data: Dict[str, Any]):
        """Handle incoming events"""
        logger.info(f"Dashboard handling event: {event_type}")
        
        # Route to event coordinator
        await self.dashboard.event_coordinator.handle_event(event_type, data)
        
        # Execute registered handlers
        if event_type in self.registered_handlers:
            for handler in self.registered_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")


class Dashboard:
    """
    Main Dashboard class that orchestrates all Contexten extensions.
    
    Provides:
    - Project discovery and management
    - Automated planning via Codegen SDK
    - Workflow execution and monitoring
    - Quality gates and PR validation
    - Real-time event coordination
    - Settings and configuration management
    """
    
    def __init__(self, contexten_app):
        self.app = contexten_app
        self.event_handler = DashboardEventHandler(self)
        
        # Initialize managers
        self.project_manager = ProjectManager(self)
        self.planning_engine = PlanningEngine(self)
        self.workflow_engine = WorkflowEngine(self)
        self.quality_manager = QualityManager(self)
        self.event_coordinator = EventCoordinator(self)
        self.settings_manager = SettingsManager(self)
        
        # WebSocket connections
        self.websocket_connections: List[WebSocket] = []
        
        # Register API routes
        self._register_routes()
        
        logger.info("Dashboard initialized successfully")
    
    def _register_routes(self):
        """Register FastAPI routes for the dashboard"""
        
        # Project management routes
        @self.app.app.get("/dashboard/projects")
        async def get_projects():
            """Get all pinned projects"""
            try:
                projects = await self.project_manager.get_all_projects()
                return {"projects": [project.dict() for project in projects]}
            except Exception as e:
                logger.error(f"Error getting projects: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.get("/dashboard/projects/discover")
        async def discover_repositories(organization: Optional[str] = None):
            """Discover GitHub repositories"""
            try:
                repositories = await self.project_manager.discover_github_repositories(organization)
                return {"repositories": repositories}
            except Exception as e:
                logger.error(f"Error discovering repositories: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.post("/dashboard/projects/pin")
        async def pin_project(request: Request):
            """Pin a project to the dashboard"""
            try:
                data = await request.json()
                repository_identifier = data.get("repository")
                if not repository_identifier:
                    raise HTTPException(status_code=400, detail="Repository identifier is required")
                
                # Extract additional configuration
                config = {k: v for k, v in data.items() if k != "repository"}
                
                project = await self.project_manager.pin_project(repository_identifier, **config)
                return {"project": project.dict()}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error pinning project: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.delete("/dashboard/projects/{project_id}")
        async def unpin_project(project_id: str):
            """Unpin a project from the dashboard"""
            try:
                success = await self.project_manager.unpin_project(project_id)
                if not success:
                    raise HTTPException(status_code=404, detail="Project not found")
                return {"message": "Project unpinned successfully"}
            except Exception as e:
                logger.error(f"Error unpinning project: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.get("/dashboard/projects/{project_id}")
        async def get_project(project_id: str):
            """Get a specific project"""
            try:
                project = await self.project_manager.get_project(project_id)
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found")
                return {"project": project.dict()}
            except Exception as e:
                logger.error(f"Error getting project: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.put("/dashboard/projects/{project_id}")
        async def update_project(project_id: str, request: Request):
            """Update a project's configuration"""
            try:
                data = await request.json()
                project = await self.project_manager.update_project(project_id, **data)
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found")
                return {"project": project.dict()}
            except Exception as e:
                logger.error(f"Error updating project: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.post("/dashboard/projects/{project_id}/flow/start")
        async def start_project_flow(project_id: str):
            """Start the automated workflow for a project"""
            try:
                success = await self.project_manager.start_project_flow(project_id)
                if not success:
                    raise HTTPException(status_code=404, detail="Project not found")
                return {"message": "Workflow started successfully"}
            except Exception as e:
                logger.error(f"Error starting workflow: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.post("/dashboard/projects/{project_id}/flow/stop")
        async def stop_project_flow(project_id: str):
            """Stop the automated workflow for a project"""
            try:
                success = await self.project_manager.stop_project_flow(project_id)
                if not success:
                    raise HTTPException(status_code=404, detail="Project not found")
                return {"message": "Workflow stopped successfully"}
            except Exception as e:
                logger.error(f"Error stopping workflow: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.get("/dashboard/projects/{project_id}/metrics")
        async def get_project_metrics(project_id: str):
            """Get metrics for a specific project"""
            try:
                metrics = await self.project_manager.get_project_metrics(project_id)
                return {"metrics": metrics}
            except Exception as e:
                logger.error(f"Error getting project metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.post("/dashboard/projects/{project_id}/sync")
        async def sync_project_with_github(project_id: str):
            """Synchronize project with GitHub"""
            try:
                success = await self.project_manager.sync_project_with_github(project_id)
                if not success:
                    raise HTTPException(status_code=404, detail="Project not found or sync failed")
                return {"message": "Project synchronized successfully"}
            except Exception as e:
                logger.error(f"Error synchronizing project: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Plans endpoints
        @self.app.app.post("/api/dashboard/projects/{project_id}/plan")
        async def generate_plan(project_id: str, request: Dict[str, str]):
            """Generate plan for project using Codegen SDK"""
            try:
                requirements = request.get("requirements")
                if not requirements:
                    raise HTTPException(status_code=400, detail="requirements required")
                
                plan = await self.planning_engine.generate_plan(project_id, requirements)
                return {"success": True, "data": plan}
            except Exception as e:
                logger.error(f"Error generating plan for {project_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.get("/api/dashboard/plans/{plan_id}")
        async def get_plan(plan_id: str):
            """Get specific plan"""
            try:
                plan = await self.planning_engine.get_plan(plan_id)
                if not plan:
                    raise HTTPException(status_code=404, detail="Plan not found")
                return {"success": True, "data": plan}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting plan {plan_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Workflow endpoints
        @self.app.app.post("/api/dashboard/projects/{project_id}/workflow/start")
        async def start_workflow(project_id: str):
            """Start workflow for project"""
            try:
                await self.workflow_engine.start_workflow(project_id)
                return {"success": True}
            except Exception as e:
                logger.error(f"Error starting workflow for {project_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.post("/api/dashboard/projects/{project_id}/workflow/stop")
        async def stop_workflow(project_id: str):
            """Stop workflow for project"""
            try:
                await self.workflow_engine.stop_workflow(project_id)
                return {"success": True}
            except Exception as e:
                logger.error(f"Error stopping workflow for {project_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Stats endpoint
        @self.app.app.get("/api/dashboard/stats")
        async def get_stats():
            """Get dashboard statistics"""
            try:
                stats = await self._calculate_stats()
                return {"success": True, "data": stats}
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Settings endpoints
        @self.app.app.get("/api/dashboard/settings")
        async def get_settings():
            """Get dashboard settings"""
            try:
                settings = await self.settings_manager.get_settings()
                return {"success": True, "data": settings}
            except Exception as e:
                logger.error(f"Error getting settings: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.app.post("/api/dashboard/settings")
        async def update_settings(settings: DashboardSettings):
            """Update dashboard settings"""
            try:
                updated_settings = await self.settings_manager.update_settings(settings)
                return {"success": True, "data": updated_settings}
            except Exception as e:
                logger.error(f"Error updating settings: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # WebSocket endpoint
        @self.app.app.websocket("/api/dashboard/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
    async def _calculate_stats(self) -> DashboardStats:
        """Calculate dashboard statistics"""
        projects = await self.project_manager.get_all_projects()
        
        stats = DashboardStats()
        stats.total_projects = len(projects)
        stats.active_projects = len([p for p in projects if p.status.value == "active"])
        stats.completed_projects = len([p for p in projects if p.status.value == "completed"])
        
        # Calculate other stats
        total_progress = sum(p.progress for p in projects)
        stats.average_project_progress = total_progress / len(projects) if projects else 0
        
        stats.running_flows = len([p for p in projects if p.flow_status.value == "running"])
        
        return stats
    
    async def broadcast_event(self, event: WorkflowEvent):
        """Broadcast event to all WebSocket connections"""
        if not self.websocket_connections:
            return
        
        event_data = {
            "type": "workflow_event",
            "payload": event.dict(),
            "timestamp": event.timestamp.isoformat()
        }
        
        # Send to all connected clients
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(event_data)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)
    
    async def start(self):
        """Start the dashboard system"""
        logger.info("Starting dashboard system...")
        
        # Initialize all managers
        await self.project_manager.initialize()
        await self.planning_engine.initialize()
        await self.workflow_engine.initialize()
        await self.quality_manager.initialize()
        await self.event_coordinator.initialize()
        await self.settings_manager.initialize()
        
        logger.info("Dashboard system started successfully")
    
    async def stop(self):
        """Stop the dashboard system"""
        logger.info("Stopping dashboard system...")
        
        # Stop all managers
        await self.workflow_engine.stop()
        await self.event_coordinator.stop()
        
        # Close WebSocket connections
        for websocket in self.websocket_connections:
            try:
                await websocket.close()
            except Exception:
                pass
        
        logger.info("Dashboard system stopped")
