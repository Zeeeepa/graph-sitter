"""
Project Manager

Handles project discovery, pinning, and lifecycle management.
Integrates with GitHub for repository discovery and management.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from graph_sitter.shared.logging.get_logger import get_logger
from .models import DashboardProject, ProjectStatus, FlowStatus

logger = get_logger(__name__)


class ProjectManager:
    """
    Manages project discovery, pinning, and lifecycle operations.
    
    Features:
    - GitHub repository discovery
    - Project pinning and unpinning
    - Project status management
    - Integration with Linear for project tracking
    - Automated project setup and configuration
    """
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.pinned_projects: Dict[str, DashboardProject] = {}
        
    async def initialize(self):
        """Initialize the project manager"""
        logger.info("Initializing ProjectManager...")
        
        # Load any existing pinned projects from storage
        await self._load_pinned_projects()
        
    async def _load_pinned_projects(self):
        """Load pinned projects from persistent storage"""
        # In a real implementation, this would load from database
        # For now, we'll start with an empty state
        logger.info("Loading pinned projects from storage...")
        
    async def discover_github_repositories(self, organization: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discover GitHub repositories available to the user.
        
        Args:
            organization: Optional organization to filter repositories
            
        Returns:
            List of repository information dictionaries
        """
        logger.info(f"Discovering GitHub repositories (org: {organization})")
        
        try:
            # Get GitHub client from the GitHub extension
            github_extension = getattr(self.dashboard.app, 'github', None)
            if not github_extension:
                logger.error("GitHub extension not available")
                return []
            
            github_client = github_extension.client
            
            # Get repositories
            repositories = []
            
            if organization:
                # Get organization repositories
                org = github_client.get_organization(organization)
                for repo in org.get_repos():
                    repositories.append(self._format_repository_info(repo))
            else:
                # Get user repositories
                user = github_client.get_user()
                for repo in user.get_repos():
                    repositories.append(self._format_repository_info(repo))
                
                # Also get repositories from organizations the user belongs to
                for org in user.get_orgs():
                    for repo in org.get_repos():
                        repositories.append(self._format_repository_info(repo))
            
            logger.info(f"Discovered {len(repositories)} repositories")
            return repositories
            
        except Exception as e:
            logger.error(f"Error discovering GitHub repositories: {e}")
            return []
    
    def _format_repository_info(self, repo) -> Dict[str, Any]:
        """Format repository information for the dashboard"""
        return {
            "id": str(repo.id),
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description or "",
            "url": repo.html_url,
            "clone_url": repo.clone_url,
            "ssh_url": repo.ssh_url,
            "private": repo.private,
            "owner": {
                "login": repo.owner.login,
                "type": repo.owner.type
            },
            "default_branch": repo.default_branch,
            "language": repo.language,
            "topics": repo.get_topics(),
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "size": repo.size,
            "archived": repo.archived,
            "disabled": repo.disabled
        }
    
    async def pin_project(self, repository_identifier: str, **kwargs) -> DashboardProject:
        """
        Pin a project to the dashboard.
        
        Args:
            repository_identifier: Repository full name (owner/repo) or URL
            **kwargs: Additional project configuration
            
        Returns:
            Created DashboardProject instance
        """
        logger.info(f"Pinning project: {repository_identifier}")
        
        try:
            # Parse repository identifier
            if repository_identifier.startswith(('http://', 'https://')):
                # Extract owner/repo from URL
                parts = repository_identifier.rstrip('/').split('/')
                if len(parts) >= 2:
                    owner, repo_name = parts[-2], parts[-1]
                    full_name = f"{owner}/{repo_name}"
                else:
                    raise ValueError(f"Invalid repository URL: {repository_identifier}")
            else:
                # Assume it's already in owner/repo format
                full_name = repository_identifier
                owner, repo_name = full_name.split('/', 1)
            
            # Check if already pinned
            if full_name in self.pinned_projects:
                logger.info(f"Project {full_name} is already pinned")
                return self.pinned_projects[full_name]
            
            # Get repository information from GitHub
            repo_info = await self._get_repository_info(owner, repo_name)
            if not repo_info:
                raise ValueError(f"Repository {full_name} not found or not accessible")
            
            # Create dashboard project
            project = DashboardProject(
                id=full_name,
                name=kwargs.get('name', repo_info['name']),
                description=kwargs.get('description', repo_info['description']),
                repository=repo_info['url'],
                github_owner=owner,
                github_repo=repo_name,
                default_branch=repo_info['default_branch'],
                tags=kwargs.get('tags', repo_info.get('topics', [])),
                **kwargs
            )
            
            # Store the pinned project
            self.pinned_projects[full_name] = project
            
            # Emit project pinned event
            await self.dashboard.event_coordinator.emit_event(
                "project.pinned",
                project_id=project.id,
                message=f"Project {project.name} has been pinned",
                repository=project.repository,
                github_owner=owner,
                github_repo=repo_name
            )
            
            # Save to persistent storage
            await self._save_pinned_projects()
            
            logger.info(f"Successfully pinned project: {full_name}")
            return project
            
        except Exception as e:
            logger.error(f"Error pinning project {repository_identifier}: {e}")
            raise
    
    async def _get_repository_info(self, owner: str, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information from GitHub"""
        try:
            github_extension = getattr(self.dashboard.app, 'github', None)
            if not github_extension:
                return None
            
            github_client = github_extension.client
            repo = github_client.get_repo(f"{owner}/{repo_name}")
            
            return self._format_repository_info(repo)
            
        except Exception as e:
            logger.error(f"Error getting repository info for {owner}/{repo_name}: {e}")
            return None
    
    async def unpin_project(self, project_id: str) -> bool:
        """
        Unpin a project from the dashboard.
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if successfully unpinned, False otherwise
        """
        logger.info(f"Unpinning project: {project_id}")
        
        if project_id not in self.pinned_projects:
            logger.warning(f"Project {project_id} is not pinned")
            return False
        
        try:
            project = self.pinned_projects[project_id]
            
            # Stop any running workflows
            if project.flow_status == FlowStatus.RUNNING:
                await self.stop_project_flow(project_id)
            
            # Remove from pinned projects
            del self.pinned_projects[project_id]
            
            # Emit project unpinned event
            await self.dashboard.event_coordinator.emit_event(
                "project.unpinned",
                project_id=project_id,
                message=f"Project {project.name} has been unpinned"
            )
            
            # Save to persistent storage
            await self._save_pinned_projects()
            
            logger.info(f"Successfully unpinned project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unpinning project {project_id}: {e}")
            return False
    
    async def get_project(self, project_id: str) -> Optional[DashboardProject]:
        """Get a specific pinned project"""
        return self.pinned_projects.get(project_id)
    
    async def get_all_projects(self) -> List[DashboardProject]:
        """Get all pinned projects"""
        return list(self.pinned_projects.values())
    
    async def update_project(self, project_id: str, **updates) -> Optional[DashboardProject]:
        """
        Update a project's configuration.
        
        Args:
            project_id: Project identifier
            **updates: Fields to update
            
        Returns:
            Updated project or None if not found
        """
        if project_id not in self.pinned_projects:
            return None
        
        try:
            project = self.pinned_projects[project_id]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(project, field):
                    setattr(project, field, value)
            
            # Update timestamp
            project.updated_at = datetime.utcnow()
            
            # Emit project updated event
            await self.dashboard.event_coordinator.emit_event(
                "project.updated",
                project_id=project_id,
                message=f"Project {project.name} has been updated",
                updates=updates
            )
            
            # Save to persistent storage
            await self._save_pinned_projects()
            
            logger.info(f"Updated project {project_id}: {list(updates.keys())}")
            return project
            
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return None
    
    async def start_project_flow(self, project_id: str) -> bool:
        """
        Start the automated workflow for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if successfully started, False otherwise
        """
        project = await self.get_project(project_id)
        if not project:
            return False
        
        try:
            # Update project status
            project.flow_enabled = True
            project.flow_status = FlowStatus.RUNNING
            project.updated_at = datetime.utcnow()
            
            # Emit workflow started event
            await self.dashboard.event_coordinator.emit_event(
                "workflow.started",
                project_id=project_id,
                message=f"Workflow started for project {project.name}",
                project_name=project.name
            )
            
            # Save changes
            await self._save_pinned_projects()
            
            logger.info(f"Started workflow for project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting workflow for project {project_id}: {e}")
            return False
    
    async def stop_project_flow(self, project_id: str) -> bool:
        """
        Stop the automated workflow for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if successfully stopped, False otherwise
        """
        project = await self.get_project(project_id)
        if not project:
            return False
        
        try:
            # Update project status
            project.flow_enabled = False
            project.flow_status = FlowStatus.STOPPED
            project.updated_at = datetime.utcnow()
            
            # Emit workflow stopped event
            await self.dashboard.event_coordinator.emit_event(
                "workflow.stopped",
                project_id=project_id,
                message=f"Workflow stopped for project {project.name}",
                project_name=project.name
            )
            
            # Save changes
            await self._save_pinned_projects()
            
            logger.info(f"Stopped workflow for project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping workflow for project {project_id}: {e}")
            return False
    
    async def sync_project_with_github(self, project_id: str) -> bool:
        """
        Synchronize project information with GitHub.
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if successfully synchronized, False otherwise
        """
        project = await self.get_project(project_id)
        if not project:
            return False
        
        try:
            # Get latest repository information
            repo_info = await self._get_repository_info(project.github_owner, project.github_repo)
            if not repo_info:
                logger.error(f"Could not fetch repository info for {project_id}")
                return False
            
            # Update project with latest information
            updates = {
                'description': repo_info['description'],
                'default_branch': repo_info['default_branch'],
                'last_activity': datetime.utcnow()
            }
            
            # Update tags with topics if not manually set
            if not project.tags or project.tags == repo_info.get('topics', []):
                updates['tags'] = repo_info.get('topics', [])
            
            await self.update_project(project_id, **updates)
            
            logger.info(f"Synchronized project {project_id} with GitHub")
            return True
            
        except Exception as e:
            logger.error(f"Error synchronizing project {project_id} with GitHub: {e}")
            return False
    
    async def _save_pinned_projects(self):
        """Save pinned projects to persistent storage"""
        # In a real implementation, this would save to database
        logger.debug(f"Saving {len(self.pinned_projects)} pinned projects to storage")
    
    async def get_project_metrics(self, project_id: str) -> Dict[str, Any]:
        """
        Get metrics for a specific project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dictionary of project metrics
        """
        project = await self.get_project(project_id)
        if not project:
            return {}
        
        try:
            # Get repository metrics from GitHub
            repo_info = await self._get_repository_info(project.github_owner, project.github_repo)
            if not repo_info:
                return {}
            
            metrics = {
                "stars": repo_info.get("stars", 0),
                "forks": repo_info.get("forks", 0),
                "open_issues": repo_info.get("open_issues", 0),
                "size": repo_info.get("size", 0),
                "language": repo_info.get("language"),
                "last_updated": repo_info.get("updated_at"),
                "created_at": repo_info.get("created_at")
            }
            
            # Add dashboard-specific metrics
            metrics.update({
                "flow_enabled": project.flow_enabled,
                "flow_status": project.flow_status.value,
                "progress": project.progress,
                "pinned_at": project.created_at.isoformat(),
                "last_dashboard_update": project.updated_at.isoformat()
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics for project {project_id}: {e}")
            return {}

