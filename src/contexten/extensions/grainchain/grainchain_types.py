"""Type definitions for Grainchain integration.

This module defines all the data structures, enums, and type hints used
throughout the Grainchain integration system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Add comprehensive exports
__all__ = [
    'SandboxProvider',
    'ProviderStatus',
    'QualityGateType',
    'QualityGateStatus',
    'IntegrationStatus',
    'GrainchainEventType',
    'SandboxConfig',
    'ExecutionResult',
    'SnapshotInfo',
    'SnapshotMetadata',
    'ProviderInfo',
    'QualityGateResult',
    'GrainchainEvent',
    'SandboxMetrics',
    'IntegrationMetrics',
    'WorkflowTask',
    'SandboxWorkflow',
    'PipelineStage',
    'PipelineResult',
    'PREnvironment',
    'CostAnalysis',
    'PerformanceBenchmark',
    'HealthCheck',
    'SystemHealth',
    'SandboxId',
    'SnapshotId',
    'ProviderId',
    'WorkflowId',
    'PipelineId',
    'ConfigValue',
    'ProviderConfig',
]

class SandboxProvider(Enum):
    """Supported sandbox providers."""
    LOCAL = "local"
    E2B = "e2b"
    DAYTONA = "daytona"
    MORPH = "morph"
    DOCKER = "docker"


class ProviderStatus(Enum):
    """Provider availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class QualityGateType(Enum):
    """Types of quality gates."""
    CODE_QUALITY = "code_quality"
    UNIT_TESTS = "unit_tests"
    INTEGRATION_TESTS = "integration_tests"
    SECURITY_SCAN = "security_scan"
    PERFORMANCE_TEST = "performance_test"
    DEPLOYMENT_TEST = "deployment_test"
    CUSTOM = "custom"


class QualityGateStatus(Enum):
    """Quality gate execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class IntegrationStatus(Enum):
    """Overall integration status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


class GrainchainEventType(Enum):
    """Types of Grainchain events."""
    SANDBOX_CREATED = "sandbox_created"
    SANDBOX_DESTROYED = "sandbox_destroyed"
    SNAPSHOT_CREATED = "snapshot_created"
    SNAPSHOT_RESTORED = "snapshot_restored"
    QUALITY_GATE_STARTED = "quality_gate_started"
    QUALITY_GATE_COMPLETED = "quality_gate_completed"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    PROVIDER_STATUS_CHANGED = "provider_status_changed"
    COST_THRESHOLD_EXCEEDED = "cost_threshold_exceeded"
    PERFORMANCE_DEGRADED = "performance_degraded"


@dataclass
class SandboxConfig:
    """Configuration for sandbox creation."""
    provider: Optional[SandboxProvider] = None
    timeout: int = 1800  # 30 minutes default
    memory_limit: str = "2GB"
    cpu_limit: float = 2.0
    disk_limit: str = "10GB"
    environment_vars: Dict[str, str] = field(default_factory=dict)
    working_directory: str = "/workspace"
    network_isolation: bool = False
    auto_cleanup: bool = True
    provider_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of command execution in sandbox."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timestamp: datetime
    sandbox_id: str
    provider: SandboxProvider


@dataclass
class SnapshotInfo:
    """Information about a sandbox snapshot."""
    id: str
    name: str
    provider: SandboxProvider
    size_bytes: int
    created_at: datetime
    metadata: Dict[str, Any]
    parent_snapshot: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    retention_policy: Optional[str] = None


@dataclass
class SnapshotMetadata:
    """Metadata for snapshot creation."""
    name: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retention_days: Optional[int] = None
    is_delta: bool = False
    parent_snapshot: Optional[str] = None


