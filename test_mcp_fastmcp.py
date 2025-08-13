from mcp.server.fastmcp import FastMCP

# Create a FastMCP server
mcp_server = FastMCP("test-mcp", instructions="Test MCP server")

# Register a tool
@mcp_server.tool()
def hello_world():
    """Say hello to the world."""
    return "Hello, world!"

# Start the server
if __name__ == "__main__":
    print("Starting FastMCP server with stdio transport...")
    mcp_server.run(transport="stdio")

