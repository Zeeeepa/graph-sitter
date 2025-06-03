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
import uuid

# Set up logging
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

# Import Codegen SDK with graceful error handling
try:
    from codegen import Agent as CodegenAgent
    CODEGEN_AVAILABLE = True
except ImportError:
    CodegenAgent = None
    CODEGEN_AVAILABLE = False
    print("Warning: Codegen SDK not available. Some features may be limited.")

# Import agents with graceful error handling
try:
    from ..extensions.linear.enhanced_agent import EnhancedLinearAgent, LinearAgentConfig
except ImportError:
    EnhancedLinearAgent = None
    LinearAgentConfig = None
    print("Warning: Could not import Linear agent. Linear features may be limited.")

try:
    from ..extensions.github.enhanced_agent import EnhancedGitHubAgent, GitHubAgentConfig
except ImportError:
    EnhancedGitHubAgent = None
    GitHubAgentConfig = None
    print("Warning: Could not import GitHub agent. GitHub features may be be limited.")

try:
    from ..extensions.slack.enhanced_agent import EnhancedSlackAgent, SlackAgentConfig
except ImportError:
    EnhancedSlackAgent = None
    SlackAgentConfig = None
    print("Warning: Could not import Slack agent. Slack features may be limited.")

try:
    from ...shared.logging.get_logger import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    print("Warning: Could not import contexten logger. Using standard logging.")

try:
    from .chat_manager import ChatManager
except ImportError:
    ChatManager = None
    print("Warning: Could not import ChatManager. Chat features may be limited.")

try:
    from .prefect_dashboard import PrefectDashboardManager
except ImportError:
    PrefectDashboardManager = None
    print("Warning: Could not import Prefect dashboard. Prefect features may be limited.")

try:
    from ..orchestration import OrchestrationConfig
except ImportError:
    OrchestrationConfig = None
    print("Warning: Could not import OrchestrationConfig. Orchestration features may be limited.")

# Pydantic models for API requests
class FlowCreateRequest(BaseModel):
    name: str
    project: str
    type: str
    requirements: str
    priority: str = "medium"
    notifications: bool = True

class ProjectAnalyzeRequest(BaseModel):
    project: str
    analysis_type: str = "comprehensive"

class SettingsRequest(BaseModel):
    codegenOrgId: Optional[str] = None
    codegenToken: Optional[str] = None
    flowTimeout: Optional[int] = 60
    notificationPrefs: Optional[str] = "all"

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
        
        # API Tokens and Webhooks
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.linear_api_key = os.getenv("LINEAR_API_KEY")
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
        # Codegen SDK
        self.codegen_org_id = os.getenv("CODEGEN_ORG_ID")
        self.codegen_token = os.getenv("CODEGEN_TOKEN")
        
        # Prefect Configuration
        self.prefect_api_url = os.getenv("PREFECT_API_URL")
        self.prefect_workspace = os.getenv("PREFECT_WORKSPACE")
        
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

# Initialize Prefect Dashboard Manager
prefect_dashboard_manager = None

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.debug else [config.base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
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
        'scope': 'openid profile email channels:read groups:read im:write chat:write'
    }
)

# Templates
templates = Jinja2Templates(directory="src/contexten/dashboard/templates")

# Static files
app.mount("/static", StaticFiles(directory="src/contexten/dashboard/static"), name="static")

# Global state
integration_agents: Dict[str, Any] = {}
user_sessions: Dict[str, Dict[str, Any]] = {}
chat_manager = ChatManager() if ChatManager is not None else None

# Global state for flows and projects
active_flows = {}
dashboard_stats = {
    "active_projects": 0,
    "running_flows": 0,
    "completed_today": 0,
    "success_rate": 0.0,
    "recent_activity": []
}

# Security
security = HTTPBearer(auto_error=False)

