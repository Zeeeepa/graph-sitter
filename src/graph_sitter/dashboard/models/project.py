"""Project data models for the dashboard."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    PINNED = "pinned"


class BranchInfo(BaseModel):
    """Branch information model."""
    name: str
    sha: str
    is_default: bool = False
    last_commit_date: Optional[datetime] = None
    last_commit_message: Optional[str] = None
    ahead_by: int = 0
    behind_by: int = 0


class PullRequestInfo(BaseModel):
    """Pull request information model."""
    number: int
    title: str
    state: str
    author: str
    created_at: datetime
    updated_at: datetime
    mergeable: Optional[bool] = None
    checks_status: Optional[str] = None
    url: str


class Project(BaseModel):
    """Project model representing a GitHub repository."""
    
    id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: Optional[str] = Field(None, description="Project description")
    url: str = Field(..., description="GitHub repository URL")
    clone_url: str = Field(..., description="Git clone URL")
    
    # Status and metadata
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE)
    is_pinned: bool = Field(default=False)
    is_private: bool = Field(default=False)
    is_fork: bool = Field(default=False)
    
    # Repository statistics
    stars_count: int = Field(default=0)
    forks_count: int = Field(default=0)
    watchers_count: int = Field(default=0)
    open_issues_count: int = Field(default=0)
    
    # Branch and PR information
    default_branch: str = Field(default="main")
    branches: List[BranchInfo] = Field(default_factory=list)
    pull_requests: List[PullRequestInfo] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None
    
    # Language and topics
    primary_language: Optional[str] = None
    languages: Dict[str, int] = Field(default_factory=dict)
    topics: List[str] = Field(default_factory=list)
    
    # Requirements and configuration
    has_requirements: bool = Field(default=False)
    requirements_path: Optional[str] = Field(None)
    
    # Webhook configuration
    webhook_configured: bool = Field(default=False)
    webhook_events: List[str] = Field(default_factory=list)
    
    # Dashboard specific
    tab_order: int = Field(default=0)
    last_viewed: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProjectFilter(BaseModel):
    """Project filtering options."""
    status: Optional[ProjectStatus] = None
    is_pinned: Optional[bool] = None
    has_requirements: Optional[bool] = None
    primary_language: Optional[str] = None
    search_query: Optional[str] = None
    topics: List[str] = Field(default_factory=list)


class ProjectSort(BaseModel):
    """Project sorting options."""
    field: str = Field(default="updated_at", description="Field to sort by")
    ascending: bool = Field(default=False, description="Sort order")
    
    class Config:
        """Valid sort fields."""
        schema_extra = {
            "example": {
                "field": "updated_at",
                "ascending": False
            }
        }

