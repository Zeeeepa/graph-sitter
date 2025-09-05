#!/usr/bin/env python3
"""
Test client for MCP server child run integration.

This script demonstrates how to interact with an MCP server and test child runs.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, Optional, List, Tuple

# Try to import MCP client - this requires the mcp package to be installed
try:
    from mcp.client import MCPClient
except ImportError:
    print("Error: mcp package not installed. Please install it with:")
    print("pip install mcp-server")
    sys.exit(1)


async def test_child_run(server_process: subprocess.Popen) -> None:
    """
    Test child run functionality with the MCP server.
    
    Args:
        server_process: The running MCP server process
    """
    # Create MCP client
    client = MCPClient(
        transport="stdio",
        process=server_process
    )
    
    # Initialize the client
    await client.initialize()
    
    # Get available tools
    tools = await client.list_tools()
    print(f"Available tools: {[tool['name'] for tool in tools]}")
    
    # Start a child run for echo task
    echo_result = await client.call_tool(
        "start_child_run",
        {
            "task_name": "echo",
            "parameters": {
                "message": "Hello from child run!"
            }
        }
    )
    
    echo_child_id = echo_result.get("child_id")
    print(f"Started echo child run: {echo_child_id}")
    
    # Start a child run for calculate task
    calc_result = await client.call_tool(
        "start_child_run",
        {
            "task_name": "calculate",
            "parameters": {
                "a": 10,
                "b": 5,
                "operation": "multiply"
            }
        }
    )
    
    calc_child_id = calc_result.get("child_id")
    print(f"Started calculate child run: {calc_child_id}")
    
    # Wait for child runs to complete
    await asyncio.sleep(3)
    
    # Check status of echo child run
    echo_status = await client.call_tool(
        "get_child_run_status",
        {
            "child_id": echo_child_id
        }
    )
    
    print(f"Echo child run status: {echo_status}")
    
    # Check status of calculate child run
    calc_status = await client.call_tool(
        "get_child_run_status",
        {
            "child_id": calc_child_id
        }
    )
    
    print(f"Calculate child run status: {calc_status}")
    
    # Shutdown the client
    await client.shutdown()


async def main():
    """Main function to run the test client."""
    print("Starting MCP client for child run integration testing")
    
    # Start the MCP server in a subprocess
    server_process = subprocess.Popen(
        [sys.executable, "test_mcp_child_run.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        # Test child run functionality
        await test_child_run(server_process)
    finally:
        # Ensure server process is terminated
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()


if __name__ == "__main__":
    asyncio.run(main())

