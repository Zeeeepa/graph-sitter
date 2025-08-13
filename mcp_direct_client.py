import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, Optional

import mcp
from mcp.client.session import ClientSession
from mcp.types import ClientCapabilities, ToolsCapability, ResourcesCapability, PromptsCapability

class StdioClient:
    def __init__(self, server_process: subprocess.Popen):
        self.server_process = server_process
        self.next_id = 1
        
    async def initialize(self) -> Dict[str, Any]:
        # Read and discard the startup message
        startup_message = self.server_process.stdout.readline()
        print(f"Server startup message: {startup_message}")
        
        # Initialize the client
        capabilities = ClientCapabilities(
            tools=ToolsCapability(include_context=True),
            resources=ResourcesCapability(include_context=True),
            prompts=PromptsCapability(include_context=True)
        )
        
        init_request = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": "initialize",
            "params": {
                "capabilities": capabilities.model_dump()
            }
        }
        self.next_id += 1
        
        # Send the initialization request
        self.server_process.stdin.write(json.dumps(init_request) + "\n")
        self.server_process.stdin.flush()
        
        # Read the initialization response
        init_response = self.server_process.stdout.readline()
        print(f"Initialization response: {init_response}")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        self.server_process.stdin.write(json.dumps(initialized_notification) + "\n")
        self.server_process.stdin.flush()
        
        try:
            return json.loads(init_response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse initialization response"}
    
    async def list_tools(self) -> Dict[str, Any]:
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": "mcp/listTools",
            "params": {}
        }
        self.next_id += 1
        
        self.server_process.stdin.write(json.dumps(list_tools_request) + "\n")
        self.server_process.stdin.flush()
        
        list_tools_response = self.server_process.stdout.readline()
        print(f"List tools response: {list_tools_response}")
        
        try:
            return json.loads(list_tools_response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse list tools response"}
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        tool_request = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": "mcp/callTool",
            "params": {
                "tool": tool_name,
                "parameters": parameters
            }
        }
        self.next_id += 1
        
        self.server_process.stdin.write(json.dumps(tool_request) + "\n")
        self.server_process.stdin.flush()
        
        tool_response = self.server_process.stdout.readline()
        print(f"Tool response: {tool_response}")
        
        try:
            return json.loads(tool_response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse tool response"}
    
    async def close(self):
        self.server_process.terminate()
        self.server_process.wait()

async def main():
    # Start the MCP server in a subprocess
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
    
    client = StdioClient(server_process)
    
    try:
        # Initialize the client
        await client.initialize()
        
        # List available tools
        await client.list_tools()
        
        # Call the hello_world tool
        result = await client.call_tool("hello_world", {"name": "Graph-sitter"})
        print(f"Hello world result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the client
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())

