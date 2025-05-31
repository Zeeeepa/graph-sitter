"""
TaskExecution tracking system for monitoring task execution
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Execution status tracking"""
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ResourceUsage(BaseModel):
    """Resource usage tracking"""
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    memory_mb: Optional[float] = Field(None, description="Memory usage in MB")
    disk_io_mb: Optional[float] = Field(None, description="Disk I/O in MB")
    network_io_mb: Optional[float] = Field(None, description="Network I/O in MB")
    gpu_percent: Optional[float] = Field(None, description="GPU usage percentage")


class ExecutionLog(BaseModel):
    """Individual execution log entry"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., description="Log level (DEBUG, INFO, WARN, ERROR)")
    message: str = Field(..., description="Log message")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class TaskExecution(BaseModel):
    """
    TaskExecution tracking system for comprehensive execution monitoring
    
    Features:
    - Resource usage monitoring and optimization
    - Execution result storage and analysis
    - Error handling and retry mechanisms
    - Detailed execution logging
    """
    
    # Core identifiers
    id: UUID = Field(default_factory=uuid4, description="Unique execution identifier")
    task_id: UUID = Field(..., description="Associated task ID")
    execution_number: int = Field(..., description="Execution attempt number")
    
    # Execution context
    executor_id: str = Field(..., description="ID of the executor (agent/worker)")
    executor_type: str = Field(..., description="Type of executor (codegen, claude, etc.)")
    execution_environment: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Execution environment details"
    )
    
    # Status and lifecycle
    status: ExecutionStatus = Field(default=ExecutionStatus.QUEUED)
    
    # Timing
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    
    # Resource monitoring
    resource_usage: ResourceUsage = Field(default_factory=ResourceUsage)
    peak_resource_usage: ResourceUsage = Field(default_factory=ResourceUsage)
    
    # Execution results
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    output: Optional[str] = Field(None, description="Execution output/logs")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    
    # Performance metrics
    execution_time_seconds: Optional[float] = Field(None, description="Total execution time")
    queue_time_seconds: Optional[float] = Field(None, description="Time spent in queue")
    
    # Execution logs
    logs: List[ExecutionLog] = Field(default_factory=list, description="Execution logs")
    
    # Retry and recovery
    retry_reason: Optional[str] = Field(None, description="Reason for retry")
    recovery_actions: List[str] = Field(default_factory=list, description="Recovery actions taken")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    def start_execution(self) -> None:
        """Mark execution as started"""
        self.status = ExecutionStatus.STARTING
        self.started_at = datetime.utcnow()
        
        if self.queued_at:
            self.queue_time_seconds = (self.started_at - self.queued_at).total_seconds()
    
    def mark_running(self) -> None:
        """Mark execution as running"""
        self.status = ExecutionStatus.RUNNING
        if not self.started_at:
            self.started_at = datetime.utcnow()
    
    def complete_execution(self, result: Optional[Dict[str, Any]] = None, output: Optional[str] = None) -> None:
        """Mark execution as completed"""
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
        if result:
            self.result = result
        if output:
            self.output = output
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def fail_execution(self, error_details: Dict[str, Any], output: Optional[str] = None) -> None:
        """Mark execution as failed"""
        self.status = ExecutionStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_details = error_details
        
        if output:
            self.output = output
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def cancel_execution(self, reason: Optional[str] = None) -> None:
        """Cancel execution"""
        self.status = ExecutionStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        if reason:
            self.add_log("INFO", f"Execution cancelled: {reason}")
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def timeout_execution(self) -> None:
        """Mark execution as timed out"""
        self.status = ExecutionStatus.TIMEOUT
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def update_resource_usage(self, usage: ResourceUsage) -> None:
        """Update current resource usage"""
        self.resource_usage = usage
        
        # Update peak usage
        if usage.cpu_percent and (not self.peak_resource_usage.cpu_percent or usage.cpu_percent > self.peak_resource_usage.cpu_percent):
            self.peak_resource_usage.cpu_percent = usage.cpu_percent
        
        if usage.memory_mb and (not self.peak_resource_usage.memory_mb or usage.memory_mb > self.peak_resource_usage.memory_mb):
            self.peak_resource_usage.memory_mb = usage.memory_mb
        
        if usage.disk_io_mb and (not self.peak_resource_usage.disk_io_mb or usage.disk_io_mb > self.peak_resource_usage.disk_io_mb):
            self.peak_resource_usage.disk_io_mb = usage.disk_io_mb
        
        if usage.network_io_mb and (not self.peak_resource_usage.network_io_mb or usage.network_io_mb > self.peak_resource_usage.network_io_mb):
            self.peak_resource_usage.network_io_mb = usage.network_io_mb
        
        if usage.gpu_percent and (not self.peak_resource_usage.gpu_percent or usage.gpu_percent > self.peak_resource_usage.gpu_percent):
            self.peak_resource_usage.gpu_percent = usage.gpu_percent
    
    def add_log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Add execution log entry"""
        log_entry = ExecutionLog(
            level=level,
            message=message,
            context=context or {}
        )
        self.logs.append(log_entry)
    
    def add_recovery_action(self, action: str) -> None:
        """Add recovery action"""
        self.recovery_actions.append(action)
        self.add_log("INFO", f"Recovery action: {action}")
    
    def get_total_duration(self) -> Optional[float]:
        """Get total duration from queue to completion"""
        if not self.completed_at:
            return None
        return (self.completed_at - self.queued_at).total_seconds()
    
    def is_completed(self) -> bool:
        """Check if execution is in a completed state"""
        return self.status in [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT
        ]
    
    def is_successful(self) -> bool:
        """Check if execution was successful"""
        return self.status == ExecutionStatus.COMPLETED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary"""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskExecution":
        """Create execution from dictionary"""
        return cls.model_validate(data)

