"""
Event database models for storing Linear/Slack/GitHub and deployment events.
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


class EventProvider(str, Enum):
    """Event providers."""
    GITHUB = "github"
    LINEAR = "linear"
    SLACK = "slack"
    DEPLOYMENT = "deployment"
    SYSTEM = "system"
    USER = "user"


class EventStatus(str, Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventModel(BaseModel):
    """Main event model for storing system events."""
    
    __tablename__ = "events"
    
    # Event identification
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True,
        comment="External event ID from the provider"
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider: Mapped[EventProvider] = mapped_column(
        SQLEnum(EventProvider), nullable=False, index=True
    )
    
    # Event details
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    status: Mapped[EventStatus] = mapped_column(
        SQLEnum(EventStatus), default=EventStatus.PENDING, index=True
    )
    priority: Mapped[EventPriority] = mapped_column(
        SQLEnum(EventPriority), default=EventPriority.MEDIUM, index=True
    )
    
    # Event payload and context
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    
    # Processing information
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    processing_duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Event source information
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source_user: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    source_repository: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    
    # Relationships
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True
    )
    
    payloads: Mapped[List["EventPayloadModel"]] = relationship(
        "EventPayloadModel", back_populates="event", cascade="all, delete-orphan"
    )
    handlers: Mapped[List["EventHandlerModel"]] = relationship(
        "EventHandlerModel", back_populates="event", cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_event_provider_type", "provider", "event_type"),
        Index("idx_event_status_priority", "status", "priority"),
        Index("idx_event_external_id", "external_id"),
        Index("idx_event_source_user", "source_user"),
        Index("idx_event_source_repository", "source_repository"),
        Index("idx_event_processed_at", "processed_at"),
    )


class EventPayloadModel(BaseModel):
    """Model for storing detailed event payload information."""
    
    __tablename__ = "event_payloads"
    
    # Payload details
    payload_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Type of payload: webhook, api_response, user_input, etc."
    )
    content_type: Mapped[str] = mapped_column(
        String(100), default="application/json", nullable=False
    )
    
    # Payload content
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Payload metadata
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Processing information
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processing_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True
    )
    event: Mapped["EventModel"] = relationship("EventModel", back_populates="payloads")
    
    # Indexes
    __table_args__ = (
        Index("idx_payload_event_type", "event_id", "payload_type"),
        Index("idx_payload_processed", "is_processed"),
        Index("idx_payload_size", "size_bytes"),
    )


class EventHandlerModel(BaseModel):
    """Model for tracking event handler execution."""
    
    __tablename__ = "event_handlers"
    
    # Handler details
    handler_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    handler_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Type of handler: webhook, processor, notifier, etc."
    )
    handler_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Execution details
    status: Mapped[EventStatus] = mapped_column(
        SQLEnum(EventStatus), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Handler configuration
    configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Performance metrics
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True
    )
    event: Mapped["EventModel"] = relationship("EventModel", back_populates="handlers")
    
    # Indexes
    __table_args__ = (
        Index("idx_handler_event_name", "event_id", "handler_name"),
        Index("idx_handler_type_status", "handler_type", "status"),
        Index("idx_handler_started_at", "started_at"),
        Index("idx_handler_duration", "duration_ms"),
    )
