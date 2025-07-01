"""
Enhanced API Endpoints for Advanced Dashboard Features
Provides endpoints for workflow monitoring, real-time metrics, and advanced settings.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
import logging

from ..services.workflow_service import workflow_service, WorkflowStatus, TaskStatus
from ..websocket import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["Enhanced Dashboard"])

# Workflow Management Endpoints

@router.post("/workflows")
async def create_workflow(
    project_id: str,
    project_name: str,
    workflow_type: str = "full_development",
    custom_tasks: Optional[List[Dict[str, Any]]] = None
):
    """Create a new workflow execution."""
    try:
        execution_id = await workflow_service.create_workflow(
            project_id=project_id,
            project_name=project_name,
            workflow_type=workflow_type,
            custom_tasks=custom_tasks
        )
        
        # Notify connected clients
        await websocket_manager.broadcast({
            "type": "workflow_created",
            "data": {
                "execution_id": execution_id,
                "project_id": project_id,
                "project_name": project_name,
                "workflow_type": workflow_type
            }
        })
        
        return {"execution_id": execution_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{execution_id}/start")
async def start_workflow(execution_id: str):
    """Start workflow execution."""
    try:
        success = await workflow_service.start_workflow(execution_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found or not in pending state")
        
        # Notify connected clients
        await websocket_manager.broadcast({
            "type": "workflow_started",
            "data": {"execution_id": execution_id}
        })
        
        return {"status": "started"}
        
    except Exception as e:
        logger.error(f"Failed to start workflow {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{execution_id}/pause")
async def pause_workflow(execution_id: str):
    """Pause workflow execution."""
    try:
        success = await workflow_service.pause_workflow(execution_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found or not running")
        
        await websocket_manager.broadcast({
            "type": "workflow_paused",
            "data": {"execution_id": execution_id}
        })
        
        return {"status": "paused"}
        
    except Exception as e:
        logger.error(f"Failed to pause workflow {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{execution_id}/resume")
async def resume_workflow(execution_id: str):
    """Resume paused workflow."""
    try:
        success = await workflow_service.resume_workflow(execution_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found or not paused")
        
        await websocket_manager.broadcast({
            "type": "workflow_resumed",
            "data": {"execution_id": execution_id}
        })
        
        return {"status": "resumed"}
        
    except Exception as e:
        logger.error(f"Failed to resume workflow {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{execution_id}/cancel")
async def cancel_workflow(execution_id: str):
    """Cancel workflow execution."""
    try:
        success = await workflow_service.cancel_workflow(execution_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        await websocket_manager.broadcast({
            "type": "workflow_cancelled",
            "data": {"execution_id": execution_id}
        })
        
        return {"status": "cancelled"}
        
    except Exception as e:
        logger.error(f"Failed to cancel workflow {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{execution_id}")
async def get_workflow(execution_id: str):
    """Get workflow execution details."""
    workflow = workflow_service.get_workflow(execution_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        "id": workflow.id,
        "project_id": workflow.project_id,
        "project_name": workflow.project_name,
        "workflow_type": workflow.workflow_type,
        "status": workflow.status.value,
        "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
        "end_time": workflow.end_time.isoformat() if workflow.end_time else None,
        "progress": workflow.progress,
        "total_steps": workflow.total_steps,
        "completed_steps": workflow.completed_steps,
        "tasks": [
            {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "status": task.status.value,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "duration": task.duration,
                "logs": task.logs,
                "error": task.error,
                "dependencies": task.dependencies
            }
            for task in workflow.tasks
        ],
        "metadata": workflow.metadata
    }

@router.get("/workflows")
async def get_workflows(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20
):
    """Get workflows with optional filtering."""
    if project_id:
        workflows = workflow_service.get_workflows_for_project(project_id)
    else:
        workflows = workflow_service.get_recent_workflows(limit)
    
    # Filter by status if provided
    if status:
        try:
            status_enum = WorkflowStatus(status)
            workflows = [w for w in workflows if w.status == status_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    return [
        {
            "id": w.id,
            "project_id": w.project_id,
            "project_name": w.project_name,
            "workflow_type": w.workflow_type,
            "status": w.status.value,
            "start_time": w.start_time.isoformat() if w.start_time else None,
            "end_time": w.end_time.isoformat() if w.end_time else None,
            "progress": w.progress,
            "total_steps": w.total_steps,
            "completed_steps": w.completed_steps
        }
        for w in workflows
    ]

# Real-time Metrics Endpoints

@router.get("/metrics/dashboard")
async def get_dashboard_metrics():
    """Get real-time dashboard metrics."""
    workflow_metrics = workflow_service.get_workflow_metrics()
    
    # Mock additional metrics (in real implementation, these would come from various services)
    current_time = datetime.now()
    
    metrics = {
        "projects": {
            "total": 12,
            "active": 8,
            "completed": 24,
            "change": 2
        },
        "pull_requests": {
            "open": 8,
            "merged_today": 5,
            "change": -1
        },
        "issues": {
            "open": 15,
            "resolved_today": 7,
            "change": 3
        },
        "workflows": {
            "active": workflow_metrics["active_workflows"],
            "completed_today": workflow_metrics["completed_workflows"],
            "success_rate": workflow_metrics["success_rate"]
        },
        "performance": {
            "avg_response_time": "2.3h",
            "code_quality_score": 94,
            "test_coverage": 87
        },
        "last_updated": current_time.isoformat()
    }
    
    return metrics

@router.get("/metrics/activity")
async def get_activity_feed(limit: int = 20):
    """Get recent activity feed."""
    # Mock activity data (in real implementation, this would aggregate from various sources)
    activities = [
        {
            "id": "act-1",
            "type": "workflow",
            "title": "Workflow completed",
            "description": "Material-UI Dashboard Enhancement",
            "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "status": "success",
            "user": "codegen-bot",
            "metadata": {"project": "Graph Sitter Dashboard"}
        },
        {
            "id": "act-2",
            "type": "pr",
            "title": "PR #234 merged",
            "description": "Material-UI Dashboard Upgrade",
            "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "status": "success",
            "user": "codegen-bot",
            "metadata": {"pr_number": 234}
        },
        {
            "id": "act-3",
            "type": "issue",
            "title": "Issue created",
            "description": "Implement real-time monitoring",
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "status": "pending",
            "user": "developer",
            "metadata": {"issue_number": 156}
        },
        {
            "id": "act-4",
            "type": "deployment",
            "title": "Deployment started",
            "description": "Dashboard v2.0 to staging",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "status": "running",
            "user": "ci-cd",
            "metadata": {"environment": "staging"}
        }
    ]
    
    return activities[:limit]

# Advanced Settings Endpoints

@router.get("/settings")
async def get_settings():
    """Get current dashboard settings."""
    # Mock settings (in real implementation, these would be stored in database)
    settings = {
        "workflow": {
            "auto_execute_workflows": True,
            "parallel_execution": False,
            "max_concurrent_tasks": 3,
            "retry_failed_tasks": True,
            "max_retries": 3,
            "task_timeout": 30
        },
        "notifications": {
            "email_notifications": True,
            "slack_notifications": True,
            "webhook_notifications": False,
            "notification_level": "important"
        },
        "quality_gates": {
            "enable_code_review": True,
            "enable_testing": True,
            "enable_security": True,
            "min_code_coverage": 80,
            "max_complexity": 10
        },
        "advanced": {
            "enable_ai_assistance": True,
            "enable_predictive_analysis": False,
            "enable_auto_optimization": True,
            "data_retention_days": 90
        }
    }
    
    return settings

@router.post("/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update dashboard settings."""
    # In real implementation, validate and store settings in database
    logger.info(f"Updating settings: {settings}")
    
    # Notify connected clients about settings change
    await websocket_manager.broadcast({
        "type": "settings_updated",
        "data": {"timestamp": datetime.now().isoformat()}
    })
    
    return {"status": "updated", "timestamp": datetime.now().isoformat()}

@router.post("/settings/test-connection")
async def test_service_connection(service: str, credentials: Dict[str, str]):
    """Test connection to external service."""
    # Mock connection test
    await asyncio.sleep(1)  # Simulate network delay
    
    # In real implementation, test actual service connections
    success = True  # Mock success
    
    if success:
        return {
            "status": "success",
            "message": f"Successfully connected to {service}",
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "status": "error",
            "message": f"Failed to connect to {service}",
            "timestamp": datetime.now().isoformat()
        }

# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe":
                # Subscribe to specific updates
                await websocket.send_text(json.dumps({
                    "type": "subscription_confirmed",
                    "data": {"subscribed_to": message.get("topics", [])}
                }))
            elif message.get("type") == "ping":
                # Respond to ping
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "workflow_service": "operational",
            "websocket_manager": "operational",
            "database": "operational"  # Mock status
        },
        "metrics": {
            "active_workflows": len(workflow_service.get_active_workflows()),
            "connected_clients": len(websocket_manager.active_connections)
        }
    }

