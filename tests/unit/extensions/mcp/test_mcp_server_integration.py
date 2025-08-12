#!/usr/bin/env python3
"""
Integration Tests for MCP Server and Orchestrator

This test suite validates the integration between the MCP server implementation
and the orchestrator components of graph-sitter.
"""

import pytest
import tempfile
import os
import json
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena.mcp_bridge import SerenaMCPBridge, MCPToolResult
from graph_sitter.cli.mcp.server import mcp as mcp_server


class TestMCPServerIntegration:
    """Test the MCP server integration."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def hello_world():\n    print('Hello, World!')\n")
            
            yield temp_dir
    
    @pytest.fixture
    def mock_codebase(self, temp_repo):
        """Create a mock codebase instance."""
        return Codebase(temp_repo)
    
    def test_mcp_bridge_initialization(self, temp_repo):
        """Test that the MCP bridge initializes correctly."""
        # Mock the subprocess.Popen to avoid actually starting a server
        with patch('subprocess.Popen') as mock_popen:
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
            })
            mock_popen.return_value = mock_process
            
            # Mock the tool discovery response
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
                }),
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "tools": [
                            {
                                "name": "test_tool",
                                "description": "A test tool",
                                "parameters": {}
                            }
                        ]
                    }
                })
            ]
            
            # Create the bridge
            bridge = SerenaMCPBridge(temp_repo)
            
            # Verify initialization
            assert bridge.is_initialized
            assert "test_tool" in bridge.available_tools
            
            # Cleanup
            bridge.shutdown()
    
    def test_mcp_bridge_call_tool(self, temp_repo):
        """Test calling a tool through the MCP bridge."""
        # Mock the subprocess.Popen to avoid actually starting a server
        with patch('subprocess.Popen') as mock_popen:
            # Mock the process
            mock_process = MagicMock()
            mock_process.stdin = MagicMock()
            mock_process.stdout = MagicMock()
            
            # Mock responses for initialization and tool call
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
                }),
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "tools": [
                            {
                                "name": "test_tool",
                                "description": "A test tool",
                                "parameters": {}
                            }
                        ]
                    }
                }),
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {
                        "output": "Tool executed successfully"
                    }
                })
            ]
            mock_popen.return_value = mock_process
            
            # Create the bridge
            bridge = SerenaMCPBridge(temp_repo)
            
            # Call a tool
            result = bridge.call_tool("test_tool", {"param": "value"})
            
            # Verify result
            assert result.success
            assert result.tool_name == "test_tool"
            assert "output" in result.content
            
            # Cleanup
            bridge.shutdown()
    
    def test_mcp_bridge_error_handling(self, temp_repo):
        """Test error handling in the MCP bridge."""
        # Mock the subprocess.Popen to avoid actually starting a server
        with patch('subprocess.Popen') as mock_popen:
            # Mock the process
            mock_process = MagicMock()
            mock_process.stdin = MagicMock()
            mock_process.stdout = MagicMock()
            
            # Mock responses for initialization and tool call
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
                }),
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "tools": [
                            {
                                "name": "test_tool",
                                "description": "A test tool",
                                "parameters": {}
                            }
                        ]
                    }
                }),
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 3,
                    "error": {
                        "code": -32603,
                        "message": "Internal error"
                    }
                })
            ]
            mock_popen.return_value = mock_process
            
            # Create the bridge
            bridge = SerenaMCPBridge(temp_repo)
            
            # Call a tool that will return an error
            result = bridge.call_tool("test_tool", {"param": "value"})
            
            # Verify error handling
            assert not result.success
            assert result.tool_name == "test_tool"
            assert result.error == "Internal error"
            
            # Cleanup
            bridge.shutdown()
    
    def test_mcp_bridge_shutdown(self, temp_repo):
        """Test proper shutdown of the MCP bridge."""
        # Mock the subprocess.Popen to avoid actually starting a server
        with patch('subprocess.Popen') as mock_popen:
            # Mock the process
            mock_process = MagicMock()
            mock_process.stdin = MagicMock()
            mock_process.stdout = MagicMock()
            mock_process.wait = MagicMock()
            mock_process.terminate = MagicMock()
            
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
                }),
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "tools": []
                    }
                })
            ]
            mock_popen.return_value = mock_process
            
            # Create the bridge
            bridge = SerenaMCPBridge(temp_repo)
            
            # Shutdown the bridge
            bridge.shutdown()
            
            # Verify shutdown
            mock_process.terminate.assert_called_once()
            mock_process.wait.assert_called_once()
            assert bridge.process is None
            assert not bridge.is_initialized


class TestMCPServerDefinition:
    """Test the MCP server definition."""
    
    def test_mcp_server_initialization(self):
        """Test that the MCP server initializes correctly."""
        # Verify server object
        assert mcp_server is not None
        assert mcp_server.name == "codegen-mcp"
        
        # Check resources
        assert mcp_server.resources is not None
        assert any(r.name == "system://agent_prompt" for r in mcp_server.resources)
        assert any(r.name == "system://setup_instructions" for r in mcp_server.resources)
        assert any(r.name == "system://manifest" for r in mcp_server.resources)
        
        # Check tools
        assert mcp_server.tools is not None
        assert any(t.name == "ask_codegen_sdk" for t in mcp_server.tools)
        assert any(t.name == "generate_codemod" for t in mcp_server.tools)
        assert any(t.name == "improve_codemod" for t in mcp_server.tools)
    
    def test_resource_functions(self):
        """Test the resource functions in the MCP server."""
        # Test get_docs resource
        from graph_sitter.cli.mcp.resources.system_prompt import SYSTEM_PROMPT
        from graph_sitter.cli.mcp.server import get_docs
        
        docs = get_docs()
        assert docs == SYSTEM_PROMPT
        
        # Test get_setup_instructions resource
        from graph_sitter.cli.mcp.resources.system_setup_instructions import SETUP_INSTRUCTIONS
        from graph_sitter.cli.mcp.server import get_setup_instructions
        
        instructions = get_setup_instructions()
        assert instructions == SETUP_INSTRUCTIONS
        
        # Test get_service_config resource
        from graph_sitter.cli.mcp.server import get_service_config
        
        config = get_service_config()
        assert config["name"] == "mcp-codegen"
        assert "version" in config
        assert "description" in config


class TestMCPServerTools:
    """Test the MCP server tools."""
    
    @patch('graph_sitter.cli.mcp.agent.docs_expert.create_sdk_expert_agent')
    def test_ask_codegen_sdk_tool(self, mock_create_agent):
        """Test the ask_codegen_sdk tool."""
        # Mock the agent
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [
                {"content": "Test response"}
            ]
        }
        mock_create_agent.return_value = mock_agent
        
        # Call the tool function
        from graph_sitter.cli.mcp.server import ask_codegen_sdk
        
        result = ask_codegen_sdk("How do I use the Codegen SDK?")
        
        # Verify result
        assert result == "Test response"
        mock_agent.invoke.assert_called_once()
    
    def test_generate_codemod_tool(self):
        """Test the generate_codemod tool."""
        from graph_sitter.cli.mcp.server import generate_codemod
        from mcp.server.fastmcp import Context
        
        # Create a mock context
        mock_context = MagicMock(spec=Context)
        
        # Call the tool function
        result = generate_codemod(
            title="test-codemod",
            task="Test task description",
            codebase_path="/test/repo",
            ctx=mock_context
        )
        
        # Verify result
        assert "codegen create test-codemod" in result
        assert "task" in result
    
    @patch('graph_sitter.cli.api.client.RestAPI')
    def test_improve_codemod_tool(self, mock_rest_api):
        """Test the improve_codemod tool."""
        # Mock the REST API
        mock_api_instance = MagicMock()
        mock_api_instance.improve_codemod.return_value = MagicMock(
            codemod_source="Improved codemod source"
        )
        mock_rest_api.return_value = mock_api_instance
        
        from graph_sitter.cli.mcp.server import improve_codemod
        from mcp.server.fastmcp import Context
        from graph_sitter.shared.enums.programming_language import ProgrammingLanguage
        
        # Create a mock context
        mock_context = MagicMock(spec=Context)
        
        # Call the tool function
        result = improve_codemod(
            codemod_source="Original codemod source",
            task="Test task description",
            concerns=["Issue 1", "Issue 2"],
            context={"files": ["file1.py", "file2.py"]},
            language=ProgrammingLanguage.PYTHON,
            ctx=mock_context
        )
        
        # Verify result
        assert result == "Improved codemod source"
        mock_api_instance.improve_codemod.assert_called_once_with(
            "Original codemod source",
            "Test task description",
            ["Issue 1", "Issue 2"],
            {"files": ["file1.py", "file2.py"]},
            ProgrammingLanguage.PYTHON
        )
    
    @patch('graph_sitter.cli.api.client.RestAPI')
    def test_improve_codemod_tool_error_handling(self, mock_rest_api):
        """Test error handling in the improve_codemod tool."""
        # Mock the REST API to raise an exception
        mock_api_instance = MagicMock()
        mock_api_instance.improve_codemod.side_effect = Exception("Test error")
        mock_rest_api.return_value = mock_api_instance
        
        from graph_sitter.cli.mcp.server import improve_codemod
        from mcp.server.fastmcp import Context
        from graph_sitter.shared.enums.programming_language import ProgrammingLanguage
        
        # Create a mock context
        mock_context = MagicMock(spec=Context)
        
        # Call the tool function
        result = improve_codemod(
            codemod_source="Original codemod source",
            task="Test task description",
            concerns=["Issue 1", "Issue 2"],
            context={"files": ["file1.py", "file2.py"]},
            language=ProgrammingLanguage.PYTHON,
            ctx=mock_context
        )
        
        # Verify error handling
        assert "Error: Test error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

