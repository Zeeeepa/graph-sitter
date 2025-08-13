import asyncio
from typing import Annotated

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(
    "test-mcp-server",
    instructions="This is a test MCP server for graph-sitter.",
)

@mcp.tool(name="hello_world", description="A simple hello world tool")
def hello_world(name: Annotated[str, "Your name"]) -> str:
    return f"Hello, {name}!"

@mcp.resource("system://manifest", mime_type="application/json")
def get_service_config() -> dict:
    """Get the service config."""
    return {
        "name": "test-mcp-server",
        "version": "0.1.0",
        "description": "A test MCP server for graph-sitter.",
    }

if __name__ == "__main__":
    # Initialize and run the server
    print("Starting test MCP server...")
    mcp.run(transport="stdio")

