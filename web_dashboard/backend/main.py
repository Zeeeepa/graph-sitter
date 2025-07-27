#!/usr/bin/env python3
"""
Web-Eval-Agent Dashboard Backend

FastAPI backend for the project management dashboard with:
- Project management and configuration
- GitHub integration and webhook handling
- Codegen API integration
- Real-time updates via WebSocket
- Validation pipeline orchestration
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import json

from database import Database, get_database
from models import (
    Project, ProjectCreate, ProjectUpdate, ProjectSettings,
    AgentRun, AgentRunCreate, AgentRunUpdate,
    WebhookEvent, ValidationResult
)
from github_integration import GitHubIntegration
from codegen_client import CodegenClient
from webhook_handler import WebhookHandler
from validation_pipeline import ValidationPipeline
from websocket_manager import WebSocketManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
websocket_manager = WebSocketManager()
github_integration = GitHubIntegration()
codegen_client = CodegenClient()
webhook_handler = WebhookHandler()
validation_pipeline = ValidationPipeline()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Web-Eval-Agent Dashboard Backend")
    
    # Initialize database
    database = Database()
    await database.initialize()
    
    # Initialize integrations
    await github_integration.initialize()
    await codegen_client.initialize()
    await validation_pipeline.initialize()
    
    logger.info("Backend initialization complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down backend")
    await database.close()
    await github_integration.shutdown()
    await codegen_client.shutdown()
    await validation_pipeline.shutdown()

# Create FastAPI app
app = FastAPI(
    title="Web-Eval-Agent Dashboard API",
    description="Backend API for project management and automated validation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user."""
    # TODO: Implement proper JWT token validation
    # For now, just return a mock user
    return {"id": "user1", "email": "user@example.com"}

# API Models
class ProjectListResponse(BaseModel):
    projects: List[Project]
    total: int

class AgentRunRequest(BaseModel):
    target_text: str = Field(..., description="Target goal for the agent run")
    auto_confirm_plan: bool = Field(default=False, description="Auto-confirm proposed plans")

class WebhookPayload(BaseModel):
    event_type: str
    payload: Dict[str, Any]

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Web-Eval-Agent Dashboard API", "status": "running"}

