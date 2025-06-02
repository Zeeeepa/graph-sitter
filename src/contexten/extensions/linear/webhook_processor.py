"""
Linear Webhook Processor

Comprehensive webhook processing system with:
- Signature validation and security
- Event routing and handler management
- Retry logic for failed events
- Event persistence and replay
- Performance monitoring
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable
import asyncio
import hashlib
import hmac
import json
import time

from .config import LinearIntegrationConfig
from .types import (
    LinearEvent, LinearEventType, WebhookEvent, ComponentStats
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class EventHandler:
    """Event handler registration"""
    event_type: Optional[LinearEventType]
    handler: Callable[[Dict[str, Any]], Awaitable[Any]]
    name: str
    priority: int = 0
    
    def matches(self, event_type: str) -> bool:
        """Check if handler matches event type"""
        return self.event_type is None or self.event_type.value == event_type


@dataclass
class ProcessingStats:
    """Webhook processing statistics"""
    events_received: int = 0
    events_processed: int = 0
    events_failed: int = 0
    events_retried: int = 0
    signature_failures: int = 0
    last_event_time: Optional[datetime] = None
    last_error: Optional[str] = None


class WebhookProcessor:
    """Comprehensive webhook processor for Linear events"""
    
    def __init__(self, config: LinearIntegrationConfig):
        self.config = config
        self.webhook_config = config.webhook
        
        # Event handlers
        self.handlers: List[EventHandler] = []
        self.global_handlers: List[EventHandler] = []
        
        # Event queue and processing
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=config.events.queue_size)
        self.processing_task: Optional[asyncio.Task] = None
        self.is_processing = False
        
        # Event persistence
        self.persistence_file = Path(config.events.persistence_file)
        self.failed_events: List[WebhookEvent] = []
        
        # Statistics
        self.stats = ComponentStats()
        self.processing_stats = ProcessingStats()
        self.start_time = datetime.now()
        
        logger.info("Webhook processor initialized")
    
    def register_handler(
        self, 
        event_type: LinearEventType, 
        handler: Callable[[Dict[str, Any]], Awaitable[Any]],
        name: Optional[str] = None,
        priority: int = 0
    ) -> None:
        """Register an event handler for specific event type"""
        handler_name = name or f"{handler.__name__}_{event_type.value}"
        event_handler = EventHandler(
            event_type=event_type,
            handler=handler,
            name=handler_name,
            priority=priority
        )
        
        self.handlers.append(event_handler)
        self.handlers.sort(key=lambda h: h.priority, reverse=True)
        
        logger.info(f"Registered handler '{handler_name}' for event type '{event_type.value}'")
    
    def register_global_handler(
        self, 
        handler: Callable[[Dict[str, Any]], Awaitable[Any]],
        name: Optional[str] = None,
        priority: int = 0
    ) -> None:
        """Register a global handler that processes all events"""
        handler_name = name or f"{handler.__name__}_global"
        event_handler = EventHandler(
            event_type=None,
            handler=handler,
            name=handler_name,
            priority=priority
        )
        
        self.global_handlers.append(event_handler)
        self.global_handlers.sort(key=lambda h: h.priority, reverse=True)
        
        logger.info(f"Registered global handler '{handler_name}'")
    
    def unregister_handler(self, name: str) -> bool:
        """Unregister a handler by name"""
        # Check specific handlers
        for i, handler in enumerate(self.handlers):
            if handler.name == name:
                del self.handlers[i]
                logger.info(f"Unregistered handler '{name}'")
                return True
        
        # Check global handlers
        for i, handler in enumerate(self.global_handlers):
            if handler.name == name:
                del self.global_handlers[i]
                logger.info(f"Unregistered global handler '{name}'")
                return True
        
        logger.warning(f"Handler '{name}' not found")
        return False
    
    def _validate_signature(self, payload: bytes, signature: str) -> bool:
        """Validate webhook signature"""
        if not self.webhook_config.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature validation")
            return True
        
        if not signature:
            logger.error("No signature provided in webhook")
            self.processing_stats.signature_failures += 1
            return False
        
        try:
            # Linear uses HMAC-SHA256
            expected_signature = hmac.new(
                self.webhook_config.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            if not hmac.compare_digest(expected_signature, signature):
                logger.error("Invalid webhook signature")
                self.processing_stats.signature_failures += 1
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signature: {e}")
            self.processing_stats.signature_failures += 1
            return False
    
    def _validate_payload_size(self, payload: bytes) -> bool:
        """Validate payload size"""
        if len(payload) > self.webhook_config.max_payload_size:
            logger.error(f"Payload too large: {len(payload)} bytes (max: {self.webhook_config.max_payload_size})")
            return False
        return True
    
    def _parse_webhook_event(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Parse webhook payload into WebhookEvent"""
        try:
            event_type = payload.get("type")
            if not event_type:
                logger.error("No event type in webhook payload")
                return None
            
            # Map event type to enum
            try:
                linear_event_type = LinearEventType(event_type)
            except ValueError:
                logger.warning(f"Unknown event type: {event_type}")
                # Create a generic event type for unknown events
                linear_event_type = event_type
            
            webhook_event = WebhookEvent(
                event_id=f"{event_type}_{int(time.time() * 1000)}",
                event_type=linear_event_type,
                payload=payload,
                timestamp=datetime.now()
            )
            
            return webhook_event
            
        except Exception as e:
            logger.error(f"Error parsing webhook event: {e}")
            return None
    
    async def process_webhook(
        self, 
        payload: bytes, 
        signature: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Process incoming webhook"""
        try:
            self.processing_stats.events_received += 1
            self.processing_stats.last_event_time = datetime.now()
            
            # Validate payload size
            if not self._validate_payload_size(payload):
                return False
            
            # Validate signature
            if not self._validate_signature(payload, signature):
                return False
            
            # Parse JSON payload
            try:
                payload_dict = json.loads(payload.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON payload: {e}")
                return False
            
            # Parse webhook event
            webhook_event = self._parse_webhook_event(payload_dict)
            if not webhook_event:
                return False
            
            webhook_event.signature = signature
            
            # Add to processing queue
            try:
                await asyncio.wait_for(
                    self.event_queue.put(webhook_event),
                    timeout=5.0
                )
                logger.info(f"Queued webhook event: {webhook_event.event_type}")
                return True
                
            except asyncio.TimeoutError:
                logger.error("Event queue is full, dropping webhook event")
                return False
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            self.processing_stats.last_error = str(e)
            return False
    
    async def _process_event(self, webhook_event: WebhookEvent) -> bool:
        """Process a single webhook event"""
        try:
            event_type = webhook_event.event_type
            payload = webhook_event.payload
            
            logger.info(f"Processing event: {event_type} (ID: {webhook_event.event_id})")
            
            # Get matching handlers
            matching_handlers = []
            
            # Add specific handlers
            for handler in self.handlers:
                if handler.matches(str(event_type)):
                    matching_handlers.append(handler)
            
            # Add global handlers
            matching_handlers.extend(self.global_handlers)
            
            if not matching_handlers:
                logger.info(f"No handlers registered for event type: {event_type}")
                return True
            
            # Execute handlers
            success = True
            for handler in matching_handlers:
                try:
                    logger.debug(f"Executing handler: {handler.name}")
                    result = await handler.handler(payload)
                    logger.debug(f"Handler {handler.name} completed successfully")
                    
                except Exception as e:
                    logger.error(f"Handler {handler.name} failed: {e}")
                    success = False
                    # Continue with other handlers
            
            if success:
                webhook_event.processed = True
                self.processing_stats.events_processed += 1
                logger.info(f"Successfully processed event: {webhook_event.event_id}")
            else:
                self.processing_stats.events_failed += 1
                logger.error(f"Failed to process event: {webhook_event.event_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing event {webhook_event.event_id}: {e}")
            self.processing_stats.events_failed += 1
            self.processing_stats.last_error = str(e)
            return False
    
    async def _retry_failed_event(self, webhook_event: WebhookEvent) -> bool:
        """Retry processing a failed event"""
        if webhook_event.retry_count >= self.webhook_config.max_retries:
            logger.error(f"Event {webhook_event.event_id} exceeded max retries ({self.webhook_config.max_retries})")
            return False
        
        webhook_event.retry_count += 1
        self.processing_stats.events_retried += 1
        
        # Exponential backoff
        delay = self.webhook_config.retry_delay * (2 ** (webhook_event.retry_count - 1))
        logger.info(f"Retrying event {webhook_event.event_id} in {delay} seconds (attempt {webhook_event.retry_count})")
        
        await asyncio.sleep(delay)
        return await self._process_event(webhook_event)
    
    async def _event_processing_loop(self) -> None:
        """Main event processing loop"""
        logger.info("Starting event processing loop")
        
        while self.is_processing:
            try:
                # Get events from queue in batches
                events_batch = []
                batch_size = self.config.events.batch_size
                
                # Get first event (blocking)
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=self.config.events.processing_interval
                    )
                    events_batch.append(event)
                except asyncio.TimeoutError:
                    continue
                
                # Get additional events (non-blocking)
                for _ in range(batch_size - 1):
                    try:
                        event = self.event_queue.get_nowait()
                        events_batch.append(event)
                    except asyncio.QueueEmpty:
                        break
                
                # Process batch
                for event in events_batch:
                    success = await self._process_event(event)
                    
                    if not success:
                        # Add to failed events for retry
                        self.failed_events.append(event)
                    
                    # Mark task as done
                    self.event_queue.task_done()
                
                # Process failed events
                if self.failed_events:
                    await self._process_failed_events()
                
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(1)
        
        logger.info("Event processing loop stopped")
    
    async def _process_failed_events(self) -> None:
        """Process failed events with retry logic"""
        if not self.failed_events:
            return
        
        events_to_retry = []
        events_to_remove = []
        
        for event in self.failed_events:
            # Check if event is too old
            age = datetime.now() - event.timestamp
            if age.total_seconds() > self.config.events.max_event_age:
                logger.warning(f"Dropping old failed event: {event.event_id}")
                events_to_remove.append(event)
                continue
            
            # Check if ready for retry
            if event.retry_count == 0 or (datetime.now() - event.timestamp).total_seconds() >= self.config.events.retry_interval:
                events_to_retry.append(event)
        
        # Remove old events
        for event in events_to_remove:
            self.failed_events.remove(event)
        
        # Retry events
        for event in events_to_retry:
            success = await self._retry_failed_event(event)
            if success or event.retry_count >= self.webhook_config.max_retries:
                self.failed_events.remove(event)
    
    async def start_processing(self) -> None:
        """Start the event processing loop"""
        if self.is_processing:
            logger.warning("Event processing is already running")
            return
        
        self.is_processing = True
        self.processing_task = asyncio.create_task(self._event_processing_loop())
        logger.info("Event processing started")
    
    async def stop_processing(self) -> None:
        """Stop the event processing loop"""
        if not self.is_processing:
            logger.warning("Event processing is not running")
            return
        
        self.is_processing = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            self.processing_task = None
        
        logger.info("Event processing stopped")
    
    async def process_event_directly(self, payload: Dict[str, Any]) -> bool:
        """Process an event directly without going through the queue"""
        webhook_event = self._parse_webhook_event(payload)
        if not webhook_event:
            return False
        
        return await self._process_event(webhook_event)
    
    def get_stats(self) -> ComponentStats:
        """Get processing statistics"""
        self.stats.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        self.stats.requests_made = self.processing_stats.events_received
        self.stats.requests_successful = self.processing_stats.events_processed
        self.stats.requests_failed = self.processing_stats.events_failed
        self.stats.last_error = self.processing_stats.last_error
        self.stats.last_request = self.processing_stats.last_event_time
        
        return self.stats
    
    def get_processing_stats(self) -> ProcessingStats:
        """Get detailed processing statistics"""
        return self.processing_stats
    
    def get_queue_info(self) -> Dict[str, Any]:
        """Get event queue information"""
        return {
            "queue_size": self.event_queue.qsize(),
            "max_queue_size": self.event_queue.maxsize,
            "failed_events": len(self.failed_events),
            "is_processing": self.is_processing,
            "registered_handlers": len(self.handlers),
            "global_handlers": len(self.global_handlers)
        }
    
    async def save_failed_events(self) -> None:
        """Save failed events to disk for persistence"""
        if not self.config.events.persistence_enabled or not self.failed_events:
            return
        
        try:
            events_data = []
            for event in self.failed_events:
                events_data.append({
                    "event_id": event.event_id,
                    "event_type": str(event.event_type),
                    "payload": event.payload,
                    "timestamp": event.timestamp.isoformat(),
                    "retry_count": event.retry_count,
                    "error_message": event.error_message
                })
            
            with open(self.persistence_file, 'w') as f:
                json.dump(events_data, f, indent=2)
            
            logger.info(f"Saved {len(events_data)} failed events to {self.persistence_file}")
            
        except Exception as e:
            logger.error(f"Error saving failed events: {e}")
    
    async def load_failed_events(self) -> None:
        """Load failed events from disk"""
        if not self.config.events.persistence_enabled or not self.persistence_file.exists():
            return
        
        try:
            with open(self.persistence_file, 'r') as f:
                events_data = json.load(f)
            
            for event_data in events_data:
                webhook_event = WebhookEvent(
                    event_id=event_data["event_id"],
                    event_type=event_data["event_type"],
                    payload=event_data["payload"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    retry_count=event_data["retry_count"],
                    error_message=event_data.get("error_message")
                )
                self.failed_events.append(webhook_event)
            
            logger.info(f"Loaded {len(events_data)} failed events from {self.persistence_file}")
            
        except Exception as e:
            logger.error(f"Error loading failed events: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        await self.stop_processing()
        
        if self.config.events.persistence_enabled:
            await self.save_failed_events()
        
        logger.info("Webhook processor cleanup completed")