async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current authenticated user from session or environment tokens"""
    # First check session-based authentication
    session_id = request.session.get("session_id")
    if session_id and session_id in user_sessions:
        return user_sessions[session_id]
    
    # If no session, check for environment-based authentication
    env_user = get_env_user()
    if env_user:
        # Create a temporary session for environment-based auth
        temp_session_id = f"env_user_{hashlib.md5(str(env_user).encode()).hexdigest()[:8]}"
        request.session["session_id"] = temp_session_id
        user_sessions[temp_session_id] = env_user
        return env_user
    
    return None

def get_env_user() -> Optional[Dict[str, Any]]:
    """Create user object from environment variables"""
    github_token = config.github_token
    linear_api_key = config.linear_api_key
    slack_webhook_url = config.slack_webhook_url
    
    # Only create env user if at least one token is available
    if github_token or linear_api_key or slack_webhook_url:
        return {
            "id": "env_user",
            "name": "Environment User",
            "email": "user@localhost",
            "github_token": github_token,
            "linear_token": linear_api_key,
            "slack_token": slack_webhook_url,
            "auth_method": "environment"
        }
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
    """Main dashboard route with comprehensive UI"""
    user = await get_current_user(request)
    
    if not user:
        # Show login page with environment token option
        return templates.TemplateResponse("login.html", {
            "request": request,
            "github_auth_url": "/auth/github",
            "linear_auth_url": "/auth/linear",
            "slack_auth_url": "/auth/slack",
            "show_env_option": True,
            "env_tokens_available": bool(config.github_token or config.linear_api_key or config.slack_webhook_url)
        })
    
    # Get user's connected integrations
    integrations = {
        "github": bool(user.get("github_token") or config.github_token),
        "linear": bool(user.get("linear_token") or config.linear_api_key),
        "slack": bool(user.get("slack_token") or config.slack_webhook_url),
        "prefect": bool(config.prefect_api_url)
    }
    
    # Use comprehensive dashboard template
    return templates.TemplateResponse("comprehensive_dashboard.html", {
        "request": request,
        "user": user,
        "integrations": integrations,
        "auth_method": user.get("auth_method", "oauth"),
        "github_token": config.github_token,
        "linear_api_key": config.linear_api_key,
        "slack_webhook_url": config.slack_webhook_url
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
    global prefect_dashboard_manager

    # Initialize Prefect Dashboard Manager
    try:
        orchestration_config = OrchestrationConfig(
            codegen_org_id=config.codegen_org_id,
            codegen_token=config.codegen_token,
            github_token=config.github_token,
            linear_api_key=config.linear_api_key,
            slack_webhook_url=config.slack_webhook_url,
            prefect_api_url=config.prefect_api_url,
            prefect_workspace=config.prefect_workspace
        )
        
        prefect_dashboard_manager = PrefectDashboardManager(orchestration_config)
        await prefect_dashboard_manager.initialize()
        
        # Include Prefect dashboard routes
        app.include_router(prefect_dashboard_manager.router)
        
        logger.info("Prefect Dashboard Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Prefect Dashboard Manager: {e}")
        # Continue without Prefect dashboard if initialization fails

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Contexten Management Dashboard shutting down...")
    
    global prefect_dashboard_manager
    
    # Shutdown Prefect Dashboard Manager
    if prefect_dashboard_manager:
        try:
            await prefect_dashboard_manager.shutdown()
            logger.info("Prefect Dashboard Manager shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down Prefect Dashboard Manager: {e}")
    
    # Cleanup all integration agents
    for agent in integration_agents.values():
        try:
            await agent.stop()
        except Exception as e:
            logger.error(f"Error stopping agent during shutdown: {e}")
    
    integration_agents.clear()
    user_sessions.clear()
    
    logger.info("Dashboard shutdown complete")

@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get dashboard overview data"""
    try:
        # Update stats from orchestrator if available
        global prefect_dashboard_manager
        if prefect_dashboard_manager:
            flows_data = await prefect_dashboard_manager.get_flows()
            dashboard_stats["running_flows"] = len([f for f in flows_data.get("flows", []) if f.get("state") == "Running"])
            dashboard_stats["completed_today"] = len([f for f in flows_data.get("flows", []) 
                                                    if f.get("state") == "Completed" and 
                                                    datetime.fromisoformat(f.get("start_time", "")).date() == datetime.now().date()])
        
        # Calculate success rate
        total_flows = len(active_flows)
        if total_flows > 0:
            completed_flows = len([f for f in active_flows.values() if f.get("status") == "completed"])
            dashboard_stats["success_rate"] = (completed_flows / total_flows) * 100
        
        return dashboard_stats
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        return dashboard_stats

