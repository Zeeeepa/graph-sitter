from mcp.server.fastmcp import FastMCP

print("Starting test MCP server...")

# Create a FastMCP server
mcp = FastMCP("test-mcp", instructions="Test MCP server")

# Register a tool
@mcp.tool()
def hello_world():
    """Say hello to the world."""
    return "Hello, world!"

# Start the server
if __name__ == "__main__":
    mcp.run(transport="stdio")

