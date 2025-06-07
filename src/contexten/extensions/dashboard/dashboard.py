#!/usr/bin/env python3
"""
Contexten Dashboard Main Module
Multi-layered Workflow Orchestration Platform
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Import dashboard modules with absolute imports
try:
    from src.contexten.extensions.dashboard.api import router as api_router
    from src.contexten.extensions.dashboard.websocket import websocket_manager
    from src.contexten.extensions.dashboard.models import Project, Plan, PlanTask
    from src.contexten.extensions.dashboard.services.github_service import GitHubService
    from src.contexten.extensions.dashboard.services.linear_service import LinearService
    from src.contexten.extensions.dashboard.services.codegen_service import CodegenService
except ImportError as e:
    # Fallback to relative imports if absolute imports fail
    try:
        from .api import router as api_router
        from .websocket import websocket_manager
        from .models import Project, Plan, PlanTask
        from .services.github_service import GitHubService
        from .services.linear_service import LinearService
        from .services.codegen_service import CodegenService
    except ImportError:
        print(f"Import error: {e}")
        print("Please run the dashboard from the project root or use start_dashboard.py")
        sys.exit(1)

logger = logging.getLogger(__name__)


class Dashboard:
    """
    Dashboard extension for Contexten providing comprehensive project management
    and workflow orchestration capabilities.
    
    Features:
    - Project pinning and management
    - GitHub repository integration
    - Automated plan generation via Codegen SDK
    - Multi-layered workflow orchestration (Prefect, ControlFlow, MCP)
    - Real-time progress tracking
    - Quality gates and validation
    """
    
    def __init__(self, contexten_app):
        """Initialize the Dashboard extension.
        
        Args:
            contexten_app: The parent ContextenApp instance
        """
        self.contexten_app = contexten_app
        self.app = contexten_app.app
        
        # Initialize components
        self.websocket_manager = websocket_manager
        self.github_manager = GitHubService()
        self.codegen_generator = CodegenService()
        self.workflow_orchestrator = None
        
        # Setup routes and middleware
        self._setup_routes()
        self._setup_static_files()
        
        logger.info("Dashboard extension initialized")
    
    def _setup_routes(self):
        """Setup FastAPI routes for the dashboard."""
        # Include API routes
        self.app.include_router(api_router)
        
        # Add WebSocket routes
        self.websocket_manager.setup_routes(self.app)
        
        # Dashboard UI routes
        @self.app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard_ui():
            """Serve the main dashboard UI."""
            return await self._serve_dashboard_ui()
        
        @self.app.get("/dashboard/{path:path}")
        async def dashboard_spa_routes(path: str):
            """Handle SPA routing for dashboard."""
            return await self._serve_dashboard_ui()
    
    def _setup_static_files(self):
        """Setup static file serving for the React frontend."""
        frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "build")
        
        if os.path.exists(frontend_path):
            self.app.mount(
                "/dashboard/static", 
                StaticFiles(directory=os.path.join(frontend_path, "static")), 
                name="dashboard_static"
            )
            logger.info(f"Serving dashboard static files from: {frontend_path}")
        else:
            logger.warning(f"Dashboard frontend build not found at: {frontend_path}")
    
    async def _serve_dashboard_ui(self) -> HTMLResponse:
        """Serve the dashboard UI HTML."""
        frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "build")
        index_path = os.path.join(frontend_path, "index.html")
        
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            # Fallback HTML if React build is not available
            return HTMLResponse(content=self._get_fallback_html())
    
    def _get_fallback_html(self) -> str:
        """Get fallback HTML when React build is not available."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Contexten Dashboard</title>
            <style>
                body {{
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }}
                .container {{
                    text-align: center;
                    max-width: 800px;
                    padding: 2rem;
                }}
                .logo {{
                    font-size: 3rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                    background: linear-gradient(45deg, #fff, #f0f0f0);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                .subtitle {{
                    font-size: 1.2rem;
                    margin-bottom: 2rem;
                    opacity: 0.9;
                }}
                .features {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 1rem;
                    margin-top: 2rem;
                }}
                .feature {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 1.5rem;
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                }}
                .feature h3 {{
                    margin: 0 0 0.5rem 0;
                    font-size: 1.1rem;
                }}
                .feature p {{
                    margin: 0;
                    opacity: 0.8;
                    font-size: 0.9rem;
                }}
                .status {{
                    margin-top: 2rem;
                    padding: 1rem;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                }}
                .api-link {{
                    color: #fff;
                    text-decoration: none;
                    background: rgba(255, 255, 255, 0.2);
                    padding: 0.5rem 1rem;
                    border-radius: 5px;
                    display: inline-block;
                    margin-top: 1rem;
                    transition: background 0.3s;
                }}
                .api-link:hover {{
                    background: rgba(255, 255, 255, 0.3);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">Contexten Dashboard</div>
                <div class="subtitle">Multi-layered Workflow Orchestration Platform</div>
                
                <div class="features">
                    <div class="feature">
                        <h3>🏗️ Project Management</h3>
                        <p>Pin GitHub repositories, manage settings, and track progress</p>
                    </div>
                    <div class="feature">
                        <h3>🤖 AI-Powered Planning</h3>
                        <p>Generate automated plans using Codegen SDK integration</p>
                    </div>
                    <div class="feature">
                        <h3>⚡ Workflow Orchestration</h3>
                        <p>Multi-layered execution with Prefect, ControlFlow, and MCP</p>
                    </div>
                    <div class="feature">
                        <h3>✅ Quality Gates</h3>
                        <p>Automated code analysis and validation cycles</p>
                    </div>
                </div>
                
                <div class="status">
                    <h3>🚀 Dashboard Status</h3>
                    <p>Backend API is running. React frontend build in progress.</p>
                    <a href="/dashboard/docs" class="api-link">View API Documentation</a>
                </div>
            </div>
            
            <script>
                // Auto-refresh to check for React build
                setTimeout(() => {{
                    window.location.reload();
                }}, 30000);
            </script>
        </body>
        </html>
        """
    
    async def initialize(self):
        """Initialize the dashboard extension."""
        try:
            # Initialize database
            await initialize_database()
            logger.info("Dashboard database initialized")
            
            # Initialize components
            await self.github_manager.initialize()
            await self.codegen_generator.initialize()
            await self.workflow_orchestrator.initialize()
            
            logger.info("Dashboard extension fully initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")
            return False
    
    async def handle_github_event(self, event_type: str, payload: Dict[str, Any]):
        """Handle GitHub webhook events."""
        try:
            logger.info(f"Dashboard handling GitHub event: {event_type}")
            
            # Process the event and broadcast updates
            await self.github_manager.handle_event(event_type, payload)
            
            # Broadcast real-time update to connected clients
            await self.websocket_manager.broadcast({
                "type": "github_event",
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload
            })
            
        except Exception as e:
            logger.error(f"Failed to handle GitHub event: {e}")
    
    async def handle_linear_event(self, event_type: str, payload: Dict[str, Any]):
        """Handle Linear webhook events."""
        try:
            logger.info(f"Dashboard handling Linear event: {event_type}")
            
            # Broadcast real-time update to connected clients
            await self.websocket_manager.broadcast({
                "type": "linear_event",
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload
            })
            
        except Exception as e:
            logger.error(f"Failed to handle Linear event: {e}")
    
    async def handle_workflow_update(self, workflow_id: str, status: str, progress: float):
        """Handle workflow execution updates."""
        try:
            logger.info(f"Dashboard handling workflow update: {workflow_id} - {status} ({progress}%)")
            
            # Broadcast real-time update to connected clients
            await self.websocket_manager.broadcast({
                "type": "workflow_update",
                "workflow_id": workflow_id,
                "status": status,
                "progress": progress,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to handle workflow update: {e}")
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics and metrics."""
        try:
            # TODO: Implement comprehensive dashboard statistics
            stats = {
                "total_projects": 0,
                "active_workflows": 0,
                "completed_tasks": 0,
                "pending_prs": 0,
                "quality_score": 85.5,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup dashboard resources."""
        try:
            await self.websocket_manager.cleanup()
            await db_manager.close()
            logger.info("Dashboard extension cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup dashboard: {e}")


# Integration function for ContextenApp
def setup_dashboard(contexten_app) -> Dashboard:
    """Setup dashboard extension for ContextenApp.
    
    Args:
        contexten_app: The ContextenApp instance
        
    Returns:
        Dashboard: The initialized dashboard extension
    """
    dashboard = Dashboard(contexten_app)
    
    # Add dashboard to the ContextenApp
    contexten_app.dashboard = dashboard
    
    return dashboard
