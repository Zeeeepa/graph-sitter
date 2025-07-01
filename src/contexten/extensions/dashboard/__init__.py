"""
Dashboard Extension for Contexten

Provides comprehensive dashboard functionality that integrates all Contexten extensions
into a unified project management and workflow automation system.

Main Components:
- Dashboard: Central orchestration and API endpoints
- ProjectManager: GitHub project discovery and management
- PlanningEngine: Codegen SDK integration for automated planning
- WorkflowEngine: ControlFlow + Prefect + Codegen orchestration
- QualityManager: Grainchain + Graph-sitter validation
- EventCoordinator: Unified event bus for cross-extension communication
- SettingsManager: Secure configuration and API key management

Usage:
    from contexten.extensions.dashboard import Dashboard
    from contexten.extensions.contexten_app import ContextenApp
    
    # Initialize dashboard with contexten app
    app = ContextenApp("dashboard-app")
    dashboard = Dashboard(app)
    
    # Start dashboard server
    dashboard.start()
"""

from .dashboard import Dashboard, DashboardEventHandler
from .project_manager import ProjectManager
from .planning_engine import PlanningEngine
from .workflow_engine import WorkflowEngine
from .quality_manager import QualityManager
from .event_coordinator import EventCoordinator
from .settings_manager import SettingsManager
from .models import (
    DashboardProject,
    DashboardPlan,
    DashboardTask,
    WorkflowEvent,
    QualityGateResult
)

__version__ = "1.0.0"
__all__ = [
    "Dashboard",
    "DashboardEventHandler",
    "ProjectManager",
    "PlanningEngine", 
    "WorkflowEngine",
    "QualityManager",
    "EventCoordinator",
    "SettingsManager",
    "DashboardProject",
    "DashboardPlan",
    "DashboardTask",
    "WorkflowEvent",
    "QualityGateResult"
]

