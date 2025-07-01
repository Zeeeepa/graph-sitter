"""
Codebase database models for storing comprehensive codebase analysis and metadata.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    String, Text, Boolean, Integer, Float, DateTime, JSON, ForeignKey,
    Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, TimestampMixin, UUIDMixin


class CodebaseStatus(str, Enum):
    """Codebase analysis status."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    OUTDATED = "outdated"


class AnalysisType(str, Enum):
    """Types of codebase analysis."""
    FULL_SCAN = "full_scan"
    INCREMENTAL = "incremental"
    TARGETED = "targeted"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    SECURITY_SCAN = "security_scan"
    PERFORMANCE_ANALYSIS = "performance_analysis"


class CodebaseModel(BaseModel):
    """Main codebase model for storing codebase information."""
    
    __tablename__ = "codebases"
    
    # Codebase identification
    repository_url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    branch: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Codebase details
    status: Mapped[CodebaseStatus] = mapped_column(
        SQLEnum(CodebaseStatus), default=CodebaseStatus.PENDING, index=True
    )
    
    # Analysis configuration
    analysis_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    included_paths: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    excluded_paths: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Codebase statistics
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_functions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_classes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Language breakdown
    languages: Mapped[Optional[Dict[str, int]]] = mapped_column(
        JSON, nullable=True,
        comment="Language breakdown with line counts"
    )
    primary_language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Analysis timing
    analysis_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    analysis_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    analysis_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    analyses: Mapped[List["CodebaseAnalysisModel"]] = relationship(
        "CodebaseAnalysisModel", back_populates="codebase", cascade="all, delete-orphan"
    )
    metadata_entries: Mapped[List["CodebaseMetadataModel"]] = relationship(
        "CodebaseMetadataModel", back_populates="codebase", cascade="all, delete-orphan"
    )
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("repository_url", "commit_sha", name="uq_codebase_repo_commit"),
        Index("idx_codebase_status_branch", "status", "branch"),
        Index("idx_codebase_language", "primary_language"),
        Index("idx_codebase_analysis_completed", "analysis_completed_at"),
    )


class CodebaseAnalysisModel(BaseModel):
    """Model for storing detailed codebase analysis results."""
    
    __tablename__ = "codebase_analyses"
    
    # Analysis details
    analysis_type: Mapped[AnalysisType] = mapped_column(
        SQLEnum(AnalysisType), nullable=False, index=True
    )
    analyzer_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    analyzer_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Analysis results
    results: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Analysis metrics
    files_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issues_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warnings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Quality metrics
    complexity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    maintainability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_coverage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Performance metrics
    analysis_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status and timing
    status: Mapped[CodebaseStatus] = mapped_column(
        SQLEnum(CodebaseStatus), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    codebase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("codebases.id"), nullable=False, index=True
    )
    codebase: Mapped["CodebaseModel"] = relationship("CodebaseModel", back_populates="analyses")
    
    # Indexes
    __table_args__ = (
        Index("idx_analysis_codebase_type", "codebase_id", "analysis_type"),
        Index("idx_analysis_analyzer", "analyzer_name", "analyzer_version"),
        Index("idx_analysis_status_started", "status", "started_at"),
        Index("idx_analysis_quality_scores", "complexity_score", "maintainability_score"),
    )


class CodebaseMetadataModel(BaseModel):
    """Model for storing codebase metadata and extracted information."""
    
    __tablename__ = "codebase_metadata"
    
    # Metadata details
    metadata_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Type of metadata: function, class, import, dependency, etc."
    )
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    
    # Code element details
    element_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    element_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Location information
    start_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_column: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_column: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata content
    content: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Relationships and dependencies
    dependencies: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    dependents: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Quality metrics
    complexity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lines_of_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    codebase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("codebases.id"), nullable=False, index=True
    )
    codebase: Mapped["CodebaseModel"] = relationship("CodebaseModel", back_populates="metadata_entries")
    
    # Indexes
    __table_args__ = (
        Index("idx_metadata_codebase_type", "codebase_id", "metadata_type"),
        Index("idx_metadata_file_element", "file_path", "element_name"),
        Index("idx_metadata_element_type", "element_type"),
        Index("idx_metadata_location", "start_line", "end_line"),
    )

