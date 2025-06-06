"""
Dashboard extension for Contexten - Multi-layered workflow orchestration dashboard.

This extension provides a comprehensive dashboard UI system for managing projects,
workflows, and automated development processes through GitHub, Linear, Slack, and
Codegen SDK integrations.

Features:
- Project pinning and management
- Requirements-based plan generation
- Multi-layered workflow orchestration (Prefect, ControlFlow, MCP)
- Real-time progress tracking
- Quality gates and validation
- Automated PR and issue management
"""

from .dashboard import Dashboard
from .models import (
    Project,
    ProjectPin,
    WorkflowPlan,
    WorkflowTask,
    WorkflowExecution,
    QualityGate,
    ProjectSettings,
)

__all__ = [
    "Dashboard",
    "Project",
    "ProjectPin", 
    "WorkflowPlan",
    "WorkflowTask",
    "WorkflowExecution",
    "QualityGate",
    "ProjectSettings",
]

