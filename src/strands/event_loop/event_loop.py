"""
Strands Event Loop

Core event loop implementation for the Strands agent framework.
Based on: https://github.com/strands-agents/sdk-python/blob/main/src/strands/event_loop/event_loop.py
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from ..types.event_loop import (
    EventLoopConfig, EventLoopStatus, Message, MessageHandler, 
    EventLoopState, MessagePriority, HealthCheck
)
from .message_processor import MessageProcessor
from .error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class StrandsEventLoop:
    """High-performance event loop for Strands agents."""
    
    def __init__(self, config: Optional[EventLoopConfig] = None):
        """Initialize the event loop.
        
        Args:
            config: Optional event loop configuration
        """
        self.config = config or EventLoopConfig()
        self.state = EventLoopState(config=self.config)
        
        # Core components
        self.message_processor = MessageProcessor(self.config)
        self.error_handler = ErrorHandler(self.config)
        
        # Async components
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()
        
        # Heartbeat and health monitoring
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        logger.info("Initialized Strands event loop")
    
    async def start(self):
        """Start the event loop."""
        if self.state.status != EventLoopStatus.STOPPED:
            raise RuntimeError(f"Event loop is already {self.state.status.value}")
        
        logger.info("Starting Strands event loop")
        self.state.status = EventLoopStatus.STARTING
        self.state.start_time = time.time()
        
        try:
            # Start core tasks
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            if self.config.enable_health_checks:
                self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            # Start message processing
            await self.message_processor.start()
            
            self.state.status = EventLoopStatus.RUNNING
            logger.info("Strands event loop started successfully")
            
            # Main event loop
            await self._main_loop()
            
        except Exception as e:
            self.state.status = EventLoopStatus.ERROR
            self.state.add_error(f"Failed to start event loop: {e}")
            logger.error(f"Failed to start event loop: {e}")
            raise
    
    async def stop(self, timeout: Optional[float] = None):
        """Stop the event loop.
        
        Args:
            timeout: Optional timeout for graceful shutdown
        """
        if self.state.status == EventLoopStatus.STOPPED:
            return
        
        timeout = timeout or self.config.graceful_shutdown_timeout
        logger.info(f"Stopping Strands event loop (timeout: {timeout}s)")
        
        self.state.status = EventLoopStatus.STOPPING
        self._shutdown_event.set()
        
        try:
            # Cancel running tasks
            for task_id, task in self._running_tasks.items():
                if not task.done():
                    task.cancel()
                    logger.debug(f"Cancelled task: {task_id}")
            
            # Wait for tasks to complete
            if self._running_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*self._running_tasks.values(), return_exceptions=True),
                    timeout=timeout
                )
            
            # Stop core components
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            if self._health_check_task:
                self._health_check_task.cancel()
            
            await self.message_processor.stop()
            
            # Shutdown executor
            self._executor.shutdown(wait=True)
            
            self.state.status = EventLoopStatus.STOPPED
            logger.info("Strands event loop stopped successfully")
            
        except asyncio.TimeoutError:
            logger.warning(f"Graceful shutdown timed out after {timeout}s")
            self.state.status = EventLoopStatus.ERROR
        except Exception as e:
            self.state.status = EventLoopStatus.ERROR
            self.state.add_error(f"Error during shutdown: {e}")
            logger.error(f"Error during shutdown: {e}")
    
    async def send_message(self, message: Message) -> str:
        """Send a message to the event loop.
        
        Args:
            message: Message to send
            
        Returns:
            Message ID
        """
        if self.state.status != EventLoopStatus.RUNNING:
            raise RuntimeError(f"Event loop is not running (status: {self.state.status.value})")
        
        try:
            await self._message_queue.put(message)
            self.state.metrics.messages_queued += 1
            logger.debug(f"Queued message: {message.id} ({message.type})")
            return message.id
        except asyncio.QueueFull:
            self.state.add_error("Message queue is full")
            raise RuntimeError("Message queue is full")
    
    def register_handler(self, handler: MessageHandler):
        """Register a message handler.
        
        Args:
            handler: Message handler to register
        """
        self.state.handlers[handler.handler_id] = handler
        self.state.metrics.handlers_registered = len(self.state.handlers)
        logger.info(f"Registered handler: {handler.handler_id} for types: {handler.message_types}")
    
    def unregister_handler(self, handler_id: str):
        """Unregister a message handler.
        
        Args:
            handler_id: ID of handler to unregister
        """
        if handler_id in self.state.handlers:
            del self.state.handlers[handler_id]
            self.state.metrics.handlers_registered = len(self.state.handlers)
            logger.info(f"Unregistered handler: {handler_id}")
    
    def add_health_check(self, health_check: HealthCheck):
        """Add a health check.
        
        Args:
            health_check: Health check to add
        """
        self.state.health_checks[health_check.name] = health_check
        logger.info(f"Added health check: {health_check.name}")
    
    async def _main_loop(self):
        """Main event loop."""
        logger.debug("Starting main event loop")
        
        while not self._shutdown_event.is_set():
            try:
                # Process messages with timeout
                try:
                    message = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=1.0  # Check shutdown event every second
                    )
                    
                    # Process message
                    task_id = str(uuid.uuid4())
                    task = asyncio.create_task(self._process_message(message))
                    self._running_tasks[task_id] = task
                    
                    # Clean up completed tasks
                    self._cleanup_completed_tasks()
                    
                except asyncio.TimeoutError:
                    continue  # Check shutdown event
                    
            except Exception as e:
                self.state.add_error(f"Error in main loop: {e}")
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(1)  # Prevent tight error loop
    
    async def _process_message(self, message: Message):
        """Process a single message.
        
        Args:
            message: Message to process
        """
        start_time = time.time()
        
        try:
            # Find handlers for this message type
            handlers = [
                h for h in self.state.handlers.values()
                if message.type in h.message_types and h.enabled
            ]
            
            if not handlers:
                logger.warning(f"No handlers found for message type: {message.type}")
                return
            
            # Process with each handler
            for handler in handlers:
                try:
                    await self._execute_handler(handler, message)
                except Exception as e:
                    await self.error_handler.handle_error(e, message, handler)
            
            self.state.metrics.messages_processed += 1
            
        except Exception as e:
            self.state.metrics.messages_failed += 1
            self.state.add_error(f"Failed to process message {message.id}: {e}")
            logger.error(f"Failed to process message {message.id}: {e}")
        
        finally:
            # Update metrics
            processing_time = time.time() - start_time
            self._update_processing_time(processing_time)
    
    async def _execute_handler(self, handler: MessageHandler, message: Message):
        """Execute a message handler.
        
        Args:
            handler: Handler to execute
            message: Message to process
        """
        if asyncio.iscoroutinefunction(handler.handler_func):
            await handler.handler_func(message)
        else:
            # Run sync handler in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, handler.handler_func, message)
    
    async def _heartbeat_loop(self):
        """Heartbeat loop for monitoring."""
        while not self._shutdown_event.is_set():
            try:
                self.state.metrics.last_heartbeat = time.time()
                self.state.metrics.uptime = time.time() - (self.state.start_time or 0)
                
                logger.debug(f"Heartbeat - uptime: {self.state.metrics.uptime:.1f}s")
                
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(1)
    
    async def _health_check_loop(self):
        """Health check loop."""
        while not self._shutdown_event.is_set():
            try:
                for health_check in self.state.health_checks.values():
                    if not health_check.enabled:
                        continue
                    
                    try:
                        result = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                self._executor, health_check.check_func
                            ),
                            timeout=health_check.timeout
                        )
                        
                        health_check.last_check = time.time()
                        health_check.last_result = result
                        
                        if not result:
                            logger.warning(f"Health check failed: {health_check.name}")
                        
                    except Exception as e:
                        logger.error(f"Health check error ({health_check.name}): {e}")
                        health_check.last_result = False
                
                await asyncio.sleep(60)  # Run health checks every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(1)
    
    def _cleanup_completed_tasks(self):
        """Clean up completed tasks."""
        completed_tasks = [
            task_id for task_id, task in self._running_tasks.items()
            if task.done()
        ]
        
        for task_id in completed_tasks:
            del self._running_tasks[task_id]
    
    def _update_processing_time(self, processing_time: float):
        """Update average processing time metric.
        
        Args:
            processing_time: Time taken to process message
        """
        current_avg = self.state.metrics.average_processing_time
        processed_count = self.state.metrics.messages_processed
        
        # Calculate new average
        if processed_count == 1:
            self.state.metrics.average_processing_time = processing_time
        else:
            self.state.metrics.average_processing_time = (
                (current_avg * (processed_count - 1) + processing_time) / processed_count
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the event loop.
        
        Returns:
            Status information
        """
        return self.state.get_status_summary()

