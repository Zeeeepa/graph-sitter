"""Event bus for Contexten.

This module provides the EventBus class which handles event routing
and delivery between components.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Base class for all events."""
    type: str
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.
        
        Returns:
            Dict representation of event
        """
        return {
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary.
        
        Args:
            data: Dictionary representation of event
            
        Returns:
            Created event instance
        """
        return cls(
            type=data["type"],
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data"),
            metadata=data.get("metadata"),
        )

class EventError(Exception):
    """Base class for event-related errors."""
    pass

class EventBus:
    """Event bus for routing events between components.
    
    This class provides event publication and subscription capabilities,
    with support for wildcards and filtering.
    """

    def __init__(self, app: 'ContextenApp'):
        """Initialize the event bus.
        
        Args:
            app: The ContextenApp instance this bus belongs to
        """
        self.app = app
        self._subscribers: Dict[str, List[Callable]] = {}
        self._wildcard_subscribers: List[Callable] = []
        self._event_types: Set[str] = set()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any],
        filter_fn: Optional[Callable[[Event], bool]] = None
    ) -> None:
        """Subscribe to events.
        
        Args:
            event_type: Type of events to subscribe to ('*' for all)
            handler: Async callable to handle events
            filter_fn: Optional function to filter events
        """
        if event_type == '*':
            if filter_fn:
                # Create wrapped handler with filter
                async def filtered_handler(event: Event):
                    if filter_fn(event):
                        await handler(event)
                self._wildcard_subscribers.append(filtered_handler)
            else:
                self._wildcard_subscribers.append(handler)
        else:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
                self._event_types.add(event_type)

            if filter_fn:
                # Create wrapped handler with filter
                async def filtered_handler(event: Event):
                    if filter_fn(event):
                        await handler(event)
                self._subscribers[event_type].append(filtered_handler)
            else:
                self._subscribers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any]
    ) -> None:
        """Unsubscribe from events.
        
        Args:
            event_type: Type of events to unsubscribe from ('*' for all)
            handler: Handler to unsubscribe
        """
        if event_type == '*':
            if handler in self._wildcard_subscribers:
                self._wildcard_subscribers.remove(handler)
        else:
            if event_type in self._subscribers:
                if handler in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event.
        
        Args:
            event: Event to publish
        """
        await self._queue.put(event)

    async def start(self) -> None:
        """Start the event bus.
        
        This starts the event processing worker.
        """
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())

    async def stop(self) -> None:
        """Stop the event bus.
        
        This stops the event processing worker.
        """
        if not self._running:
            return

        self._running = False
        if self._worker_task:
            await self._worker_task

    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                # Get next event
                event = await self._queue.get()

                # Call wildcard subscribers
                for handler in self._wildcard_subscribers:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(
                            f"Error in wildcard handler for {event.type}: {e}",
                            exc_info=True
                        )

                # Call specific subscribers
                if event.type in self._subscribers:
                    for handler in self._subscribers[event.type]:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.error(
                                f"Error in handler for {event.type}: {e}",
                                exc_info=True
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
            finally:
                self._queue.task_done()

    def get_event_types(self) -> Set[str]:
        """Get all registered event types.
        
        Returns:
            Set of registered event types
        """
        return self._event_types.copy()

    async def health_check(self) -> Dict[str, Any]:
        """Check event bus health.
        
        Returns:
            Dict containing health status
        """
        return {
            "status": "healthy" if self._running else "stopped",
            "queue_size": self._queue.qsize(),
            "event_types": len(self._event_types),
            "subscribers": {
                "wildcard": len(self._wildcard_subscribers),
                "specific": sum(len(s) for s in self._subscribers.values()),
            },
            "timestamp": self.app.current_time.isoformat(),
        }

