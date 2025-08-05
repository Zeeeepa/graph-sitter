"""Data models for error detection and classification."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    BUILD_FAILURE = "build_failure"
    TEST_FAILURE = "test_failure"
    DEPENDENCY_ISSUE = "dependency_issue"
    CONFIGURATION_ERROR = "configuration_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_ISSUE = "network_issue"
    SECURITY_VIOLATION = "security_violation"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    UNKNOWN = "unknown"


class HealingStrategy(Enum):
    """Self-healing strategies."""
    RETRY = "retry"
    ROLLBACK = "rollback"
    RESOURCE_ADJUSTMENT = "resource_adjustment"
    DEPENDENCY_UPDATE = "dependency_update"
    CONFIGURATION_FIX = "configuration_fix"
    ALTERNATIVE_APPROACH = "alternative_approach"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    IGNORE = "ignore"


class ErrorPattern(BaseModel):
    """Error pattern for classification."""
    id: str
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    patterns: List[str]  # Regex patterns to match
    keywords: List[str]  # Keywords to look for
    context_patterns: List[str] = Field(default_factory=list)
    confidence_threshold: float = 0.8
    healing_strategies: List[HealingStrategy] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorClassification(BaseModel):
    """Error classification result."""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    confidence: float
    matched_patterns: List[str]
    context: Dict[str, Any]
    suggested_healing: List[HealingStrategy]
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealingAction(BaseModel):
    """Self-healing action definition."""
    id: str
    strategy: HealingStrategy
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    prerequisites: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    rollback_actions: List[str] = Field(default_factory=list)
    max_attempts: int = 3
    timeout_seconds: int = 300
    
    class Config:
        use_enum_values = True


class ErrorInstance(BaseModel):
    """Specific error instance."""
    id: str
    pipeline_id: str
    stage: str
    error_message: str
    stack_trace: Optional[str] = None
    log_context: List[str] = Field(default_factory=list)
    classification: Optional[ErrorClassification] = None
    healing_attempts: List[Dict[str, Any]] = Field(default_factory=list)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealingResult(BaseModel):
    """Result of a healing action."""
    action_id: str
    strategy: HealingStrategy
    success: bool
    error_message: Optional[str] = None
    execution_time: float
    side_effects: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

