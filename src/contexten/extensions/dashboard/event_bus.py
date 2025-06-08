"""
Central Event Bus

Unified event coordination system that routes events between all Contexten extensions
while preventing loops and managing dependencies.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from graph_sitter.shared.logging.get_logger import get_logger
from .models import WorkflowEvent

logger = get_logger(__name__)


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EventRule:
    """Event routing and transformation rule"""
    source_event: str
    target_event: Optional[str] = None
    target_extensions: List[str] = None
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    priority: EventPriority = EventPriority.NORMAL
    max_retries: int = 3
    timeout: float = 30.0


@dataclass
class EventContext:
    """Context for event processing"""
    event_id: str
    correlation_id: str
    source_extension: str
    timestamp: datetime
    priority: EventPriority
    retry_count: int = 0
    parent_event_id: Optional[str] = None
    trace_id: Optional[str] = None


class EventBus:
    """
    Central event bus for coordinating communication between all Contexten extensions.
    
    Features:
    - Event routing and transformation
    - Loop prevention and dependency management
    - Priority-based processing
    - Error handling and retry mechanisms
    - Event tracing and audit logging
    """
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        
        # Event handlers by event type
        self.handlers: Dict[str, List[Callable]] = {}
        
        # Event routing rules
        self.rules: List[EventRule] = []
        
        # Event processing queue with priority
        self.event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        
        # Active event processing
        self.processing_events: Set[str] = set()
        
        # Event history for loop detection
        self.event_history: Dict[str, List[str]] = {}
        
        # Extension registry
        self.extensions: Dict[str, Any] = {}
        
        # Processing control
        self.is_running = False
        self.processor_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = {
            "events_processed": 0,
            "events_failed": 0,
            "events_retried": 0,
            "loops_prevented": 0
        }
        
        # Initialize default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default event routing rules"""
        
        # GitHub webhook events
        self.add_rule(EventRule(
            source_event="github.push",
            target_extensions=["grainchain", "graph_sitter", "linear"],
            priority=EventPriority.HIGH
        ))
        
        self.add_rule(EventRule(
            source_event="github.pull_request.opened",
            target_extensions=["grainchain", "graph_sitter", "circleci"],
            priority=EventPriority.HIGH
        ))
        
        # Linear webhook events
        self.add_rule(EventRule(
            source_event="linear.issue.created",
            target_extensions=["github", "codegen"],
            priority=EventPriority.NORMAL
        ))
        
        self.add_rule(EventRule(
            source_event="linear.issue.completed",
            target_extensions=["github", "slack"],
            priority=EventPriority.NORMAL
        ))
        
        # Codegen task events
        self.add_rule(EventRule(
            source_event="codegen.task.completed",
            target_extensions=["linear", "github", "grainchain"],
            priority=EventPriority.HIGH
        ))
        
        # Quality gate events
        self.add_rule(EventRule(
            source_event="grainchain.quality_gate.failed",
            target_extensions=["github", "linear", "slack"],
            priority=EventPriority.CRITICAL
        ))
        
        self.add_rule(EventRule(
            source_event="graph_sitter.analysis.completed",
            target_extensions=["github", "linear"],
            priority=EventPriority.NORMAL
        ))
        
        # CircleCI events
        self.add_rule(EventRule(
            source_event="circleci.build.failed",
            target_extensions=["github", "linear", "slack"],
            priority=EventPriority.HIGH
        ))
        
        # Slack notification events
        self.add_rule(EventRule(
            source_event="slack.command",
            target_extensions=["github", "linear", "codegen"],
            priority=EventPriority.NORMAL
        ))
    
    def register_extension(self, name: str, extension: Any):
        """Register an extension with the event bus"""
        self.extensions[name] = extension
        logger.info(f"Registered extension: {name}")
    
    def add_rule(self, rule: EventRule):
        """Add an event routing rule"""
        self.rules.append(rule)
        logger.debug(f"Added event rule: {rule.source_event} -> {rule.target_extensions}")
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe from an event type"""
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
            logger.debug(f"Unsubscribed handler from event: {event_type}")
    
    async def emit(self, event_type: str, data: Dict[str, Any], 
                   source: str = "dashboard", priority: EventPriority = EventPriority.NORMAL,
                   correlation_id: Optional[str] = None, parent_event_id: Optional[str] = None):
        """Emit an event to the bus"""
        
        # Generate event context
        event_id = f"{event_type}-{int(datetime.utcnow().timestamp() * 1000)}"
        correlation_id = correlation_id or event_id
        
        context = EventContext(
            event_id=event_id,
            correlation_id=correlation_id,
            source_extension=source,
            timestamp=datetime.utcnow(),
            priority=priority,
            parent_event_id=parent_event_id
        )
        
        # Check for potential loops
        if self._would_create_loop(event_type, correlation_id):
            self.metrics["loops_prevented"] += 1
            logger.warning(f"Prevented potential event loop for {event_type} (correlation: {correlation_id})")
            return
        
        # Add to processing queue
        priority_value = priority.value
        await self.event_queue.put((priority_value, context, event_type, data))
        
        logger.debug(f"Emitted event: {event_type} (id: {event_id}, priority: {priority.name})")
    
    def _would_create_loop(self, event_type: str, correlation_id: str) -> bool:
        """Check if emitting this event would create a loop"""
        if correlation_id not in self.event_history:
            return False
        
        # Check if we've seen this event type in this correlation chain recently
        recent_events = self.event_history[correlation_id]
        if len(recent_events) > 10:  # Prevent very long chains
            return True
        
        # Check for immediate loops (same event type repeated)
        if len(recent_events) >= 2 and recent_events[-1] == event_type and recent_events[-2] == event_type:
            return True
        
        return False
    
    async def start(self):
        """Start the event bus processor"""
        if self.is_running:
            return
        
        self.is_running = True
        self.processor_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")
    
    async def stop(self):
        """Stop the event bus processor"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event bus stopped")
    
    async def _process_events(self):
        """Main event processing loop"""
        while self.is_running:
            try:
                # Get next event from queue (with timeout to allow graceful shutdown)
                try:
                    priority, context, event_type, data = await asyncio.wait_for(
                        self.event_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                await self._handle_event(context, event_type, data)
                
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _handle_event(self, context: EventContext, event_type: str, data: Dict[str, Any]):
        """Handle a single event"""
        try:
            # Track event in history
            if context.correlation_id not in self.event_history:
                self.event_history[context.correlation_id] = []
            self.event_history[context.correlation_id].append(event_type)
            
            # Limit history size
            if len(self.event_history[context.correlation_id]) > 50:
                self.event_history[context.correlation_id] = self.event_history[context.correlation_id][-25:]
            
            # Mark as processing
            self.processing_events.add(context.event_id)
            
            # Execute direct handlers
            await self._execute_handlers(event_type, data, context)
            
            # Apply routing rules
            await self._apply_routing_rules(event_type, data, context)
            
            # Create workflow event for dashboard
            workflow_event = WorkflowEvent(
                id=context.event_id,
                project_id=data.get("project_id", "unknown"),
                event_type=event_type,
                source=context.source_extension,
                message=data.get("message", f"Event: {event_type}"),
                data=data,
                timestamp=context.timestamp
            )
            
            # Broadcast to dashboard
            await self.dashboard.broadcast_event(workflow_event)
            
            self.metrics["events_processed"] += 1
            logger.debug(f"Processed event: {event_type} (id: {context.event_id})")
            
        except Exception as e:
            self.metrics["events_failed"] += 1
            logger.error(f"Error handling event {event_type} (id: {context.event_id}): {e}")
            
            # Retry logic
            if context.retry_count < 3:
                context.retry_count += 1
                self.metrics["events_retried"] += 1
                
                # Re-queue with delay
                await asyncio.sleep(2 ** context.retry_count)  # Exponential backoff
                await self.event_queue.put((context.priority.value, context, event_type, data))
                logger.info(f"Retrying event {event_type} (attempt {context.retry_count})")
        
        finally:
            # Remove from processing
            self.processing_events.discard(context.event_id)
    
    async def _execute_handlers(self, event_type: str, data: Dict[str, Any], context: EventContext):
        """Execute direct event handlers"""
        if event_type not in self.handlers:
            return
        
        for handler in self.handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data, context)
                else:
                    handler(data, context)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def _apply_routing_rules(self, event_type: str, data: Dict[str, Any], context: EventContext):
        """Apply routing rules to forward events to other extensions"""
        for rule in self.rules:
            if rule.source_event != event_type:
                continue
            
            # Check condition if specified
            if rule.condition and not rule.condition(data):
                continue
            
            # Transform data if specified
            transformed_data = data
            if rule.transform:
                try:
                    transformed_data = rule.transform(data)
                except Exception as e:
                    logger.error(f"Error transforming data for rule {rule.source_event}: {e}")
                    continue
            
            # Route to target extensions
            if rule.target_extensions:
                for extension_name in rule.target_extensions:
                    await self._route_to_extension(
                        extension_name, rule.target_event or event_type, 
                        transformed_data, context
                    )
    
    async def _route_to_extension(self, extension_name: str, event_type: str, 
                                 data: Dict[str, Any], context: EventContext):
        """Route event to a specific extension"""
        if extension_name not in self.extensions:
            logger.warning(f"Extension {extension_name} not registered for event routing")
            return
        
        extension = self.extensions[extension_name]
        
        try:
            # Try to call the extension's event handler
            if hasattr(extension, 'handle_event'):
                if asyncio.iscoroutinefunction(extension.handle_event):
                    await extension.handle_event(event_type, data)
                else:
                    extension.handle_event(event_type, data)
            elif hasattr(extension, 'process_event'):
                if asyncio.iscoroutinefunction(extension.process_event):
                    await extension.process_event(event_type, data)
                else:
                    extension.process_event(event_type, data)
            else:
                logger.warning(f"Extension {extension_name} has no event handler method")
                
        except Exception as e:
            logger.error(f"Error routing event {event_type} to extension {extension_name}: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics"""
        return {
            **self.metrics,
            "active_events": len(self.processing_events),
            "queue_size": self.event_queue.qsize(),
            "registered_extensions": len(self.extensions),
            "event_rules": len(self.rules),
            "event_handlers": sum(len(handlers) for handlers in self.handlers.values())
        }
    
    def clear_history(self, older_than_hours: int = 24):
        """Clear old event history"""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        # This is a simplified cleanup - in a real implementation,
        # you'd want to track timestamps for each correlation chain
        if len(self.event_history) > 1000:
            # Keep only the most recent 500 correlation chains
            sorted_keys = sorted(self.event_history.keys())
            for key in sorted_keys[:-500]:
                del self.event_history[key]

