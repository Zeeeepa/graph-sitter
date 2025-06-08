"""HTTP connection implementation.

This module provides a standard HTTP connection implementation
using aiohttp for asynchronous HTTP requests.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import ClientTimeout

from ..connection import (
    AuthType,
    ConnectionError,
    ConnectionEvent,
    ConnectionStatus,
    ExtensionConnection,
)

logger = logging.getLogger(__name__)

class HTTPConnection(ExtensionConnection):
    """HTTP connection implementation."""

    def __init__(self, config):
        """Initialize HTTP connection."""
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        self._headers: Dict[str, str] = {}
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
        """Establish HTTP connection."""
        try:
            self.status = ConnectionStatus.CONNECTING
            timeout = ClientTimeout(total=self.config.endpoints.timeout)
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=timeout
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
                message=f"Failed to establish HTTP connection: {e}",
                details={"error": str(e)}
            )
            await self._handle_error(error)
            raise

    async def disconnect(self) -> None:
        """Close HTTP connection."""
        if self._session:
            try:
                await self._session.close()
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
                    message=f"Failed to close HTTP connection: {e}",
                    details={"error": str(e)}
                )
                await self._handle_error(error)
                raise

    async def is_connected(self) -> bool:
        """Check if connection is active."""
        return (
            self._session is not None
            and not self._session.closed
            and self.status == ConnectionStatus.CONNECTED
        )

    async def send(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """Send HTTP request.

        Args:
            method: HTTP method
            path: Endpoint path
            data: Request data
            **kwargs: Additional arguments

        Returns:
            Response data

        Raises:
            ConnectionError: If request fails
        """
        if not self._session:
            raise ConnectionError("No active HTTP session")

        url = f"{self.config.endpoints.base_url}{path}"
        method = method.upper()

        for attempt in range(self.config.endpoints.retry_count + 1):
            try:
                async with self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    **kwargs
                ) as response:
                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientError as e:
                if attempt == self.config.endpoints.retry_count:
                    error = ConnectionError(
                        message=f"HTTP request failed: {e}",
                        status_code=getattr(e, "status", None),
                        details={
                            "error": str(e),
                            "url": url,
                            "method": method
                        }
                    )
                    await self._handle_error(error)
                    raise error
                else:
                    await asyncio.sleep(self.config.endpoints.retry_delay)

            except Exception as e:
                error = ConnectionError(
                    message=f"HTTP request failed: {e}",
                    details={
                        "error": str(e),
                        "url": url,
                        "method": method
                    }
                )
                await self._handle_error(error)
                raise