@app.get("/api/projects", response_model=ProjectListResponse)
async def list_projects(
    db: Database = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """List all projects for the current user."""
    try:
        projects = await db.get_user_projects(current_user["id"])
        return ProjectListResponse(projects=projects, total=len(projects))
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to list projects")

@app.post("/api/projects", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    db: Database = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Create a new project."""
    try:
        # Validate GitHub repository access
        repo_info = await github_integration.get_repository_info(
            project_data.github_owner, project_data.github_repo
        )
        
        if not repo_info:
            raise HTTPException(status_code=400, detail="Cannot access GitHub repository")
        
        # Create project in database
        project = await db.create_project(
            user_id=current_user["id"],
            project_data=project_data
        )
        
        # Set up webhook for the repository
        webhook_url = f"{os.getenv('WEBHOOK_BASE_URL')}/api/webhooks/{project.id}"
        webhook_id = await github_integration.create_webhook(
            project_data.github_owner,
            project_data.github_repo,
            webhook_url
        )
        
        # Update project with webhook ID
        await db.update_project(project.id, {"webhook_id": webhook_id})
        project.webhook_id = webhook_id
        
        # Notify connected clients
        await websocket_manager.broadcast_to_user(
            current_user["id"],
            {
                "type": "project_created",
                "project": project.dict()
            }
        )
        
        return project
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")

@app.get("/api/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    db: Database = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific project."""
    try:
        project = await db.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project")

@app.put("/api/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Database = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Update a project."""
    try:
        project = await db.update_project(project_id, project_data.dict(exclude_unset=True))
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Notify connected clients
        await websocket_manager.broadcast_to_user(
            current_user["id"],
            {
                "type": "project_updated",
                "project": project.dict()
            }
        )
        
        return project
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project")

@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    db: Database = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Delete a project."""
    try:
        project = await db.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Remove webhook
        if project.webhook_id:
            await github_integration.delete_webhook(
                project.github_owner,
                project.github_repo,
                project.webhook_id
            )
        
        # Delete from database
        await db.delete_project(project_id)
        
        # Notify connected clients
        await websocket_manager.broadcast_to_user(
            current_user["id"],
            {
                "type": "project_deleted",
                "project_id": project_id
            }
        )
        
        return {"message": "Project deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project")

@app.post("/api/projects/{project_id}/agent-run")
async def start_agent_run(
    project_id: str,
    run_request: AgentRunRequest,
    db: Database = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Start an agent run for a project."""
    try:
        project = await db.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create agent run record
        agent_run = await db.create_agent_run(
            project_id=project_id,
            target_text=run_request.target_text,
            auto_confirm_plan=run_request.auto_confirm_plan
        )
        
        # Start the agent run asynchronously
        asyncio.create_task(
            _execute_agent_run(agent_run, project, current_user["id"])
        )
        
        return {"message": "Agent run started", "run_id": agent_run.id}
        
    except Exception as e:
        logger.error(f"Error starting agent run: {e}")
        raise HTTPException(status_code=500, detail="Failed to start agent run")

@app.post("/api/projects/{project_id}/agent-run/{run_id}/continue")
async def continue_agent_run(
    project_id: str,
    run_id: str,
    continuation_text: str,
    db: Database = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Continue an existing agent run."""
    try:
        agent_run = await db.get_agent_run(run_id, project_id)
        if not agent_run:
            raise HTTPException(status_code=404, detail="Agent run not found")
        
        # Continue the agent run
        asyncio.create_task(
            _continue_agent_run(agent_run, continuation_text, current_user["id"])
        )
        
        return {"message": "Agent run continued"}
        
    except Exception as e:
        logger.error(f"Error continuing agent run: {e}")
        raise HTTPException(status_code=500, detail="Failed to continue agent run")

@app.post("/api/webhooks/{project_id}")
async def handle_webhook(
    project_id: str,
    payload: WebhookPayload,
    db: Database = Depends(get_database)
):
    """Handle GitHub webhook events."""
    try:
        project = await db.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Process webhook event
        await webhook_handler.process_event(
            project=project,
            event_type=payload.event_type,
            payload=payload.payload
        )
        
        return {"message": "Webhook processed successfully"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")

@app.get("/api/projects/{project_id}/tree")
async def get_project_tree(
    project_id: str,
    db: Database = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get project file tree with error annotations."""
    try:
        project = await db.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get repository tree structure
        tree = await github_integration.get_repository_tree(
            project.github_owner,
            project.github_repo,
            project.branch or "main"
        )
        
        # TODO: Add error annotations from graph-sitter analysis
        
        return {"tree": tree}
        
    except Exception as e:
        logger.error(f"Error getting project tree: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project tree")

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates."""
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client messages (ping, etc.)
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id)

# Helper functions

async def _execute_agent_run(agent_run: AgentRun, project: Project, user_id: str):
    """Execute an agent run asynchronously."""
    try:
        # Update status to running
        await websocket_manager.broadcast_to_user(
            user_id,
            {
                "type": "agent_run_status",
                "run_id": agent_run.id,
                "status": "running",
                "message": "Starting agent run..."
            }
        )
        
        # Prepare context prompt
        context_prompt = f"Project='{project.name}'"
        if project.repository_rules:
            context_prompt += f"\nRepository Rules: {project.repository_rules}"
        
        full_prompt = f"{context_prompt}\n\nTarget: {agent_run.target_text}"
        
        # Start Codegen API session
        session = await codegen_client.start_session(
            project_context=context_prompt,
            initial_prompt=agent_run.target_text
        )
        
        # Update agent run with session ID
        agent_run.session_id = session.id
        await Database().update_agent_run(agent_run.id, {"session_id": session.id})
        
        # Process the response
        await _process_agent_response(session, agent_run, project, user_id)
        
    except Exception as e:
        logger.error(f"Error executing agent run: {e}")
        await websocket_manager.broadcast_to_user(
            user_id,
            {
                "type": "agent_run_error",
                "run_id": agent_run.id,
                "error": str(e)
            }
        )

async def _continue_agent_run(agent_run: AgentRun, continuation_text: str, user_id: str):
    """Continue an existing agent run."""
    try:
        if not agent_run.session_id:
            raise ValueError("No active session for agent run")
        
        # Continue the session
        session = await codegen_client.continue_session(
            agent_run.session_id,
            continuation_text
        )
        
        # Process the response
        await _process_agent_response(session, agent_run, None, user_id)
        
    except Exception as e:
        logger.error(f"Error continuing agent run: {e}")
        await websocket_manager.broadcast_to_user(
            user_id,
            {
                "type": "agent_run_error",
                "run_id": agent_run.id,
                "error": str(e)
            }
        )

async def _process_agent_response(session, agent_run: AgentRun, project: Optional[Project], user_id: str):
    """Process agent response and handle different response types."""
    try:
        response = session.get_latest_response()
        
        if response.type == "regular":
            # Regular response - show continue button
            await websocket_manager.broadcast_to_user(
                user_id,
                {
                    "type": "agent_run_response",
                    "run_id": agent_run.id,
                    "response_type": "regular",
                    "content": response.content,
                    "can_continue": True
                }
            )
            
        elif response.type == "plan":
            # Plan response - show confirm/modify buttons
            await websocket_manager.broadcast_to_user(
                user_id,
                {
                    "type": "agent_run_response",
                    "run_id": agent_run.id,
                    "response_type": "plan",
                    "content": response.content,
                    "plan": response.plan,
                    "can_confirm": True,
                    "can_modify": True
                }
            )
            
        elif response.type == "pr":
            # PR created - show validation flow
            pr_number = response.pr_number
            pr_url = response.pr_url
            
            await websocket_manager.broadcast_to_user(
                user_id,
                {
                    "type": "agent_run_response",
                    "run_id": agent_run.id,
                    "response_type": "pr",
                    "content": response.content,
                    "pr_number": pr_number,
                    "pr_url": pr_url,
                    "can_validate": True
                }
            )
            
            # Start validation pipeline if project has auto-merge enabled
            if project and project.auto_merge_validated_pr:
                asyncio.create_task(
                    _start_validation_pipeline(project, pr_number, user_id)
                )
        
    except Exception as e:
        logger.error(f"Error processing agent response: {e}")
        raise

async def _start_validation_pipeline(project: Project, pr_number: int, user_id: str):
    """Start the validation pipeline for a PR."""
    try:
        await websocket_manager.broadcast_to_user(
            user_id,
            {
                "type": "validation_started",
                "project_id": project.id,
                "pr_number": pr_number,
                "message": "Starting validation pipeline..."
            }
        )
        
        # Run validation pipeline
        result = await validation_pipeline.validate_pr(
            project=project,
            pr_number=pr_number,
            progress_callback=lambda msg: websocket_manager.broadcast_to_user(
                user_id,
                {
                    "type": "validation_progress",
                    "project_id": project.id,
                    "pr_number": pr_number,
                    "message": msg
                }
            )
        )
        
        # Send final result
        await websocket_manager.broadcast_to_user(
            user_id,
            {
                "type": "validation_complete",
                "project_id": project.id,
                "pr_number": pr_number,
                "success": result.success,
                "message": result.message,
                "can_merge": result.success and project.auto_merge_validated_pr
            }
        )
        
    except Exception as e:
        logger.error(f"Error in validation pipeline: {e}")
        await websocket_manager.broadcast_to_user(
            user_id,
            {
                "type": "validation_error",
                "project_id": project.id,
                "pr_number": pr_number,
                "error": str(e)
            }
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
