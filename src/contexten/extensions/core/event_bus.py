"""Event Bus for inter-extension communication.

This module provides a centralized event bus that enables asynchronous
communication between extensions through a publish-subscribe pattern.
"""

import asyncio
import logging
import json
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, Union
from collections import defaultdict
import weakref

from pydantic import BaseModel, Field

from .extension_base import ExtensionEvent, ExtensionMessage, ExtensionResponse

logger = logging.getLogger(__name__)


class EventFilter(BaseModel):
    """Event filter for subscription."""
    event_types: Optional[List[str]] = None
    source_patterns: Optional[List[str]] = None
    target_patterns: Optional[List[str]] = None
    data_filters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class EventSubscription(BaseModel):
    """Event subscription information."""
    subscriber_id: str
    event_filter: EventFilter
    handler: Any = Field(exclude=True)  # Exclude from serialization
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    active: bool = True


class EventMetrics(BaseModel):
    """Event bus metrics."""
    total_events_published: int = 0
    total_events_delivered: int = 0
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    failed_deliveries: int = 0
    average_delivery_time_ms: float = 0.0
    events_by_type: Dict[str, int] = Field(default_factory=dict)
    events_by_source: Dict[str, int] = Field(default_factory=dict)


class EventBusConfig(BaseModel):
    """Event bus configuration."""
    max_queue_size: int = 10000
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    event_ttl_seconds: int = 3600  # 1 hour
    enable_persistence: bool = False
    persistence_path: Optional[str] = None
    enable_metrics: bool = True
    delivery_timeout_seconds: float = 30.0
    batch_size: int = 100
    enable_dead_letter_queue: bool = True


