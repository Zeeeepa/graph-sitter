"""
Projects and Repositories Models

Project management and repository tracking models that integrate with
the existing graph-sitter codebase analysis functionality.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, Session

from ..base import DatabaseModel, AuditedModel, DescriptionMixin, StatusMixin


# Define enums
PROJECT_STATUS_ENUM = ENUM(
    'active', 'inactive', 'archived', 'planning', 'development', 'testing', 'production', 'maintenance',
    name='project_status',
    create_type=True
)

REPOSITORY_TYPE_ENUM = ENUM(
    'primary', 'fork', 'mirror', 'archive', 'template',
    name='repository_type', 
    create_type=True
)


class Project(AuditedModel, DescriptionMixin, StatusMixin):
    """
    Project model for organizing repositories and development work.
    
    Provides top-level organization of repositories, teams, and development
    activities with comprehensive project lifecycle management.
    """
    __tablename__ = 'projects'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Basic information
    slug = Column(String(100), nullable=False, index=True)
    
    # Project metadata
    priority = Column(Integer, nullable=False, default=0)
    
    # Configuration and settings
    settings = Column('settings', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Ownership and team management
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    team_ids = Column('team_ids', DatabaseModel.metadata.type, nullable=False, default=list)
    
    # Project lifecycle
    started_at = Column('started_at', DatabaseModel.created_at.type, nullable=True)
    completed_at = Column('completed_at', DatabaseModel.created_at.type, nullable=True)
    archived_at = Column('archived_at', DatabaseModel.created_at.type, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    owner = relationship("User", foreign_keys=[owner_id])
    repositories = relationship("Repository", back_populates="project", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'slug', name='uq_project_org_slug'),
        Index('idx_projects_org', 'organization_id'),
        Index('idx_projects_owner', 'owner_id'),
        Index('idx_projects_status', 'status'),
        Index('idx_projects_priority', 'priority'),
        Index('idx_projects_started_at', 'started_at'),
    )
    
    def __init__(self, organization_id: str, name: str, slug: str, **kwargs):
        """Initialize project with required fields."""
        super().__init__(
            organization_id=organization_id,
            name=name,
            slug=slug,
            **kwargs
        )
    
    @property
    def active_repositories(self) -> List['Repository']:
        """Get all active repositories in the project."""
        return [r for r in self.repositories if not r.is_archived]
    
    @property
    def primary_repositories(self) -> List['Repository']:
        """Get primary repositories (not forks or mirrors)."""
        return [r for r in self.repositories if r.type == 'primary']
    
    def get_repository_by_name(self, name: str) -> Optional['Repository']:
        """Get a repository by name."""
        for repo in self.repositories:
            if repo.name == name:
                return repo
        return None
    
    def add_repository(self, session: Session, repository: 'Repository') -> None:
        """Add a repository to the project."""
        repository.project = self
        session.add(repository)
    
    def remove_repository(self, session: Session, repository: 'Repository') -> None:
        """Remove a repository from the project."""
        repository.project = None
        session.add(repository)
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Get project statistics."""
        total_repos = len(self.repositories)
        active_repos = len(self.active_repositories)
        primary_repos = len(self.primary_repositories)
        
        # Calculate total lines of code across all repositories
        total_lines = sum(r.total_lines or 0 for r in self.repositories)
        
        return {
            'total_repositories': total_repos,
            'active_repositories': active_repos,
            'primary_repositories': primary_repos,
            'archived_repositories': total_repos - active_repos,
            'total_lines_of_code': total_lines,
            'languages': self._get_language_distribution(),
            'status': self.status,
            'priority': self.priority,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def _get_language_distribution(self) -> Dict[str, int]:
        """Get language distribution across project repositories."""
        languages = {}
        for repo in self.repositories:
            if repo.language:
                languages[repo.language] = languages.get(repo.language, 0) + 1
        return languages
    
    def start_project(self) -> None:
        """Mark project as started."""
        self.status = 'development'
        self.started_at = datetime.utcnow()
    
    def complete_project(self) -> None:
        """Mark project as completed."""
        self.status = 'production'
        self.completed_at = datetime.utcnow()
    
    def archive_project(self) -> None:
        """Archive the project."""
        self.status = 'archived'
        self.archived_at = datetime.utcnow()


class Repository(AuditedModel, DescriptionMixin):
    """
    Repository model with comprehensive tracking and analysis integration.
    
    Integrates with existing graph-sitter codebase analysis functionality
    while providing enhanced metadata and configuration management.
    """
    __tablename__ = 'repositories'
    
    # Organization and project relationships
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    
    # Repository identification
    full_name = Column(String(255), nullable=False, index=True)  # org/repo format
    owner = Column(String(255), nullable=False)
    
    # Repository metadata
    language = Column(String(100), nullable=True, index=True)
    languages = Column('languages', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Repository configuration
    type = Column(REPOSITORY_TYPE_ENUM, nullable=False, default='primary')
    is_private = Column(Boolean, nullable=False, default=False)
    is_fork = Column(Boolean, nullable=False, default=False)
    is_archived = Column(Boolean, nullable=False, default=False)
    
    # Git metadata
    github_id = Column(Integer, unique=True, nullable=True, index=True)
    clone_url = Column(String(500), nullable=True)
    ssh_url = Column(String(500), nullable=True)
    default_branch = Column(String(100), nullable=False, default='main')
    
    # Repository statistics
    stars_count = Column(Integer, nullable=False, default=0)
    forks_count = Column(Integer, nullable=False, default=0)
    size_kb = Column(Integer, nullable=False, default=0)
    
    # Codebase analysis metadata
    total_files = Column(Integer, nullable=False, default=0)
    total_functions = Column(Integer, nullable=False, default=0)
    total_classes = Column(Integer, nullable=False, default=0)
    total_lines = Column(Integer, nullable=False, default=0)
    
    # Analysis configuration and timing
    analysis_config = Column('analysis_config', DatabaseModel.metadata.type, nullable=False, default=dict)
    last_analyzed_at = Column('last_analyzed_at', DatabaseModel.created_at.type, nullable=True)
    last_synced_at = Column('last_synced_at', DatabaseModel.created_at.type, nullable=True)
    
    # Configuration and settings
    settings = Column('settings', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Relationships
    organization = relationship("Organization", back_populates="repositories")
    project = relationship("Project", back_populates="repositories")
    branches = relationship("RepositoryBranch", back_populates="repository", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'full_name', name='uq_repo_org_fullname'),
        Index('idx_repositories_org', 'organization_id'),
        Index('idx_repositories_project', 'project_id'),
        Index('idx_repositories_full_name', 'full_name'),
        Index('idx_repositories_owner', 'owner'),
        Index('idx_repositories_language', 'language'),
        Index('idx_repositories_github_id', 'github_id'),
        Index('idx_repositories_type', 'type'),
        Index('idx_repositories_last_analyzed', 'last_analyzed_at'),
        Index('idx_repositories_analysis_config_gin', 'analysis_config', postgresql_using='gin'),
    )
    
    def __init__(self, organization_id: str, full_name: str, name: str, owner: str, **kwargs):
        """Initialize repository with required fields."""
        super().__init__(
            organization_id=organization_id,
            full_name=full_name,
            name=name,
            owner=owner,
            **kwargs
        )
    
    @property
    def active_branches(self) -> List['RepositoryBranch']:
        """Get all active branches."""
        return [b for b in self.branches if not b.is_deleted]
    
    @property
    def default_branch_obj(self) -> Optional['RepositoryBranch']:
        """Get the default branch object."""
        for branch in self.branches:
            if branch.name == self.default_branch:
                return branch
        return None
    
    def get_branch_by_name(self, name: str) -> Optional['RepositoryBranch']:
        """Get a branch by name."""
        for branch in self.branches:
            if branch.name == name:
                return branch
        return None
    
    def update_analysis_metadata(self, analysis_results: Dict[str, Any]) -> None:
        """Update repository with analysis results."""
        self.total_files = analysis_results.get('total_files', self.total_files)
        self.total_functions = analysis_results.get('total_functions', self.total_functions)
        self.total_classes = analysis_results.get('total_classes', self.total_classes)
        self.total_lines = analysis_results.get('total_lines', self.total_lines)
        self.languages = analysis_results.get('languages', self.languages)
        self.last_analyzed_at = datetime.utcnow()
    
    def sync_with_remote(self, remote_data: Dict[str, Any]) -> None:
        """Sync repository metadata with remote source."""
        self.description = remote_data.get('description', self.description)
        self.language = remote_data.get('language', self.language)
        self.size_kb = remote_data.get('size', self.size_kb)
        self.stars_count = remote_data.get('stargazers_count', self.stars_count)
        self.forks_count = remote_data.get('forks_count', self.forks_count)
        self.is_private = remote_data.get('private', self.is_private)
        self.is_archived = remote_data.get('archived', self.is_archived)
        self.last_synced_at = datetime.utcnow()
    
    def get_repository_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        return {
            'id': str(self.id),
            'full_name': self.full_name,
            'name': self.name,
            'owner': self.owner,
            'language': self.language,
            'languages': self.languages,
            'type': self.type,
            'is_private': self.is_private,
            'is_fork': self.is_fork,
            'is_archived': self.is_archived,
            'stars_count': self.stars_count,
            'forks_count': self.forks_count,
            'size_kb': self.size_kb,
            'total_files': self.total_files,
            'total_functions': self.total_functions,
            'total_classes': self.total_classes,
            'total_lines': self.total_lines,
            'total_branches': len(self.branches),
            'active_branches': len(self.active_branches),
            'default_branch': self.default_branch,
            'last_analyzed_at': self.last_analyzed_at.isoformat() if self.last_analyzed_at else None,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'project_id': str(self.project_id) if self.project_id else None,
            'project_name': self.project.name if self.project else None,
        }
    
    def needs_analysis(self, max_age_hours: int = 24) -> bool:
        """Check if repository needs analysis."""
        if not self.last_analyzed_at:
            return True
        
        age = datetime.utcnow() - self.last_analyzed_at
        return age.total_seconds() > (max_age_hours * 3600)


class RepositoryBranch(DatabaseModel, AuditedModel):
    """
    Repository branch tracking with commit information.
    
    Tracks individual branches within repositories for analysis
    and development workflow management.
    """
    __tablename__ = 'repository_branches'
    
    # Repository relationship
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False)
    
    # Branch information
    name = Column(String(255), nullable=False)
    commit_sha = Column(String(40), nullable=True, index=True)
    
    # Branch metadata
    is_default = Column(Boolean, nullable=False, default=False)
    is_protected = Column(Boolean, nullable=False, default=False)
    
    # Commit information
    last_commit_at = Column('last_commit_at', DatabaseModel.created_at.type, nullable=True)
    last_commit_message = Column(Text, nullable=True)
    last_commit_author = Column(String(255), nullable=True)
    
    # Analysis tracking
    last_analyzed_at = Column('last_analyzed_at', DatabaseModel.created_at.type, nullable=True)
    analysis_status = Column(String(50), nullable=False, default='pending')
    
    # Relationships
    repository = relationship("Repository", back_populates="branches")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('repository_id', 'name', name='uq_repo_branch_name'),
        Index('idx_repo_branches_repo', 'repository_id'),
        Index('idx_repo_branches_name', 'name'),
        Index('idx_repo_branches_commit', 'commit_sha'),
        Index('idx_repo_branches_default', 'repository_id', 'is_default'),
        Index('idx_repo_branches_protected', 'repository_id', 'is_protected'),
        Index('idx_repo_branches_last_commit', 'last_commit_at'),
    )
    
    def __init__(self, repository_id: str, name: str, **kwargs):
        """Initialize branch with required fields."""
        super().__init__(repository_id=repository_id, name=name, **kwargs)
    
    def update_commit_info(self, commit_sha: str, commit_data: Dict[str, Any]) -> None:
        """Update branch with latest commit information."""
        self.commit_sha = commit_sha
        self.last_commit_at = commit_data.get('committed_at')
        self.last_commit_message = commit_data.get('message')
        self.last_commit_author = commit_data.get('author', {}).get('name')
    
    def mark_as_analyzed(self, status: str = 'completed') -> None:
        """Mark branch as analyzed."""
        self.last_analyzed_at = datetime.utcnow()
        self.analysis_status = status
    
    def needs_analysis(self, max_age_hours: int = 24) -> bool:
        """Check if branch needs analysis."""
        if not self.last_analyzed_at:
            return True
        
        age = datetime.utcnow() - self.last_analyzed_at
        return age.total_seconds() > (max_age_hours * 3600)
    
    def get_branch_info(self) -> Dict[str, Any]:
        """Get branch information."""
        return {
            'id': str(self.id),
            'repository_id': str(self.repository_id),
            'name': self.name,
            'commit_sha': self.commit_sha,
            'is_default': self.is_default,
            'is_protected': self.is_protected,
            'last_commit_at': self.last_commit_at.isoformat() if self.last_commit_at else None,
            'last_commit_message': self.last_commit_message,
            'last_commit_author': self.last_commit_author,
            'last_analyzed_at': self.last_analyzed_at.isoformat() if self.last_analyzed_at else None,
            'analysis_status': self.analysis_status,
            'needs_analysis': self.needs_analysis(),
        }

