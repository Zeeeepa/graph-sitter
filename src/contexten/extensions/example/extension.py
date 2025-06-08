"""Example extension using unified connection interface.

This module demonstrates how to use the unified connection interface
to create a Contexten extension with multiple connection types.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from ..core import (
    AuthConfig,
    AuthType,
    ConnectionConfig,
    ConnectionError,
    ConnectionEvent,
    ConnectionManager,
    ConnectionStatus,
    ConnectionType,
    EndpointConfig,
    GraphQLConnection,
    HTTPConnection,
    WebSocketConnection,
)

logger = logging.getLogger(__name__)

class ExampleExtension:
    """Example extension implementation."""

    def __init__(self) -> None:
        """Initialize example extension."""
        self.connection_manager = ConnectionManager()
        self._setup_connections()

    def _setup_connections(self) -> None:
        """Setup connection types."""
        # Register connection implementations
        self.connection_manager.register_connection_type(
            ConnectionType.HTTP,
            HTTPConnection
        )
        self.connection_manager.register_connection_type(
            ConnectionType.WEBSOCKET,
            WebSocketConnection
        )
        self.connection_manager.register_connection_type(
            ConnectionType.GRAPHQL,
            GraphQLConnection
        )

        # Add global event handler
        self.connection_manager.add_global_event_handler(
            "connected",
            self._handle_connection
        )
        self.connection_manager.add_global_event_handler(
            "disconnected",
            self._handle_disconnection
        )

        # Add global error handler
        self.connection_manager.add_global_error_handler(
            self._handle_error
        )

    async def initialize(self) -> None:
        """Initialize extension connections."""
        try:
            # Create HTTP connection
            await self.connection_manager.create_connection(
                name="example_http",
                type_=ConnectionType.HTTP,
                auth=AuthConfig(
                    type=AuthType.TOKEN,
                    token="example_token"
                ),
                endpoints=EndpointConfig(
                    base_url="https://api.example.com",
                    paths={
                        "data": "/data",
                        "status": "/status"
                    }
                )
            )

            # Create WebSocket connection
            await self.connection_manager.create_connection(
                name="example_ws",
                type_=ConnectionType.WEBSOCKET,
                auth=AuthConfig(
                    type=AuthType.TOKEN,
                    token="example_token"
                ),
                endpoints=EndpointConfig(
                    base_url="wss://ws.example.com"
                )
            )

            # Create GraphQL connection
            await self.connection_manager.create_connection(
                name="example_graphql",
                type_=ConnectionType.GRAPHQL,
                auth=AuthConfig(
                    type=AuthType.TOKEN,
                    token="example_token"
                ),
                endpoints=EndpointConfig(
                    base_url="https://graphql.example.com"
                )
            )

            # Connect all
            await self.connection_manager.connect_all()

        except Exception as e:
            logger.error(f"Failed to initialize extension: {e}")
            raise

    async def cleanup(self) -> None:
        """Cleanup extension connections."""
        try:
            await self.connection_manager.disconnect_all()
        except Exception as e:
            logger.error(f"Failed to cleanup extension: {e}")
            raise

    async def _handle_connection(self, event: ConnectionEvent) -> None:
        """Handle connection event."""
        logger.info(f"Connection established: {event.source}")

    async def _handle_disconnection(self, event: ConnectionEvent) -> None:
        """Handle disconnection event."""
        logger.info(f"Connection closed: {event.source}")

    async def _handle_error(self, error: ConnectionError) -> None:
        """Handle connection error."""
        logger.error(f"Connection error: {error}")

    async def fetch_data(self) -> Dict[str, Any]:
        """Example method using HTTP connection."""
        connection = self.connection_manager.get_connection("example_http")
        if not connection:
            raise ValueError("HTTP connection not found")

        return await connection.send(
            method="GET",
            path="/data"
        )

    async def subscribe_to_events(self) -> str:
        """Example method using WebSocket connection."""
        connection = self.connection_manager.get_connection("example_ws")
        if not connection:
            raise ValueError("WebSocket connection not found")

        await connection.send(
            method="subscribe",
            path="events",
            data={"type": "all"}
        )

    async def execute_query(self, query: str, variables: Dict[str, Any]) -> Any:
        """Example method using GraphQL connection."""
        connection = self.connection_manager.get_connection("example_graphql")
        if not connection:
            raise ValueError("GraphQL connection not found")

        return await connection.send(
            method="query",
            path=query,
            data=variables
        )

