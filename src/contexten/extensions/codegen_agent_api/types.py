"""
Type definitions for Codegen Agent API extension.

Comprehensive type definitions for all components including overlay functionality.
"""

from typing import Dict, Any, List, Optional, Union, Callable, TypedDict, Literal
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


# ===== Core Enums =====

class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class OverlayStrategy(str, Enum):
    """Overlay strategy enumeration."""
    PIP_ONLY = "pip_only"
    LOCAL_ONLY = "local_only"
    PIP_WITH_LOCAL_FALLBACK = "pip_with_local_fallback"
    LOCAL_WITH_PIP_FALLBACK = "local_with_pip_fallback"


class OverlayPriority(str, Enum):
    """Overlay priority enumeration."""
    PIP_FIRST = "pip_first"
    LOCAL_FIRST = "local_first"
    PIP_ONLY = "pip_only"
    LOCAL_ONLY = "local_only"


class WebhookEventType(str, Enum):
    """Webhook event types."""
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    TASK_TIMEOUT = "task.timeout"


class ErrorCode(str, Enum):
    """Error code enumeration."""
    AUTH_ERROR = "AUTH_ERROR"
    API_ERROR = "API_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TASK_ERROR = "TASK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"
    OVERLAY_ERROR = "OVERLAY_ERROR"


# ===== TypedDict Definitions =====

class TaskInfo(TypedDict, total=False):
    """Task information structure."""
    task_id: str
    status: TaskStatus
    result: Optional[str]
    error: Optional[str]
    progress: Optional[Dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]
    prompt: Optional[str]
    metadata: Optional[Dict[str, Any]]
    logs: Optional[List[str]]
    artifacts: Optional[List[Dict[str, Any]]]
    org_id: str
    repository: Optional[str]
    branch: Optional[str]
    priority: TaskPriority
    timeout: Optional[int]
    tags: Optional[List[str]]
    webhook_url: Optional[str]


class AgentStats(TypedDict):
    """Agent statistics structure."""
    org_id: str
    uptime_seconds: float
    request_count: int
    error_count: int
    rate_limit_count: int
    error_rate: float
    last_request_time: Optional[float]
    is_rate_limited: bool
    webhooks_count: int
    config: Dict[str, Any]


class UsageStats(TypedDict, total=False):
    """Usage statistics structure."""
    org_id: str
    period_start: str
    period_end: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    total_runtime_seconds: float
    average_runtime_seconds: float
    api_calls: int
    data_processed_mb: float
    cost_usd: float


class RepositoryInfo(TypedDict):
    """Repository information structure."""
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    default_branch: str
    languages: List[str]
    size_kb: int
    last_updated: str


class WebhookInfo(TypedDict):
    """Webhook information structure."""
    id: str
    url: str
    events: List[WebhookEventType]
    secret: Optional[str]
    active: bool
    created_at: str
    last_triggered: Optional[str]


class ArtifactInfo(TypedDict):
    """Artifact information structure."""
    id: str
    name: str
    type: str
    size_bytes: int
    content_type: str
    url: str
    created_at: str
    metadata: Optional[Dict[str, Any]]


class PipPackageInfo(TypedDict, total=False):
    """Pip package information structure."""
    installed: bool
    version: str
    name: str
    summary: str
    home_page: Optional[str]
    author: Optional[str]
    location: Optional[str]


class OverlayInfo(TypedDict):
    """Overlay information structure."""
    strategy: OverlayStrategy
    pip_available: bool
    pip_info: Optional[PipPackageInfo]
    local_available: bool
    active_implementation: Literal["pip", "local"]


# ===== Dataclass Definitions =====

@dataclass
class TaskProgress:
    """Task progress information."""
    current_step: str
    total_steps: int
    completed_steps: int
    percentage: float
    estimated_remaining_seconds: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    
    @property
    def is_complete(self) -> bool:
        """Check if progress is complete."""
        return self.completed_steps >= self.total_steps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "percentage": self.percentage,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
            "details": self.details,
            "is_complete": self.is_complete
        }


@dataclass
class TaskMetrics:
    """Task execution metrics."""
    creation_time: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    refresh_count: int = 0
    last_refresh_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def total_lifetime(self) -> Optional[float]:
        """Get total task lifetime in seconds."""
        if self.end_time:
            return self.end_time - self.creation_time
        return None


@dataclass
class AgentMetrics:
    """Agent execution metrics."""
    start_time: float
    request_count: int = 0
    error_count: int = 0
    rate_limit_count: int = 0
    last_request_time: Optional[float] = None
    rate_limit_reset_time: Optional[float] = None
    
    @property
    def uptime(self) -> float:
        """Get agent uptime in seconds."""
        import time
        return time.time() - self.start_time
    
    @property
    def error_rate(self) -> float:
        """Get error rate as a percentage."""
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100


@dataclass
class WebhookEvent:
    """Webhook event data."""
    event_type: WebhookEventType
    task_id: str
    org_id: str
    timestamp: datetime
    data: Dict[str, Any]
    webhook_id: Optional[str] = None


@dataclass
class ExtensionMetrics:
    """Extension-specific metrics."""
    overlay_strategy: OverlayStrategy
    pip_calls: int = 0
    local_calls: int = 0
    fallback_count: int = 0
    overlay_errors: int = 0
    
    @property
    def total_calls(self) -> int:
        """Get total number of calls."""
        return self.pip_calls + self.local_calls
    
    @property
    def pip_usage_percentage(self) -> float:
        """Get percentage of calls using pip implementation."""
        if self.total_calls == 0:
            return 0.0
        return (self.pip_calls / self.total_calls) * 100


