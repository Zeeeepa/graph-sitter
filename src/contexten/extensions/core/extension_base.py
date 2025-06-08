"""Base extension interface for the unified extension system.

This module provides the base classes and interfaces that all extensions
must implement to participate in the unified extension ecosystem.
"""

import abc
import asyncio
import enum
import logging
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .capabilities import ExtensionCapability
from .connection import ExtensionConnection

logger = logging.getLogger(__name__)


class ExtensionStatus(str, enum.Enum):
    """Extension status enumeration."""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ExtensionMetadata(BaseModel):
    """Extension metadata model."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    capabilities: List[ExtensionCapability] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    min_python_version: str = "3.8"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExtensionConfig(BaseModel):
    """Base extension configuration."""
    enabled: bool = True
    log_level: str = "INFO"
    health_check_interval: int = 60  # seconds
    retry_count: int = 3
    retry_delay: int = 1  # seconds
    timeout: int = 30  # seconds
    custom_config: Dict[str, Any] = Field(default_factory=dict)


class ExtensionEvent(BaseModel):
    """Extension event model."""
    type: str
    source: str
    target: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class ExtensionMessage(BaseModel):
    """Extension message model for inter-extension communication."""
    id: str
    type: str
    source: str
    target: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds


class ExtensionResponse(BaseModel):
    """Extension response model."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExtensionBase(abc.ABC):
    """Base class for all extensions."""

    def __init__(self, config: Optional[ExtensionConfig] = None):
        """Initialize extension.
        
        Args:
            config: Extension configuration
        """
        self.config = config or ExtensionConfig()
        self.metadata = self._create_metadata()
        self.status = ExtensionStatus.REGISTERED
        self._connections: Dict[str, ExtensionConnection] = {}
        self._event_handlers: Dict[str, List[Any]] = {}
        self._message_handlers: Dict[str, Any] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._last_health_check: Optional[datetime] = None
        self._startup_time: Optional[datetime] = None
        self._logger = logging.getLogger(f"{__name__}.{self.metadata.name}")

    @abc.abstractmethod
    def _create_metadata(self) -> ExtensionMetadata:
        """Create extension metadata.
        
        Returns:
            Extension metadata
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def initialize(self) -> bool:
        """Initialize the extension.
        
        Returns:
            True if initialization successful, False otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def start(self) -> bool:
        """Start the extension.
        
        Returns:
            True if start successful, False otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def stop(self) -> bool:
        """Stop the extension.
        
        Returns:
            True if stop successful, False otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Perform health check.
        
        Returns:
            True if healthy, False otherwise
        """
        raise NotImplementedError

    async def get_status(self) -> ExtensionStatus:
        """Get current extension status.
        
        Returns:
            Current status
        """
        return self.status

    async def get_metadata(self) -> ExtensionMetadata:
        """Get extension metadata.
        
        Returns:
            Extension metadata
        """
        return self.metadata

    async def get_config(self) -> ExtensionConfig:
        """Get extension configuration.
        
        Returns:
            Extension configuration
        """
        return self.config

    async def update_config(self, config: ExtensionConfig) -> bool:
        """Update extension configuration.
        
        Args:
            config: New configuration
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            old_config = self.config
            self.config = config
            
            # Restart health check if interval changed
            if (old_config.health_check_interval != config.health_check_interval and
                self._health_check_task):
                self._health_check_task.cancel()
                await self._start_health_check()
                
            return True
        except Exception as e:
            self._logger.error(f"Failed to update config: {e}")
            return False

    async def get_connections(self) -> Dict[str, ExtensionConnection]:
        """Get extension connections.
        
        Returns:
            Dictionary of connection names to connections
        """
        return self._connections.copy()

    def add_connection(self, name: str, connection: ExtensionConnection) -> None:
        """Add connection to extension.
        
        Args:
            name: Connection name
            connection: Connection instance
        """
        self._connections[name] = connection
        self._logger.info(f"Added connection: {name}")

    def remove_connection(self, name: str) -> None:
        """Remove connection from extension.
        
        Args:
            name: Connection name
        """
        if name in self._connections:
            del self._connections[name]
            self._logger.info(f"Removed connection: {name}")

    def add_event_handler(self, event_type: str, handler: Any) -> None:
        """Add event handler.
        
        Args:
            event_type: Event type to handle
            handler: Event handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: Any) -> None:
        """Remove event handler.
        
        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._event_handlers:
            self._event_handlers[event_type].remove(handler)

    def add_message_handler(self, message_type: str, handler: Any) -> None:
        """Add message handler.
        
        Args:
            message_type: Message type to handle
            handler: Message handler function
        """
        self._message_handlers[message_type] = handler

    def remove_message_handler(self, message_type: str) -> None:
        """Remove message handler.
        
        Args:
            message_type: Message type
        """
        if message_type in self._message_handlers:
            del self._message_handlers[message_type]

    async def handle_event(self, event: ExtensionEvent) -> None:
        """Handle incoming event.
        
        Args:
            event: Event to handle
        """
        handlers = self._event_handlers.get(event.type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self._logger.error(f"Error in event handler for {event.type}: {e}")

    async def handle_message(self, message: ExtensionMessage) -> ExtensionResponse:
        """Handle incoming message.
        
        Args:
            message: Message to handle
            
        Returns:
            Response to the message
        """
        handler = self._message_handlers.get(message.type)
        if not handler:
            return ExtensionResponse(
                success=False,
                error=f"No handler for message type: {message.type}",
                error_code="NO_HANDLER"
            )

        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(message)
            else:
                result = handler(message)
                
            return ExtensionResponse(
                success=True,
                data=result
            )
        except Exception as e:
            self._logger.error(f"Error in message handler for {message.type}: {e}")
            return ExtensionResponse(
                success=False,
                error=str(e),
                error_code="HANDLER_ERROR"
            )

    async def send_message(
        self,
        target: str,
        message_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> ExtensionResponse:
        """Send message to another extension.
        
        Args:
            target: Target extension name
            message_type: Message type
            payload: Message payload
            correlation_id: Optional correlation ID
            
        Returns:
            Response from target extension
        """
        # This would be implemented by the registry/event bus
        # For now, return a placeholder response
        return ExtensionResponse(
            success=False,
            error="Message sending not implemented",
            error_code="NOT_IMPLEMENTED"
        )

    async def emit_event(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None
    ) -> None:
        """Emit event.
        
        Args:
            event_type: Event type
            data: Event data
            target: Optional target extension
        """
        event = ExtensionEvent(
            type=event_type,
            source=self.metadata.name,
            target=target,
            data=data
        )
        
        # This would be implemented by the registry/event bus
        # For now, just log the event
        self._logger.info(f"Emitted event: {event_type}")

    async def _start_health_check(self) -> None:
        """Start periodic health check."""
        if self.config.health_check_interval > 0:
            self._health_check_task = asyncio.create_task(
                self._health_check_loop()
            )

    async def _health_check_loop(self) -> None:
        """Health check loop."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                is_healthy = await self.health_check()
                self._last_health_check = datetime.now(UTC)
                
                if not is_healthy:
                    self._logger.warning("Health check failed")
                    await self.emit_event(
                        "extension.health.failed",
                        {"extension": self.metadata.name}
                    )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in health check loop: {e}")

    async def _lifecycle_start(self) -> bool:
        """Internal start method with lifecycle management."""
        try:
            self.status = ExtensionStatus.INITIALIZING
            
            # Initialize extension
            if not await self.initialize():
                self.status = ExtensionStatus.ERROR
                return False
                
            # Start extension
            if not await self.start():
                self.status = ExtensionStatus.ERROR
                return False
                
            self.status = ExtensionStatus.RUNNING
            self._startup_time = datetime.now(UTC)
            
            # Start health check
            await self._start_health_check()
            
            # Emit start event
            await self.emit_event("extension.started")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to start extension: {e}")
            self.status = ExtensionStatus.ERROR
            return False

    async def _lifecycle_stop(self) -> bool:
        """Internal stop method with lifecycle management."""
        try:
            # Cancel health check
            if self._health_check_task:
                self._health_check_task.cancel()
                self._health_check_task = None
                
            # Stop extension
            if not await self.stop():
                self.status = ExtensionStatus.ERROR
                return False
                
            self.status = ExtensionStatus.STOPPED
            
            # Emit stop event
            await self.emit_event("extension.stopped")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to stop extension: {e}")
            self.status = ExtensionStatus.ERROR
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get extension statistics.
        
        Returns:
            Dictionary of extension statistics
        """
        uptime = None
        if self._startup_time:
            uptime = (datetime.now(UTC) - self._startup_time).total_seconds()
            
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "connection_count": len(self._connections),
            "event_handler_count": sum(len(handlers) for handlers in self._event_handlers.values()),
            "message_handler_count": len(self._message_handlers)
        }


class SimpleExtension(ExtensionBase):
    """Simple extension implementation for basic use cases."""

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        capabilities: Optional[List[ExtensionCapability]] = None,
        config: Optional[ExtensionConfig] = None
    ):
        """Initialize simple extension.
        
        Args:
            name: Extension name
            version: Extension version
            description: Extension description
            capabilities: Extension capabilities
            config: Extension configuration
        """
        self._name = name
        self._version = version
        self._description = description
        self._capabilities = capabilities or []
        super().__init__(config)

    def _create_metadata(self) -> ExtensionMetadata:
        """Create extension metadata."""
        return ExtensionMetadata(
            name=self._name,
            version=self._version,
            description=self._description,
            capabilities=self._capabilities
        )

    async def initialize(self) -> bool:
        """Initialize the extension."""
        self._logger.info(f"Initializing extension: {self.metadata.name}")
        return True

    async def start(self) -> bool:
        """Start the extension."""
        self._logger.info(f"Starting extension: {self.metadata.name}")
        return True

    async def stop(self) -> bool:
        """Stop the extension."""
        self._logger.info(f"Stopping extension: {self.metadata.name}")
        return True

    async def health_check(self) -> bool:
        """Perform health check."""
        return self.status == ExtensionStatus.RUNNING

