#!/usr/bin/env python3
"""
Simple MCP client test for graph-sitter integration
"""

import asyncio
import json
import subprocess
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio.stdio_client import create_stdio_client

async def main():
    # Start the MCP server as a subprocess
    server_process = subprocess.Popen(
        ["python", "test_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Give the server a moment to start
    await asyncio.sleep(1)
    
    # Create an MCP client
    client = await create_stdio_client(process=server_process)
    session = ClientSession(client)
    
    try:
        # Initialize the session
        await session.initialize()
        
        # Get the manifest
        manifest = await session.get_resource("system://manifest")
        print(f"Manifest: {json.dumps(manifest, indent=2)}")
        
        # Call the hello_world tool
        result = await session.call_tool("hello_world", {"name": "MCP Integration Test"})
        print(f"Tool result: {result}")
        
        print("\nMCP server integration test successful! 🎉")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        await session.close()
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    asyncio.run(main())

