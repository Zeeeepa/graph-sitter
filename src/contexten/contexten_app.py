"""
Enhanced CodegenApp (renamed to ContextenApp) with comprehensive CI/CD system integration.

This module provides the main application class that integrates all components:
- Database management (7-module system)
- System orchestration
- Event handling (GitHub, Linear, Slack)
- Performance monitoring
- Error handling and recovery
- Continuous learning capabilities
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

# Core system imports
from .config import get_settings, get_database_config, get_integrations_config
from .core import SystemOrchestrator, ErrorHandler, PerformanceMonitor
from .database import (
    get_database_manager, TaskModel, ProjectModel, EventModel,
    CodebaseModel, AnalyticsModel, LearningModel
)

# Integration imports
from .extensions.events.github import GitHub
from .extensions.events.linear import Linear
from .extensions.events.slack import Slack

# Graph-sitter imports for codebase analysis
from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.configs.models.secrets import SecretsConfig
from graph_sitter import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ContextenApp:
    """
    Enhanced CI/CD application with comprehensive system integration.
    
    This is the main application class that coordinates all system components:
    - Database operations across 7 modules
    - Event handling for GitHub, Linear, Slack
    - Performance monitoring and optimization
    - Error handling and recovery
    - Continuous learning and improvement
    - Codebase analysis and management
    """
    
    def __init__(
        self,
        name: str,
        repo: Optional[str] = None,
        tmp_dir: str = "/tmp/contexten",
        commit: Optional[str] = "latest",
        enable_monitoring: bool = True,
        enable_learning: bool = True
    ):
        self.name = name
        self.tmp_dir = tmp_dir
        self.repo = repo
        self.commit = commit
        self.enable_monitoring = enable_monitoring
        self.enable_learning = enable_learning
        
        # Load configurations
        self.settings = get_settings()
        self.db_config = get_database_config()
        self.integrations_config = get_integrations_config()
        
        # Initialize core components
        self.orchestrator = SystemOrchestrator()
        self.db_manager = get_database_manager()
        self.error_handler = ErrorHandler()
        self.performance_monitor = PerformanceMonitor() if enable_monitoring else None
        
        # Initialize event handlers
        self.linear = Linear(self)
        self.slack = Slack(self)
        self.github = GitHub(self)
        
        # Codebase management
        self.codebase: Optional[Codebase] = None
        self.codebases: Dict[str, Codebase] = {}
        
        # Application state
        self._initialized = False
        self._shutdown = False
        
        # Create FastAPI app with lifespan
        self.app = FastAPI(
            title=f"Contexten CI/CD System - {name}",
            description="Comprehensive CI/CD system with continuous learning",
            version="1.0.0",
            lifespan=self._lifespan
        )
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"ContextenApp '{name}' initialized")
    
    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """FastAPI lifespan context manager for startup and shutdown."""
        # Startup
        await self.initialize()
        yield
        # Shutdown
        await self.shutdown()
    
    async def initialize(self) -> None:
        """Initialize all system components."""
        if self._initialized:
            return
        
        logger.info(f"Initializing ContextenApp '{self.name}'")
        
        try:
            # Initialize orchestrator (which initializes database and monitoring)
            await self.orchestrator.initialize()
            
            # Register this app with the orchestrator
            self.orchestrator.register_component("contexten_app", self)
            
            # Setup event handlers
            await self._setup_event_handlers()
            
            # Parse initial repository if provided
            if self.repo:
                await self._parse_repo(self.repo, self.commit)
            
            # Initialize learning system if enabled
            if self.enable_learning:
                await self._initialize_learning_system()
            
            self._initialized = True
            logger.info(f"ContextenApp '{self.name}' initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize ContextenApp: {e}")
            await self.error_handler.handle_error(e, {"component": "contexten_app", "operation": "initialize"})
            raise
    
    async def shutdown(self) -> None:
        """Shutdown all system components."""
        if self._shutdown:
            return
        
        logger.info(f"Shutting down ContextenApp '{self.name}'")
        
        try:
            # Shutdown orchestrator
            await self.orchestrator.shutdown()
            
            self._shutdown = True
            logger.info(f"ContextenApp '{self.name}' shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during ContextenApp shutdown: {e}")
    
    async def _setup_event_handlers(self) -> None:
        """Setup event handlers for system events."""
        # Register event handlers with the orchestrator
        self.orchestrator.register_event_handler("task_created", self._on_task_created)
        self.orchestrator.register_event_handler("task_completed", self._on_task_completed)
        self.orchestrator.register_event_handler("task_failed", self._on_task_failed)
        self.orchestrator.register_event_handler("project_created", self._on_project_created)
        self.orchestrator.register_event_handler("performance_alert", self._on_performance_alert)
        
        logger.info("Event handlers registered")
    
    async def _initialize_learning_system(self) -> None:
        """Initialize the continuous learning system."""
        try:
            # Create initial learning patterns
            async with self.orchestrator.get_db_session() as session:
                # Check if learning system is already initialized
                existing_learning = await session.execute(
                    "SELECT COUNT(*) FROM learning WHERE learning_type = 'system_improvement'"
                )
                count = existing_learning.scalar()
                
                if count == 0:
                    # Create initial learning entry
                    learning = LearningModel(
                        name="System Initialization",
                        description="Initial learning system setup",
                        learning_type="system_improvement",
                        data={"initialized_at": datetime.utcnow().isoformat()},
                        source_component="contexten_app"
                    )
                    session.add(learning)
                    await session.flush()
                    
                    logger.info("Learning system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize learning system: {e}")
    
    # Event handlers
    async def _on_task_created(self, data: Dict[str, Any]) -> None:
        """Handle task created events."""
        logger.info(f"Task created: {data.get('task_id')}")
        
        # Log analytics event
        await self._log_analytics_event("task_started", data)
    
    async def _on_task_completed(self, data: Dict[str, Any]) -> None:
        """Handle task completed events."""
        logger.info(f"Task completed: {data.get('task_id')}")
        
        # Log analytics event
        await self._log_analytics_event("task_completed", data)
        
        # Update learning system if enabled
        if self.enable_learning:
            await self._update_learning_from_task(data, success=True)
    
    async def _on_task_failed(self, data: Dict[str, Any]) -> None:
        """Handle task failed events."""
        logger.warning(f"Task failed: {data.get('task_id')}")
        
        # Log analytics event
        await self._log_analytics_event("task_failed", data)
        
        # Update learning system if enabled
        if self.enable_learning:
            await self._update_learning_from_task(data, success=False)
    
    async def _on_project_created(self, data: Dict[str, Any]) -> None:
        """Handle project created events."""
        logger.info(f"Project created: {data.get('project_id')}")
        
        # Log analytics event
        await self._log_analytics_event("project_created", data)
    
    async def _on_performance_alert(self, data: Dict[str, Any]) -> None:
        """Handle performance alert events."""
        logger.warning(f"Performance alert: {data.get('issues')}")
        
        # Log analytics event
        await self._log_analytics_event("performance_alert", data)
    
    async def _log_analytics_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log an analytics event."""
        try:
            async with self.orchestrator.get_db_session() as session:
                analytics = AnalyticsModel(
                    name=f"Event: {event_type}",
                    description=f"Analytics event for {event_type}",
                    event_type=event_type,
                    component="contexten_app",
                    operation=event_type,
                    event_data=data,
                    success=True
                )
                session.add(analytics)
                await session.flush()
        except Exception as e:
            logger.error(f"Failed to log analytics event: {e}")
    
    async def _update_learning_from_task(self, task_data: Dict[str, Any], success: bool) -> None:
        """Update learning system based on task completion."""
        try:
            async with self.orchestrator.get_db_session() as session:
                learning = LearningModel(
                    name=f"Task Learning: {task_data.get('task_id')}",
                    description=f"Learning from task {'success' if success else 'failure'}",
                    learning_type="success_analysis" if success else "error_analysis",
                    data={
                        "task_data": task_data,
                        "success": success,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    source_component="contexten_app",
                    confidence_score=0.8 if success else 0.6
                )
                session.add(learning)
                await session.flush()
        except Exception as e:
            logger.error(f"Failed to update learning system: {e}")
    
    # Codebase management methods
    async def _parse_repo(self, repo_name: str, commit: Optional[str] = None) -> None:
        """Parse a GitHub repository and cache it."""
        try:
            logger.info(f"[CODEBASE] Parsing repository: {repo_name}")
            
            # Create codebase configuration
            config = CodebaseConfig(sync_enabled=True)
            secrets = SecretsConfig(
                github_token=os.environ.get("GITHUB_ACCESS_TOKEN"),
                linear_api_key=os.environ.get("LINEAR_ACCESS_TOKEN")
            )
            
            # Parse the repository
            codebase = Codebase.from_repo(
                repo_full_name=repo_name,
                tmp_dir=self.tmp_dir,
                commit=commit,
                config=config,
                secrets=secrets
            )
            
            # Cache the codebase
            self.codebase = codebase
            self.codebases[repo_name] = codebase
            
            # Store codebase information in database
            await self._store_codebase_info(repo_name, codebase)
            
            logger.info(f"[CODEBASE] Successfully parsed and cached: {repo_name}")
            
        except Exception as e:
            logger.error(f"[CODEBASE] Failed to parse repository {repo_name}: {e}")
            await self.error_handler.handle_error(e, {
                "component": "codebase",
                "operation": "parse_repo",
                "repo_name": repo_name
            })
            raise
    
    async def _store_codebase_info(self, repo_name: str, codebase: Codebase) -> None:
        """Store codebase information in the database."""
        try:
            async with self.orchestrator.get_db_session() as session:
                codebase_model = CodebaseModel(
                    name=repo_name,
                    description=f"Codebase for repository {repo_name}",
                    repository_url=f"https://github.com/{repo_name}",
                    commit_sha=self.commit or "latest",
                    branch="main",  # Default branch
                    status="completed",
                    total_files=len(codebase.files) if hasattr(codebase, 'files') else 0,
                    analysis_completed_at=datetime.utcnow()
                )
                session.add(codebase_model)
                await session.flush()
                
                logger.info(f"Stored codebase info for {repo_name}")
        except Exception as e:
            logger.error(f"Failed to store codebase info: {e}")
    
    def get_codebase(self, repo_name: Optional[str] = None) -> Codebase:
        """Get a cached codebase by repository name."""
        if repo_name:
            if repo_name not in self.codebases:
                raise KeyError(f"Repository {repo_name} has not been parsed")
            return self.codebases[repo_name]
        else:
            if not self.codebase:
                raise KeyError("No default repository has been parsed")
            return self.codebase
    
    async def add_repo(self, repo_name: str, commit: Optional[str] = None) -> None:
        """Add a new repository to parse and cache."""
        await self._parse_repo(repo_name, commit)
    
    # Event simulation and handling
    async def simulate_event(self, provider: str, event_type: str, payload: Dict[str, Any]) -> Any:
        """Simulate an event without running the server."""
        provider_map = {
            "slack": self.slack,
            "github": self.github,
            "linear": self.linear
        }
        
        if provider not in provider_map:
            raise ValueError(f"Unknown provider: {provider}. Must be one of {list(provider_map.keys())}")
        
        handler = provider_map[provider]
        
        # Log the event
        await self.orchestrator.log_event({
            "name": f"Simulated {provider} event",
            "description": f"Simulated {event_type} event from {provider}",
            "event_type": event_type,
            "provider": provider,
            "payload": payload,
            "external_id": f"sim_{datetime.utcnow().timestamp()}"
        })
        
        return await handler.handle(payload)
    
    # API endpoints
    async def root(self) -> str:
        """Render the main page."""
        system_health = await self.orchestrator.get_system_health()
        
        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Contexten CI/CD System</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 20px;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                        background-color: #1a1a1a;
                        color: #ffffff;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 40px;
                    }}
                    h1 {{
                        font-size: 3rem;
                        font-weight: 700;
                        letter-spacing: -0.05em;
                        margin-bottom: 10px;
                    }}
                    .subtitle {{
                        font-size: 1.2rem;
                        color: #888;
                    }}
                    .status {{
                        background: #2a2a2a;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 20px 0;
                    }}
                    .status-item {{
                        display: flex;
                        justify-content: space-between;
                        margin: 10px 0;
                    }}
                    .healthy {{ color: #4ade80; }}
                    .degraded {{ color: #fbbf24; }}
                    .unhealthy {{ color: #f87171; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Contexten CI/CD</h1>
                    <div class="subtitle">Comprehensive CI/CD System with Continuous Learning</div>
                </div>
                
                <div class="status">
                    <h2>System Status</h2>
                    <div class="status-item">
                        <span>Overall Status:</span>
                        <span class="{system_health['status']}">{system_health['status'].title()}</span>
                    </div>
                    <div class="status-item">
                        <span>Application:</span>
                        <span>{self.name}</span>
                    </div>
                    <div class="status-item">
                        <span>Monitoring:</span>
                        <span class="{'healthy' if self.enable_monitoring else 'degraded'}">
                            {'Enabled' if self.enable_monitoring else 'Disabled'}
                        </span>
                    </div>
                    <div class="status-item">
                        <span>Learning:</span>
                        <span class="{'healthy' if self.enable_learning else 'degraded'}">
                            {'Enabled' if self.enable_learning else 'Disabled'}
                        </span>
                    </div>
                </div>
            </body>
        </html>
        """
    
    async def health_check(self) -> Dict[str, Any]:
        """Get system health status."""
        return await self.orchestrator.get_system_health()
    
    async def handle_slack_event(self, request: Request) -> Any:
        """Handle incoming Slack events."""
        payload = await request.json()
        
        # Log the event
        await self.orchestrator.log_event({
            "name": "Slack webhook event",
            "description": "Incoming Slack webhook event",
            "event_type": payload.get("type", "unknown"),
            "provider": "slack",
            "payload": payload
        })
        
        return await self.slack.handle(payload)
    
    async def handle_github_event(self, request: Request) -> Any:
        """Handle incoming GitHub events."""
        payload = await request.json()
        
        # Log the event
        await self.orchestrator.log_event({
            "name": "GitHub webhook event",
            "description": "Incoming GitHub webhook event",
            "event_type": request.headers.get("X-GitHub-Event", "unknown"),
            "provider": "github",
            "payload": payload,
            "headers": dict(request.headers)
        })
        
        return await self.github.handle(payload, request)
    
    async def handle_linear_event(self, request: Request) -> Any:
        """Handle incoming Linear events."""
        payload = await request.json()
        
        # Log the event
        await self.orchestrator.log_event({
            "name": "Linear webhook event",
            "description": "Incoming Linear webhook event",
            "event_type": payload.get("type", "unknown"),
            "provider": "linear",
            "payload": payload
        })
        
        return await self.linear.handle(payload)
    
    def _setup_routes(self) -> None:
        """Set up the FastAPI routes for different event types."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def _root():
            return await self.root()
        
        @self.app.get("/health")
        async def _health_check():
            return await self.health_check()
        
        @self.app.post("/slack/events")
        async def _handle_slack_event(request: Request):
            return await self.handle_slack_event(request)
        
        @self.app.post("/github/events")
        async def _handle_github_event(request: Request):
            return await self.handle_github_event(request)
        
        @self.app.post("/linear/events")
        async def _handle_linear_event(request: Request):
            return await self.handle_linear_event(request)
        
        # Additional API endpoints for system management
        @self.app.get("/api/system/status")
        async def _system_status():
            return await self.health_check()
        
        @self.app.get("/api/performance/metrics")
        async def _performance_metrics():
            if not self.performance_monitor:
                raise HTTPException(status_code=404, detail="Performance monitoring not enabled")
            return await self.performance_monitor.get_current_metrics()
        
        @self.app.get("/api/performance/report")
        async def _performance_report(hours: int = 24):
            if not self.performance_monitor:
                raise HTTPException(status_code=404, detail="Performance monitoring not enabled")
            return await self.performance_monitor.get_performance_report(hours)
        
        @self.app.get("/api/errors/statistics")
        async def _error_statistics():
            return self.error_handler.get_error_statistics()
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs) -> None:
        """Run the FastAPI application."""
        import uvicorn
        
        logger.info(f"Starting ContextenApp '{self.name}' on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, **kwargs)


# Backward compatibility alias
CodegenApp = ContextenApp