# ===== Callback Type Definitions =====

StatusCallback = Callable[[str, str], None]  # (old_status, new_status)
ProgressCallback = Callable[[TaskProgress], None]
WebhookCallback = Callable[[WebhookEvent], None]
ErrorCallback = Callable[[Exception], None]


# ===== Request/Response Types =====

class CreateTaskRequest(TypedDict, total=False):
    """Create task request structure."""
    org_id: str
    prompt: str
    context: Optional[Dict[str, Any]]
    repository: Optional[str]
    branch: Optional[str]
    priority: TaskPriority
    timeout: Optional[int]
    tags: Optional[List[str]]
    webhook_url: Optional[str]
    created_at: str


class CreateTaskResponse(TypedDict):
    """Create task response structure."""
    task_id: str
    status: TaskStatus
    created_at: str
    estimated_completion: Optional[str]


class ListTasksRequest(TypedDict, total=False):
    """List tasks request structure."""
    org_id: str
    status: Optional[TaskStatus]
    limit: int
    offset: int
    tags: Optional[List[str]]
    created_after: Optional[str]
    created_before: Optional[str]


class ListTasksResponse(TypedDict):
    """List tasks response structure."""
    tasks: List[TaskInfo]
    total_count: int
    has_more: bool


class CreateWebhookRequest(TypedDict, total=False):
    """Create webhook request structure."""
    org_id: str
    url: str
    events: List[WebhookEventType]
    secret: Optional[str]


class CreateWebhookResponse(TypedDict):
    """Create webhook response structure."""
    webhook_id: str
    url: str
    events: List[WebhookEventType]
    active: bool
    created_at: str


# ===== CodebaseAI Interface Types =====

class CodebaseAITarget(TypedDict, total=False):
    """CodebaseAI target structure."""
    source: Optional[str]
    type: Optional[str]
    name: Optional[str]
    metadata: Optional[Dict[str, Any]]


class CodebaseAIContext(TypedDict, total=False):
    """CodebaseAI context structure."""
    style: Optional[str]
    analysis_type: Optional[str]
    doc_type: Optional[str]
    refactor_type: Optional[str]
    class_info: Optional[Dict[str, Any]]
    usages: Optional[List[Dict[str, Any]]]
    dependencies: Optional[List[str]]


class CodebaseAIRequest(TypedDict, total=False):
    """CodebaseAI request structure."""
    prompt: str
    target: Optional[CodebaseAITarget]
    context: Optional[CodebaseAIContext]
    timeout: Optional[int]
    priority: TaskPriority
    wait_for_completion: bool


# ===== Integration Types =====

class IntegrationEvent(TypedDict):
    """Integration event structure."""
    event_type: str
    source: str
    timestamp: str
    data: Dict[str, Any]


class IntegrationStatus(TypedDict):
    """Integration status structure."""
    name: str
    active: bool
    last_activity: Optional[str]
    error_count: int
    success_count: int


class ComponentStats(TypedDict):
    """Component statistics structure."""
    component_name: str
    uptime_seconds: float
    operation_count: int
    error_count: int
    last_operation: Optional[str]


class CodegenAgentAPIMetrics(TypedDict):
    """Overall extension metrics structure."""
    extension_name: str
    version: str
    uptime_seconds: float
    overlay_info: OverlayInfo
    agent_metrics: AgentMetrics
    extension_metrics: ExtensionMetrics
    integration_status: List[IntegrationStatus]
    component_stats: List[ComponentStats]


# ===== Error Types =====

class ErrorDetails(TypedDict, total=False):
    """Error details structure."""
    error_code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]]
    timestamp: str
    request_id: Optional[str]
    retry_after: Optional[int]
    original_error: Optional[str]


# ===== Configuration Types =====

class ConfigValidationResult(TypedDict):
    """Configuration validation result."""
    valid: bool
    errors: List[str]
    warnings: List[str]


# ===== Export all types =====

__all__ = [
    # Enums
    "TaskStatus",
    "TaskPriority", 
    "OverlayStrategy",
    "OverlayPriority",
    "WebhookEventType",
    "ErrorCode",
    
    # TypedDict classes
    "TaskInfo",
    "AgentStats",
    "UsageStats",
    "RepositoryInfo",
    "WebhookInfo",
    "ArtifactInfo",
    "PipPackageInfo",
    "OverlayInfo",
    "CreateTaskRequest",
    "CreateTaskResponse",
    "ListTasksRequest",
    "ListTasksResponse",
    "CreateWebhookRequest",
    "CreateWebhookResponse",
    "CodebaseAITarget",
    "CodebaseAIContext",
    "CodebaseAIRequest",
    "IntegrationEvent",
    "IntegrationStatus",
    "ComponentStats",
    "CodegenAgentAPIMetrics",
    "ErrorDetails",
    "ConfigValidationResult",
    
    # Dataclasses
    "TaskProgress",
    "TaskMetrics",
    "AgentMetrics",
    "ExtensionMetrics",
    "WebhookEvent",
    
    # Callback types
    "StatusCallback",
    "ProgressCallback",
    "WebhookCallback",
    "ErrorCallback",
]
