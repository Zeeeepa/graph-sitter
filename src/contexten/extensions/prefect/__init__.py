"""
Prefect Integration for Autonomous CI/CD Workflows

This module provides Prefect-based workflow orchestration for the autonomous CI/CD system,
enabling intelligent task scheduling, monitoring, and execution coordination.
"""

from .workflows import (
    autonomous_maintenance_flow,
    failure_analysis_flow,
    dependency_update_flow,
    performance_optimization_flow,
)
from .tasks import (
    analyze_codebase_task,
    generate_fixes_task,
    apply_fixes_task,
    monitor_performance_task,
    update_dependencies_task,
)
from .config import PrefectConfig
from .client import PrefectOrchestrator

__all__ = [
    "autonomous_maintenance_flow",
    "failure_analysis_flow", 
    "dependency_update_flow",
    "performance_optimization_flow",
    "analyze_codebase_task",
    "generate_fixes_task",
    "apply_fixes_task",
    "monitor_performance_task",
    "update_dependencies_task",
    "PrefectConfig",
    "PrefectOrchestrator",
]

