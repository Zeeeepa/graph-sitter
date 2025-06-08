"""Connection manager for Contexten extensions.

This module provides a centralized connection manager for handling
multiple extension connections with unified configuration and error handling.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from .connection import (
    AuthConfig,
    ConnectionConfig,
    ConnectionError,
    ConnectionEvent,
    ConnectionStatus,
    ConnectionType,
    EndpointConfig,
    ExtensionConnection,
)

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Connection manager for extensions."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self._connections: Dict[str, ExtensionConnection] = {}
        self._connection_types: Dict[ConnectionType, Type[ExtensionConnection]] = {}
        self._global_event_handlers: Dict[str, List[Any]] = {}
        self._global_error_handlers: List[Any] = []

    def register_connection_type(
        self,
        type_: ConnectionType,
        connection_class: Type[ExtensionConnection]
    ) -> None:
        """Register connection type.

        Args:
            type_: Connection type
            connection_class: Connection class
        """
        self._connection_types[type_] = connection_class
        logger.info(f"Registered connection type: {type_}")

    async def create_connection(
        self,
        name: str,
        type_: ConnectionType,
        auth: AuthConfig,
        endpoints: EndpointConfig,
        options: Optional[Dict[str, Any]] = None
    ) -> ExtensionConnection:
        """Create new connection.

        Args:
            name: Connection name
            type_: Connection type
            auth: Authentication configuration
            endpoints: Endpoint configuration
            options: Additional options

        Returns:
            Created connection

        Raises:
            ValueError: If connection type not registered
        """
        if type_ not in self._connection_types:
            raise ValueError(f"Connection type not registered: {type_}")

        config = ConnectionConfig(
            type=type_,
            name=name,
            auth=auth,
            endpoints=endpoints,
            options=options
        )

        connection_class = self._connection_types[type_]
        connection = connection_class(config)

        # Add global handlers
        for event_type, handlers in self._global_event_handlers.items():
            for handler in handlers:
                connection.add_event_handler(event_type, handler)

        for handler in self._global_error_handlers:
            connection.add_error_handler(handler)

        self._connections[name] = connection
        logger.info(f"Created connection: {name} ({type_})")

        return connection

    def get_connection(self, name: str) -> Optional[ExtensionConnection]:
        """Get connection by name.

        Args:
            name: Connection name

        Returns:
            Connection if found, None otherwise
        """
        return self._connections.get(name)

    def remove_connection(self, name: str) -> None:
        """Remove connection.

        Args:
            name: Connection name
        """
        if name in self._connections:
            del self._connections[name]
            logger.info(f"Removed connection: {name}")

    async def connect_all(self) -> None:
        """Connect all registered connections."""
        connect_tasks = []
        for connection in self._connections.values():
            connect_tasks.append(connection.connect())

        await asyncio.gather(*connect_tasks)
        logger.info("Connected all connections")

    async def disconnect_all(self) -> None:
        """Disconnect all connections."""
        disconnect_tasks = []
        for connection in self._connections.values():
            disconnect_tasks.append(connection.disconnect())

        await asyncio.gather(*disconnect_tasks)
        logger.info("Disconnected all connections")

    def add_global_event_handler(
        self,
        event_type: str,
        handler: Any
    ) -> None:
        """Add global event handler.

        Args:
            event_type: Event type to handle
            handler: Event handler function
        """
        if event_type not in self._global_event_handlers:
            self._global_event_handlers[event_type] = []
        self._global_event_handlers[event_type].append(handler)

        # Add to existing connections
        for connection in self._connections.values():
            connection.add_event_handler(event_type, handler)

    def remove_global_event_handler(
        self,
        event_type: str,
        handler: Any
    ) -> None:
        """Remove global event handler.

        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._global_event_handlers:
            self._global_event_handlers[event_type].remove(handler)

            # Remove from existing connections
            for connection in self._connections.values():
                connection.remove_event_handler(event_type, handler)

    def add_global_error_handler(self, handler: Any) -> None:
        """Add global error handler.

        Args:
            handler: Error handler function
        """
        self._global_error_handlers.append(handler)

        # Add to existing connections
        for connection in self._connections.values():
            connection.add_error_handler(handler)

    def remove_global_error_handler(self, handler: Any) -> None:
        """Remove global error handler.

        Args:
            handler: Handler to remove
        """
        self._global_error_handlers.remove(handler)

        # Remove from existing connections
        for connection in self._connections.values():
            connection.remove_error_handler(handler)

    async def get_connection_statuses(self) -> Dict[str, ConnectionStatus]:
        """Get status of all connections.

        Returns:
            Dictionary of connection names to statuses
        """
        statuses = {}
        for name, connection in self._connections.items():
            statuses[name] = await connection.get_status()
        return statuses

    async def broadcast_event(
        self,
        event: ConnectionEvent,
        exclude: Optional[List[str]] = None
    ) -> None:
        """Broadcast event to all connections.

        Args:
            event: Event to broadcast
            exclude: List of connection names to exclude
        """
        exclude = exclude or []
        for name, connection in self._connections.items():
            if name not in exclude:
                await connection._handle_event(event)

    async def handle_error(
        self,
        name: str,
        error: ConnectionError
    ) -> None:
        """Handle connection error.

        Args:
            name: Connection name
            error: Error to handle
        """
        connection = self.get_connection(name)
        if connection:
            await connection._handle_error(error)

