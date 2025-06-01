"""Data models for pattern analysis engine."""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import uuid
from datetime import datetime


class PatternType(Enum):
    """Types of patterns that can be detected."""
    TASK_PERFORMANCE = "task_performance"
    PIPELINE_EFFICIENCY = "pipeline_efficiency"
    RESOURCE_USAGE = "resource_usage"
    ERROR_FREQUENCY = "error_frequency"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    TEMPORAL_TREND = "temporal_trend"


class ModelType(Enum):
    """Types of ML models."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES = "time_series"


class RecommendationType(Enum):
    """Types of optimization recommendations."""
    CONFIGURATION_TUNING = "configuration_tuning"
    WORKFLOW_IMPROVEMENT = "workflow_improvement"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    PERFORMANCE_ENHANCEMENT = "performance_enhancement"
    ERROR_PREVENTION = "error_prevention"


@dataclass
class Pattern:
    """Represents a detected pattern."""
    id: str
    pattern_type: PatternType
    pattern_data: Dict[str, Any]
    significance_score: float
    detected_at: datetime
    frequency: int
    impact_score: float
    confidence: float = 0.0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class MLModel:
    """Represents a machine learning model."""
    id: str
    model_name: str
    model_type: ModelType
    version: str
    accuracy: float
    training_data_size: int
    trained_at: datetime
    deployed_at: Optional[datetime] = None
    model_data: Optional[bytes] = None
    hyperparameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.hyperparameters is None:
            self.hyperparameters = {}


@dataclass
class Prediction:
    """Represents a model prediction."""
    id: str
    model_id: str
    prediction_type: str
    input_data: Dict[str, Any]
    prediction_result: Dict[str, Any]
    confidence_score: float
    actual_outcome: Optional[Dict[str, Any]] = None
    accuracy_score: Optional[float] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class OptimizationRecommendation:
    """Represents an optimization recommendation."""
    id: str
    recommendation_type: RecommendationType
    target_component: str
    recommendation_data: Dict[str, Any]
    expected_impact: Dict[str, Any]
    priority_score: float
    status: str = "pending"
    implemented_at: Optional[datetime] = None
    effectiveness_score: Optional[float] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class TaskMetrics:
    """Metrics for task performance analysis."""
    task_id: str
    task_type: str
    duration: float
    success: bool
    resource_usage: Dict[str, float]
    complexity_score: float
    timestamp: datetime
    error_message: Optional[str] = None


@dataclass
class PipelineMetrics:
    """Metrics for pipeline performance analysis."""
    pipeline_id: str
    pipeline_name: str
    total_duration: float
    task_count: int
    success_rate: float
    throughput: float
    resource_efficiency: float
    timestamp: datetime
    bottlenecks: List[str] = None
    
    def __post_init__(self):
        if self.bottlenecks is None:
            self.bottlenecks = []


@dataclass
class FeatureVector:
    """Feature vector for ML models."""
    features: Dict[str, Union[float, int, str]]
    target: Optional[Union[float, int, str]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for ML models."""
    model_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: Optional[float] = None
    mean_squared_error: Optional[float] = None
    mean_absolute_error: Optional[float] = None
    evaluated_at: datetime = None
    
    def __post_init__(self):
        if self.evaluated_at is None:
            self.evaluated_at = datetime.utcnow()

