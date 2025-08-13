#!/usr/bin/env python3
"""
Test script for MCP server child run integration.

This script demonstrates how to test a child run from an MCP server integration.
It creates a simple MCP server, initiates a parent process, and then spawns a child run.
"""

import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Try to import FastMCP - this requires the mcp package to be installed
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: mcp package not installed. Please install it with:")
    print("pip install mcp-server")
    sys.exit(1)

# Create a simple MCP server for testing
mcp = FastMCP(
    "test-mcp-server",
    instructions="Test MCP server for child run integration testing",
)

# Global state to track child runs
child_runs = {}


@mcp.tool(name="start_child_run", description="Start a child run process")
async def start_child_run(task_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Start a child run process with the given parameters.
    
    Args:
        task_name: Name of the task to run
        parameters: Optional parameters to pass to the child run
    
    Returns:
        Dictionary with child run information
    """
    # Create a unique ID for this child run
    child_id = f"child_{len(child_runs) + 1}"
    
    # Prepare parameters
    params = parameters or {}
    
    # Create child process
    # In a real implementation, this would use subprocess.Popen or similar
    # to start a new process, but for this test we'll just simulate it
    child_runs[child_id] = {
        "id": child_id,
        "task_name": task_name,
        "parameters": params,
        "status": "running",
        "result": None
    }
    
    # Simulate async processing
    asyncio.create_task(process_child_run(child_id, task_name, params))
    
    return {
        "child_id": child_id,
        "status": "started",
        "message": f"Child run '{child_id}' started for task '{task_name}'"
    }


@mcp.tool(name="get_child_run_status", description="Get the status of a child run")
async def get_child_run_status(child_id: str) -> Dict[str, Any]:
    """
    Get the status of a child run.
    
    Args:
        child_id: ID of the child run
    
    Returns:
        Dictionary with child run status information
    """
    if child_id not in child_runs:
        return {
            "error": f"Child run '{child_id}' not found"
        }
    
    return {
        "child_id": child_id,
        "status": child_runs[child_id]["status"],
        "task_name": child_runs[child_id]["task_name"],
        "result": child_runs[child_id]["result"]
    }


async def process_child_run(child_id: str, task_name: str, parameters: Dict[str, Any]) -> None:
    """
    Process a child run asynchronously.
    
    Args:
        child_id: ID of the child run
        task_name: Name of the task
        parameters: Parameters for the task
    """
    # Simulate processing time
    await asyncio.sleep(2)
    
    # Update status to completed
    child_runs[child_id]["status"] = "completed"
    
    # Set result based on task
    if task_name == "echo":
        child_runs[child_id]["result"] = {
            "message": f"Echo: {parameters.get('message', 'No message provided')}"
        }
    elif task_name == "calculate":
        a = parameters.get("a", 0)
        b = parameters.get("b", 0)
        operation = parameters.get("operation", "add")
        
        result = None
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            result = a / b if b != 0 else "Error: Division by zero"
        
        child_runs[child_id]["result"] = {
            "operation": operation,
            "a": a,
            "b": b,
            "result": result
        }
    else:
        child_runs[child_id]["result"] = {
            "message": f"Unknown task: {task_name}"
        }


def main():
    """Main function to run the MCP server."""
    print("Starting test MCP server for child run integration testing")
    
    # Run the MCP server
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()

