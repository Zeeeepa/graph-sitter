"""
Event models for the self-healing architecture.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

from .enums import ErrorSeverity, ErrorType, RecoveryStatus, HealthStatus, DiagnosisConfidence


@dataclass
class ErrorEvent:
    """Represents an error event detected by the system."""
    id: str = field(default_factory=lambda: str(uuid4()))
    error_type: ErrorType = ErrorType.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    source_component: Optional[str] = None
    stack_trace: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
            "detected_at": self.detected_at.isoformat(),
            "source_component": self.source_component,
            "stack_trace": self.stack_trace,
            "metrics": self.metrics,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorEvent":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            error_type=ErrorType(data["error_type"]),
            severity=ErrorSeverity(data["severity"]),
            message=data["message"],
            context=data.get("context", {}),
            detected_at=datetime.fromisoformat(data["detected_at"]),
            source_component=data.get("source_component"),
            stack_trace=data.get("stack_trace"),
            metrics=data.get("metrics", {}),
            tags=data.get("tags", []),
        )


@dataclass
class DiagnosisResult:
    """Result of automated diagnosis."""
    id: str = field(default_factory=lambda: str(uuid4()))
    error_event_id: str = ""
    root_cause: str = ""
    confidence: DiagnosisConfidence = DiagnosisConfidence.MEDIUM
    recommended_actions: List[str] = field(default_factory=list)
    analysis_data: Dict[str, Any] = field(default_factory=dict)
    correlated_events: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "error_event_id": self.error_event_id,
            "root_cause": self.root_cause,
            "confidence": self.confidence.value,
            "recommended_actions": self.recommended_actions,
            "analysis_data": self.analysis_data,
            "correlated_events": self.correlated_events,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class RecoveryAction:
    """Represents a recovery action to be executed."""
    id: str = field(default_factory=lambda: str(uuid4()))
    error_event_id: str = ""
    diagnosis_id: Optional[str] = None
    action_type: str = ""
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: RecoveryStatus = RecoveryStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "error_event_id": self.error_event_id,
            "diagnosis_id": self.diagnosis_id,
            "action_type": self.action_type,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


@dataclass
class HealthMetric:
    """Represents a system health metric."""
    id: str = field(default_factory=lambda: str(uuid4()))
    metric_name: str = ""
    current_value: float = 0.0
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    status: HealthStatus = HealthStatus.UNKNOWN
    measured_at: datetime = field(default_factory=datetime.utcnow)
    component: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "status": self.status.value,
            "measured_at": self.measured_at.isoformat(),
            "component": self.component,
            "tags": self.tags,
        }
    
    def evaluate_status(self) -> HealthStatus:
        """Evaluate health status based on thresholds."""
        if self.threshold_critical is not None and self.current_value >= self.threshold_critical:
            self.status = HealthStatus.CRITICAL
        elif self.threshold_warning is not None and self.current_value >= self.threshold_warning:
            self.status = HealthStatus.WARNING
        else:
            self.status = HealthStatus.HEALTHY
        return self.status

