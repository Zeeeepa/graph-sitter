"""
Consolidated LSP Client for Serena Integration

This module consolidates all LSP functionality from the lsp/ subdirectory
into a single, maintainable module.
"""

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum

from .types import ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)


# Core LSP Types
class ConnectionType:
    """LSP connection types."""
    STDIO = "stdio"
    TCP = "tcp"
    WEBSOCKET = "websocket"
    HTTP = "http"


class LSPError(Exception):
    """Base LSP error."""
    pass


class LSPConnectionError(LSPError):
    """LSP connection error."""
    pass


class LSPTimeoutError(LSPError):
    """LSP timeout error."""
    pass


@dataclass
class LSPMessage:
    """Base LSP message."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


@dataclass
class LSPRequest(LSPMessage):
    """LSP request message."""
    method: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LSPResponse(LSPMessage):
    """LSP response message."""
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


@dataclass
class LSPNotification(LSPMessage):
    """LSP notification message."""
    method: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeError:
    """Represents a code error from LSP diagnostics."""
    file_path: str
    line: int
    character: int
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    code: Optional[str] = None
    source: str = "lsp"
    range_start: Optional[Dict[str, int]] = None
    range_end: Optional[Dict[str, int]] = None


@dataclass
class DiagnosticStats:
    """Statistics about diagnostics."""
    total_errors: int = 0
    total_warnings: int = 0
    total_info: int = 0
    total_hints: int = 0
    files_with_errors: int = 0
    most_common_errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ServerConfig:
    """Configuration for LSP server."""
    name: str
    command: List[str]
    connection_type: str = ConnectionType.STDIO
    host: str = "localhost"
    port: int = 8080
    timeout: float = 30.0
    auto_restart: bool = True
    initialization_options: Dict[str, Any] = field(default_factory=dict)


class SerenaLSPClient:
    """
    Consolidated LSP client for Serena language servers.
    Combines functionality from client.py, server_manager.py, and protocol.py.
    """
    
    def __init__(
        self,
        server_config: ServerConfig,
        connection_type: str = ConnectionType.STDIO,
        timeout: float = 30.0
    ):
        self.server_config = server_config
        self.connection_type = connection_type
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self.connected = False
        self.request_id = 0
        self.pending_requests: Dict[int, asyncio.Future] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.diagnostics: List[CodeError] = []
        
    async def connect(self) -> bool:
        """Connect to the LSP server."""
        try:
            if self.connection_type == ConnectionType.STDIO:
                return await self._connect_stdio()
            elif self.connection_type == ConnectionType.TCP:
                return await self._connect_tcp()
            else:
                raise LSPConnectionError(f"Unsupported connection type: {self.connection_type}")
        except Exception as e:
            logger.error(f"Failed to connect to LSP server: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Connect via STDIO."""
        try:
            self.process = subprocess.Popen(
                self.server_config.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send initialize request
            init_result = await self.initialize()
            if init_result:
                self.connected = True
                # Start message processing
                asyncio.create_task(self._process_messages())
                return True
            return False
            
        except Exception as e:
            logger.error(f"STDIO connection failed: {e}")
            return False
    
    async def _connect_tcp(self) -> bool:
        """Connect via TCP."""
        # TCP connection implementation would go here
        raise NotImplementedError("TCP connection not yet implemented")
    
    async def initialize(self) -> bool:
        """Initialize the LSP server."""
        try:
            init_params = {
                "processId": None,
                "clientInfo": {"name": "Serena", "version": "1.0.0"},
                "capabilities": {
                    "textDocument": {
                        "publishDiagnostics": {"relatedInformation": True},
                        "completion": {"completionItem": {"snippetSupport": True}},
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "signatureHelp": {"signatureInformation": {"documentationFormat": ["markdown"]}},
                        "rename": {"prepareSupport": True}
                    }
                }
            }
            
            response = await self.send_request("initialize", init_params)
            if response and not response.get("error"):
                # Send initialized notification
                await self.send_notification("initialized", {})
                return True
            return False
            
        except Exception as e:
            logger.error(f"LSP initialization failed: {e}")
            return False
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send an LSP request and wait for response."""
        if not self.connected:
            raise LSPConnectionError("Not connected to LSP server")
        
        request_id = self.request_id
        self.request_id += 1
        
        request = LSPRequest(
            id=request_id,
            method=method,
            params=params
        )
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        try:
            # Send request
            await self._send_message(request)
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=self.timeout)
            return response
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise LSPTimeoutError(f"Request {method} timed out")
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            raise LSPError(f"Request {method} failed: {e}")
    
    async def send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """Send an LSP notification."""
        if not self.connected:
            raise LSPConnectionError("Not connected to LSP server")
        
        notification = LSPNotification(method=method, params=params)
        await self._send_message(notification)
    
    async def _send_message(self, message: LSPMessage) -> None:
        """Send a message to the LSP server."""
        if not self.process or not self.process.stdin:
            raise LSPConnectionError("No active connection")
        
        content = json.dumps(message.__dict__)
        full_message = f"Content-Length: {len(content)}\r\n\r\n{content}"
        
        self.process.stdin.write(full_message)
        self.process.stdin.flush()
    
    async def _process_messages(self) -> None:
        """Process incoming messages from LSP server."""
        if not self.process or not self.process.stdout:
            return
        
        buffer = ""
        while self.connected and self.process.poll() is None:
            try:
                # Read data
                data = self.process.stdout.read(1024)
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages
                while "\r\n\r\n" in buffer:
                    header_end = buffer.find("\r\n\r\n")
                    header = buffer[:header_end]
                    
                    # Parse content length
                    content_length = 0
                    for line in header.split("\r\n"):
                        if line.startswith("Content-Length:"):
                            content_length = int(line.split(":")[1].strip())
                            break
                    
                    if len(buffer) >= header_end + 4 + content_length:
                        # Extract message
                        content = buffer[header_end + 4:header_end + 4 + content_length]
                        buffer = buffer[header_end + 4 + content_length:]
                        
                        # Process message
                        await self._handle_message(content)
                    else:
                        break
                        
            except Exception as e:
                logger.error(f"Error processing messages: {e}")
                break
    
    async def _handle_message(self, content: str) -> None:
        """Handle an incoming LSP message."""
        try:
            message = json.loads(content)
            
            # Handle response
            if "id" in message and message["id"] in self.pending_requests:
                future = self.pending_requests.pop(message["id"])
                if not future.done():
                    future.set_result(message)
            
            # Handle notification
            elif "method" in message:
                method = message["method"]
                params = message.get("params", {})
                
                # Handle diagnostics
                if method == "textDocument/publishDiagnostics":
                    await self._handle_diagnostics(params)
                
                # Handle other notifications
                if method in self.message_handlers:
                    await self.message_handlers[method](params)
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _handle_diagnostics(self, params: Dict[str, Any]) -> None:
        """Handle diagnostic notifications."""
        try:
            uri = params.get("uri", "")
            diagnostics = params.get("diagnostics", [])
            
            # Convert to CodeError objects
            file_errors = []
            for diag in diagnostics:
                severity_map = {1: ErrorSeverity.ERROR, 2: ErrorSeverity.WARNING, 3: ErrorSeverity.INFO, 4: ErrorSeverity.HINT}
                severity = severity_map.get(diag.get("severity", 1), ErrorSeverity.ERROR)
                
                error = CodeError(
                    file_path=uri.replace("file://", ""),
                    line=diag["range"]["start"]["line"] + 1,
                    character=diag["range"]["start"]["character"],
                    severity=severity,
                    category=ErrorCategory.SYNTAX,  # Default, could be improved
                    message=diag.get("message", ""),
                    code=str(diag.get("code", "")),
                    source=diag.get("source", "lsp"),
                    range_start=diag["range"]["start"],
                    range_end=diag["range"]["end"]
                )
                file_errors.append(error)
            
            # Update diagnostics
            # Remove old diagnostics for this file
            self.diagnostics = [d for d in self.diagnostics if d.file_path != error.file_path]
            # Add new diagnostics
            self.diagnostics.extend(file_errors)
            
        except Exception as e:
            logger.error(f"Error handling diagnostics: {e}")
    
    async def get_diagnostics(self, file_path: Optional[str] = None) -> List[CodeError]:
        """Get diagnostics for a file or all files."""
        if file_path:
            return [d for d in self.diagnostics if d.file_path == file_path]
        return self.diagnostics.copy()
    
    async def get_completions(self, file_path: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get code completions."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": {"line": line - 1, "character": character}
        }
        
        response = await self.send_request("textDocument/completion", params)
        if response and "result" in response:
            items = response["result"]
            if isinstance(items, dict) and "items" in items:
                return items["items"]
            elif isinstance(items, list):
                return items
        return []
    
    async def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Get hover information."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": {"line": line - 1, "character": character}
        }
        
        response = await self.send_request("textDocument/hover", params)
        if response and "result" in response:
            return response["result"]
        return None
    
    async def rename_symbol(self, file_path: str, line: int, character: int, new_name: str) -> Optional[Dict[str, Any]]:
        """Rename a symbol."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": {"line": line - 1, "character": character},
            "newName": new_name
        }
        
        response = await self.send_request("textDocument/rename", params)
        if response and "result" in response:
            return response["result"]
        return None
    
    def get_stats(self) -> DiagnosticStats:
        """Get diagnostic statistics."""
        stats = DiagnosticStats()
        
        for diag in self.diagnostics:
            if diag.severity == ErrorSeverity.ERROR:
                stats.total_errors += 1
            elif diag.severity == ErrorSeverity.WARNING:
                stats.total_warnings += 1
            elif diag.severity == ErrorSeverity.INFO:
                stats.total_info += 1
            elif diag.severity == ErrorSeverity.HINT:
                stats.total_hints += 1
        
        # Count files with errors
        files_with_issues = set(d.file_path for d in self.diagnostics)
        stats.files_with_errors = len(files_with_issues)
        
        return stats
    
    async def disconnect(self) -> None:
        """Disconnect from the LSP server."""
        self.connected = False
        
        if self.process:
            try:
                await self.send_notification("exit", {})
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            finally:
                self.process = None
        
        # Cancel pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()


