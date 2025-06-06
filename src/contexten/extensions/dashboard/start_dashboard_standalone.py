#!/usr/bin/env python3
"""
Standalone startup script for the Consolidated Dashboard.
This script doesn't depend on the existing contexten module.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add the dashboard directory to Python path
dashboard_dir = Path(__file__).parent
sys.path.insert(0, str(dashboard_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print the dashboard banner."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║        🚀 Consolidated Strands Agent Dashboard 🚀           ║")
    print("║                                                              ║")
    print("║  Comprehensive dashboard for Strands tools ecosystem        ║")
    print("║  • Multi-layer orchestration (Strands + ControlFlow +       ║")
    print("║    Prefect)                                                  ║")
    print("║  • AI-powered planning with Codegen SDK                     ║")
    print("║  • Real-time monitoring and quality gates                   ║")
    print("║  • GitHub, Linear, and Slack integrations                   ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

def check_environment():
    """Check environment variables and configuration."""
    logger.info("Checking environment configuration...")
    
    # Required variables
    required_vars = {
        'CODEGEN_ORG_ID': 'Codegen organization ID',
        'CODEGEN_TOKEN': 'Codegen API token'
    }
    
    # Optional variables
    optional_vars = {
        'GITHUB_ACCESS_TOKEN': 'GitHub integration',
        'LINEAR_ACCESS_TOKEN': 'Linear integration', 
        'SLACK_BOT_TOKEN': 'Slack integration',
        'OPENAI_API_KEY': 'OpenAI API for ControlFlow'
    }
    
    missing_required = []
    missing_optional = []
    
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"{var} ({desc})")
    
    for var, desc in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"{var} ({desc})")
    
    if missing_required:
        logger.error("❌ Missing required environment variables:")
        for var in missing_required:
            logger.error(f"   - {var}")
        logger.error("\nPlease set these variables and try again.")
        return False
    
    if missing_optional:
        logger.info("ℹ️  Optional integrations not configured:")
        for var in missing_optional:
            logger.info(f"   - {var}")
        logger.info("\n   Dashboard will use mock implementations for missing integrations.")
    
    logger.info("✅ Environment configuration validated")
    return True

def create_standalone_dashboard():
    """Create a standalone dashboard instance."""
    try:
        # Import FastAPI and create a simple dashboard
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
        import uvicorn
        import json
        from datetime import datetime
        
        # Import our models
        from consolidated_models import Project, Flow, Task, FlowStatus, TaskStatus
        
        # Create FastAPI app
        app = FastAPI(
            title="Consolidated Strands Agent Dashboard",
            version="1.0.0",
            description="Comprehensive dashboard for Strands tools ecosystem"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # WebSocket connections
        active_connections = []
        
        # Basic routes
        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        
        @app.get("/api/health")
        async def api_health():
            return {
                "status": "healthy",
                "services": {
                    "api": "running",
                    "websocket": "active",
                    "dashboard": "operational"
                },
                "timestamp": datetime.now().isoformat()
            }
        
        @app.get("/api/projects")
        async def get_projects():
            # Mock projects for demonstration
            return [
                {
                    "id": "demo-1",
                    "name": "Demo Project",
                    "repo_url": "https://github.com/demo/project",
                    "status": "active",
                    "progress": 75.0,
                    "quality_score": 85.5
                }
            ]
        
        @app.post("/api/projects")
        async def create_project(project_data: dict):
            # Mock project creation
            project = Project(
                id=f"project-{datetime.now().timestamp()}",
                name=project_data.get("name", "New Project"),
                repo_url=project_data.get("repo_url", ""),
                owner="demo",
                repo_name="project",
                full_name="demo/project",
                requirements=project_data.get("requirements", "")
            )
            return project.to_dict()
        
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            active_connections.append(websocket)
            logger.info(f"WebSocket connection established. Total connections: {len(active_connections)}")
            
            try:
                # Send welcome message
                welcome_msg = {
                    "type": "connection",
                    "message": "Connected to Consolidated Dashboard",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(welcome_msg))
                
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Echo back the message with timestamp
                    response = {
                        "type": "echo",
                        "data": message,
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(response))
                    
            except WebSocketDisconnect:
                active_connections.remove(websocket)
                logger.info(f"WebSocket connection closed. Total connections: {len(active_connections)}")
        
        return app
        
    except Exception as e:
        logger.error(f"❌ Failed to create dashboard: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main entry point."""
    print_banner()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create dashboard
    logger.info("Creating dashboard application...")
    app = create_standalone_dashboard()
    
    if not app:
        logger.error("❌ Failed to create dashboard application")
        sys.exit(1)
    
    logger.info("✅ Dashboard application created successfully")
    
    # Configuration
    host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port = int(os.getenv("DASHBOARD_PORT", "8000"))
    debug = os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting dashboard server...")
    logger.info(f"   Host: {host}")
    logger.info(f"   Port: {port}")
    logger.info(f"   Debug: {debug}")
    logger.info(f"   Dashboard: http://{host}:{port}")
    logger.info(f"   API Docs: http://{host}:{port}/docs")
    logger.info(f"   WebSocket: ws://{host}:{port}/ws")
    print()
    
    try:
        import uvicorn
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info" if debug else "warning",
            reload=debug
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Dashboard stopped by user")
    except Exception as e:
        logger.error(f"❌ Dashboard server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

