"""
Task database models for storing task context and execution data.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, JSON, 
    ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, TimestampMixin, UUIDMixin


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(str, Enum):
    """Types of tasks in the system."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    FEATURE_IMPLEMENTATION = "feature_implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    INTEGRATION = "integration"


class TaskModel(BaseModel):
    """Main task model for storing task information."""
    
    __tablename__ = "tasks"
    
    # Task identification
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True,
        comment="External ID from Linear, GitHub, etc."
    )
    
    # Task details
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    task_type: Mapped[TaskType] = mapped_column(SQLEnum(TaskType), nullable=False, index=True)
    priority: Mapped[TaskPriority] = mapped_column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, index=True)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    # Task context
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    requirements: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    constraints: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Execution details
    assigned_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Results and outputs
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_files: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True
    )
    
    # Relationships
    executions: Mapped[List["TaskExecutionModel"]] = relationship(
        "TaskExecutionModel", back_populates="task", cascade="all, delete-orphan"
    )
    dependencies: Mapped[List["TaskDependencyModel"]] = relationship(
        "TaskDependencyModel", foreign_keys="TaskDependencyModel.task_id",
        back_populates="task", cascade="all, delete-orphan"
    )
    dependent_tasks: Mapped[List["TaskDependencyModel"]] = relationship(
        "TaskDependencyModel", foreign_keys="TaskDependencyModel.depends_on_task_id",
        back_populates="depends_on_task"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_task_status_priority", "status", "priority"),
        Index("idx_task_type_status", "task_type", "status"),
        Index("idx_task_assigned_agent_status", "assigned_agent", "status"),
        Index("idx_task_external_id", "external_id"),
    )


class TaskExecutionModel(BaseModel):
    """Model for tracking task execution attempts and details."""
    
    __tablename__ = "task_executions"
    
    # Execution details
    execution_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), nullable=False, index=True)
    
    # Execution context
    agent_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    execution_environment: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    input_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Results
    output: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Performance metrics
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    api_calls_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )
    task: Mapped["TaskModel"] = relationship("TaskModel", back_populates="executions")
    
    # Indexes
    __table_args__ = (
        Index("idx_execution_task_status", "task_id", "status"),
        Index("idx_execution_started_at", "started_at"),
    )


class TaskDependencyModel(UUIDMixin, TimestampMixin, BaseModel):
    """Model for tracking task dependencies."""
    
    __tablename__ = "task_dependencies"
    
    # Dependency relationship
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )
    depends_on_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )
    
    # Dependency details
    dependency_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="blocks",
        comment="Type of dependency: blocks, requires, suggests"
    )
    is_hard_dependency: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    task: Mapped["TaskModel"] = relationship(
        "TaskModel", foreign_keys=[task_id], back_populates="dependencies"
    )
    depends_on_task: Mapped["TaskModel"] = relationship(
        "TaskModel", foreign_keys=[depends_on_task_id], back_populates="dependent_tasks"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_dependency_task_depends", "task_id", "depends_on_task_id"),
        Index("idx_dependency_type", "dependency_type"),
    )

