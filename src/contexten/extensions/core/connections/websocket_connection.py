"""WebSocket connection implementation.

This module provides a standard WebSocket connection implementation
using websockets for asynchronous WebSocket communication.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import WebSocketException

from ..connection import (
    AuthType,
    ConnectionError,
    ConnectionEvent,
    ConnectionStatus,
    ExtensionConnection,
)

logger = logging.getLogger(__name__)

class WebSocketConnection(ExtensionConnection):
    """WebSocket connection implementation."""

    def __init__(self, config):
        """Initialize WebSocket connection."""
        super().__init__(config)
        self._ws: Optional[WebSocketClientProtocol] = None
        self._headers: Dict[str, str] = {}
        self._receive_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
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
        """Establish WebSocket connection."""
        try:
            self.status = ConnectionStatus.CONNECTING
            url = f"{self.config.endpoints.base_url}"

            self._ws = await websockets.connect(
                url,
                extra_headers=self._headers,
                ping_interval=20,
                ping_timeout=10
            )

            self.status = ConnectionStatus.CONNECTED

            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Emit connection event
            await self._handle_event(
                ConnectionEvent(
                    type="connected",
                    source=self.config.name
                )
            )

        except Exception as e:
            error = ConnectionError(
                message=f"Failed to establish WebSocket connection: {e}",
                details={"error": str(e)}
            )
            await self._handle_error(error)
            raise

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._ws:
            try:
                # Cancel background tasks
                if self._receive_task:
                    self._receive_task.cancel()
                if self._heartbeat_task:
                    self._heartbeat_task.cancel()

                await self._ws.close()
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
                    message=f"Failed to close WebSocket connection: {e}",
                    details={"error": str(e)}
                )
                await self._handle_error(error)
                raise

    async def is_connected(self) -> bool:
        """Check if connection is active."""
        return (
            self._ws is not None
            and not self._ws.closed
            and self.status == ConnectionStatus.CONNECTED
        )

    async def send(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """Send WebSocket message.

        Args:
            method: Message type
            path: Message path/topic
            data: Message data
            **kwargs: Additional arguments

        Raises:
            ConnectionError: If send fails
        """
        if not self._ws:
            raise ConnectionError("No active WebSocket connection")

        message = {
            "type": method,
            "path": path,
            "data": data,
            **kwargs
        }

        try:
            await self._ws.send(json.dumps(message))
        except Exception as e:
            error = ConnectionError(
                message=f"Failed to send WebSocket message: {e}",
                details={
                    "error": str(e),
                    "message": message
                }
            )
            await self._handle_error(error)
            raise

    async def _receive_loop(self) -> None:
        """Background task for receiving messages."""
        if not self._ws:
            return

        try:
            while True:
                message = await self._ws.recv()
                try:
                    data = json.loads(message)
                    event_type = data.get("type", "message")
                    await self._handle_event(
                        ConnectionEvent(
                            type=event_type,
                            source=self.config.name,
                            data=data
                        )
                    )
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {message}")

        except asyncio.CancelledError:
            pass
        except WebSocketException as e:
            error = ConnectionError(
                message=f"WebSocket receive error: {e}",
                details={"error": str(e)}
            )
            await self._handle_error(error)
        except Exception as e:
            error = ConnectionError(
                message=f"Unexpected WebSocket error: {e}",
                details={"error": str(e)}
            )
            await self._handle_error(error)

    async def _heartbeat_loop(self) -> None:
        """Background task for connection heartbeat."""
        try:
            while True:
                if not await self.is_connected():
                    await self._handle_error(
                        ConnectionError(
                            message="WebSocket connection lost",
                            details={"reason": "heartbeat_failed"}
                        )
                    )
                    break
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass

