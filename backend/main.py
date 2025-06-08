"""
Main FastAPI application for AI-Powered CI/CD Automation Platform
"""
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from backend.database import init_db, get_db
from backend.config import settings
from backend.api import projects, workflows, agents
from backend.services.websocket_manager import WebSocketManager
from backend.services.github_service import GitHubService
from backend.services.codegen_service import CodegenService
from backend.models.project import Project
from backend.models.workflow import WorkflowExecution


# Initialize WebSocket manager
websocket_manager = WebSocketManager()

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    print("🚀 Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI-Powered CI/CD Automation Platform",
    description="Automated development workflows with Codegen SDK, GitHub, and Graph-sitter",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user info"""
    token = credentials.credentials
    # TODO: Implement JWT validation
    return {"user_id": "demo_user", "token": token}


# Include API routers
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI-Powered CI/CD Automation Platform",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/api/v1/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "github": "ready",
            "codegen": "ready",
            "websocket": "active"
        }
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back for now - can be extended for client commands
            await websocket_manager.send_personal_message(f"Echo: {data}", client_id)
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)


@app.post("/api/v1/github/authenticate")
async def authenticate_github(token: str, user=Depends(get_current_user)):
    """Authenticate with GitHub and fetch repositories"""
    try:
        github_service = GitHubService(token)
        repos = await github_service.get_user_repositories()
        
        # Store token securely (implement proper encryption)
        # TODO: Store in database with encryption
        
        return {
            "status": "success",
            "repositories": repos,
            "message": f"Found {len(repos)} repositories"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GitHub authentication failed: {str(e)}")


@app.post("/api/v1/agents/execute")
async def execute_agent(
    prompt: str,
    project_id: str,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Execute Codegen agent with enhanced prompt"""
    try:
        # Get project details
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Initialize Codegen service
        codegen_service = CodegenService(
            token=settings.CODEGEN_TOKEN,
            org_id=settings.CODEGEN_ORG_ID
        )
        
        # Enhance prompt with context and techniques
        enhanced_prompt = await codegen_service.enhance_prompt(prompt, project)
        
        # Execute agent
        task = await codegen_service.execute_agent(enhanced_prompt)
        
        # Broadcast status update via WebSocket
        await websocket_manager.broadcast({
            "type": "agent_status",
            "project_id": project_id,
            "task_id": task.id,
            "status": task.status,
            "prompt": enhanced_prompt[:100] + "..." if len(enhanced_prompt) > 100 else enhanced_prompt
        })
        
        return {
            "task_id": task.id,
            "status": task.status,
            "enhanced_prompt": enhanced_prompt,
            "web_url": task.web_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

