"""
Prefect Workflow Definitions for Autonomous CI/CD

This module defines the core workflow types, configurations, and data structures
for the Prefect-based orchestration system.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class AutonomousWorkflowType(Enum):
    """Types of autonomous workflows supported by the orchestration system"""
    
    # CI/CD Core Workflows
    FAILURE_ANALYSIS = "failure_analysis"
    PERFORMANCE_MONITORING = "performance_monitoring"
    DEPENDENCY_MANAGEMENT = "dependency_management"
    SECURITY_AUDIT = "security_audit"
    TEST_OPTIMIZATION = "test_optimization"
    RELEASE_MANAGEMENT = "release_management"
    
    # Integration Workflows
    LINEAR_SYNC = "linear_sync"
    GITHUB_AUTOMATION = "github_automation"
    CODEGEN_TASK_EXECUTION = "codegen_task_execution"
    
    # Monitoring & Recovery
    HEALTH_CHECK = "health_check"
    SYSTEM_RECOVERY = "system_recovery"
    ALERT_MANAGEMENT = "alert_management"
    
    # Optimization Workflows
    CODE_QUALITY_OPTIMIZATION = "code_quality_optimization"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"


class WorkflowPriority(Enum):
    """Workflow execution priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    PAUSED = "paused"


@dataclass
class WorkflowTrigger:
    """Configuration for workflow triggers"""
    trigger_type: str  # schedule, event, manual, webhook
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    
    # Schedule-specific
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    
    # Event-specific
    event_types: List[str] = field(default_factory=list)
    event_filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRetryConfig:
    """Retry configuration for workflows"""
    max_retries: int = 3
    retry_delay_seconds: int = 60
    exponential_backoff: bool = True
    retry_on_failure_types: List[str] = field(default_factory=lambda: ["timeout", "network", "temporary"])


@dataclass
class WorkflowNotificationConfig:
    """Notification configuration for workflows"""
    on_success: bool = False
    on_failure: bool = True
    on_retry: bool = False
    channels: List[str] = field(default_factory=lambda: ["slack", "linear"])
    custom_messages: Dict[str, str] = field(default_factory=dict)


class WorkflowConfig(BaseModel):
    """Complete workflow configuration"""
    
    workflow_type: AutonomousWorkflowType
    name: str
    description: str
    priority: WorkflowPriority = WorkflowPriority.MEDIUM
    
    # Execution configuration
    timeout_seconds: int = 3600
    retry_config: WorkflowRetryConfig = Field(default_factory=WorkflowRetryConfig)
    
    # Triggers
    triggers: List[WorkflowTrigger] = Field(default_factory=list)
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list)
    blocks_workflows: List[str] = Field(default_factory=list)
    
    # Environment and resources
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)
    
    # Monitoring and notifications
    monitoring_enabled: bool = True
    notification_config: WorkflowNotificationConfig = Field(default_factory=WorkflowNotificationConfig)
    
    # Workflow-specific parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


@dataclass
class OrchestrationMetrics:
    """Metrics for orchestration system performance"""
    
    # Workflow execution metrics
    total_workflows_executed: int = 0
    successful_workflows: int = 0
    failed_workflows: int = 0
    retried_workflows: int = 0
    cancelled_workflows: int = 0
    
    # Performance metrics
    average_execution_time: float = 0.0
    median_execution_time: float = 0.0
    p95_execution_time: float = 0.0
    
    # Resource utilization
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    active_workflows: int = 0
    queued_workflows: int = 0
    
    # Error tracking
    error_rate_percent: float = 0.0
    most_common_errors: List[str] = field(default_factory=list)
    
    # System health
    system_health_score: float = 100.0
    last_health_check: Optional[datetime] = None
    uptime_seconds: int = 0
    
    # Integration metrics
    codegen_tasks_executed: int = 0
    linear_issues_processed: int = 0
    github_events_handled: int = 0
    
    # Autonomous operation metrics
    autonomous_fixes_applied: int = 0
    performance_optimizations: int = 0
    security_issues_resolved: int = 0


@dataclass
class WorkflowExecution:
    """Runtime information for a workflow execution"""
    
    execution_id: str
    workflow_config: WorkflowConfig
    status: WorkflowStatus
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Execution details
    current_step: Optional[str] = None
    progress_percent: float = 0.0
    logs: List[str] = field(default_factory=list)
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    # Retry information
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    
    # Resource usage
    cpu_time_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    
    # Integration tracking
    codegen_task_id: Optional[str] = None
    linear_issue_id: Optional[str] = None
    github_run_id: Optional[str] = None


# Predefined workflow configurations
DEFAULT_WORKFLOW_CONFIGS = {
    AutonomousWorkflowType.FAILURE_ANALYSIS: WorkflowConfig(
        workflow_type=AutonomousWorkflowType.FAILURE_ANALYSIS,
        name="Autonomous Failure Analysis",
        description="Automatically analyze CI/CD failures and propose fixes",
        priority=WorkflowPriority.HIGH,
        timeout_seconds=1800,
        triggers=[
            WorkflowTrigger(
                trigger_type="event",
                event_types=["workflow_run.completed"],
                event_filters={"conclusion": "failure"}
            )
        ],
        parameters={
            "auto_fix_enabled": True,
            "create_pr_for_fixes": True,
            "notify_on_analysis": True
        }
    ),
    
    AutonomousWorkflowType.PERFORMANCE_MONITORING: WorkflowConfig(
        workflow_type=AutonomousWorkflowType.PERFORMANCE_MONITORING,
        name="Performance Monitoring",
        description="Monitor CI/CD performance and detect regressions",
        priority=WorkflowPriority.MEDIUM,
        triggers=[
            WorkflowTrigger(
                trigger_type="schedule",
                cron_expression="0 */6 * * *"  # Every 6 hours
            ),
            WorkflowTrigger(
                trigger_type="event",
                event_types=["push"],
                event_filters={"ref": "refs/heads/develop"}
            )
        ],
        parameters={
            "baseline_branch": "develop",
            "alert_threshold_percent": 20,
            "auto_optimize": True
        }
    ),
    
    AutonomousWorkflowType.DEPENDENCY_MANAGEMENT: WorkflowConfig(
        workflow_type=AutonomousWorkflowType.DEPENDENCY_MANAGEMENT,
        name="Autonomous Dependency Management",
        description="Automatically update and manage dependencies",
        priority=WorkflowPriority.LOW,
        triggers=[
            WorkflowTrigger(
                trigger_type="schedule",
                cron_expression="0 2 * * 1"  # Weekly on Monday at 2 AM
            )
        ],
        parameters={
            "update_strategy": "smart",
            "test_before_merge": True,
            "security_priority": "high"
        }
    ),
    
    AutonomousWorkflowType.HEALTH_CHECK: WorkflowConfig(
        workflow_type=AutonomousWorkflowType.HEALTH_CHECK,
        name="System Health Check",
        description="Monitor overall system health and trigger recovery if needed",
        priority=WorkflowPriority.HIGH,
        triggers=[
            WorkflowTrigger(
                trigger_type="schedule",
                cron_expression="*/15 * * * *"  # Every 15 minutes
            )
        ],
        parameters={
            "check_all_integrations": True,
            "auto_recovery": True,
            "alert_on_degradation": True
        }
    )
}

