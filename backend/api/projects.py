"""
Projects API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import uuid

from backend.database import get_db, DatabaseManager, Project
from backend.services.github_service import GitHubService
from backend.services.websocket_manager import WebSocketManager

router = APIRouter()
websocket_manager = WebSocketManager()


class ProjectCreate(BaseModel):
    repository: str
    requirements: Optional[str] = None
    plan: Optional[str] = None
    is_pinned: bool = False


class ProjectUpdate(BaseModel):
    requirements: Optional[str] = None
    plan: Optional[str] = None
    is_pinned: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    github_url: str
    owner: str
    repo_name: str
    default_branch: str
    is_pinned: bool
    requirements: Optional[str]
    plan: Optional[str]
    created_at: str
    updated_at: str


@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    pinned_only: bool = Query(False, description="Return only pinned projects"),
    db=Depends(get_db)
):
    """Get all projects"""
    try:
        if pinned_only:
            projects = await DatabaseManager.get_pinned_projects()
        else:
            # This would be implemented in DatabaseManager
            projects = []  # await DatabaseManager.get_all_projects()
        
        return [ProjectResponse(**project.__dict__) for project in projects]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")


@router.post("/", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate, db=Depends(get_db)):
    """Create a new project"""
    try:
        # Parse repository information
        if "/" not in project_data.repository:
            raise HTTPException(status_code=400, detail="Repository must be in format 'owner/repo'")
        
        owner, repo_name = project_data.repository.split("/", 1)
        
        # Generate project data
        project_dict = {
            "id": str(uuid.uuid4()),
            "name": repo_name,
            "description": f"AI-powered CI/CD for {project_data.repository}",
            "github_url": f"https://github.com/{project_data.repository}",
            "github_token": "placeholder",  # This should be handled securely
            "owner": owner,
            "repo_name": repo_name,
            "default_branch": "main",
            "is_pinned": project_data.is_pinned,
            "requirements": project_data.requirements,
            "plan": project_data.plan
        }
        
        # Create project in database
        project = await DatabaseManager.create_project(project_dict)
        
        # Broadcast project creation
        await websocket_manager.broadcast({
            "type": "project_created",
            "project": project_dict,
            "message": f"Project {repo_name} created successfully"
        })
        
        return ProjectResponse(**project.__dict__)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db=Depends(get_db)):
    """Get a specific project"""
    try:
        project = await DatabaseManager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectResponse(**project.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project: {str(e)}")


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_data: ProjectUpdate, db=Depends(get_db)):
    """Update a project"""
    try:
        # Get existing project
        project = await DatabaseManager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update fields
        update_data = {}
        if project_data.requirements is not None:
            update_data["requirements"] = project_data.requirements
        if project_data.plan is not None:
            update_data["plan"] = project_data.plan
        if project_data.is_pinned is not None:
            update_data["is_pinned"] = project_data.is_pinned
        
        # Update in database
        # updated_project = await DatabaseManager.update_project(project_id, update_data)
        
        # For now, simulate update
        for key, value in update_data.items():
            setattr(project, key, value)
        
        # Broadcast project update
        await websocket_manager.broadcast({
            "type": "project_updated",
            "project_id": project_id,
            "updates": update_data,
            "message": f"Project {project.name} updated"
        })
        
        return ProjectResponse(**project.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")


@router.delete("/{project_id}")
async def delete_project(project_id: str, db=Depends(get_db)):
    """Delete a project"""
    try:
        # Get existing project
        project = await DatabaseManager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete from database
        # await DatabaseManager.delete_project(project_id)
        
        # Broadcast project deletion
        await websocket_manager.broadcast({
            "type": "project_deleted",
            "project_id": project_id,
            "message": f"Project {project.name} deleted"
        })
        
        return {"message": "Project deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


@router.post("/{project_id}/pin")
async def pin_project(project_id: str, db=Depends(get_db)):
    """Pin a project to dashboard"""
    try:
        # Get existing project
        project = await DatabaseManager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update pin status
        # await DatabaseManager.update_project(project_id, {"is_pinned": True})
        project.is_pinned = True
        
        # Broadcast pin update
        await websocket_manager.broadcast({
            "type": "project_pinned",
            "project_id": project_id,
            "message": f"Project {project.name} pinned to dashboard"
        })
        
        return {"message": "Project pinned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pin project: {str(e)}")


@router.post("/{project_id}/unpin")
async def unpin_project(project_id: str, db=Depends(get_db)):
    """Unpin a project from dashboard"""
    try:
        # Get existing project
        project = await DatabaseManager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update pin status
        # await DatabaseManager.update_project(project_id, {"is_pinned": False})
        project.is_pinned = False
        
        # Broadcast unpin update
        await websocket_manager.broadcast({
            "type": "project_unpinned",
            "project_id": project_id,
            "message": f"Project {project.name} unpinned from dashboard"
        })
        
        return {"message": "Project unpinned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unpin project: {str(e)}")


@router.get("/{project_id}/stats")
async def get_project_stats(project_id: str, db=Depends(get_db)):
    """Get project statistics"""
    try:
        # Get project
        project = await DatabaseManager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get statistics (this would be implemented with actual database queries)
        stats = {
            "total_workflows": 0,
            "active_workflows": 0,
            "completed_workflows": 0,
            "failed_workflows": 0,
            "total_agent_tasks": 0,
            "active_agent_tasks": 0,
            "analysis_issues": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "deployments": {
                "staging": 0,
                "production": 0,
                "pr_environments": 0
            },
            "last_activity": None
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project stats: {str(e)}")


@router.post("/{project_id}/analyze")
async def analyze_project_code(project_id: str, db=Depends(get_db)):
    """Trigger code analysis for a project"""
    try:
        # Get project
        project = await DatabaseManager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # This would trigger the code analysis service
        # from backend.services.graph_sitter_service import CodeAnalysisService
        # analysis_service = CodeAnalysisService()
        # result = await analysis_service.analyze_repository(
        #     project_id, project.github_token, project.owner, project.repo_name
        # )
        
        # For now, return a placeholder
        result = {
            "status": "started",
            "message": "Code analysis started",
            "analysis_id": str(uuid.uuid4())
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start code analysis: {str(e)}")


@router.get("/{project_id}/analysis")
async def get_project_analysis(project_id: str, db=Depends(get_db)):
    """Get code analysis results for a project"""
    try:
        # Get project
        project = await DatabaseManager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # This would fetch analysis results from database
        # analysis_results = await DatabaseManager.get_analysis_results(project_id)
        
        # For now, return placeholder data
        analysis_results = []
        
        return {
            "project_id": project_id,
            "total_issues": len(analysis_results),
            "issues_by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "issues_by_type": {},
            "issues": analysis_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analysis results: {str(e)}")

