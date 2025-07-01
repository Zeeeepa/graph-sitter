"""
Type definitions for CircleCI extension
"""

from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


class CircleCIEventType(str, Enum):
    """CircleCI event types"""
    WORKFLOW_COMPLETED = "workflow-completed"
    JOB_COMPLETED = "job-completed"
    PING = "ping"


class BuildStatus(str, Enum):
    """Build status types"""
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"
    UNAUTHORIZED = "unauthorized"
    RUNNING = "running"
    NOT_RUN = "not_run"
    ON_HOLD = "on_hold"
    NEEDS_SETUP = "needs_setup"


class FailureType(str, Enum):
    """Types of build failures"""
    TEST_FAILURE = "test_failure"
    COMPILATION_ERROR = "compilation_error"
    DEPENDENCY_ERROR = "dependency_error"
    RESOURCE_ERROR = "resource_error"
    TIMEOUT = "timeout"
    PERMISSION_ERROR = "permission_error"
    UNKNOWN = "unknown"


class FixConfidence(str, Enum):
    """Confidence levels for auto-fixes"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class CircleCIEvent:
    """Base class for CircleCI events"""
    type: CircleCIEventType
    id: str
    happened_at: datetime
    raw_payload: Dict[str, Any]


@dataclass
class WorkflowEvent(CircleCIEvent):
    """Workflow event data"""
    workflow_id: str
    workflow_name: str
    project_slug: str
    status: BuildStatus
    started_at: datetime
    stopped_at: datetime
    pipeline_id: str
    pipeline_number: int
    branch: str
    revision: str


@dataclass
class JobEvent(CircleCIEvent):
    """Job event data"""
    job_id: str
    job_name: str
    project_slug: str
    status: BuildStatus
    started_at: datetime
    stopped_at: datetime
    web_url: str
    exit_code: Optional[int]
    branch: str
    revision: str


@dataclass
class FailureAnalysis:
    """Build failure analysis results"""
    project_slug: str
    workflow_id: str
    job_id: Optional[str]
    failure_type: FailureType
    error_messages: List[str]
    confidence: float
    analysis_time: float
    suggested_fixes: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class WebhookResult:
    """Webhook processing result"""
    success: bool
    event_type: Optional[CircleCIEventType] = None
    event_id: Optional[str] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


@dataclass
class WebhookStats:
    """Webhook processing statistics"""
    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    events_processed: int = 0
    events_failed: int = 0
    workflow_events: int = 0
    job_events: int = 0
    ping_events: int = 0
    processing_time_total: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.requests_total == 0:
            return 0.0
        return (self.requests_successful / self.requests_total) * 100.0

    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time"""
        if self.events_processed == 0:
            return 0.0
        return self.processing_time_total / self.events_processed