class EventBus:
    """Centralized event bus for extension communication."""

    def __init__(self, config: Optional[EventBusConfig] = None):
        """Initialize event bus.
        
        Args:
            config: Event bus configuration
        """
        self.config = config or EventBusConfig()
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        self._dead_letter_queue: asyncio.Queue = asyncio.Queue()
        self._metrics = EventMetrics()
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._cleanup_task: Optional[asyncio.Task] = None
        self._event_history: List[ExtensionEvent] = []
        self._max_history_size = 1000
        
        # Topic-based routing
        self._topic_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Weak references to avoid memory leaks
        self._extension_refs: Dict[str, Any] = {}

    async def start(self) -> None:
        """Start the event bus."""
        if self._running:
            return
            
        self._running = True
        
        # Start worker tasks
        num_workers = 3  # Configurable
        for i in range(num_workers):
            task = asyncio.create_task(self._event_worker(f"worker-{i}"))
            self._worker_tasks.append(task)
            
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())
        
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop the event bus."""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
            
        if self._cleanup_task:
            self._cleanup_task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self._worker_tasks, self._cleanup_task, return_exceptions=True)
        
        self._worker_tasks.clear()
        self._cleanup_task = None
        
        logger.info("Event bus stopped")

    def subscribe(
        self,
        subscriber_id: str,
        handler: Callable[[ExtensionEvent], Union[None, asyncio.Future]],
        event_filter: Optional[EventFilter] = None
    ) -> str:
        """Subscribe to events.
        
        Args:
            subscriber_id: Unique identifier for the subscriber
            handler: Event handler function (sync or async)
            event_filter: Optional filter for events
            
        Returns:
            Subscription ID
        """
        if event_filter is None:
            event_filter = EventFilter()
            
        subscription = EventSubscription(
            subscriber_id=subscriber_id,
            event_filter=event_filter,
            handler=handler
        )
        
        subscription_id = f"{subscriber_id}_{len(self._subscriptions)}"
        self._subscriptions[subscription_id] = subscription
        
        # Update topic subscriptions
        if event_filter.event_types:
            for event_type in event_filter.event_types:
                self._topic_subscriptions[event_type].add(subscription_id)
        else:
            # Subscribe to all events
            self._topic_subscriptions["*"].add(subscription_id)
            
        self._metrics.total_subscriptions += 1
        self._metrics.active_subscriptions += 1
        
        logger.info(f"Added subscription: {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID to remove
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        if subscription_id not in self._subscriptions:
            return False
            
        subscription = self._subscriptions[subscription_id]
        
        # Remove from topic subscriptions
        if subscription.event_filter.event_types:
            for event_type in subscription.event_filter.event_types:
                self._topic_subscriptions[event_type].discard(subscription_id)
        else:
            self._topic_subscriptions["*"].discard(subscription_id)
            
        # Remove subscription
        del self._subscriptions[subscription_id]
        self._metrics.active_subscriptions -= 1
        
        logger.info(f"Removed subscription: {subscription_id}")
        return True

    async def publish(self, event: ExtensionEvent) -> bool:
        """Publish an event.
        
        Args:
            event: Event to publish
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self._running:
            logger.warning("Event bus not running, cannot publish event")
            return False
            
        try:
            # Add to queue
            await self._event_queue.put(event)
            
            # Update metrics
            self._metrics.total_events_published += 1
            self._metrics.events_by_type[event.type] = self._metrics.events_by_type.get(event.type, 0) + 1
            self._metrics.events_by_source[event.source] = self._metrics.events_by_source.get(event.source, 0) + 1
            
            # Add to history
            self._add_to_history(event)
            
            return True
            
        except asyncio.QueueFull:
            logger.error("Event queue full, dropping event")
            return False
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    async def publish_message(
        self,
        source: str,
        target: str,
        message_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Optional[ExtensionResponse]:
        """Publish a message and wait for response.
        
        Args:
            source: Source extension name
            target: Target extension name
            message_type: Message type
            payload: Message payload
            correlation_id: Optional correlation ID
            
        Returns:
            Response from target extension, None if failed
        """
        message = ExtensionMessage(
            id=f"{source}_{target}_{datetime.now(UTC).timestamp()}",
            type=message_type,
            source=source,
            target=target,
            payload=payload,
            correlation_id=correlation_id
        )
        
        # Create event for message
        event = ExtensionEvent(
            type="message",
            source=source,
            target=target,
            data={
                "message": message.dict(),
                "expects_response": True
            }
        )
        
        # Publish and wait for response
        if await self.publish(event):
            # TODO: Implement response waiting mechanism
            # For now, return a placeholder response
            return ExtensionResponse(
                success=True,
                data={"message": "Message published successfully"}
            )
        
        return None

    def get_subscriptions(self, subscriber_id: Optional[str] = None) -> List[EventSubscription]:
        """Get subscriptions.
        
        Args:
            subscriber_id: Optional subscriber ID filter
            
        Returns:
            List of subscriptions
        """
        if subscriber_id:
            return [sub for sub in self._subscriptions.values() if sub.subscriber_id == subscriber_id]
        return list(self._subscriptions.values())

    def get_metrics(self) -> EventMetrics:
        """Get event bus metrics.
        
        Returns:
            Current metrics
        """
        return self._metrics.copy()

    def get_event_history(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[ExtensionEvent]:
        """Get event history.
        
        Args:
            event_type: Optional event type filter
            source: Optional source filter
            limit: Maximum number of events to return
            
        Returns:
            List of historical events
        """
        events = self._event_history
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.type == event_type]
        if source:
            events = [e for e in events if e.source == source]
            
        # Return most recent events
        return events[-limit:]

    async def _event_worker(self, worker_id: str) -> None:
        """Event processing worker.
        
        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Event worker {worker_id} started")
        
        while self._running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                
                # Process event
                await self._process_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in event worker {worker_id}: {e}")
                
        logger.info(f"Event worker {worker_id} stopped")

    async def _process_event(self, event: ExtensionEvent) -> None:
        """Process a single event.
        
        Args:
            event: Event to process
        """
        start_time = datetime.now(UTC)
        delivered_count = 0
        
        # Find matching subscriptions
        matching_subscriptions = self._find_matching_subscriptions(event)
        
        # Deliver to each subscription
        delivery_tasks = []
        for subscription_id in matching_subscriptions:
            subscription = self._subscriptions.get(subscription_id)
            if subscription and subscription.active:
                task = asyncio.create_task(
                    self._deliver_event(subscription, event)
                )
                delivery_tasks.append(task)
                
        # Wait for all deliveries
        if delivery_tasks:
            results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Event delivery failed: {result}")
                    self._metrics.failed_deliveries += 1
                else:
                    delivered_count += 1
                    
        # Update metrics
        self._metrics.total_events_delivered += delivered_count
        
        delivery_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        self._update_average_delivery_time(delivery_time)

    def _find_matching_subscriptions(self, event: ExtensionEvent) -> Set[str]:
        """Find subscriptions that match an event.
        
        Args:
            event: Event to match
            
        Returns:
            Set of matching subscription IDs
        """
        matching = set()
        
        # Check topic-based subscriptions
        if event.type in self._topic_subscriptions:
            matching.update(self._topic_subscriptions[event.type])
            
        # Check wildcard subscriptions
        matching.update(self._topic_subscriptions.get("*", set()))
        
        # Apply additional filters
        filtered_matching = set()
        for subscription_id in matching:
            subscription = self._subscriptions.get(subscription_id)
            if subscription and self._event_matches_filter(event, subscription.event_filter):
                filtered_matching.add(subscription_id)
                
        return filtered_matching

    def _event_matches_filter(self, event: ExtensionEvent, event_filter: EventFilter) -> bool:
        """Check if event matches filter.
        
        Args:
            event: Event to check
            event_filter: Filter to apply
            
        Returns:
            True if event matches filter, False otherwise
        """
        # Check event types
        if event_filter.event_types and event.type not in event_filter.event_types:
            return False
            
        # Check source patterns
        if event_filter.source_patterns:
            if not any(self._matches_pattern(event.source, pattern) 
                      for pattern in event_filter.source_patterns):
                return False
                
        # Check target patterns
        if event_filter.target_patterns and event.target:
            if not any(self._matches_pattern(event.target, pattern) 
                      for pattern in event_filter.target_patterns):
                return False
                
        # Check data filters
        if event_filter.data_filters and event.data:
            for key, expected_value in event_filter.data_filters.items():
                if key not in event.data or event.data[key] != expected_value:
                    return False
                    
        return True

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches pattern (supports wildcards).
        
        Args:
            text: Text to check
            pattern: Pattern to match (supports * wildcard)
            
        Returns:
            True if text matches pattern, False otherwise
        """
        if "*" not in pattern:
            return text == pattern
            
        # Simple wildcard matching
        import re
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}$", text))

    async def _deliver_event(self, subscription: EventSubscription, event: ExtensionEvent) -> None:
        """Deliver event to subscription.
        
        Args:
            subscription: Subscription to deliver to
            event: Event to deliver
        """
        try:
            # Update subscription metrics
            subscription.last_triggered = datetime.now(UTC)
            subscription.trigger_count += 1
            
            # Call handler
            if asyncio.iscoroutinefunction(subscription.handler):
                await asyncio.wait_for(
                    subscription.handler(event),
                    timeout=self.config.delivery_timeout_seconds
                )
            else:
                subscription.handler(event)
                
        except asyncio.TimeoutError:
            logger.warning(f"Event delivery timeout for subscription {subscription.subscriber_id}")
            raise
        except Exception as e:
            logger.error(f"Event delivery failed for subscription {subscription.subscriber_id}: {e}")
            
            # Add to dead letter queue if enabled
            if self.config.enable_dead_letter_queue:
                try:
                    await self._dead_letter_queue.put({
                        "event": event,
                        "subscription_id": subscription.subscriber_id,
                        "error": str(e),
                        "timestamp": datetime.now(UTC)
                    })
                except asyncio.QueueFull:
                    logger.error("Dead letter queue full")
                    
            raise

    async def _cleanup_worker(self) -> None:
        """Cleanup worker for expired events and subscriptions."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Clean up event history
                if len(self._event_history) > self._max_history_size:
                    self._event_history = self._event_history[-self._max_history_size:]
                    
                # Clean up inactive subscriptions
                current_time = datetime.now(UTC)
                inactive_threshold = timedelta(hours=24)
                
                inactive_subscriptions = []
                for sub_id, subscription in self._subscriptions.items():
                    if (subscription.last_triggered and 
                        current_time - subscription.last_triggered > inactive_threshold):
                        inactive_subscriptions.append(sub_id)
                        
                for sub_id in inactive_subscriptions:
                    logger.info(f"Removing inactive subscription: {sub_id}")
                    self.unsubscribe(sub_id)
                    
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")

    def _add_to_history(self, event: ExtensionEvent) -> None:
        """Add event to history.
        
        Args:
            event: Event to add
        """
        self._event_history.append(event)
        
        # Trim history if too large
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]

    def _update_average_delivery_time(self, delivery_time_ms: float) -> None:
        """Update average delivery time metric.
        
        Args:
            delivery_time_ms: Delivery time in milliseconds
        """
        current_avg = self._metrics.average_delivery_time_ms
        total_events = self._metrics.total_events_delivered
        
        if total_events == 0:
            self._metrics.average_delivery_time_ms = delivery_time_ms
        else:
            # Calculate running average
            self._metrics.average_delivery_time_ms = (
                (current_avg * (total_events - 1) + delivery_time_ms) / total_events
            )

