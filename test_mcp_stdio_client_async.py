import asyncio
import subprocess
import time
import mcp
from mcp.client.stdio import StdioServerParameters

async def main():
    """Main function to test the MCP stdio client."""
    print("Starting MCP stdio client test...")
    
    try:
        # Create the server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["test_mcp_server.py"],
            encoding="utf-8"
        )
        
        # Create the client
        async with mcp.stdio_client(server_params) as client:
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
        print(f"Error: {e}")
    
    finally:
        print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