@dataclass
class ProviderInfo:
    """Information about a sandbox provider."""
    name: SandboxProvider
    status: ProviderStatus
    available: bool
    capabilities: List[str]
    performance_metrics: Dict[str, float]
    cost_per_hour: Optional[float] = None
    startup_time_ms: Optional[float] = None
    max_memory: Optional[str] = None
    max_cpu: Optional[float] = None
    supported_features: List[str] = field(default_factory=list)
    last_health_check: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class QualityGateResult:
    """Result of a quality gate execution."""
    gate_type: QualityGateType
    status: QualityGateStatus
    passed: bool
    duration: float
    timestamp: datetime
    sandbox_id: str
    snapshot_id: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


@dataclass
class GrainchainEvent:
    """Event emitted by Grainchain integration."""
    event_type: GrainchainEventType
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    severity: str = "info"  # info, warning, error, critical


@dataclass
class SandboxMetrics:
    """Metrics for sandbox usage."""
    provider: SandboxProvider
    total_sandboxes_created: int
    active_sandboxes: int
    total_execution_time: float
    average_startup_time: float
    success_rate: float
    cost_total: float
    cost_per_hour: float
    resource_utilization: Dict[str, float]
    error_count: int
    last_updated: datetime


@dataclass
class IntegrationMetrics:
    """Overall integration metrics."""
    active_sandboxes: int
    total_snapshots: int
    quality_gate_success_rate: float
    average_deployment_time: float
    monthly_cost: float
    provider_metrics: Dict[SandboxProvider, SandboxMetrics]
    health_status: IntegrationStatus
    uptime_percentage: float
    last_updated: datetime


@dataclass
class WorkflowTask:
    """A task within a workflow."""
    name: str
    task_type: str
    config: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 1800
    retry_count: int = 0
    max_retries: int = 3
    condition: Optional[str] = None
    parallel: bool = False


@dataclass
class SandboxWorkflow:
    """A workflow definition for sandbox operations."""
    name: str
    description: str
    tasks: List[WorkflowTask]
    global_config: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 7200  # 2 hours default
    on_failure: str = "stop"  # stop, continue, retry
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineStage:
    """A stage in a CI/CD pipeline."""
    name: str
    provider: SandboxProvider
    config: SandboxConfig
    quality_gates: List[QualityGateType]
    parallel: bool = False
    timeout: int = 1800
    depends_on: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    pipeline_id: str
    status: str
    stages: Dict[str, Dict[str, Any]]
    total_duration: float
    cost: float
    artifacts: Dict[str, str]
    snapshots: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class PREnvironment:
    """PR environment information."""
    pr_number: int
    commit_sha: str
    deployment_url: str
    sandbox_id: str
    snapshot_id: str
    provider: SandboxProvider
    status: str
    created_at: datetime
    last_updated: datetime
    cost: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostAnalysis:
    """Cost analysis results."""
    total_cost: float
    cost_by_provider: Dict[SandboxProvider, float]
    cost_by_project: Dict[str, float]
    cost_trends: Dict[str, List[float]]
    recommendations: List[Dict[str, Any]]
    potential_savings: float
    period_start: datetime
    period_end: datetime


@dataclass
class PerformanceBenchmark:
    """Performance benchmark results."""
    provider: SandboxProvider
    test_suite: str
    startup_time: float
    execution_time: float
    memory_usage: float
    cpu_usage: float
    network_latency: float
    cost_per_test: float
    success_rate: float
    timestamp: datetime


@dataclass
class HealthCheck:
    """Health check result."""
    component: str
    status: str
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    response_time: Optional[float] = None


@dataclass
class SystemHealth:
    """Overall system health status."""
    overall_status: IntegrationStatus
    components: List[HealthCheck]
    uptime: float
    last_check: datetime
    issues: List[Dict[str, str]] = field(default_factory=list)


# Type aliases for common use cases
SandboxId = str
SnapshotId = str
ProviderId = str
WorkflowId = str
PipelineId = str

# Configuration type unions
ConfigValue = Union[str, int, float, bool, Dict[str, Any], List[Any]]
ProviderConfig = Dict[str, ConfigValue]
