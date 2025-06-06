"""
CircleCI Webhook Processor

Comprehensive webhook processing system with:
- Signature validation and security
- Event routing and handler management
- Retry logic for failed events
- Event persistence and replay
- Performance monitoring
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from dataclasses import dataclass, field
from pathlib import Path
import aiohttp
from urllib.parse import parse_qs

from .config import CircleCIIntegrationConfig
from .types import (
    CircleCIEvent, CircleCIEventType, WorkflowCompletedPayload, JobCompletedPayload,
    PingPayload, CircleCIWebhookPayload, BuildStatus, WebhookStats, ProcessingContext
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class WebhookValidationError(Exception):
    """Webhook validation error"""
    pass


class WebhookProcessingError(Exception):
    """Webhook processing error"""
    pass


@dataclass
class EventHandler:
    """Event handler registration"""
    event_type: Optional[CircleCIEventType]
    handler: Callable[[CircleCIEvent], Awaitable[Any]]
    name: str
    priority: int = 0
    
    def matches(self, event_type: CircleCIEventType) -> bool:
        """Check if handler matches event type"""
        return self.event_type is None or self.event_type == event_type


@dataclass
class ProcessingResult:
    """Result of webhook processing"""
    success: bool
    event_id: Optional[str] = None
    event_type: Optional[CircleCIEventType] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class QueuedEvent:
    """Queued event for processing"""
    event: CircleCIEvent
    context: ProcessingContext
    retry_count: int = 0
    queued_at: datetime = field(default_factory=datetime.now)
    last_attempt: Optional[datetime] = None
    next_retry: Optional[datetime] = None


class WebhookProcessor:
    """
    Comprehensive webhook processor for CircleCI events
    """
    
    def __init__(self, config: CircleCIIntegrationConfig):
        self.config = config
        self.handlers: List[EventHandler] = []
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=config.webhook.max_queue_size)
        self.processing_task: Optional[asyncio.Task] = None
        self.stats = WebhookStats()
        
        # Event storage for replay
        self.event_history: List[CircleCIEvent] = []
        self.max_history_size = 1000
        
        # Processing state
        self.is_running = False
        self.shutdown_event = asyncio.Event()
    
    def register_handler(
        self,
        handler: Callable[[CircleCIEvent], Awaitable[Any]],
        event_type: Optional[CircleCIEventType] = None,
        name: Optional[str] = None,
        priority: int = 0
    ):
        """Register an event handler"""
        handler_name = name or f"{handler.__name__}_{len(self.handlers)}"
        
        event_handler = EventHandler(
            event_type=event_type,
            handler=handler,
            name=handler_name,
            priority=priority
        )
        
        self.handlers.append(event_handler)
        # Sort by priority (higher priority first)
        self.handlers.sort(key=lambda h: h.priority, reverse=True)
        
        logger.info(f"Registered handler '{handler_name}' for event type {event_type}")
    
    def unregister_handler(self, name: str) -> bool:
        """Unregister an event handler by name"""
        for i, handler in enumerate(self.handlers):
            if handler.name == name:
                del self.handlers[i]
                logger.info(f"Unregistered handler '{name}'")
                return True
        
        logger.warning(f"Handler '{name}' not found")
        return False
    
    async def start(self):
        """Start the webhook processor"""
        if self.is_running:
            logger.warning("Webhook processor is already running")
            return
        
        self.is_running = True
        self.shutdown_event.clear()
        
        # Start processing task
        self.processing_task = asyncio.create_task(self._process_events())
        
        logger.info("Webhook processor started")
    
    async def stop(self):
        """Stop the webhook processor"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.shutdown_event.set()
        
        # Cancel processing task
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Webhook processor stopped")
    
    async def process_webhook(
        self,
        headers: Dict[str, str],
        body: Union[str, bytes],
        remote_addr: Optional[str] = None
    ) -> ProcessingResult:
        """Process incoming webhook"""
        start_time = time.time()
        
        try:
            # Update stats
            self.stats.requests_total += 1
            self.stats.last_request_at = datetime.now()
            
            # Validate webhook
            await self._validate_webhook(headers, body, remote_addr)
            
            # Parse payload
            payload = await self._parse_payload(body)
            
            # Convert to internal event
            event = await self._convert_to_event(payload)
            
            # Queue for processing
            context = ProcessingContext(
                event_id=event.id,
                project_slug=event.project_slug,
                organization=event.organization,
                timestamp=event.timestamp
            )
            
            queued_event = QueuedEvent(event=event, context=context)
            
            try:
                self.event_queue.put_nowait(queued_event)
            except asyncio.QueueFull:
                logger.error("Event queue is full, dropping event")
                self.stats.requests_failed += 1
                return ProcessingResult(
                    success=False,
                    error="Event queue is full"
                )
            
            # Update stats
            self.stats.requests_successful += 1
            self.stats.events_processed += 1
            
            processing_time = time.time() - start_time
            self.stats.average_response_time = (
                (self.stats.average_response_time * (self.stats.requests_total - 1) + processing_time) /
                self.stats.requests_total
            )
            
            # Update event type stats
            if event.type == CircleCIEventType.WORKFLOW_COMPLETED:
                self.stats.workflow_events += 1
            elif event.type == CircleCIEventType.JOB_COMPLETED:
                self.stats.job_events += 1
            elif event.type == CircleCIEventType.PING:
                self.stats.ping_events += 1
            
            return ProcessingResult(
                success=True,
                event_id=event.id,
                event_type=event.type,
                processing_time=processing_time
            )
            
        except WebhookValidationError as e:
            self.stats.requests_failed += 1
            self.stats.signature_failures += 1
            logger.warning(f"Webhook validation failed: {e}")
            return ProcessingResult(success=False, error=str(e))
            
        except Exception as e:
            self.stats.requests_failed += 1
            self.stats.events_failed += 1
            logger.error(f"Webhook processing failed: {e}")
            return ProcessingResult(success=False, error=str(e))
    
    async def _validate_webhook(
        self,
        headers: Dict[str, str],
        body: Union[str, bytes],
        remote_addr: Optional[str] = None
    ):
        """Validate webhook signature and headers"""
        
        # Convert body to bytes if needed
        if isinstance(body, str):
            body_bytes = body.encode('utf-8')
        else:
            body_bytes = body
        
        # Validate signature if configured
        if self.config.webhook.validate_signatures and self.config.webhook.webhook_secret:
            signature_header = self.config.webhook.webhook_signature_header
            signature = headers.get(signature_header)
            
            if not signature:
                raise WebhookValidationError(f"Missing signature header: {signature_header}")
            
            # CircleCI uses HMAC-SHA256
            expected_signature = hmac.new(
                self.config.webhook.webhook_secret.get_secret_value().encode('utf-8'),
                body_bytes,
                hashlib.sha256
            ).hexdigest()
            
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            if not hmac.compare_digest(signature, expected_signature):
                raise WebhookValidationError("Invalid webhook signature")
            
            self.stats.signature_validations += 1
        
        # Validate timestamp if configured
        if self.config.webhook.validate_timestamps:
            timestamp_header = headers.get('x-circleci-timestamp')
            if timestamp_header:
                try:
                    webhook_time = datetime.fromisoformat(timestamp_header.replace('Z', '+00:00'))
                    time_diff = abs((datetime.now() - webhook_time).total_seconds())
                    
                    if time_diff > self.config.webhook.timestamp_tolerance:
                        raise WebhookValidationError(f"Webhook timestamp too old: {time_diff}s")
                        
                except ValueError as e:
                    raise WebhookValidationError(f"Invalid timestamp format: {e}")
        
        # TODO: Add IP allowlist validation if needed
        
        logger.debug("Webhook validation passed")
    
    async def _parse_payload(self, body: Union[str, bytes]) -> CircleCIWebhookPayload:
        """Parse webhook payload"""
        try:
            if isinstance(body, bytes):
                body_str = body.decode('utf-8')
            else:
                body_str = body
            
            data = json.loads(body_str)
            
            # Determine event type
            event_type = data.get('type')
            if not event_type:
                raise WebhookProcessingError("Missing event type in payload")
            
            try:
                event_type_enum = CircleCIEventType(event_type)
            except ValueError:
                raise WebhookProcessingError(f"Unknown event type: {event_type}")
            
            # Create appropriate payload object
            if event_type_enum == CircleCIEventType.WORKFLOW_COMPLETED:
                return WorkflowCompletedPayload(**data)
            elif event_type_enum == CircleCIEventType.JOB_COMPLETED:
                return JobCompletedPayload(**data)
            elif event_type_enum == CircleCIEventType.PING:
                return PingPayload(**data)
            else:
                # Generic payload for unknown types
                return CircleCIWebhookPayload(**data)
                
        except json.JSONDecodeError as e:
            raise WebhookProcessingError(f"Invalid JSON payload: {e}")
        except Exception as e:
            raise WebhookProcessingError(f"Failed to parse payload: {e}")
    
    async def _convert_to_event(self, payload: CircleCIWebhookPayload) -> CircleCIEvent:
        """Convert webhook payload to internal event"""
        
        # Extract common fields
        event_data = {
            "id": payload.id,
            "type": payload.type,
            "timestamp": payload.happened_at,
            "processed_at": datetime.now()
        }
        
        # Extract type-specific fields
        if isinstance(payload, WorkflowCompletedPayload):
            event_data.update({
                "project_slug": payload.workflow.project_slug,
                "organization": payload.project.organization_name,
                "workflow_id": payload.workflow.id,
                "status": payload.workflow.status,
                "branch": payload.pipeline.get("vcs", {}).get("branch"),
                "commit_sha": payload.pipeline.get("vcs", {}).get("revision")
            })
            
        elif isinstance(payload, JobCompletedPayload):
            event_data.update({
                "project_slug": payload.job.project_slug,
                "organization": payload.project.organization_name,
                "job_id": payload.job.id,
                "status": payload.job.status,
                "branch": payload.pipeline.get("vcs", {}).get("branch"),
                "commit_sha": payload.pipeline.get("vcs", {}).get("revision")
            })
            
        elif isinstance(payload, PingPayload):
            # Ping events don't have project info
            event_data.update({
                "project_slug": "ping",
                "organization": "circleci"
            })
        
        return CircleCIEvent(**event_data)
    
    async def _process_events(self):
        """Main event processing loop"""
        logger.info("Started event processing loop")
        
        while self.is_running:
            try:
                # Wait for event or shutdown
                try:
                    queued_event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                await self._process_single_event(queued_event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(1)
        
        logger.info("Event processing loop stopped")
    
    async def _process_single_event(self, queued_event: QueuedEvent):
        """Process a single event"""
        event = queued_event.event
        context = queued_event.context
        
        start_time = time.time()
        
        try:
            # Check if event should be processed
            if not await self._should_process_event(event):
                logger.debug(f"Skipping event {event.id} (filtered)")
                return
            
            # Add to history
            self._add_to_history(event)
            
            # Find matching handlers
            matching_handlers = [h for h in self.handlers if h.matches(event.type)]
            
            if not matching_handlers:
                logger.debug(f"No handlers for event type {event.type}")
                return
            
            # Process with each handler
            for handler in matching_handlers:
                try:
                    logger.debug(f"Processing event {event.id} with handler {handler.name}")
                    
                    # Set timeout for handler
                    await asyncio.wait_for(
                        handler.handler(event),
                        timeout=self.config.webhook.processing_timeout
                    )
                    
                    logger.debug(f"Handler {handler.name} completed successfully")
                    
                except asyncio.TimeoutError:
                    logger.error(f"Handler {handler.name} timed out for event {event.id}")
                    self.stats.events_failed += 1
                    
                except Exception as e:
                    logger.error(f"Handler {handler.name} failed for event {event.id}: {e}")
                    self.stats.events_failed += 1
                    
                    # Decide whether to retry
                    if (self.config.webhook.retry_failed_events and 
                        queued_event.retry_count < self.config.webhook.max_event_retries):
                        
                        await self._schedule_retry(queued_event)
                        return
            
            # Update processing stats
            processing_time = time.time() - start_time
            context.metadata["processing_time"] = processing_time
            
            logger.debug(f"Event {event.id} processed successfully in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to process event {event.id}: {e}")
            self.stats.events_failed += 1
            
            # Schedule retry if configured
            if (self.config.webhook.retry_failed_events and 
                queued_event.retry_count < self.config.webhook.max_event_retries):
                
                await self._schedule_retry(queued_event)
    
    async def _should_process_event(self, event: CircleCIEvent) -> bool:
        """Check if event should be processed"""
        
        # Skip ping events if configured
        if (event.type == CircleCIEventType.PING and 
            self.config.webhook.ignore_ping_events):
            return False
        
        # Check branch filters
        if event.branch:
            if (self.config.webhook.filter_branches and 
                event.branch not in self.config.webhook.filter_branches):
                return False
            
            if (self.config.webhook.ignore_branches and 
                event.branch in self.config.webhook.ignore_branches):
                return False
        
        # Check project filters
        if event.project_slug:
            if (self.config.security.allowed_projects and 
                event.project_slug not in self.config.security.allowed_projects):
                return False
            
            if event.project_slug in self.config.security.blocked_projects:
                return False
        
        return True
    
    async def _schedule_retry(self, queued_event: QueuedEvent):
        """Schedule event for retry"""
        queued_event.retry_count += 1
        queued_event.last_attempt = datetime.now()
        
        # Calculate retry delay (exponential backoff)
        delay = min(2 ** queued_event.retry_count, 300)  # Max 5 minutes
        queued_event.next_retry = datetime.now() + timedelta(seconds=delay)
        
        logger.info(f"Scheduling retry {queued_event.retry_count} for event {queued_event.event.id} in {delay}s")
        
        # Schedule the retry
        asyncio.create_task(self._retry_event(queued_event, delay))
        
        self.stats.events_retried += 1
    
    async def _retry_event(self, queued_event: QueuedEvent, delay: float):
        """Retry an event after delay"""
        await asyncio.sleep(delay)
        
        if self.is_running:
            try:
                self.event_queue.put_nowait(queued_event)
                logger.debug(f"Retrying event {queued_event.event.id}")
            except asyncio.QueueFull:
                logger.error(f"Queue full, dropping retry for event {queued_event.event.id}")
    
    def _add_to_history(self, event: CircleCIEvent):
        """Add event to history"""
        self.event_history.append(event)
        
        # Trim history if too large
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
    
    # Public API methods
    def get_stats(self) -> WebhookStats:
        """Get webhook processing statistics"""
        return self.stats
    
    def get_queue_info(self) -> Dict[str, Any]:
        """Get queue information"""
        return {
            "queue_size": self.event_queue.qsize(),
            "max_queue_size": self.event_queue.maxsize,
            "is_running": self.is_running,
            "handlers_registered": len(self.handlers)
        }
    
    def get_recent_events(self, limit: int = 10) -> List[CircleCIEvent]:
        """Get recent events from history"""
        return self.event_history[-limit:]
    
    def get_handlers(self) -> List[Dict[str, Any]]:
        """Get registered handlers info"""
        return [
            {
                "name": handler.name,
                "event_type": handler.event_type.value if handler.event_type else "all",
                "priority": handler.priority
            }
            for handler in self.handlers
        ]
    
    async def replay_event(self, event_id: str) -> bool:
        """Replay an event from history"""
        for event in self.event_history:
            if event.id == event_id:
                context = ProcessingContext(
                    event_id=event.id,
                    project_slug=event.project_slug,
                    organization=event.organization,
                    timestamp=event.timestamp,
                    metadata={"replayed": True}
                )
                
                queued_event = QueuedEvent(event=event, context=context)
                
                try:
                    self.event_queue.put_nowait(queued_event)
                    logger.info(f"Replaying event {event_id}")
                    return True
                except asyncio.QueueFull:
                    logger.error(f"Queue full, cannot replay event {event_id}")
                    return False
        
        logger.warning(f"Event {event_id} not found in history")
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "healthy": self.is_running,
            "queue_size": self.event_queue.qsize(),
            "queue_full": self.event_queue.full(),
            "handlers_count": len(self.handlers),
            "stats": self.stats.dict()
        }

