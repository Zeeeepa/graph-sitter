"""GitHub service for project management and integration."""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import aiohttp
from github import Github
from github.Repository import Repository

from ..models.project import BranchInfo, Project, ProjectFilter, ProjectSort, ProjectStatus, PullRequestInfo
from ..utils.cache import CacheManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GitHubService:
    """Service for GitHub API interactions and project management."""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize GitHub service.
        
        Args:
            access_token: GitHub personal access token
        """
        self.access_token = access_token or os.getenv("GITHUB_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("GitHub access token is required")
            
        self.github = Github(self.access_token)
        self.cache = CacheManager()
        
    async def get_all_projects(self, 
                             organization: Optional[str] = None,
                             include_forks: bool = False,
                             include_archived: bool = False) -> List[Project]:
        """Get all GitHub projects/repositories.
        
        Args:
            organization: Organization name to filter by
            include_forks: Whether to include forked repositories
            include_archived: Whether to include archived repositories
            
        Returns:
            List of Project objects
        """
        cache_key = f"projects_{organization}_{include_forks}_{include_archived}"
        cached_projects = await self.cache.get(cache_key)
        
        if cached_projects:
            logger.info(f"Returning {len(cached_projects)} cached projects")
            return cached_projects
            
        projects = []
        
        try:
            if organization:
                org = self.github.get_organization(organization)
                repos = org.get_repos()
            else:
                repos = self.github.get_user().get_repos()
                
            for repo in repos:
                if not include_forks and repo.fork:
                    continue
                if not include_archived and repo.archived:
                    continue
                    
                project = await self._convert_repo_to_project(repo)
                projects.append(project)
                
            # Cache for 5 minutes
            await self.cache.set(cache_key, projects, ttl=300)
            logger.info(f"Retrieved {len(projects)} projects from GitHub")
            
        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            raise
            
        return projects
    
    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get a specific project by ID.
        
        Args:
            project_id: GitHub repository ID or full name (owner/repo)
            
        Returns:
            Project object or None if not found
        """
        try:
            if "/" in project_id:
                repo = self.github.get_repo(project_id)
            else:
                repo = self.github.get_repo(int(project_id))
                
            return await self._convert_repo_to_project(repo)
            
        except Exception as e:
            logger.error(f"Error fetching project {project_id}: {e}")
            return None
    
    async def get_project_branches(self, project_id: str) -> List[BranchInfo]:
        """Get all branches for a project.
        
        Args:
            project_id: GitHub repository ID or full name
            
        Returns:
            List of BranchInfo objects
        """
        cache_key = f"branches_{project_id}"
        cached_branches = await self.cache.get(cache_key)
        
        if cached_branches:
            return cached_branches
            
        try:
            repo = self.github.get_repo(project_id)
            branches = []
            
            for branch in repo.get_branches():
                branch_info = BranchInfo(
                    name=branch.name,
                    sha=branch.commit.sha,
                    is_default=(branch.name == repo.default_branch),
                    last_commit_date=branch.commit.commit.author.date,
                    last_commit_message=branch.commit.commit.message,
                )
                
                # Calculate ahead/behind counts for non-default branches
                if not branch_info.is_default:
                    try:
                        comparison = repo.compare(repo.default_branch, branch.name)
                        branch_info.ahead_by = comparison.ahead_by
                        branch_info.behind_by = comparison.behind_by
                    except Exception:
                        # Ignore comparison errors
                        pass
                        
                branches.append(branch_info)
                
            # Cache for 2 minutes
            await self.cache.set(cache_key, branches, ttl=120)
            return branches
            
        except Exception as e:
            logger.error(f"Error fetching branches for {project_id}: {e}")
            return []
    
    async def get_project_pull_requests(self, project_id: str, state: str = "open") -> List[PullRequestInfo]:
        """Get pull requests for a project.
        
        Args:
            project_id: GitHub repository ID or full name
            state: PR state (open, closed, all)
            
        Returns:
            List of PullRequestInfo objects
        """
        cache_key = f"prs_{project_id}_{state}"
        cached_prs = await self.cache.get(cache_key)
        
        if cached_prs:
            return cached_prs
            
        try:
            repo = self.github.get_repo(project_id)
            prs = []
            
            for pr in repo.get_pulls(state=state):
                pr_info = PullRequestInfo(
                    number=pr.number,
                    title=pr.title,
                    state=pr.state,
                    author=pr.user.login,
                    created_at=pr.created_at,
                    updated_at=pr.updated_at,
                    mergeable=pr.mergeable,
                    url=pr.html_url,
                )
                
                # Get check status
                try:
                    if pr.head.sha:
                        status = repo.get_commit(pr.head.sha).get_combined_status()
                        pr_info.checks_status = status.state
                except Exception:
                    # Ignore check status errors
                    pass
                    
                prs.append(pr_info)
                
            # Cache for 1 minute
            await self.cache.set(cache_key, prs, ttl=60)
            return prs
            
        except Exception as e:
            logger.error(f"Error fetching PRs for {project_id}: {e}")
            return []
    
    async def get_project_diff(self, project_id: str, base: str, head: str) -> Optional[str]:
        """Get diff between two branches/commits.
        
        Args:
            project_id: GitHub repository ID or full name
            base: Base branch/commit
            head: Head branch/commit
            
        Returns:
            Diff content or None if error
        """
        try:
            repo = self.github.get_repo(project_id)
            comparison = repo.compare(base, head)
            
            # Return simplified diff info
            return {
                "ahead_by": comparison.ahead_by,
                "behind_by": comparison.behind_by,
                "total_commits": comparison.total_commits,
                "files_changed": len(comparison.files),
                "additions": sum(f.additions for f in comparison.files),
                "deletions": sum(f.deletions for f in comparison.files),
            }
            
        except Exception as e:
            logger.error(f"Error getting diff for {project_id} ({base}...{head}): {e}")
            return None
    
    async def filter_projects(self, projects: List[Project], filters: ProjectFilter) -> List[Project]:
        """Filter projects based on criteria.
        
        Args:
            projects: List of projects to filter
            filters: Filter criteria
            
        Returns:
            Filtered list of projects
        """
        filtered = projects
        
        if filters.status:
            filtered = [p for p in filtered if p.status == filters.status]
            
        if filters.is_pinned is not None:
            filtered = [p for p in filtered if p.is_pinned == filters.is_pinned]
            
        if filters.has_requirements is not None:
            filtered = [p for p in filtered if p.has_requirements == filters.has_requirements]
            
        if filters.primary_language:
            filtered = [p for p in filtered if p.primary_language == filters.primary_language]
            
        if filters.search_query:
            query = filters.search_query.lower()
            filtered = [
                p for p in filtered 
                if query in p.name.lower() 
                or query in (p.description or "").lower()
                or any(query in topic.lower() for topic in p.topics)
            ]
            
        if filters.topics:
            filtered = [
                p for p in filtered 
                if any(topic in p.topics for topic in filters.topics)
            ]
            
        return filtered
    
    async def sort_projects(self, projects: List[Project], sort: ProjectSort) -> List[Project]:
        """Sort projects based on criteria.
        
        Args:
            projects: List of projects to sort
            sort: Sort criteria
            
        Returns:
            Sorted list of projects
        """
        try:
            reverse = not sort.ascending
            
            if sort.field == "name":
                return sorted(projects, key=lambda p: p.name.lower(), reverse=reverse)
            elif sort.field == "updated_at":
                return sorted(projects, key=lambda p: p.updated_at, reverse=reverse)
            elif sort.field == "created_at":
                return sorted(projects, key=lambda p: p.created_at, reverse=reverse)
            elif sort.field == "stars_count":
                return sorted(projects, key=lambda p: p.stars_count, reverse=reverse)
            elif sort.field == "forks_count":
                return sorted(projects, key=lambda p: p.forks_count, reverse=reverse)
            elif sort.field == "open_issues_count":
                return sorted(projects, key=lambda p: p.open_issues_count, reverse=reverse)
            else:
                # Default to updated_at
                return sorted(projects, key=lambda p: p.updated_at, reverse=reverse)
                
        except Exception as e:
            logger.error(f"Error sorting projects: {e}")
            return projects
    
    async def _convert_repo_to_project(self, repo: Repository) -> Project:
        """Convert GitHub Repository to Project model.
        
        Args:
            repo: GitHub Repository object
            
        Returns:
            Project object
        """
        # Get languages
        languages = {}
        try:
            languages = repo.get_languages()
        except Exception:
            pass
            
        # Determine primary language
        primary_language = None
        if languages:
            primary_language = max(languages.keys(), key=lambda k: languages[k])
            
        # Check for requirements file
        has_requirements = False
        requirements_path = None
        try:
            for filename in ["REQUIREMENTS.md", "requirements.md", "Requirements.md"]:
                try:
                    repo.get_contents(filename)
                    has_requirements = True
                    requirements_path = filename
                    break
                except Exception:
                    continue
        except Exception:
            pass
            
        return Project(
            id=str(repo.id),
            name=repo.name,
            full_name=repo.full_name,
            description=repo.description,
            url=repo.html_url,
            clone_url=repo.clone_url,
            status=ProjectStatus.ARCHIVED if repo.archived else ProjectStatus.ACTIVE,
            is_private=repo.private,
            is_fork=repo.fork,
            stars_count=repo.stargazers_count,
            forks_count=repo.forks_count,
            watchers_count=repo.watchers_count,
            open_issues_count=repo.open_issues_count,
            default_branch=repo.default_branch,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            pushed_at=repo.pushed_at,
            primary_language=primary_language,
            languages=languages,
            topics=list(repo.get_topics()),
            has_requirements=has_requirements,
            requirements_path=requirements_path,
        )

