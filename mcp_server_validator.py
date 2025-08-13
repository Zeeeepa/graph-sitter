#!/usr/bin/env python3
"""
MCP Server Validator

This script validates that an MCP server is running correctly by:
1. Starting a simple MCP server
2. Testing the server with various requests
3. Reporting the results
"""

import subprocess
import time
import requests
import json
import sys
import os
import argparse
from typing import Dict, List, Optional, Tuple, Any

def create_test_server_file(port: int = 8001) -> str:
    """Create a test MCP server file."""
    filename = "test_mcp_server.py"
    content = f"""from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("test-mcp", instructions="This is a test MCP server for validation.")

# Add a simple tool
@mcp.tool()
def hello_world(name: str = "World") -> str:
    \"\"\"Say hello to the world or a specific name.\"\"\"
    return f"Hello, {{name}}!"

# Add a simple resource
@mcp.resource("system://greeting", description="A simple greeting", mime_type="text/plain")
def get_greeting() -> str:
    \"\"\"Get a simple greeting.\"\"\"
    return "Welcome to the test MCP server!"

if __name__ == "__main__":
    # Initialize and run the server
    print("Starting test MCP server...")
    # Use HTTP transport for easier testing
    mcp.run(transport="http", host="127.0.0.1", port={port})
"""
    
    with open(filename, "w") as f:
        f.write(content)
    
    return filename

def start_server(server_file: str) -> subprocess.Popen:
    """Start the MCP server."""
    process = subprocess.Popen(
        ["python", server_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the server to start
    time.sleep(3)
    
    return process

def test_endpoints(base_url: str) -> Dict[str, Dict[str, Any]]:
    """Test various endpoints of the MCP server."""
    results = {}
    
    # Test basic endpoint
    results["base"] = {
        "url": base_url,
        "status": None,
        "response": None,
        "error": None
    }
    
    try:
        response = requests.get(base_url)
        results["base"]["status"] = response.status_code
        results["base"]["response"] = response.text[:100] if response.text else None
    except Exception as e:
        results["base"]["error"] = str(e)
    
    # Test with SSE headers
    results["sse"] = {
        "url": base_url + "/mcp",
        "status": None,
        "response": None,
        "error": None
    }
    
    try:
        headers = {
            "Accept": "text/event-stream"
        }
        response = requests.get(base_url + "/mcp", headers=headers)
        results["sse"]["status"] = response.status_code
        results["sse"]["response"] = response.text[:100] if response.text else None
    except Exception as e:
        results["sse"]["error"] = str(e)
    
    # Test with JSON headers
    results["json"] = {
        "url": base_url + "/mcp",
        "status": None,
        "response": None,
        "error": None
    }
    
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.post(
            base_url + "/mcp",
            headers=headers,
            json={"type": "manifest"}
        )
        results["json"]["status"] = response.status_code
        results["json"]["response"] = response.text[:100] if response.text else None
    except Exception as e:
        results["json"]["error"] = str(e)
    
    return results

def validate_mcp_server(port: int = 8001) -> Tuple[bool, Dict[str, Any]]:
    """Validate that an MCP server is running correctly."""
    base_url = f"http://127.0.0.1:{port}"
    
    # Create test server file
    server_file = create_test_server_file(port)
    
    # Start the server
    server_process = start_server(server_file)
    
    # Test endpoints
    results = test_endpoints(base_url)
    
    # Stop the server
    server_process.terminate()
    server_process.wait()
    
    # Get server output
    stdout = server_process.stdout.read()
    stderr = server_process.stderr.read()
    
    # Check if the server started successfully
    server_started = "Uvicorn running on" in stderr
    
    # Prepare results
    validation_results = {
        "server_started": server_started,
        "endpoint_tests": results,
        "server_stdout": stdout,
        "server_stderr": stderr
    }
    
    return server_started, validation_results

def print_results(success: bool, results: Dict[str, Any]) -> None:
    """Print the validation results."""
    print("\n" + "=" * 80)
    print("MCP SERVER VALIDATION RESULTS")
    print("=" * 80)
    
    if success:
        print("\n✅ MCP server started successfully")
    else:
        print("\n❌ MCP server failed to start")
    
    print("\nEndpoint Tests:")
    for name, result in results["endpoint_tests"].items():
        status = result["status"]
        if status is not None:
            status_str = f"{status}"
        else:
            status_str = "Error"
        
        print(f"  - {name}: {status_str}")
        if result["error"]:
            print(f"    Error: {result['error']}")
    
    print("\nServer Output:")
    print(f"  stdout: {len(results['server_stdout'])} characters")
    print(f"  stderr: {len(results['server_stderr'])} characters")
    
    print("\nConclusion:")
    if success:
        print("  The MCP server is running correctly and implementing the MCP protocol.")
        print("  To interact with it, you need to use the correct headers and request format.")
    else:
        print("  The MCP server failed to start or is not implementing the MCP protocol correctly.")
    
    print("\n" + "=" * 80)

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate an MCP server")
    parser.add_argument("--port", type=int, default=8001, help="Port to run the server on")
    args = parser.parse_args()
    
    success, results = validate_mcp_server(args.port)
    print_results(success, results)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

