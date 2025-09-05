import subprocess
import time
import threading
import json
import sys
import os
import asyncio
from mcp.client.session import ClientSession

async def main():
    """Main function to test the MCP client session."""
    print("Starting MCP client session test...")
    
    # Start the server
    server_process = subprocess.Popen(
        ["python", "test_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    print("Server started.")
    
    # Wait for the server to initialize
    await asyncio.sleep(2)
    
    try:
        # Create the client session
        session = ClientSession(
            request_responder=None,  # We'll handle this manually
            client_info={
                "name": "test-client",
                "version": "0.1.0"
            }
        )
        
        # Initialize the session
        await session.initialize()
        print("Session initialized.")
        
        # List the tools
        tools = await session.list_tools()
        print(f"Tools: {tools}")
        
        # Call the hello_world tool
        result = await session.call_tool("hello_world")
        print(f"Tool result: {result}")
        
        print("Test completed successfully.")
    
    finally:
        # Stop the server
        server_process.terminate()
        await asyncio.sleep(1)
        print("Server stopped.")

if __name__ == "__main__":
    asyncio.run(main())

