"""
Project database models for storing project context and repository management.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    String, Text, Boolean, DateTime, JSON, ForeignKey, Integer,
    Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, TimestampMixin, UUIDMixin


class ProjectStatus(str, Enum):
    """Project status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    MAINTENANCE = "maintenance"


class RepositoryProvider(str, Enum):
    """Repository hosting providers."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"
    LOCAL = "local"


class ProjectModel(BaseModel):
    """Main project model for storing project information."""
    
    __tablename__ = "projects"
    
    # Project identification
    slug: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True,
        comment="URL-friendly project identifier"
    )
    
    # Project details
    full_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus), default=ProjectStatus.ACTIVE, index=True
    )
    
    # Project configuration
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    programming_languages: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    frameworks: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Project settings
    auto_deploy_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    continuous_learning_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    analytics_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Team and ownership
    owner_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    team_members: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Project metrics
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    
    # Relationships
    repositories: Mapped[List["RepositoryModel"]] = relationship(
        "RepositoryModel", back_populates="project", cascade="all, delete-orphan"
    )
    configurations: Mapped[List["ProjectConfigModel"]] = relationship(
        "ProjectConfigModel", back_populates="project", cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_project_status_owner", "status", "owner_id"),
        Index("idx_project_last_activity", "last_activity_at"),
    )


class RepositoryModel(BaseModel):
    """Model for storing repository information."""
    
    __tablename__ = "repositories"
    
    # Repository identification
    provider: Mapped[RepositoryProvider] = mapped_column(
        SQLEnum(RepositoryProvider), nullable=False, index=True
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(
        String(500), nullable=False, index=True,
        comment="Full repository name (owner/repo)"
    )
    
    # Repository details
    clone_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    ssh_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    
    # Repository status
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fork: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Repository metadata
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    topics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Repository statistics
    stars_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_issues_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Sync information
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    last_commit_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    
    # Relationships
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="repositories")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("provider", "full_name", name="uq_repository_provider_fullname"),
        Index("idx_repository_provider_owner", "provider", "owner"),
        Index("idx_repository_language", "language"),
        Index("idx_repository_last_synced", "last_synced_at"),
    )


class ProjectConfigModel(BaseModel):
    """Model for storing project-specific configurations."""
    
    __tablename__ = "project_configs"
    
    # Configuration details
    config_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Type of configuration: ci_cd, deployment, testing, etc."
    )
    config_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    config_value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Configuration metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    environment: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True,
        comment="Environment: development, staging, production"
    )
    
    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    previous_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="configurations")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint(
            "project_id", "config_type", "config_key", "environment",
            name="uq_project_config_key"
        ),
        Index("idx_config_type_active", "config_type", "is_active"),
        Index("idx_config_environment", "environment"),
    )
