"""Core connection interface for Contexten extensions.

This module provides the base connection interface and types that all
extensions should implement for standardized connection management.
"""

import abc
import asyncio
import enum
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ConnectionType(str, enum.Enum):
    """Connection type enumeration."""
    HTTP = "http"
    WEBSOCKET = "websocket"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    CUSTOM = "custom"

class ConnectionStatus(str, enum.Enum):
    """Connection status enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

class AuthType(str, enum.Enum):
    """Authentication type enumeration."""
    NONE = "none"
    TOKEN = "token"
    OAUTH = "oauth"
    API_KEY = "api_key"
    CUSTOM = "custom"

class AuthConfig(BaseModel):
    """Authentication configuration."""
    type: AuthType = AuthType.NONE
    token: Optional[str] = None
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    oauth_config: Optional[Dict[str, Any]] = None
    custom_config: Optional[Dict[str, Any]] = None

class EndpointConfig(BaseModel):
    """Endpoint configuration."""
    base_url: str
    paths: Dict[str, str] = Field(default_factory=dict)
    timeout: int = 30
    retry_count: int = 3
    retry_delay: int = 1

class ConnectionConfig(BaseModel):
    """Connection configuration."""
    type: ConnectionType
    name: str
    auth: AuthConfig
    endpoints: EndpointConfig
    options: Optional[Dict[str, Any]] = None

class ConnectionError(Exception):
    """Base connection error."""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now(UTC)

class ConnectionEvent(BaseModel):
    """Connection event model."""
    type: str
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data: Optional[Dict[str, Any]] = None

T = TypeVar("T")

class ExtensionConnection(abc.ABC):
    """Base connection interface for extensions."""

    def __init__(self, config: ConnectionConfig) -> None:
        """Initialize connection.

        Args:
            config: Connection configuration
        """
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self._event_handlers: Dict[str, List[Any]] = {}
        self._error_handlers: List[Any] = []
        self._last_error: Optional[ConnectionError] = None
        self._reconnect_task: Optional[asyncio.Task] = None

    @abc.abstractmethod
    async def connect(self) -> None:
        """Establish connection."""
        raise NotImplementedError

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        raise NotImplementedError

    @abc.abstractmethod
    async def is_connected(self) -> bool:
        """Check if connection is active."""
        raise NotImplementedError

    @abc.abstractmethod
    async def send(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """Send request through connection.

        Args:
            method: HTTP method or operation name
            path: Endpoint path or operation path
            data: Request data
            **kwargs: Additional arguments

        Returns:
            Response data
        """
        raise NotImplementedError

    async def get_status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self.status

    def add_event_handler(
        self,
        event_type: str,
        handler: Any
    ) -> None:
        """Add event handler.

        Args:
            event_type: Event type to handle
            handler: Event handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def remove_event_handler(
        self,
        event_type: str,
        handler: Any
    ) -> None:
        """Remove event handler.

        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._event_handlers:
            self._event_handlers[event_type].remove(handler)

    def add_error_handler(self, handler: Any) -> None:
        """Add error handler.

        Args:
            handler: Error handler function
        """
        self._error_handlers.append(handler)

    def remove_error_handler(self, handler: Any) -> None:
        """Remove error handler.

        Args:
            handler: Handler to remove
        """
        self._error_handlers.remove(handler)

    async def _handle_event(self, event: ConnectionEvent) -> None:
        """Handle connection event.

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
                logger.error(f"Error in event handler: {e}")

    async def _handle_error(self, error: ConnectionError) -> None:
        """Handle connection error.

        Args:
            error: Error to handle
        """
        self._last_error = error
        self.status = ConnectionStatus.ERROR

        for handler in self._error_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error)
                else:
                    handler(error)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")

        # Start reconnection if appropriate
        if not self._reconnect_task:
            self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Attempt to reconnect."""
        try:
            self.status = ConnectionStatus.RECONNECTING
            await self.connect()
            self._reconnect_task = None
        except Exception as e:
            logger.error(f"Failed to reconnect: {e}")
            # Schedule next reconnection attempt
            await asyncio.sleep(self.config.endpoints.retry_delay)
            self._reconnect_task = asyncio.create_task(self._reconnect())

