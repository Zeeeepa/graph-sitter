"""
Analytics database models for OpenEvolve mechanics to analyze each system step.
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


class AnalyticsEventType(str, Enum):
    """Types of analytics events."""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    CODE_GENERATED = "code_generated"
    CODE_REVIEWED = "code_reviewed"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_MEASURED = "performance_measured"
    USER_INTERACTION = "user_interaction"
    SYSTEM_OPTIMIZATION = "system_optimization"
    LEARNING_UPDATE = "learning_update"


class MetricType(str, Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AnalyticsModel(BaseModel):
    """Main analytics model for storing system analysis data."""
    
    __tablename__ = "analytics"
    
    # Analytics session details
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[AnalyticsEventType] = mapped_column(
        SQLEnum(AnalyticsEventType), nullable=False, index=True
    )
    
    # Context information
    component: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="System component that generated the event"
    )
    operation: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True,
        comment="Specific operation being performed"
    )
    
    # Event data
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Performance metrics
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Success/failure tracking
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # User and environment context
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    environment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Relationships
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    
    events: Mapped[List["AnalyticsEventModel"]] = relationship(
        "AnalyticsEventModel", back_populates="analytics", cascade="all, delete-orphan"
    )
    metrics: Mapped[List["AnalyticsMetricModel"]] = relationship(
        "AnalyticsMetricModel", back_populates="analytics", cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_analytics_session_event", "session_id", "event_type"),
        Index("idx_analytics_component_operation", "component", "operation"),
        Index("idx_analytics_success_error", "success", "error_code"),
        Index("idx_analytics_user_environment", "user_id", "environment"),
        Index("idx_analytics_created_at", "created_at"),
    )


class AnalyticsEventModel(BaseModel):
    """Model for storing detailed analytics events."""
    
    __tablename__ = "analytics_events"
    
    # Event details
    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_action: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Event properties
    properties: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Timing information
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Event context
    page_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Custom dimensions
    custom_dimensions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    analytics_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analytics.id"), nullable=False, index=True
    )
    analytics: Mapped["AnalyticsModel"] = relationship("AnalyticsModel", back_populates="events")
    
    # Indexes
    __table_args__ = (
        Index("idx_event_analytics_category", "analytics_id", "event_category"),
        Index("idx_event_name_action", "event_name", "event_action"),
        Index("idx_event_timestamp", "timestamp"),
    )


class AnalyticsMetricModel(BaseModel):
    """Model for storing system performance metrics."""
    
    __tablename__ = "analytics_metrics"
    
    # Metric details
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    metric_type: Mapped[MetricType] = mapped_column(
        SQLEnum(MetricType), nullable=False, index=True
    )
    
    # Metric values
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Metric context
    labels: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    dimensions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Aggregation information
    sample_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    percentile_95: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    percentile_99: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timing
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    collection_interval_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    analytics_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analytics.id"), nullable=False, index=True
    )
    analytics: Mapped["AnalyticsModel"] = relationship("AnalyticsModel", back_populates="metrics")
    
    # Indexes
    __table_args__ = (
        Index("idx_metric_analytics_name", "analytics_id", "metric_name"),
        Index("idx_metric_type_timestamp", "metric_type", "timestamp"),
        Index("idx_metric_value", "value"),
        Index("idx_metric_timestamp", "timestamp"),
    )

