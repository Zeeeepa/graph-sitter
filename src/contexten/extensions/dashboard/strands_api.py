"""
Strands API
Clean API endpoints using proper Strands tools integrations
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import os

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

from .strands_orchestrator import StrandsOrchestrator, OrchestrationLayer
from .strands_codegen import StrandsCodegenManager
from .system_watcher import SystemWatcher

logger = logging.getLogger(__name__)

# Pydantic models for API requests
class WorkflowConfig(BaseModel):
    name: str
    description: str = ""
    layers: List[str] = ["workflow"]
    workflow: Dict[str, Any] = {}
    mcp_agents: List[Dict[str, Any]] = []
    controlflow_tasks: List[Dict[str, Any]] = []
    prefect_flows: List[Dict[str, Any]] = []

class CodegenTaskRequest(BaseModel):
    prompt: str
    context: Dict[str, Any] = {}
    task_type: str = "code_generation"  # or "plan_creation"

class PlanCreationRequest(BaseModel):
    requirements: str
    context: Dict[str, Any] = {}

# Global instances
orchestrator = None
codegen_manager = None
system_watcher = None
websocket_connections = []

def create_strands_api() -> FastAPI:
    """Create FastAPI app with Strands integrations"""
    
    app = FastAPI(
        title="Strands Agent Dashboard API",
        description="API for Strands tools ecosystem",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize Strands integrations on startup"""
        global orchestrator, codegen_manager, system_watcher
        
        try:
            logger.info("Initializing Strands integrations...")
            
            # Initialize orchestrator
            orchestrator = StrandsOrchestrator()
            layer_status = await orchestrator.initialize()
            logger.info(f"Orchestrator initialized. Layer status: {layer_status}")
            
            # Initialize Codegen manager
            codegen_manager = StrandsCodegenManager()
            codegen_success = await codegen_manager.initialize()
            logger.info(f"Codegen manager initialized: {codegen_success}")
            
            # Initialize system watcher
            system_watcher = SystemWatcher(orchestrator)
            await system_watcher.start()
            logger.info("System watcher started")
            
            logger.info("Strands integrations initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Strands integrations: {e}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        global system_watcher
        
        try:
            if system_watcher:
                await system_watcher.stop()
                logger.info("System watcher stopped")
            
            logger.info("Strands integrations shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint"""
        try:
            health_summary = await system_watcher.get_health_summary() if system_watcher else {
                'overall_status': 'unknown',
                'message': 'System watcher not initialized'
            }
            
            return {
                "status": "running",
                "message": "Strands Agent Dashboard API",
                "timestamp": datetime.now().isoformat(),
                "health": health_summary
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Workflow endpoints
    @app.post("/api/workflows")
    async def create_workflow(config: WorkflowConfig, background_tasks: BackgroundTasks):
        """Create a new workflow orchestration"""
        try:
            if not orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            orchestration_id = await orchestrator.create_multi_layer_orchestration(config.dict())
            
            # Start execution in background
            background_tasks.add_task(execute_workflow_background, orchestration_id)
            
            # Broadcast to WebSocket clients
            await broadcast_workflow_update({
                'type': 'workflow_created',
                'orchestration_id': orchestration_id,
                'config': config.dict()
            })
            
            return {
                "orchestration_id": orchestration_id,
                "status": "created",
                "message": "Workflow orchestration created and execution started"
            }
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/workflows")
    async def list_workflows():
        """List all workflow orchestrations"""
        try:
            if not orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            orchestrations = await orchestrator.list_orchestrations()
            return {"workflows": orchestrations}
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/workflows/{orchestration_id}")
    async def get_workflow_status(orchestration_id: str):
        """Get workflow orchestration status"""
        try:
            if not orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            status = await orchestrator.get_orchestration_status(orchestration_id)
            return status
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/workflows/{orchestration_id}")
    async def cancel_workflow(orchestration_id: str):
        """Cancel a workflow orchestration"""
        try:
            if not orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            success = await orchestrator.cancel_orchestration(orchestration_id)
            
            if success:
                # Broadcast to WebSocket clients
                await broadcast_workflow_update({
                    'type': 'workflow_cancelled',
                    'orchestration_id': orchestration_id
                })
                
                return {"message": "Workflow cancelled successfully"}
            else:
                raise HTTPException(status_code=404, detail="Workflow not found or cannot be cancelled")
                
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Codegen endpoints
    @app.post("/api/codegen/tasks")
    async def create_codegen_task(request: CodegenTaskRequest, background_tasks: BackgroundTasks):
        """Create a new Codegen task"""
        try:
            if not codegen_manager:
                raise HTTPException(status_code=503, detail="Codegen manager not initialized")
            
            if request.task_type == "code_generation":
                task_id = await codegen_manager.create_code_generation_task(
                    request.prompt, 
                    request.context
                )
            elif request.task_type == "plan_creation":
                task_id = await codegen_manager.create_plan_creation_task(
                    request.prompt,  # Using prompt as requirements
                    request.context
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid task type")
            
            # Start execution in background
            background_tasks.add_task(execute_codegen_task_background, task_id)
            
            return {
                "task_id": task_id,
                "status": "created",
                "message": "Codegen task created and execution started"
            }
            
        except Exception as e:
            logger.error(f"Failed to create Codegen task: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/codegen/plans")
    async def create_plan(request: PlanCreationRequest, background_tasks: BackgroundTasks):
        """Create a new plan creation task"""
        try:
            if not codegen_manager:
                raise HTTPException(status_code=503, detail="Codegen manager not initialized")
            
            task_id = await codegen_manager.create_plan_creation_task(
                request.requirements,
                request.context
            )
            
            # Start execution in background
            background_tasks.add_task(execute_codegen_task_background, task_id)
            
            return {
                "task_id": task_id,
                "status": "created",
                "message": "Plan creation task created and execution started"
            }
            
        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/codegen/tasks")
    async def list_codegen_tasks():
        """List Codegen tasks"""
        try:
            if not codegen_manager:
                raise HTTPException(status_code=503, detail="Codegen manager not initialized")
            
            active_tasks = await codegen_manager.list_active_tasks()
            task_history = await codegen_manager.list_task_history(20)
            
            return {
                "active_tasks": active_tasks,
                "recent_tasks": task_history
            }
            
        except Exception as e:
            logger.error(f"Failed to list Codegen tasks: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/codegen/tasks/{task_id}")
    async def get_codegen_task_status(task_id: str):
        """Get Codegen task status"""
        try:
            if not codegen_manager:
                raise HTTPException(status_code=503, detail="Codegen manager not initialized")
            
            status = await codegen_manager.get_task_status(task_id)
            return status
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get Codegen task status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/codegen/tasks/{task_id}")
    async def cancel_codegen_task(task_id: str):
        """Cancel a Codegen task"""
        try:
            if not codegen_manager:
                raise HTTPException(status_code=503, detail="Codegen manager not initialized")
            
            success = await codegen_manager.cancel_task(task_id)
            
            if success:
                return {"message": "Codegen task cancelled successfully"}
            else:
                raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
                
        except Exception as e:
            logger.error(f"Failed to cancel Codegen task: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # System monitoring endpoints
    @app.get("/api/system/health")
    async def get_system_health():
        """Get detailed system health"""
        try:
            if not system_watcher:
                raise HTTPException(status_code=503, detail="System watcher not initialized")
            
            health = await system_watcher.get_detailed_health()
            return health
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/system/layers")
    async def get_layer_health():
        """Get orchestration layer health"""
        try:
            if not orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            health = await orchestrator.get_layer_health()
            return health
            
        except Exception as e:
            logger.error(f"Failed to get layer health: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        websocket_connections.append(websocket)
        
        try:
            # Send initial connection message
            await websocket.send_text(json.dumps({
                "type": "connection",
                "data": {"message": "Connected to Strands Dashboard"}
            }))
            
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle different message types
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    break
                    
        except WebSocketDisconnect:
            pass
        finally:
            if websocket in websocket_connections:
                websocket_connections.remove(websocket)
    
    return app

# Background task functions
async def execute_workflow_background(orchestration_id: str):
    """Execute workflow in background"""
    try:
        if orchestrator:
            result = await orchestrator.execute_orchestration(orchestration_id)
            
            # Broadcast completion
            await broadcast_workflow_update({
                'type': 'workflow_completed',
                'orchestration_id': orchestration_id,
                'result': result
            })
            
    except Exception as e:
        logger.error(f"Background workflow execution failed: {e}")
        
        # Broadcast error
        await broadcast_workflow_update({
            'type': 'workflow_error',
            'orchestration_id': orchestration_id,
            'error': str(e)
        })

async def execute_codegen_task_background(task_id: str):
    """Execute Codegen task in background"""
    try:
        if codegen_manager:
            result = await codegen_manager.execute_task(task_id)
            
            # Broadcast completion
            await broadcast_codegen_update({
                'type': 'task_started',
                'task_id': task_id,
                'result': result
            })
            
    except Exception as e:
        logger.error(f"Background Codegen task execution failed: {e}")
        
        # Broadcast error
        await broadcast_codegen_update({
            'type': 'task_error',
            'task_id': task_id,
            'error': str(e)
        })

async def broadcast_workflow_update(data: Dict[str, Any]):
    """Broadcast workflow update to all WebSocket clients"""
    if websocket_connections:
        message = json.dumps({
            "type": "workflow_update",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send to all connected clients
        disconnected = []
        for websocket in websocket_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            websocket_connections.remove(websocket)

async def broadcast_codegen_update(data: Dict[str, Any]):
    """Broadcast Codegen update to all WebSocket clients"""
    if websocket_connections:
        message = json.dumps({
            "type": "codegen_update",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send to all connected clients
        disconnected = []
        for websocket in websocket_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            websocket_connections.remove(websocket)

