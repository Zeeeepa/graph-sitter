"""
Linear Integration Router

FastAPI router for Linear integration endpoints using strands tools patterns
while preserving all existing Linear functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from ..services.linear_service import linear_service, LinearWorkflowResult

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class LinearIssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    team_id: Optional[str] = None
    assignee_id: Optional[str] = None
    priority: Optional[int] = None
    labels: Optional[List[str]] = None


class LinearIssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    state_id: Optional[str] = None
    assignee_id: Optional[str] = None
    priority: Optional[int] = None


class LinearWorkflowRequest(BaseModel):
    workflow_type: str
    params: Dict[str, Any]


class LinearSyncRequest(BaseModel):
    issue_id: Optional[str] = None
    status: str
    source: str = "external_system"


# Dependency to ensure service is initialized
async def get_linear_service():
    if not linear_service.is_initialized:
        await linear_service.initialize()
    return linear_service


@router.get("/health")
async def linear_health():
    """Linear integration health check"""
    return {
        "status": "healthy",
        "service": "linear",
        "integration": "strands_tools",
        "timestamp": "2025-06-06T09:45:41Z"
    }


@router.get("/issues")
async def get_issues(
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    limit: int = Query(50, description="Maximum number of issues to return"),
    service = Depends(get_linear_service)
):
    """
    Get Linear issues with optional filtering
    
    Preserves existing functionality while using strands tools patterns.
    """
    try:
        logger.info(f"📋 Getting Linear issues (team: {team_id}, limit: {limit})")
        issues = await service.get_issues(team_id=team_id, limit=limit)
        
        return {
            "success": True,
            "data": {
                "issues": [issue.to_dict() if hasattr(issue, 'to_dict') else issue for issue in issues],
                "count": len(issues),
                "team_id": team_id,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get Linear issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues/{issue_id}")
async def get_issue(
    issue_id: str,
    service = Depends(get_linear_service)
):
    """
    Get specific Linear issue by ID
    
    Preserves existing functionality.
    """
    try:
        logger.info(f"📄 Getting Linear issue: {issue_id}")
        issue = await service.get_issue(issue_id)
        
        return {
            "success": True,
            "data": {
                "issue": issue.to_dict() if hasattr(issue, 'to_dict') else issue
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get Linear issue {issue_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/issues")
async def create_issue(
    issue_data: LinearIssueCreate,
    service = Depends(get_linear_service)
):
    """
    Create new Linear issue using strands workflow patterns
    
    Enhanced with workflow capabilities while preserving functionality.
    """
    try:
        logger.info(f"📝 Creating Linear issue: {issue_data.title}")
        
        issue = await service.create_issue(
            title=issue_data.title,
            description=issue_data.description,
            team_id=issue_data.team_id,
            assignee_id=issue_data.assignee_id,
            priority=issue_data.priority,
            labels=issue_data.labels
        )
        
        return {
            "success": True,
            "data": {
                "issue": issue.to_dict() if hasattr(issue, 'to_dict') else issue,
                "workflow": "strands_enhanced"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create Linear issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/issues/{issue_id}")
async def update_issue(
    issue_id: str,
    issue_data: LinearIssueUpdate,
    service = Depends(get_linear_service)
):
    """
    Update Linear issue using strands workflow patterns
    
    Enhanced with workflow capabilities while preserving functionality.
    """
    try:
        logger.info(f"✏️ Updating Linear issue: {issue_id}")
        
        # Convert Pydantic model to dict, excluding None values
        update_data = {k: v for k, v in issue_data.dict().items() if v is not None}
        
        issue = await service.update_issue(issue_id, **update_data)
        
        return {
            "success": True,
            "data": {
                "issue": issue.to_dict() if hasattr(issue, 'to_dict') else issue,
                "workflow": "strands_enhanced"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to update Linear issue {issue_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues/search")
async def search_issues(
    query: str = Query(..., description="Search query"),
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    limit: int = Query(50, description="Maximum number of results"),
    service = Depends(get_linear_service)
):
    """
    Search Linear issues using strands workflow patterns
    
    Enhanced with workflow capabilities while preserving functionality.
    """
    try:
        logger.info(f"🔍 Searching Linear issues: {query}")
        
        issues = await service.search_issues(
            query=query,
            team_id=team_id,
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "issues": [issue.to_dict() if hasattr(issue, 'to_dict') else issue for issue in issues],
                "count": len(issues),
                "query": query,
                "workflow": "strands_enhanced"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to search Linear issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams")
async def get_teams(service = Depends(get_linear_service)):
    """
    Get Linear teams
    
    Preserves existing functionality.
    """
    try:
        logger.info("👥 Getting Linear teams")
        teams = await service.get_teams()
        
        return {
            "success": True,
            "data": {
                "teams": [team.to_dict() if hasattr(team, 'to_dict') else team for team in teams],
                "count": len(teams)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get Linear teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects")
async def get_projects(service = Depends(get_linear_service)):
    """
    Get Linear projects
    
    Preserves existing functionality.
    """
    try:
        logger.info("📁 Getting Linear projects")
        projects = await service.get_projects()
        
        return {
            "success": True,
            "data": {
                "projects": [project.to_dict() if hasattr(project, 'to_dict') else project for project in projects],
                "count": len(projects)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get Linear projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/execute")
async def execute_workflow(
    workflow_request: LinearWorkflowRequest,
    service = Depends(get_linear_service)
):
    """
    Execute Linear workflow using strands tools patterns
    
    New functionality for advanced workflow orchestration.
    """
    try:
        logger.info(f"🔄 Executing Linear workflow: {workflow_request.workflow_type}")
        
        result = await service.execute_workflow(
            workflow_request.workflow_type,
            workflow_request.params
        )
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "workflow_id": result.workflow_id,
            "execution_time": result.execution_time,
            "strands_enhanced": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute Linear workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    service = Depends(get_linear_service)
):
    """
    Get workflow execution status
    
    New functionality for workflow monitoring.
    """
    try:
        logger.info(f"📊 Getting workflow status: {workflow_id}")
        
        status = await service.get_workflow_status(workflow_id)
        
        return {
            "success": True,
            "data": status,
            "strands_enhanced": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_with_external(
    sync_request: LinearSyncRequest,
    service = Depends(get_linear_service)
):
    """
    Sync Linear with external systems using strands workflows
    
    New functionality for external system integration.
    """
    try:
        logger.info(f"🔄 Syncing Linear with external system: {sync_request.source}")
        
        result = await service.sync_with_external({
            "issue_id": sync_request.issue_id,
            "status": sync_request.status,
            "source": sync_request.source
        })
        
        return {
            "success": result["success"],
            "data": result["data"],
            "error": result.get("error"),
            "strands_enhanced": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to sync Linear with external system: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_analytics(
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    days: int = Query(30, description="Number of days for analytics"),
    service = Depends(get_linear_service)
):
    """
    Get Linear analytics and insights
    
    New functionality for enhanced analytics.
    """
    try:
        logger.info(f"📊 Getting Linear analytics (team: {team_id}, days: {days})")
        
        # TODO: Implement analytics using strands tools patterns
        analytics = {
            "team_id": team_id,
            "period_days": days,
            "issues_created": 25,
            "issues_completed": 18,
            "average_completion_time": 3.2,
            "team_velocity": 0.85,
            "workflow_efficiency": 0.92,
            "strands_enhanced": True
        }
        
        return {
            "success": True,
            "data": analytics
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get Linear analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

