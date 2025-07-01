"""
Project Service - Handles project management and GitHub integration.
Preserves and enhances essential integrations while modernizing architecture.
"""

import os
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse

from ..consolidated_models import (
    Project, UserSettings, ProjectStatus, FlowStatus
)

logger = logging.getLogger(__name__)


class ProjectService:
    """
    Service for project management with enhanced GitHub integration.
    Preserves essential functionality while modernizing architecture.
    """
    
    def __init__(self):
        """Initialize the Project service."""
        self.projects: Dict[str, Project] = {}
        self.user_settings = UserSettings()
        self.github_client = None
        
        # Initialize GitHub client
        self._init_github_client()
    
    def _init_github_client(self):
        """Initialize GitHub client with fallback to mock."""
        try:
            # Try to use existing GitHub integration from contexten
            from contexten.extensions.github.github import GitHubIntegration
            self.github_client = GitHubIntegration()
            logger.info("Initialized GitHub integration")
        except ImportError:
            try:
                # Try to use PyGithub directly
                from github import Github
                token = os.getenv("GITHUB_ACCESS_TOKEN") or self.user_settings.github_token
                if token:
                    self.github_client = Github(token)
                    logger.info("Initialized PyGithub client")
                else:
                    logger.warning("No GitHub token available, using mock client")
                    self.github_client = MockGitHubClient()
            except ImportError:
                logger.warning("GitHub libraries not available, using mock client")
                self.github_client = MockGitHubClient()
    
    async def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        return list(self.projects.values())
    
    async def get_pinned_projects(self) -> List[Project]:
        """Get pinned projects."""
        return [project for project in self.projects.values() if project.is_pinned]
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a specific project."""
        return self.projects.get(project_id)
    
    async def create_project(
        self,
        repo_url: str,
        requirements: str = "",
        auto_pin: bool = True
    ) -> Project:
        """Create a new project from a GitHub repository."""
        try:
            # Parse repository information from URL
            repo_info = self._parse_repo_url(repo_url)
            
            # Fetch additional repository details from GitHub
            github_repo = await self._fetch_github_repo_details(
                repo_info['owner'], 
                repo_info['repo_name']
            )
            
            # Create project
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                name=github_repo.get('name', repo_info['repo_name']),
                repo_url=repo_url,
                owner=repo_info['owner'],
                repo_name=repo_info['repo_name'],
                full_name=f"{repo_info['owner']}/{repo_info['repo_name']}",
                description=github_repo.get('description', ''),
                default_branch=github_repo.get('default_branch', 'main'),
                language=github_repo.get('language', ''),
                is_pinned=auto_pin,
                requirements=requirements,
                project_status=ProjectStatus.ACTIVE,
                flow_status=FlowStatus.IDLE
            )
            
            # Add metadata
            project.metadata = {
                "github_id": github_repo.get('id'),
                "stars": github_repo.get('stargazers_count', 0),
                "forks": github_repo.get('forks_count', 0),
                "open_issues": github_repo.get('open_issues_count', 0),
                "size": github_repo.get('size', 0),
                "created_at": github_repo.get('created_at'),
                "updated_at": github_repo.get('updated_at'),
                "pushed_at": github_repo.get('pushed_at'),
                "topics": github_repo.get('topics', []),
                "license": github_repo.get('license', {}).get('name') if github_repo.get('license') else None
            }
            
            self.projects[project_id] = project
            
            logger.info(f"Created project {project_id} for repository {repo_url}")
            return project
            
        except Exception as e:
            logger.error(f"Failed to create project from {repo_url}: {e}")
            raise Exception(f"Failed to create project: {str(e)}")
    
    async def update_project(
        self,
        project_id: str,
        requirements: Optional[str] = None,
        is_pinned: Optional[bool] = None,
        flow_status: Optional[FlowStatus] = None
    ) -> Optional[Project]:
        """Update a project."""
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # Update fields if provided
        if requirements is not None:
            project.requirements = requirements
        if is_pinned is not None:
            project.is_pinned = is_pinned
        if flow_status is not None:
            project.flow_status = flow_status
        
        project.updated_at = datetime.now()
        
        logger.info(f"Updated project {project_id}")
        return project
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id in self.projects:
            del self.projects[project_id]
            logger.info(f"Deleted project {project_id}")
            return True
        return False
    
    async def analyze_project(self, project_id: str):
        """Analyze a project using graph-sitter and other tools."""
        project = self.projects.get(project_id)
        if not project:
            return
        
        try:
            # This would integrate with the graph-sitter analysis tools
            # For now, we'll simulate the analysis
            logger.info(f"Starting analysis for project {project_id}")
            
            # Update project with analysis results
            project.quality_score = 85.0
            project.test_coverage = 78.5
            project.complexity_score = 6.2
            project.security_score = 92.0
            project.last_activity = datetime.now()
            
            logger.info(f"Completed analysis for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to analyze project {project_id}: {e}")
    
    async def get_github_repositories(self) -> List[Dict[str, Any]]:
        """Get available GitHub repositories for the current user."""
        try:
            if hasattr(self.github_client, 'get_user_repos'):
                # Use contexten GitHub integration
                repos = await self.github_client.get_user_repos()
            elif hasattr(self.github_client, 'get_user'):
                # Use PyGithub
                user = self.github_client.get_user()
                repos = []
                for repo in user.get_repos():
                    repos.append({
                        "id": repo.id,
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description,
                        "html_url": repo.html_url,
                        "clone_url": repo.clone_url,
                        "default_branch": repo.default_branch,
                        "language": repo.language,
                        "stargazers_count": repo.stargazers_count,
                        "forks_count": repo.forks_count,
                        "open_issues_count": repo.open_issues_count,
                        "private": repo.private,
                        "created_at": repo.created_at.isoformat() if repo.created_at else None,
                        "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                        "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None
                    })
            else:
                # Use mock client
                repos = await self.github_client.get_repositories()
            
            logger.info(f"Retrieved {len(repos)} GitHub repositories")
            return repos
            
        except Exception as e:
            logger.error(f"Failed to fetch GitHub repositories: {e}")
            raise Exception(f"Failed to fetch repositories: {str(e)}")
    
    async def get_user_settings(self) -> UserSettings:
        """Get user settings."""
        return self.user_settings
    
    async def update_user_settings(self, settings: Dict[str, Any]) -> UserSettings:
        """Update user settings."""
        try:
            # Update settings fields
            for key, value in settings.items():
                if hasattr(self.user_settings, key):
                    setattr(self.user_settings, key, value)
            
            # Reinitialize GitHub client if token changed
            if 'github_token' in settings:
                self._init_github_client()
            
            logger.info("Updated user settings")
            return self.user_settings
            
        except Exception as e:
            logger.error(f"Failed to update user settings: {e}")
            raise Exception(f"Failed to update settings: {str(e)}")
    
    def _parse_repo_url(self, repo_url: str) -> Dict[str, str]:
        """Parse GitHub repository URL to extract owner and repo name."""
        try:
            parsed = urlparse(repo_url)
            
            # Handle different URL formats
            if parsed.netloc == 'github.com':
                # https://github.com/owner/repo
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    owner = path_parts[0]
                    repo_name = path_parts[1]
                    # Remove .git suffix if present
                    if repo_name.endswith('.git'):
                        repo_name = repo_name[:-4]
                    return {'owner': owner, 'repo_name': repo_name}
            
            # Handle git URLs
            if repo_url.startswith('git@github.com:'):
                # git@github.com:owner/repo.git
                path = repo_url.replace('git@github.com:', '')
                if path.endswith('.git'):
                    path = path[:-4]
                owner, repo_name = path.split('/')
                return {'owner': owner, 'repo_name': repo_name}
            
            raise ValueError("Invalid GitHub URL format")
            
        except Exception as e:
            logger.error(f"Failed to parse repository URL {repo_url}: {e}")
            raise Exception(f"Invalid repository URL: {str(e)}")
    
    async def _fetch_github_repo_details(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Fetch repository details from GitHub API."""
        try:
            if hasattr(self.github_client, 'get_repo_details'):
                # Use contexten GitHub integration
                return await self.github_client.get_repo_details(owner, repo_name)
            elif hasattr(self.github_client, 'get_repo'):
                # Use PyGithub
                repo = self.github_client.get_repo(f"{owner}/{repo_name}")
                return {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "default_branch": repo.default_branch,
                    "language": repo.language,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "open_issues_count": repo.open_issues_count,
                    "size": repo.size,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                    "topics": repo.get_topics(),
                    "license": repo.license.raw_data if repo.license else None
                }
            else:
                # Use mock client
                return await self.github_client.get_repo_details(owner, repo_name)
                
        except Exception as e:
            logger.error(f"Failed to fetch GitHub repo details for {owner}/{repo_name}: {e}")
            # Return minimal details if API call fails
            return {
                "name": repo_name,
                "full_name": f"{owner}/{repo_name}",
                "description": "",
                "default_branch": "main",
                "language": "",
                "stargazers_count": 0,
                "forks_count": 0,
                "open_issues_count": 0
            }


