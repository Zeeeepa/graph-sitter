"""
Strands Event Loop Types

Defines types and configurations for the Strands event loop system.
Based on: https://github.com/strands-agents/sdk-python/blob/main/src/strands/types/event_loop.py
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import asyncio


class EventLoopStatus(Enum):
    """Status of the event loop."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class MessagePriority(Enum):
    """Priority levels for messages."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EventLoopConfig:
    """Configuration for the Strands event loop."""
    max_workers: int = 4
    max_queue_size: int = 1000
    message_timeout: float = 30.0
    heartbeat_interval: float = 10.0
    error_retry_attempts: int = 3
    error_retry_delay: float = 1.0
    enable_telemetry: bool = True
    enable_health_checks: bool = True
    graceful_shutdown_timeout: float = 30.0


@dataclass
class Message:
    """Represents a message in the event loop."""
    id: str
    type: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    correlation_id: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None


@dataclass
class MessageHandler:
    """Represents a message handler."""
    handler_id: str
    message_types: List[str]
    handler_func: Callable[[Message], Any]
    priority: int = 0
    enabled: bool = True
    max_concurrent: int = 1


@dataclass
class EventLoopMetrics:
    """Metrics for the event loop."""
    messages_processed: int = 0
    messages_failed: int = 0
    messages_queued: int = 0
    handlers_registered: int = 0
    average_processing_time: float = 0.0
    uptime: float = 0.0
    last_heartbeat: Optional[float] = None


@dataclass
class HealthCheck:
    """Health check configuration."""
    name: str
    check_func: Callable[[], bool]
    interval: float = 60.0
    timeout: float = 5.0
    enabled: bool = True
    last_check: Optional[float] = None
    last_result: Optional[bool] = None


@dataclass
class EventLoopState:
    """Current state of the event loop."""
    status: EventLoopStatus = EventLoopStatus.STOPPED
    config: EventLoopConfig = field(default_factory=EventLoopConfig)
    metrics: EventLoopMetrics = field(default_factory=EventLoopMetrics)
    handlers: Dict[str, MessageHandler] = field(default_factory=dict)
    health_checks: Dict[str, HealthCheck] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    
    def add_error(self, error: str):
        """Add an error to the error log."""
        self.error_log.append(error)
        # Keep only last 100 errors
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the current status."""
        return {
            "status": self.status.value,
            "uptime": self.metrics.uptime,
            "messages_processed": self.metrics.messages_processed,
            "messages_failed": self.metrics.messages_failed,
            "messages_queued": self.metrics.messages_queued,
            "handlers_count": len(self.handlers),
            "health_checks_count": len(self.health_checks),
            "recent_errors": len(self.error_log),
            "average_processing_time": self.metrics.average_processing_time
        }

