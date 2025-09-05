import asyncio
import subprocess
import time
import mcp
import traceback
import sys
from mcp.client.stdio import StdioServerParameters

async def main():
    """Main function to test the MCP stdio client."""
    print("Starting MCP simple test...")
    
    try:
        # Create the server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["test_mcp_server.py"],
            encoding="utf-8"
        )
        
        # Print the server parameters
        print(f"Server parameters: {server_params}")
        
        # Create the client
        print("Creating client...")
        client_context = mcp.stdio_client(server_params)
        print(f"Client context: {client_context}")
        
        print("Test completed successfully.")
    
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    
    finally:
        print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

