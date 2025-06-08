"""
Strands SDK - Agent framework integration

Provides comprehensive agent framework capabilities including telemetry,
event loops, tools, and workflow management.
"""

from .telemetry.tracer import StrandsTracer
from .types.event_loop import EventLoopConfig, EventLoopStatus
from .types.traces import TraceEvent, TraceSpan
from .event_loop.event_loop import StrandsEventLoop
from .event_loop.message_processor import MessageProcessor
from .event_loop.error_handler import ErrorHandler
from .tools.mcp.mcp_client import MCPClient
from .tools.watcher import Watcher

__version__ = "1.0.0"
__all__ = [
    "StrandsTracer",
    "EventLoopConfig", 
    "EventLoopStatus",
    "TraceEvent",
    "TraceSpan", 
    "StrandsEventLoop",
    "MessageProcessor",
    "ErrorHandler",
    "MCPClient",
    "Watcher"
]

