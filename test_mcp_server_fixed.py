from mcp.server.fastmcp import FastMCP
import json
import sys

# Create a FastMCP server
mcp_server = FastMCP("test-mcp", instructions="Test MCP server")

# Register a tool
@mcp_server.tool()
def hello_world():
    """Say hello to the world."""
    return "Hello, world!"

# Handle JSON-RPC messages manually
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
                    "name": "test-mcp",
                    "instructions": "Test MCP server",
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
                            "name": "hello_world",
                            "title": "Hello World",
                            "description": "Say hello to the world."
                        }
                    ]
                }
            }
        elif method == "tools/call":
            # Call a tool
            tool_name = request.get("params", {}).get("name")
            if tool_name == "hello_world":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "result": "Hello, world!"
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
    print("Starting MCP server with manual JSON-RPC handling...", file=sys.stderr)
    
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

