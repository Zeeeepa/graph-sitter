"""
Strands Trace Types

Defines types for tracing and telemetry in the Strands system.
Based on: https://github.com/strands-agents/sdk-python/blob/main/src/strands/types/traces.py
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time


class TraceLevel(Enum):
    """Trace level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SpanStatus(Enum):
    """Span status enumeration."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class TraceEvent:
    """Represents a trace event."""
    event_id: str
    name: str
    event_type: str
    timestamp: float
    span_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    level: TraceLevel = TraceLevel.INFO
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "name": self.name,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "span_id": self.span_id,
            "attributes": self.attributes,
            "level": self.level.value
        }


@dataclass
class TraceSpan:
    """Represents a trace span."""
    span_id: str
    name: str
    operation_type: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    parent_span_id: Optional[str] = None
    status: str = "unset"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[TraceEvent] = field(default_factory=list)
    
    def add_event(self, event: TraceEvent):
        """Add an event to this span."""
        event.span_id = self.span_id
        self.events.append(event)
    
    def set_attribute(self, key: str, value: Any):
        """Set an attribute on this span."""
        self.attributes[key] = value
    
    def finish(self, status: str = "ok"):
        """Finish the span."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "span_id": self.span_id,
            "name": self.name,
            "operation_type": self.operation_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "parent_span_id": self.parent_span_id,
            "status": self.status,
            "attributes": self.attributes,
            "events": [event.to_dict() for event in self.events]
        }


@dataclass
class TraceContext:
    """Represents trace context."""
    trace_id: str
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "baggage": self.baggage
        }


@dataclass
class TraceSummary:
    """Summary of trace data."""
    trace_id: str
    total_spans: int
    total_events: int
    total_duration: float
    error_count: int
    start_time: float
    end_time: Optional[float] = None
    root_span_name: Optional[str] = None
    status: str = "unset"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "total_spans": self.total_spans,
            "total_events": self.total_events,
            "total_duration": self.total_duration,
            "error_count": self.error_count,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "root_span_name": self.root_span_name,
            "status": self.status
        }

