# Graph-sitter MCP Server

This repository contains a Model Context Protocol (MCP) server implementation for graph-sitter, allowing AI agents to interact with the graph-sitter codebase analysis tools.

## Overview

The MCP (Model Context Protocol) is a standardized protocol for AI agents to interact with external tools and resources. This implementation provides a simple MCP server that exposes graph-sitter functionality to AI agents.

## Files

- `final_mcp_server.py`: A complete MCP server implementation with support for tools and resources
- `final_mcp_client.py`: A client implementation to interact with the MCP server
- `debug_mcp_server.py`: A debug version of the MCP server with detailed logging
- `debug_mcp_client.py`: A debug client for testing the MCP server
- `test_mcp_server.py`: A minimal MCP server for testing
- `simple_mcp_client.py`: A simple client implementation
- `minimal_mcp_client.py`: A minimal client implementation
- `mcp_direct_client.py`: A client using the MCP module directly
- `complete_mcp_client.py`: A more complete client implementation

## Features

The MCP server provides the following features:

- Tool execution: Execute graph-sitter tools like code parsing and analysis
- Resource access: Access resources like configuration and documentation
- JSON-RPC protocol: Standard JSON-RPC 2.0 protocol for communication

## Available Tools

- `hello_world`: A simple hello world tool for testing
- `parse_code`: Parse code using graph-sitter

## Available Resources

- `system://manifest`: Get the service configuration

## Usage

### Running the Server

```bash
python final_mcp_server.py
```

### Running the Client

```bash
python final_mcp_client.py
```

## Protocol

The MCP server implements the JSON-RPC 2.0 protocol with the following methods:

- `initialize`: Initialize the client-server connection
- `initialized`: Notification that initialization is complete
- `mcp/listTools`: List available tools
- `mcp/callTool`: Call a tool with parameters
- `mcp/listResources`: List available resources
- `mcp/readResource`: Read a resource

## Example

Here's an example of calling the `hello_world` tool:

```python
# Initialize the client
client = MCPClient(server_process)
await client.initialize()

# Call the hello_world tool
result = await client.call_tool("hello_world", {"name": "Graph-sitter"})
print(f"Result: {result.get('result')}")  # Output: "Hello, Graph-sitter!"
```

## Integration with AI Agents

This MCP server can be integrated with AI agents like Claude Code, Cursor, or other MCP-compatible agents to provide graph-sitter functionality for code analysis and manipulation.

## Development

To extend the MCP server with additional tools, add new functions with the `@server.tool` decorator:

```python
@server.tool(name="new_tool", description="Description of the new tool")
def new_tool(param1: Annotated[str, "Parameter description"]) -> str:
    # Tool implementation
    return "Result"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

