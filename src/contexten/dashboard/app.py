"""
Contexten Management Dashboard

A comprehensive web interface for managing GitHub/Linear integrations with OAuth
authentication and Codegen SDK integration.
"""

import asyncio
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import secrets
import hashlib

from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.sessions import SessionMiddleware

import httpx
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware as StarletteSessionMiddleware

# Import Codegen SDK
from codegen import Agent as CodegenAgent

# Import contexten components
from ..extensions.linear.enhanced_agent import EnhancedLinearAgent, LinearAgentConfig
from ..extensions.github.enhanced_agent import EnhancedGitHubAgent, GitHubAgentConfig
from ..extensions.slack.enhanced_agent import EnhancedSlackAgent, SlackAgentConfig
from ...shared.logging.get_logger import get_logger

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
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Stop Codegen task"""
    session_id = request.session.get("session_id")
    user_data = user_sessions.get(session_id, {})
    
    task_info = user_data.get("codegen_task")
    if not task_info:
        raise HTTPException(status_code=400, detail="No active task found")
    
    # TODO: Implement actual task stopping with Codegen SDK
    
    # Update task status
    user_sessions[session_id]["codegen_task"]["status"] = "stopped"
    user_sessions[session_id]["codegen_task"]["stopped_at"] = datetime.utcnow().isoformat()
    
    return {"status": "success", "message": "Codegen task stopped"}

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
2. Sub-issues for each major feature/component
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
    """Application startup"""
    logger.info("Contexten Management Dashboard starting up...")
    
    # Validate configuration
    missing_config = []
    if not config.codegen_org_id:
        missing_config.append("CODEGEN_ORG_ID")
    if not config.codegen_token:
        missing_config.append("CODEGEN_TOKEN")
    
    if missing_config:
        logger.warning(f"Missing configuration: {', '.join(missing_config)}")
    
    logger.info("Dashboard startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Contexten Management Dashboard shutting down...")
    
    # Cleanup all integration agents
    for agent in integration_agents.values():
        try:
            await agent.stop()
        except Exception as e:
            logger.error(f"Error stopping agent during shutdown: {e}")
    
    integration_agents.clear()
    user_sessions.clear()
    
    logger.info("Dashboard shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="debug" if config.debug else "info"
    )

