from mcp.server.fastmcp import FastMCP
import asyncio
import mcp

print("Starting test MCP stdio server...")

# Create a FastMCP server
mcp_server = FastMCP("test-mcp", instructions="Test MCP server")

# Register a tool
@mcp_server.tool()
def hello_world():
    """Say hello to the world."""
    return "Hello, world!"

# Start the server
async def main():
    print("Running stdio server...")
    await mcp_server.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())

