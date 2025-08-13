#!/usr/bin/env python3
"""
Integration test for Graph-Sitter MCP server child run functionality.

This script tests the child run functionality in Graph-Sitter's MCP server implementation.
It creates a parent process that initiates child runs and verifies their execution.
"""

import asyncio
import json
import os
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Try to import required packages
try:
    from mcp.client import MCPClient
    from graph_sitter import Codebase
except ImportError:
    print("Error: Required packages not installed. Please install them with:")
    print("pip install mcp-server graph-sitter")
    sys.exit(1)


class GraphSitterMCPChildRunTest(unittest.TestCase):
    """Test case for Graph-Sitter MCP server child run functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Create a temporary directory for test files
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.repo_path = Path(cls.temp_dir.name)
        
        # Create a simple Python file for testing
        test_file = cls.repo_path / "test_file.py"
        test_file.write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")
        
        # Start the MCP server
        cls.server_process = cls._start_mcp_server(cls.repo_path)
        
        # Create MCP client
        cls.client = MCPClient(
            transport="stdio",
            process=cls.server_process
        )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment."""
        # Shutdown the client
        asyncio.run(cls.client.shutdown())
        
        # Terminate the server process
        if cls.server_process:
            cls.server_process.terminate()
            try:
                cls.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server_process.kill()
                cls.server_process.wait()
        
        # Clean up temporary directory
        cls.temp_dir.cleanup()
    
    @staticmethod
    def _start_mcp_server(repo_path: Path) -> subprocess.Popen:
        """
        Start the Graph-Sitter MCP server.
        
        Args:
            repo_path: Path to the repository
        
        Returns:
            The server process
        """
        # In a real test, this would start the actual Graph-Sitter MCP server
        # For this example, we'll use our test MCP server
        server_process = subprocess.Popen(
            [sys.executable, "test_mcp_child_run.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            cwd=str(repo_path)
        )
        
        return server_process
    
    async def _initialize_client(self):
        """Initialize the MCP client."""
        await self.client.initialize()
    
    async def test_child_run_echo(self):
        """Test child run with echo task."""
        # Initialize client
        await self._initialize_client()
        
        # Start a child run for echo task
        echo_result = await self.client.call_tool(
            "start_child_run",
            {
                "task_name": "echo",
                "parameters": {
                    "message": "Test message from echo child run"
                }
            }
        )
        
        # Verify child run was started
        self.assertIn("child_id", echo_result)
        self.assertEqual(echo_result["status"], "started")
        
        echo_child_id = echo_result["child_id"]
        
        # Wait for child run to complete
        await asyncio.sleep(3)
        
        # Check status of child run
        echo_status = await self.client.call_tool(
            "get_child_run_status",
            {
                "child_id": echo_child_id
            }
        )
        
        # Verify child run completed successfully
        self.assertEqual(echo_status["status"], "completed")
        self.assertIn("result", echo_status)
        self.assertIn("message", echo_status["result"])
        self.assertEqual(echo_status["result"]["message"], "Echo: Test message from echo child run")
    
    async def test_child_run_calculate(self):
        """Test child run with calculate task."""
        # Initialize client
        await self._initialize_client()
        
        # Start a child run for calculate task
        calc_result = await self.client.call_tool(
            "start_child_run",
            {
                "task_name": "calculate",
                "parameters": {
                    "a": 15,
                    "b": 3,
                    "operation": "divide"
                }
            }
        )
        
        # Verify child run was started
        self.assertIn("child_id", calc_result)
        self.assertEqual(calc_result["status"], "started")
        
        calc_child_id = calc_result["child_id"]
        
        # Wait for child run to complete
        await asyncio.sleep(3)
        
        # Check status of child run
        calc_status = await self.client.call_tool(
            "get_child_run_status",
            {
                "child_id": calc_child_id
            }
        )
        
        # Verify child run completed successfully
        self.assertEqual(calc_status["status"], "completed")
        self.assertIn("result", calc_status)
        self.assertEqual(calc_status["result"]["operation"], "divide")
        self.assertEqual(calc_status["result"]["a"], 15)
        self.assertEqual(calc_status["result"]["b"], 3)
        self.assertEqual(calc_status["result"]["result"], 5.0)
    
    async def test_multiple_child_runs(self):
        """Test running multiple child runs concurrently."""
        # Initialize client
        await self._initialize_client()
        
        # Start multiple child runs
        tasks = []
        child_ids = []
        
        # Echo task
        echo_result = await self.client.call_tool(
            "start_child_run",
            {
                "task_name": "echo",
                "parameters": {
                    "message": "Concurrent echo task"
                }
            }
        )
        child_ids.append(echo_result["child_id"])
        
        # Calculate tasks with different operations
        operations = ["add", "subtract", "multiply", "divide"]
        for i, operation in enumerate(operations):
            calc_result = await self.client.call_tool(
                "start_child_run",
                {
                    "task_name": "calculate",
                    "parameters": {
                        "a": 10,
                        "b": 2,
                        "operation": operation
                    }
                }
            )
            child_ids.append(calc_result["child_id"])
        
        # Wait for all child runs to complete
        await asyncio.sleep(3)
        
        # Check status of all child runs
        for child_id in child_ids:
            status = await self.client.call_tool(
                "get_child_run_status",
                {
                    "child_id": child_id
                }
            )
            
            # Verify child run completed
            self.assertEqual(status["status"], "completed")
            self.assertIn("result", status)


def run_tests():
    """Run the integration tests."""
    # Create test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GraphSitterMCPChildRunTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == "__main__":
    # Run the tests using asyncio
    asyncio.run(run_tests())

