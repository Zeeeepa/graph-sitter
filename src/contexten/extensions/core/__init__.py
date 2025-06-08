"""Core module for Contexten extensions."""

from .connection import (
    AuthConfig,
    AuthType,
    ConnectionConfig,
    ConnectionError,
    ConnectionEvent,
    ConnectionStatus,
    ConnectionType,
    EndpointConfig,
    ExtensionConnection,
)
from .connection_manager import ConnectionManager
from .connections import GraphQLConnection, HTTPConnection, WebSocketConnection

__all__ = [
    # Connection types
    "AuthConfig",
    "AuthType",
    "ConnectionConfig",
    "ConnectionError",
    "ConnectionEvent",
    "ConnectionStatus",
    "ConnectionType",
    "EndpointConfig",
    "ExtensionConnection",
    
    # Connection manager
    "ConnectionManager",
    
    # Connection implementations
    "GraphQLConnection",
    "HTTPConnection",
    "WebSocketConnection",
]

