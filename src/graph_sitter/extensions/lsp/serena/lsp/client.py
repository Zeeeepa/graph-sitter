"""
Serena LSP Client Implementation

This module provides a comprehensive LSP client for communicating with Serena
language servers, handling connection management, message routing, and
real-time error retrieval.
"""

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
import websockets
import aiohttp

from .protocol import ProtocolHandler, LSPRequest, LSPResponse, LSPNotification, SerenaProtocolExtensions
from .error_retrieval import ErrorRetriever, ComprehensiveErrorList, CodeError

logger = logging.getLogger(__name__)


class LSPError(Exception):
    """Base LSP error."""
    pass


class LSPConnectionError(LSPError):
    """LSP connection error."""
    pass


class LSPTimeoutError(LSPError):
    """LSP timeout error."""
    pass


class ConnectionType:
    """LSP connection types."""
    STDIO = "stdio"
    TCP = "tcp"
    WEBSOCKET = "websocket"
    HTTP = "http"


class SerenaLSPClient:
    """
    Comprehensive LSP client for Serena language servers.
    
    Features:
    - Multiple connection types (stdio, TCP, WebSocket, HTTP)
    - Automatic reconnection and error recovery
    - Real-time error monitoring
    - Request/response correlation
    - Notification handling
    - Connection health monitoring
    """
    
    def __init__(self, 
                 server_command: Optional[List[str]] = None,
                 server_host: str = "localhost",
                 server_port: int = 8080,
                 connection_type: str = ConnectionType.STDIO,
                 timeout: float = 30.0,
                 auto_reconnect: bool = True,
                 max_reconnect_attempts: int = 5):
        
        self.server_command = server_command or ["serena-lsp-server"]
        self.server_host = server_host
        self.server_port = server_port
        self.connection_type = connection_type
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        
        # Core components
        self.protocol = ProtocolHandler()
        self.error_retriever = ErrorRetriever(self.protocol)
        
        # Connection state
        self._connected = False
        self._server_process: Optional[subprocess.Popen] = None
        self._websocket: Optional[websockets.WebSocketServerProtocol] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        
        # Monitoring
        self._message_handlers: List[Callable] = []
        self._connection_listeners: List[Callable] = []
        self._reconnect_attempts = 0
        self._last_heartbeat: Optional[float] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._message_loop_task: Optional[asyncio.Task] = None
        
        # Initialize capabilities
        self._server_capabilities: Dict[str, Any] = {}
        self._client_capabilities = self._get_client_capabilities()
    
    async def connect(self) -> bool:
        """
        Connect to the Serena LSP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.connection_type == ConnectionType.STDIO:
                await self._connect_stdio()
            elif self.connection_type == ConnectionType.TCP:
                await self._connect_tcp()
            elif self.connection_type == ConnectionType.WEBSOCKET:
                await self._connect_websocket()
            elif self.connection_type == ConnectionType.HTTP:
                await self._connect_http()
            else:
                raise LSPConnectionError(f"Unsupported connection type: {self.connection_type}")
            
            # Initialize the server
            await self._initialize_server()
            
            # Start message handling loop
            self._message_loop_task = asyncio.create_task(self._message_loop())
            
            # Start heartbeat monitoring
            if self.connection_type in [ConnectionType.TCP, ConnectionType.WEBSOCKET]:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            self._connected = True
            self._reconnect_attempts = 0
            
            # Notify connection listeners
            await self._notify_connection_listeners(True)
            
            logger.info(f"Successfully connected to Serena LSP server via {self.connection_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Serena LSP server: {e}")
            await self._cleanup_connection()
            return False
    
    async def disconnect(self):
        """Disconnect from the LSP server."""
        if not self._connected:
            return
        
        try:
            # Send shutdown request
            await self._send_shutdown()
            
            # Cancel background tasks
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            if self._message_loop_task:
                self._message_loop_task.cancel()
            
            # Cleanup connection
            await self._cleanup_connection()
            
            self._connected = False
            
            # Notify connection listeners
            await self._notify_connection_listeners(False)
            
            logger.info("Disconnected from Serena LSP server")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def get_comprehensive_errors(self, **kwargs) -> ComprehensiveErrorList:
        """Get comprehensive error list from server."""
        if not self._connected:
            raise LSPConnectionError("Not connected to LSP server")
        
        return await self.error_retriever.get_comprehensive_errors(**kwargs)
    
    async def get_file_errors(self, file_path: str) -> List[CodeError]:
        """Get errors for a specific file."""
        if not self._connected:
            raise LSPConnectionError("Not connected to LSP server")
        
        return await self.error_retriever.get_file_errors(file_path)
    
    async def analyze_codebase(self, root_path: str, **kwargs) -> ComprehensiveErrorList:
        """Analyze entire codebase."""
        if not self._connected:
            raise LSPConnectionError("Not connected to LSP server")
        
        return await self.error_retriever.analyze_codebase(root_path, **kwargs)
    
    async def analyze_file(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a specific file."""
        if not self._connected:
            raise LSPConnectionError("Not connected to LSP server")
        
        params = SerenaProtocolExtensions.create_analyze_file_request(file_path, content)
        
        request = self.protocol.create_request(
            SerenaProtocolExtensions.SERENA_ANALYZE_FILE,
            params
        )
        
        return await self._send_request(request)
    
    async def refresh_analysis(self) -> bool:
        """Refresh server analysis."""
        if not self._connected:
            raise LSPConnectionError("Not connected to LSP server")
        
        request = self.protocol.create_request(
            SerenaProtocolExtensions.SERENA_REFRESH_ANALYSIS
        )
        
        try:
            await self._send_request(request)
            return True
        except Exception as e:
            logger.error(f"Error refreshing analysis: {e}")
            return False
    
    def add_error_listener(self, listener: Callable[[List[CodeError]], None]):
        """Add listener for error updates."""
        self.error_retriever.add_error_listener(listener)
    
    def add_connection_listener(self, listener: Callable[[bool], None]):
        """Add listener for connection status changes."""
        self._connection_listeners.append(listener)
    
    def add_message_handler(self, handler: Callable):
        """Add custom message handler."""
        self._message_handlers.append(handler)
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected
    
    @property
    def server_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        return self._server_capabilities.copy()
    
    async def _connect_stdio(self):
        """Connect via stdio."""
        try:
            self._server_process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Create asyncio streams
            self._reader = asyncio.StreamReader()
            self._writer = asyncio.StreamWriter(
                self._server_process.stdin,
                self.protocol,
                self._reader,
                asyncio.get_event_loop()
            )
            
        except Exception as e:
            raise LSPConnectionError(f"Failed to start LSP server process: {e}")
    
    async def _connect_tcp(self):
        """Connect via TCP."""
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self.server_host, self.server_port
            )
        except Exception as e:
            raise LSPConnectionError(f"Failed to connect via TCP: {e}")
    
    async def _connect_websocket(self):
        """Connect via WebSocket."""
        try:
            uri = f"ws://{self.server_host}:{self.server_port}/lsp"
            self._websocket = await websockets.connect(uri)
        except Exception as e:
            raise LSPConnectionError(f"Failed to connect via WebSocket: {e}")
    
    async def _connect_http(self):
        """Connect via HTTP."""
        try:
            self._http_session = aiohttp.ClientSession()
        except Exception as e:
            raise LSPConnectionError(f"Failed to create HTTP session: {e}")
    
    async def _initialize_server(self):
        """Initialize the LSP server."""
        # Send initialize request
        initialize_params = {
            "processId": None,
            "clientInfo": {
                "name": "Serena Graph-Sitter Client",
                "version": "1.0.0"
            },
            "capabilities": self._client_capabilities,
            "workspaceFolders": None
        }
        
        request = self.protocol.create_request("initialize", initialize_params)
        response = await self._send_request(request)
        
        # Store server capabilities
        self._server_capabilities = response.get("capabilities", {})
        
        # Send initialized notification
        notification = self.protocol.create_notification("initialized", {})
        await self._send_notification(notification)
    
    async def _send_shutdown(self):
        """Send shutdown request."""
        try:
            request = self.protocol.create_request("shutdown")
            await self._send_request(request)
            
            # Send exit notification
            notification = self.protocol.create_notification("exit")
            await self._send_notification(notification)
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _send_request(self, request: LSPRequest) -> Any:
        """Send request and wait for response."""
        future = self.protocol.track_request(request)
        
        await self._send_message(request)
        
        try:
            result = await asyncio.wait_for(future, timeout=self.timeout)
            return result
        except asyncio.TimeoutError:
            self.protocol.cancel_request(request.id)
            raise LSPTimeoutError(f"Request {request.method} timed out")
    
    async def _send_notification(self, notification: LSPNotification):
        """Send notification."""
        await self._send_message(notification)
    
    async def _send_message(self, message: Union[LSPRequest, LSPResponse, LSPNotification]):
        """Send message via appropriate transport."""
        message_json = message.to_json()
        
        if self.connection_type == ConnectionType.STDIO:
            await self._send_stdio_message(message_json)
        elif self.connection_type == ConnectionType.TCP:
            await self._send_tcp_message(message_json)
        elif self.connection_type == ConnectionType.WEBSOCKET:
            await self._send_websocket_message(message_json)
        elif self.connection_type == ConnectionType.HTTP:
            await self._send_http_message(message_json)
    
    async def _send_stdio_message(self, message: str):
        """Send message via stdio."""
        if not self._writer:
            raise LSPConnectionError("No stdio connection")
        
        content_length = len(message.encode('utf-8'))
        full_message = f"Content-Length: {content_length}\r\n\r\n{message}"
        
        self._writer.write(full_message.encode('utf-8'))
        await self._writer.drain()
    
    async def _send_tcp_message(self, message: str):
        """Send message via TCP."""
        if not self._writer:
            raise LSPConnectionError("No TCP connection")
        
        content_length = len(message.encode('utf-8'))
        full_message = f"Content-Length: {content_length}\r\n\r\n{message}"
        
        self._writer.write(full_message.encode('utf-8'))
        await self._writer.drain()
    
    async def _send_websocket_message(self, message: str):
        """Send message via WebSocket."""
        if not self._websocket:
            raise LSPConnectionError("No WebSocket connection")
        
        await self._websocket.send(message)
    
    async def _send_http_message(self, message: str):
        """Send message via HTTP."""
        if not self._http_session:
            raise LSPConnectionError("No HTTP session")
        
        url = f"http://{self.server_host}:{self.server_port}/lsp"
        
        async with self._http_session.post(
            url,
            data=message,
            headers={"Content-Type": "application/json"}
        ) as response:
            return await response.json()
    
    async def _message_loop(self):
        """Main message handling loop."""
        try:
            while self._connected:
                message = await self._receive_message()
                if message:
                    await self._handle_message(message)
        except Exception as e:
            logger.error(f"Error in message loop: {e}")
            if self.auto_reconnect:
                await self._attempt_reconnect()
    
    async def _receive_message(self) -> Optional[str]:
        """Receive message from server."""
        if self.connection_type in [ConnectionType.STDIO, ConnectionType.TCP]:
            return await self._receive_stream_message()
        elif self.connection_type == ConnectionType.WEBSOCKET:
            return await self._receive_websocket_message()
        elif self.connection_type == ConnectionType.HTTP:
            # HTTP is request-response, no continuous receiving
            return None
    
    async def _receive_stream_message(self) -> Optional[str]:
        """Receive message from stream (stdio/TCP)."""
        if not self._reader:
            return None
        
        try:
            # Read headers
            headers = {}
            while True:
                line = await self._reader.readline()
                if not line:
                    return None
                
                line = line.decode('utf-8').strip()
                if not line:
                    break
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            # Read content
            content_length = int(headers.get('Content-Length', 0))
            if content_length > 0:
                content = await self._reader.read(content_length)
                return content.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error receiving stream message: {e}")
        
        return None
    
    async def _receive_websocket_message(self) -> Optional[str]:
        """Receive message from WebSocket."""
        if not self._websocket:
            return None
        
        try:
            message = await self._websocket.recv()
            return message
        except Exception as e:
            logger.error(f"Error receiving WebSocket message: {e}")
            return None
    
    async def _handle_message(self, raw_message: str):
        """Handle incoming message."""
        try:
            message = self.protocol.parse_message(raw_message)
            
            # Handle with protocol handler
            response = await self.protocol.handle_message(message)
            
            # Send response if needed
            if response:
                await self._send_message(response)
            
            # Call custom message handlers
            for handler in self._message_handlers:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _heartbeat_loop(self):
        """Heartbeat monitoring loop."""
        while self._connected:
            try:
                # Send ping/heartbeat
                await self._send_heartbeat()
                self._last_heartbeat = time.time()
                
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                if self.auto_reconnect:
                    await self._attempt_reconnect()
                break
    
    async def _send_heartbeat(self):
        """Send heartbeat/ping message."""
        notification = self.protocol.create_notification("$/ping", {})
        await self._send_notification(notification)
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect to server."""
        if self._reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return
        
        self._reconnect_attempts += 1
        logger.info(f"Attempting reconnection {self._reconnect_attempts}/{self.max_reconnect_attempts}")
        
        await self._cleanup_connection()
        await asyncio.sleep(2 ** self._reconnect_attempts)  # Exponential backoff
        
        success = await self.connect()
        if not success:
            await self._attempt_reconnect()
    
    async def _cleanup_connection(self):
        """Clean up connection resources."""
        try:
            if self._websocket:
                await self._websocket.close()
                self._websocket = None
            
            if self._http_session:
                await self._http_session.close()
                self._http_session = None
            
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
                self._writer = None
            
            self._reader = None
            
            if self._server_process:
                self._server_process.terminate()
                self._server_process.wait()
                self._server_process = None
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def _notify_connection_listeners(self, connected: bool):
        """Notify connection status listeners."""
        for listener in self._connection_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(connected)
                else:
                    listener(connected)
            except Exception as e:
                logger.error(f"Error in connection listener: {e}")
    
    def _get_client_capabilities(self) -> Dict[str, Any]:
        """Get client capabilities."""
        return {
            "textDocument": {
                "publishDiagnostics": {
                    "relatedInformation": True,
                    "versionSupport": True,
                    "codeDescriptionSupport": True,
                    "dataSupport": True
                },
                "synchronization": {
                    "dynamicRegistration": True,
                    "willSave": True,
                    "willSaveWaitUntil": True,
                    "didSave": True
                }
            },
            "workspace": {
                "workspaceFolders": True,
                "configuration": True
            },
            "experimental": {
                "serenaExtensions": True
            }
        }

