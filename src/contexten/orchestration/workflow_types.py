"""
Workflow Types for Autonomous CI/CD Operations

This module defines all the workflow types supported by the autonomous orchestration system.
"""

from enum import Enum


class AutonomousWorkflowType(Enum):
    """
    Enumeration of autonomous workflow types supported by the orchestration system.
    
    Each workflow type represents a specific autonomous operation that can be
    triggered and managed by the orchestrator.
    """
    
    # Core Analysis Workflows
    COMPONENT_ANALYSIS = "component_analysis"
    FAILURE_ANALYSIS = "failure_analysis"
    PERFORMANCE_MONITORING = "performance_monitoring"
    CODE_QUALITY_CHECK = "code_quality_check"
    
    # Maintenance Workflows
    DEPENDENCY_MANAGEMENT = "dependency_management"
    SECURITY_AUDIT = "security_audit"
    TEST_OPTIMIZATION = "test_optimization"
    DEAD_CODE_CLEANUP = "dead_code_cleanup"
    
    # Integration Workflows
    LINEAR_SYNC = "linear_sync"
    GITHUB_AUTOMATION = "github_automation"
    SLACK_NOTIFICATIONS = "slack_notifications"
    
    # System Workflows
    HEALTH_CHECK = "health_check"
    BACKUP_OPERATIONS = "backup_operations"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    
    # Advanced Workflows
    AUTONOMOUS_REFACTORING = "autonomous_refactoring"
    INTELLIGENT_DEPLOYMENT = "intelligent_deployment"
    PREDICTIVE_MAINTENANCE = "predictive_maintenance"
    
    # Recovery Workflows
    ERROR_HEALING = "error_healing"
    SYSTEM_RECOVERY = "system_recovery"
    DATA_RECOVERY = "data_recovery"


class WorkflowPriority(Enum):
    """Priority levels for workflow execution"""
    
    CRITICAL = 10    # System-critical operations
    HIGH = 8         # Important operations that should run soon
    NORMAL = 5       # Standard operations
    LOW = 3          # Background operations
    MAINTENANCE = 1  # Low-priority maintenance tasks


class WorkflowCategory(Enum):
    """Categories for organizing workflows"""
    
    ANALYSIS = "analysis"
    MAINTENANCE = "maintenance"
    INTEGRATION = "integration"
    SYSTEM = "system"
    RECOVERY = "recovery"
    ADVANCED = "advanced"


