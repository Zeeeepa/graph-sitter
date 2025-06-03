"""Data models for autogenlib module."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a Codegen task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRequest(BaseModel):
    """Request model for Codegen tasks."""
    prompt: str = Field(..., description="The task prompt for the Codegen agent")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the task")
    codebase_path: Optional[str] = Field(None, description="Path to the codebase to analyze")
    enhance_context: bool = Field(True, description="Whether to enhance prompt with codebase context")
    timeout: Optional[int] = Field(300, description="Task timeout in seconds")
    priority: int = Field(1, description="Task priority (1-10, higher is more urgent)")


class TaskResponse(BaseModel):
    """Response model for Codegen tasks."""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    result: Optional[str] = Field(None, description="Task result when completed")
    error: Optional[str] = Field(None, description="Error message if task failed")
    created_at: str = Field(..., description="Task creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional task metadata")


class ContextData(BaseModel):
    """Model for codebase context data."""
    codebase_summary: Optional[str] = Field(None, description="Overall codebase summary")
    file_summaries: Optional[List[str]] = Field(None, description="Relevant file summaries")
    class_summaries: Optional[List[str]] = Field(None, description="Relevant class summaries")
    function_summaries: Optional[List[str]] = Field(None, description="Relevant function summaries")
    symbol_summaries: Optional[List[str]] = Field(None, description="Relevant symbol summaries")


class AgentConfig(BaseModel):
    """Configuration for Codegen agent behavior."""
    model: Optional[str] = Field(None, description="AI model to use")
    temperature: Optional[float] = Field(None, description="Model temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in response")
    custom_instructions: Optional[str] = Field(None, description="Custom instructions for the agent")


class UsageStats(BaseModel):
    """Usage statistics for tracking and cost management."""
    total_requests: int = Field(0, description="Total number of requests")
    successful_requests: int = Field(0, description="Number of successful requests")
    failed_requests: int = Field(0, description="Number of failed requests")
    total_tokens: int = Field(0, description="Total tokens used")
    estimated_cost: float = Field(0.0, description="Estimated cost in USD")
    last_reset: str = Field(..., description="Last statistics reset timestamp")

