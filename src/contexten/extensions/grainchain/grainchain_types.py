"""Type definitions for Grainchain integration.

This module defines all the data structures, enums, and type hints used
throughout the Grainchain integration system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


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
    provider: SandboxProvider | None = None
    timeout: int = 1800  # 30 minutes default
    memory_limit: str = "2GB"
    cpu_limit: float = 2.0
    disk_limit: str = "10GB"
    environment_vars: dict[str, str] = field(default_factory=dict)
    working_directory: str = "/workspace"
    network_isolation: bool = False
    auto_cleanup: bool = True
    provider_config: dict[str, Any] = field(default_factory=dict)


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
    metadata: dict[str, Any]
    parent_snapshot: str | None = None
    tags: list[str] = field(default_factory=list)
    retention_policy: str | None = None


@dataclass
class SnapshotMetadata:
    """Metadata for snapshot creation."""
    name: str
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    retention_days: int | None = None
    is_delta: bool = False
    parent_snapshot: str | None = None


@dataclass
class ProviderInfo:
    """Information about a sandbox provider."""
    name: SandboxProvider
    status: ProviderStatus
    available: bool
    capabilities: list[str]
    performance_metrics: dict[str, float]
    cost_per_hour: float | None = None
    startup_time_ms: float | None = None
    max_memory: str | None = None
    max_cpu: float | None = None
    supported_features: list[str] = field(default_factory=list)
    last_health_check: datetime | None = None
    error_message: str | None = None


@dataclass
class QualityGateResult:
    """Result of a quality gate execution."""
    gate_type: QualityGateType
    status: QualityGateStatus
    passed: bool
    duration: float
    timestamp: datetime
    sandbox_id: str
    snapshot_id: str | None = None
    results: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    error_message: str | None = None
    recommendations: list[str] = field(default_factory=list)


@dataclass
class GrainchainEvent:
    """Event emitted by Grainchain integration."""
    event_type: GrainchainEventType
    timestamp: datetime
    source: str
    data: dict[str, Any]
    correlation_id: str | None = None
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
    resource_utilization: dict[str, float]
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
    provider_metrics: dict[SandboxProvider, SandboxMetrics]
    health_status: IntegrationStatus
    uptime_percentage: float
    last_updated: datetime


@dataclass
class WorkflowTask:
    """A task within a workflow."""
    name: str
    task_type: str
    config: dict[str, Any]
    dependencies: list[str] = field(default_factory=list)
    timeout: int = 1800
    retry_count: int = 0
    max_retries: int = 3
    condition: str | None = None
    parallel: bool = False


@dataclass
class SandboxWorkflow:
    """A workflow definition for sandbox operations."""
    name: str
    description: str
    tasks: list[WorkflowTask]
    global_config: dict[str, Any] = field(default_factory=dict)
    timeout: int = 7200  # 2 hours default
    on_failure: str = "stop"  # stop, continue, retry
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineStage:
    """A stage in a CI/CD pipeline."""
    name: str
    provider: SandboxProvider
    config: SandboxConfig
    quality_gates: list[QualityGateType]
    parallel: bool = False
    timeout: int = 1800
    depends_on: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    pipeline_id: str
    status: str
    stages: dict[str, dict[str, Any]]
    total_duration: float
    cost: float
    artifacts: dict[str, str]
    snapshots: list[str]
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None


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
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CostAnalysis:
    """Cost analysis results."""
    total_cost: float
    cost_by_provider: dict[SandboxProvider, float]
    cost_by_project: dict[str, float]
    cost_trends: dict[str, list[float]]
    recommendations: list[dict[str, Any]]
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
    details: dict[str, Any] = field(default_factory=dict)
    response_time: float | None = None


@dataclass
class SystemHealth:
    """Overall system health status."""
    overall_status: IntegrationStatus
    components: list[HealthCheck]
    uptime: float
    last_check: datetime
    issues: list[dict[str, str]] = field(default_factory=list)


# Type aliases for common use cases
SandboxId = str
SnapshotId = str
ProviderId = str
WorkflowId = str
PipelineId = str

# Configuration type unions
ConfigValue = str | int | float | bool | dict[str, Any] | list[Any]
ProviderConfig = dict[str, ConfigValue]