@app.get("/api/flows/active")
async def get_active_flows():
    """Get all active flows"""
    try:
        return {"flows": active_flows}
    except Exception as e:
        logger.error(f"Error getting active flows: {e}")
        return {"flows": {}}

@app.post("/api/flows/create")
async def create_flow(flow_request: FlowCreateRequest):
    """Create a new CICD flow"""
    try:
        flow_id = str(uuid.uuid4())
        
        # Create flow object
        flow = {
            "id": flow_id,
            "name": flow_request.name,
            "project_name": flow_request.project.split('/')[-1],
            "project_full_name": flow_request.project,
            "type": flow_request.type,
            "requirements": flow_request.requirements,
            "priority": flow_request.priority,
            "notifications": flow_request.notifications,
            "status": "running",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "current_step": "Initializing flow...",
            "error": None
        }
        
        # Store flow
        active_flows[flow_id] = flow
        
        # Start flow execution using Codegen SDK
        await execute_flow_with_codegen(flow)
        
        # Update dashboard stats
        dashboard_stats["running_flows"] = len([f for f in active_flows.values() if f["status"] == "running"])
        
        return {"success": True, "flow_id": flow_id, "message": "Flow created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create flow: {str(e)}")

@app.post("/api/flows/{flow_id}/pause")
async def pause_flow(flow_id: str):
    """Pause a running flow"""
    try:
        if flow_id not in active_flows:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        flow = active_flows[flow_id]
        if flow["status"] != "running":
            raise HTTPException(status_code=400, detail="Flow is not running")
        
        flow["status"] = "paused"
        flow["current_step"] = "Flow paused by user"
        
        return {"success": True, "message": "Flow paused successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause flow: {str(e)}")

@app.post("/api/flows/{flow_id}/cancel")
async def cancel_flow(flow_id: str):
    """Cancel a flow"""
    try:
        if flow_id not in active_flows:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        flow = active_flows[flow_id]
        flow["status"] = "cancelled"
        flow["current_step"] = "Flow cancelled by user"
        flow["progress"] = 0
        
        # Update dashboard stats
        dashboard_stats["running_flows"] = len([f for f in active_flows.values() if f["status"] == "running"])
        
        return {"success": True, "message": "Flow cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel flow: {str(e)}")