class SerenaServerManager:
    """
    Manages multiple LSP servers for different languages.
    Consolidated from server_manager.py.
    """
    
    def __init__(self):
        self.servers: Dict[str, SerenaLSPClient] = {}
        self.configs: Dict[str, ServerConfig] = {}
    
    def add_server(self, language: str, config: ServerConfig) -> None:
        """Add a server configuration."""
        self.configs[language] = config
    
    async def start_server(self, language: str) -> bool:
        """Start a language server."""
        if language not in self.configs:
            logger.error(f"No configuration for language: {language}")
            return False
        
        config = self.configs[language]
        client = SerenaLSPClient(config, config.connection_type, config.timeout)
        
        if await client.connect():
            self.servers[language] = client
            logger.info(f"Started {language} language server")
            return True
        else:
            logger.error(f"Failed to start {language} language server")
            return False
    
    async def stop_server(self, language: str) -> None:
        """Stop a language server."""
        if language in self.servers:
            await self.servers[language].disconnect()
            del self.servers[language]
            logger.info(f"Stopped {language} language server")
    
    def get_server(self, language: str) -> Optional[SerenaLSPClient]:
        """Get a language server client."""
        return self.servers.get(language)
    
    async def get_all_diagnostics(self) -> List[CodeError]:
        """Get diagnostics from all servers."""
        all_diagnostics = []
        for server in self.servers.values():
            diagnostics = await server.get_diagnostics()
            all_diagnostics.extend(diagnostics)
        return all_diagnostics
    
    async def shutdown_all(self) -> None:
        """Shutdown all servers."""
        for language in list(self.servers.keys()):
            await self.stop_server(language)


# Utility functions
def create_python_server_config() -> ServerConfig:
    """Create configuration for Python language server."""
    return ServerConfig(
        name="python",
        command=["pylsp"],
        connection_type=ConnectionType.STDIO,
        initialization_options={
            "settings": {
                "pylsp": {
                    "plugins": {
                        "pycodestyle": {"enabled": True},
                        "pyflakes": {"enabled": True},
                        "pylint": {"enabled": False},
                        "mypy": {"enabled": True}
                    }
                }
            }
        }
    )


def create_typescript_server_config() -> ServerConfig:
    """Create configuration for TypeScript language server."""
    return ServerConfig(
        name="typescript",
        command=["typescript-language-server", "--stdio"],
        connection_type=ConnectionType.STDIO
    )
