import asyncio
import subprocess
import time
import mcp
import traceback
import sys
from mcp.client.stdio import StdioServerParameters

async def main():
    """Main function to test the MCP stdio client with a context manager."""
    print("Starting MCP context test...")
    
    try:
        # Create the server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["test_mcp_server.py"],
            encoding="utf-8"
        )
        
        # Create the client
        print("Creating client...")
        async with mcp.stdio_client(server_params) as (read_stream, write_stream):
            print(f"Read stream: {read_stream}")
            print(f"Write stream: {write_stream}")
            
            # Create a client session
            print("Creating client session...")
            client = mcp.ClientSession(read_stream, write_stream)
            print(f"Client: {client}")
            
            print("Test completed successfully.")
    
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    
    finally:
        print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

