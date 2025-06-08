"""GraphQL connection implementation.

This module provides a standard GraphQL connection implementation
using gql for asynchronous GraphQL operations.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Union

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import WebsocketsTransport

from ..connection import (
    AuthType,
    ConnectionError,
    ConnectionEvent,
    ConnectionStatus,
    ExtensionConnection,
)

logger = logging.getLogger(__name__)

class GraphQLConnection(ExtensionConnection):
    """GraphQL connection implementation."""

    def __init__(self, config):
        """Initialize GraphQL connection."""
        super().__init__(config)
        self._client: Optional[Client] = None
        self._headers: Dict[str, str] = {}
        self._subscriptions: Dict[str, asyncio.Task] = {}
        self._setup_auth()

    def _setup_auth(self) -> None:
        """Setup authentication headers."""
        auth = self.config.auth
        if auth.type == AuthType.TOKEN:
            self._headers["Authorization"] = f"Bearer {auth.token}"
        elif auth.type == AuthType.API_KEY:
            self._headers["X-API-Key"] = auth.api_key
        elif auth.type == AuthType.OAUTH:
            # OAuth setup would go here
            pass
        elif auth.type == AuthType.CUSTOM:
            # Custom auth setup
            if auth.custom_config:
                self._headers.update(auth.custom_config.get("headers", {}))

    async def connect(self) -> None:
        """Establish GraphQL connection."""
        try:
            self.status = ConnectionStatus.CONNECTING
            url = self.config.endpoints.base_url

            # Setup transport based on URL scheme
            if url.startswith("ws"):
                transport = WebsocketsTransport(
                    url=url,
                    headers=self._headers,
                    keep_alive_timeout=30
                )
            else:
                transport = AIOHTTPTransport(
                    url=url,
                    headers=self._headers,
                    timeout=self.config.endpoints.timeout
                )

            self._client = Client(
                transport=transport,
                fetch_schema_from_transport=True
            )

            self.status = ConnectionStatus.CONNECTED

            # Emit connection event
            await self._handle_event(
                ConnectionEvent(
                    type="connected",
                    source=self.config.name
                )
            )

        except Exception as e:
            error = ConnectionError(
                message=f"Failed to establish GraphQL connection: {e}",
                details={"error": str(e)}
            )
            await self._handle_error(error)
            raise

    async def disconnect(self) -> None:
        """Close GraphQL connection."""
        if self._client:
            try:
                # Cancel all subscriptions
                for task in self._subscriptions.values():
                    task.cancel()
                self._subscriptions.clear()

                # Close transport
                await self._client.transport.close()
                self.status = ConnectionStatus.DISCONNECTED

                # Emit disconnection event
                await self._handle_event(
                    ConnectionEvent(
                        type="disconnected",
                        source=self.config.name
                    )
                )

            except Exception as e:
                error = ConnectionError(
                    message=f"Failed to close GraphQL connection: {e}",
                    details={"error": str(e)}
                )
                await self._handle_error(error)
                raise

    async def is_connected(self) -> bool:
        """Check if connection is active."""
        return (
            self._client is not None
            and self.status == ConnectionStatus.CONNECTED
        )

    async def send(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """Execute GraphQL operation.

        Args:
            method: Operation type (query/mutation/subscription)
            path: GraphQL operation
            data: Operation variables
            **kwargs: Additional arguments

        Returns:
            Operation result

        Raises:
            ConnectionError: If operation fails
        """
        if not self._client:
            raise ConnectionError("No active GraphQL connection")

        try:
            # Parse operation
            operation = gql(path)

            if method.lower() == "subscription":
                # Handle subscription
                subscription_id = kwargs.get("subscription_id", str(len(self._subscriptions)))
                task = asyncio.create_task(
                    self._handle_subscription(
                        subscription_id,
                        operation,
                        data
                    )
                )
                self._subscriptions[subscription_id] = task
                return subscription_id
            else:
                # Execute query/mutation
                result = await self._client.execute(
                    operation,
                    variable_values=data
                )
                return result

        except Exception as e:
            error = ConnectionError(
                message=f"GraphQL operation failed: {e}",
                details={
                    "error": str(e),
                    "operation": path,
                    "variables": data
                }
            )
            await self._handle_error(error)
            raise

    async def _handle_subscription(
        self,
        subscription_id: str,
        operation: Any,
        variables: Optional[Dict[str, Any]] = None
    ) -> None:
        """Handle GraphQL subscription.

        Args:
            subscription_id: Subscription identifier
            operation: GraphQL operation
            variables: Operation variables
        """
        try:
            async for result in self._client.subscribe(
                operation,
                variable_values=variables
            ):
                await self._handle_event(
                    ConnectionEvent(
                        type="subscription",
                        source=self.config.name,
                        data={
                            "subscription_id": subscription_id,
                            "result": result
                        }
                    )
                )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            error = ConnectionError(
                message=f"GraphQL subscription error: {e}",
                details={
                    "error": str(e),
                    "subscription_id": subscription_id
                }
            )
            await self._handle_error(error)

    def cancel_subscription(self, subscription_id: str) -> None:
        """Cancel GraphQL subscription.

        Args:
            subscription_id: Subscription to cancel
        """
        if subscription_id in self._subscriptions:
            self._subscriptions[subscription_id].cancel()
            del self._subscriptions[subscription_id]

