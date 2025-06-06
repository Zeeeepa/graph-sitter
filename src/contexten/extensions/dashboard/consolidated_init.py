"""
Consolidated Dashboard Extension - Main Module.
Combines the best elements from all three PRs into a unified system.
"""

from .consolidated_dashboard import ConsolidatedDashboard, create_consolidated_dashboard
from .consolidated_api import ConsolidatedDashboardAPI, create_dashboard_app
from .consolidated_models import (
    Project, Flow, Task, UserSettings, QualityGate,
    FlowStatus, TaskStatus, ServiceStatus, ProjectStatus, QualityGateStatus,
    ServiceStatusResponse, ProjectCreateRequest, ProjectUpdateRequest,
    FlowStartRequest, PlanGenerateRequest, CodegenTaskRequest,
    SystemHealthResponse, DashboardResponse, WebSocketEvent
)
from .services import (
    StrandsOrchestrator, ProjectService, CodegenService, 
    QualityService, MonitoringService
)

__version__ = "1.0.0"
__title__ = "Consolidated Strands Agent Dashboard"
__description__ = "Comprehensive dashboard for Strands tools ecosystem integration"

__all__ = [
    # Main classes
    "ConsolidatedDashboard",
    "ConsolidatedDashboardAPI",
    
    # Factory functions
    "create_consolidated_dashboard",
    "create_dashboard_app",
    
    # Data models
    "Project",
    "Flow", 
    "Task",
    "UserSettings",
    "QualityGate",
    
    # Enums
    "FlowStatus",
    "TaskStatus", 
    "ServiceStatus",
    "ProjectStatus",
    "QualityGateStatus",
    
    # Request/Response models
    "ServiceStatusResponse",
    "ProjectCreateRequest",
    "ProjectUpdateRequest", 
    "FlowStartRequest",
    "PlanGenerateRequest",
    "CodegenTaskRequest",
    "SystemHealthResponse",
    "DashboardResponse",
    "WebSocketEvent",
    
    # Services
    "StrandsOrchestrator",
    "ProjectService",
    "CodegenService",
    "QualityService", 
    "MonitoringService"
]


def setup_dashboard(contexten_app=None, **kwargs):
    """
    Setup function for easy integration with Contexten.
    
    Args:
        contexten_app: Optional Contexten application instance
        **kwargs: Additional configuration options
        
    Returns:
        ConsolidatedDashboard: Configured dashboard instance
    """
    dashboard = create_consolidated_dashboard(contexten_app)
    
    # Apply any additional configuration
    for key, value in kwargs.items():
        if hasattr(dashboard, key):
            setattr(dashboard, key, value)
    
    return dashboard


# Convenience imports for backward compatibility
Dashboard = ConsolidatedDashboard
DashboardAPI = ConsolidatedDashboardAPI

