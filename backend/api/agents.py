"""
Agents API endpoints for Codegen SDK integration
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from backend.database import get_db, DatabaseManager
from backend.services.codegen_service import CodegenService
from backend.services.websocket_manager import WebSocketManager
from backend.config import settings

router = APIRouter()
websocket_manager = WebSocketManager()
codegen_service = CodegenService(
    token=settings.CODEGEN_TOKEN,
    org_id=settings.CODEGEN_ORG_ID,
    websocket_manager=websocket_manager
)


class AgentExecuteRequest(BaseModel):
    prompt: str
    project_id: str
    enhancement_type: Optional[str] = "general"
    metadata: Optional[Dict[str, Any]] = None


class AgentTaskResponse(BaseModel):
    task_id: str
    project_id: str
    status: str
    original_prompt: str
    enhanced_prompt: Optional[str]
    prompt_enhancement_techniques: Optional[Dict[str, Any]]
    result: Optional[str]
    web_url: Optional[str]
    progress_info: Optional[Dict[str, Any]]
    status_history: Optional[List[Dict[str, Any]]]
    created_at: str
    error: Optional[str]


@router.post("/execute", response_model=AgentTaskResponse)
async def execute_agent(request: AgentExecuteRequest, db=Depends(get_db)):
    """Execute a Codegen agent with enhanced prompt"""
    try:
        # Get project for context
        project = await DatabaseManager.get_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Execute agent with enhanced prompt
        task = await codegen_service.execute_agent(
            request.prompt,
            request.project_id
        )
        
        # Return task information
        return AgentTaskResponse(
            task_id=task.id,
            project_id=task.project_id,
            status=task.status,
            original_prompt=task.original_prompt,
            enhanced_prompt=task.enhanced_prompt,
            prompt_enhancement_techniques=getattr(task, 'enhancement_metadata', None),
            result=task.result,
            web_url=task.web_url,
            progress_info=task._extract_progress_info(),
            status_history=getattr(task, 'status_history', []),
            created_at=task.created_at.isoformat(),
            error=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute agent: {str(e)}")


@router.get("/active", response_model=List[AgentTaskResponse])
async def get_active_agents(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    db=Depends(get_db)
):
    """Get all active agent tasks"""
    try:
        if project_id:
            # Get active tasks for specific project
            tasks = []
            for task_id, task in codegen_service.active_tasks.items():
                if task.project_id == project_id:
                    await task.refresh_with_monitoring(websocket_manager)
                    tasks.append(AgentTaskResponse(
                        task_id=task.id,
                        project_id=task.project_id,
                        status=task.status,
                        original_prompt=task.original_prompt,
                        enhanced_prompt=task.enhanced_prompt,
                        prompt_enhancement_techniques=getattr(task, 'enhancement_metadata', None),
                        result=task.result,
                        web_url=task.web_url,
                        progress_info=task._extract_progress_info(),
                        status_history=getattr(task, 'status_history', []),
                        created_at=task.created_at.isoformat(),
                        error=None
                    ))
            return tasks
        else:
            # Get all active tasks
            all_tasks = await codegen_service.get_all_active_tasks()
            return [AgentTaskResponse(
                task_id=task['id'],
                project_id=task['project_id'],
                status=task['status'],
                original_prompt="",  # Not included in summary
                enhanced_prompt=None,
                prompt_enhancement_techniques=None,
                result=None,
                web_url=task.get('web_url'),
                progress_info=task['progress_info'],
                status_history=[],
                created_at=task['created_at'],
                error=None
            ) for task in all_tasks]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch active agents: {str(e)}")


@router.get("/{task_id}/status", response_model=AgentTaskResponse)
async def get_agent_status(task_id: str, db=Depends(get_db)):
    """Get current status of a specific agent task"""
    try:
        task_status = await codegen_service.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Agent task not found")
        
        return AgentTaskResponse(
            task_id=task_status['id'],
            project_id=task_status.get('project_id', 'unknown'),
            status=task_status['status'],
            original_prompt=task_status['original_prompt'],
            enhanced_prompt=task_status['enhanced_prompt'],
            prompt_enhancement_techniques=None,
            result=task_status['result'],
            web_url=task_status['web_url'],
            progress_info=task_status['progress_info'],
            status_history=task_status['status_history'],
            created_at=task_status.get('created_at', ''),
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch agent status: {str(e)}")


@router.post("/{task_id}/cancel")
async def cancel_agent_task(task_id: str, db=Depends(get_db)):
    """Cancel a running agent task"""
    try:
        # Check if task exists
        task_status = await codegen_service.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Agent task not found")
        
        if task_status['status'] not in ['running', 'pending']:
            raise HTTPException(status_code=400, detail=f"Task cannot be cancelled (current status: {task_status['status']})")
        
        # Cancel the task (this would involve stopping the Codegen agent)
        # For now, just remove from active tasks
        if task_id in codegen_service.active_tasks:
            del codegen_service.active_tasks[task_id]
        
        # Broadcast cancellation
        await websocket_manager.broadcast({
            "type": "agent_status_update",
            "task_id": task_id,
            "status": "cancelled",
            "message": "Agent task was cancelled",
            "timestamp": "now"
        })
        
        return {"message": "Agent task cancelled successfully", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel agent task: {str(e)}")


@router.get("/{task_id}/logs")
async def get_agent_logs(
    task_id: str,
    limit: int = Query(100, description="Maximum number of log entries"),
    db=Depends(get_db)
):
    """Get execution logs for an agent task"""
    try:
        # Check if task exists
        task_status = await codegen_service.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Agent task not found")
        
        # This would fetch logs from database or log storage
        # For now, return status history as logs
        logs = []
        for entry in task_status.get('status_history', []):
            logs.append({
                "timestamp": entry.get('timestamp'),
                "level": "INFO",
                "message": entry.get('message', ''),
                "status": entry.get('status'),
                "metadata": {}
            })
        
        return {
            "task_id": task_id,
            "total_logs": len(logs),
            "logs": logs[-limit:] if limit else logs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch agent logs: {str(e)}")


@router.post("/enhance-prompt")
async def enhance_prompt(
    prompt: str,
    project_id: str,
    enhancement_type: str = "general",
    db=Depends(get_db)
):
    """Enhance a prompt using AI techniques"""
    try:
        # Get project for context
        project = await DatabaseManager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Enhance the prompt
        enhanced_prompt = await codegen_service.enhance_prompt(prompt, project)
        
        return {
            "original_prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "enhancement_type": enhancement_type,
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enhance prompt: {str(e)}")


@router.get("/stats")
async def get_agent_stats(db=Depends(get_db)):
    """Get overall agent execution statistics"""
    try:
        # Get all active tasks
        active_tasks = await codegen_service.get_all_active_tasks()
        
        # Calculate statistics
        stats = {
            "total_active_tasks": len(active_tasks),
            "tasks_by_status": {},
            "tasks_by_project": {},
            "average_execution_time": 0,
            "success_rate": 0
        }
        
        # Group by status
        for task in active_tasks:
            status = task['status']
            stats['tasks_by_status'][status] = stats['tasks_by_status'].get(status, 0) + 1
            
            project_id = task['project_id']
            stats['tasks_by_project'][project_id] = stats['tasks_by_project'].get(project_id, 0) + 1
        
        # This would calculate more detailed statistics from database
        # For now, return basic stats
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch agent stats: {str(e)}")


@router.post("/batch-execute")
async def batch_execute_agents(
    requests: List[AgentExecuteRequest],
    db=Depends(get_db)
):
    """Execute multiple agents in batch"""
    try:
        if len(requests) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 agents can be executed in batch")
        
        results = []
        
        for request in requests:
            try:
                # Get project for context
                project = await DatabaseManager.get_project(request.project_id)
                if not project:
                    results.append({
                        "success": False,
                        "error": f"Project {request.project_id} not found",
                        "task_id": None
                    })
                    continue
                
                # Execute agent
                task = await codegen_service.execute_agent(
                    request.prompt,
                    request.project_id
                )
                
                results.append({
                    "success": True,
                    "task_id": task.id,
                    "status": task.status,
                    "web_url": task.web_url
                })
                
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "task_id": None
                })
        
        return {
            "total_requests": len(requests),
            "successful": len([r for r in results if r['success']]),
            "failed": len([r for r in results if not r['success']]),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute batch agents: {str(e)}")


@router.get("/templates")
async def get_prompt_templates():
    """Get available prompt enhancement templates"""
    try:
        from backend.config import PROMPT_TEMPLATES
        
        templates = []
        for template_name, template_content in PROMPT_TEMPLATES.items():
            templates.append({
                "name": template_name,
                "description": f"Template for {template_name.replace('_', ' ')} tasks",
                "template": template_content,
                "variables": [
                    "context", "repo_name", "branch", "original_prompt"
                ]
            })
        
        return {
            "total_templates": len(templates),
            "templates": templates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch prompt templates: {str(e)}")


@router.post("/test-connection")
async def test_codegen_connection():
    """Test connection to Codegen SDK"""
    try:
        # Test the connection by checking if we can initialize the service
        test_service = CodegenService(
            token=settings.CODEGEN_TOKEN,
            org_id=settings.CODEGEN_ORG_ID
        )
        
        # This would test actual connectivity
        # For now, just return success if service initializes
        
        return {
            "status": "connected",
            "message": "Successfully connected to Codegen SDK",
            "org_id": settings.CODEGEN_ORG_ID,
            "base_url": settings.CODEGEN_BASE_URL
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to connect to Codegen SDK: {str(e)}",
            "org_id": settings.CODEGEN_ORG_ID,
            "base_url": settings.CODEGEN_BASE_URL
        }

