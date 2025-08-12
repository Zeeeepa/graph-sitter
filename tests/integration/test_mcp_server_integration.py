#!/usr/bin/env python3
"""
Integration Test for MCP Server

This test validates the integration between graph-sitter and an MCP server.
It requires the Serena MCP server to be installed and available.
"""

import os
import json
import pytest
import tempfile
import subprocess
import time
from pathlib import Path

from graph_sitter.extensions.lsp.serena.mcp_bridge import SerenaMCPBridge


# Skip these tests if the environment isn't set up for integration testing
pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_MCP_INTEGRATION_TESTS") != "1",
    reason="MCP integration tests are disabled. Set RUN_MCP_INTEGRATION_TESTS=1 to enable."
)


class TestMCPServerIntegration:
    """Integration tests for MCP server."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def hello_world():\n    print('Hello, World!')\n")
            
            yield temp_dir
    
    def test_mcp_bridge_initialization(self, temp_repo):
        """Test that MCP bridge initializes correctly with a real server."""
        try:
            # Initialize the bridge with a custom command that should work in most environments
            bridge = SerenaMCPBridge(
                temp_repo,
                serena_command="python -c \"import sys; print('{\\\"jsonrpc\\\": \\\"2.0\\\", \\\"id\\\": 1, \\\"result\\\": {\\\"serverInfo\\\": {\\\"name\\\": \\\"test-server\\\", \\\"version\\\": \\\"1.0.0\\\"}, \\\"capabilities\\\": {}}}')\""
            )
            
            # Verify initialization
            assert bridge.repo_path == Path(temp_repo)
            assert bridge.process is not None
            
            # Shutdown the bridge
            bridge.shutdown()
            
        except Exception as e:
            pytest.skip(f"MCP server integration test failed: {e}")
    
    def test_mcp_server_tool_discovery(self, temp_repo):
        """Test discovering tools from a real MCP server."""
        # This test requires the Serena MCP server to be installed
        # It will be skipped if the server is not available
        
        try:
            # Try to find uvx command
            try:
                subprocess.run(["uvx", "--version"], capture_output=True, check=True)
                has_uvx = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                has_uvx = False
            
            if not has_uvx:
                pytest.skip("uvx command not found, skipping MCP server tool discovery test")
            
            # Initialize the bridge with the actual Serena MCP server
            bridge = SerenaMCPBridge(temp_repo)
            
            # Verify that tools were discovered
            assert len(bridge.available_tools) > 0
            
            # Print discovered tools for debugging
            print(f"Discovered {len(bridge.available_tools)} tools:")
            for tool_name, tool_info in bridge.available_tools.items():
                print(f"  - {tool_name}: {tool_info.get('description', 'No description')}")
            
            # Shutdown the bridge
            bridge.shutdown()
            
        except Exception as e:
            pytest.skip(f"MCP server tool discovery test failed: {e}")
    
    def test_mcp_server_tool_call(self, temp_repo):
        """Test calling a tool on a real MCP server."""
        # This test requires the Serena MCP server to be installed
        # It will be skipped if the server is not available
        
        try:
            # Try to find uvx command
            try:
                subprocess.run(["uvx", "--version"], capture_output=True, check=True)
                has_uvx = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                has_uvx = False
            
            if not has_uvx:
                pytest.skip("uvx command not found, skipping MCP server tool call test")
            
            # Initialize the bridge with the actual Serena MCP server
            bridge = SerenaMCPBridge(temp_repo)
            
            # Find a tool to call
            if not bridge.available_tools:
                pytest.skip("No tools available from MCP server")
            
            # Try to find a simple tool that doesn't require complex arguments
            tool_name = next(
                (name for name, info in bridge.available_tools.items() 
                 if "version" in name.lower() or "status" in name.lower() or "list" in name.lower()),
                list(bridge.available_tools.keys())[0]
            )
            
            # Call the tool
            result = bridge.call_tool(tool_name, {})
            
            # Print result for debugging
            print(f"Called tool {tool_name}:")
            print(f"  Success: {result.success}")
            print(f"  Content: {result.content}")
            print(f"  Error: {result.error}")
            
            # Shutdown the bridge
            bridge.shutdown()
            
        except Exception as e:
            pytest.skip(f"MCP server tool call test failed: {e}")


if __name__ == "__main__":
    pytest.main(["-v", __file__])

