"""
Linear Webhook Processor

This module handles processing of incoming Linear webhooks with validation,
routing, and event handling capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime
import time

from .handlers import WebhookHandlers
from .validator import WebhookValidator
from ..types import LinearEvent, LinearIssue, LinearProject, LinearComment
from ....shared.logging.get_logger import get_logger

logger = get_logger(__name__)

@dataclass
class WebhookConfig:
    """Configuration for webhook processor"""
    secret: Optional[str] = None
    validate_signatures: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    rate_limit_per_minute: int = 1000

class WebhookProcessor:
    """
    Linear Webhook Processor with comprehensive event handling:
    - Signature validation
    - Event routing and processing
    - Retry logic with exponential backoff
    - Rate limiting
    - Error handling and recovery
    """
    
    def __init__(self, secret: Optional[str] = None, config: Optional[WebhookConfig] = None):
        self.config = config or WebhookConfig(secret=secret)
        self.validator = WebhookValidator(self.config.secret)
        self.handlers = WebhookHandlers()
        
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._processing_queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: List[asyncio.Task] = []
        self._running = False
        self._rate_limiter = asyncio.Semaphore(self.config.rate_limit_per_minute)
        
        # Statistics
        self._stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "validation_errors": 0,
            "rate_limited": 0,
            "last_processed": None
        }
        
        logger.info("Webhook processor initialized")
    
    async def start(self, num_workers: int = 3) -> None:
        """Start the webhook processor with worker tasks"""
        if self._running:
            return
        
        self._running = True
        
        # Start worker tasks
        for i in range(num_workers):
            task = asyncio.create_task(self._worker())
            self._worker_tasks.append(task)
        
        logger.info(f"Webhook processor started with {num_workers} workers")
    
    async def stop(self) -> None:
        """Stop the webhook processor and cleanup"""
        self._running = False
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        self._worker_tasks.clear()
        logger.info("Webhook processor stopped")
    
    async def _worker(self) -> None:
        """Worker task for processing webhook events"""
        while self._running:
            try:
                # Get event from queue with timeout
                try:
                    event_data = await asyncio.wait_for(
                        self._processing_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                await self._process_event_internal(event_data)
                
                # Mark task as done
                self._processing_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in webhook worker: {e}")
                await asyncio.sleep(1.0)
    
    def validate_signature(self, payload: Dict[str, Any], signature: Optional[str] = None) -> bool:
        """Validate webhook signature"""
        if not self.config.validate_signatures:
            return True
        
        try:
            return self.validator.validate_signature(payload, signature)
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            self._stats["validation_errors"] += 1
            return False
    
    async def process(self, payload: Dict[str, Any], signature: Optional[str] = None) -> bool:
        """Process incoming webhook payload"""
        try:
            # Validate signature
            if not self.validate_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return False
            
            # Add to processing queue
            await self._processing_queue.put({
                "payload": payload,
                "signature": signature,
                "received_at": datetime.utcnow().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            self._stats["failed"] += 1
            return False
    
    async def _process_event_internal(self, event_data: Dict[str, Any]) -> None:
        """Internal event processing with rate limiting and retries"""
        payload = event_data["payload"]
        
        # Apply rate limiting
        async with self._rate_limiter:
            try:
                # Extract event information
                event_type = payload.get("type", "unknown")
                action = payload.get("action", "unknown")
                data = payload.get("data", {})
                
                # Create event object
                event = LinearEvent(
                    type=event_type,
                    action=action,
                    data=data,
                    timestamp=datetime.utcnow(),
                    webhook_id=payload.get("webhookId"),
                    organization_id=payload.get("organizationId")
                )
                
                # Process with retries
                success = await self._process_with_retries(event)
                
                # Update statistics
                self._stats["total_processed"] += 1
                if success:
                    self._stats["successful"] += 1
                else:
                    self._stats["failed"] += 1
                self._stats["last_processed"] = datetime.utcnow().isoformat()
                
                logger.debug(f"Processed webhook event: {event_type}.{action}")
                
            except Exception as e:
                logger.error(f"Error in internal event processing: {e}")
                self._stats["failed"] += 1
    
    async def _process_with_retries(self, event: LinearEvent) -> bool:
        """Process event with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Route and handle the event
                await self._route_event(event)
                return True
                
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Event processing failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Event processing failed after {self.config.max_retries + 1} attempts: {e}")
        
        return False
    
    async def _route_event(self, event: LinearEvent) -> None:
        """Route event to appropriate handlers"""
        event_key = f"{event.type}.{event.action}"
        
        # Call registered handlers
        if event_key in self._event_handlers:
            tasks = []
            for handler in self._event_handlers[event_key]:
                tasks.append(asyncio.create_task(handler(event)))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        # Call built-in handlers
        await self.handlers.handle_event(event)
        
        # Call wildcard handlers
        if "*" in self._event_handlers:
            tasks = []
            for handler in self._event_handlers["*"]:
                tasks.append(asyncio.create_task(handler(event)))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def register_handler(
        self,
        event_type: str,
        handler: Callable[[LinearEvent], Awaitable[None]]
    ) -> None:
        """Register an event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
    
    def unregister_handler(
        self,
        event_type: str,
        handler: Callable[[LinearEvent], Awaitable[None]]
    ) -> None:
        """Unregister an event handler"""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                logger.info(f"Unregistered handler for event type: {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for event type: {event_type}")
    
    def register_issue_handler(self, handler: Callable[[LinearEvent], Awaitable[None]]) -> None:
        """Register handler for all issue events"""
        issue_events = [
            "Issue.create",
            "Issue.update",
            "Issue.delete",
            "Issue.archive",
            "Issue.unarchive"
        ]
        
        for event_type in issue_events:
            self.register_handler(event_type, handler)
    
    def register_project_handler(self, handler: Callable[[LinearEvent], Awaitable[None]]) -> None:
        """Register handler for all project events"""
        project_events = [
            "Project.create",
            "Project.update",
            "Project.delete",
            "Project.archive"
        ]
        
        for event_type in project_events:
            self.register_handler(event_type, handler)
    
    def register_comment_handler(self, handler: Callable[[LinearEvent], Awaitable[None]]) -> None:
        """Register handler for all comment events"""
        comment_events = [
            "Comment.create",
            "Comment.update",
            "Comment.delete"
        ]
        
        for event_type in comment_events:
            self.register_handler(event_type, handler)
    
    def is_healthy(self) -> bool:
        """Check if webhook processor is healthy"""
        return (
            self._running and
            len(self._worker_tasks) > 0 and
            all(not task.done() for task in self._worker_tasks)
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self._stats,
            "queue_size": self._processing_queue.qsize(),
            "workers_active": len([t for t in self._worker_tasks if not t.done()]),
            "is_healthy": self.is_healthy()
        }
    
    def reset_stats(self) -> None:
        """Reset processing statistics"""
        self._stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "validation_errors": 0,
            "rate_limited": 0,
            "last_processed": None
        }
        logger.info("Webhook processor statistics reset")
    
    async def wait_for_queue_empty(self, timeout: Optional[float] = None) -> bool:
        """Wait for processing queue to be empty"""
        try:
            await asyncio.wait_for(self._processing_queue.join(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

