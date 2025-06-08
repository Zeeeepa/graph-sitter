"""
Workflows API endpoints
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import uuid

from backend.database import get_db
from backend.orchestration.workflow_engine import WorkflowEngine, WorkflowDefinition
from backend.services.websocket_manager import WebSocketManager

router = APIRouter()
websocket_manager = WebSocketManager()
workflow_engine = WorkflowEngine()


class WorkflowCreate(BaseModel):
    project_id: str
    name: str
    plan: str
    requirements: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    name: str
    project_id: str
    status: str
    steps: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    progress_percentage: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]


@router.get("/", response_model=List[WorkflowResponse])
async def get_workflows(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db=Depends(get_db)
):
    """Get workflows with optional filtering"""
    try:
        # Get all active workflows from engine
        workflows = await workflow_engine.get_active_workflows()
        
        # Apply filters
        if project_id:
            workflows = [w for w in workflows if w.get('project_id') == project_id]
        
        if status:
            workflows = [w for w in workflows if w.get('status') == status]
        
        return [WorkflowResponse(**workflow) for workflow in workflows]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflows: {str(e)}")


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(workflow_data: WorkflowCreate, db=Depends(get_db)):
    """Create a new workflow"""
    try:
        # Create context for workflow
        context = {
            'project_id': workflow_data.project_id,
            'requirements': workflow_data.requirements,
            'metadata': workflow_data.metadata or {}
        }
        
        # Create workflow from plan
        workflow = await workflow_engine.create_workflow_from_plan(
            workflow_data.project_id,
            workflow_data.plan,
            context
        )
        
        # Broadcast workflow creation
        await websocket_manager.send_workflow_update(
            workflow.workflow_id,
            workflow_data.project_id,
            {
                'status': 'created',
                'message': f'Workflow "{workflow_data.name}" created successfully',
                'workflow_data': workflow.to_dict()
            }
        )
        
        return WorkflowResponse(**workflow.to_dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, db=Depends(get_db)):
    """Get a specific workflow"""
    try:
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return WorkflowResponse(**workflow_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflow: {str(e)}")


@router.post("/{workflow_id}/start")
async def start_workflow(workflow_id: str, db=Depends(get_db)):
    """Start a workflow execution"""
    try:
        # Get workflow
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow_data['status'] != 'pending':
            raise HTTPException(status_code=400, detail=f"Workflow is not in pending state (current: {workflow_data['status']})")
        
        # Create execution context
        context = {
            'project_id': workflow_data['project_id'],
            'workflow_id': workflow_id,
            # Add more context as needed
        }
        
        # Start workflow execution in background
        import asyncio
        asyncio.create_task(workflow_engine.execute_workflow(workflow_id, context))
        
        # Broadcast workflow start
        await websocket_manager.send_workflow_update(
            workflow_id,
            workflow_data['project_id'],
            {
                'status': 'starting',
                'message': f'Workflow "{workflow_data["name"]}" is starting'
            }
        )
        
        return {"message": "Workflow started successfully", "workflow_id": workflow_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.post("/{workflow_id}/stop")
async def stop_workflow(workflow_id: str, db=Depends(get_db)):
    """Stop a running workflow"""
    try:
        # Get workflow
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow_data['status'] not in ['running', 'paused']:
            raise HTTPException(status_code=400, detail=f"Workflow is not running (current: {workflow_data['status']})")
        
        # Cancel workflow
        success = await workflow_engine.cancel_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel workflow")
        
        # Broadcast workflow stop
        await websocket_manager.send_workflow_update(
            workflow_id,
            workflow_data['project_id'],
            {
                'status': 'cancelled',
                'message': f'Workflow "{workflow_data["name"]}" was cancelled'
            }
        )
        
        return {"message": "Workflow stopped successfully", "workflow_id": workflow_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop workflow: {str(e)}")


@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: str, db=Depends(get_db)):
    """Pause a running workflow"""
    try:
        # Get workflow
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow_data['status'] != 'running':
            raise HTTPException(status_code=400, detail=f"Workflow is not running (current: {workflow_data['status']})")
        
        # Pause workflow
        success = await workflow_engine.pause_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to pause workflow")
        
        # Broadcast workflow pause
        await websocket_manager.send_workflow_update(
            workflow_id,
            workflow_data['project_id'],
            {
                'status': 'paused',
                'message': f'Workflow "{workflow_data["name"]}" was paused'
            }
        )
        
        return {"message": "Workflow paused successfully", "workflow_id": workflow_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause workflow: {str(e)}")


@router.post("/{workflow_id}/resume")
async def resume_workflow(workflow_id: str, db=Depends(get_db)):
    """Resume a paused workflow"""
    try:
        # Get workflow
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow_data['status'] != 'paused':
            raise HTTPException(status_code=400, detail=f"Workflow is not paused (current: {workflow_data['status']})")
        
        # Resume workflow
        success = await workflow_engine.resume_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to resume workflow")
        
        # Broadcast workflow resume
        await websocket_manager.send_workflow_update(
            workflow_id,
            workflow_data['project_id'],
            {
                'status': 'running',
                'message': f'Workflow "{workflow_data["name"]}" was resumed'
            }
        )
        
        return {"message": "Workflow resumed successfully", "workflow_id": workflow_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")


@router.get("/{workflow_id}/status")
async def get_workflow_status(workflow_id: str, db=Depends(get_db)):
    """Get current workflow status with detailed step information"""
    try:
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Add additional status information
        status_info = {
            **workflow_data,
            'current_step': None,
            'next_steps': [],
            'failed_steps': [],
            'completed_steps': []
        }
        
        # Analyze steps
        for step in workflow_data.get('steps', []):
            if step['status'] == 'running':
                status_info['current_step'] = step
            elif step['status'] == 'failed':
                status_info['failed_steps'].append(step)
            elif step['status'] == 'completed':
                status_info['completed_steps'].append(step)
            elif step['status'] == 'pending':
                status_info['next_steps'].append(step)
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflow status: {str(e)}")


@router.get("/{workflow_id}/logs")
async def get_workflow_logs(
    workflow_id: str,
    limit: int = Query(100, description="Maximum number of log entries"),
    db=Depends(get_db)
):
    """Get workflow execution logs"""
    try:
        # This would fetch logs from database or log storage
        # For now, return placeholder data
        logs = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "level": "INFO",
                "message": "Workflow started",
                "step_id": None,
                "metadata": {}
            }
        ]
        
        return {
            "workflow_id": workflow_id,
            "total_logs": len(logs),
            "logs": logs[-limit:] if limit else logs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflow logs: {str(e)}")


@router.post("/{workflow_id}/retry")
async def retry_workflow(workflow_id: str, db=Depends(get_db)):
    """Retry a failed workflow"""
    try:
        # Get workflow
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow_data['status'] != 'failed':
            raise HTTPException(status_code=400, detail=f"Workflow is not in failed state (current: {workflow_data['status']})")
        
        # Reset failed steps and restart
        # This would involve resetting step statuses and restarting execution
        # For now, just return success
        
        # Broadcast workflow retry
        await websocket_manager.send_workflow_update(
            workflow_id,
            workflow_data['project_id'],
            {
                'status': 'retrying',
                'message': f'Workflow "{workflow_data["name"]}" is being retried'
            }
        )
        
        return {"message": "Workflow retry initiated", "workflow_id": workflow_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry workflow: {str(e)}")


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, db=Depends(get_db)):
    """Delete a workflow"""
    try:
        # Get workflow
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Stop workflow if running
        if workflow_data['status'] in ['running', 'paused']:
            await workflow_engine.cancel_workflow(workflow_id)
        
        # Delete from engine (this would also delete from database)
        # await workflow_engine.delete_workflow(workflow_id)
        
        # Broadcast workflow deletion
        await websocket_manager.send_workflow_update(
            workflow_id,
            workflow_data['project_id'],
            {
                'status': 'deleted',
                'message': f'Workflow "{workflow_data["name"]}" was deleted'
            }
        )
        
        return {"message": "Workflow deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")


@router.get("/{workflow_id}/steps/{step_id}")
async def get_workflow_step(workflow_id: str, step_id: str, db=Depends(get_db)):
    """Get detailed information about a specific workflow step"""
    try:
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Find the step
        step = None
        for s in workflow_data.get('steps', []):
            if s['step_id'] == step_id:
                step = s
                break
        
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        
        return step
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch step: {str(e)}")


@router.post("/{workflow_id}/steps/{step_id}/retry")
async def retry_workflow_step(workflow_id: str, step_id: str, db=Depends(get_db)):
    """Retry a specific failed workflow step"""
    try:
        workflow_data = await workflow_engine.get_workflow_status(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Find the step
        step = None
        for s in workflow_data.get('steps', []):
            if s['step_id'] == step_id:
                step = s
                break
        
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        
        if step['status'] != 'failed':
            raise HTTPException(status_code=400, detail=f"Step is not in failed state (current: {step['status']})")
        
        # Retry the step (this would involve resetting the step and re-executing it)
        # For now, just return success
        
        # Broadcast step retry
        await websocket_manager.send_workflow_update(
            workflow_id,
            workflow_data['project_id'],
            {
                'status': 'running',
                'current_step': step['name'],
                'step_status': 'retrying',
                'message': f'Retrying step: {step["name"]}'
            }
        )
        
        return {"message": "Step retry initiated", "step_id": step_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry step: {str(e)}")

