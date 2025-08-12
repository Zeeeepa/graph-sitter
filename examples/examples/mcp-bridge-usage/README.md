# MCP Bridge Usage Example

This example demonstrates how to use the Serena MCP Bridge to interact with an MCP server.

## Overview

The Serena MCP Bridge provides a bridge between Serena's MCP server implementation and graph-sitter's codebase analysis system. It allows you to:

1. Initialize an MCP server
2. Discover available tools
3. Call tools on the server
4. Handle tool results and errors
5. Properly shut down the server

## Prerequisites

- Python 3.8+
- graph-sitter installed
- Serena MCP server (installed via `uvx` or directly)

## Running the Example

```bash
# Run with the current directory as the repository path
python mcp_bridge_example.py

# Or specify a repository path
python mcp_bridge_example.py /path/to/your/repo
```

## How It Works

The example demonstrates:

1. Initializing the MCP bridge with a repository path
2. Checking if the bridge initialized successfully
3. Discovering available tools from the MCP server
4. Checking if a specific tool is available
5. Calling a tool and handling the result
6. Properly shutting down the bridge

## Key Components

### SerenaMCPBridge

The main class that handles communication with the MCP server:

```python
from graph_sitter.extensions.lsp.serena.mcp_bridge import SerenaMCPBridge

# Initialize the bridge
bridge = SerenaMCPBridge(repo_path)

# Get available tools
tools = bridge.get_available_tools()

# Check if a tool is available
is_available = bridge.is_tool_available("tool_name")

# Call a tool
result = bridge.call_tool("tool_name", {"param1": "value1"})

# Shutdown the bridge
bridge.shutdown()
```

### MCPToolResult

Represents the result of a tool call:

```python
# Check if the tool call was successful
if result.success:
    # Access the content
    content = result.content
else:
    # Handle the error
    error = result.error
```

## Integration with Graph-Sitter

The MCP bridge can be used to enhance graph-sitter's capabilities by providing access to additional tools through the MCP server. This allows for more advanced code analysis, refactoring, and other operations that may not be available directly in graph-sitter.

## Error Handling

The example demonstrates proper error handling for:

1. Bridge initialization failures
2. Tool discovery issues
3. Tool call failures
4. Proper cleanup with `finally` block

## Next Steps

- Explore the available tools in the MCP server
- Integrate the MCP bridge into your own applications
- Extend the bridge with additional functionality
- Create custom MCP servers with specialized tools

