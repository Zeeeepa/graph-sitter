"""
Configuration models for the self-healing architecture.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ErrorDetectionConfig:
    """Configuration for error detection system."""
    monitoring_interval: int = 30  # seconds
    threshold_cpu: float = 80.0  # percentage
    threshold_memory: float = 85.0  # percentage
    threshold_error_rate: float = 5.0  # percentage
    threshold_response_time: float = 2000.0  # milliseconds
    pattern_recognition_enabled: bool = True
    anomaly_detection_enabled: bool = True
    alert_escalation_timeout: int = 300  # seconds


@dataclass
class RecoveryConfig:
    """Configuration for recovery system."""
    max_retry_attempts: int = 3
    escalation_timeout: int = 300  # seconds
    rollback_enabled: bool = True
    auto_scaling_enabled: bool = True
    circuit_breaker_enabled: bool = True
    recovery_timeout: int = 600  # seconds


@dataclass
class LearningConfig:
    """Configuration for continuous learning system."""
    effectiveness_tracking: bool = True
    pattern_recognition: bool = True
    continuous_improvement: bool = True
    learning_rate: float = 0.1
    min_samples_for_learning: int = 10
    confidence_threshold: float = 0.8


@dataclass
class SelfHealingConfig:
    """Main configuration for self-healing architecture."""
    enabled: bool = True
    error_detection: ErrorDetectionConfig = None
    recovery: RecoveryConfig = None
    learning: LearningConfig = None
    database_url: Optional[str] = None
    log_level: str = "INFO"
    metrics_retention_days: int = 30
    
    def __post_init__(self):
        """Initialize sub-configurations if not provided."""
        if self.error_detection is None:
            self.error_detection = ErrorDetectionConfig()
        if self.recovery is None:
            self.recovery = RecoveryConfig()
        if self.learning is None:
            self.learning = LearningConfig()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SelfHealingConfig":
        """Create configuration from dictionary."""
        error_detection_dict = config_dict.get("error_detection", {})
        recovery_dict = config_dict.get("recovery", {})
        learning_dict = config_dict.get("learning", {})
        
        return cls(
            enabled=config_dict.get("enabled", True),
            error_detection=ErrorDetectionConfig(**error_detection_dict),
            recovery=RecoveryConfig(**recovery_dict),
            learning=LearningConfig(**learning_dict),
            database_url=config_dict.get("database_url"),
            log_level=config_dict.get("log_level", "INFO"),
            metrics_retention_days=config_dict.get("metrics_retention_days", 30),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "enabled": self.enabled,
            "error_detection": {
                "monitoring_interval": self.error_detection.monitoring_interval,
                "threshold_cpu": self.error_detection.threshold_cpu,
                "threshold_memory": self.error_detection.threshold_memory,
                "threshold_error_rate": self.error_detection.threshold_error_rate,
                "threshold_response_time": self.error_detection.threshold_response_time,
                "pattern_recognition_enabled": self.error_detection.pattern_recognition_enabled,
                "anomaly_detection_enabled": self.error_detection.anomaly_detection_enabled,
                "alert_escalation_timeout": self.error_detection.alert_escalation_timeout,
            },
            "recovery": {
                "max_retry_attempts": self.recovery.max_retry_attempts,
                "escalation_timeout": self.recovery.escalation_timeout,
                "rollback_enabled": self.recovery.rollback_enabled,
                "auto_scaling_enabled": self.recovery.auto_scaling_enabled,
                "circuit_breaker_enabled": self.recovery.circuit_breaker_enabled,
                "recovery_timeout": self.recovery.recovery_timeout,
            },
            "learning": {
                "effectiveness_tracking": self.learning.effectiveness_tracking,
                "pattern_recognition": self.learning.pattern_recognition,
                "continuous_improvement": self.learning.continuous_improvement,
                "learning_rate": self.learning.learning_rate,
                "min_samples_for_learning": self.learning.min_samples_for_learning,
                "confidence_threshold": self.learning.confidence_threshold,
            },
            "database_url": self.database_url,
            "log_level": self.log_level,
            "metrics_retention_days": self.metrics_retention_days,
        }

