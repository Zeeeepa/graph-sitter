#!/bin/bash
# Script to run MCP server integration tests

set -e

echo "=== MCP Server Child Run Integration Tests ==="
echo

# Check if required packages are installed
echo "Checking required packages..."
python -c "import mcp.server.fastmcp" 2>/dev/null || {
    echo "Error: mcp package not installed. Please install it with:"
    echo "pip install mcp-server"
    exit 1
}

python -c "import graph_sitter" 2>/dev/null || {
    echo "Error: graph_sitter package not installed. Please install it with:"
    echo "pip install graph-sitter"
    exit 1
}

echo "Required packages found."
echo

# Run the client test
echo "=== Running MCP Client Test ==="
python test_mcp_client.py
echo

# Run the Graph-Sitter integration test
echo "=== Running Graph-Sitter MCP Integration Test ==="
python test_graph_sitter_mcp_child_run.py
echo

echo "All tests completed."

