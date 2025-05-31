"""Requirements management data models."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RequirementItem(BaseModel):
    """Individual requirement item."""
    id: str
    title: str
    description: str
    priority: str = Field(default="medium", description="Priority: low, medium, high, critical")
    status: str = Field(default="pending", description="Status: pending, in_progress, completed, cancelled")
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None


class Requirements(BaseModel):
    """Project requirements model."""
    
    project_id: str = Field(..., description="Associated project ID")
    version: str = Field(default="1.0.0", description="Requirements version")
    
    # Basic information
    title: str = Field(..., description="Requirements document title")
    description: Optional[str] = Field(None, description="Overall project description")
    
    # Requirements sections
    functional_requirements: List[RequirementItem] = Field(default_factory=list)
    non_functional_requirements: List[RequirementItem] = Field(default_factory=list)
    technical_requirements: List[RequirementItem] = Field(default_factory=list)
    business_requirements: List[RequirementItem] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    created_by: str
    last_modified_by: str
    
    # Version control
    file_path: str = Field(default="REQUIREMENTS.md", description="Path to requirements file")
    git_hash: Optional[str] = Field(None, description="Git commit hash of last update")
    
    # Approval and status
    status: str = Field(default="draft", description="Status: draft, review, approved, implemented")
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Dependencies and relationships
    dependencies: List[str] = Field(default_factory=list, description="List of dependent project IDs")
    related_issues: List[str] = Field(default_factory=list, description="Related Linear issue IDs")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RequirementsTemplate(BaseModel):
    """Template for creating new requirements."""
    name: str
    description: str
    sections: List[str]
    default_items: List[RequirementItem] = Field(default_factory=list)


class RequirementsHistory(BaseModel):
    """Requirements change history."""
    id: str
    project_id: str
    version: str
    change_type: str = Field(description="Type: created, updated, approved, implemented")
    changes: Dict = Field(default_factory=dict, description="Detailed changes")
    changed_by: str
    changed_at: datetime
    commit_hash: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

