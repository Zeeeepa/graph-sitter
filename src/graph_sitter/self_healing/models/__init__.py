"""
Self-Healing Models Module

Contains data models and configurations for the self-healing architecture.
"""

from .config import SelfHealingConfig, ErrorDetectionConfig, RecoveryConfig, LearningConfig
from .events import ErrorEvent, RecoveryAction, DiagnosisResult, HealthMetric
from .enums import ErrorSeverity, ErrorType, RecoveryStatus, HealthStatus

__all__ = [
    "SelfHealingConfig",
    "ErrorDetectionConfig", 
    "RecoveryConfig",
    "LearningConfig",
    "ErrorEvent",
    "RecoveryAction",
    "DiagnosisResult",
    "HealthMetric",
    "ErrorSeverity",
    "ErrorType",
    "RecoveryStatus",
    "HealthStatus",
]

