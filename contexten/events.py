"""
Event Evaluator - System-level event evaluation with real-time monitoring and intelligent classification
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid


class EventType(Enum):
    """Event type classifications"""
    SYSTEM = "system"
    TASK = "task"
    ERROR = "error"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USER = "user"
    INTEGRATION = "integration"
    CICD = "cicd"
    MEMORY = "memory"
    CUSTOM = "custom"


class EventPriority(Enum):
    """Event priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Event:
    """Represents a system event"""
    id: str
    type: EventType
    priority: EventPriority
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    response_generated: bool = False
    impact_score: float = 0.0
    classification_confidence: float = 0.0


@dataclass
class EventPattern:
    """Represents an event pattern for classification"""
    name: str
    type: EventType
    priority: EventPriority
    conditions: Dict[str, Any]
    response_template: Optional[str] = None
    auto_response: bool = False


class EventEvaluator:
    """
    System-Level Event Evaluation Engine
    
    Features:
    - Real-time event monitoring
    - Intelligent event classification
    - Automated response generation
    - Impact assessment and prioritization
    - Pattern recognition and learning
    """
    
    def __init__(
        self,
        monitoring_enabled: bool = True,
        classification_threshold: float = 0.8,
        real_time_processing: bool = True,
        max_event_history: int = 10000
    ):
        """Initialize the Event Evaluator"""
        self.monitoring_enabled = monitoring_enabled
        self.classification_threshold = classification_threshold
        self.real_time_processing = real_time_processing
        self.max_event_history = max_event_history
        
        self.logger = logging.getLogger(__name__)
        
        # Event storage
        self._events: Dict[str, Event] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Event patterns for classification
        self._patterns: List[EventPattern] = []
        self._load_default_patterns()
        
        # Event handlers
        self._handlers: Dict[EventType, List[Callable]] = {}
        
        # Statistics
        self._stats = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_priority": {},
            "auto_responses_generated": 0,
            "patterns_matched": 0,
            "processing_errors": 0,
            "last_event_time": None
        }
        
        # Processing task
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
    
    def _load_default_patterns(self):
        """Load default event patterns"""
        default_patterns = [
            EventPattern(
                name="task_failure",
                type=EventType.ERROR,
                priority=EventPriority.HIGH,
                conditions={
                    "type": "task_execution",
                    "status": "failed"
                },
                response_template="Task {task_id} failed: {error_message}",
                auto_response=True
            ),
            EventPattern(
                name="memory_optimization",
                type=EventType.MEMORY,
                priority=EventPriority.MEDIUM,
                conditions={
                    "type": "memory_optimization",
                    "entries_removed": {"$gt": 100}
                },
                response_template="Memory optimization completed: {entries_removed} entries removed",
                auto_response=False
            ),
            EventPattern(
                name="cicd_pipeline_failure",
                type=EventType.CICD,
                priority=EventPriority.CRITICAL,
                conditions={
                    "type": "pipeline_execution",
                    "status": "failed",
                    "stage": {"$in": ["build", "test", "deploy"]}
                },
                response_template="CI/CD pipeline failed at {stage}: {error_details}",
                auto_response=True
            ),
            EventPattern(
                name="performance_degradation",
                type=EventType.PERFORMANCE,
                priority=EventPriority.HIGH,
                conditions={
                    "type": "performance_metric",
                    "response_time": {"$gt": 5000}  # > 5 seconds
                },
                response_template="Performance degradation detected: {response_time}ms response time",
                auto_response=True
            ),
            EventPattern(
                name="security_alert",
                type=EventType.SECURITY,
                priority=EventPriority.CRITICAL,
                conditions={
                    "type": "security_event",
                    "severity": {"$in": ["high", "critical"]}
                },
                response_template="Security alert: {alert_type} - {description}",
                auto_response=True
            ),
            EventPattern(
                name="integration_error",
                type=EventType.INTEGRATION,
                priority=EventPriority.HIGH,
                conditions={
                    "type": "integration_event",
                    "status": "error"
                },
                response_template="Integration error with {service}: {error_message}",
                auto_response=True
            )
        ]
        
        self._patterns.extend(default_patterns)
    
    async def start(self):
        """Start the event evaluator"""
        self.logger.info("Starting Event Evaluator...")
        
        if not self.monitoring_enabled:
            self.logger.info("Event monitoring is disabled")
            return
        
        self._running = True
        
        if self.real_time_processing:
            self._processing_task = asyncio.create_task(self._event_processing_loop())
        
        self.logger.info("Event Evaluator started successfully")
    
    async def stop(self):
        """Stop the event evaluator"""
        self.logger.info("Stopping Event Evaluator...")
        
        self._running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Event Evaluator stopped successfully")
    
    async def evaluate_event(self, event_data: Dict[str, Any]) -> str:
        """
        Evaluate and process an event
        
        Args:
            event_data: Event data to evaluate
            
        Returns:
            Event ID
        """
        try:
            # Create event
            event = await self._create_event(event_data)
            
            # Store event
            self._events[event.id] = event
            
            # Manage event history size
            if len(self._events) > self.max_event_history:
                await self._cleanup_old_events()
            
            # Queue for processing
            if self.real_time_processing:
                await self._event_queue.put(event)
            else:
                await self._process_event(event)
            
            # Update statistics
            self._update_stats(event)
            
            self.logger.debug(f"Event {event.id} evaluated and queued for processing")
            return event.id
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate event: {e}")
            self._stats["processing_errors"] += 1
            raise
    
    async def _create_event(self, event_data: Dict[str, Any]) -> Event:
        """Create an event from data"""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Extract basic information
        source = event_data.get("source", "unknown")
        data = event_data.copy()
        
        # Classify event
        event_type, priority, confidence = await self._classify_event(event_data)
        
        # Calculate impact score
        impact_score = await self._calculate_impact_score(event_data, event_type, priority)
        
        return Event(
            id=event_id,
            type=event_type,
            priority=priority,
            timestamp=timestamp,
            source=source,
            data=data,
            impact_score=impact_score,
            classification_confidence=confidence
        )
    
    async def _classify_event(self, event_data: Dict[str, Any]) -> tuple[EventType, EventPriority, float]:
        """Classify an event using patterns"""
        best_match = None
        best_confidence = 0.0
        
        for pattern in self._patterns:
            confidence = await self._match_pattern(event_data, pattern)
            if confidence > best_confidence and confidence >= self.classification_threshold:
                best_match = pattern
                best_confidence = confidence
        
        if best_match:
            self._stats["patterns_matched"] += 1
            return best_match.type, best_match.priority, best_confidence
        
        # Default classification
        return self._default_classification(event_data)
    
    async def _match_pattern(self, event_data: Dict[str, Any], pattern: EventPattern) -> float:
        """Match event data against a pattern"""
        try:
            conditions = pattern.conditions
            matches = 0
            total_conditions = len(conditions)
            
            for key, expected in conditions.items():
                if key not in event_data:
                    continue
                
                actual = event_data[key]
                
                if isinstance(expected, dict):
                    # Handle operators like $gt, $in, etc.
                    if "$gt" in expected:
                        if isinstance(actual, (int, float)) and actual > expected["$gt"]:
                            matches += 1
                    elif "$lt" in expected:
                        if isinstance(actual, (int, float)) and actual < expected["$lt"]:
                            matches += 1
                    elif "$in" in expected:
                        if actual in expected["$in"]:
                            matches += 1
                    elif "$eq" in expected:
                        if actual == expected["$eq"]:
                            matches += 1
                else:
                    # Direct comparison
                    if actual == expected:
                        matches += 1
            
            return matches / total_conditions if total_conditions > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Pattern matching error: {e}")
            return 0.0
    
    def _default_classification(self, event_data: Dict[str, Any]) -> tuple[EventType, EventPriority, float]:
        """Provide default classification for unmatched events"""
        event_type_str = event_data.get("type", "").lower()
        
        # Simple keyword-based classification
        if "error" in event_type_str or "fail" in event_type_str:
            return EventType.ERROR, EventPriority.HIGH, 0.6
        elif "performance" in event_type_str or "slow" in event_type_str:
            return EventType.PERFORMANCE, EventPriority.MEDIUM, 0.6
        elif "security" in event_type_str or "auth" in event_type_str:
            return EventType.SECURITY, EventPriority.HIGH, 0.6
        elif "task" in event_type_str:
            return EventType.TASK, EventPriority.MEDIUM, 0.6
        elif "memory" in event_type_str:
            return EventType.MEMORY, EventPriority.LOW, 0.6
        elif "cicd" in event_type_str or "pipeline" in event_type_str:
            return EventType.CICD, EventPriority.MEDIUM, 0.6
        else:
            return EventType.SYSTEM, EventPriority.LOW, 0.5
    
    async def _calculate_impact_score(
        self,
        event_data: Dict[str, Any],
        event_type: EventType,
        priority: EventPriority
    ) -> float:
        """Calculate impact score for an event"""
        base_score = {
            EventPriority.CRITICAL: 1.0,
            EventPriority.HIGH: 0.8,
            EventPriority.MEDIUM: 0.6,
            EventPriority.LOW: 0.4,
            EventPriority.INFO: 0.2
        }.get(priority, 0.5)
        
        # Adjust based on event type
        type_multiplier = {
            EventType.SECURITY: 1.2,
            EventType.ERROR: 1.1,
            EventType.CICD: 1.0,
            EventType.PERFORMANCE: 0.9,
            EventType.TASK: 0.8,
            EventType.SYSTEM: 0.7,
            EventType.MEMORY: 0.6,
            EventType.USER: 0.5,
            EventType.INTEGRATION: 0.8,
            EventType.CUSTOM: 0.7
        }.get(event_type, 0.7)
        
        # Consider additional factors
        frequency_factor = 1.0
        if "frequency" in event_data:
            frequency_factor = min(event_data["frequency"] / 10.0, 2.0)
        
        return min(base_score * type_multiplier * frequency_factor, 1.0)
    
    async def _event_processing_loop(self):
        """Main event processing loop"""
        while self._running:
            try:
                # Wait for events with timeout
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Event processing error: {e}")
                self._stats["processing_errors"] += 1
    
    async def _process_event(self, event: Event):
        """Process a single event"""
        try:
            self.logger.debug(f"Processing event {event.id} ({event.type.value}, {event.priority.value})")
            
            # Mark as processed
            event.processed = True
            
            # Generate automated response if applicable
            if await self._should_generate_response(event):
                response = await self._generate_response(event)
                if response:
                    event.response_generated = True
                    event.metadata["auto_response"] = response
                    self._stats["auto_responses_generated"] += 1
            
            # Trigger event handlers
            await self._trigger_handlers(event)
            
            # Log significant events
            if event.priority in [EventPriority.CRITICAL, EventPriority.HIGH]:
                self.logger.warning(
                    f"High-priority event: {event.type.value} - "
                    f"Impact: {event.impact_score:.2f} - "
                    f"Data: {json.dumps(event.data, default=str)[:200]}"
                )
            
        except Exception as e:
            self.logger.error(f"Failed to process event {event.id}: {e}")
            self._stats["processing_errors"] += 1
    
    async def _should_generate_response(self, event: Event) -> bool:
        """Determine if an automated response should be generated"""
        # Check if any matching pattern has auto_response enabled
        for pattern in self._patterns:
            confidence = await self._match_pattern(event.data, pattern)
            if confidence >= self.classification_threshold and pattern.auto_response:
                return True
        
        # Generate response for critical events
        if event.priority == EventPriority.CRITICAL:
            return True
        
        return False
    
    async def _generate_response(self, event: Event) -> Optional[str]:
        """Generate automated response for an event"""
        try:
            # Find matching pattern with response template
            for pattern in self._patterns:
                confidence = await self._match_pattern(event.data, pattern)
                if confidence >= self.classification_threshold and pattern.response_template:
                    # Format response template with event data
                    response = pattern.response_template.format(**event.data)
                    return response
            
            # Generate generic response
            return f"Event {event.type.value} detected with {event.priority.value} priority"
            
        except Exception as e:
            self.logger.error(f"Failed to generate response for event {event.id}: {e}")
            return None
    
    async def _trigger_handlers(self, event: Event):
        """Trigger registered event handlers"""
        handlers = self._handlers.get(event.type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        self.logger.info(f"Registered handler for {event_type.value} events")
    
    def add_pattern(self, pattern: EventPattern):
        """Add a custom event pattern"""
        self._patterns.append(pattern)
        self.logger.info(f"Added event pattern: {pattern.name}")
    
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        priority: Optional[EventPriority] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get events matching criteria"""
        events = []
        
        for event in self._events.values():
            # Apply filters
            if event_type and event.type != event_type:
                continue
            if priority and event.priority != priority:
                continue
            if since and event.timestamp < since:
                continue
            
            events.append({
                "id": event.id,
                "type": event.type.value,
                "priority": event.priority.value,
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "data": event.data,
                "metadata": event.metadata,
                "processed": event.processed,
                "response_generated": event.response_generated,
                "impact_score": event.impact_score,
                "classification_confidence": event.classification_confidence
            })
        
        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events[:limit]
    
    async def _cleanup_old_events(self):
        """Remove old events to maintain history size"""
        if len(self._events) <= self.max_event_history:
            return
        
        # Sort events by timestamp
        sorted_events = sorted(
            self._events.items(),
            key=lambda x: x[1].timestamp
        )
        
        # Remove oldest events
        events_to_remove = len(self._events) - self.max_event_history + 100  # Remove extra for buffer
        
        for i in range(events_to_remove):
            event_id, _ = sorted_events[i]
            del self._events[event_id]
    
    def _update_stats(self, event: Event):
        """Update statistics"""
        self._stats["total_events"] += 1
        self._stats["last_event_time"] = event.timestamp.isoformat()
        
        # Update type statistics
        type_key = event.type.value
        if type_key not in self._stats["events_by_type"]:
            self._stats["events_by_type"][type_key] = 0
        self._stats["events_by_type"][type_key] += 1
        
        # Update priority statistics
        priority_key = event.priority.value
        if priority_key not in self._stats["events_by_priority"]:
            self._stats["events_by_priority"][priority_key] = 0
        self._stats["events_by_priority"][priority_key] += 1
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get event evaluation statistics"""
        return {
            **self._stats,
            "active_events": len(self._events),
            "patterns_loaded": len(self._patterns),
            "handlers_registered": sum(len(handlers) for handlers in self._handlers.values()),
            "monitoring_enabled": self.monitoring_enabled,
            "real_time_processing": self.real_time_processing,
            "classification_threshold": self.classification_threshold
        }
    
    def is_healthy(self) -> bool:
        """Check if event evaluator is healthy"""
        return (
            self._running and
            self._stats["processing_errors"] < 100 and  # Less than 100 errors
            len(self._events) <= self.max_event_history * 1.1  # Allow 10% overflow
        )