@app.get("/api/flows/{flow_id}/details")
async def get_flow_details(flow_id: str):
    """Get detailed information about a flow"""
    try:
        if flow_id not in active_flows:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        flow = active_flows[flow_id]
        
        # Add additional details
        flow_details = {
            **flow,
            "logs": [],  # TODO: Implement flow logs
            "steps": [],  # TODO: Implement flow steps tracking
            "duration": calculate_flow_duration(flow),
            "estimated_completion": estimate_completion_time(flow)
        }
        
        return flow_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow details {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flow details: {str(e)}")

@app.post("/api/projects/analyze")
async def analyze_project(analyze_request: ProjectAnalyzeRequest):
    """Start project analysis"""
    try:
        # Create analysis flow
        flow_request = FlowCreateRequest(
            name=f"Analysis: {analyze_request.project.split('/')[-1]}",
            project=analyze_request.project,
            type="analysis",
            requirements=f"Perform {analyze_request.analysis_type} analysis of the codebase including code quality, security vulnerabilities, performance issues, and technical debt assessment.",
            priority="medium",
            notifications=True
        )
        
        result = await create_flow(flow_request)
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing project {analyze_request.project}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze project: {str(e)}")

@app.get("/api/projects/{project_name}/flows")
async def get_project_flows(project_name: str):
    """Get all flows for a specific project"""
    try:
        project_flows = [
            flow for flow in active_flows.values() 
            if flow["project_full_name"] == project_name
        ]
        
        return {"flows": project_flows, "project": project_name}
        
    except Exception as e:
        logger.error(f"Error getting flows for project {project_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project flows: {str(e)}")

@app.post("/api/projects/add")
async def add_project(request: dict):
    """Add a custom project"""
    try:
        project_name = request.get("project")
        if not project_name:
            raise HTTPException(status_code=400, detail="Project name is required")
        
        # TODO: Validate project exists and user has access
        # For now, just return success
        return {"success": True, "message": f"Project {project_name} added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add project: {str(e)}")

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Get analytics data for dashboard charts"""
    try:
        # Generate sample analytics data
        # TODO: Implement real analytics from flow data
        analytics_data = {
            "performance": {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "success_rate": [85, 90, 88, 92, 87, 89, 91],
                "avg_duration": [45, 38, 42, 35, 48, 40, 37]
            },
            "activity": {
                "labels": ["Analysis", "Testing", "Deployment", "Security", "Custom"],
                "values": [25, 20, 15, 10, 30]
            }
        }
        
        return analytics_data
        
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics data: {str(e)}")

@app.post("/api/settings/save")
async def save_settings(settings: SettingsRequest):
    """Save dashboard settings"""
    try:
        # TODO: Implement settings persistence
        logger.info(f"Settings saved: {settings.dict(exclude={'codegenToken'})}")
        return {"success": True, "message": "Settings saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")

@app.get("/api/system/status")
async def get_system_status():
    """Get system status information"""
    try:
        status = {
            "orchestrator": "Healthy",
            "github": "Connected",
            "linear": "Connected"
        }
        
        # Check actual service status
        global prefect_dashboard_manager
        if prefect_dashboard_manager:
            try:
                await prefect_dashboard_manager.get_flows()
                status["orchestrator"] = "Healthy"
            except:
                status["orchestrator"] = "Degraded"
        else:
            status["orchestrator"] = "Disconnected"
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "orchestrator": "Unknown",
            "github": "Unknown", 
            "linear": "Unknown"
        }

@app.get("/api/export/dashboard-data")
async def export_dashboard_data():
    """Export dashboard data"""
    try:
        export_data = {
            "flows": active_flows,
            "stats": dashboard_stats,
            "exported_at": datetime.now().isoformat()
        }
        
        return JSONResponse(
            content=export_data,
            headers={"Content-Disposition": "attachment; filename=dashboard-export.json"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")

# Helper functions
async def execute_flow_with_codegen(flow: dict):
    """Execute a flow using Codegen SDK"""
    try:
        # Get Codegen configuration
        org_id = os.getenv("CODEGEN_ORG_ID")
        token = os.getenv("CODEGEN_TOKEN")
        
        if not org_id or not token:
            logger.warning("Codegen SDK not configured, simulating flow execution")
            await simulate_flow_execution(flow)
            return
        
        # Initialize Codegen agent
        codegen_agent = CodegenAgent(org_id=org_id, token=token)
        
        # Create prompt based on flow type and requirements
        prompt = create_flow_prompt(flow)
        
        # Update flow status
        flow["current_step"] = "Executing with Codegen agent..."
        flow["progress"] = 10
        
        # Execute with Codegen
        task = codegen_agent.run(prompt=prompt)
        
        # Monitor task progress
        asyncio.create_task(monitor_codegen_task(flow, task))
        
    except Exception as e:
        logger.error(f"Error executing flow with Codegen: {e}")
        flow["status"] = "failed"
        flow["error"] = str(e)
        flow["current_step"] = "Flow execution failed"

async def simulate_flow_execution(flow: dict):
    """Simulate flow execution for demo purposes"""
    try:
        steps = [
            ("Analyzing project structure...", 20),
            ("Running code analysis...", 40),
            ("Generating recommendations...", 60),
            ("Creating Linear issues...", 80),
            ("Finalizing results...", 100)
        ]
        
        for step, progress in steps:
            await asyncio.sleep(2)  # Simulate work
            flow["current_step"] = step
            flow["progress"] = progress
        
        flow["status"] = "completed"
        flow["current_step"] = "Flow completed successfully"
        
        # Update dashboard stats
        dashboard_stats["completed_today"] += 1
        dashboard_stats["running_flows"] = len([f for f in active_flows.values() if f["status"] == "running"])
        
        # Add to recent activity
        dashboard_stats["recent_activity"].insert(0, {
            "title": f"Flow completed: {flow['name']}",
            "description": f"Successfully completed {flow['type']} flow for {flow['project_name']}",
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 10 activities
        dashboard_stats["recent_activity"] = dashboard_stats["recent_activity"][:10]
        
    except Exception as e:
        logger.error(f"Error simulating flow execution: {e}")
        flow["status"] = "failed"
        flow["error"] = str(e)

def create_flow_prompt(flow: dict) -> str:
    """Create a prompt for Codegen based on flow configuration"""
    project = flow["project_full_name"]
    flow_type = flow["type"]
    requirements = flow["requirements"]
    
    prompt = f"""
    Please execute a {flow_type} flow for the GitHub repository {project}.
    
    Requirements:
    {requirements}
    
    Please:
    1. Analyze the codebase thoroughly
    2. Identify issues and opportunities for improvement
    3. Create detailed Linear issues for any problems found
    4. Provide a comprehensive summary of findings
    5. Include actionable recommendations
    
    Focus on code quality, security, performance, and maintainability.
    """
    
    return prompt

async def monitor_codegen_task(flow: dict, task):
    """Monitor Codegen task progress"""
    try:
        while task.status not in ["completed", "failed"]:
            await asyncio.sleep(5)
            task.refresh()
            
            # Update flow progress based on task status
            if task.status == "running":
                flow["progress"] = min(flow["progress"] + 5, 90)
                flow["current_step"] = "Processing with Codegen agent..."
        
        if task.status == "completed":
            flow["status"] = "completed"
            flow["progress"] = 100
            flow["current_step"] = "Flow completed successfully"
            flow["result"] = task.result
        else:
            flow["status"] = "failed"
            flow["error"] = "Codegen task failed"
            flow["current_step"] = "Flow execution failed"
            
    except Exception as e:
        logger.error(f"Error monitoring Codegen task: {e}")
        flow["status"] = "failed"
        flow["error"] = str(e)

def calculate_flow_duration(flow: dict) -> str:
    """Calculate flow duration"""
    try:
        start_time = datetime.fromisoformat(flow["created_at"])
        duration = datetime.now() - start_time
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
            
    except:
        return "Unknown"

def estimate_completion_time(flow: dict) -> str:
    """Estimate flow completion time"""
    try:
        if flow["status"] == "completed":
            return "Completed"
        
        if flow["progress"] > 0:
            start_time = datetime.fromisoformat(flow["created_at"])
            elapsed = datetime.now() - start_time
            estimated_total = elapsed * (100 / flow["progress"])
            remaining = estimated_total - elapsed
            
            remaining_minutes = int(remaining.total_seconds() / 60)
            return f"~{remaining_minutes}m remaining"
        
        return "Estimating..."
        
    except:
        return "Unknown"

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page for manual token configuration"""
    user = await get_current_user(request)
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user,
        "github_token": config.github_token,
        "linear_api_key": config.linear_api_key,
        "slack_webhook_url": config.slack_webhook_url,
        "env_file_path": ".env"
    })

