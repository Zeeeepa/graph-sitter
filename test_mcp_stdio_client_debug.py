import asyncio
import mcp
from mcp.client.stdio import StdioServerParameters
from mcp.client.session import ClientSession
import traceback

async def main():
    """Main function to test the MCP stdio client with a debug server."""
    print("Starting MCP stdio client test...")
    
    try:
        # Create the server parameters with debug enabled
        server_params = StdioServerParameters(
            command="python",
            args=["test_mcp_fastmcp.py"],
            encoding="utf-8"
        )
        
        # Create the client
        try:
            async with mcp.stdio_client(server_params) as client:
                # The client is a tuple of (read_stream, write_stream)
                await client.initialize()
        except Exception as e:
            print(f"Client error: {e}")
    
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    
    finally:
        print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

