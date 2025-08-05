"""
Database models for self-healing architecture.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID


@dataclass
class ErrorIncident:
    """Database model for error incidents."""
    id: UUID
    error_type: str
    severity: str
    message: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    diagnosis: Optional[Dict[str, Any]] = None
    recovery_actions: Optional[Dict[str, Any]] = None
    effectiveness_score: Optional[float] = None
    source_component: Optional[str] = None
    stack_trace: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class RecoveryProcedure:
    """Database model for recovery procedures."""
    id: UUID
    error_pattern: str
    procedure_steps: Dict[str, Any]
    success_rate: float = 0.0
    execution_count: int = 0
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    description: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    enabled: bool = True


@dataclass
class SystemHealthMetric:
    """Database model for system health metrics."""
    id: UUID
    metric_name: str
    current_value: float
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    status: str = "unknown"
    measured_at: Optional[datetime] = None
    component: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class DiagnosisResultDB:
    """Database model for diagnosis results."""
    id: UUID
    error_event_id: UUID
    root_cause: str
    confidence: str
    recommended_actions: Optional[List[str]] = None
    analysis_data: Optional[Dict[str, Any]] = None
    correlated_events: Optional[List[UUID]] = None
    created_at: Optional[datetime] = None


@dataclass
class RecoveryActionDB:
    """Database model for recovery actions."""
    id: UUID
    error_event_id: UUID
    diagnosis_id: Optional[UUID] = None
    action_type: str = ""
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: str = "pending"
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class LearningPattern:
    """Database model for learning patterns."""
    id: UUID
    pattern_type: str
    pattern_data: Dict[str, Any]
    effectiveness_score: Optional[float] = None
    usage_count: int = 0
    last_used: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

