"""
Contexten Management Dashboard

A comprehensive web-based dashboard for managing and monitoring
the Contexten orchestrator, integrations, and workflows.
"""

import os
import secrets
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# Import monitoring components
try:
    from graph_sitter.monitoring import (
        QualityMonitor,
        MonitoringConfig,
        RealTimeAnalyzer,
        AlertSystem,
        DashboardMonitor,
        ContinuousMonitor
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Real-time monitoring components not available")

# Import Codegen SDK
from codegen import Agent as CodegenAgent

# Import contexten components
from ..extensions.linear.enhanced_agent import EnhancedLinearAgent, LinearAgentConfig
from ..extensions.github.enhanced_agent import EnhancedGitHubAgent, GitHubAgentConfig
from ..extensions.slack.enhanced_agent import EnhancedSlackAgent, SlackAgentConfig
from ...shared.logging.get_logger import get_logger
from .chat_manager import ChatManager
from .monitoring_integration import EnhancedDashboardMonitoring
from .autonomous_dependency_manager import AutonomousDependencyManager
from .autonomous_failure_analyzer import AutonomousFailureAnalyzer

logger = get_logger(__name__)

# Configuration
class DashboardConfig:
    """Dashboard configuration"""
    
    def __init__(self):
        # Server configuration
        self.host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
        self.port = int(os.getenv("DASHBOARD_PORT", "8080"))
        self.debug = os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"
        
        # Security
        self.secret_key = os.getenv("DASHBOARD_SECRET_KEY", secrets.token_urlsafe(32))
        
        # OAuth Configuration
        self.github_client_id = os.getenv("GITHUB_CLIENT_ID")
        self.github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.linear_client_id = os.getenv("LINEAR_CLIENT_ID")
        self.linear_client_secret = os.getenv("LINEAR_CLIENT_SECRET")
        self.slack_client_id = os.getenv("SLACK_CLIENT_ID")
        self.slack_client_secret = os.getenv("SLACK_CLIENT_SECRET")
        
        # Codegen SDK
        self.codegen_org_id = os.getenv("CODEGEN_ORG_ID")
        self.codegen_token = os.getenv("CODEGEN_TOKEN")
        
        # Redirect URIs
        self.base_url = os.getenv("DASHBOARD_BASE_URL", f"http://localhost:{self.port}")
        self.github_redirect_uri = f"{self.base_url}/auth/github/callback"
        self.linear_redirect_uri = f"{self.base_url}/auth/linear/callback"
        self.slack_redirect_uri = f"{self.base_url}/auth/slack/callback"
        
        # Real-time monitoring configuration
        self.monitoring_enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
        self.monitoring_interval = int(os.getenv("MONITORING_INTERVAL", "300"))  # 5 minutes
        self.alert_check_interval = int(os.getenv("ALERT_CHECK_INTERVAL", "60"))  # 1 minute
        self.websocket_enabled = os.getenv("WEBSOCKET_ENABLED", "true").lower() == "true"

# Global configuration
config = DashboardConfig()

# FastAPI app
app = FastAPI(
    title="Contexten Management Dashboard",
    description="Management interface for GitHub/Linear integrations with Codegen SDK",
    version="1.0.0",
    docs_url="/docs" if config.debug else None,
    redoc_url="/redoc" if config.debug else None
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.debug else [config.base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    StarletteSessionMiddleware,
    secret_key=config.secret_key,
    max_age=86400  # 24 hours
)

# OAuth setup
oauth = OAuth()

oauth.register(
    name='github',
    client_id=config.github_client_id,
    client_secret=config.github_client_secret,
    server_metadata_url='https://api.github.com/.well-known/oauth_authorization_server',
    client_kwargs={
        'scope': 'repo user:email'
    }
)

oauth.register(
    name='linear',
    client_id=config.linear_client_id,
    client_secret=config.linear_client_secret,
    authorize_url='https://linear.app/oauth/authorize',
    access_token_url='https://api.linear.app/oauth/token',
    client_kwargs={
        'scope': 'read write'
    }
)

oauth.register(
    name='slack',
    client_id=config.slack_client_id,
    client_secret=config.slack_client_secret,
    server_metadata_url='https://slack.com/.well-known/openid_connect_configuration',
    client_kwargs={
        'scope': 'openid profile email channels:read groups:read im:read mpim:read chat:write'
    }
)

# Templates
templates = Jinja2Templates(directory="src/contexten/dashboard/templates")

# Static files
app.mount("/static", StaticFiles(directory="src/contexten/dashboard/static"), name="static")

# Global state
integration_agents: Dict[str, Any] = {}
user_sessions: Dict[str, Dict[str, Any]] = {}
chat_manager = ChatManager()

# Security
security = HTTPBearer(auto_error=False)

async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current authenticated user from session"""
    session_id = request.session.get("session_id")
    if session_id and session_id in user_sessions:
        return user_sessions[session_id]
    return None

async def require_auth(request: Request) -> Dict[str, Any]:
    """Require authentication"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

# Routes

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Dashboard home page"""
    user = await get_current_user(request)
    
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "github_auth_url": "/auth/github",
            "linear_auth_url": "/auth/linear",
            "slack_auth_url": "/auth/slack"
        })
    
    # Get user's connected integrations
    integrations = {
        "github": user.get("github_token") is not None,
        "linear": user.get("linear_token") is not None,
        "slack": user.get("slack_token") is not None
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "integrations": integrations
    })

# Authentication Routes

@app.get("/auth/{provider}")
async def auth_login(provider: str, request: Request):
    """Initiate OAuth login"""
    if provider not in ["github", "linear", "slack"]:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    client = oauth.create_client(provider)
    redirect_uri = getattr(config, f"{provider}_redirect_uri")
    
    return await client.authorize_redirect(request, redirect_uri)

@app.get("/auth/{provider}/callback")
async def auth_callback(provider: str, request: Request):
    """Handle OAuth callback"""
    if provider not in ["github", "linear", "slack"]:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    try:
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)
        
        # Get user info
        if provider == "github":
            user_info = await get_github_user_info(token["access_token"])
        elif provider == "linear":
            user_info = await get_linear_user_info(token["access_token"])
        elif provider == "slack":
            user_info = await get_slack_user_info(token["access_token"])
        
        # Create or update session
        session_id = request.session.get("session_id")
        if not session_id:
            session_id = secrets.token_urlsafe(32)
            request.session["session_id"] = session_id
        
        if session_id not in user_sessions:
            user_sessions[session_id] = {}
        
        # Store user info and token
        user_sessions[session_id].update({
            f"{provider}_token": token["access_token"],
            f"{provider}_user": user_info,
            "last_login": datetime.utcnow().isoformat()
        })
        
        # Initialize integration agent
        await initialize_integration_agent(session_id, provider, token["access_token"])
        
        logger.info(f"User authenticated with {provider}: {user_info.get('login', user_info.get('name'))}")
        
        return RedirectResponse(url="/", status_code=302)
        
    except Exception as e:
        logger.error(f"OAuth callback error for {provider}: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.post("/auth/logout")
async def logout(request: Request):
    """Logout user"""
    session_id = request.session.get("session_id")
    if session_id and session_id in user_sessions:
        # Cleanup integration agents
        await cleanup_integration_agents(session_id)
        del user_sessions[session_id]
    
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

# Project Management Routes

@app.get("/api/projects")
async def get_projects(request: Request, user: Dict[str, Any] = Depends(require_auth)):
    """Get user's GitHub projects"""
    session_id = request.session.get("session_id")
    github_agent = integration_agents.get(f"{session_id}_github")
    
    if not github_agent:
        raise HTTPException(status_code=400, detail="GitHub integration not connected")
    
    try:
        projects = await github_agent.get_repositories()
        return {"projects": projects}
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to get projects")

@app.post("/api/projects/{project_id}/select")
async def select_project(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Select a project for management"""
    session_id = request.session.get("session_id")
    
    # Store selected project in session
    if session_id in user_sessions:
        user_sessions[session_id]["selected_project"] = project_id
    
    return {"status": "success", "project_id": project_id}

@app.post("/api/projects/{project_id}/pin")
async def pin_project(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Pin a project for persistent access"""
    session_id = request.session.get("session_id")
    
    if session_id in user_sessions:
        pinned_projects = user_sessions[session_id].get("pinned_projects", [])
        if project_id not in pinned_projects:
            pinned_projects.append(project_id)
            user_sessions[session_id]["pinned_projects"] = pinned_projects
    
    return {"status": "success", "project_id": project_id}

@app.delete("/api/projects/{project_id}/pin")
async def unpin_project(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Unpin a project"""
    session_id = request.session.get("session_id")
    
    if session_id in user_sessions:
        pinned_projects = user_sessions[session_id].get("pinned_projects", [])
        if project_id in pinned_projects:
            pinned_projects.remove(project_id)
            user_sessions[session_id]["pinned_projects"] = pinned_projects
    
    return {"status": "success", "project_id": project_id}

# Requirements Management Routes

@app.post("/api/requirements")
async def submit_requirements(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Submit project requirements"""
    try:
        data = await request.json()
        requirements = data.get("requirements", "")
        project_id = data.get("project_id")
        
        if not requirements or not project_id:
            raise HTTPException(status_code=400, detail="Requirements and project_id are required")
        
        session_id = request.session.get("session_id")
        
        # Store requirements in session
        if session_id in user_sessions:
            user_sessions[session_id]["requirements"] = {
                "text": requirements,
                "project_id": project_id,
                "submitted_at": datetime.utcnow().isoformat()
            }
        
        return {"status": "success", "message": "Requirements submitted successfully"}
        
    except Exception as e:
        logger.error(f"Error submitting requirements: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit requirements")

@app.post("/api/codegen/start")
async def start_codegen_task(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Start Codegen task with requirements"""
    try:
        session_id = request.session.get("session_id")
        user_data = user_sessions.get(session_id, {})
        
        requirements_data = user_data.get("requirements")
        if not requirements_data:
            raise HTTPException(status_code=400, detail="No requirements found")
        
        # Initialize Codegen agent
        if not config.codegen_org_id or not config.codegen_token:
            raise HTTPException(status_code=500, detail="Codegen SDK not configured")
        
        codegen_agent = CodegenAgent(
            org_id=config.codegen_org_id,
            token=config.codegen_token
        )
        
        # Create comprehensive prompt
        prompt = await create_codegen_prompt(requirements_data, user_data)
        
        # Start Codegen task
        task = codegen_agent.run(prompt=prompt)
        
        # Store task info
        user_sessions[session_id]["codegen_task"] = {
            "task_id": task.id if hasattr(task, 'id') else str(task),
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "prompt": prompt
        }
        
        # Create Linear issue if Linear is connected
        linear_agent = integration_agents.get(f"{session_id}_linear")
        if linear_agent:
            await create_linear_main_issue(linear_agent, requirements_data, task)
        
        logger.info(f"Started Codegen task for user {session_id}")
        
        return {
            "status": "success",
            "task_id": task.id if hasattr(task, 'id') else str(task),
            "message": "Codegen task started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error starting Codegen task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start Codegen task: {str(e)}")

@app.get("/api/codegen/status")
async def get_codegen_status(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get Codegen task status"""
    session_id = request.session.get("session_id")
    user_data = user_sessions.get(session_id, {})
    
    task_info = user_data.get("codegen_task")
    if not task_info:
        return {"status": "no_task"}
    
    # TODO: Implement actual task status checking with Codegen SDK
    # For now, return stored info
    return {"status": "success", "task": task_info}

@app.post("/api/codegen/stop")
async def stop_codegen_task(
    user: Dict[str, Any] = Depends(require_auth)
):
    """Stop Codegen task"""
    try:
        # Implementation would stop the actual Codegen task
        return {"status": "stopped", "message": "Codegen task stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping Codegen task: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop Codegen task")

# Chat API Endpoints

@app.post("/api/chat")
async def chat_message(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Process chat message"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        thread_id = data.get("thread_id")
        project_id = data.get("project_id")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get user tokens for agent creation
        user_tokens = {
            "github_token": user.get("github_token"),
            "linear_token": user.get("linear_token"),
            "slack_token": user.get("slack_token")
        }
        
        # Process the chat message
        result = await chat_manager.process_chat_message(
            message=message,
            thread_id=thread_id,
            project_id=project_id,
            user_tokens=user_tokens
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@app.get("/api/chat/history/{thread_id}")
async def get_chat_history(
    thread_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get chat history for a thread"""
    try:
        # Implementation would retrieve chat history
        return {"thread_id": thread_id, "messages": []}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

# Agent Management API Endpoints

@app.post("/api/agents/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Stop a monitoring agent"""
    try:
        success = await chat_manager.stop_agent(agent_id)
        if success:
            return {"status": "stopped", "agent_id": agent_id}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop agent")

@app.get("/api/agents")
async def list_active_agents(user: Dict[str, Any] = Depends(require_auth)):
    """List all active agents"""
    try:
        # Implementation would list active agents
        return {"agents": []}
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list agents")

# Monitoring API Endpoints

@app.get("/api/monitoring/status")
async def get_monitoring_status(user: Dict[str, Any] = Depends(require_auth)):
    """Get current monitoring status"""
    try:
        status = await chat_manager.get_monitoring_status()
        return status
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")

@app.get("/api/monitoring/activity")
async def get_recent_activity(
    limit: int = 50,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get recent activity across all integrations"""
    try:
        # Implementation would get recent activity
        return {"activities": [], "limit": limit}
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent activity")

# Integration Status Routes

@app.get("/api/integrations/status")
async def get_integration_status(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get status of all integrations"""
    session_id = request.session.get("session_id")
    
    status = {}
    for provider in ["github", "linear", "slack"]:
        agent = integration_agents.get(f"{session_id}_{provider}")
        if agent:
            status[provider] = await agent.health_check()
        else:
            status[provider] = {"status": "disconnected"}
    
    return {"integrations": status}

# Helper Functions

async def get_github_user_info(token: str) -> Dict[str, Any]:
    """Get GitHub user information"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()

async def get_linear_user_info(token: str) -> Dict[str, Any]:
    """Get Linear user information"""
    query = """
    query {
        viewer {
            id
            name
            displayName
            email
            avatarUrl
        }
    }
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.linear.app/graphql",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query}
        )
        response.raise_for_status()
        data = response.json()
        return data["data"]["viewer"]

async def get_slack_user_info(token: str) -> Dict[str, Any]:
    """Get Slack user information"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()

async def initialize_integration_agent(session_id: str, provider: str, token: str) -> None:
    """Initialize integration agent for user session"""
    try:
        if provider == "github":
            config = GitHubAgentConfig(token=token)
            agent = EnhancedGitHubAgent(config)
        elif provider == "linear":
            config = LinearAgentConfig(api_key=token)
            agent = EnhancedLinearAgent(config)
        elif provider == "slack":
            config = SlackAgentConfig(token=token)
            agent = EnhancedSlackAgent(config)
        else:
            return
        
        await agent.start()
        integration_agents[f"{session_id}_{provider}"] = agent
        
        logger.info(f"Initialized {provider} agent for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error initializing {provider} agent: {e}")

async def cleanup_integration_agents(session_id: str) -> None:
    """Cleanup integration agents for user session"""
    for provider in ["github", "linear", "slack"]:
        agent_key = f"{session_id}_{provider}"
        if agent_key in integration_agents:
            try:
                await integration_agents[agent_key].stop()
                del integration_agents[agent_key]
            except Exception as e:
                logger.error(f"Error cleaning up {provider} agent: {e}")

async def create_codegen_prompt(requirements_data: Dict[str, Any], user_data: Dict[str, Any]) -> str:
    """Create comprehensive prompt for Codegen"""
    project_id = requirements_data.get("project_id")
    requirements = requirements_data.get("text")
    
    prompt_template = f"""
# Codegen Task: Project Implementation

## Project Information
- **Project ID**: {project_id}
- **Requirements**: {requirements}

## Task Instructions
Please analyze the requirements and create a comprehensive implementation plan with the following:

1. **Step-by-step breakdown** of the implementation
2. **Create a main Linear issue** with comprehensive instructions
3. **Create sub-issues** for each feature implementation
4. **Provide detailed technical specifications** for each component
5. **Include testing and documentation requirements**

## Integration Context
- GitHub integration is available for repository management
- Linear integration is available for issue tracking
- Slack integration is available for notifications

## Expected Deliverables
1. Main Linear issue with project overview and requirements
2. Sub-issues for each major component and feature implementation
3. Technical documentation and implementation guidelines
4. Testing strategy and acceptance criteria

Please proceed with creating the Linear issues and implementation plan.
"""
    
    return prompt_template

async def create_linear_main_issue(
    linear_agent: EnhancedLinearAgent,
    requirements_data: Dict[str, Any],
    codegen_task: Any
) -> None:
    """Create main Linear issue for the project"""
    try:
        title = f"🤖 Codegen Project: {requirements_data.get('project_id', 'Unknown Project')}"
        
        description = f"""
# Project Implementation Request

## Requirements
{requirements_data.get('text', 'No requirements specified')}

## Codegen Task Information
- **Task ID**: {getattr(codegen_task, 'id', 'Unknown')}
- **Started**: {datetime.utcnow().isoformat()}
- **Status**: In Progress

## Implementation Plan
This issue will be updated with detailed implementation steps and sub-issues as the Codegen agent analyzes the requirements.

## Sub-Issues
Sub-issues will be created for each major component and feature implementation.

---
*This issue was automatically created by the Contexten Management Dashboard*
"""
        
        issue = await linear_agent.create_issue(
            title=title,
            description=description,
            priority=2  # High priority
        )
        
        logger.info(f"Created main Linear issue: {issue.id}")
        
    except Exception as e:
        logger.error(f"Error creating Linear main issue: {e}")

# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Contexten Management Dashboard starting up...")
    
    try:
        # Initialize orchestrator integration
        await orchestrator_integration.start()
        
        # Initialize enhanced monitoring
        await initialize_monitoring()
        
        # Initialize other components
        await chat_manager.initialize()
        
        logger.info("Dashboard startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Contexten Management Dashboard shutting down...")
    
    try:
        # Shutdown enhanced monitoring
        if enhanced_monitoring:
            await enhanced_monitoring.shutdown()
        
        # Shutdown orchestrator integration
        await orchestrator_integration.stop()
        
        # Cleanup other components
        await chat_manager.cleanup()
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    
    logger.info("Dashboard shutdown complete")

# Real-time monitoring

quality_monitor = None
real_time_analyzer = None
alert_system = None
dashboard_monitor = None
continuous_monitor = None

# Enhanced monitoring integration
enhanced_monitoring = None

async def initialize_monitoring():
    """Initialize the real-time monitoring system"""
    global quality_monitor, real_time_analyzer, alert_system, dashboard_monitor, continuous_monitor, enhanced_monitoring
    global autonomous_dependency_manager, autonomous_failure_analyzer
    
    if not config.monitoring_enabled:
        logger.info("Real-time monitoring is disabled")
        return
    
    try:
        # Initialize enhanced monitoring integration
        enhanced_monitoring = EnhancedDashboardMonitoring(codebase_path=".")
        
        # Initialize autonomous systems
        autonomous_dependency_manager = AutonomousDependencyManager(
            codegen_org_id=config.codegen_org_id,
            codegen_token=config.codegen_token,
            project_path="."
        )
        
        autonomous_failure_analyzer = AutonomousFailureAnalyzer(
            codegen_org_id=config.codegen_org_id,
            codegen_token=config.codegen_token
        )
        
        # Initialize the monitoring system
        success = await enhanced_monitoring.initialize()
        
        if success:
            logger.info("Enhanced dashboard monitoring initialized successfully")
        else:
            logger.warning("Enhanced monitoring initialized with mock data")
        
        # Setup WebSocket callbacks
        enhanced_monitoring.add_metrics_callback(_on_metrics_websocket_update)
        enhanced_monitoring.add_alerts_callback(_on_alert_websocket_update)
        enhanced_monitoring.add_file_change_callback(_on_file_change_websocket_update)
        
        # Setup autonomous system callbacks
        autonomous_dependency_manager.add_update_callback(_on_dependency_update)
        autonomous_dependency_manager.add_vulnerability_callback(_on_security_vulnerability)
        
        autonomous_failure_analyzer.add_failure_callback(_on_failure_analysis)
        autonomous_failure_analyzer.add_fix_callback(_on_auto_fix_result)
        
        logger.info("Autonomous systems initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize enhanced monitoring: {e}")

async def _on_metrics_websocket_update(metrics):
    """Handle metrics update for WebSocket broadcast"""
    # This would broadcast to connected WebSocket clients
    # Implementation would depend on WebSocket connection management
    pass

async def _on_alert_websocket_update(alert):
    """Handle alert update for WebSocket broadcast"""
    # This would broadcast to connected WebSocket clients
    pass

async def _on_file_change_websocket_update(change):
    """Handle file change update for WebSocket broadcast"""
    # This would broadcast to connected WebSocket clients
    pass

async def _on_dependency_update(analysis_result):
    """Handle dependency analysis update for WebSocket broadcast"""
    # This would broadcast dependency updates to connected WebSocket clients
    logger.info(f"Dependency analysis update: {analysis_result.outdated_dependencies} updates available")

async def _on_security_vulnerability(vulnerabilities):
    """Handle security vulnerability detection for WebSocket broadcast"""
    # This would broadcast security alerts to connected WebSocket clients
    logger.warning(f"Security vulnerabilities detected: {len(vulnerabilities)} critical issues")

async def _on_failure_analysis(analysis):
    """Handle failure analysis result for WebSocket broadcast"""
    # This would broadcast failure analysis to connected WebSocket clients
    logger.info(f"Failure analysis complete: {analysis.failure_type} (confidence: {analysis.confidence_score})")

async def _on_auto_fix_result(fix_result):
    """Handle auto-fix result for WebSocket broadcast"""
    # This would broadcast auto-fix results to connected WebSocket clients
    status = "successful" if fix_result.success else "failed"
    logger.info(f"Auto-fix {status}: {fix_result.fix_strategy}")

@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        # Get data from orchestrator integration
        orchestrator_data = await orchestrator_integration.get_system_dashboard_data()
        
        # Get enhanced monitoring data
        monitoring_data = {}
        if enhanced_monitoring:
            current_metrics = enhanced_monitoring.get_current_metrics()
            if current_metrics:
                monitoring_data = {
                    "health_score": current_metrics.health_score,
                    "technical_debt_score": current_metrics.technical_debt_score,
                    "complexity_score": current_metrics.complexity_score,
                    "maintainability_score": current_metrics.maintainability_score,
                    "documentation_coverage": current_metrics.documentation_coverage,
                    "test_coverage": current_metrics.test_coverage,
                    "security_score": current_metrics.security_score,
                    "performance_score": current_metrics.performance_score,
                    "total_files": current_metrics.total_files,
                    "total_functions": current_metrics.total_functions,
                    "total_classes": current_metrics.total_classes,
                    "dead_code_count": current_metrics.dead_code_count,
                    "circular_dependencies_count": current_metrics.circular_dependencies_count,
                    "security_issues_count": current_metrics.security_issues_count,
                    "health_trend": current_metrics.health_trend,
                    "quality_change_24h": current_metrics.quality_change_24h,
                    "last_analysis": current_metrics.last_analysis.isoformat(),
                    "last_updated": current_metrics.last_updated.isoformat()
                }
        
        # Get recent alerts from enhanced monitoring
        alerts = []
        if enhanced_monitoring:
            alerts = enhanced_monitoring.get_recent_alerts(limit=10)
        
        # Combine all data
        dashboard_data = {
            **orchestrator_data,
            **monitoring_data,
            "alerts": alerts,
            "monitoring_enabled": config.monitoring_enabled,
            "last_updated": datetime.now().isoformat()
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        return {"error": "Failed to load dashboard data"}

@app.get("/api/dashboard/section/{section_id}")
async def get_section_data(section_id: str):
    """Get data for a specific dashboard section"""
    try:
        if section_id == "code-quality":
            return await get_code_quality_data()
        elif section_id == "architecture":
            return await get_architecture_data()
        elif section_id == "dependencies":
            return await get_dependencies_data()
        elif section_id == "security":
            return await get_security_data()
        elif section_id == "performance":
            return await get_performance_data()
        elif section_id == "real-time":
            return await get_real_time_data()
        elif section_id == "alerts":
            return await get_alerts_data()
        else:
            return {"error": "Unknown section"}
            
    except Exception as e:
        logger.error(f"Failed to get {section_id} data: {e}")
        return {"error": f"Failed to load {section_id} data"}

async def get_code_quality_data():
    """Get comprehensive code quality analysis data"""
    if enhanced_monitoring:
        # Get data from enhanced monitoring
        code_issues = enhanced_monitoring.get_code_issues()
        file_quality = enhanced_monitoring.get_file_quality_info()
        current_metrics = enhanced_monitoring.get_current_metrics()
        
        data = {
            "metrics": {
                "health": current_metrics.health_score if current_metrics else 0.85,
                "maintainability": current_metrics.maintainability_score if current_metrics else 0.75,
                "complexity": current_metrics.complexity_score if current_metrics else 0.65,
                "documentation": current_metrics.documentation_coverage if current_metrics else 0.70,
                "test_coverage": current_metrics.test_coverage if current_metrics else 0.78,
                "security": current_metrics.security_score if current_metrics else 0.82
            },
            "issues": [
                {
                    "title": issue.title,
                    "description": issue.description,
                    "severity": issue.severity,
                    "file": issue.file_path,
                    "line": issue.line_number
                }
                for issue in code_issues[:10]  # Limit to 10 most recent
            ],
            "file_quality": [
                {
                    "path": info.path,
                    "quality_score": info.quality_score,
                    "complexity": "High" if info.complexity_score > 0.7 else "Medium" if info.complexity_score > 0.4 else "Low",
                    "maintainability": "High" if info.maintainability_score > 0.7 else "Medium" if info.maintainability_score > 0.4 else "Low",
                    "issues": info.issues_count
                }
                for info in file_quality[:20]  # Limit to 20 files
            ]
        }
        
        return data
    
    # Fallback to mock data
    data = {
        "metrics": {
            "health": 0.85,
            "maintainability": 0.75,
            "complexity": 0.65,
            "documentation": 0.70,
            "test_coverage": 0.78,
            "security": 0.82
        },
        "issues": [
            {
                "title": "High complexity function detected",
                "description": "Function 'process_data' has cyclomatic complexity of 15",
                "severity": "high",
                "file": "src/data_processor.py",
                "line": 45
            },
            {
                "title": "Missing documentation",
                "description": "Class 'DataAnalyzer' lacks docstring",
                "severity": "medium",
                "file": "src/analyzer.py",
                "line": 12
            }
        ],
        "file_quality": [
            {
                "path": "src/main.py",
                "quality_score": 0.92,
                "complexity": "Low",
                "maintainability": "High",
                "issues": 1
            },
            {
                "path": "src/data_processor.py",
                "quality_score": 0.65,
                "complexity": "High",
                "maintainability": "Medium",
                "issues": 3
            }
        ]
    }
    
    return data

async def get_architecture_data():
    """Get architecture analysis data"""
    if enhanced_monitoring:
        return {
            "dependency_graph": {
                "nodes": [
                    {"id": "main", "group": "core"},
                    {"id": "processor", "group": "core"},
                    {"id": "analyzer", "group": "analysis"},
                    {"id": "utils", "group": "utility"}
                ],
                "links": [
                    {"source": "main", "target": "processor"},
                    {"source": "main", "target": "analyzer"},
                    {"source": "processor", "target": "utils"},
                    {"source": "analyzer", "target": "utils"}
                ]
            },
            "metrics": enhanced_monitoring.get_architecture_metrics()
        }
    
    # Fallback to mock data
    return {
        "dependency_graph": {
            "nodes": [
                {"id": "main", "group": "core"},
                {"id": "processor", "group": "core"},
                {"id": "analyzer", "group": "analysis"},
                {"id": "utils", "group": "utility"}
            ],
            "links": [
                {"source": "main", "target": "processor"},
                {"source": "main", "target": "analyzer"},
                {"source": "processor", "target": "utils"},
                {"source": "analyzer", "target": "utils"}
            ]
        },
        "metrics": {
            "modules": 15,
            "coupling": 0.45,
            "cohesion": 0.78,
            "depth": 4,
            "fan_in": 3.2,
            "fan_out": 2.8
        }
    }

async def get_dependencies_data():
    """Get dependency analysis data"""
    if enhanced_monitoring:
        arch_metrics = enhanced_monitoring.get_architecture_metrics()
        return {
            "circular_dependencies": arch_metrics.get("circular_dependencies", []),
            "dependency_health": {
                "healthy": 70,
                "warning": 20,
                "critical": 10
            },
            "outdated_dependencies": [
                {"name": "requests", "current": "2.25.1", "latest": "2.31.0"},
                {"name": "numpy", "current": "1.20.0", "latest": "1.24.3"}
            ]
        }
    
    # Fallback to mock data
    return {
        "circular_dependencies": [
            {
                "cycle": ["module_a", "module_b", "module_c", "module_a"]
            }
        ],
        "dependency_health": {
            "healthy": 70,
            "warning": 20,
            "critical": 10
        },
        "outdated_dependencies": [
            {"name": "requests", "current": "2.25.1", "latest": "2.31.0"},
            {"name": "numpy", "current": "1.20.0", "latest": "1.24.3"}
        ]
    }

async def get_security_data():
    """Get security analysis data"""
    if enhanced_monitoring:
        return enhanced_monitoring.get_security_analysis()
    
    # Fallback to mock data
    return {
        "security_issues": [
            {
                "title": "SQL Injection vulnerability",
                "description": "Potential SQL injection in user input handling",
                "severity": "critical",
                "category": "injection",
                "file": "src/database.py",
                "line": 78
            },
            {
                "title": "Hardcoded credentials",
                "description": "API key found in source code",
                "severity": "high",
                "category": "credentials",
                "file": "src/config.py",
                "line": 15
            }
        ],
        "security_score": {
            "authentication": 0.9,
            "authorization": 0.8,
            "data_protection": 0.85,
            "input_validation": 0.75,
            "error_handling": 0.88
        }
    }

async def get_performance_data():
    """Get performance analysis data"""
    if enhanced_monitoring:
        return enhanced_monitoring.get_performance_analysis()
    
    # Fallback to mock data
    return {
        "metrics": {
            "response_times": [120, 135, 98, 156, 142, 118, 167],
            "memory_usage": [45, 52, 48, 61, 58, 44, 67],
            "timestamps": ["10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30"]
        },
        "bottlenecks": [
            {
                "function": "heavy_computation",
                "file": "src/processor.py",
                "line": 234,
                "impact": "High",
                "avg_time": "2.3s"
            },
            {
                "function": "database_query",
                "file": "src/database.py",
                "line": 156,
                "impact": "Medium",
                "avg_time": "0.8s"
            }
        ]
    }

async def get_real_time_data():
    """Get real-time monitoring data"""
    data = {
        "live_metrics": [],
        "file_changes": []
    }
    
    if real_time_analyzer:
        # Get recent file changes
        data["file_changes"] = [
            {
                "file": "src/main.py",
                "type": "modified",
                "timestamp": datetime.now().isoformat()
            },
            {
                "file": "src/new_feature.py",
                "type": "added",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat()
            }
        ]
    
    if quality_monitor:
        # Get recent quality metrics for live chart
        trends = quality_monitor.get_quality_trends(hours=1)
        if trends:
            data["live_metrics"] = [
                {
                    "timestamp": trend.timestamp.isoformat(),
                    "health_score": trend.health_score
                }
                for trend in trends[-20:]  # Last 20 data points
            ]
    
    return data

async def get_alerts_data():
    """Get alerts data"""
    alerts = []
    
    if alert_system:
        alerts = alert_system.get_all_alerts()
    else:
        # Mock data for demonstration
        alerts = [
            {
                "id": "alert_1",
                "severity": "critical",
                "type": "quality",
                "message": "Health score dropped below 60%",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "alert_2",
                "severity": "warning",
                "type": "security",
                "message": "New security vulnerability detected",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
            }
        ]
    
    return {"alerts": alerts}

@app.post("/api/dashboard/export")
async def export_dashboard_report(request: Request):
    """Export comprehensive dashboard report"""
    try:
        body = await request.json()
        format_type = body.get("format", "pdf")
        sections = body.get("sections", ["overview"])
        
        # Generate report data
        report_data = {}
        for section in sections:
            if section == "overview":
                report_data[section] = await get_dashboard_data()
            else:
                report_data[section] = await get_section_data(section)
        
        # For now, return JSON data
        # In a real implementation, you would generate PDF/Excel files
        if format_type == "json":
            return report_data
        else:
            # Mock PDF generation
            from io import BytesIO
            import json
            
            pdf_content = json.dumps(report_data, indent=2).encode()
            
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=dashboard-report.pdf"}
            )
            
    except Exception as e:
        logger.error(f"Failed to export report: {e}")
        return {"error": "Failed to export report"}

# WebSocket endpoint for real-time updates
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "payload": {"status": "connected", "timestamp": datetime.now().isoformat()}
        })
        
        # Keep connection alive and send periodic updates
        while True:
            # Send quality metrics update
            if quality_monitor:
                current_metrics = quality_monitor.get_current_metrics()
                if current_metrics:
                    await websocket.send_json({
                        "type": "quality_metrics",
                        "payload": {
                            "health_score": current_metrics.health_score,
                            "technical_debt_score": current_metrics.technical_debt_score,
                            "complexity_score": current_metrics.complexity_score,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
            
            # Wait before next update
            await asyncio.sleep(30)  # Send updates every 30 seconds
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# Autonomous Systems API Endpoints

@app.get("/api/autonomous/dependencies")
async def get_dependency_analysis(
    request: Request,
    force_scan: bool = False,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get dependency analysis results"""
    try:
        if autonomous_dependency_manager:
            if force_scan:
                result = await autonomous_dependency_manager.analyze_dependencies(force_scan=True)
            else:
                result = autonomous_dependency_manager.get_last_scan_result()
                if not result:
                    result = await autonomous_dependency_manager.analyze_dependencies()
            
            return await autonomous_dependency_manager.get_dashboard_data()
        else:
            return {"error": "Autonomous dependency manager not available"}
    except Exception as e:
        logger.error(f"Failed to get dependency analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/autonomous/dependencies/scan")
async def trigger_dependency_scan(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Trigger a new dependency scan"""
    try:
        if autonomous_dependency_manager:
            result = await autonomous_dependency_manager.analyze_dependencies(force_scan=True)
            return {
                "message": "Dependency scan completed",
                "summary": {
                    "total_dependencies": result.total_dependencies,
                    "outdated_dependencies": result.outdated_dependencies,
                    "security_vulnerabilities": result.security_vulnerabilities
                }
            }
        else:
            raise HTTPException(status_code=503, detail="Autonomous dependency manager not available")
    except Exception as e:
        logger.error(f"Failed to trigger dependency scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/autonomous/dependencies/update")
async def apply_dependency_updates(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Apply selected dependency updates"""
    try:
        body = await request.json()
        update_names = body.get("updates", [])
        strategy = body.get("strategy", "smart")
        
        if autonomous_dependency_manager:
            result = await autonomous_dependency_manager.apply_updates(update_names, strategy)
            return result
        else:
            raise HTTPException(status_code=503, detail="Autonomous dependency manager not available")
    except Exception as e:
        logger.error(f"Failed to apply dependency updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/autonomous/failures")
async def get_failure_analysis(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get failure analysis results"""
    try:
        if autonomous_failure_analyzer:
            return autonomous_failure_analyzer.get_dashboard_data()
        else:
            return {"error": "Autonomous failure analyzer not available"}
    except Exception as e:
        logger.error(f"Failed to get failure analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/autonomous/failures/analyze")
async def analyze_workflow_failure(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Analyze a specific workflow failure"""
    try:
        body = await request.json()
        workflow_run_id = body.get("workflow_run_id")
        failure_logs = body.get("failure_logs", "")
        context = body.get("context", {})
        
        if not workflow_run_id:
            raise HTTPException(status_code=400, detail="workflow_run_id is required")
        
        if autonomous_failure_analyzer:
            analysis = await autonomous_failure_analyzer.analyze_failure(
                workflow_run_id=workflow_run_id,
                failure_logs=failure_logs,
                context=context
            )
            
            return {
                "analysis": {
                    "id": analysis.id,
                    "workflow_run_id": analysis.workflow_run_id,
                    "failure_type": analysis.failure_type,
                    "root_cause": analysis.root_cause,
                    "suggested_fix": analysis.suggested_fix,
                    "confidence_score": analysis.confidence_score,
                    "auto_fixable": analysis.auto_fixable,
                    "affected_files": analysis.affected_files,
                    "estimated_fix_time": analysis.estimated_fix_time
                }
            }
        else:
            raise HTTPException(status_code=503, detail="Autonomous failure analyzer not available")
    except Exception as e:
        logger.error(f"Failed to analyze workflow failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/autonomous/failures/autofix")
async def attempt_auto_fix(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Attempt to automatically fix a failure"""
    try:
        body = await request.json()
        analysis_id = body.get("analysis_id")
        
        if not analysis_id:
            raise HTTPException(status_code=400, detail="analysis_id is required")
        
        if autonomous_failure_analyzer:
            # Find the analysis
            analysis = None
            for failure in autonomous_failure_analyzer.get_recent_failures(100):
                if failure.id == analysis_id:
                    analysis = failure
                    break
            
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            fix_result = await autonomous_failure_analyzer.attempt_auto_fix(analysis)
            
            if fix_result:
                return {
                    "fix_result": {
                        "fix_id": fix_result.fix_id,
                        "success": fix_result.success,
                        "fix_strategy": fix_result.fix_strategy,
                        "changes_made": fix_result.changes_made,
                        "pr_created": fix_result.pr_created,
                        "execution_time": fix_result.execution_time,
                        "error_message": fix_result.error_message
                    }
                }
            else:
                return {"message": "Auto-fix not attempted (conditions not met)"}
        else:
            raise HTTPException(status_code=503, detail="Autonomous failure analyzer not available")
    except Exception as e:
        logger.error(f"Failed to attempt auto-fix: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/autonomous/status")
async def get_autonomous_systems_status(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get status of all autonomous systems"""
    try:
        status = {
            "dependency_manager": {
                "available": autonomous_dependency_manager is not None,
                "status": autonomous_dependency_manager.get_scan_status() if autonomous_dependency_manager else None
            },
            "failure_analyzer": {
                "available": autonomous_failure_analyzer is not None,
                "statistics": autonomous_failure_analyzer.get_failure_statistics() if autonomous_failure_analyzer else None
            },
            "enhanced_monitoring": {
                "available": enhanced_monitoring is not None,
                "running": enhanced_monitoring.is_running if enhanced_monitoring else False
            }
        }
        
        return status
    except Exception as e:
        logger.error(f"Failed to get autonomous systems status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="debug" if config.debug else "info"
    )
