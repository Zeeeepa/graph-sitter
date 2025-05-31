"""
Event Processing Engine for Multi-Platform Integration
Core-7: Event System & Multi-Platform Integration
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
from queue import Queue, Empty
import time

from pydantic import BaseModel
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class EventStatus(Enum):
    """Event processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ProcessedEvent:
    """Represents a processed event with metadata."""
    id: str
    platform: str
    event_type: str
    source_id: Optional[str]
    source_name: Optional[str]
    actor_id: Optional[str]
    actor_name: Optional[str]
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    processing_duration: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class EventProcessor:
    """Represents an event processor configuration."""
    name: str
    handler: Callable
    event_filters: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    is_async: bool = False


class EventCorrelator:
    """Handles event correlation across platforms."""
    
    def __init__(self):
        self.correlation_rules: List[Callable] = []
        self.active_correlations: Dict[str, List[ProcessedEvent]] = {}
        
    def add_correlation_rule(self, rule: Callable[[ProcessedEvent], Optional[str]]):
        """Add a correlation rule function."""
        self.correlation_rules.append(rule)
        
    def correlate_event(self, event: ProcessedEvent) -> Optional[str]:
        """Attempt to correlate an event with existing events."""
        for rule in self.correlation_rules:
            try:
                correlation_id = rule(event)
                if correlation_id:
                    if correlation_id not in self.active_correlations:
                        self.active_correlations[correlation_id] = []
                    self.active_correlations[correlation_id].append(event)
                    event.correlation_id = correlation_id
                    return correlation_id
            except Exception as e:
                logger.warning(f"Correlation rule failed: {e}")
        return None
        
    def get_correlated_events(self, correlation_id: str) -> List[ProcessedEvent]:
        """Get all events with the given correlation ID."""
        return self.active_correlations.get(correlation_id, [])


class EventQueue:
    """Thread-safe event queue with priority support."""
    
    def __init__(self, maxsize: int = 0):
        self.queues = {
            EventPriority.CRITICAL: Queue(maxsize),
            EventPriority.HIGH: Queue(maxsize),
            EventPriority.NORMAL: Queue(maxsize),
            EventPriority.LOW: Queue(maxsize),
        }
        self.lock = threading.Lock()
        
    def put(self, event: ProcessedEvent, timeout: Optional[float] = None):
        """Add an event to the appropriate priority queue."""
        self.queues[event.priority].put(event, timeout=timeout)
        
    def get(self, timeout: Optional[float] = None) -> Optional[ProcessedEvent]:
        """Get the next event from the highest priority queue."""
        # Check queues in priority order
        for priority in [EventPriority.CRITICAL, EventPriority.HIGH, 
                        EventPriority.NORMAL, EventPriority.LOW]:
            try:
                return self.queues[priority].get_nowait()
            except Empty:
                continue
        
        # If no events available immediately, wait on normal priority queue
        try:
            return self.queues[EventPriority.NORMAL].get(timeout=timeout)
        except Empty:
            return None
            
    def qsize(self) -> Dict[EventPriority, int]:
        """Get the size of each priority queue."""
        return {priority: queue.qsize() for priority, queue in self.queues.items()}
        
    def empty(self) -> bool:
        """Check if all queues are empty."""
        return all(queue.empty() for queue in self.queues.values())


class EventMetrics:
    """Tracks event processing metrics."""
    
    def __init__(self):
        self.metrics = {
            'events_processed': 0,
            'events_failed': 0,
            'processing_times': [],
            'platform_counts': {},
            'event_type_counts': {},
            'error_counts': {},
        }
        self.lock = threading.Lock()
        
    def record_event_processed(self, event: ProcessedEvent, duration: float):
        """Record a successfully processed event."""
        with self.lock:
            self.metrics['events_processed'] += 1
            self.metrics['processing_times'].append(duration)
            
            # Track platform counts
            platform = event.platform
            self.metrics['platform_counts'][platform] = \
                self.metrics['platform_counts'].get(platform, 0) + 1
                
            # Track event type counts
            event_type = event.event_type
            self.metrics['event_type_counts'][event_type] = \
                self.metrics['event_type_counts'].get(event_type, 0) + 1
                
    def record_event_failed(self, event: ProcessedEvent, error: str):
        """Record a failed event."""
        with self.lock:
            self.metrics['events_failed'] += 1
            self.metrics['error_counts'][error] = \
                self.metrics['error_counts'].get(error, 0) + 1
                
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self.lock:
            metrics = self.metrics.copy()
            if metrics['processing_times']:
                metrics['avg_processing_time'] = sum(metrics['processing_times']) / len(metrics['processing_times'])
                metrics['max_processing_time'] = max(metrics['processing_times'])
                metrics['min_processing_time'] = min(metrics['processing_times'])
            return metrics
            
    def reset_metrics(self):
        """Reset all metrics."""
        with self.lock:
            self.metrics = {
                'events_processed': 0,
                'events_failed': 0,
                'processing_times': [],
                'platform_counts': {},
                'event_type_counts': {},
                'error_counts': {},
            }


