"""Data models for OpenEvolve integration."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EvaluationStatus(str, Enum):
    """Status of an evaluation."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationTrigger(str, Enum):
    """Types of events that can trigger evaluations."""
    TASK_FAILURE = "task_failure"
    PIPELINE_FAILURE = "pipeline_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class EvaluationRequest(BaseModel):
    """Request model for creating an evaluation."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique evaluation ID")
    trigger_event: EvaluationTrigger = Field(description="Event that triggered the evaluation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context data for the evaluation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    priority: int = Field(default=5, ge=1, le=10, description="Evaluation priority (1=highest, 10=lowest)")
    timeout: Optional[int] = Field(default=None, description="Evaluation timeout in seconds")
    
    class Config:
        use_enum_values = True


class EvaluationMetrics(BaseModel):
    """Metrics collected during evaluation."""
    
    accuracy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    performance_score: Optional[float] = Field(default=None, ge=0.0)
    improvement_score: Optional[float] = Field(default=None)
    execution_time: Optional[float] = Field(default=None, ge=0.0)
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Result of an evaluation."""
    
    id: UUID = Field(description="Evaluation ID")
    evaluation_id: str = Field(description="OpenEvolve evaluation ID")
    status: EvaluationStatus = Field(description="Current status")
    submitted_at: datetime = Field(description="When the evaluation was submitted")
    started_at: Optional[datetime] = Field(default=None, description="When the evaluation started")
    completed_at: Optional[datetime] = Field(default=None, description="When the evaluation completed")
    results: Dict[str, Any] = Field(default_factory=dict, description="Evaluation results")
    metrics: Optional[EvaluationMetrics] = Field(default=None, description="Evaluation metrics")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    class Config:
        use_enum_values = True


class EvaluationSummary(BaseModel):
    """Summary of evaluation results for reporting."""
    
    total_evaluations: int = Field(description="Total number of evaluations")
    completed_evaluations: int = Field(description="Number of completed evaluations")
    failed_evaluations: int = Field(description="Number of failed evaluations")
    average_execution_time: Optional[float] = Field(default=None, description="Average execution time")
    average_improvement_score: Optional[float] = Field(default=None, description="Average improvement score")
    success_rate: float = Field(description="Success rate percentage")
    last_evaluation_at: Optional[datetime] = Field(default=None, description="Last evaluation timestamp")


class SystemImprovement(BaseModel):
    """System improvement recommendation from OpenEvolve."""
    
    id: UUID = Field(default_factory=uuid4)
    evaluation_id: UUID = Field(description="Source evaluation ID")
    improvement_type: str = Field(description="Type of improvement")
    description: str = Field(description="Description of the improvement")
    priority: int = Field(ge=1, le=10, description="Priority level")
    estimated_impact: Optional[float] = Field(default=None, description="Estimated impact score")
    implementation_complexity: Optional[str] = Field(default=None, description="Implementation complexity")
    applied: bool = Field(default=False, description="Whether the improvement has been applied")
    applied_at: Optional[datetime] = Field(default=None, description="When the improvement was applied")
    results: Dict[str, Any] = Field(default_factory=dict, description="Results after applying improvement")

