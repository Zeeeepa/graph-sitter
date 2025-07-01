# Linear integration module exports

# Legacy components (backward compatibility)
from .assignment_detector import AssignmentDetector
from .config import LinearIntegrationConfig, get_linear_config, create_config_template
from .enhanced_client import EnhancedLinearClient
from .integration_agent import LinearIntegrationAgent, create_linear_integration_agent
from .linear_client import LinearClient
from .types import (
from .types import LinearUser, LinearTeam, LinearComment, LinearIssue, LinearEvent
from .webhook_processor import WebhookProcessor
from .workflow_automation import WorkflowAutomation
    LinearEventType, LinearEventAction, AssignmentAction, AssignmentEvent,
    TaskStatus, TaskProgress, WorkflowTask, WebhookEvent, IntegrationStatus,
    ComponentStats, LinearIntegrationMetrics
)

__version__ = "2.0.0"
__all__ = [
    # Legacy exports
    "LinearClient",
    "LinearUser", 
    "LinearTeam",
    "LinearComment",
    "LinearIssue", 
    "LinearEvent",
    
    # Configuration
    "LinearIntegrationConfig",
    "get_linear_config",
    "create_config_template",
    
    # Core components
    "EnhancedLinearClient",
    "WebhookProcessor",
    "AssignmentDetector", 
    "WorkflowAutomation",
    "LinearIntegrationAgent",
    "create_linear_integration_agent",
    
    # Types
    "LinearEventType",
    "LinearEventAction", 
    "AssignmentAction",
    "AssignmentEvent",
    "TaskStatus",
    "TaskProgress",
    "WorkflowTask", 
    "WebhookEvent",
    "IntegrationStatus",
    "ComponentStats",
    "LinearIntegrationMetrics"
]

