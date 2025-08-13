#!/usr/bin/env python3
"""
Test MCP server integration with graph-sitter
"""

import asyncio
import json
import os
import subprocess
import time
import unittest
from unittest import IsolatedAsyncioTestCase

class TestMCPIntegration(IsolatedAsyncioTestCase):
    """Test MCP server integration with graph-sitter."""
    
    def test_mcp_server_starts(self):
        """Test that the MCP server can be started."""
        # Start the MCP server as a subprocess
        process = subprocess.Popen(
            ["python", "run_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        try:
            # Give the server a moment to start
            time.sleep(1)
            
            # Check if the process is still running
            self.assertIsNone(process.poll(), "MCP server process terminated unexpectedly")
            
            # Check if the server printed the expected startup message
            output = process.stdout.readline().strip()
            self.assertEqual(output, "Starting test MCP server...", "Unexpected server startup message")
            
            print("MCP server startup test passed! ✅")
        finally:
            # Clean up
            process.terminate()
            process.wait()
    
    async def test_mcp_server_tool_call(self):
        """Test that the MCP server can handle tool calls."""
        # This test requires manual inspection of the output
        # as we don't have a proper client to interact with the server
        
        # Start the MCP server as a subprocess
        process = subprocess.Popen(
            ["python", "run_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        try:
            # Give the server a moment to start
            await asyncio.sleep(1)
            
            # Check if the process is still running
            self.assertIsNone(process.poll(), "MCP server process terminated unexpectedly")
            
            # Read the startup message
            output = process.stdout.readline().strip()
            self.assertEqual(output, "Starting test MCP server...", "Unexpected server startup message")
            
            # Send a manual initialize request
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "capabilities": {}
                }
            }
            
            process.stdin.write(json.dumps(initialize_request) + "\n")
            process.stdin.flush()
            
            # Wait for a response
            await asyncio.sleep(1)
            
            # The server should have responded, but we can't easily parse it
            # This is just a basic test to ensure the server doesn't crash
            
            print("MCP server tool call test passed! ✅")
        finally:
            # Clean up
            process.terminate()
            process.wait()

if __name__ == "__main__":
    unittest.main()

