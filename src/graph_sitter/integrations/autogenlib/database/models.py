"""Database models for autogenlib integration."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class GenerationHistory(BaseModel):
    """Model for storing code generation history."""
    
    id: Optional[int] = Field(default=None, description="Unique identifier")
    module_name: str = Field(description="Name of the generated module")
    function_name: Optional[str] = Field(default=None, description="Name of the generated function")
    description: str = Field(description="Description used for generation")
    generated_code: str = Field(description="The generated code")
    context_used: Dict[str, Any] = Field(default_factory=dict, description="Context used for generation")
    success: bool = Field(description="Whether generation was successful")
    error_message: Optional[str] = Field(default=None, description="Error message if generation failed")
    generation_time: float = Field(description="Time taken for generation in seconds")
    model_used: str = Field(description="AI model used for generation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the generation occurred")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GenerationPattern(BaseModel):
    """Model for storing successful generation patterns."""
    
    id: Optional[int] = Field(default=None, description="Unique identifier")
    pattern_name: str = Field(description="Name of the pattern")
    pattern_type: str = Field(description="Type of pattern (function, class, module, etc.)")
    description_keywords: list[str] = Field(description="Keywords from successful descriptions")
    code_template: str = Field(description="Template code for this pattern")
    context_requirements: Dict[str, Any] = Field(default_factory=dict, description="Required context for this pattern")
    success_count: int = Field(default=1, description="Number of times this pattern was successful")
    last_used: datetime = Field(default_factory=datetime.utcnow, description="When this pattern was last used")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this pattern was created")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GenerationCache(BaseModel):
    """Model for caching generated code."""
    
    id: Optional[int] = Field(default=None, description="Unique identifier")
    cache_key: str = Field(description="Unique cache key")
    module_name: str = Field(description="Name of the cached module")
    function_name: Optional[str] = Field(default=None, description="Name of the cached function")
    description_hash: str = Field(description="Hash of the description used")
    context_hash: str = Field(description="Hash of the context used")
    generated_code: str = Field(description="The cached generated code")
    hit_count: int = Field(default=0, description="Number of times this cache was hit")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="When this cache was last accessed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this cache entry was created")
    expires_at: Optional[datetime] = Field(default=None, description="When this cache entry expires")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GenerationMetrics(BaseModel):
    """Model for storing generation metrics and analytics."""
    
    id: Optional[int] = Field(default=None, description="Unique identifier")
    date: datetime = Field(description="Date of the metrics")
    total_generations: int = Field(default=0, description="Total number of generations")
    successful_generations: int = Field(default=0, description="Number of successful generations")
    failed_generations: int = Field(default=0, description="Number of failed generations")
    average_generation_time: float = Field(default=0.0, description="Average generation time")
    cache_hits: int = Field(default=0, description="Number of cache hits")
    cache_misses: int = Field(default=0, description="Number of cache misses")
    most_common_patterns: list[str] = Field(default_factory=list, description="Most commonly used patterns")
    error_types: Dict[str, int] = Field(default_factory=dict, description="Count of different error types")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

