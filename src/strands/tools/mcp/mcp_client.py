"""
Strands MCP Client

Model Context Protocol client for Strands agents.
Based on: https://github.com/strands-agents/sdk-python/blob/main/src/strands/tools/mcp/mcp_client.py
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPMessage:
    """MCP protocol message."""
    id: str
    type: MCPMessageType
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())


@dataclass
class MCPServer:
    """MCP server configuration."""
    name: str
    url: str
    capabilities: List[str] = field(default_factory=list)
    auth_token: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    enabled: bool = True


@dataclass
class MCPClientConfig:
    """Configuration for MCP client."""
    default_timeout: float = 30.0
    max_concurrent_requests: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_heartbeat: bool = True
    heartbeat_interval: float = 30.0


class MCPClient:
    """Model Context Protocol client for agent communication."""
    
    def __init__(self, config: Optional[MCPClientConfig] = None):
        """Initialize MCP client.
        
        Args:
            config: Optional client configuration
        """
        self.config = config or MCPClientConfig()
        self.servers: Dict[str, MCPServer] = {}
        self.connections: Dict[str, Any] = {}  # WebSocket connections
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.message_handlers: Dict[str, Callable[[MCPMessage], None]] = {}
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "connections_active": 0
        }
        
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        logger.info("Initialized MCP client")
    
    async def start(self):
        """Start the MCP client."""
        if self._running:
            return
        
        self._running = True
        
        if self.config.enable_heartbeat:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("Started MCP client")
    
    async def stop(self):
        """Stop the MCP client."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        
        # Close all connections
        for server_name in list(self.connections.keys()):
            await self.disconnect_server(server_name)
        
        # Cancel pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        
        logger.info("Stopped MCP client")
    
    def add_server(self, server: MCPServer):
        """Add an MCP server.
        
        Args:
            server: Server configuration to add
        """
        self.servers[server.name] = server
        logger.info(f"Added MCP server: {server.name} ({server.url})")
    
    def remove_server(self, server_name: str):
        """Remove an MCP server.
        
        Args:
            server_name: Name of server to remove
        """
        if server_name in self.servers:
            # Disconnect if connected
            if server_name in self.connections:
                asyncio.create_task(self.disconnect_server(server_name))
            
            del self.servers[server_name]
            logger.info(f"Removed MCP server: {server_name}")
    
    async def connect_server(self, server_name: str) -> bool:
        """Connect to an MCP server.
        
        Args:
            server_name: Name of server to connect to
            
        Returns:
            True if connection was successful
        """
        if server_name not in self.servers:
            logger.error(f"Server not found: {server_name}")
            return False
        
        if server_name in self.connections:
            logger.warning(f"Already connected to server: {server_name}")
            return True
        
        server = self.servers[server_name]
        
        try:
            # Simulate WebSocket connection (replace with actual implementation)
            connection = await self._create_connection(server)
            self.connections[server_name] = connection
            self.stats["connections_active"] += 1
            
            logger.info(f"Connected to MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to server {server_name}: {e}")
            return False
    
    async def disconnect_server(self, server_name: str):
        """Disconnect from an MCP server.
        
        Args:
            server_name: Name of server to disconnect from
        """
        if server_name not in self.connections:
            return
        
        try:
            connection = self.connections[server_name]
            await self._close_connection(connection)
            del self.connections[server_name]
            self.stats["connections_active"] -= 1
            
            logger.info(f"Disconnected from MCP server: {server_name}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from server {server_name}: {e}")
    
    async def send_request(self, 
                          server_name: str, 
                          method: str, 
                          params: Optional[Dict[str, Any]] = None,
                          timeout: Optional[float] = None) -> Any:
        """Send a request to an MCP server.
        
        Args:
            server_name: Name of target server
            method: Method to call
            params: Optional parameters
            timeout: Optional timeout override
            
        Returns:
            Response from server
        """
        if server_name not in self.connections:
            if not await self.connect_server(server_name):
                raise ConnectionError(f"Cannot connect to server: {server_name}")
        
        request_id = str(uuid.uuid4())
        timeout = timeout or self.config.default_timeout
        
        message = MCPMessage(
            id=request_id,
            type=MCPMessageType.REQUEST,
            method=method,
            params=params
        )
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        try:
            # Send message
            await self._send_message(server_name, message)
            self.stats["messages_sent"] += 1
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            self.stats["requests_successful"] += 1
            
            return response
            
        except asyncio.TimeoutError:
            self.stats["requests_failed"] += 1
            raise TimeoutError(f"Request timed out: {method}")
        except Exception as e:
            self.stats["requests_failed"] += 1
            raise
        finally:
            # Clean up
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
    
    async def send_notification(self, 
                               server_name: str, 
                               method: str, 
                               params: Optional[Dict[str, Any]] = None):
        """Send a notification to an MCP server.
        
        Args:
            server_name: Name of target server
            method: Method to call
            params: Optional parameters
        """
        if server_name not in self.connections:
            if not await self.connect_server(server_name):
                raise ConnectionError(f"Cannot connect to server: {server_name}")
        
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.NOTIFICATION,
            method=method,
            params=params
        )
        
        await self._send_message(server_name, message)
        self.stats["messages_sent"] += 1
    
    def add_message_handler(self, method: str, handler: Callable[[MCPMessage], None]):
        """Add a message handler for incoming messages.
        
        Args:
            method: Method name to handle
            handler: Handler function
        """
        self.message_handlers[method] = handler
        logger.info(f"Added message handler for method: {method}")
    
    async def _create_connection(self, server: MCPServer) -> Any:
        """Create connection to server (placeholder implementation).
        
        Args:
            server: Server to connect to
            
        Returns:
            Connection object
        """
        # This would be replaced with actual WebSocket connection
        # For now, return a mock connection
        return {
            "url": server.url,
            "connected": True,
            "server": server
        }
    
    async def _close_connection(self, connection: Any):
        """Close connection (placeholder implementation).
        
        Args:
            connection: Connection to close
        """
        # This would close the actual WebSocket connection
        connection["connected"] = False
    
    async def _send_message(self, server_name: str, message: MCPMessage):
        """Send message to server (placeholder implementation).
        
        Args:
            server_name: Name of target server
            message: Message to send
        """
        # This would send the actual message over WebSocket
        logger.debug(f"Sending message to {server_name}: {message.method}")
        
        # Simulate response for requests
        if message.type == MCPMessageType.REQUEST:
            # Simulate async response
            asyncio.create_task(self._simulate_response(message))
    
    async def _simulate_response(self, request: MCPMessage):
        """Simulate server response (for testing).
        
        Args:
            request: Original request message
        """
        await asyncio.sleep(0.1)  # Simulate network delay
        
        response = MCPMessage(
            id=request.id,
            type=MCPMessageType.RESPONSE,
            result={"status": "success", "method": request.method}
        )
        
        await self._handle_message(response)
    
    async def _handle_message(self, message: MCPMessage):
        """Handle incoming message.
        
        Args:
            message: Incoming message
        """
        self.stats["messages_received"] += 1
        
        if message.type == MCPMessageType.RESPONSE:
            # Handle response to pending request
            if message.id in self.pending_requests:
                future = self.pending_requests[message.id]
                if not future.done():
                    if message.error:
                        future.set_exception(Exception(message.error.get("message", "Unknown error")))
                    else:
                        future.set_result(message.result)
        
        elif message.type == MCPMessageType.NOTIFICATION:
            # Handle notification
            if message.method in self.message_handlers:
                try:
                    handler = self.message_handlers[message.method]
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler for {message.method}: {e}")
    
    async def _heartbeat_loop(self):
        """Heartbeat loop to maintain connections."""
        while self._running:
            try:
                for server_name in list(self.connections.keys()):
                    try:
                        await self.send_notification(server_name, "heartbeat")
                    except Exception as e:
                        logger.warning(f"Heartbeat failed for {server_name}: {e}")
                        # Attempt reconnection
                        await self.disconnect_server(server_name)
                        await self.connect_server(server_name)
                
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status.
        
        Returns:
            Status information
        """
        return {
            "running": self._running,
            "servers_configured": len(self.servers),
            "connections_active": len(self.connections),
            "pending_requests": len(self.pending_requests),
            "message_handlers": len(self.message_handlers),
            "stats": self.stats.copy(),
            "servers": {
                name: {
                    "url": server.url,
                    "connected": name in self.connections,
                    "enabled": server.enabled
                }
                for name, server in self.servers.items()
            }
        }

