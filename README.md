# MCP Orchestrator

This repository contains a Python implementation of an MCP (Model Context Protocol) orchestrator. The orchestrator allows you to start MCP servers, create clients to interact with them, and call tools provided by the servers.

## Overview

The MCP Orchestrator consists of three main components:

1. **MCPServer**: A class to manage an MCP server process.
2. **MCPClient**: A class to interact with an MCP server.
3. **MCPOrchestrator**: A class to orchestrate MCP servers and clients.

## Usage

### Basic Usage

```python
import asyncio
from mcp_orchestrator import MCPOrchestrator

async def main():
    # Create an orchestrator
    orchestrator = MCPOrchestrator()
    
    try:
        # Start a server
        await orchestrator.start_server("my-server", "python", ["my_mcp_server.py"])
        
        # Create a client
        orchestrator.create_client("my-client", "my-server")
        
        # Initialize the client
        result = await orchestrator.initialize_client("my-client")
        print(f"Initialization result: {result}")
        
        # List the tools
        tools = await orchestrator.list_tools("my-client")
        print(f"Tools: {tools}")
        
        # Call a tool
        result = await orchestrator.call_tool("my-client", "my-tool", {"arg1": "value1"})
        print(f"Tool result: {result}")
    
    finally:
        # Stop all servers
        await orchestrator.stop_all_servers()

if __name__ == "__main__":
    asyncio.run(main())
```

### Creating a Custom MCP Server

You can create a custom MCP server by implementing the JSON-RPC protocol. Here's a simple example:

```python
import json
import sys

def handle_message(message):
    """Handle a JSON-RPC message."""
    try:
        # Parse the message
        request = json.loads(message)
        
        # Get the method
        method = request.get("method")
        
        # Handle the method
        if method == "initialize":
            # Initialize the server
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2025-06-18",
                    "name": "my-mcp",
                    "instructions": "My MCP server",
                    "capabilities": {}
                }
            }
        elif method == "tools/list":
            # List the tools
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "my-tool",
                            "title": "My Tool",
                            "description": "My tool description."
                        }
                    ]
                }
            }
        elif method == "tools/call":
            # Call a tool
            tool_name = request.get("params", {}).get("name")
            if tool_name == "my-tool":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "result": "My tool result!"
                    }
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
        else:
            # Unknown method
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        # Send the response
        response_json = json.dumps(response)
        content_length = len(response_json)
        sys.stdout.write(f"Content-Length: {content_length}\r\n\r\n")
        sys.stdout.write(response_json)
        sys.stdout.flush()
    
    except Exception as e:
        # Send an error response
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
        response_json = json.dumps(error_response)
        content_length = len(response_json)
        sys.stdout.write(f"Content-Length: {content_length}\r\n\r\n")
        sys.stdout.write(response_json)
        sys.stdout.flush()

# Start the server
if __name__ == "__main__":
    print("Starting MCP server...", file=sys.stderr)
    
    # Read messages from stdin
    headers = {}
    content_length = 0
    
    while True:
        try:
            # Read headers
            line = sys.stdin.readline().strip()
            if not line:
                # End of headers
                if content_length > 0:
                    # Read the content
                    content = sys.stdin.read(content_length)
                    
                    # Handle the message
                    handle_message(content)
                    
                    # Reset headers and content length
                    headers = {}
                    content_length = 0
            elif ":" in line:
                # Parse header
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
                
                # Check for Content-Length
                if key.strip().lower() == "content-length":
                    content_length = int(value.strip())
        
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
```

## API Reference

### MCPServer

- `__init__(command, args)`: Initialize the server.
- `start()`: Start the server process.
- `stop()`: Stop the server process.
- `send_message(message)`: Send a message to the server.
- `read_message()`: Read a message from the server.

### MCPClient

- `__init__(server)`: Initialize the client.
- `next_request_id()`: Get the next request ID.
- `initialize()`: Initialize the client.
- `list_tools()`: List the available tools.
- `call_tool(name, arguments=None)`: Call a tool.

### MCPOrchestrator

- `__init__()`: Initialize the orchestrator.
- `start_server(name, command, args)`: Start a server.
- `stop_server(name)`: Stop a server.
- `stop_all_servers()`: Stop all servers.
- `create_client(name, server_name)`: Create a client.
- `initialize_client(name)`: Initialize a client.
- `list_tools(name)`: List the tools for a client.
- `call_tool(name, tool_name, arguments=None)`: Call a tool for a client.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

