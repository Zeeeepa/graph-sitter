"""
Serena MCP Bridge for Graph-Sitter

This module provides a bridge between Serena's MCP server implementation
and graph-sitter's codebase analysis system.
"""

import asyncio
import json
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Callable
from enum import IntEnum
import tempfile
import os

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class MCPToolResult:
    """Result from an MCP tool invocation."""
    success: bool
    content: Any
    error: Optional[str] = None
    tool_name: Optional[str] = None
    
    def __str__(self) -> str:
        if self.success:
            return f"MCP Tool '{self.tool_name}' succeeded"
        else:
            return f"MCP Tool '{self.tool_name}' failed: {self.error}"


class SerenaMCPBridge:
    """Bridge between Serena's MCP server and graph-sitter."""
    
    def __init__(self, repo_path: str, serena_command: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.serena_command = serena_command or self._get_default_serena_command()
        self.process: Optional[subprocess.Popen] = None
        self.is_initialized = False
        self.available_tools: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._message_id = 0
        
        # Initialize the MCP server
        self._initialize_mcp_server()
    
    def _get_default_serena_command(self) -> str:
        """Get the default command to run Serena MCP server."""
        # Try uvx first (recommended approach)
        try:
            subprocess.run(["uvx", "--version"], capture_output=True, check=True)
            return "uvx --from git+https://github.com/oraios/serena serena-mcp-server"
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("uvx not found, falling back to direct git clone approach")
            return self._setup_local_serena()
    
    def _setup_local_serena(self) -> str:
        """Set up local Serena installation if uvx is not available."""
        # Create a temporary directory for Serena
        serena_dir = Path.home() / ".graph_sitter" / "serena"
        serena_dir.mkdir(parents=True, exist_ok=True)
        
        if not (serena_dir / "serena").exists():
            logger.info("Cloning Serena repository...")
            try:
                subprocess.run([
                    "git", "clone", "https://github.com/oraios/serena.git",
                    str(serena_dir / "serena")
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone Serena: {e}")
                raise RuntimeError("Could not set up Serena MCP server")
        
        return f"uv run --directory {serena_dir / 'serena'} serena-mcp-server"
    
    def _initialize_mcp_server(self) -> None:
        """Initialize the MCP server process."""
        try:
            # Change to the repository directory
            env = os.environ.copy()
            env["PWD"] = str(self.repo_path)
            
            # Start the Serena MCP server
            cmd = self.serena_command.split()
            cmd.extend(["--transport", "stdio"])
            
            logger.info(f"Starting Serena MCP server: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.repo_path),
                env=env,
                text=True,
                bufsize=0
            )
            
            # Initialize MCP protocol
            self._initialize_mcp_protocol()
            
            # Get available tools
            self._discover_tools()
            
            self.is_initialized = True
            logger.info(f"Serena MCP bridge initialized with {len(self.available_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize Serena MCP server: {e}")
            if self.process:
                self.process.terminate()
                self.process = None
    
    def _initialize_mcp_protocol(self) -> None:
        """Initialize the MCP protocol with handshake."""
        if not self.process:
            raise RuntimeError("MCP server process not started")
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "graph-sitter-serena",
                    "version": "1.0.0"
                }
            }
        }
        
        response = self._send_request(init_request)
        if not response or "error" in response:
            raise RuntimeError(f"MCP initialization failed: {response}")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        self._send_notification(initialized_notification)
    
    def _discover_tools(self) -> None:
        """Discover available tools from the MCP server."""
        if not self.process:
            return
        
        tools_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list"
        }
        
        response = self._send_request(tools_request)
        if response and "result" in response and "tools" in response["result"]:
            for tool in response["result"]["tools"]:
                self.available_tools[tool["name"]] = tool
                logger.debug(f"Discovered tool: {tool['name']}")
    
    def _get_next_id(self) -> int:
        """Get next message ID."""
        self._message_id += 1
        return self._message_id
    
    def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request to the MCP server and wait for response."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            return None
        
        try:
            # Send request
            request_line = json.dumps(request) + "\n"
            self.process.stdin.write(request_line)
            self.process.stdin.flush()
            
            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                return None
            
            return json.loads(response_line.strip())
            
        except Exception as e:
            logger.error(f"Error sending MCP request: {e}")
            return None
    
    def _send_notification(self, notification: Dict[str, Any]) -> None:
        """Send a notification to the MCP server (no response expected)."""
        if not self.process or not self.process.stdin:
            return
        
        try:
            notification_line = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_line)
            self.process.stdin.flush()
        except Exception as e:
            logger.error(f"Error sending MCP notification: {e}")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Call a tool on the MCP server."""
        if not self.is_initialized:
            return MCPToolResult(
                success=False,
                content=None,
                error="MCP server not initialized",
                tool_name=tool_name
            )
        
        if tool_name not in self.available_tools:
            return MCPToolResult(
                success=False,
                content=None,
                error=f"Tool '{tool_name}' not available",
                tool_name=tool_name
            )
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = self._send_request(request)
        
        if not response:
            return MCPToolResult(
                success=False,
                content=None,
                error="No response from MCP server",
                tool_name=tool_name
            )
        
        if "error" in response:
            return MCPToolResult(
                success=False,
                content=None,
                error=response["error"].get("message", "Unknown error"),
                tool_name=tool_name
            )
        
        if "result" in response:
            return MCPToolResult(
                success=True,
                content=response["result"],
                tool_name=tool_name
            )
        
        return MCPToolResult(
            success=False,
            content=None,
            error="Invalid response format",
            tool_name=tool_name
        )
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available tools."""
        return self.available_tools.copy()
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a specific tool is available."""
        return tool_name in self.available_tools
    
    def shutdown(self) -> None:
        """Shutdown the MCP server."""
        if self.process:
            try:
                # Send shutdown notification
                shutdown_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/cancelled"
                }
                self._send_notification(shutdown_notification)
                
                # Terminate process
                self.process.terminate()
                
                # Wait for process to end
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                
            except Exception as e:
                logger.error(f"Error shutting down MCP server: {e}")
            finally:
                self.process = None
        
        self.is_initialized = False
        logger.info("Serena MCP bridge shutdown")
    
    def __del__(self):
        """Cleanup when bridge is destroyed."""
        self.shutdown()


# Compatibility layer for existing LSP-based code
class ErrorInfo:
    """Compatibility class for LSP ErrorInfo."""
    
    def __init__(self, file_path: str, line: int, character: int, message: str, 
                 severity: int = 1, source: Optional[str] = None, 
                 code: Optional[Union[str, int]] = None,
                 end_line: Optional[int] = None, end_character: Optional[int] = None):
        self.file_path = file_path
        self.line = line
        self.character = character
        self.message = message
        self.severity = severity
        self.source = source
        self.code = code
        self.end_line = end_line
        self.end_character = end_character
    
    @property
    def is_error(self) -> bool:
        return self.severity == 1
    
    @property
    def is_warning(self) -> bool:
        return self.severity == 2
    
    @property
    def is_hint(self) -> bool:
        return self.severity == 4
    
    def __str__(self) -> str:
        severity_str = {1: "ERROR", 2: "WARNING", 3: "INFO", 4: "HINT"}.get(self.severity, "UNKNOWN")
        return f"{severity_str} {self.file_path}:{self.line}:{self.character} - {self.message}"


# For backward compatibility, alias the MCP bridge as LSP bridge
SerenaLSPBridge = SerenaMCPBridge
