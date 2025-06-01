"""Configuration models for the pattern analysis engine."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


@dataclass
class TimeRange:
    """Time range for data extraction."""
    start_timestamp: float
    end_timestamp: float


class DataPipelineConfig(BaseModel):
    """Configuration for data pipeline."""
    batch_size: int = Field(default=10000, description="Batch size for data processing")
    processing_interval: int = Field(default=3600, description="Processing interval in seconds")
    retention_days: int = Field(default=365, description="Data retention period in days")
    max_workers: int = Field(default=4, description="Maximum number of worker threads")


class MLModelConfig(BaseModel):
    """Configuration for ML models."""
    training_interval: int = Field(default=86400, description="Training interval in seconds (daily)")
    min_training_samples: int = Field(default=1000, description="Minimum samples required for training")
    accuracy_threshold: float = Field(default=0.8, description="Minimum accuracy threshold")
    model_cache_size: int = Field(default=10, description="Number of models to cache")


class RecommendationConfig(BaseModel):
    """Configuration for recommendation engine."""
    generation_interval: int = Field(default=3600, description="Recommendation generation interval in seconds")
    min_confidence: float = Field(default=0.7, description="Minimum confidence threshold")
    max_recommendations: int = Field(default=10, description="Maximum recommendations to generate")


class PatternAnalysisConfig(BaseModel):
    """Main configuration for pattern analysis engine."""
    data_pipeline: DataPipelineConfig = Field(default_factory=DataPipelineConfig)
    ml_models: MLModelConfig = Field(default_factory=MLModelConfig)
    recommendations: RecommendationConfig = Field(default_factory=RecommendationConfig)
    
    # Database connection settings
    database_url: Optional[str] = Field(default=None, description="Database connection URL")
    
    # Feature engineering settings
    feature_window_hours: int = Field(default=24, description="Time window for feature extraction in hours")
    pattern_significance_threshold: float = Field(default=0.05, description="Statistical significance threshold")
    
    # Model settings
    random_state: int = Field(default=42, description="Random state for reproducibility")
    cross_validation_folds: int = Field(default=5, description="Number of CV folds")
    
    class Config:
        """Pydantic config."""
        extra = "forbid"