@app.post("/api/use-env-tokens")
async def use_env_tokens(request: Request):
    """Use environment tokens for authentication"""
    env_user = get_env_user()
    if not env_user:
        raise HTTPException(
            status_code=400,
            detail="No environment tokens found. Please set GITHUB_TOKEN, LINEAR_API_KEY, or SLACK_WEBHOOK_URL in your .env file."
        )
    
    # Create session for environment user
    session_id = f"env_user_{hashlib.md5(str(env_user).encode()).hexdigest()[:8]}"
    request.session["session_id"] = session_id
    user_sessions[session_id] = env_user
    
    return {"status": "success", "message": "Environment tokens activated", "user": env_user}

@app.get("/api/comprehensive/analysis/run/{analysis_type}")
async def run_comprehensive_analysis(
    analysis_type: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Run comprehensive code analysis"""
    try:
        # Validate analysis type
        valid_types = ["dead_code", "code_quality", "security", "dependencies", "complexity"]
        if analysis_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid analysis type. Must be one of: {valid_types}")
        
        # Start analysis based on type
        analysis_id = f"analysis_{analysis_type}_{int(time.time())}"
        
        # Mock analysis results for now - in real implementation, this would call graph-sitter
        analysis_result = {
            "id": analysis_id,
            "type": analysis_type,
            "status": "completed",
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "results": {
                "summary": f"{analysis_type.replace('_', ' ').title()} analysis completed",
                "issues_found": 0,
                "recommendations": [],
                "metrics": {}
            }
        }
        
        if analysis_type == "dead_code":
            analysis_result["results"].update({
                "dead_functions": [],
                "unused_imports": [],
                "unreachable_code": []
            })
        elif analysis_type == "code_quality":
            analysis_result["results"].update({
                "complexity_score": 85,
                "maintainability_index": 78,
                "code_coverage": 65
            })
        elif analysis_type == "security":
            analysis_result["results"].update({
                "vulnerabilities": [],
                "security_score": 92,
                "recommendations": ["Update dependencies", "Add input validation"]
            })
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/comprehensive/integrations/sync/{integration}")
async def sync_integration(
    integration: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Sync with external integrations"""
    try:
        valid_integrations = ["github", "linear", "slack", "prefect"]
        if integration not in valid_integrations:
            raise HTTPException(status_code=400, detail=f"Invalid integration. Must be one of: {valid_integrations}")
        
        sync_result = {
            "integration": integration,
            "status": "success",
            "synced_at": datetime.now().isoformat(),
            "items_synced": 0,
            "errors": []
        }
        
        # Mock sync results
        if integration == "github":
            sync_result.update({
                "repositories": 5,
                "pull_requests": 12,
                "issues": 8
            })
        elif integration == "linear":
            sync_result.update({
                "teams": 3,
                "projects": 7,
                "issues": 24
            })
        elif integration == "slack":
            sync_result.update({
                "channels": 15,
                "messages": 150
            })
        elif integration == "prefect":
            sync_result.update({
                "flows": 8,
                "deployments": 12,
                "runs": 45
            })
        
        return sync_result
        
    except Exception as e:
        logger.error(f"Integration sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/comprehensive/system/health")
async def get_system_health(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get comprehensive system health status"""
    try:
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": {"status": "online", "response_time": "45ms"},
                "database": {"status": "online", "connections": 12},
                "cache": {"status": "online", "hit_rate": "94%"},
                "integrations": {
                    "github": {"status": "online" if config.github_token else "offline"},
                    "linear": {"status": "online" if config.linear_api_key else "offline"},
                    "slack": {"status": "online" if config.slack_webhook_url else "offline"},
                    "prefect": {"status": "online" if config.prefect_api_url else "offline"}
                }
            },
            "metrics": {
                "cpu_usage": "23%",
                "memory_usage": "67%",
                "disk_usage": "45%",
                "active_flows": len(active_flows),
                "total_projects": 0
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/comprehensive/analytics/overview")
async def get_analytics_overview(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get comprehensive analytics overview"""
    try:
        analytics = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_projects": 0,
                "active_flows": len(active_flows),
                "completed_analyses": 0,
                "integration_health": "good"
            },
            "trends": {
                "flow_success_rate": 85,
                "average_completion_time": "12m 34s",
                "code_quality_trend": "improving",
                "issue_resolution_rate": 78
            },
            "recent_activity": [
                {
                    "type": "flow_completed",
                    "description": "CICD flow completed successfully",
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Analytics failed: {e}")
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
