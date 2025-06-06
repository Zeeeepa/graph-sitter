"""
Dashboard Services Module.
Consolidated service layer for the dashboard extension.
"""

from .strands_orchestrator import StrandsOrchestrator
from .project_service import ProjectService
from .codegen_service import CodegenService
from .quality_service import QualityService
from .monitoring_service import MonitoringService

__all__ = [
    "StrandsOrchestrator",
    "ProjectService", 
    "CodegenService",
    "QualityService",
    "MonitoringService"
]

