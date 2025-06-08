"""Project service for managing GitHub projects and user settings."""

import os
import uuid
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

from ..models import Project, UserSettings, FlowStatus


class ProjectService:
    """Service for managing projects and user settings."""
    
    def __init__(self):
        """Initialize the project service."""
        # In-memory storage for now (should be replaced with database)
        self._projects: Dict[str, Project] = {}
        self._user_settings: Optional[UserSettings] = None
    
    async def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        return list(self._projects.values())
    
    async def get_pinned_projects(self) -> List[Project]:
        """Get only pinned projects."""
        return [project for project in self._projects.values() if project.is_pinned]
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a specific project by ID."""
        return self._projects.get(project_id)
    
    async def create_project(self, repo_url: str, requirements: str = "") -> Project:
        """Create a new project from a GitHub repository URL."""
        # Parse repository information from URL
        repo_info = self._parse_repo_url(repo_url)
        if not repo_info:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        # Check if project already exists
        existing_project = self._find_project_by_repo(repo_url)
        if existing_project:
            raise ValueError(f"Project for repository {repo_url} already exists")
        
        # Create new project
        project = Project(
            id=str(uuid.uuid4()),
            name=repo_info["name"],
            repo_url=repo_url,
            owner=repo_info["owner"],
            repo_name=repo_info["name"],
            requirements=requirements,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self._projects[project.id] = project
        return project
    
    async def update_project(
        self, 
        project_id: str, 
        requirements: Optional[str] = None,
        is_pinned: Optional[bool] = None
    ) -> Optional[Project]:
        """Update a project."""
        project = self._projects.get(project_id)
        if not project:
            return None
        
        # Update fields if provided
        if requirements is not None:
            project.requirements = requirements
        
        if is_pinned is not None:
            project.is_pinned = is_pinned
        
        project.updated_at = datetime.now()
        return project
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False
    
    async def pin_project(self, project_id: str) -> Optional[Project]:
        """Pin a project to the dashboard."""
        return await self.update_project(project_id, is_pinned=True)
    
    async def unpin_project(self, project_id: str) -> Optional[Project]:
        """Unpin a project from the dashboard."""
        return await self.update_project(project_id, is_pinned=False)
    
    async def update_project_flow_status(
        self, 
        project_id: str, 
        flow_status: FlowStatus,
        progress_percentage: float = 0.0
    ) -> Optional[Project]:
        """Update project flow status and progress."""
        project = self._projects.get(project_id)
        if not project:
            return None
        
        project.flow_status = flow_status
        project.progress_percentage = progress_percentage
        project.last_activity = datetime.now()
        project.updated_at = datetime.now()
        
        return project
    
    async def get_github_repositories(self) -> List[Dict[str, Any]]:
        """Get available GitHub repositories for the user."""
        # This would integrate with GitHub API to fetch user's repositories
        # For now, return mock data
        
        # Check if GitHub token is available
        settings = await self.get_user_settings()
        if not settings.github_token:
            raise ValueError("GitHub token not configured. Please update settings.")
        
        # Mock repository data (replace with actual GitHub API call)
        mock_repos = [
            {
                "id": "repo-1",
                "name": "awesome-project",
                "full_name": "user/awesome-project",
                "url": "https://github.com/user/awesome-project",
                "description": "An awesome project for testing",
                "private": False,
                "language": "Python",
                "stars": 42,
                "forks": 7,
                "updated_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": "repo-2", 
                "name": "dashboard-ui",
                "full_name": "user/dashboard-ui",
                "url": "https://github.com/user/dashboard-ui",
                "description": "React dashboard UI components",
                "private": False,
                "language": "TypeScript",
                "stars": 15,
                "forks": 3,
                "updated_at": "2024-01-10T14:20:00Z"
            },
            {
                "id": "repo-3",
                "name": "api-backend",
                "full_name": "user/api-backend",
                "url": "https://github.com/user/api-backend",
                "description": "FastAPI backend service",
                "private": True,
                "language": "Python",
                "stars": 8,
                "forks": 1,
                "updated_at": "2024-01-12T09:15:00Z"
            }
        ]
        
        return mock_repos
    
    async def get_user_settings(self) -> UserSettings:
        """Get user settings."""
        if self._user_settings is None:
            # Load from environment variables or create default
            self._user_settings = UserSettings(
                github_token=os.getenv("GITHUB_TOKEN"),
                linear_token=os.getenv("LINEAR_TOKEN"),
                slack_token=os.getenv("SLACK_TOKEN"),
                codegen_org_id=os.getenv("CODEGEN_ORG_ID"),
                codegen_token=os.getenv("CODEGEN_TOKEN"),
                database_url=os.getenv("DATABASE_URL")
            )
        
        return self._user_settings
    
    async def update_user_settings(self, settings_data: Dict[str, Any]) -> UserSettings:
        """Update user settings."""
        current_settings = await self.get_user_settings()
        
        # Update only provided fields
        if "github_token" in settings_data:
            current_settings.github_token = settings_data["github_token"]
        
        if "linear_token" in settings_data:
            current_settings.linear_token = settings_data["linear_token"]
        
        if "slack_token" in settings_data:
            current_settings.slack_token = settings_data["slack_token"]
        
        if "codegen_org_id" in settings_data:
            current_settings.codegen_org_id = settings_data["codegen_org_id"]
        
        if "codegen_token" in settings_data:
            current_settings.codegen_token = settings_data["codegen_token"]
        
        if "database_url" in settings_data:
            current_settings.database_url = settings_data["database_url"]
        
        # In a real implementation, save to database or secure storage
        self._user_settings = current_settings
        
        return current_settings
    
    def _parse_repo_url(self, repo_url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub repository URL to extract owner and repo name."""
        try:
            # Handle different GitHub URL formats
            # https://github.com/owner/repo
            # https://github.com/owner/repo.git
            # git@github.com:owner/repo.git
            
            if repo_url.startswith("git@github.com:"):
                # SSH format: git@github.com:owner/repo.git
                path = repo_url.replace("git@github.com:", "")
                if path.endswith(".git"):
                    path = path[:-4]
                parts = path.split("/")
                if len(parts) == 2:
                    return {"owner": parts[0], "name": parts[1]}
            
            else:
                # HTTPS format
                parsed = urlparse(repo_url)
                if parsed.netloc != "github.com":
                    return None
                
                path = parsed.path.strip("/")
                if path.endswith(".git"):
                    path = path[:-4]
                
                parts = path.split("/")
                if len(parts) == 2:
                    return {"owner": parts[0], "name": parts[1]}
            
            return None
            
        except Exception:
            return None
    
    def _find_project_by_repo(self, repo_url: str) -> Optional[Project]:
        """Find an existing project by repository URL."""
        for project in self._projects.values():
            if project.repo_url == repo_url:
                return project
        return None
    
    async def search_projects(self, query: str) -> List[Project]:
        """Search projects by name or repository name."""
        query_lower = query.lower()
        results = []
        
        for project in self._projects.values():
            if (query_lower in project.name.lower() or 
                query_lower in project.repo_name.lower() or
                query_lower in project.owner.lower()):
                results.append(project)
        
        return results
    
    async def get_project_statistics(self) -> Dict[str, Any]:
        """Get project statistics for dashboard overview."""
        all_projects = list(self._projects.values())
        pinned_projects = [p for p in all_projects if p.is_pinned]
        
        # Count projects by flow status
        status_counts = {}
        for status in FlowStatus:
            status_counts[status.value] = len([
                p for p in all_projects if p.flow_status == status
            ])
        
        return {
            "total_projects": len(all_projects),
            "pinned_projects": len(pinned_projects),
            "active_flows": len([p for p in all_projects if p.flow_status in [
                FlowStatus.PLANNING, FlowStatus.RUNNING
            ]]),
            "status_breakdown": status_counts,
            "average_progress": sum(p.progress_percentage for p in all_projects) / len(all_projects) if all_projects else 0
        }

