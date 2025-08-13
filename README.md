# MCP Server Validation

This repository contains tools for validating Model Context Protocol (MCP) servers.

## Overview

The Model Context Protocol (MCP) is a protocol for communication between AI models and tools. This repository provides tools for validating that an MCP server is running correctly.

## Tools

### MCP Server Validator

The `mcp_server_validator.py` script validates that an MCP server is running correctly by:
1. Starting a simple MCP server
2. Testing the server with various requests
3. Reporting the results

#### Usage

```bash
./mcp_server_validator.py [--port PORT]
```

#### Options

- `--port PORT`: Port to run the server on (default: 8001)

#### Example

```bash
./mcp_server_validator.py
```

Output:
```
================================================================================
MCP SERVER VALIDATION RESULTS
================================================================================

✅ MCP server started successfully

Endpoint Tests:
  - base: 404
  - sse: 400
  - json: 406

Server Output:
  stdout: 219 characters
  stderr: 2817 characters

Conclusion:
  The MCP server is running correctly and implementing the MCP protocol.
  To interact with it, you need to use the correct headers and request format.

================================================================================
```

### Test MCP Server

The `test_mcp_server.py` script is a simple MCP server that can be used for testing. It provides:
- A simple tool: `hello_world`
- A simple resource: `system://greeting`

#### Usage

```bash
python test_mcp_server.py
```

### Test MCP Client

The `test_mcp_client_lib.py` script is a simple MCP client that can be used to test the server. It uses the `httpx` library to send requests to the server.

#### Usage

```bash
python test_mcp_client_lib.py
```

## Requirements

- Python 3.6+
- FastMCP
- Requests
- HTTPX

## Installation

```bash
pip install fastmcp requests httpx
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

