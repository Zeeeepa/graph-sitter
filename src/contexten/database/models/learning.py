"""
Learning database models for storing patterns and continuous improvement data.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    String, Text, Boolean, Integer, Float, DateTime, JSON, ForeignKey,
    Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, TimestampMixin, UUIDMixin


class LearningType(str, Enum):
    """Types of learning data."""
    PATTERN_RECOGNITION = "pattern_recognition"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ERROR_ANALYSIS = "error_analysis"
    SUCCESS_ANALYSIS = "success_analysis"
    USER_BEHAVIOR = "user_behavior"
    CODE_QUALITY = "code_quality"
    SYSTEM_IMPROVEMENT = "system_improvement"


class PatternType(str, Enum):
    """Types of patterns identified."""
    CODE_PATTERN = "code_pattern"
    ERROR_PATTERN = "error_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    USER_PATTERN = "user_pattern"
    WORKFLOW_PATTERN = "workflow_pattern"
    INTEGRATION_PATTERN = "integration_pattern"


class FeedbackType(str, Enum):
    """Types of feedback."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


class LearningStatus(str, Enum):
    """Learning data processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    APPLIED = "applied"
    REJECTED = "rejected"


class LearningModel(BaseModel):
    """Main learning model for storing continuous improvement data."""
    
    __tablename__ = "learning"
    
    # Learning details
    learning_type: Mapped[LearningType] = mapped_column(
        SQLEnum(LearningType), nullable=False, index=True
    )
    status: Mapped[LearningStatus] = mapped_column(
        SQLEnum(LearningStatus), default=LearningStatus.PENDING, index=True
    )
    
    # Learning content
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Learning metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Confidence score for the learning (0.0 to 1.0)"
    )
    impact_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Expected impact score (0.0 to 1.0)"
    )
    validation_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Validation score after application (0.0 to 1.0)"
    )
    
    # Source information
    source_component: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_operation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    source_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Application tracking
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    application_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    
    patterns: Mapped[List["LearningPatternModel"]] = relationship(
        "LearningPatternModel", back_populates="learning", cascade="all, delete-orphan"
    )
    feedback: Mapped[List["LearningFeedbackModel"]] = relationship(
        "LearningFeedbackModel", back_populates="learning", cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_learning_type_status", "learning_type", "status"),
        Index("idx_learning_source_component", "source_component"),
        Index("idx_learning_confidence", "confidence_score"),
        Index("idx_learning_impact", "impact_score"),
        Index("idx_learning_applied_at", "applied_at"),
    )


class LearningPatternModel(BaseModel):
    """Model for storing identified patterns and their analysis."""
    
    __tablename__ = "learning_patterns"
    
    # Pattern details
    pattern_type: Mapped[PatternType] = mapped_column(
        SQLEnum(PatternType), nullable=False, index=True
    )
    pattern_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Pattern definition
    pattern_definition: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    pattern_rules: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    
    # Pattern statistics
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    average_performance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Pattern context
    contexts: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True,
        comment="Contexts where this pattern was observed"
    )
    conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True,
        comment="Conditions under which this pattern applies"
    )
    
    # Pattern validation
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Pattern evolution
    first_observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    
    # Relationships
    learning_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning.id"), nullable=False, index=True
    )
    learning: Mapped["LearningModel"] = relationship("LearningModel", back_populates="patterns")
    
    # Indexes
    __table_args__ = (
        Index("idx_pattern_learning_type", "learning_id", "pattern_type"),
        Index("idx_pattern_name", "pattern_name"),
        Index("idx_pattern_occurrence", "occurrence_count"),
        Index("idx_pattern_success_rate", "success_rate"),
        Index("idx_pattern_validated", "is_validated"),
        Index("idx_pattern_observed", "first_observed_at", "last_observed_at"),
    )


class LearningFeedbackModel(BaseModel):
    """Model for storing feedback on learning and system improvements."""
    
    __tablename__ = "learning_feedback"
    
    # Feedback details
    feedback_type: Mapped[FeedbackType] = mapped_column(
        SQLEnum(FeedbackType), nullable=False, index=True
    )
    feedback_content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Feedback source
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="Source of feedback: user, system, automated, etc."
    )
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Feedback context
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    related_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True
    )
    
    # Feedback processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processing_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    
    # Feedback rating and impact
    rating: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="Rating from 1-5 if applicable"
    )
    impact_assessment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Action taken
    action_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    learning_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning.id"), nullable=False, index=True
    )
    learning: Mapped["LearningModel"] = relationship("LearningModel", back_populates="feedback")
    
    # Indexes
    __table_args__ = (
        Index("idx_feedback_learning_type", "learning_id", "feedback_type"),
        Index("idx_feedback_source", "source_type", "source_id"),
        Index("idx_feedback_processed", "is_processed"),
        Index("idx_feedback_rating", "rating"),
        Index("idx_feedback_processed_at", "processed_at"),
    )

