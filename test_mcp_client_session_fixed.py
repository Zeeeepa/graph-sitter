import asyncio
import subprocess
import time
import mcp
import traceback
import sys
from mcp.client.stdio import StdioServerParameters
from mcp import ClientSession

async def main():
    """Main function to test the MCP client session."""
    print("Starting MCP client session test...")
    
    try:
        # Create the server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["test_mcp_server.py"],
            encoding="utf-8"
        )
        
        # Create the client
        try:
            async with mcp.stdio_client(server_params) as (read_stream, write_stream):
                # Create a client session
                client = ClientSession(read_stream, write_stream)
                
                # Initialize the client
                await client.initialize()
                print("Client initialized.")
                
                # List the tools
                tools = await client.list_tools()
                print(f"Tools: {tools}")
                
                # Call the hello_world tool
                result = await client.call_tool("hello_world")
                print(f"Tool result: {result}")
                
                print("Test completed successfully.")
        except Exception as e:
            print(f"Client error: {e}")
            traceback.print_exc()
    
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    
    finally:
        print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