# Mapping of workflow types to their categories and default priorities
WORKFLOW_METADATA = {
    # Analysis Workflows
    AutonomousWorkflowType.COMPONENT_ANALYSIS: {
        "category": WorkflowCategory.ANALYSIS,
        "priority": WorkflowPriority.NORMAL,
        "description": "Comprehensive analysis of code components for quality and optimization",
        "estimated_duration_minutes": 15,
        "requires_human_approval": False
    },
    AutonomousWorkflowType.FAILURE_ANALYSIS: {
        "category": WorkflowCategory.RECOVERY,
        "priority": WorkflowPriority.HIGH,
        "description": "Analyze and automatically fix CI/CD failures",
        "estimated_duration_minutes": 20,
        "requires_human_approval": False
    },
    AutonomousWorkflowType.PERFORMANCE_MONITORING: {
        "category": WorkflowCategory.ANALYSIS,
        "priority": WorkflowPriority.NORMAL,
        "description": "Monitor system performance and identify optimization opportunities",
        "estimated_duration_minutes": 10,
        "requires_human_approval": False
    },
    AutonomousWorkflowType.CODE_QUALITY_CHECK: {
        "category": WorkflowCategory.ANALYSIS,
        "priority": WorkflowPriority.NORMAL,
        "description": "Comprehensive code quality analysis and improvement suggestions",
        "estimated_duration_minutes": 12,
        "requires_human_approval": False
    },
    
    # Maintenance Workflows
    AutonomousWorkflowType.DEPENDENCY_MANAGEMENT: {
        "category": WorkflowCategory.MAINTENANCE,
        "priority": WorkflowPriority.NORMAL,
        "description": "Automated dependency updates and security patching",
        "estimated_duration_minutes": 25,
        "requires_human_approval": True
    },
    AutonomousWorkflowType.SECURITY_AUDIT: {
        "category": WorkflowCategory.MAINTENANCE,
        "priority": WorkflowPriority.HIGH,
        "description": "Comprehensive security audit and vulnerability remediation",
        "estimated_duration_minutes": 30,
        "requires_human_approval": True
    },
    AutonomousWorkflowType.TEST_OPTIMIZATION: {
        "category": WorkflowCategory.MAINTENANCE,
        "priority": WorkflowPriority.NORMAL,
        "description": "Optimize test suite performance and coverage",
        "estimated_duration_minutes": 20,
        "requires_human_approval": False
    },
    AutonomousWorkflowType.DEAD_CODE_CLEANUP: {
        "category": WorkflowCategory.MAINTENANCE,
        "priority": WorkflowPriority.LOW,
        "description": "Identify and remove dead code and unused dependencies",
        "estimated_duration_minutes": 15,
        "requires_human_approval": True
    },
    
    # Integration Workflows
    AutonomousWorkflowType.LINEAR_SYNC: {
        "category": WorkflowCategory.INTEGRATION,
        "priority": WorkflowPriority.NORMAL,
        "description": "Synchronize with Linear for task management and tracking",
        "estimated_duration_minutes": 5,
        "requires_human_approval": False
    },
    AutonomousWorkflowType.GITHUB_AUTOMATION: {
        "category": WorkflowCategory.INTEGRATION,
        "priority": WorkflowPriority.NORMAL,
        "description": "Automate GitHub operations like PR management and deployments",
        "estimated_duration_minutes": 8,
        "requires_human_approval": False
    },
    AutonomousWorkflowType.SLACK_NOTIFICATIONS: {
        "category": WorkflowCategory.INTEGRATION,
        "priority": WorkflowPriority.LOW,
        "description": "Send notifications and status updates to Slack",
        "estimated_duration_minutes": 2,
        "requires_human_approval": False
    },
    
    # System Workflows
    AutonomousWorkflowType.HEALTH_CHECK: {
        "category": WorkflowCategory.SYSTEM,
        "priority": WorkflowPriority.NORMAL,
        "description": "Comprehensive system health monitoring and reporting",
        "estimated_duration_minutes": 5,
        "requires_human_approval": False
    },
    AutonomousWorkflowType.BACKUP_OPERATIONS: {
        "category": WorkflowCategory.SYSTEM,
        "priority": WorkflowPriority.NORMAL,
        "description": "Automated backup and data protection operations",
        "estimated_duration_minutes": 10,
        "requires_human_approval": False
    },
    AutonomousWorkflowType.RESOURCE_OPTIMIZATION: {
        "category": WorkflowCategory.SYSTEM,
        "priority": WorkflowPriority.LOW,
        "description": "Optimize system resource usage and capacity planning",
        "estimated_duration_minutes": 15,
        "requires_human_approval": False
    },
    
    # Advanced Workflows
    AutonomousWorkflowType.AUTONOMOUS_REFACTORING: {
        "category": WorkflowCategory.ADVANCED,
        "priority": WorkflowPriority.LOW,
        "description": "AI-powered code refactoring and architectural improvements",
        "estimated_duration_minutes": 45,
        "requires_human_approval": True
    },
    AutonomousWorkflowType.INTELLIGENT_DEPLOYMENT: {
        "category": WorkflowCategory.ADVANCED,
        "priority": WorkflowPriority.HIGH,
        "description": "Smart deployment with automated rollback and monitoring",
        "estimated_duration_minutes": 20,
        "requires_human_approval": True
    },
    AutonomousWorkflowType.PREDICTIVE_MAINTENANCE: {
        "category": WorkflowCategory.ADVANCED,
        "priority": WorkflowPriority.LOW,
        "description": "Predictive analysis for proactive system maintenance",
        "estimated_duration_minutes": 30,
        "requires_human_approval": False
    },
    
    # Recovery Workflows
    AutonomousWorkflowType.ERROR_HEALING: {
        "category": WorkflowCategory.RECOVERY,
        "priority": WorkflowPriority.CRITICAL,
        "description": "Autonomous error detection and healing",
        "estimated_duration_minutes": 10,
        "requires_human_approval": False
    },
    AutonomousWorkflowType.SYSTEM_RECOVERY: {
        "category": WorkflowCategory.RECOVERY,
        "priority": WorkflowPriority.CRITICAL,
        "description": "System-wide recovery and restoration operations",
        "estimated_duration_minutes": 30,
        "requires_human_approval": True
    },
    AutonomousWorkflowType.DATA_RECOVERY: {
        "category": WorkflowCategory.RECOVERY,
        "priority": WorkflowPriority.CRITICAL,
        "description": "Data recovery and integrity restoration",
        "estimated_duration_minutes": 25,
        "requires_human_approval": True
    }
}


def get_workflow_metadata(workflow_type: AutonomousWorkflowType) -> dict:
    """Get metadata for a specific workflow type"""
    return WORKFLOW_METADATA.get(workflow_type, {
        "category": WorkflowCategory.SYSTEM,
        "priority": WorkflowPriority.NORMAL,
        "description": f"Autonomous workflow: {workflow_type.value}",
        "estimated_duration_minutes": 15,
        "requires_human_approval": False
    })


def get_workflows_by_category(category: WorkflowCategory) -> list[AutonomousWorkflowType]:
    """Get all workflows in a specific category"""
    return [
        workflow_type for workflow_type, metadata in WORKFLOW_METADATA.items()
        if metadata.get("category") == category
    ]


def get_workflows_by_priority(priority: WorkflowPriority) -> list[AutonomousWorkflowType]:
    """Get all workflows with a specific priority"""
    return [
        workflow_type for workflow_type, metadata in WORKFLOW_METADATA.items()
        if metadata.get("priority") == priority
    ]


def requires_human_approval(workflow_type: AutonomousWorkflowType) -> bool:
    """Check if a workflow type requires human approval"""
    metadata = get_workflow_metadata(workflow_type)
    return metadata.get("requires_human_approval", False)

