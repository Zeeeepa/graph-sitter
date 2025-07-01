"""
Strands Message Processor

Handles message processing and routing in the Strands event loop.
Based on: https://github.com/strands-agents/sdk-python/blob/main/src/strands/event_loop/message_processor.py
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

from ..types.event_loop import Message, MessageHandler, EventLoopConfig, MessagePriority

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics for message processing."""
    total_processed: int = 0
    total_failed: int = 0
    average_processing_time: float = 0.0
    last_processed_time: Optional[float] = None
    processing_times: List[float] = None
    
    def __post_init__(self):
        if self.processing_times is None:
            self.processing_times = []


class MessageProcessor:
    """Advanced message processor with routing and filtering capabilities."""
    
    def __init__(self, config: EventLoopConfig):
        """Initialize the message processor.
        
        Args:
            config: Event loop configuration
        """
        self.config = config
        self.stats = ProcessingStats()
        self.handlers: Dict[str, MessageHandler] = {}
        self.middleware: List[Callable[[Message], Message]] = []
        self.filters: List[Callable[[Message], bool]] = []
        
        # Priority queues for different message priorities
        self.priority_queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in MessagePriority
        }
        
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        
        logger.info("Initialized message processor")
    
    async def start(self):
        """Start the message processor."""
        if self._running:
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_messages())
        logger.info("Started message processor")
    
    async def stop(self):
        """Stop the message processor."""
        if not self._running:
            return
        
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped message processor")
    
    async def process_message(self, message: Message) -> bool:
        """Process a single message.
        
        Args:
            message: Message to process
            
        Returns:
            True if processing was successful
        """
        start_time = time.time()
        
        try:
            # Apply filters
            if not self._should_process_message(message):
                logger.debug(f"Message filtered out: {message.id}")
                return False
            
            # Apply middleware
            processed_message = self._apply_middleware(message)
            
            # Find and execute handlers
            handlers = self._find_handlers(processed_message)
            
            if not handlers:
                logger.warning(f"No handlers found for message type: {processed_message.type}")
                return False
            
            # Execute handlers
            success = True
            for handler in handlers:
                try:
                    await self._execute_handler(handler, processed_message)
                except Exception as e:
                    logger.error(f"Handler {handler.handler_id} failed: {e}")
                    success = False
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(processing_time, success)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to process message {message.id}: {e}")
            self._update_stats(time.time() - start_time, False)
            return False
    
    def add_handler(self, handler: MessageHandler):
        """Add a message handler.
        
        Args:
            handler: Handler to add
        """
        self.handlers[handler.handler_id] = handler
        logger.info(f"Added handler: {handler.handler_id}")
    
    def remove_handler(self, handler_id: str):
        """Remove a message handler.
        
        Args:
            handler_id: ID of handler to remove
        """
        if handler_id in self.handlers:
            del self.handlers[handler_id]
            logger.info(f"Removed handler: {handler_id}")
    
    def add_middleware(self, middleware_func: Callable[[Message], Message]):
        """Add middleware function.
        
        Args:
            middleware_func: Middleware function that transforms messages
        """
        self.middleware.append(middleware_func)
        logger.info("Added middleware function")
    
    def add_filter(self, filter_func: Callable[[Message], bool]):
        """Add filter function.
        
        Args:
            filter_func: Filter function that returns True if message should be processed
        """
        self.filters.append(filter_func)
        logger.info("Added filter function")
    
    async def queue_message(self, message: Message):
        """Queue a message for processing.
        
        Args:
            message: Message to queue
        """
        priority_queue = self.priority_queues[message.priority]
        await priority_queue.put(message)
        logger.debug(f"Queued message: {message.id} (priority: {message.priority.name})")
    
    async def _process_messages(self):
        """Main message processing loop."""
        logger.debug("Starting message processing loop")
        
        while self._running:
            try:
                # Process messages by priority (highest first)
                message = await self._get_next_message()
                
                if message:
                    await self.process_message(message)
                else:
                    # No messages available, wait a bit
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(1)  # Prevent tight error loop
    
    async def _get_next_message(self) -> Optional[Message]:
        """Get the next message to process based on priority.
        
        Returns:
            Next message to process or None if no messages available
        """
        # Check queues in priority order (highest to lowest)
        for priority in sorted(MessagePriority, key=lambda p: p.value, reverse=True):
            queue = self.priority_queues[priority]
            
            try:
                message = queue.get_nowait()
                return message
            except asyncio.QueueEmpty:
                continue
        
        return None
    
    def _should_process_message(self, message: Message) -> bool:
        """Check if message should be processed based on filters.
        
        Args:
            message: Message to check
            
        Returns:
            True if message should be processed
        """
        for filter_func in self.filters:
            try:
                if not filter_func(message):
                    return False
            except Exception as e:
                logger.error(f"Filter function error: {e}")
                return False
        
        return True
    
    def _apply_middleware(self, message: Message) -> Message:
        """Apply middleware transformations to message.
        
        Args:
            message: Original message
            
        Returns:
            Transformed message
        """
        processed_message = message
        
        for middleware_func in self.middleware:
            try:
                processed_message = middleware_func(processed_message)
            except Exception as e:
                logger.error(f"Middleware function error: {e}")
                # Continue with original message if middleware fails
                break
        
        return processed_message
    
    def _find_handlers(self, message: Message) -> List[MessageHandler]:
        """Find handlers for a message.
        
        Args:
            message: Message to find handlers for
            
        Returns:
            List of matching handlers
        """
        matching_handlers = []
        
        for handler in self.handlers.values():
            if (handler.enabled and 
                message.type in handler.message_types):
                matching_handlers.append(handler)
        
        # Sort by priority (higher priority first)
        matching_handlers.sort(key=lambda h: h.priority, reverse=True)
        
        return matching_handlers
    
    async def _execute_handler(self, handler: MessageHandler, message: Message):
        """Execute a message handler.
        
        Args:
            handler: Handler to execute
            message: Message to process
        """
        if asyncio.iscoroutinefunction(handler.handler_func):
            await handler.handler_func(message)
        else:
            # Run synchronous handler in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, handler.handler_func, message)
    
    def _update_stats(self, processing_time: float, success: bool):
        """Update processing statistics.
        
        Args:
            processing_time: Time taken to process message
            success: Whether processing was successful
        """
        if success:
            self.stats.total_processed += 1
        else:
            self.stats.total_failed += 1
        
        self.stats.last_processed_time = time.time()
        self.stats.processing_times.append(processing_time)
        
        # Keep only last 1000 processing times
        if len(self.stats.processing_times) > 1000:
            self.stats.processing_times = self.stats.processing_times[-1000:]
        
        # Update average processing time
        if self.stats.processing_times:
            self.stats.average_processing_time = sum(self.stats.processing_times) / len(self.stats.processing_times)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Processing statistics
        """
        return {
            "total_processed": self.stats.total_processed,
            "total_failed": self.stats.total_failed,
            "success_rate": (
                self.stats.total_processed / (self.stats.total_processed + self.stats.total_failed)
                if (self.stats.total_processed + self.stats.total_failed) > 0 else 0
            ),
            "average_processing_time": self.stats.average_processing_time,
            "last_processed_time": self.stats.last_processed_time,
            "handlers_count": len(self.handlers),
            "middleware_count": len(self.middleware),
            "filters_count": len(self.filters),
            "queue_sizes": {
                priority.name: queue.qsize() 
                for priority, queue in self.priority_queues.items()
            }
        }

