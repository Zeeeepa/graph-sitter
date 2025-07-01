"""
Direct GitHub Project Manager for Single-User Dashboard

Handles project discovery, pinning, and lifecycle management.
Integrates directly with GitHub for repository discovery and management.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from graph_sitter.shared.logging.get_logger import get_logger
from .models import DashboardProject, ProjectStatus, FlowStatus, create_project_from_github
from ..github.github import GitHub
from ..linear.linear import Linear

logger = get_logger(__name__)


class ProjectManager:
    """
    Manages project discovery, pinning, and lifecycle operations.
    
    Features:
    - GitHub repository discovery
    - Project pinning and unpinning
    - Project status management
    - Integration with Linear for project tracking
    - Simple in-memory caching for performance
    """
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.projects: Dict[str, DashboardProject] = {}
        self.github: Optional[GitHub] = None
        self.linear: Optional[Linear] = None
        self._cache_timeout = 300  # 5 minutes
        self._last_repo_fetch = None
        self._cached_repos = []
        
    async def initialize(self):
        """Initialize the project manager"""
        logger.info("Initializing ProjectManager...")
        
        # Get GitHub integration
        if self.dashboard.settings_manager.is_extension_enabled("github"):
            github_token = self.dashboard.settings_manager.get_api_credential("github")
            if github_token:
                self.github = GitHub({"api_token": github_token})
                await self.github.initialize()
                logger.info("GitHub integration initialized")
            else:
                logger.warning("GitHub token not configured")
        
        # Get Linear integration
        if self.dashboard.settings_manager.is_extension_enabled("linear"):
            linear_key = self.dashboard.settings_manager.get_api_credential("linear")
            if linear_key:
                self.linear = Linear({"api_key": linear_key})
                await self.linear.initialize()
                logger.info("Linear integration initialized")
            else:
                logger.warning("Linear API key not configured")
                
    async def discover_repositories(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Discover GitHub repositories for the authenticated user
        
        Args:
            force_refresh: Force refresh of cached repositories
            
        Returns:
            List of repository data
        """
        if not self.github:
            logger.error("GitHub integration not available")
            return []
            
        # Check cache first
        now = datetime.now()
        if (not force_refresh and 
            self._last_repo_fetch and 
            self._cached_repos and
            (now - self._last_repo_fetch).seconds < self._cache_timeout):
            logger.info("Returning cached repositories")
            return self._cached_repos
            
        try:
            logger.info("Fetching repositories from GitHub...")
            
            # Get user's repositories
            repos = await self.github.get_user_repositories()
            
            # Format repository data
            formatted_repos = []
            for repo in repos:
                formatted_repos.append({
                    "id": repo.get("id"),
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description"),
                    "private": repo.get("private", False),
                    "html_url": repo.get("html_url"),
                    "clone_url": repo.get("clone_url"),
                    "language": repo.get("language"),
                    "stargazers_count": repo.get("stargazers_count", 0),
                    "forks_count": repo.get("forks_count", 0),
                    "updated_at": repo.get("updated_at"),
                    "topics": repo.get("topics", [])
                })
                
            # Update cache
            self._cached_repos = formatted_repos
            self._last_repo_fetch = now
            
            logger.info(f"Discovered {len(formatted_repos)} repositories")
            return formatted_repos
            
        except Exception as e:
            logger.error(f"Failed to discover repositories: {e}")
            return []
            
    async def pin_project(self, repo_url: str) -> Optional[DashboardProject]:
        """
        Pin a GitHub repository as a project
        
        Args:
            repo_url: GitHub repository URL or full_name (owner/repo)
            
        Returns:
            Created project or None if failed
        """
        try:
            # Normalize repo URL
            if not repo_url.startswith("https://"):
                repo_url = f"https://github.com/{repo_url}"
                
            # Extract owner and repo name
            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) != 2:
                logger.error(f"Invalid repository URL: {repo_url}")
                return None
                
            owner, repo_name = parts[0], parts[1]
            project_id = f"{owner}_{repo_name}"
            
            # Check if already pinned
            if project_id in self.projects:
                logger.warning(f"Project already pinned: {project_id}")
                return self.projects[project_id]
                
            # Get repository data from GitHub
            if self.github:
                repo_data = await self.github.get_repository(owner, repo_name)
                if not repo_data:
                    logger.error(f"Repository not found: {owner}/{repo_name}")
                    return None
            else:
                # Create minimal repo data if GitHub not available
                repo_data = {
                    "name": repo_name,
                    "full_name": f"{owner}/{repo_name}",
                    "html_url": repo_url
                }
                
            # Create project
            project = create_project_from_github(repo_url, repo_data)
            project.pinned = True
            project.pinned_at = datetime.now()
            project.update_status(ProjectStatus.PINNED)
            
            # Store project
            self.projects[project_id] = project
            
            # Create Linear project if available
            if self.linear:
                await self._create_linear_project(project)
                
            # Emit event
            await self.dashboard.event_coordinator.emit_event(
                "project_pinned",
                "project_manager",
                project_id=project_id,
                data={"repo_url": repo_url}
            )
            
            logger.info(f"Pinned project: {project_id}")
            return project
            
        except Exception as e:
            logger.error(f"Failed to pin project {repo_url}: {e}")
            return None
            
    async def unpin_project(self, project_id: str) -> bool:
        """
        Unpin a project
        
        Args:
            project_id: Project ID to unpin
            
        Returns:
            True if successful
        """
        try:
            if project_id not in self.projects:
                logger.warning(f"Project not found: {project_id}")
                return False
                
            project = self.projects[project_id]
            project.pinned = False
            project.pinned_at = None
            project.update_status(ProjectStatus.DISCOVERED)
            
            # Emit event
            await self.dashboard.event_coordinator.emit_event(
                "project_unpinned",
                "project_manager",
                project_id=project_id
            )
            
            logger.info(f"Unpinned project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unpin project {project_id}: {e}")
            return False
            
    async def get_project(self, project_id: str) -> Optional[DashboardProject]:
        """Get a project by ID"""
        return self.projects.get(project_id)
        
    async def get_pinned_projects(self) -> List[DashboardProject]:
        """Get all pinned projects"""
        return [p for p in self.projects.values() if p.pinned]
        
    async def get_all_projects(self) -> List[DashboardProject]:
        """Get all projects"""
        return list(self.projects.values())
        
    async def update_project_status(self, project_id: str, status: ProjectStatus) -> bool:
        """Update project status"""
        try:
            if project_id not in self.projects:
                logger.warning(f"Project not found: {project_id}")
                return False
                
            project = self.projects[project_id]
            old_status = project.status
            project.update_status(status)
            
            # Emit event
            await self.dashboard.event_coordinator.emit_event(
                "project_status_changed",
                "project_manager",
                project_id=project_id,
                data={"old_status": old_status, "new_status": status}
            )
            
            logger.info(f"Updated project {project_id} status: {old_status} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update project status: {e}")
            return False
            
    async def update_flow_status(self, project_id: str, flow_status: FlowStatus) -> bool:
        """Update project flow status"""
        try:
            if project_id not in self.projects:
                logger.warning(f"Project not found: {project_id}")
                return False
                
            project = self.projects[project_id]
            old_status = project.flow_status
            project.flow_status = flow_status
            project.updated_at = datetime.now()
            
            # Emit event
            await self.dashboard.event_coordinator.emit_event(
                "project_flow_status_changed",
                "project_manager",
                project_id=project_id,
                data={"old_status": old_status, "new_status": flow_status}
            )
            
            logger.info(f"Updated project {project_id} flow status: {old_status} -> {flow_status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update flow status: {e}")
            return False
            
    async def _create_linear_project(self, project: DashboardProject):
        """Create corresponding Linear project"""
        try:
            if not self.linear:
                return
                
            # Create Linear project
            linear_project = await self.linear.create_project(
                name=project.name,
                description=f"Project for GitHub repository: {project.github_owner}/{project.github_repo}"
            )
            
            if linear_project:
                project.linear_project_id = linear_project.get("id")
                project.linear_team_id = linear_project.get("team_id")
                logger.info(f"Created Linear project for {project.project_id}")
                
        except Exception as e:
            logger.error(f"Failed to create Linear project: {e}")
            
    async def sync_with_github(self, project_id: str) -> bool:
        """Sync project data with GitHub"""
        try:
            if not self.github or project_id not in self.projects:
                return False
                
            project = self.projects[project_id]
            
            # Get latest repository data
            repo_data = await self.github.get_repository(
                project.github_owner, 
                project.github_repo
            )
            
            if repo_data:
                project.github_data = repo_data
                project.updated_at = datetime.now()
                logger.info(f"Synced project {project_id} with GitHub")
                return True
                
        except Exception as e:
            logger.error(f"Failed to sync with GitHub: {e}")
            
        return False
        
    async def get_project_statistics(self) -> Dict[str, Any]:
        """Get project statistics"""
        total_projects = len(self.projects)
        pinned_projects = len([p for p in self.projects.values() if p.pinned])
        
        status_counts = {}
        for project in self.projects.values():
            status = project.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
        flow_status_counts = {}
        for project in self.projects.values():
            status = project.flow_status.value
            flow_status_counts[status] = flow_status_counts.get(status, 0) + 1
            
        return {
            "total_projects": total_projects,
            "pinned_projects": pinned_projects,
            "status_distribution": status_counts,
            "flow_status_distribution": flow_status_counts,
            "github_connected": bool(self.github),
            "linear_connected": bool(self.linear)
        }

