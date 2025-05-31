"""Data models for pipeline management."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectType(Enum):
    """Supported project types."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    MIXED = "mixed"
    GENERIC = "generic"


class PipelineStatus(Enum):
    """Pipeline execution status."""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class PipelineStrategy(Enum):
    """Pipeline execution strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


class PipelineConfig(BaseModel):
    """Pipeline configuration model."""
    name: str
    strategy: PipelineStrategy = PipelineStrategy.ADAPTIVE
    stages: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    timeout_minutes: int = 30
    retry_attempts: int = 3
    parallel_jobs: int = 4
    resource_limits: Dict[str, str] = Field(default_factory=dict)
    quality_gates: Dict[str, Any] = Field(default_factory=dict)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class PipelineMetrics(BaseModel):
    """Pipeline execution metrics."""
    execution_time: float
    success_rate: float
    resource_usage: Dict[str, float]
    bottlenecks: List[str]
    optimization_opportunities: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineExecution(BaseModel):
    """Pipeline execution instance."""
    id: str
    config: PipelineConfig
    project_path: Path
    project_type: ProjectType
    status: PipelineStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: Optional[PipelineMetrics] = None
    workflow_run_id: Optional[str] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v)
        }


class PipelineOptimization(BaseModel):
    """Pipeline optimization data."""
    config_name: str
    successful_optimizations: List[Dict[str, Any]] = Field(default_factory=list)
    failed_optimizations: List[Dict[str, Any]] = Field(default_factory=list)
    performance_history: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ResourceAllocation(BaseModel):
    """Resource allocation configuration."""
    cpu_cores: int = 2
    memory_gb: int = 4
    disk_gb: int = 10
    gpu_enabled: bool = False
    network_bandwidth_mbps: int = 100
    
    
class QualityGate(BaseModel):
    """Quality gate configuration."""
    name: str
    threshold: float
    operator: str = "gte"  # gte, lte, eq, ne
    required: bool = True
    description: Optional[str] = None


class PipelineTemplate(BaseModel):
    """Pipeline template for reusable configurations."""
    name: str
    description: str
    project_types: List[ProjectType]
    config: PipelineConfig
    variables: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