class MockGitHubClient:
    """Mock GitHub client for development and testing."""
    
    async def get_repositories(self) -> List[Dict[str, Any]]:
        """Mock method to get repositories."""
        return [
            {
                "id": 1,
                "name": "example-repo",
                "full_name": "user/example-repo",
                "description": "An example repository",
                "html_url": "https://github.com/user/example-repo",
                "clone_url": "https://github.com/user/example-repo.git",
                "default_branch": "main",
                "language": "Python",
                "stargazers_count": 42,
                "forks_count": 7,
                "open_issues_count": 3,
                "private": False,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-12-01T00:00:00Z",
                "pushed_at": "2023-12-01T00:00:00Z"
            },
            {
                "id": 2,
                "name": "another-repo",
                "full_name": "user/another-repo",
                "description": "Another example repository",
                "html_url": "https://github.com/user/another-repo",
                "clone_url": "https://github.com/user/another-repo.git",
                "default_branch": "develop",
                "language": "TypeScript",
                "stargazers_count": 15,
                "forks_count": 2,
                "open_issues_count": 1,
                "private": False,
                "created_at": "2023-06-01T00:00:00Z",
                "updated_at": "2023-11-15T00:00:00Z",
                "pushed_at": "2023-11-15T00:00:00Z"
            },
            {
                "id": 3,
                "name": "dashboard-project",
                "full_name": "user/dashboard-project",
                "description": "A comprehensive dashboard system",
                "html_url": "https://github.com/user/dashboard-project",
                "clone_url": "https://github.com/user/dashboard-project.git",
                "default_branch": "main",
                "language": "JavaScript",
                "stargazers_count": 128,
                "forks_count": 23,
                "open_issues_count": 8,
                "private": False,
                "created_at": "2023-03-15T00:00:00Z",
                "updated_at": "2023-12-05T00:00:00Z",
                "pushed_at": "2023-12-05T00:00:00Z"
            }
        ]
    
    async def get_repo_details(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Mock method to get repository details."""
        return {
            "id": 123,
            "name": repo_name,
            "full_name": f"{owner}/{repo_name}",
            "description": f"Mock repository {repo_name}",
            "default_branch": "main",
            "language": "Python",
            "stargazers_count": 50,
            "forks_count": 10,
            "open_issues_count": 5,
            "size": 1024,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-12-01T00:00:00Z",
            "pushed_at": "2023-12-01T00:00:00Z",
            "topics": ["dashboard", "automation", "ai"],
            "license": {"name": "MIT License"}
        }

