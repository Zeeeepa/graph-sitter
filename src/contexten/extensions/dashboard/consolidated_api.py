"""
Consolidated API endpoints for the dashboard extension.
Combines the best elements from all three PRs into a unified FastAPI system.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .consolidated_models import (
    Project, Flow, Task, UserSettings, QualityGate,
    FlowStatus, TaskStatus, ServiceStatus, ProjectStatus, QualityGateStatus,
    ServiceStatusResponse, ProjectCreateRequest, ProjectUpdateRequest,
    FlowStartRequest, PlanGenerateRequest, CodegenTaskRequest,
    SystemHealthResponse, DashboardResponse, WebSocketEvent,
    ProjectUpdateEvent, FlowUpdateEvent, TaskUpdateEvent, QualityGateEvent, SystemHealthEvent
)

# Import service layers (will be created next)
from .services.strands_orchestrator import StrandsOrchestrator
from .services.project_service import ProjectService
from .services.codegen_service import CodegenService
from .services.quality_service import QualityService
from .services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)


class ConsolidatedDashboardAPI:
    """
    Consolidated Dashboard API class combining all PR features.
    Provides REST endpoints and WebSocket connections for the complete dashboard system.
    """
    
    def __init__(self, contexten_app=None):
        """Initialize the Consolidated Dashboard API."""
        self.app = FastAPI(
            title="Strands Agent Dashboard API",
            version="1.0.0",
            description="Comprehensive dashboard for Strands tools ecosystem integration"
        )
        self.contexten_app = contexten_app
        
        # Initialize service layers
        self.strands_orchestrator = StrandsOrchestrator()
        self.project_service = ProjectService()
        self.codegen_service = CodegenService()
        self.quality_service = QualityService()
        self.monitoring_service = MonitoringService()
        
        # WebSocket connections for real-time updates
        self.active_connections: List[WebSocket] = []
        self.connection_subscriptions: Dict[WebSocket, List[str]] = {}
        
        # Background tasks
        self.background_tasks = set()
        
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
        
        # Start background monitoring
        self._start_background_tasks()
    
    def _setup_routes(self):
        """Setup all API routes."""
        
        # Health and monitoring endpoints
        @self.app.get("/health")
        async def health_check():
            """Basic health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/health", response_model=SystemHealthResponse)
        async def get_system_health():
            """Get comprehensive system health status."""
            return await self.monitoring_service.get_system_health()
        
        @self.app.get("/api/status", response_model=ServiceStatusResponse)
        async def get_service_status():
            """Get status of all integrated services."""
            return ServiceStatusResponse(
                github=await self._check_github_status(),
                linear=await self._check_linear_status(),
                slack=await self._check_slack_status(),
                codegen=await self._check_codegen_status(),
                database=await self._check_database_status(),
                strands_workflow=await self.strands_orchestrator.check_workflow_status(),
                strands_mcp=await self.strands_orchestrator.check_mcp_status(),
                controlflow=await self.strands_orchestrator.check_controlflow_status(),
                prefect=await self.strands_orchestrator.check_prefect_status()
            )
        
        # Project management endpoints
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
        async def create_project(request: ProjectCreateRequest, background_tasks: BackgroundTasks):
            """Create a new project."""
            try:
                project = await self.project_service.create_project(
                    repo_url=request.repo_url,
                    requirements=request.requirements or "",
                    auto_pin=request.auto_pin
                )
                
                # Broadcast update
                await self._broadcast_event(ProjectUpdateEvent(
                    data={"action": "created", "project": project.to_dict()}
                ))
                
                # Start background analysis
                background_tasks.add_task(
                    self._analyze_project_background, project.id
                )
                
                return DashboardResponse(
                    success=True,
                    message="Project created successfully",
                    data={"project": project.to_dict()}
                )
            except Exception as e:
                logger.error(f"Failed to create project: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/projects/{project_id}")
        async def get_project(project_id: str):
            """Get a specific project."""
            project = await self.project_service.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            return DashboardResponse(
                success=True,
                message="Project retrieved successfully",
                data={"project": project.to_dict()}
            )
        
        @self.app.put("/api/projects/{project_id}")
        async def update_project(project_id: str, request: ProjectUpdateRequest):
            """Update a project."""
            try:
                project = await self.project_service.update_project(
                    project_id=project_id,
                    requirements=request.requirements,
                    is_pinned=request.is_pinned,
                    flow_status=request.flow_status
                )
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found")
                
                await self._broadcast_event(ProjectUpdateEvent(
                    data={"action": "updated", "project": project.to_dict()},
                    project_id=project_id
                ))
                
                return DashboardResponse(
                    success=True,
                    message="Project updated successfully",
                    data={"project": project.to_dict()}
                )
            except Exception as e:
                logger.error(f"Failed to update project: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.delete("/api/projects/{project_id}")
        async def delete_project(project_id: str):
            """Delete a project."""
            success = await self.project_service.delete_project(project_id)
            if not success:
                raise HTTPException(status_code=404, detail="Project not found")
            
            await self._broadcast_event(ProjectUpdateEvent(
                data={"action": "deleted", "project_id": project_id},
                project_id=project_id
            ))
            
            return DashboardResponse(
                success=True,
                message="Project deleted successfully"
            )
        
        # GitHub integration endpoints
        @self.app.get("/api/github/repositories")
        async def get_github_repositories():
            """Get available GitHub repositories."""
            try:
                repos = await self.project_service.get_github_repositories()
                return DashboardResponse(
                    success=True,
                    message=f"Retrieved {len(repos)} repositories",
                    data={"repositories": repos}
                )
            except Exception as e:
                logger.error(f"Failed to fetch repositories: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")
        
        # Workflow and orchestration endpoints
        @self.app.post("/api/workflows/start")
        async def start_workflow(request: FlowStartRequest, background_tasks: BackgroundTasks):
            """Start a multi-layer workflow orchestration."""
            try:
                flow = await self.strands_orchestrator.start_workflow(
                    project_id=request.project_id,
                    requirements=request.requirements,
                    flow_name=request.flow_name,
                    auto_execute=request.auto_execute
                )
                
                await self._broadcast_event(FlowUpdateEvent(
                    data={"action": "started", "flow": flow.to_dict()},
                    project_id=request.project_id,
                    flow_id=flow.id
                ))
                
                # Start background execution monitoring
                background_tasks.add_task(
                    self._monitor_workflow_execution, flow.id
                )
                
                return DashboardResponse(
                    success=True,
                    message="Workflow started successfully",
                    data={"flow": flow.to_dict()}
                )
            except Exception as e:
                logger.error(f"Failed to start workflow: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")
        
        @self.app.get("/api/workflows/{flow_id}")
        async def get_workflow(flow_id: str):
            """Get workflow details."""
            flow = await self.strands_orchestrator.get_workflow(flow_id)
            if not flow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            return DashboardResponse(
                success=True,
                message="Workflow retrieved successfully",
                data={"flow": flow.to_dict()}
            )
        
        @self.app.post("/api/workflows/{flow_id}/pause")
        async def pause_workflow(flow_id: str):
            """Pause a running workflow."""
            try:
                flow = await self.strands_orchestrator.pause_workflow(flow_id)
                if not flow:
                    raise HTTPException(status_code=404, detail="Workflow not found")
                
                await self._broadcast_event(FlowUpdateEvent(
                    data={"action": "paused", "flow": flow.to_dict()},
                    flow_id=flow_id
                ))
                
                return DashboardResponse(
                    success=True,
                    message="Workflow paused successfully",
                    data={"flow": flow.to_dict()}
                )
            except Exception as e:
                logger.error(f"Failed to pause workflow: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to pause workflow: {str(e)}")
        
        @self.app.post("/api/workflows/{flow_id}/resume")
        async def resume_workflow(flow_id: str):
            """Resume a paused workflow."""
            try:
                flow = await self.strands_orchestrator.resume_workflow(flow_id)
                if not flow:
                    raise HTTPException(status_code=404, detail="Workflow not found")
                
                await self._broadcast_event(FlowUpdateEvent(
                    data={"action": "resumed", "flow": flow.to_dict()},
                    flow_id=flow_id
                ))
                
                return DashboardResponse(
                    success=True,
                    message="Workflow resumed successfully",
                    data={"flow": flow.to_dict()}
                )
            except Exception as e:
                logger.error(f"Failed to resume workflow: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")
        
        @self.app.post("/api/workflows/{flow_id}/stop")
        async def stop_workflow(flow_id: str):
            """Stop a running workflow."""
            try:
                flow = await self.strands_orchestrator.stop_workflow(flow_id)
                if not flow:
                    raise HTTPException(status_code=404, detail="Workflow not found")
                
                await self._broadcast_event(FlowUpdateEvent(
                    data={"action": "stopped", "flow": flow.to_dict()},
                    flow_id=flow_id
                ))
                
                return DashboardResponse(
                    success=True,
                    message="Workflow stopped successfully",
                    data={"flow": flow.to_dict()}
                )
            except Exception as e:
                logger.error(f"Failed to stop workflow: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to stop workflow: {str(e)}")
        
        # Codegen SDK endpoints
        @self.app.post("/api/codegen/plans")
        async def generate_plan(request: PlanGenerateRequest):
            """Generate a plan using Codegen SDK."""
            try:
                plan = await self.codegen_service.generate_plan(
                    project_id=request.project_id,
                    requirements=request.requirements,
                    include_quality_gates=request.include_quality_gates
                )
                
                await self._broadcast_event(WebSocketEvent(
                    type="plan_generated",
                    data={"project_id": request.project_id, "plan": plan},
                    project_id=request.project_id
                ))
                
                return DashboardResponse(
                    success=True,
                    message="Plan generated successfully",
                    data={"plan": plan}
                )
            except Exception as e:
                logger.error(f"Failed to generate plan: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")
        
        @self.app.post("/api/codegen/tasks")
        async def create_codegen_task(request: CodegenTaskRequest, background_tasks: BackgroundTasks):
            """Create a Codegen SDK task."""
            try:
                task = await self.codegen_service.create_task(
                    task_type=request.task_type,
                    project_id=request.project_id,
                    prompt=request.prompt,
                    context=request.context or {}
                )
                
                # Start background task execution
                background_tasks.add_task(
                    self._execute_codegen_task, task.id
                )
                
                return DashboardResponse(
                    success=True,
                    message="Codegen task created successfully",
                    data={"task": task.to_dict()}
                )
            except Exception as e:
                logger.error(f"Failed to create codegen task: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to create codegen task: {str(e)}")
        
        @self.app.get("/api/codegen/tasks")
        async def get_codegen_tasks():
            """Get all Codegen tasks."""
            tasks = await self.codegen_service.get_all_tasks()
            return DashboardResponse(
                success=True,
                message=f"Retrieved {len(tasks)} tasks",
                data={"tasks": [task.to_dict() for task in tasks]}
            )
        
        @self.app.get("/api/codegen/tasks/{task_id}")
        async def get_codegen_task(task_id: str):
            """Get a specific Codegen task."""
            task = await self.codegen_service.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            return DashboardResponse(
                success=True,
                message="Task retrieved successfully",
                data={"task": task.to_dict()}
            )
        
        # Quality gates endpoints
        @self.app.get("/api/quality-gates/{project_id}")
        async def get_quality_gates(project_id: str):
            """Get quality gates for a project."""
            gates = await self.quality_service.get_quality_gates(project_id)
            return DashboardResponse(
                success=True,
                message=f"Retrieved {len(gates)} quality gates",
                data={"quality_gates": [gate.to_dict() for gate in gates]}
            )
        
        @self.app.post("/api/quality-gates/{project_id}/validate")
        async def validate_quality_gates(project_id: str, background_tasks: BackgroundTasks):
            """Validate quality gates for a project."""
            try:
                # Start background validation
                background_tasks.add_task(
                    self._validate_quality_gates_background, project_id
                )
                
                return DashboardResponse(
                    success=True,
                    message="Quality gate validation started"
                )
            except Exception as e:
                logger.error(f"Failed to start quality gate validation: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to start validation: {str(e)}")
        
        # Settings endpoints
        @self.app.get("/api/settings")
        async def get_settings():
            """Get user settings (masked for security)."""
            settings = await self.project_service.get_user_settings()
            return DashboardResponse(
                success=True,
                message="Settings retrieved successfully",
                data={"settings": settings.to_dict()}
            )
        
        @self.app.put("/api/settings")
        async def update_settings(settings: Dict[str, Any]):
            """Update user settings."""
            try:
                updated_settings = await self.project_service.update_user_settings(settings)
                return DashboardResponse(
                    success=True,
                    message="Settings updated successfully",
                    data={"settings": updated_settings.to_dict()}
                )
            except Exception as e:
                logger.error(f"Failed to update settings: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await self.connect(websocket)
            try:
                while True:
                    # Listen for client messages (subscription management)
                    data = await websocket.receive_text()
                    try:
                        message = json.loads(data)
                        await self._handle_websocket_message(websocket, message)
                    except json.JSONDecodeError:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }))
            except WebSocketDisconnect:
                self.disconnect(websocket)
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_subscriptions[websocket] = []
        
        # Send initial system status
        status = await self.monitoring_service.get_system_health()
        await websocket.send_text(json.dumps({
            "type": "system_status",
            "data": status.dict(),
            "timestamp": datetime.now().isoformat()
        }))
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_subscriptions:
            del self.connection_subscriptions[websocket]
    
    async def _handle_websocket_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        message_type = message.get("type")
        
        if message_type == "subscribe":
            # Subscribe to specific topics
            topics = message.get("topics", [])
            self.connection_subscriptions[websocket] = topics
            await websocket.send_text(json.dumps({
                "type": "subscription_confirmed",
                "topics": topics
            }))
        
        elif message_type == "unsubscribe":
            # Unsubscribe from topics
            topics = message.get("topics", [])
            current_subs = self.connection_subscriptions.get(websocket, [])
            self.connection_subscriptions[websocket] = [
                topic for topic in current_subs if topic not in topics
            ]
            await websocket.send_text(json.dumps({
                "type": "unsubscription_confirmed",
                "topics": topics
            }))
        
        elif message_type == "ping":
            # Respond to ping
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }))
    
    async def _broadcast_event(self, event: WebSocketEvent):
        """Broadcast an event to all connected WebSocket clients."""
        if not self.active_connections:
            return
        
        message = event.dict()
        
        # Send to all connected clients (with subscription filtering)
        disconnected = []
        for connection in self.active_connections:
            try:
                # Check if client is subscribed to this event type
                subscriptions = self.connection_subscriptions.get(connection, [])
                if not subscriptions or event.type in subscriptions or "all" in subscriptions:
                    await connection.send_text(json.dumps(message))
            except Exception:
                # Connection is broken, mark for removal
                disconnected.append(connection)
        
        # Remove broken connections
        for connection in disconnected:
            self.disconnect(connection)
    
    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        # Start system health monitoring
        task = asyncio.create_task(self._system_health_monitor())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def _system_health_monitor(self):
        """Background task for system health monitoring."""
        while True:
            try:
                health = await self.monitoring_service.get_system_health()
                await self._broadcast_event(SystemHealthEvent(
                    data=health.dict()
                ))
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"System health monitor error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _analyze_project_background(self, project_id: str):
        """Background task for project analysis."""
        try:
            await self.project_service.analyze_project(project_id)
        except Exception as e:
            logger.error(f"Project analysis failed for {project_id}: {e}")
    
    async def _monitor_workflow_execution(self, flow_id: str):
        """Background task for workflow execution monitoring."""
        try:
            await self.strands_orchestrator.monitor_workflow_execution(flow_id)
        except Exception as e:
            logger.error(f"Workflow monitoring failed for {flow_id}: {e}")
    
    async def _execute_codegen_task(self, task_id: str):
        """Background task for Codegen task execution."""
        try:
            await self.codegen_service.execute_task(task_id)
        except Exception as e:
            logger.error(f"Codegen task execution failed for {task_id}: {e}")
    
    async def _validate_quality_gates_background(self, project_id: str):
        """Background task for quality gate validation."""
        try:
            results = await self.quality_service.validate_all_gates(project_id)
            await self._broadcast_event(QualityGateEvent(
                data={"project_id": project_id, "results": results},
                project_id=project_id
            ))
        except Exception as e:
            logger.error(f"Quality gate validation failed for {project_id}: {e}")
    
    # Service status check methods
    async def _check_github_status(self) -> ServiceStatus:
        """Check GitHub service status."""
        try:
            if self.contexten_app and hasattr(self.contexten_app, 'github'):
                return ServiceStatus.CONNECTED
            return ServiceStatus.DISCONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_linear_status(self) -> ServiceStatus:
        """Check Linear service status."""
        try:
            if self.contexten_app and hasattr(self.contexten_app, 'linear'):
                return ServiceStatus.CONNECTED
            return ServiceStatus.DISCONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_slack_status(self) -> ServiceStatus:
        """Check Slack service status."""
        try:
            if self.contexten_app and hasattr(self.contexten_app, 'slack'):
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


def create_dashboard_app(contexten_app=None) -> FastAPI:
    """Factory function to create the dashboard FastAPI app."""
    dashboard_api = ConsolidatedDashboardAPI(contexten_app)
    return dashboard_api.app

