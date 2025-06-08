"""
Main Dashboard for Single-User System

Central orchestrator that manages all components and provides the main interface.
Integrates all 11 extensions into a cohesive, functional system.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from graph_sitter.shared.logging.get_logger import get_logger
from .models import DashboardConfig, ProjectStatus, FlowStatus
from .settings_manager import SettingsManager
from .project_manager import ProjectManager
from .planning_engine import PlanningEngine
from .workflow_engine import WorkflowEngine
from .quality_manager import QualityManager
from .event_coordinator import EventCoordinator

logger = get_logger(__name__)


class Dashboard:
    """
    Main dashboard that orchestrates all components.
    
    Features:
    - Central coordination of all 11 extensions
    - FastAPI web interface
    - Real-time WebSocket updates
    - Project lifecycle management
    - Settings and configuration management
    """
    
    def __init__(self, config_file: str = "dashboard_config.json"):
        # Core components
        self.settings_manager = SettingsManager(config_file)
        self.project_manager = ProjectManager(self)
        self.planning_engine = PlanningEngine(self)
        self.workflow_engine = WorkflowEngine(self)
        self.quality_manager = QualityManager(self)
        self.event_coordinator = EventCoordinator(self)
        
        # FastAPI app
        self.app = FastAPI(title="Contexten Dashboard", version="1.0.0")
        self.templates = None
        
        # State
        self.initialized = False
        self.startup_time = None
        
        # Setup routes
        self._setup_routes()
        
    async def initialize(self):
        """Initialize all dashboard components"""
        if self.initialized:
            logger.warning("Dashboard already initialized")
            return
            
        logger.info("Initializing Dashboard...")
        self.startup_time = datetime.now()
        
        try:
            # Initialize components in order
            await self.event_coordinator.initialize()
            await self.project_manager.initialize()
            await self.planning_engine.initialize()
            await self.workflow_engine.initialize()
            await self.quality_manager.initialize()
            
            # Setup templates if frontend exists
            frontend_path = Path("src/contexten/frontend")
            if frontend_path.exists():
                self.templates = Jinja2Templates(directory=str(frontend_path))
                self.app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
                
            self.initialized = True
            logger.info("Dashboard initialization complete")
            
            # Emit startup event
            await self.event_coordinator.emit_event(
                "dashboard_started",
                "dashboard",
                data={"startup_time": self.startup_time.isoformat()}
            )
            
        except Exception as e:
            logger.error(f"Dashboard initialization failed: {e}")
            raise
            
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        # Main dashboard page
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            if self.templates:
                return self.templates.TemplateResponse("index.html", {"request": request})
            else:
                return HTMLResponse(self._get_simple_html())
                
        # API Routes
        
        # Projects
        @self.app.get("/api/projects")
        async def get_projects():
            projects = await self.project_manager.get_all_projects()
            return [self._serialize_project(p) for p in projects]
            
        @self.app.get("/api/projects/pinned")
        async def get_pinned_projects():
            projects = await self.project_manager.get_pinned_projects()
            return [self._serialize_project(p) for p in projects]
            
        @self.app.get("/api/projects/{project_id}")
        async def get_project(project_id: str):
            project = await self.project_manager.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            return self._serialize_project(project)
            
        @self.app.post("/api/projects/pin")
        async def pin_project(request: Dict[str, str]):
            repo_url = request.get("repo_url")
            if not repo_url:
                raise HTTPException(status_code=400, detail="repo_url required")
                
            project = await self.project_manager.pin_project(repo_url)
            if not project:
                raise HTTPException(status_code=400, detail="Failed to pin project")
                
            return self._serialize_project(project)
            
        @self.app.post("/api/projects/{project_id}/unpin")
        async def unpin_project(project_id: str):
            success = await self.project_manager.unpin_project(project_id)
            if not success:
                raise HTTPException(status_code=404, detail="Project not found")
            return {"success": True}
            
        # Repository discovery
        @self.app.get("/api/repositories")
        async def discover_repositories(force_refresh: bool = False):
            repos = await self.project_manager.discover_repositories(force_refresh)
            return repos
            
        # Planning
        @self.app.post("/api/projects/{project_id}/plan")
        async def generate_plan(project_id: str, request: Dict[str, str]):
            requirements = request.get("requirements")
            if not requirements:
                raise HTTPException(status_code=400, detail="requirements required")
                
            # Get analysis if available
            analysis = await self.quality_manager.get_analysis(project_id)
            
            plan = await self.planning_engine.generate_plan(project_id, requirements, analysis)
            if not plan:
                raise HTTPException(status_code=400, detail="Failed to generate plan")
                
            return self._serialize_plan(plan)
            
        @self.app.get("/api/projects/{project_id}/plans")
        async def get_project_plans(project_id: str):
            plans = await self.planning_engine.get_project_plans(project_id)
            return [self._serialize_plan(p) for p in plans]
            
        # Workflows
        @self.app.post("/api/projects/{project_id}/workflow/start")
        async def start_workflow(project_id: str):
            success = await self.workflow_engine.start_workflow(project_id)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to start workflow")
            return {"success": True}
            
        @self.app.post("/api/projects/{project_id}/workflow/stop")
        async def stop_workflow(project_id: str):
            success = await self.workflow_engine.stop_workflow(project_id)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to stop workflow")
            return {"success": True}
            
        @self.app.get("/api/projects/{project_id}/workflow/status")
        async def get_workflow_status(project_id: str):
            status = await self.workflow_engine.get_workflow_status(project_id)
            return status or {"status": "inactive"}
            
        # Analysis
        @self.app.post("/api/projects/{project_id}/analyze")
        async def analyze_project(project_id: str, force_refresh: bool = False):
            analysis = await self.quality_manager.analyze_project(project_id, force_refresh)
            if not analysis:
                raise HTTPException(status_code=400, detail="Analysis failed")
            return self._serialize_analysis(analysis)
            
        @self.app.get("/api/projects/{project_id}/analysis")
        async def get_project_analysis(project_id: str):
            analysis = await self.quality_manager.get_analysis(project_id)
            if not analysis:
                raise HTTPException(status_code=404, detail="No analysis found")
            return self._serialize_analysis(analysis)
            
        # Deployment
        @self.app.post("/api/projects/{project_id}/deploy")
        async def deploy_project(project_id: str, request: Dict[str, str] = None):
            environment_type = (request or {}).get("environment_type", "development")
            deployment = await self.quality_manager.deploy_to_sandbox(project_id, environment_type)
            if not deployment:
                raise HTTPException(status_code=400, detail="Deployment failed")
            return self._serialize_deployment(deployment)
            
        @self.app.get("/api/projects/{project_id}/deployment")
        async def get_project_deployment(project_id: str):
            deployment = await self.quality_manager.get_project_deployment(project_id)
            if not deployment:
                raise HTTPException(status_code=404, detail="No deployment found")
            return self._serialize_deployment(deployment)
            
        # Quality summary
        @self.app.get("/api/projects/{project_id}/quality")
        async def get_quality_summary(project_id: str):
            summary = await self.quality_manager.get_quality_summary(project_id)
            return summary
            
        # Events
        @self.app.get("/api/events")
        async def get_recent_events(limit: int = 50, event_type: str = None, project_id: str = None):
            events = await self.event_coordinator.get_recent_events(limit, event_type, project_id)
            return [self._serialize_event(e) for e in events]
            
        @self.app.get("/api/events/statistics")
        async def get_event_statistics():
            return await self.event_coordinator.get_event_statistics()
            
        # Settings
        @self.app.get("/api/settings")
        async def get_settings():
            return {
                "setup_status": self.settings_manager.get_setup_status(),
                "notification_settings": await self.event_coordinator.get_notification_settings(),
                "extensions": {
                    name: {
                        "enabled": self.settings_manager.is_extension_enabled(name),
                        "config": self.settings_manager.get_extension_config(name).config
                    }
                    for name in ["github", "linear", "codegen", "slack", "circleci", 
                               "grainchain", "graph_sitter", "prefect", "controlflow", "modal"]
                }
            }
            
        @self.app.post("/api/settings/notifications")
        async def update_notification_settings(settings: Dict[str, bool]):
            await self.event_coordinator.update_notification_settings(settings)
            return {"success": True}
            
        @self.app.post("/api/settings/test-slack")
        async def test_slack():
            success = await self.event_coordinator.test_slack_integration()
            return {"success": success}
            
        # System status
        @self.app.get("/api/status")
        async def get_system_status():
            return {
                "initialized": self.initialized,
                "startup_time": self.startup_time.isoformat() if self.startup_time else None,
                "uptime_seconds": (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0,
                "project_statistics": await self.project_manager.get_project_statistics(),
                "active_workflows": len(await self.workflow_engine.get_active_workflows()),
                "event_statistics": await self.event_coordinator.get_event_statistics()
            }
            
        # WebSocket for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            await self.event_coordinator.add_websocket_connection(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except Exception as e:
                logger.info(f"WebSocket disconnected: {e}")
            finally:
                await self.event_coordinator.remove_websocket_connection(websocket)
                
    def _serialize_project(self, project) -> Dict[str, Any]:
        """Serialize project for API response"""
        return {
            "project_id": project.project_id,
            "name": project.name,
            "github_repo": project.github_repo,
            "github_owner": project.github_owner,
            "status": project.status.value,
            "flow_status": project.flow_status.value,
            "pinned": project.pinned,
            "pinned_at": project.pinned_at.isoformat() if project.pinned_at else None,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "current_plan_id": project.current_plan_id,
            "active_workflow_id": project.active_workflow_id,
            "linear_project_id": project.linear_project_id,
            "has_analysis": bool(project.analysis),
            "has_deployment": bool(project.deployment),
            "github_data": project.github_data
        }
        
    def _serialize_plan(self, plan) -> Dict[str, Any]:
        """Serialize plan for API response"""
        return {
            "plan_id": plan.plan_id,
            "project_id": plan.project_id,
            "title": plan.title,
            "description": plan.description,
            "requirements": plan.requirements,
            "status": plan.status,
            "created_at": plan.created_at.isoformat(),
            "estimated_duration": plan.estimated_duration,
            "task_count": len(plan.tasks),
            "tasks": [self._serialize_task(task) for task in plan.tasks]
        }
        
    def _serialize_task(self, task) -> Dict[str, Any]:
        """Serialize task for API response"""
        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "status": task.status.value,
            "progress": task.progress,
            "estimated_duration": task.estimated_duration,
            "linear_issue_id": task.linear_issue_id,
            "github_pr_id": task.github_pr_id,
            "codegen_task_id": task.codegen_task_id,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message
        }
        
    def _serialize_analysis(self, analysis) -> Dict[str, Any]:
        """Serialize analysis for API response"""
        return {
            "project_id": analysis.project_id,
            "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
            "quality_score": analysis.quality_score,
            "complexity_score": analysis.complexity_score,
            "maintainability_score": analysis.maintainability_score,
            "test_coverage": analysis.test_coverage,
            "error_count": len(analysis.errors),
            "missing_features_count": len(analysis.missing_features),
            "config_issues_count": len(analysis.config_issues),
            "errors": [
                {
                    "file_path": e.file_path,
                    "line_number": e.line_number,
                    "error_type": e.error_type,
                    "message": e.message,
                    "severity": e.severity,
                    "suggestion": e.suggestion
                }
                for e in analysis.errors[:10]  # Limit to first 10
            ],
            "missing_features": [
                {
                    "feature_name": f.feature_name,
                    "description": f.description,
                    "priority": f.priority
                }
                for f in analysis.missing_features[:5]  # Limit to first 5
            ],
            "config_issues": [
                {
                    "config_file": i.config_file,
                    "issue_type": i.issue_type,
                    "message": i.message
                }
                for i in analysis.config_issues[:5]  # Limit to first 5
            ]
        }
        
    def _serialize_deployment(self, deployment) -> Dict[str, Any]:
        """Serialize deployment for API response"""
        return {
            "deployment_id": deployment.deployment_id,
            "project_id": deployment.project_id,
            "status": deployment.status.value,
            "sandbox": {
                "sandbox_id": deployment.sandbox.sandbox_id,
                "environment_type": deployment.sandbox.environment_type,
                "status": deployment.sandbox.status,
                "url": deployment.sandbox.url,
                "created_at": deployment.sandbox.created_at.isoformat()
            },
            "test_results": [
                {
                    "test_name": t.test_name,
                    "status": t.status,
                    "duration": t.duration,
                    "message": t.message
                }
                for t in deployment.test_results
            ],
            "snapshots": [
                {
                    "snapshot_id": s.snapshot_id,
                    "created_at": s.created_at.isoformat(),
                    "description": s.description,
                    "status": s.status
                }
                for s in deployment.snapshots
            ],
            "created_at": deployment.created_at.isoformat(),
            "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None
        }
        
    def _serialize_event(self, event) -> Dict[str, Any]:
        """Serialize event for API response"""
        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "source": event.source,
            "project_id": event.project_id,
            "task_id": event.task_id,
            "data": event.data,
            "timestamp": event.timestamp.isoformat()
        }
        
    def _get_simple_html(self) -> str:
        """Get simple HTML page when templates not available"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Contexten Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .status { padding: 20px; background: #f0f0f0; border-radius: 5px; margin: 20px 0; }
                .api-link { display: block; margin: 10px 0; padding: 10px; background: #e0e0e0; text-decoration: none; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Contexten Dashboard</h1>
                <div class="status">
                    <h2>System Status</h2>
                    <p>Dashboard is running and ready to use.</p>
                    <p>Frontend templates not found - using simple interface.</p>
                </div>
                <h2>API Endpoints</h2>
                <a href="/api/status" class="api-link">System Status</a>
                <a href="/api/projects" class="api-link">Projects</a>
                <a href="/api/repositories" class="api-link">Discover Repositories</a>
                <a href="/api/settings" class="api-link">Settings</a>
                <a href="/api/events" class="api-link">Recent Events</a>
                <h2>Setup</h2>
                <p>Configure your environment variables and start using the dashboard:</p>
                <ul>
                    <li>GITHUB_TOKEN - GitHub personal access token</li>
                    <li>CODEGEN_ORG_ID - Your Codegen organization ID</li>
                    <li>CODEGEN_TOKEN - Your Codegen API token</li>
                    <li>LINEAR_API_KEY - Linear API key (optional)</li>
                    <li>SLACK_WEBHOOK - Slack webhook URL (optional)</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
    async def shutdown(self):
        """Shutdown the dashboard"""
        logger.info("Shutting down Dashboard...")
        
        if self.event_coordinator:
            await self.event_coordinator.shutdown()
            
        logger.info("Dashboard shutdown complete")


# Factory function for creating dashboard instance
def create_dashboard(config_file: str = "dashboard_config.json") -> Dashboard:
    """Create and return a dashboard instance"""
    return Dashboard(config_file)

