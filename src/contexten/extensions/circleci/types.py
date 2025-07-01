"""
CircleCI Integration Types

Comprehensive data models for CircleCI API responses, webhook events,
and internal processing. All models use Pydantic for validation and serialization.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass


# Enums
class BuildStatus(str, Enum):
    """CircleCI build status values"""
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"
    RUNNING = "running"
    NOT_RUN = "not_run"
    INFRASTRUCTURE_FAIL = "infrastructure_fail"
    TIMEDOUT = "timedout"
    ON_HOLD = "on_hold"
    NEEDS_SETUP = "needs_setup"
    MALFORMED_CONFIG = "malformed_config"
    UNAUTHORIZED = "unauthorized"


class CircleCIEventType(str, Enum):
    """CircleCI webhook event types"""
    WORKFLOW_COMPLETED = "workflow-completed"
    JOB_COMPLETED = "job-completed"
    PING = "ping"


class FailureType(str, Enum):
    """Types of build failures"""
    TEST_FAILURE = "test_failure"
    COMPILATION_ERROR = "compilation_error"
    DEPENDENCY_ERROR = "dependency_error"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN = "unknown"


class FixConfidence(str, Enum):
    """Confidence levels for generated fixes"""
    HIGH = "high"      # 80-100%
    MEDIUM = "medium"  # 50-79%
    LOW = "low"        # 20-49%
    VERY_LOW = "very_low"  # 0-19%


# Core CircleCI Models
class CircleCIProject(BaseModel):
    """CircleCI project information"""
    slug: str
    name: str
    organization_name: str
    organization_slug: str
    organization_id: str
    vcs_info: Dict[str, Any] = Field(default_factory=dict)


class CircleCIUser(BaseModel):
    """CircleCI user information"""
    id: str
    login: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class CircleCICommit(BaseModel):
    """Git commit information"""
    sha: str
    subject: str
    body: Optional[str] = None
    author: Optional[CircleCIUser] = None
    committer: Optional[CircleCIUser] = None
    committed_at: Optional[datetime] = None


class CircleCIJob(BaseModel):
    """CircleCI job information"""
    id: str
    name: str
    project_slug: str
    status: BuildStatus
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    credits_used: Optional[int] = None
    exit_code: Optional[int] = None
    parallel: Optional[bool] = None
    parallelism: Optional[int] = None
    web_url: str
    
    # Job details
    executor: Optional[Dict[str, Any]] = None
    contexts: List[str] = Field(default_factory=list)
    
    @property
    def is_failed(self) -> bool:
        """Check if job failed"""
        return self.status in [
            BuildStatus.FAILED,
            BuildStatus.INFRASTRUCTURE_FAIL,
            BuildStatus.TIMEDOUT
        ]


class CircleCIWorkflow(BaseModel):
    """CircleCI workflow information"""
    id: str
    name: str
    project_slug: str
    status: BuildStatus
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    pipeline_id: str
    pipeline_number: int
    
    # Workflow details
    tag: Optional[str] = None
    
    @property
    def is_failed(self) -> bool:
        """Check if workflow failed"""
        return self.status in [
            BuildStatus.FAILED,
            BuildStatus.INFRASTRUCTURE_FAIL,
            BuildStatus.TIMEDOUT,
            BuildStatus.CANCELED
        ]


class CircleCIBuild(BaseModel):
    """CircleCI build information (legacy v1.1 API)"""
    build_num: int
    username: str
    reponame: str
    branch: str
    vcs_revision: str
    status: BuildStatus
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    build_time_millis: Optional[int] = None
    
    # Build details
    subject: Optional[str] = None
    body: Optional[str] = None
    why: Optional[str] = None
    dont_build: Optional[str] = None
    queued_at: Optional[datetime] = None
    lifecycle: Optional[str] = None
    outcome: Optional[str] = None
    
    # URLs
    build_url: Optional[str] = None
    compare: Optional[str] = None
    
    # User info
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    committer_name: Optional[str] = None
    committer_email: Optional[str] = None
    
    @property
    def is_failed(self) -> bool:
        """Check if build failed"""
        return self.status in [
            BuildStatus.FAILED,
            BuildStatus.INFRASTRUCTURE_FAIL,
            BuildStatus.TIMEDOUT
        ]


# Webhook Event Models
class CircleCIWebhookPayload(BaseModel):
    """Base CircleCI webhook payload"""
    type: CircleCIEventType
    id: str
    happened_at: datetime
    webhook: Dict[str, Any] = Field(default_factory=dict)


class WorkflowCompletedPayload(CircleCIWebhookPayload):
    """Workflow completed webhook payload"""
    type: CircleCIEventType = CircleCIEventType.WORKFLOW_COMPLETED
    workflow: CircleCIWorkflow
    project: CircleCIProject
    organization: Dict[str, Any] = Field(default_factory=dict)
    pipeline: Dict[str, Any] = Field(default_factory=dict)


class JobCompletedPayload(CircleCIWebhookPayload):
    """Job completed webhook payload"""
    type: CircleCIEventType = CircleCIEventType.JOB_COMPLETED
    job: CircleCIJob
    project: CircleCIProject
    organization: Dict[str, Any] = Field(default_factory=dict)
    pipeline: Dict[str, Any] = Field(default_factory=dict)


class PingPayload(CircleCIWebhookPayload):
    """Ping webhook payload"""
    type: CircleCIEventType = CircleCIEventType.PING


# Event Processing Models
class CircleCIEvent(BaseModel):
    """Processed CircleCI event"""
    id: str
    type: CircleCIEventType
    timestamp: datetime
    project_slug: str
    organization: str
    
    # Event data
    workflow_id: Optional[str] = None
    job_id: Optional[str] = None
    build_number: Optional[int] = None
    status: Optional[BuildStatus] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    
    # Processing metadata
    processed_at: Optional[datetime] = None
    processing_duration: Optional[float] = None  # seconds
    retry_count: int = 0
    
    @property
    def is_failure_event(self) -> bool:
        """Check if this is a failure event"""
        return self.status in [
            BuildStatus.FAILED,
            BuildStatus.INFRASTRUCTURE_FAIL,
            BuildStatus.TIMEDOUT
        ]


# Failure Analysis Models
class LogEntry(BaseModel):
    """Build log entry"""
    timestamp: Optional[datetime] = None
    level: str = "info"  # debug, info, warn, error
    message: str
    source: Optional[str] = None  # job name, step name, etc.
    
    # Parsed information
    is_error: bool = False
    error_type: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class TestResult(BaseModel):
    """Test execution result"""
    name: str
    classname: Optional[str] = None
    file: Optional[str] = None
    result: str  # passed, failed, skipped
    message: Optional[str] = None
    time: Optional[float] = None  # execution time in seconds
    
    # Failure details
    failure_message: Optional[str] = None
    failure_type: Optional[str] = None
    stack_trace: Optional[str] = None


class FailurePattern(BaseModel):
    """Identified failure pattern"""
    pattern_type: FailureType
    confidence: float = Field(ge=0.0, le=1.0)
    description: str
    
    # Pattern details
    error_message: Optional[str] = None
    file_patterns: List[str] = Field(default_factory=list)
    command_patterns: List[str] = Field(default_factory=list)
    
    # Suggested actions
    suggested_fixes: List[str] = Field(default_factory=list)
    documentation_links: List[str] = Field(default_factory=list)


class FailureAnalysis(BaseModel):
    """Comprehensive failure analysis"""
    build_id: str
    project_slug: str
    analysis_timestamp: datetime
    
    # Failure classification
    failure_type: FailureType
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Analysis details
    error_messages: List[str] = Field(default_factory=list)
    failed_tests: List[TestResult] = Field(default_factory=list)
    log_entries: List[LogEntry] = Field(default_factory=list)
    patterns: List[FailurePattern] = Field(default_factory=list)
    
    # Context information
    affected_files: List[str] = Field(default_factory=list)
    dependencies_involved: List[str] = Field(default_factory=list)
    environment_info: Dict[str, Any] = Field(default_factory=dict)
    
    # Recommendations
    suggested_fixes: List[str] = Field(default_factory=list)
    similar_failures: List[str] = Field(default_factory=list)  # IDs of similar past failures
    
    # Processing metadata
    analysis_duration: Optional[float] = None  # seconds
    analyzer_version: str = "1.0.0"


# Fix Generation Models
class CodeFix(BaseModel):
    """Generated code fix"""
    file_path: str
    description: str
    fix_type: str  # "modification", "addition", "deletion"
    
    # Fix content
    original_content: Optional[str] = None
    fixed_content: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    
    # Metadata
    confidence: FixConfidence
    reasoning: str
    estimated_impact: str = "low"  # low, medium, high


class ConfigurationFix(BaseModel):
    """Configuration file fix"""
    file_path: str
    description: str
    
    # Configuration changes
    changes: Dict[str, Any] = Field(default_factory=dict)
    additions: Dict[str, Any] = Field(default_factory=dict)
    removals: List[str] = Field(default_factory=list)
    
    # Metadata
    confidence: FixConfidence
    reasoning: str


class DependencyFix(BaseModel):
    """Dependency-related fix"""
    description: str
    fix_type: str  # "update", "add", "remove", "pin"
    
    # Dependency details
    package_name: str
    current_version: Optional[str] = None
    target_version: Optional[str] = None
    package_manager: str = "npm"  # npm, pip, maven, etc.
    
    # Metadata
    confidence: FixConfidence
    reasoning: str


class GeneratedFix(BaseModel):
    """Complete generated fix"""
    id: str
    failure_analysis_id: str
    timestamp: datetime
    
    # Fix details
    title: str
    description: str
    overall_confidence: FixConfidence
    
    # Fix components
    code_fixes: List[CodeFix] = Field(default_factory=list)
    config_fixes: List[ConfigurationFix] = Field(default_factory=list)
    dependency_fixes: List[DependencyFix] = Field(default_factory=list)
    
    # Implementation details
    branch_name: Optional[str] = None
    commit_message: Optional[str] = None
    pr_title: Optional[str] = None
    pr_description: Optional[str] = None
    
    # Validation
    validation_commands: List[str] = Field(default_factory=list)
    test_commands: List[str] = Field(default_factory=list)
    
    # Status tracking
    status: str = "generated"  # generated, applied, tested, merged, failed
    applied_at: Optional[datetime] = None
    pr_url: Optional[str] = None
    
    # Results
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    success: Optional[bool] = None
    error_message: Optional[str] = None


# Integration Metrics and Status
class ComponentStats(BaseModel):
    """Statistics for a component"""
    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    average_response_time: float = 0.0
    last_request_at: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.requests_total == 0:
            return 0.0
        return (self.requests_successful / self.requests_total) * 100


class WebhookStats(ComponentStats):
    """Webhook processing statistics"""
    events_processed: int = 0
    events_failed: int = 0
    signature_validations: int = 0
    signature_failures: int = 0
    
    # Event type breakdown
    workflow_events: int = 0
    job_events: int = 0
    ping_events: int = 0


class AnalysisStats(ComponentStats):
    """Failure analysis statistics"""
    failures_analyzed: int = 0
    patterns_identified: int = 0
    high_confidence_analyses: int = 0
    analysis_cache_hits: int = 0


class FixGenerationStats(ComponentStats):
    """Fix generation statistics"""
    fixes_generated: int = 0
    fixes_applied: int = 0
    fixes_successful: int = 0
    prs_created: int = 0
    prs_merged: int = 0
    
    # Confidence breakdown
    high_confidence_fixes: int = 0
    medium_confidence_fixes: int = 0
    low_confidence_fixes: int = 0


class CircleCIIntegrationMetrics(BaseModel):
    """Overall integration metrics"""
    # Component statistics
    webhook_stats: WebhookStats = Field(default_factory=WebhookStats)
    analysis_stats: AnalysisStats = Field(default_factory=AnalysisStats)
    fix_stats: FixGenerationStats = Field(default_factory=FixGenerationStats)
    
    # Overall metrics
    uptime_start: datetime = Field(default_factory=datetime.now)
    builds_monitored: int = 0
    failures_detected: int = 0
    projects_monitored: int = 0
    
    # Performance metrics
    average_fix_time: Optional[float] = None  # seconds from failure to fix
    average_analysis_time: Optional[float] = None  # seconds
    
    @property
    def uptime_duration(self) -> timedelta:
        """Calculate uptime duration"""
        return datetime.now() - self.uptime_start
    
    @property
    def overall_success_rate(self) -> float:
        """Calculate overall fix success rate"""
        if self.fix_stats.fixes_applied == 0:
            return 0.0
        return (self.fix_stats.fixes_successful / self.fix_stats.fixes_applied) * 100


class IntegrationStatus(BaseModel):
    """Current integration status"""
    healthy: bool = True
    last_check: datetime = Field(default_factory=datetime.now)
    
    # Component health
    webhook_healthy: bool = True
    api_healthy: bool = True
    analysis_healthy: bool = True
    fix_generation_healthy: bool = True
    
    # Issues and warnings
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Configuration status
    config_valid: bool = True
    credentials_valid: bool = True
    
    # Monitoring status
    projects_monitored: int = 0
    active_workflows: int = 0
    pending_analyses: int = 0
    pending_fixes: int = 0


# Dataclasses for internal processing
@dataclass
class ProcessingContext:
    """Context for event processing"""
    event_id: str
    project_slug: str
    organization: str
    timestamp: datetime
    retry_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnalysisContext:
    """Context for failure analysis"""
    build_id: str
    project_slug: str
    failure_type: FailureType
    logs_available: bool = False
    tests_available: bool = False
    artifacts_available: bool = False
    
    # Repository context
    repository_url: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    
    # Analysis options
    deep_analysis: bool = True
    pattern_matching: bool = True
    similarity_search: bool = True


@dataclass
class FixContext:
    """Context for fix generation"""
    failure_analysis: FailureAnalysis
    repository_url: str
    branch: str
    commit_sha: str
    
    # Fix options
    auto_apply: bool = False
    create_pr: bool = True
    run_tests: bool = True
    
    # Integration settings
    github_token: Optional[str] = None
    codegen_token: Optional[str] = None

