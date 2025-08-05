"""Projects API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from ...models.project import Project, ProjectFilter, ProjectSort, ProjectStatus
from ...services.github_service import GitHubService
from ...utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ProjectUpdateRequest(BaseModel):
    """Request model for updating project properties."""
    is_pinned: Optional[bool] = None
    status: Optional[ProjectStatus] = None
    tab_order: Optional[int] = None


class ProjectsResponse(BaseModel):
    """Response model for projects list."""
    projects: List[Project]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


def get_github_service(request: Request) -> GitHubService:
    """Dependency to get GitHub service."""
    if not hasattr(request.app.state, "github_service"):
        raise HTTPException(status_code=503, detail="GitHub service not available")
    return request.app.state.github_service


@router.get("/", response_model=ProjectsResponse)
async def get_projects(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    has_requirements: Optional[bool] = Query(None, description="Filter by requirements"),
    primary_language: Optional[str] = Query(None, description="Filter by primary language"),
    search: Optional[str] = Query(None, description="Search query"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    github_service: GitHubService = Depends(get_github_service),
):
    """Get all projects with filtering and pagination."""
    try:
        # Get configuration
        config = request.app.state.config
        
        # Fetch all projects
        projects = await github_service.get_all_projects(
            organization=config.github_organization,
            include_forks=config.github_include_forks,
            include_archived=config.github_include_archived,
        )
        
        # Apply filters
        filters = ProjectFilter(
            status=status,
            is_pinned=is_pinned,
            has_requirements=has_requirements,
            primary_language=primary_language,
            search_query=search,
        )
        
        filtered_projects = await github_service.filter_projects(projects, filters)
        
        # Apply sorting
        sort = ProjectSort(
            field=sort_by,
            ascending=(sort_order.lower() == "asc")
        )
        
        sorted_projects = await github_service.sort_projects(filtered_projects, sort)
        
        # Apply pagination
        total = len(sorted_projects)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_projects = sorted_projects[start_idx:end_idx]
        
        return ProjectsResponse(
            projects=paginated_projects,
            total=total,
            page=page,
            per_page=per_page,
            has_next=end_idx < total,
            has_prev=page > 1,
        )
        
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    github_service: GitHubService = Depends(get_github_service),
):
    """Get a specific project by ID."""
    try:
        project = await github_service.get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch project")


@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    update_data: ProjectUpdateRequest,
    github_service: GitHubService = Depends(get_github_service),
):
    """Update project properties (pinned status, tab order, etc.)."""
    try:
        project = await github_service.get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Update fields
        if update_data.is_pinned is not None:
            project.is_pinned = update_data.is_pinned
            
        if update_data.status is not None:
            project.status = update_data.status
            
        if update_data.tab_order is not None:
            project.tab_order = update_data.tab_order
            
        # In a real implementation, you'd save these changes to a database
        # For now, just return the updated project
        
        logger.info(f"Updated project {project_id}")
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project")


@router.get("/{project_id}/branches")
async def get_project_branches(
    project_id: str,
    github_service: GitHubService = Depends(get_github_service),
):
    """Get all branches for a project."""
    try:
        branches = await github_service.get_project_branches(project_id)
        return {"branches": branches}
        
    except Exception as e:
        logger.error(f"Error fetching branches for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch branches")


@router.get("/{project_id}/pull-requests")
async def get_project_pull_requests(
    project_id: str,
    state: str = Query("open", description="PR state (open, closed, all)"),
    github_service: GitHubService = Depends(get_github_service),
):
    """Get pull requests for a project."""
    try:
        prs = await github_service.get_project_pull_requests(project_id, state)
        return {"pull_requests": prs}
        
    except Exception as e:
        logger.error(f"Error fetching PRs for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pull requests")


@router.get("/{project_id}/diff")
async def get_project_diff(
    project_id: str,
    base: str = Query(..., description="Base branch/commit"),
    head: str = Query(..., description="Head branch/commit"),
    github_service: GitHubService = Depends(get_github_service),
):
    """Get diff between two branches/commits."""
    try:
        diff = await github_service.get_project_diff(project_id, base, head)
        
        if diff is None:
            raise HTTPException(status_code=404, detail="Diff not found")
            
        return {"diff": diff}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching diff for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch diff")


@router.get("/languages/list")
async def get_available_languages(
    request: Request,
    github_service: GitHubService = Depends(get_github_service),
):
    """Get list of all available programming languages across projects."""
    try:
        config = request.app.state.config
        
        # Fetch all projects to get languages
        projects = await github_service.get_all_projects(
            organization=config.github_organization,
            include_forks=config.github_include_forks,
            include_archived=config.github_include_archived,
        )
        
        # Collect all unique languages
        languages = set()
        for project in projects:
            if project.primary_language:
                languages.add(project.primary_language)
            languages.update(project.languages.keys())
                
        return {"languages": sorted(list(languages))}
        
    except Exception as e:
        logger.error(f"Error fetching languages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch languages")


@router.get("/stats/overview")
async def get_projects_stats(
    request: Request,
    github_service: GitHubService = Depends(get_github_service),
):
    """Get overview statistics for all projects."""
    try:
        config = request.app.state.config
        
        # Fetch all projects
        projects = await github_service.get_all_projects(
            organization=config.github_organization,
            include_forks=config.github_include_forks,
            include_archived=config.github_include_archived,
        )
        
        # Calculate statistics
        total_projects = len(projects)
        pinned_projects = len([p for p in projects if p.is_pinned])
        active_projects = len([p for p in projects if p.status == ProjectStatus.ACTIVE])
        archived_projects = len([p for p in projects if p.status == ProjectStatus.ARCHIVED])
        projects_with_requirements = len([p for p in projects if p.has_requirements])
        
        # Language distribution
        language_counts = {}
        for project in projects:
            if project.primary_language:
                language_counts[project.primary_language] = language_counts.get(project.primary_language, 0) + 1
                
        # Total stars and forks
        total_stars = sum(p.stars_count for p in projects)
        total_forks = sum(p.forks_count for p in projects)
        total_open_issues = sum(p.open_issues_count for p in projects)
        
        return {
            "total_projects": total_projects,
            "pinned_projects": pinned_projects,
            "active_projects": active_projects,
            "archived_projects": archived_projects,
            "projects_with_requirements": projects_with_requirements,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_open_issues": total_open_issues,
            "language_distribution": language_counts,
        }
        
    except Exception as e:
        logger.error(f"Error fetching project stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch project statistics")