class EventProcessingEngine:
    """Main event processing engine with queuing, correlation, and streaming."""
    
    def __init__(self, 
                 max_workers: int = 4,
                 queue_maxsize: int = 1000,
                 enable_correlation: bool = True,
                 enable_streaming: bool = True):
        self.max_workers = max_workers
        self.queue = EventQueue(queue_maxsize)
        self.processors: Dict[str, EventProcessor] = {}
        self.correlator = EventCorrelator() if enable_correlation else None
        self.metrics = EventMetrics()
        self.enable_streaming = enable_streaming
        
        # Worker management
        self.workers: List[threading.Thread] = []
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Streaming subscribers
        self.stream_subscribers: Dict[str, List[Callable]] = {}
        
        # Database storage (will be injected)
        self.storage = None
        
    def set_storage(self, storage):
        """Set the database storage backend."""
        self.storage = storage
        
    def register_processor(self, processor: EventProcessor):
        """Register an event processor."""
        self.processors[processor.name] = processor
        logger.info(f"Registered event processor: {processor.name}")
        
    def unregister_processor(self, processor_name: str):
        """Unregister an event processor."""
        if processor_name in self.processors:
            del self.processors[processor_name]
            logger.info(f"Unregistered event processor: {processor_name}")
            
    def add_correlation_rule(self, rule: Callable[[ProcessedEvent], Optional[str]]):
        """Add an event correlation rule."""
        if self.correlator:
            self.correlator.add_correlation_rule(rule)
            
    def subscribe_to_stream(self, stream_name: str, callback: Callable[[ProcessedEvent], None]):
        """Subscribe to an event stream."""
        if stream_name not in self.stream_subscribers:
            self.stream_subscribers[stream_name] = []
        self.stream_subscribers[stream_name].append(callback)
        logger.info(f"Added subscriber to stream: {stream_name}")
        
    def unsubscribe_from_stream(self, stream_name: str, callback: Callable):
        """Unsubscribe from an event stream."""
        if stream_name in self.stream_subscribers:
            try:
                self.stream_subscribers[stream_name].remove(callback)
                logger.info(f"Removed subscriber from stream: {stream_name}")
            except ValueError:
                logger.warning(f"Callback not found in stream: {stream_name}")
                
    def submit_event(self, 
                    platform: str,
                    event_type: str,
                    payload: Dict[str, Any],
                    source_id: Optional[str] = None,
                    source_name: Optional[str] = None,
                    actor_id: Optional[str] = None,
                    actor_name: Optional[str] = None,
                    priority: EventPriority = EventPriority.NORMAL,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Submit an event for processing."""
        event = ProcessedEvent(
            id=str(uuid.uuid4()),
            platform=platform,
            event_type=event_type,
            source_id=source_id,
            source_name=source_name,
            actor_id=actor_id,
            actor_name=actor_name,
            payload=payload,
            metadata=metadata or {},
            priority=priority
        )
        
        # Attempt correlation
        if self.correlator:
            self.correlator.correlate_event(event)
            
        # Store in database if available
        if self.storage:
            try:
                self.storage.store_event(event)
            except Exception as e:
                logger.error(f"Failed to store event in database: {e}")
                
        # Add to processing queue
        self.queue.put(event)
        logger.debug(f"Submitted event {event.id} for processing")
        
        return event.id
        
    def start(self):
        """Start the event processing workers."""
        if self.running:
            logger.warning("Event processing engine is already running")
            return
            
        self.running = True
        self.shutdown_event.clear()
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, name=f"EventWorker-{i}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
        logger.info(f"Started event processing engine with {self.max_workers} workers")
        
    def stop(self, timeout: float = 30.0):
        """Stop the event processing workers."""
        if not self.running:
            return
            
        logger.info("Stopping event processing engine...")
        self.running = False
        self.shutdown_event.set()
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=timeout)
            
        self.workers.clear()
        logger.info("Event processing engine stopped")
        
    def _worker_loop(self):
        """Main worker loop for processing events."""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Get next event from queue
                event = self.queue.get(timeout=1.0)
                if event is None:
                    continue
                    
                # Process the event
                self._process_event(event)
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                
    def _process_event(self, event: ProcessedEvent):
        """Process a single event through all matching processors."""
        start_time = time.time()
        
        try:
            # Find matching processors
            matching_processors = self._find_matching_processors(event)
            
            if not matching_processors:
                logger.debug(f"No processors found for event {event.id}")
                return
                
            # Process with each matching processor
            for processor in matching_processors:
                try:
                    self._execute_processor(processor, event)
                except Exception as e:
                    logger.error(f"Processor {processor.name} failed for event {event.id}: {e}")
                    event.error_message = str(e)
                    self.metrics.record_event_failed(event, str(e))
                    
                    # Handle retries
                    if event.retry_count < processor.max_retries:
                        event.retry_count += 1
                        logger.info(f"Retrying event {event.id} with processor {processor.name} "
                                  f"(attempt {event.retry_count}/{processor.max_retries})")
                        # Re-queue for retry (could add delay here)
                        self.queue.put(event)
                    continue
                    
            # Mark as processed
            event.processed_at = datetime.now(timezone.utc)
            event.processing_duration = time.time() - start_time
            
            # Update storage
            if self.storage:
                try:
                    self.storage.mark_event_processed(event.id)
                except Exception as e:
                    logger.error(f"Failed to update event status in database: {e}")
                    
            # Record metrics
            self.metrics.record_event_processed(event, event.processing_duration)
            
            # Stream to subscribers
            if self.enable_streaming:
                self._stream_event(event)
                
            logger.debug(f"Successfully processed event {event.id}")
            
        except Exception as e:
            logger.error(f"Failed to process event {event.id}: {e}")
            event.error_message = str(e)
            self.metrics.record_event_failed(event, str(e))
            
    def _find_matching_processors(self, event: ProcessedEvent) -> List[EventProcessor]:
        """Find processors that match the event criteria."""
        matching = []
        
        for processor in self.processors.values():
            if self._event_matches_filters(event, processor.event_filters):
                matching.append(processor)
                
        return matching
        
    def _event_matches_filters(self, event: ProcessedEvent, filters: Dict[str, Any]) -> bool:
        """Check if an event matches the given filters."""
        if not filters:
            return True
            
        for key, value in filters.items():
            if key == 'platform' and event.platform != value:
                return False
            elif key == 'event_type':
                if isinstance(value, str):
                    if value.endswith('*'):
                        if not event.event_type.startswith(value[:-1]):
                            return False
                    elif value.startswith('*'):
                        if not event.event_type.endswith(value[1:]):
                            return False
                    elif event.event_type != value:
                        return False
                elif isinstance(value, list) and event.event_type not in value:
                    return False
            elif key == 'source_id' and event.source_id != value:
                return False
            elif key == 'source_name' and event.source_name != value:
                return False
                
        return True
        
    def _execute_processor(self, processor: EventProcessor, event: ProcessedEvent):
        """Execute a processor on an event."""
        if processor.is_async:
            # Handle async processors
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(processor.handler(event))
            finally:
                loop.close()
        else:
            # Handle sync processors
            processor.handler(event)
            
    def _stream_event(self, event: ProcessedEvent):
        """Stream an event to all matching subscribers."""
        # Stream to 'all_events' subscribers
        for callback in self.stream_subscribers.get('all_events', []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Stream callback failed: {e}")
                
        # Stream to platform-specific subscribers
        platform_stream = f"{event.platform}_events"
        for callback in self.stream_subscribers.get(platform_stream, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Stream callback failed: {e}")
                
        # Stream to event-type-specific subscribers
        event_type_stream = f"{event.event_type}_events"
        for callback in self.stream_subscribers.get(event_type_stream, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Stream callback failed: {e}")
                
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            'queue_sizes': self.queue.qsize(),
            'total_queued': sum(self.queue.qsize().values()),
            'workers_active': len([w for w in self.workers if w.is_alive()]),
            'running': self.running
        }
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics."""
        return self.metrics.get_metrics()
        
    def reset_metrics(self):
        """Reset processing metrics."""
        self.metrics.reset_metrics()


# Default correlation rules
def github_pr_to_linear_issue_correlation(event: ProcessedEvent) -> Optional[str]:
    """Correlate GitHub PR events with Linear issues based on branch names or descriptions."""
    if event.platform != 'github' or 'pull_request' not in event.event_type:
        return None
        
    # Look for Linear issue references in PR title or description
    payload = event.payload
    pr_title = payload.get('pull_request', {}).get('title', '')
    pr_body = payload.get('pull_request', {}).get('body', '')
    
    # Simple pattern matching for Linear issue IDs (e.g., ZAM-1025)
    import re
    pattern = r'([A-Z]+-\d+)'
    
    for text in [pr_title, pr_body]:
        match = re.search(pattern, text)
        if match:
            return f"linear_issue_{match.group(1)}"
            
    return None


def slack_mention_to_github_pr_correlation(event: ProcessedEvent) -> Optional[str]:
    """Correlate Slack mentions with GitHub PRs based on PR URLs in messages."""
    if event.platform != 'slack' or event.event_type != 'app_mention':
        return None
        
    message_text = event.payload.get('text', '')
    
    # Look for GitHub PR URLs
    import re
    pattern = r'github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    match = re.search(pattern, message_text)
    
    if match:
        org, repo, pr_number = match.groups()
        return f"github_pr_{org}_{repo}_{pr_number}"
        
    return None


# Factory function to create a configured engine
def create_event_engine(config: Optional[Dict[str, Any]] = None) -> EventProcessingEngine:
    """Create and configure an event processing engine."""
    config = config or {}
    
    engine = EventProcessingEngine(
        max_workers=config.get('max_workers', 4),
        queue_maxsize=config.get('queue_maxsize', 1000),
        enable_correlation=config.get('enable_correlation', True),
        enable_streaming=config.get('enable_streaming', True)
    )
    
    # Add default correlation rules
    if config.get('enable_correlation', True):
        engine.add_correlation_rule(github_pr_to_linear_issue_correlation)
        engine.add_correlation_rule(slack_mention_to_github_pr_correlation)
        
    return engine

