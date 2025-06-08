"""
Strands Telemetry Tracer

Provides comprehensive tracing and telemetry capabilities for Strands agents.
Based on: https://github.com/strands-agents/sdk-python/blob/main/src/strands/telemetry/tracer.py
"""

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from ..types.traces import TraceEvent, TraceSpan

logger = logging.getLogger(__name__)


@dataclass
class TracingConfig:
    """Configuration for tracing."""
    enabled: bool = True
    sample_rate: float = 1.0
    max_spans: int = 1000
    export_interval: float = 30.0
    include_stack_traces: bool = False


class StrandsTracer:
    """Comprehensive tracing system for Strands agents."""
    
    def __init__(self, config: Optional[TracingConfig] = None):
        """Initialize the tracer.
        
        Args:
            config: Optional tracing configuration
        """
        self.config = config or TracingConfig()
        self.spans: List[TraceSpan] = []
        self.events: List[TraceEvent] = []
        self.active_spans: Dict[str, TraceSpan] = {}
        self._span_stack: List[str] = []
        
        logger.info("Initialized Strands tracer")
    
    def start_span(self, 
                   name: str, 
                   operation_type: str = "operation",
                   parent_span_id: Optional[str] = None,
                   attributes: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace span.
        
        Args:
            name: Name of the span
            operation_type: Type of operation being traced
            parent_span_id: Optional parent span ID
            attributes: Optional span attributes
            
        Returns:
            Span ID
        """
        if not self.config.enabled:
            return ""
        
        span_id = str(uuid.uuid4())
        
        # Use parent from stack if not specified
        if parent_span_id is None and self._span_stack:
            parent_span_id = self._span_stack[-1]
        
        span = TraceSpan(
            span_id=span_id,
            name=name,
            operation_type=operation_type,
            start_time=time.time(),
            parent_span_id=parent_span_id,
            attributes=attributes or {}
        )
        
        self.spans.append(span)
        self.active_spans[span_id] = span
        self._span_stack.append(span_id)
        
        logger.debug(f"Started span: {name} ({span_id})")
        return span_id
    
    def end_span(self, span_id: str, status: str = "success", error: Optional[str] = None):
        """End a trace span.
        
        Args:
            span_id: ID of the span to end
            status: Final status of the span
            error: Optional error message
        """
        if not self.config.enabled or span_id not in self.active_spans:
            return
        
        span = self.active_spans[span_id]
        span.end_time = time.time()
        span.duration = span.end_time - span.start_time
        span.status = status
        
        if error:
            span.attributes["error"] = error
        
        # Remove from active spans and stack
        del self.active_spans[span_id]
        if span_id in self._span_stack:
            self._span_stack.remove(span_id)
        
        logger.debug(f"Ended span: {span.name} ({span_id}) - {status}")
    
    @contextmanager
    def trace(self, 
              name: str, 
              operation_type: str = "operation",
              attributes: Optional[Dict[str, Any]] = None):
        """Context manager for tracing operations.
        
        Args:
            name: Name of the operation
            operation_type: Type of operation
            attributes: Optional attributes
        """
        span_id = self.start_span(name, operation_type, attributes=attributes)
        try:
            yield span_id
            self.end_span(span_id, "success")
        except Exception as e:
            self.end_span(span_id, "error", str(e))
            raise
    
    def add_event(self, 
                  name: str, 
                  event_type: str = "info",
                  attributes: Optional[Dict[str, Any]] = None,
                  span_id: Optional[str] = None):
        """Add a trace event.
        
        Args:
            name: Name of the event
            event_type: Type of event
            attributes: Optional event attributes
            span_id: Optional span to associate with
        """
        if not self.config.enabled:
            return
        
        # Use current span if not specified
        if span_id is None and self._span_stack:
            span_id = self._span_stack[-1]
        
        event = TraceEvent(
            event_id=str(uuid.uuid4()),
            name=name,
            event_type=event_type,
            timestamp=time.time(),
            span_id=span_id,
            attributes=attributes or {}
        )
        
        self.events.append(event)
        logger.debug(f"Added event: {name} ({event_type})")
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get a summary of all traces.
        
        Returns:
            Trace summary
        """
        total_spans = len(self.spans)
        total_events = len(self.events)
        active_spans = len(self.active_spans)
        
        # Calculate statistics
        completed_spans = [s for s in self.spans if s.end_time is not None]
        avg_duration = sum(s.duration for s in completed_spans) / len(completed_spans) if completed_spans else 0
        
        error_spans = [s for s in completed_spans if s.status == "error"]
        error_rate = len(error_spans) / len(completed_spans) if completed_spans else 0
        
        return {
            "total_spans": total_spans,
            "total_events": total_events,
            "active_spans": active_spans,
            "completed_spans": len(completed_spans),
            "average_duration": avg_duration,
            "error_rate": error_rate,
            "config": {
                "enabled": self.config.enabled,
                "sample_rate": self.config.sample_rate,
                "max_spans": self.config.max_spans
            }
        }
    
    def export_traces(self) -> Dict[str, Any]:
        """Export all traces for external processing.
        
        Returns:
            Exported trace data
        """
        return {
            "spans": [span.__dict__ for span in self.spans],
            "events": [event.__dict__ for event in self.events],
            "summary": self.get_trace_summary()
        }
    
    def clear_traces(self):
        """Clear all trace data."""
        self.spans.clear()
        self.events.clear()
        self.active_spans.clear()
        self._span_stack.clear()
        logger.info("Cleared all trace data")
    
    def set_attribute(self, key: str, value: Any, span_id: Optional[str] = None):
        """Set an attribute on a span.
        
        Args:
            key: Attribute key
            value: Attribute value
            span_id: Optional span ID (uses current span if not specified)
        """
        if not self.config.enabled:
            return
        
        if span_id is None and self._span_stack:
            span_id = self._span_stack[-1]
        
        if span_id and span_id in self.active_spans:
            self.active_spans[span_id].attributes[key] = value

