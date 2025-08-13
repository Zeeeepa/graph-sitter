import asyncio
import json
import logging
import subprocess
import sys
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_client")

class MCPClient:
    def __init__(self, server_process: subprocess.Popen):
        self.server_process = server_process
        self.next_id = 1
        self.initialized = False
        self.server_info = None
        self.capabilities = None
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the client."""
        # Read and discard the startup message
        startup_message = self.server_process.stdout.readline()
        logger.info(f"Server startup message: {startup_message.strip()}")
        
        # Initialize the client
        init_request = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": "initialize",
            "params": {
                "capabilities": {
                    "tools": {
                        "include_context": True
                    },
                    "resources": {
                        "include_context": True
                    },
                    "prompts": {
                        "include_context": True
                    }
                },
                "client_info": {
                    "name": "mcp-client",
                    "version": "0.1.0"
                }
            }
        }
        self.next_id += 1
        
        response = await self._send_request(init_request)
        
        if "result" in response:
            self.server_info = response["result"].get("server_info")
            self.capabilities = response["result"].get("capabilities")
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "initialized",
                "params": {}
            }
            
            await self._send_notification(initialized_notification)
            self.initialized = True
            
            logger.info(f"Initialized client with server: {self.server_info}")
        
        return response
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        if not self.initialized:
            raise RuntimeError("Client not initialized")
        
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": "mcp/listTools",
            "params": {}
        }
        self.next_id += 1
        
        response = await self._send_request(list_tools_request)
        
        if "result" in response:
            tools = response["result"].get("tools", [])
            logger.info(f"Available tools: {[tool['name'] for tool in tools]}")
        
        return response
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool."""
        if not self.initialized:
            raise RuntimeError("Client not initialized")
        
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
        
        response = await self._send_request(tool_request)
        
        if "result" in response:
            logger.info(f"Tool {tool_name} result: {response['result']}")
        
        return response
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources."""
        if not self.initialized:
            raise RuntimeError("Client not initialized")
        
        list_resources_request = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": "mcp/listResources",
            "params": {}
        }
        self.next_id += 1
        
        response = await self._send_request(list_resources_request)
        
        if "result" in response:
            resources = response["result"].get("resources", [])
            logger.info(f"Available resources: {[resource['path'] for resource in resources]}")
        
        return response
    
    async def read_resource(self, path: str) -> Dict[str, Any]:
        """Read a resource."""
        if not self.initialized:
            raise RuntimeError("Client not initialized")
        
        read_resource_request = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": "mcp/readResource",
            "params": {
                "path": path
            }
        }
        self.next_id += 1
        
        response = await self._send_request(read_resource_request)
        
        if "result" in response:
            logger.info(f"Resource {path} content type: {response['result'].get('mime_type')}")
        
        return response
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the server and wait for a response."""
        self.server_process.stdin.write(json.dumps(request) + "\n")
        self.server_process.stdin.flush()
        
        response = self.server_process.stdout.readline()
        logger.debug(f"Response: {response.strip()}")
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse response: {response}")
            return {
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
    
    async def _send_notification(self, notification: Dict[str, Any]) -> None:
        """Send a notification to the server."""
        self.server_process.stdin.write(json.dumps(notification) + "\n")
        self.server_process.stdin.flush()
    
    async def close(self) -> None:
        """Close the client and terminate the server."""
        self.server_process.terminate()
        self.server_process.wait()

async def main():
    # Start the MCP server in a subprocess
    server_process = subprocess.Popen(
        ["python", "final_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Give the server a moment to start
    await asyncio.sleep(1)
    
    client = MCPClient(server_process)
    
    try:
        # Initialize the client
        await client.initialize()
        
        # List available tools
        tools_response = await client.list_tools()
        
        # Call the hello_world tool
        hello_result = await client.call_tool("hello_world", {"name": "Graph-sitter"})
        print(f"Hello world result: {hello_result.get('result')}")
        
        # Call the parse_code tool
        parse_result = await client.call_tool("parse_code", {
            "code": "def hello(): print('Hello, world!')",
            "language": "python"
        })
        print(f"Parse code result: {parse_result.get('result')}")
        
        # List available resources
        resources_response = await client.list_resources()
        
        # Read the manifest resource
        manifest_response = await client.read_resource("system://manifest")
        print(f"Manifest: {manifest_response.get('result', {}).get('content')}")
        
    except Exception as e:
        logger.exception(f"Error: {e}")
    finally:
        # Close the client
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())

