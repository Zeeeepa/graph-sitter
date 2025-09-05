from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("test-mcp", instructions="This is a test MCP server for validation.")

# Add a simple tool
@mcp.tool()
def hello_world(name: str = "World") -> str:
    """Say hello to the world or a specific name."""
    return f"Hello, {name}!"

# Add a simple resource
@mcp.resource("system://greeting", description="A simple greeting", mime_type="text/plain")
def get_greeting() -> str:
    """Get a simple greeting."""
    return "Welcome to the test MCP server!"

if __name__ == "__main__":
    # Initialize and run the server
    print("Starting test MCP server...")
    # Use HTTP transport for easier testing
    mcp.run(transport="http", host="127.0.0.1", port=8001)
