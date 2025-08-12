#!/usr/bin/env python3
"""
Test Suite for Serena MCP Bridge

This test suite validates the functionality of the Serena MCP Bridge,
which provides a bridge between Serena's MCP server implementation
and graph-sitter's codebase analysis system.
"""

import os
import json
import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from graph_sitter.extensions.lsp.serena.mcp_bridge import (
    SerenaMCPBridge,
    MCPToolResult,
    ErrorInfo
)


class TestMCPBridge:
    """Test the MCP Bridge functionality."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def hello_world():\n    print('Hello, World!')\n")
            
            yield temp_dir
    
    @patch('subprocess.Popen')
    def test_mcp_bridge_initialization(self, mock_popen, temp_repo):
        """Test that MCP bridge initializes correctly."""
        # Mock the process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "serverInfo": {
                    "name": "test-mcp-server",
                    "version": "1.0.0"
                },
                "capabilities": {}
            }
        }) + "\n"
        mock_popen.return_value = mock_process
        
        # Initialize the bridge
        bridge = SerenaMCPBridge(temp_repo)
        
        # Verify initialization
        assert bridge.repo_path == Path(temp_repo)
        assert bridge.process is not None
        assert bridge.is_initialized is True
        
        # Verify that _initialize_mcp_protocol was called
        mock_process.stdin.write.assert_called()
        mock_process.stdout.readline.assert_called()
    
    @patch('subprocess.Popen')
    def test_discover_tools(self, mock_popen, temp_repo):
        """Test tool discovery."""
        # Mock the process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        
        # Mock initialization response
        mock_process.stdout.readline.side_effect = [
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "serverInfo": {
                        "name": "test-mcp-server",
                        "version": "1.0.0"
                    },
                    "capabilities": {}
                }
            }) + "\n",
            # Mock tools/list response
            json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "tools": [
                        {
                            "name": "test_tool",
                            "description": "A test tool",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "param1": {
                                        "type": "string",
                                        "description": "A test parameter"
                                    }
                                }
                            }
                        }
                    ]
                }
            }) + "\n"
        ]
        mock_popen.return_value = mock_process
        
        # Initialize the bridge
        bridge = SerenaMCPBridge(temp_repo)
        
        # Verify tool discovery
        assert "test_tool" in bridge.available_tools
        assert bridge.available_tools["test_tool"]["name"] == "test_tool"
        assert bridge.available_tools["test_tool"]["description"] == "A test tool"
    
    @patch('subprocess.Popen')
    def test_call_tool(self, mock_popen, temp_repo):
        """Test calling a tool."""
        # Mock the process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        
        # Mock initialization and tool discovery responses
        mock_process.stdout.readline.side_effect = [
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "serverInfo": {
                        "name": "test-mcp-server",
                        "version": "1.0.0"
                    },
                    "capabilities": {}
                }
            }) + "\n",
            # Mock tools/list response
            json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "tools": [
                        {
                            "name": "test_tool",
                            "description": "A test tool",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "param1": {
                                        "type": "string",
                                        "description": "A test parameter"
                                    }
                                }
                            }
                        }
                    ]
                }
            }) + "\n",
            # Mock tools/call response
            json.dumps({
                "jsonrpc": "2.0",
                "id": 3,
                "result": {
                    "success": True,
                    "message": "Tool executed successfully",
                    "data": {"key": "value"}
                }
            }) + "\n"
        ]
        mock_popen.return_value = mock_process
        
        # Initialize the bridge
        bridge = SerenaMCPBridge(temp_repo)
        
        # Call the tool
        result = bridge.call_tool("test_tool", {"param1": "test_value"})
        
        # Verify the result
        assert result.success is True
        assert result.tool_name == "test_tool"
        assert result.content["success"] is True
        assert result.content["message"] == "Tool executed successfully"
        assert result.content["data"]["key"] == "value"
        
        # Verify the request was sent correctly
        expected_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "test_tool",
                "arguments": {"param1": "test_value"}
            }
        }
        mock_process.stdin.write.assert_any_call(json.dumps(expected_request) + "\n")
    
    @patch('subprocess.Popen')
    def test_call_nonexistent_tool(self, mock_popen, temp_repo):
        """Test calling a tool that doesn't exist."""
        # Mock the process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        
        # Mock initialization and tool discovery responses
        mock_process.stdout.readline.side_effect = [
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "serverInfo": {
                        "name": "test-mcp-server",
                        "version": "1.0.0"
                    },
                    "capabilities": {}
                }
            }) + "\n",
            # Mock tools/list response
            json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "tools": [
                        {
                            "name": "test_tool",
                            "description": "A test tool",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "param1": {
                                        "type": "string",
                                        "description": "A test parameter"
                                    }
                                }
                            }
                        }
                    ]
                }
            }) + "\n"
        ]
        mock_popen.return_value = mock_process
        
        # Initialize the bridge
        bridge = SerenaMCPBridge(temp_repo)
        
        # Call a nonexistent tool
        result = bridge.call_tool("nonexistent_tool", {"param1": "test_value"})
        
        # Verify the result
        assert result.success is False
        assert result.tool_name == "nonexistent_tool"
        assert "not available" in result.error
    
    @patch('subprocess.Popen')
    def test_tool_error_response(self, mock_popen, temp_repo):
        """Test handling of error response from tool call."""
        # Mock the process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        
        # Mock initialization and tool discovery responses
        mock_process.stdout.readline.side_effect = [
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "serverInfo": {
                        "name": "test-mcp-server",
                        "version": "1.0.0"
                    },
                    "capabilities": {}
                }
            }) + "\n",
            # Mock tools/list response
            json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "tools": [
                        {
                            "name": "test_tool",
                            "description": "A test tool",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "param1": {
                                        "type": "string",
                                        "description": "A test parameter"
                                    }
                                }
                            }
                        }
                    ]
                }
            }) + "\n",
            # Mock tools/call error response
            json.dumps({
                "jsonrpc": "2.0",
                "id": 3,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": "Something went wrong"}
                }
            }) + "\n"
        ]
        mock_popen.return_value = mock_process
        
        # Initialize the bridge
        bridge = SerenaMCPBridge(temp_repo)
        
        # Call the tool
        result = bridge.call_tool("test_tool", {"param1": "test_value"})
        
        # Verify the result
        assert result.success is False
        assert result.tool_name == "test_tool"
        assert "Internal error" in result.error
    
    @patch('subprocess.Popen')
    def test_shutdown(self, mock_popen, temp_repo):
        """Test shutting down the MCP bridge."""
        # Mock the process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.wait = MagicMock()
        
        # Mock initialization response
        mock_process.stdout.readline.side_effect = [
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "serverInfo": {
                        "name": "test-mcp-server",
                        "version": "1.0.0"
                    },
                    "capabilities": {}
                }
            }) + "\n",
            # Mock tools/list response
            json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "tools": []
                }
            }) + "\n"
        ]
        mock_popen.return_value = mock_process
        
        # Initialize the bridge
        bridge = SerenaMCPBridge(temp_repo)
        
        # Shutdown the bridge
        bridge.shutdown()
        
        # Verify shutdown
        mock_process.stdin.write.assert_called()  # Should send shutdown notification
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert bridge.process is None
        assert bridge.is_initialized is False
    
    def test_error_info_class(self):
        """Test the ErrorInfo compatibility class."""
        # Create an ErrorInfo instance
        error = ErrorInfo(
            file_path="test.py",
            line=10,
            character=5,
            message="Test error",
            severity=1,
            source="test",
            code="E001"
        )
        
        # Verify properties
        assert error.file_path == "test.py"
        assert error.line == 10
        assert error.character == 5
        assert error.message == "Test error"
        assert error.severity == 1
        assert error.source == "test"
        assert error.code == "E001"
        
        # Verify helper properties
        assert error.is_error is True
        assert error.is_warning is False
        assert error.is_hint is False
        
        # Verify string representation
        assert "ERROR test.py:10:5 - Test error" in str(error)


class TestMCPToolResult:
    """Test the MCPToolResult class."""
    
    def test_successful_result(self):
        """Test creating a successful tool result."""
        result = MCPToolResult(
            success=True,
            content={"data": "test_data"},
            tool_name="test_tool"
        )
        
        assert result.success is True
        assert result.content["data"] == "test_data"
        assert result.tool_name == "test_tool"
        assert result.error is None
        assert "succeeded" in str(result)
    
    def test_failed_result(self):
        """Test creating a failed tool result."""
        result = MCPToolResult(
            success=False,
            content=None,
            error="Test error",
            tool_name="test_tool"
        )
        
        assert result.success is False
        assert result.content is None
        assert result.error == "Test error"
        assert result.tool_name == "test_tool"
        assert "failed" in str(result)
        assert "Test error" in str(result)


if __name__ == "__main__":
    pytest.main(["-v", __file__])

