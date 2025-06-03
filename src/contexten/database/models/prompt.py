"""
Prompt database models for storing conditional prompt templates.
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


class PromptType(str, Enum):
    """Types of prompts in the system."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"
    ANALYSIS = "analysis"
    SYSTEM_PROMPT = "system_prompt"
    USER_PROMPT = "user_prompt"


class PromptStatus(str, Enum):
    """Prompt status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    TESTING = "testing"


class ConditionOperator(str, Enum):
    """Operators for prompt conditions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN = "in"
    NOT_IN = "not_in"
    REGEX_MATCH = "regex_match"


class PromptModel(BaseModel):
    """Main prompt model for storing prompt templates."""
    
    __tablename__ = "prompts"
    
    # Prompt identification
    slug: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True,
        comment="URL-friendly prompt identifier"
    )
    
    # Prompt details
    prompt_type: Mapped[PromptType] = mapped_column(
        SQLEnum(PromptType), nullable=False, index=True
    )
    status: Mapped[PromptStatus] = mapped_column(
        SQLEnum(PromptStatus), default=PromptStatus.ACTIVE, index=True
    )
    
    # Prompt content
    template: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Prompt configuration
    variables: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True,
        comment="List of variables that can be substituted in the template"
    )
    default_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True,
        comment="Default values for template variables"
    )
    
    # Usage and performance
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    average_response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Version control
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    parent_prompt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=True, index=True
    )
    
    # Categorization
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Relationships
    templates: Mapped[List["PromptTemplateModel"]] = relationship(
        "PromptTemplateModel", back_populates="prompt", cascade="all, delete-orphan"
    )
    conditions: Mapped[List["PromptConditionModel"]] = relationship(
        "PromptConditionModel", back_populates="prompt", cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_prompt_type_status", "prompt_type", "status"),
        Index("idx_prompt_category", "category", "subcategory"),
        Index("idx_prompt_usage", "usage_count"),
    )


class PromptTemplateModel(BaseModel):
    """Model for storing prompt template variations."""
    
    __tablename__ = "prompt_templates"
    
    # Template details
    template_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Template configuration
    language: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, index=True,
        comment="Language code for localized templates"
    )
    context_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True,
        comment="Type of context this template is optimized for"
    )
    
    # Template metadata
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Performance metrics
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False, index=True
    )
    prompt: Mapped["PromptModel"] = relationship("PromptModel", back_populates="templates")
    
    # Indexes
    __table_args__ = (
        Index("idx_template_prompt_priority", "prompt_id", "priority"),
        Index("idx_template_language_context", "language", "context_type"),
        Index("idx_template_default", "is_default"),
    )


class PromptConditionModel(UUIDMixin, TimestampMixin, BaseModel):
    """Model for storing conditions that determine when to use specific prompts."""
    
    __tablename__ = "prompt_conditions"
    
    # Condition details
    condition_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Field name to evaluate (e.g., 'task_type', 'file_extension')"
    )
    operator: Mapped[ConditionOperator] = mapped_column(
        SQLEnum(ConditionOperator), nullable=False, index=True
    )
    expected_value: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Condition configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        comment="Higher priority conditions are evaluated first"
    )
    
    # Logic operators
    logical_operator: Mapped[str] = mapped_column(
        String(10), default="AND", nullable=False,
        comment="Logical operator to combine with other conditions (AND, OR)"
    )
    group_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True,
        comment="Group ID for complex condition grouping"
    )
    
    # Relationships
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False, index=True
    )
    prompt: Mapped["PromptModel"] = relationship("PromptModel", back_populates="conditions")
    
    # Indexes
    __table_args__ = (
        Index("idx_condition_prompt_priority", "prompt_id", "priority"),
        Index("idx_condition_field_operator", "field_name", "operator"),
        Index("idx_condition_group", "group_id"),
        Index("idx_condition_active", "is_active"),
    )

