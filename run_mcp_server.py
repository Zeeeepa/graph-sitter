#!/usr/bin/env python3
"""
Run MCP server for testing
"""

import asyncio
import sys
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(
    "test-mcp-server",
    instructions="This is a test MCP server for graph-sitter integration validation."
)

@mcp.tool(name="hello_world", description="A simple hello world tool")
def hello_world(name: str = "World") -> str:
    """Return a hello world message."""
    return f"Hello, {name}!"

@mcp.resource("system://manifest", mime_type="application/json")
def get_service_config() -> dict:
    """Get the service config."""
    return {
        "name": "test-mcp-server",
        "version": "0.1.0",
        "description": "Test MCP server for graph-sitter integration validation.",
    }

async def main():
    # Initialize and run the server
    print("Starting test MCP server...")
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())

