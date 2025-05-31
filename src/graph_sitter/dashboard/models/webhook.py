"""Webhook data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WebhookEventType(str, Enum):
    """Webhook event types."""
    PULL_REQUEST = "pull_request"
    PUSH = "push"
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    PULL_REQUEST_REVIEW = "pull_request_review"
    PULL_REQUEST_REVIEW_COMMENT = "pull_request_review_comment"
    BRANCH_PROTECTION_RULE = "branch_protection_rule"
    CREATE = "create"
    DELETE = "delete"
    FORK = "fork"
    RELEASE = "release"
    STAR = "star"
    WATCH = "watch"


class WebhookEvent(BaseModel):
    """Webhook event model."""
    
    id: str = Field(..., description="Unique event ID")
    event_type: WebhookEventType
    action: str = Field(..., description="Event action (opened, closed, etc.)")
    
    # Source information
    repository_id: str
    repository_name: str
    sender: str
    
    # Event payload
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # Processing information
    received_at: datetime
    processed_at: Optional[datetime] = None
    processing_status: str = Field(default="pending", description="Status: pending, processing, completed, failed")
    error_message: Optional[str] = None
    
    # Notification settings
    notify_linear: bool = Field(default=True)
    notify_slack: bool = Field(default=False)
    notify_email: bool = Field(default=False)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookConfiguration(BaseModel):
    """Webhook configuration for a project."""
    
    project_id: str
    webhook_url: str
    secret: Optional[str] = None
    
    # Event subscriptions
    events: List[WebhookEventType] = Field(default_factory=list)
    
    # Configuration options
    active: bool = Field(default=True)
    ssl_verification: bool = Field(default=True)
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    last_delivery: Optional[datetime] = None
    
    # Statistics
    total_deliveries: int = Field(default=0)
    successful_deliveries: int = Field(default=0)
    failed_deliveries: int = Field(default=0)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookDelivery(BaseModel):
    """Webhook delivery attempt."""
    
    id: str
    webhook_config_id: str
    event_id: str
    
    # Delivery details
    url: str
    http_method: str = Field(default="POST")
    headers: Dict[str, str] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # Response details
    status_code: Optional[int] = None
    response_headers: Dict[str, str] = Field(default_factory=dict)
    response_body: Optional[str] = None
    
    # Timing
    delivered_at: datetime
    response_time_ms: Optional[int] = None
    
    # Status
    success: bool = Field(default=False)
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

