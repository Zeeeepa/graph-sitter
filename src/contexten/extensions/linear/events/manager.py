"""
Linear Event Manager

This module provides enhanced event management and processing for Linear integration
with persistent storage, batch processing, and event replay capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from ....shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class EventStatus(str, Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class PersistedEvent:
    """Persistent event with metadata"""
    id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    status: EventStatus
    retry_count: int = 0
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "retry_count": self.retry_count,
            "last_attempt": self.last_attempt.isoformat() if self.last_attempt else None,
            "error_message": self.error_message,
            "max_retries": self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersistedEvent":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            event_type=data["event_type"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=EventStatus(data["status"]),
            retry_count=data.get("retry_count", 0),
            last_attempt=datetime.fromisoformat(data["last_attempt"]) if data.get("last_attempt") else None,
            error_message=data.get("error_message"),
            max_retries=data.get("max_retries", 3)
        )


class EnhancedEventManager:
    """Enhanced Linear event management system with persistence and batch processing"""
    
    def __init__(
        self, 
        persistence_file: str = "linear_events.json",
        batch_size: int = 10,
        processing_interval: int = 5,
        retry_interval: int = 60,
        max_event_age_hours: int = 24
    ):
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._pending_events: List[PersistedEvent] = []
        self._failed_events: List[PersistedEvent] = []
        self._running = False
        
        # Configuration
        self.persistence_file = Path(persistence_file)
        self.batch_size = batch_size
        self.processing_interval = processing_interval
        self.retry_interval = retry_interval
        self.max_event_age = timedelta(hours=max_event_age_hours)
        
        # Background tasks
        self._processing_task: Optional[asyncio.Task] = None
        self._retry_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "events_processed": 0,
            "events_failed": 0,
            "events_retried": 0,
            "batch_operations": 0,
            "last_persistence": None,
            "last_cleanup": None,
            "start_time": datetime.utcnow()
        }
        
        # Load persisted events on initialization
        self._load_persisted_events()

    async def start(self) -> None:
        """Start enhanced event manager with background processing"""
        self._running = True
        
        # Start background processing tasks
        self._processing_task = asyncio.create_task(self._process_events_loop())
        self._retry_task = asyncio.create_task(self._retry_failed_events_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_old_events_loop())
        
        logger.info(f"Enhanced Linear event manager started with batch_size={self.batch_size}")
    
    async def stop(self) -> None:
        """Stop event manager and cleanup"""
        self._running = False
        
        # Cancel background tasks
        for task in [self._processing_task, self._retry_task, self._cleanup_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Persist remaining events
        await self._persist_events()
        
        logger.info("Enhanced Linear event manager stopped")
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type}")

    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Emit an event with persistence"""
        event = PersistedEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
            status=EventStatus.PENDING
        )
        
        self._pending_events.append(event)
        logger.debug(f"Emitted event: {event_type} (ID: {event.id})")
        
        # Persist immediately for critical events
        if len(self._pending_events) >= self.batch_size:
            await self._persist_events()
        
        return event.id
    
    async def process_pending_events(self) -> None:
        """Process all pending events"""
        while self._pending_events:
            event = self._pending_events.pop(0)
            await self._process_event(event)
    
    async def _process_event(self, event: Dict[str, Any]) -> None:
        """Process a single event"""
        event_type = event.get("type")
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
    
    def is_healthy(self) -> bool:
        """Check if event manager is healthy"""
        return (
            self._running and 
            len(self._pending_events) < self.batch_size * 10 and  # Not overwhelmed
            len(self._failed_events) < 100  # Not too many failures
        )

    async def _process_events_loop(self) -> None:
        """Background loop for processing events in batches"""
        while self._running:
            try:
                if self._pending_events:
                    await self._process_event_batch()
                await asyncio.sleep(self.processing_interval)
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(self.processing_interval)
    
    async def _process_event_batch(self) -> None:
        """Process a batch of events"""
        if not self._pending_events:
            return
        
        # Get batch of events to process
        batch = self._pending_events[:self.batch_size]
        
        logger.info(f"Processing batch of {len(batch)} events")
        
        processed_events = []
        failed_events = []
        
        for event in batch:
            try:
                event.status = EventStatus.PROCESSING
                event.last_attempt = datetime.utcnow()
                
                success = await self._process_single_event(event)
                
                if success:
                    event.status = EventStatus.COMPLETED
                    processed_events.append(event)
                    self.stats["events_processed"] += 1
                else:
                    event.status = EventStatus.FAILED
                    event.retry_count += 1
                    failed_events.append(event)
                    self.stats["events_failed"] += 1
                    
            except Exception as e:
                event.status = EventStatus.FAILED
                event.error_message = str(e)
                event.retry_count += 1
                failed_events.append(event)
                self.stats["events_failed"] += 1
                logger.error(f"Error processing event {event.id}: {e}")
        
        # Remove processed events from pending
        for event in processed_events + failed_events:
            if event in self._pending_events:
                self._pending_events.remove(event)
        
        # Add failed events to retry queue if they haven't exceeded max retries
        for event in failed_events:
            if event.retry_count < event.max_retries:
                event.status = EventStatus.RETRYING
                self._failed_events.append(event)
            else:
                logger.error(f"Event {event.id} exceeded max retries ({event.max_retries})")
        
        self.stats["batch_operations"] += 1
        
        # Persist state after batch processing
        await self._persist_events()
    
    async def _process_single_event(self, event: PersistedEvent) -> bool:
        """Process a single event"""
        event_type = event.event_type
        
        if event_type not in self._event_handlers:
            logger.warning(f"No handlers registered for event type: {event_type}")
            return True  # Consider unhandled events as "processed"
        
        success = True
        for handler in self._event_handlers[event_type]:
            try:
                await handler(event.data)
            except Exception as e:
                logger.error(f"Handler {handler.__name__} failed for event {event.id}: {e}")
                success = False
        
        return success
    
    async def _retry_failed_events_loop(self) -> None:
        """Background loop for retrying failed events"""
        while self._running:
            try:
                await self._retry_failed_events()
                await asyncio.sleep(self.retry_interval)
            except Exception as e:
                logger.error(f"Error in retry loop: {e}")
                await asyncio.sleep(self.retry_interval)
    
    async def _retry_failed_events(self) -> None:
        """Retry failed events that are ready for retry"""
        if not self._failed_events:
            return
        
        retry_cutoff = datetime.utcnow() - timedelta(seconds=self.retry_interval)
        events_to_retry = [
            event for event in self._failed_events 
            if event.last_attempt and event.last_attempt < retry_cutoff
        ]
        
        if not events_to_retry:
            return
        
        logger.info(f"Retrying {len(events_to_retry)} failed events")
        
        for event in events_to_retry:
            self._failed_events.remove(event)
            self._pending_events.append(event)
            self.stats["events_retried"] += 1
    
    async def _cleanup_old_events_loop(self) -> None:
        """Background loop for cleaning up old events"""
        while self._running:
            try:
                await self._cleanup_old_events()
                await asyncio.sleep(3600)  # Run cleanup every hour
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_old_events(self) -> None:
        """Clean up old events that exceed max age"""
        cutoff_time = datetime.utcnow() - self.max_event_age
        
        # Clean up completed events older than max age
        initial_count = len(self._pending_events) + len(self._failed_events)
        
        self._pending_events = [
            event for event in self._pending_events 
            if event.timestamp > cutoff_time or event.status != EventStatus.COMPLETED
        ]
        
        self._failed_events = [
            event for event in self._failed_events 
            if event.timestamp > cutoff_time
        ]
        
        final_count = len(self._pending_events) + len(self._failed_events)
        cleaned_count = initial_count - final_count
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old events")
        
        self.stats["last_cleanup"] = datetime.utcnow()
        await self._persist_events()
    
    def _load_persisted_events(self) -> None:
        """Load persisted events from disk"""
        if not self.persistence_file.exists():
            logger.info("No persisted events file found")
            return
        
        try:
            with open(self.persistence_file, 'r') as f:
                data = json.load(f)
            
            # Load pending events
            for event_data in data.get("pending_events", []):
                event = PersistedEvent.from_dict(event_data)
                self._pending_events.append(event)
            
            # Load failed events
            for event_data in data.get("failed_events", []):
                event = PersistedEvent.from_dict(event_data)
                self._failed_events.append(event)
            
            # Load statistics
            self.stats.update(data.get("stats", {}))
            
            logger.info(f"Loaded {len(self._pending_events)} pending and {len(self._failed_events)} failed events from persistence")
            
        except Exception as e:
            logger.error(f"Error loading persisted events: {e}")

    async def _persist_events(self) -> None:
        """Persist events to disk"""
        try:
            # Prepare data for persistence
            data = {
                "pending_events": [event.to_dict() for event in self._pending_events],
                "failed_events": [event.to_dict() for event in self._failed_events],
                "stats": self.stats,
                "last_persisted": datetime.utcnow().isoformat()
            }
            
            # Write to temporary file first, then rename for atomic operation
            temp_file = self.persistence_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            temp_file.rename(self.persistence_file)
            self.stats["last_persistence"] = datetime.utcnow()
            
            logger.debug(f"Persisted {len(self._pending_events)} pending and {len(self._failed_events)} failed events")
            
        except Exception as e:
            logger.error(f"Error persisting events: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event manager statistics"""
        return {
            **self.stats,
            "pending_events": len(self._pending_events),
            "failed_events": len(self._failed_events),
            "is_running": self._running,
            "uptime_seconds": (datetime.utcnow() - self.stats.get("start_time", datetime.utcnow())).total_seconds()
        }
    
    async def replay_events(self, event_ids: Optional[List[str]] = None) -> int:
        """Replay specific events or all failed events"""
        if event_ids:
            # Replay specific events
            events_to_replay = [
                event for event in self._failed_events 
                if event.id in event_ids
            ]
        else:
            # Replay all failed events
            events_to_replay = self._failed_events.copy()
        
        if not events_to_replay:
            return 0
        
        # Move events back to pending queue
        for event in events_to_replay:
            event.status = EventStatus.PENDING
            event.retry_count = 0
            event.error_message = None
            if event in self._failed_events:
                self._failed_events.remove(event)
            self._pending_events.append(event)
        
        logger.info(f"Replaying {len(events_to_replay)} events")
        return len(events_to_replay)


# Backward compatibility alias
EventManager = EnhancedEventManager
