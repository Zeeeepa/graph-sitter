"""
Self-Healing Architecture Module

This module implements automated error detection, diagnosis, and recovery capabilities
for the graph-sitter system, enabling continuous learning and self-optimization.
"""

from .error_detection.service import ErrorDetectionService
from .diagnosis.engine import DiagnosisEngine
from .recovery.system import RecoverySystem
from .monitoring.health_monitor import HealthMonitor
from .models.config import SelfHealingConfig
from .models.events import ErrorEvent, RecoveryAction

__all__ = [
    "ErrorDetectionService",
    "DiagnosisEngine", 
    "RecoverySystem",
    "HealthMonitor",
    "SelfHealingConfig",
    "ErrorEvent",
    "RecoveryAction",
]

