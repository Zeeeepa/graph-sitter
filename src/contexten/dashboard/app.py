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
from .chat_manager import ChatManager
from .core_multi_project_manager import (
    CoreMultiProjectManager, ProjectConfig, QualityGate, FlowExecution,
    ProjectType, FlowStatus, handle_chat_command
)
from .enhanced_ui import (
    WebSocketManager, EventStreamProcessor, generate_enhanced_dashboard_html
)

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
chat_manager = ChatManager()
multi_project_manager = CoreMultiProjectManager(
    codegen_org_id=config.codegen_org_id,
    codegen_token=config.codegen_token
)
lightweight_orchestrator = LightweightOrchestrator(
    codegen_org_id=config.codegen_org_id,
    codegen_token=config.codegen_token
)

# WebSocket and Event Streaming
websocket_manager = WebSocketManager()
event_stream_processor = EventStreamProcessor(websocket_manager)

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

# CI/CD Orchestration API Endpoints

@app.get("/api/cicd/templates")
async def get_workflow_templates(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get all workflow templates"""
    try:
        templates = lightweight_orchestrator.get_workflow_templates()
        return {
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "type": t.type.value,
                    "description": t.description,
                    "estimated_duration": t.estimated_duration,
                    "default_triggers": [trigger.value for trigger in t.default_triggers],
                    "required_permissions": t.required_permissions
                }
                for t in templates
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get workflow templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cicd/workflows")
async def create_workflow_from_template(
    request: Request,
    workflow_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create a workflow from a template"""
    try:
        flow_id = await lightweight_orchestrator.create_workflow_from_template(
            project_id=workflow_data["project_id"],
            template_id=workflow_data["template_id"],
            name=workflow_data["name"],
            triggers=[TriggerType(t) for t in workflow_data.get("triggers", [])],
            custom_settings=workflow_data.get("settings", {})
        )
        
        if flow_id:
            return {"message": "Workflow created successfully", "flow_id": flow_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to create workflow")
            
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cicd/trigger")
async def trigger_workflows(
    request: Request,
    trigger_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Trigger workflows based on events"""
    try:
        executions = await lightweight_orchestrator.trigger_workflow(
            project_id=trigger_data["project_id"],
            trigger_type=TriggerType(trigger_data["trigger_type"]),
            trigger_data=trigger_data.get("data", {})
        )
        
        return {
            "message": f"Triggered {len(executions)} workflows",
            "execution_ids": executions
        }
    except Exception as e:
        logger.error(f"Failed to trigger workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cicd/analytics")
async def get_orchestration_analytics(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get CI/CD orchestration analytics"""
    try:
        analytics = await lightweight_orchestrator.get_orchestration_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Failed to get orchestration analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cicd/recommendations/{project_id}")
async def get_workflow_recommendations(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get workflow recommendations for a project"""
    try:
        recommendations = await lightweight_orchestrator.get_workflow_recommendations(project_id)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Failed to get workflow recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cicd/rules")
async def create_orchestration_rule(
    request: Request,
    rule_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create an orchestration rule"""
    try:
        rule = OrchestrationRule(
            id=rule_data.get("id", f"rule_{int(datetime.now().timestamp())}"),
            name=rule_data["name"],
            description=rule_data.get("description", ""),
            conditions=rule_data["conditions"],
            actions=rule_data["actions"],
            priority=rule_data.get("priority", 1),
            enabled=rule_data.get("enabled", True)
        )
        
        success = lightweight_orchestrator.add_orchestration_rule(rule)
        
        if success:
            return {"message": "Orchestration rule created successfully", "rule_id": rule.id}
        else:
            raise HTTPException(status_code=400, detail="Failed to create orchestration rule")
            
    except Exception as e:
        logger.error(f"Failed to create orchestration rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cicd/rules")
async def get_orchestration_rules(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get all orchestration rules"""
    try:
        rules = lightweight_orchestrator.get_orchestration_rules()
        return {
            "rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "conditions": r.conditions,
                    "actions": r.actions,
                    "priority": r.priority,
                    "enabled": r.enabled,
                    "created_at": r.created_at.isoformat()
                }
                for r in rules
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get orchestration rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cicd/rules/{rule_id}/toggle")
async def toggle_orchestration_rule(
    rule_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Enable or disable an orchestration rule"""
    try:
        # Get current rule state
        rules = lightweight_orchestrator.get_orchestration_rules()
        rule = next((r for r in rules if r.id == rule_id), None)
        
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Toggle the rule
        if rule.enabled:
            success = lightweight_orchestrator.disable_rule(rule_id)
            action = "disabled"
        else:
            success = lightweight_orchestrator.enable_rule(rule_id)
            action = "enabled"
        
        if success:
            return {"message": f"Rule {action} successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to {action.replace('d', '')} rule")
            
    except Exception as e:
        logger.error(f"Failed to toggle orchestration rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lightweight Orchestration API Endpoints

@app.get("/api/orchestrator/workflows")
async def get_workflows(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get all workflows"""
    try:
        workflows = lightweight_orchestrator.get_workflows()
        return {
            "workflows": [
                {
                    "id": w.id,
                    "name": w.name,
                    "type": w.type.value,
                    "project_path": w.project_path,
                    "auto_trigger": w.auto_trigger,
                    "created_at": w.created_at.isoformat()
                }
                for w in workflows
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orchestrator/workflows")
async def create_simple_workflow(
    request: Request,
    workflow_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create a simple workflow"""
    try:
        workflow_id = f"workflow_{int(datetime.now().timestamp())}"
        
        success = lightweight_orchestrator.create_workflow(
            workflow_id=workflow_id,
            name=workflow_data["name"],
            workflow_type=WorkflowType(workflow_data["type"]),
            project_path=workflow_data["project_path"],
            codegen_prompt=workflow_data["codegen_prompt"],
            auto_trigger=workflow_data.get("auto_trigger", False)
        )
        
        if success:
            return {"message": "Workflow created successfully", "workflow_id": workflow_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to create workflow")
            
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orchestrator/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Execute a workflow"""
    try:
        execution_id = await lightweight_orchestrator.execute_workflow(workflow_id)
        
        if execution_id:
            return {"message": "Workflow execution started", "execution_id": execution_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to start workflow execution")
            
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orchestrator/executions")
async def get_executions(
    request: Request,
    workflow_id: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get workflow executions"""
    try:
        executions = lightweight_orchestrator.get_executions(workflow_id)
        return {
            "executions": [
                {
                    "id": e.id,
                    "workflow_id": e.workflow_id,
                    "status": e.status,
                    "started_at": e.started_at.isoformat(),
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "result": e.result,
                    "error": e.error
                }
                for e in executions
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orchestrator/projects")
async def add_project_to_orchestrator(
    request: Request,
    project_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Add a project to the orchestrator"""
    try:
        success = lightweight_orchestrator.add_project(
            project_id=project_data["project_id"],
            project_path=project_data["project_path"]
        )
        
        if success:
            return {"message": "Project added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add project")
            
    except Exception as e:
        logger.error(f"Failed to add project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orchestrator/projects/{project_id}/analysis")
async def get_project_analysis(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get analysis for a project"""
    try:
        analysis = await lightweight_orchestrator.get_project_analysis(project_id)
        
        if analysis:
            return analysis
        else:
            raise HTTPException(status_code=404, detail="Project not found or analysis failed")
            
    except Exception as e:
        logger.error(f"Failed to get project analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orchestrator/projects/{project_id}/analyze")
async def trigger_project_analysis(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Trigger analysis for a project"""
    try:
        execution_id = await lightweight_orchestrator.trigger_analysis_for_project(project_id)
        
        if execution_id:
            return {"message": "Analysis started", "execution_id": execution_id}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
            
    except Exception as e:
        logger.error(f"Failed to trigger analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orchestrator/status")
async def get_orchestrator_status(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get orchestrator system status"""
    try:
        status = lightweight_orchestrator.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get orchestrator status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Simplified Chat Interface

@app.post("/api/chat/orchestrator")
async def chat_orchestrator_command(
    request: Request,
    chat_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Handle orchestrator chat commands"""
    try:
        message = chat_data.get("message", "")
        project_id = chat_data.get("project_id")
        
        response = await handle_chat_command(
            lightweight_orchestrator,
            message,
            project_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to process orchestrator chat command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Webhook endpoints for external integrations
@app.post("/api/webhooks/github")
async def github_webhook(request: Request):
    """Handle GitHub webhook events"""
    try:
        payload = await request.json()
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        
        await lightweight_orchestrator.handle_github_event(event_type, payload)
        
        return {"message": "GitHub event processed successfully"}
    except Exception as e:
        logger.error(f"Failed to process GitHub webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhooks/linear")
async def linear_webhook(request: Request):
    """Handle Linear webhook events"""
    try:
        payload = await request.json()
        event_type = payload.get("type", "unknown")
        
        await lightweight_orchestrator.handle_linear_event(event_type, payload)
        
        return {"message": "Linear event processed successfully"}
    except Exception as e:
        logger.error(f"Failed to process Linear webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Chat Agent Integration
@app.post("/api/chat/cicd")
async def chat_cicd_command(
    request: Request,
    chat_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Handle CI/CD related chat commands"""
    try:
        message = chat_data.get("message", "")
        project_id = chat_data.get("project_id")
        
        # Parse chat commands for CI/CD operations
        if "create workflow" in message.lower():
            # Extract workflow creation parameters from natural language
            response = await _handle_create_workflow_command(message, project_id, user)
        elif "trigger" in message.lower() and "workflow" in message.lower():
            # Handle workflow triggering
            response = await _handle_trigger_workflow_command(message, project_id, user)
        elif "status" in message.lower():
            # Get project/workflow status
            response = await _handle_status_command(message, project_id, user)
        elif "recommend" in message.lower():
            # Get recommendations
            response = await _handle_recommendations_command(message, project_id, user)
        else:
            # Use Codegen SDK for general queries
            if lightweight_orchestrator.codegen_agent:
                task = lightweight_orchestrator.codegen_agent.run(
                    prompt=f"Help with CI/CD question: {message}"
                )
                # Wait for completion (with timeout)
                max_wait = 30
                waited = 0
                while task.status not in ["completed", "failed"] and waited < max_wait:
                    await asyncio.sleep(1)
                    task.refresh()
                    waited += 1
                
                if task.status == "completed":
                    response = {"message": task.result, "type": "codegen_response"}
                else:
                    response = {"message": "I'm still working on that. Please check back in a moment.", "type": "processing"}
            else:
                response = {"message": "I can help you with CI/CD workflows. Try asking me to 'create workflow', 'trigger workflow', or 'show status'.", "type": "help"}
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to process CI/CD chat command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions for chat commands
async def _handle_create_workflow_command(message: str, project_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """Handle workflow creation from chat"""
    # Simple keyword extraction - could be enhanced with NLP
    workflow_types = {
        "test": "build_and_test_basic",
        "security": "security_scan_comprehensive", 
        "review": "code_review_ai",
        "deploy": "deploy_production"
    }
    
    template_id = None
    for keyword, template in workflow_types.items():
        if keyword in message.lower():
            template_id = template
            break
    
    if not template_id:
        return {
            "message": "I can create workflows for: testing, security scanning, code review, or deployment. Which would you like?",
            "type": "clarification"
        }
    
    # Create workflow with auto-generated name
    workflow_name = f"Auto-created {template_id.replace('_', ' ').title()}"
    
    flow_id = await lightweight_orchestrator.create_workflow_from_template(
        project_id=project_id,
        template_id=template_id,
        name=workflow_name
    )
    
    if flow_id:
        return {
            "message": f"✅ Created {workflow_name} workflow! Flow ID: {flow_id}",
            "type": "success",
            "flow_id": flow_id
        }
    else:
        return {
            "message": "❌ Failed to create workflow. Please check the project configuration.",
            "type": "error"
        }

async def _handle_trigger_workflow_command(message: str, project_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """Handle workflow triggering from chat"""
    # Trigger all workflows for the project (manual trigger)
    executions = await lightweight_orchestrator.trigger_workflow(
        project_id=project_id,
        trigger_type=TriggerType.MANUAL,
        trigger_data={"triggered_by": user.get("email", "chat_user")}
    )
    
    if executions:
        return {
            "message": f"🚀 Triggered {len(executions)} workflows! Execution IDs: {', '.join(executions)}",
            "type": "success",
            "execution_ids": executions
        }
    else:
        return {
            "message": "No workflows available to trigger. Try creating some workflows first!",
            "type": "info"
        }

async def _handle_status_command(message: str, project_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """Handle status requests from chat"""
    if project_id:
        # Get project-specific status
        project = await multi_project_manager.get_project(project_id)
        flows = await multi_project_manager.get_flows(project_id)
        running_flows = await multi_project_manager.get_running_flows()
        
        project_running = [e for e in running_flows.values() if e.project_id == project_id]
        
        status_msg = f"📊 **Project Status: {project.name if project else 'Unknown'}**\n"
        status_msg += f"• Workflows: {len(flows)}\n"
        status_msg += f"• Running: {len(project_running)}\n"
        
        if project_running:
            status_msg += "\n🔄 **Currently Running:**\n"
            for execution in project_running:
                status_msg += f"• {execution.current_step} ({execution.progress:.0%})\n"
        
        return {"message": status_msg, "type": "status"}
    else:
        # Get system-wide status
        system_status = await multi_project_manager.get_system_status()
        analytics = await lightweight_orchestrator.get_orchestration_analytics()
        
        status_msg = "📊 **System Status**\n"
        status_msg += f"• Projects: {system_status['projects']['total']} ({system_status['projects']['active']} active)\n"
        status_msg += f"• Running Flows: {system_status['flows']['running']}\n"
        status_msg += f"• Success Rate: {analytics['workflow_statistics']['success_rate']:.1%}\n"
        
        return {"message": status_msg, "type": "status"}

async def _handle_recommendations_command(message: str, project_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """Handle recommendation requests from chat"""
    if not project_id:
        return {
            "message": "Please specify a project to get recommendations for.",
            "type": "clarification"
        }
    
    recommendations = await lightweight_orchestrator.get_workflow_recommendations(project_id)
    
    if not recommendations:
        return {
            "message": "🎉 Great! Your project looks well-configured with appropriate workflows.",
            "type": "success"
        }
    
    rec_msg = "💡 **Recommendations for your project:**\n"
    for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
        rec_msg += f"{i}. {rec['description']}\n"
    
    return {"message": rec_msg, "type": "recommendations", "recommendations": recommendations}

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
    """Initialize the dashboard on startup"""
    logger.info("Starting dashboard...")
    
    # Initialize multi-project manager
    await multi_project_manager.start()
    
    # Initialize event stream processor
    await event_stream_processor.start(multi_project_manager)
    
    # Validate configuration
    missing_config = []
    if not config.codegen_org_id:
        missing_config.append("CODEGEN_ORG_ID")
    if not config.codegen_token:
        missing_config.append("CODEGEN_TOKEN")
    
    if missing_config:
        logger.warning(f"Missing configuration: {', '.join(missing_config)}")
        logger.warning("Some features may not be available")
    
    logger.info("Dashboard startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down dashboard...")
    
    # Stop event stream processor
    await event_stream_processor.stop(multi_project_manager)
    
    # Stop multi-project manager
    await multi_project_manager.stop()
    
    logger.info("Dashboard shutdown complete")
    
    # Cleanup all integration agents
    for agent in integration_agents.values():
        try:
            if hasattr(agent, 'stop'):
                await agent.stop()
        except Exception as e:
            logger.error(f"Error stopping agent: {e}")

# Core Multi-Project Management API

@app.get("/api/core-projects")
async def get_core_projects(
    request: Request,
    active_only: bool = False,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get all projects"""
    try:
        projects = await multi_project_manager.get_projects(active_only=active_only)
        return [
            {
                "id": p.id,
                "name": p.name,
                "type": p.type.value,
                "path": p.path,
                "source_url": p.source_url,
                "branch": p.branch,
                "description": p.description,
                "tags": p.tags,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat()
            }
            for p in projects
        ]
    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/core-projects")
async def add_core_project(
    request: Request,
    project_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Add a new project"""
    try:
        project = ProjectConfig(
            id=project_data["id"],
            name=project_data["name"],
            type=ProjectType(project_data["type"]),
            path=project_data["path"],
            source_url=project_data.get("source_url"),
            branch=project_data.get("branch", "main"),
            description=project_data.get("description", ""),
            tags=project_data.get("tags", [])
        )
        
        success = await multi_project_manager.add_project(project)
        
        if success:
            return {"message": "Project added successfully", "project_id": project.id}
        else:
            raise HTTPException(status_code=400, detail="Failed to add project")
            
    except Exception as e:
        logger.error(f"Failed to add project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/core-projects/{project_id}")
async def get_core_project(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get a specific project"""
    try:
        project = await multi_project_manager.get_project(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "id": project.id,
            "name": project.name,
            "type": project.type.value,
            "path": project.path,
            "source_url": project.source_url,
            "branch": project.branch,
            "description": project.description,
            "tags": project.tags,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/core-projects/{project_id}")
async def remove_core_project(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Remove a project"""
    try:
        success = await multi_project_manager.remove_project(project_id)
        
        if success:
            return {"message": "Project removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/core-projects/{project_id}/analyze")
async def analyze_core_project(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Trigger analysis for a project"""
    try:
        result = await multi_project_manager.analyze_project(project_id)
        
        if result:
            return {"message": "Analysis completed", "result": result}
        else:
            raise HTTPException(status_code=404, detail="Project not found or analysis failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/core-projects/{project_id}/executions")
async def get_project_executions(
    project_id: str,
    request: Request,
    limit: int = 20,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get execution history for a project"""
    try:
        executions = await multi_project_manager.get_executions(project_id=project_id, limit=limit)
        
        return [
            {
                "id": e.id,
                "project_id": e.project_id,
                "flow_type": e.flow_type,
                "status": e.status.value,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "result": e.result,
                "error": e.error,
                "triggered_by": e.triggered_by
            }
            for e in executions
        ]
    except Exception as e:
        logger.error(f"Failed to get project executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/core-projects/status")
async def get_core_system_status(
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get system status"""
    try:
        status = await multi_project_manager.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Quality Gates API

@app.post("/api/core-projects/{project_id}/quality-gates")
async def add_quality_gate(
    project_id: str,
    request: Request,
    gate_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Add a quality gate for a project"""
    try:
        gate = QualityGate(
            id=f"gate_{project_id}_{int(datetime.now().timestamp())}",
            name=gate_data["name"],
            project_id=project_id,
            conditions=gate_data["conditions"],
            actions=gate_data["actions"],
            enabled=gate_data.get("enabled", True)
        )
        
        success = await multi_project_manager.add_quality_gate(gate)
        
        if success:
            return {"message": "Quality gate added successfully", "gate_id": gate.id}
        else:
            raise HTTPException(status_code=400, detail="Failed to add quality gate")
            
    except Exception as e:
        logger.error(f"Failed to add quality gate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/core-projects/{project_id}/quality-gates")
async def get_quality_gates(
    project_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get quality gates for a project"""
    try:
        gates = await multi_project_manager.get_quality_gates(project_id=project_id)
        
        return [
            {
                "id": g.id,
                "name": g.name,
                "project_id": g.project_id,
                "conditions": g.conditions,
                "actions": g.actions,
                "enabled": g.enabled,
                "created_at": g.created_at.isoformat()
            }
            for g in gates
        ]
    except Exception as e:
        logger.error(f"Failed to get quality gates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat Integration API

@app.post("/api/chat/core-projects")
async def chat_core_projects(
    request: Request,
    chat_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Handle chat commands for core projects"""
    try:
        message = chat_data.get("message", "")
        project_id = chat_data.get("project_id")
        user_email = user.get("email")
        
        response = await handle_chat_command(
            multi_project_manager,
            message,
            project_id,
            user_email
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to process chat command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/core-projects/{project_id}/codegen-task")
async def execute_codegen_task(
    project_id: str,
    request: Request,
    task_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Execute a Codegen task for a project"""
    try:
        prompt = task_data.get("prompt", "")
        triggered_by = user.get("email", "user")
        
        execution_id = await multi_project_manager.execute_codegen_task(
            project_id=project_id,
            prompt=prompt,
            triggered_by=triggered_by
        )
        
        if execution_id:
            return {"message": "Codegen task started", "execution_id": execution_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to start Codegen task")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute Codegen task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for Real-time Events

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time events"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.websocket("/ws/project/{project_id}")
async def websocket_project_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for project-specific events"""
    await websocket_manager.connect(websocket, project_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, project_id)

# Enhanced Dashboard UI

@app.get("/dashboard/enhanced", response_class=HTMLResponse)
async def enhanced_dashboard():
    """Serve the enhanced dashboard UI"""
    return generate_enhanced_dashboard_html()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="debug" if config.debug else "info"
    )
