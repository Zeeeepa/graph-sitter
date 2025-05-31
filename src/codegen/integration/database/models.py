"""
Database Models

Data models for the OpenEvolve integration evaluation system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid


@dataclass
class EvaluationSession:
    """Represents an evaluation session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_name: str = ""
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentEvaluation:
    """Represents a component evaluation result."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    component_type: str = ""  # 'evaluator', 'database', 'controller'
    component_name: str = ""
    evaluation_timestamp: datetime = field(default_factory=datetime.now)
    effectiveness_score: float = 0.0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int = 0
    memory_usage_mb: Optional[float] = None
    success_rate: float = 0.0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationStep:
    """Represents a step in the evaluation process."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    component_evaluation_id: str = ""
    step_number: int = 0
    step_name: str = ""
    step_description: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    status: str = "pending"  # 'pending', 'running', 'completed', 'failed'
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    effectiveness_contribution: float = 0.0


@dataclass
class OutcomeCorrelation:
    """Represents outcome vs effectiveness correlation data."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    component_type: str = ""
    expected_outcome: Dict[str, Any] = field(default_factory=dict)
    actual_outcome: Dict[str, Any] = field(default_factory=dict)
    correlation_score: float = 0.0  # -1.0 to 1.0
    effectiveness_impact: float = 0.0
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    analysis_method: str = "statistical"
    confidence_level: float = 0.95
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAnalysis:
    """Represents a performance analysis result."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    component_type: str = ""
    analysis_type: str = ""  # 'bottleneck', 'optimization', 'regression'
    baseline_metrics: Dict[str, Any] = field(default_factory=dict)
    current_metrics: Dict[str, Any] = field(default_factory=dict)
    improvement_percentage: float = 0.0
    optimization_suggestions: List[str] = field(default_factory=list)
    priority_level: int = 3  # 1=high, 2=medium, 3=low
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    analyst_agent: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentExecution:
    """Represents an OpenEvolve agent execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    agent_type: str = ""  # 'evaluator_agent', 'database_agent', 'selection_controller'
    agent_instance_id: str = ""
    execution_start: datetime = field(default_factory=datetime.now)
    execution_end: Optional[datetime] = None
    execution_status: str = "running"
    input_parameters: Dict[str, Any] = field(default_factory=dict)
    output_results: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[str] = None
    parent_execution_id: Optional[str] = None


@dataclass
class EvaluationMetric:
    """Represents an evaluation metric."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    metric_name: str = ""
    metric_category: str = ""  # 'effectiveness', 'performance', 'reliability'
    metric_value: float = 0.0
    metric_unit: str = ""
    aggregation_period: str = "real-time"  # 'real-time', 'hourly', 'daily', 'session'
    timestamp: datetime = field(default_factory=datetime.now)
    component_filter: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

