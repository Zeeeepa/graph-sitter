"""Comprehensive Dashboard Extension for Contexten.

This extension provides a complete dashboard system that integrates:
- Project management
- Flow orchestration
- Real-time monitoring
- Settings management
- Multi-service integration
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from ...core.extension import ServiceExtension, ExtensionMetadata
from ...core.events.bus import Event

logger = logging.getLogger(__name__)

class DashboardExtension(ServiceExtension):
    """Comprehensive dashboard extension."""

    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app, config)
        self.fastapi_app: Optional[FastAPI] = None
        self.server = None
        self._pinned_projects: Dict[str, Dict[str, Any]] = {}
        self._project_flows: Dict[str, Dict[str, Any]] = {}
        self._websocket_connections: List[WebSocket] = []
        self._settings: Dict[str, Any] = {}

    @property
    def metadata(self) -> ExtensionMetadata:
        return ExtensionMetadata(
            name="dashboard",
            version="1.0.0",
            description="Comprehensive dashboard for project management and monitoring",
            author="Contexten",
            dependencies=["github", "linear", "codegen", "flow_orchestrator"],
            required=False,
            config_schema={
                "type": "object",
                "properties": {
                    "host": {"type": "string", "default": "0.0.0.0"},
                    "port": {"type": "integer", "default": 8000},
                    "frontend_path": {"type": "string", "description": "Path to frontend build"},
                },
            },
            tags={"ui", "dashboard", "management"}
        )

    async def initialize(self) -> None:
        """Initialize dashboard extension."""
        # Create FastAPI app
        self.fastapi_app = FastAPI(
            title="Contexten Dashboard",
            description="Comprehensive project management dashboard",
            version="1.0.0"
        )

        # Add CORS middleware
        self.fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self._setup_routes()
        self._setup_websocket()
        self._setup_static_files()

        # Register event handlers
        self.register_event_handler("project.pin", self._handle_project_pin)
        self.register_event_handler("project.unpin", self._handle_project_unpin)
        self.register_event_handler("flow.*", self._handle_flow_events)
        self.register_event_handler("github.*", self._handle_github_events)
        self.register_event_handler("linear.*", self._handle_linear_events)

        logger.info("Dashboard extension initialized")

    async def start(self) -> None:
        """Start dashboard server."""
        host = self.config.get("host", "0.0.0.0")
        port = self.config.get("port", 8000)

        # Start FastAPI server
        config = uvicorn.Config(
            self.fastapi_app,
            host=host,
            port=port,
            log_level="info"
        )
        self.server = uvicorn.Server(config)
        
        # Start server in background
        asyncio.create_task(self.server.serve())
        
        logger.info(f"Dashboard server started on http://{host}:{port}")

    async def stop(self) -> None:
        """Stop dashboard server."""
        if self.server:
            self.server.should_exit = True
            
        # Close WebSocket connections
        for ws in self._websocket_connections:
            try:
                await ws.close()
            except Exception:
                pass
        
        logger.info("Dashboard extension stopped")

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""
        
        # Health check
        @self.fastapi_app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat()
            }

        # Get available projects from GitHub
        @self.fastapi_app.get("/api/projects/available")
        async def get_available_projects():
            try:
                github_ext = self.app.extension_registry.get_extension("github")
                if not github_ext:
                    raise HTTPException(status_code=503, detail="GitHub extension not available")
                
                repositories = await github_ext.get_repositories()
                return {"success": True, "data": repositories}
            except Exception as e:
                logger.error(f"Failed to get available projects: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Get pinned projects
        @self.fastapi_app.get("/api/projects/pinned")
        async def get_pinned_projects():
            return {"success": True, "data": list(self._pinned_projects.values())}

        # Pin a project
        @self.fastapi_app.post("/api/projects/pin")
        async def pin_project(request: Dict[str, Any]):
            try:
                project_id = request.get("project_id")
                repository = request.get("repository")
                
                if not project_id or not repository:
                    raise HTTPException(status_code=400, detail="project_id and repository required")

                # Get project details from GitHub
                github_ext = self.app.extension_registry.get_extension("github")
                project_data = await github_ext.get_repository(repository)
                
                # Store pinned project
                self._pinned_projects[project_id] = {
                    "id": project_id,
                    "repository": repository,
                    "pinned_at": datetime.utcnow().isoformat(),
                    "flow_enabled": False,
                    "flow_status": "stopped",
                    **project_data
                }

                # Publish event
                await self.app.event_bus.publish(Event(
                    type="project.pinned",
                    source="dashboard",
                    data={"project_id": project_id, "repository": repository}
                ))

                return {"success": True, "data": self._pinned_projects[project_id]}
            except Exception as e:
                logger.error(f"Failed to pin project: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Unpin a project
        @self.fastapi_app.post("/api/projects/unpin")
        async def unpin_project(request: Dict[str, Any]):
            try:
                project_id = request.get("project_id")
                
                if not project_id:
                    raise HTTPException(status_code=400, detail="project_id required")

                if project_id not in self._pinned_projects:
                    raise HTTPException(status_code=404, detail="Project not found")

                # Stop flow if running
                if project_id in self._project_flows:
                    flow_orchestrator = self.app.extension_registry.get_extension("flow_orchestrator")
                    if flow_orchestrator:
                        flow = self._project_flows[project_id]
                        if flow.get("execution_id"):
                            await flow_orchestrator.stop_flow(flow["execution_id"])

                # Remove project
                project = self._pinned_projects.pop(project_id)
                self._project_flows.pop(project_id, None)

                # Publish event
                await self.app.event_bus.publish(Event(
                    type="project.unpinned",
                    source="dashboard",
                    data={"project_id": project_id}
                ))

                return {"success": True, "data": project}
            except Exception as e:
                logger.error(f"Failed to unpin project: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Add requirements to project
        @self.fastapi_app.post("/api/projects/{project_id}/requirements")
        async def add_requirements(project_id: str, request: Dict[str, Any]):
            try:
                requirements = request.get("requirements")
                
                if not requirements:
                    raise HTTPException(status_code=400, detail="requirements required")

                if project_id not in self._pinned_projects:
                    raise HTTPException(status_code=404, detail="Project not found")

                # Update project with requirements
                self._pinned_projects[project_id]["requirements"] = requirements
                self._pinned_projects[project_id]["updated_at"] = datetime.utcnow().isoformat()

                return {"success": True, "data": self._pinned_projects[project_id]}
            except Exception as e:
                logger.error(f"Failed to add requirements: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Generate plan for project
        @self.fastapi_app.post("/api/projects/{project_id}/plan")
        async def generate_plan(project_id: str):
            try:
                if project_id not in self._pinned_projects:
                    raise HTTPException(status_code=404, detail="Project not found")

                project = self._pinned_projects[project_id]
                requirements = project.get("requirements")
                
                if not requirements:
                    raise HTTPException(status_code=400, detail="Requirements not set")

                # Generate plan using Codegen
                codegen_ext = self.app.extension_registry.get_extension("codegen")
                if not codegen_ext:
                    raise HTTPException(status_code=503, detail="Codegen extension not available")

                plan_result = await codegen_ext.generate_plan(
                    project_name=project["name"],
                    repository=project["repository"],
                    requirements=requirements
                )

                # Update project with plan
                self._pinned_projects[project_id]["plan"] = plan_result
                self._pinned_projects[project_id]["plan_generated_at"] = datetime.utcnow().isoformat()

                return {"success": True, "data": plan_result}
            except Exception as e:
                logger.error(f"Failed to generate plan: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Start project flow
        @self.fastapi_app.post("/api/projects/{project_id}/flow/start")
        async def start_project_flow(project_id: str):
            try:
                if project_id not in self._pinned_projects:
                    raise HTTPException(status_code=404, detail="Project not found")

                project = self._pinned_projects[project_id]
                requirements = project.get("requirements")
                
                if not requirements:
                    raise HTTPException(status_code=400, detail="Requirements not set")

                # Create and start flow
                flow_orchestrator = self.app.extension_registry.get_extension("flow_orchestrator")
                if not flow_orchestrator:
                    raise HTTPException(status_code=503, detail="Flow orchestrator not available")

                # Create flow
                flow_result = await flow_orchestrator.create_project_flow(
                    project_id=project_id,
                    project_name=project["name"],
                    repository=project["repository"],
                    requirements=requirements
                )

                # Start flow
                execution_result = await flow_orchestrator.start_flow(flow_result["flow_id"])

                # Update project and flow tracking
                self._pinned_projects[project_id]["flow_enabled"] = True
                self._pinned_projects[project_id]["flow_status"] = "running"
                self._project_flows[project_id] = {
                    "flow_id": flow_result["flow_id"],
                    "execution_id": execution_result["execution_id"],
                    "started_at": execution_result["started_at"]
                }

                return {"success": True, "data": execution_result}
            except Exception as e:
                logger.error(f"Failed to start project flow: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Stop project flow
        @self.fastapi_app.post("/api/projects/{project_id}/flow/stop")
        async def stop_project_flow(project_id: str):
            try:
                if project_id not in self._pinned_projects:
                    raise HTTPException(status_code=404, detail="Project not found")

                if project_id not in self._project_flows:
                    raise HTTPException(status_code=400, detail="No active flow")

                flow = self._project_flows[project_id]
                
                # Stop flow
                flow_orchestrator = self.app.extension_registry.get_extension("flow_orchestrator")
                if flow_orchestrator and flow.get("execution_id"):
                    stop_result = await flow_orchestrator.stop_flow(flow["execution_id"])

                # Update project status
                self._pinned_projects[project_id]["flow_enabled"] = False
                self._pinned_projects[project_id]["flow_status"] = "stopped"
                del self._project_flows[project_id]

                return {"success": True, "data": stop_result}
            except Exception as e:
                logger.error(f"Failed to stop project flow: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Get project flow status
        @self.fastapi_app.get("/api/projects/{project_id}/flow/status")
        async def get_project_flow_status(project_id: str):
            try:
                if project_id not in self._pinned_projects:
                    raise HTTPException(status_code=404, detail="Project not found")

                if project_id not in self._project_flows:
                    return {"success": True, "data": {"status": "no_flow"}}

                flow = self._project_flows[project_id]
                
                # Get flow status
                flow_orchestrator = self.app.extension_registry.get_extension("flow_orchestrator")
                if flow_orchestrator and flow.get("execution_id"):
                    status = await flow_orchestrator.get_execution_status(flow["execution_id"])
                    return {"success": True, "data": status}

                return {"success": True, "data": flow}
            except Exception as e:
                logger.error(f"Failed to get flow status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Settings management
        @self.fastapi_app.get("/api/settings")
        async def get_settings():
            return {"success": True, "data": self._settings}

        @self.fastapi_app.post("/api/settings")
        async def update_settings(request: Dict[str, Any]):
            try:
                self._settings.update(request)
                
                # Publish event
                await self.app.event_bus.publish(Event(
                    type="settings.updated",
                    source="dashboard",
                    data={"settings": self._settings}
                ))

                return {"success": True, "data": self._settings}
            except Exception as e:
                logger.error(f"Failed to update settings: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Dashboard stats
        @self.fastapi_app.get("/api/stats")
        async def get_dashboard_stats():
            try:
                stats = {
                    "pinned_projects": len(self._pinned_projects),
                    "active_flows": len(self._project_flows),
                    "total_connections": len(self._websocket_connections),
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Get extension stats
                for ext_name in ["github", "linear", "codegen", "flow_orchestrator"]:
                    ext = self.app.extension_registry.get_extension(ext_name)
                    if ext:
                        try:
                            ext_health = await ext.health_check()
                            stats[f"{ext_name}_status"] = ext_health.get("status", "unknown")
                        except Exception:
                            stats[f"{ext_name}_status"] = "error"

                return {"success": True, "data": stats}
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def _setup_websocket(self) -> None:
        """Setup WebSocket endpoint."""
        
        @self.fastapi_app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self._websocket_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if websocket in self._websocket_connections:
                    self._websocket_connections.remove(websocket)

    def _setup_static_files(self) -> None:
        """Setup static file serving."""
        frontend_path = self.config.get("frontend_path")
        if frontend_path:
            try:
                self.fastapi_app.mount("/static", StaticFiles(directory=frontend_path), name="static")
                
                @self.fastapi_app.get("/", response_class=HTMLResponse)
                async def serve_frontend():
                    try:
                        with open(f"{frontend_path}/index.html", "r") as f:
                            return HTMLResponse(content=f.read())
                    except FileNotFoundError:
                        return HTMLResponse(content=self._get_fallback_html())
                        
            except Exception as e:
                logger.warning(f"Failed to setup static files: {e}")

    def _get_fallback_html(self) -> str:
        """Get fallback HTML when frontend is not available."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Contexten Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .status { background: #f0f0f0; padding: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Contexten Dashboard</h1>
                <div class="status">
                    <h2>Dashboard Backend Active</h2>
                    <p>The dashboard backend is running. Frontend build not found.</p>
                    <p><a href="/docs">View API Documentation</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    async def _broadcast_to_websockets(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all WebSocket connections."""
        if not self._websocket_connections:
            return

        disconnected = []
        for ws in self._websocket_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        # Remove disconnected WebSockets
        for ws in disconnected:
            self._websocket_connections.remove(ws)

    # Event handlers
    async def _handle_project_pin(self, event_data: Dict[str, Any]) -> None:
        """Handle project pin events."""
        await self._broadcast_to_websockets({
            "type": "project_pinned",
            "data": event_data
        })

    async def _handle_project_unpin(self, event_data: Dict[str, Any]) -> None:
        """Handle project unpin events."""
        await self._broadcast_to_websockets({
            "type": "project_unpinned",
            "data": event_data
        })

    async def _handle_flow_events(self, event_data: Dict[str, Any]) -> None:
        """Handle flow-related events."""
        await self._broadcast_to_websockets({
            "type": "flow_event",
            "data": event_data
        })

    async def _handle_github_events(self, event_data: Dict[str, Any]) -> None:
        """Handle GitHub events."""
        await self._broadcast_to_websockets({
            "type": "github_event",
            "data": event_data
        })

    async def _handle_linear_events(self, event_data: Dict[str, Any]) -> None:
        """Handle Linear events."""
        await self._broadcast_to_websockets({
            "type": "linear_event",
            "data": event_data
        })

    async def health_check(self) -> Dict[str, Any]:
        """Check dashboard extension health."""
        return {
            "status": "healthy",
            "server_running": self.server is not None,
            "pinned_projects": len(self._pinned_projects),
            "active_flows": len(self._project_flows),
            "websocket_connections": len(self._websocket_connections),
            "timestamp": self.app.current_time.isoformat(),
        }

