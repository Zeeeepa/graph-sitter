# MCP Server Child Run Integration Test

This directory contains test scripts for testing child run functionality in MCP (Model Context Protocol) server integration.

## Overview

The test consists of two main components:

1. **MCP Server** (`test_mcp_child_run.py`): A simple MCP server implementation that provides tools for starting and monitoring child runs.
2. **MCP Client** (`test_mcp_client.py`): A client that interacts with the MCP server to test child run functionality.

## Prerequisites

Before running the tests, ensure you have the following installed:

- Python 3.7 or higher
- MCP server package: `pip install mcp-server`

## Running the Tests

You can run the tests in two ways:

### Method 1: Run the client script directly

The client script will automatically start the server in a subprocess:

```bash
python test_mcp_client.py
```

### Method 2: Run server and client separately

1. Start the MCP server in one terminal:

```bash
python test_mcp_child_run.py
```

2. In another terminal, run the client (you'll need to modify the client to connect to the running server):

```bash
# Modify test_mcp_client.py to connect to the running server
python test_mcp_client.py
```

## Test Functionality

The test demonstrates the following functionality:

1. Starting child runs with different tasks and parameters
2. Monitoring the status of child runs
3. Retrieving results from completed child runs

## Child Run Tasks

The test includes two example tasks:

1. **Echo Task**: Simply echoes back a message provided in the parameters.
2. **Calculate Task**: Performs a mathematical operation (add, subtract, multiply, divide) on two numbers.

## Extending the Tests

You can extend the tests by:

1. Adding new task types to the `process_child_run` function in `test_mcp_child_run.py`
2. Adding more complex child run scenarios in `test_mcp_client.py`
3. Implementing error handling and recovery tests

## Integration with Graph-Sitter

To integrate these tests with Graph-Sitter's MCP server implementation:

1. Replace the simple MCP server with Graph-Sitter's MCP server
2. Modify the client to use Graph-Sitter's specific tools and parameters
3. Add assertions to verify expected behavior

## Troubleshooting

If you encounter issues:

- Ensure the MCP server package is installed correctly
- Check that the server is running and accessible
- Verify that the client is sending properly formatted requests
- Check for any error messages in the server or client output

