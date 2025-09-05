import asyncio
import unittest
import subprocess
import json
import sys
import logging
import time
import os
from unittest.mock import patch, MagicMock
from mcp_orchestrator import MCPServer, MCPClient, MCPOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_test")

class TestMCPOrchestrator(unittest.TestCase):
    """Test the MCP orchestrator."""
    
    async def asyncSetUp(self):
        """Set up the test."""
        self.orchestrator = MCPOrchestrator()
    
    async def asyncTearDown(self):
        """Tear down the test."""
        await self.orchestrator.stop_all_servers()
    
    async def test_start_server(self):
        """Test starting a server."""
        server = await self.orchestrator.start_server("test-server", "python", ["test_mcp_server_fixed.py"])
        self.assertIsNotNone(server)
        self.assertIn("test-server", self.orchestrator.servers)
    
    async def test_create_client(self):
        """Test creating a client."""
        await self.orchestrator.start_server("test-server", "python", ["test_mcp_server_fixed.py"])
        client = self.orchestrator.create_client("test-client", "test-server")
        self.assertIsNotNone(client)
        self.assertIn("test-client", self.orchestrator.clients)
    
    async def test_initialize_client(self):
        """Test initializing a client."""
        await self.orchestrator.start_server("test-server", "python", ["test_mcp_server_fixed.py"])
        self.orchestrator.create_client("test-client", "test-server")
        result = await self.orchestrator.initialize_client("test-client")
        self.assertIsNotNone(result)
        self.assertIn("result", result)
        self.assertEqual(result["jsonrpc"], "2.0")
    
    async def test_list_tools(self):
        """Test listing tools."""
        await self.orchestrator.start_server("test-server", "python", ["test_mcp_server_fixed.py"])
        self.orchestrator.create_client("test-client", "test-server")
        await self.orchestrator.initialize_client("test-client")
        result = await self.orchestrator.list_tools("test-client")
        self.assertIsNotNone(result)
        self.assertIn("result", result)
        self.assertIn("tools", result["result"])
        self.assertEqual(len(result["result"]["tools"]), 1)
        self.assertEqual(result["result"]["tools"][0]["name"], "hello_world")
    
    async def test_call_tool(self):
        """Test calling a tool."""
        await self.orchestrator.start_server("test-server", "python", ["test_mcp_server_fixed.py"])
        self.orchestrator.create_client("test-client", "test-server")
        await self.orchestrator.initialize_client("test-client")
        result = await self.orchestrator.call_tool("test-client", "hello_world")
        self.assertIsNotNone(result)
        self.assertIn("result", result)
        self.assertIn("result", result["result"])
        self.assertEqual(result["result"]["result"], "Hello, world!")
    
    async def test_stop_server(self):
        """Test stopping a server."""
        await self.orchestrator.start_server("test-server", "python", ["test_mcp_server_fixed.py"])
        await self.orchestrator.stop_server("test-server")
        self.assertNotIn("test-server", self.orchestrator.servers)
    
    async def test_stop_all_servers(self):
        """Test stopping all servers."""
        await self.orchestrator.start_server("test-server-1", "python", ["test_mcp_server_fixed.py"])
        await self.orchestrator.start_server("test-server-2", "python", ["test_mcp_server_fixed.py"])
        await self.orchestrator.stop_all_servers()
        self.assertEqual(len(self.orchestrator.servers), 0)

def run_tests():
    """Run the tests."""
    unittest.main()

if __name__ == "__main__":
    # Create a test runner
    runner = unittest.TextTestRunner()
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add the tests
    for method_name in dir(TestMCPOrchestrator):
        if method_name.startswith("test_"):
            suite.addTest(TestMCPOrchestrator(method_name))
    
    # Run the tests
    runner.run(suite)

