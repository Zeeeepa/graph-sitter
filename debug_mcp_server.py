import asyncio
import json
import logging
import sys
from typing import Annotated, Dict, Any

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_mcp_server")

# Initialize FastMCP server
mcp = FastMCP(
    "debug-mcp-server",
    instructions="This is a debug MCP server for graph-sitter.",
)

@mcp.tool(name="hello_world", description="A simple hello world tool")
def hello_world(name: Annotated[str, "Your name"]) -> str:
    logger.debug(f"hello_world tool called with name: {name}")
    return f"Hello, {name}!"

@mcp.resource("system://manifest", mime_type="application/json")
def get_service_config() -> dict:
    """Get the service config."""
    logger.debug("get_service_config resource called")
    return {
        "name": "debug-mcp-server",
        "version": "0.1.0",
        "description": "A debug MCP server for graph-sitter.",
    }

# Custom handler for stdin/stdout
async def handle_stdio():
    logger.debug("Starting stdio handler")
    
    # Read from stdin
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                logger.debug("Empty line received, exiting")
                break
                
            logger.debug(f"Received: {line.strip()}")
            
            try:
                request = json.loads(line)
                logger.debug(f"Parsed request: {request}")
                
                # Handle the request
                if request.get("method") == "initialize":
                    logger.debug("Handling initialize request")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "capabilities": {
                                "tools": {},
                                "resources": {},
                                "prompts": {}
                            },
                            "server_info": {
                                "name": "debug-mcp-server",
                                "version": "0.1.0"
                            }
                        }
                    }
                    print(json.dumps(response), flush=True)
                    logger.debug(f"Sent response: {response}")
                    
                elif request.get("method") == "initialized":
                    logger.debug("Handling initialized notification")
                    # No response needed for notifications
                    
                elif request.get("method") == "mcp/listTools":
                    logger.debug("Handling listTools request")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "tools": [
                                {
                                    "name": "hello_world",
                                    "description": "A simple hello world tool",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "name": {
                                                "type": "string",
                                                "description": "Your name"
                                            }
                                        },
                                        "required": ["name"]
                                    },
                                    "returns": {
                                        "type": "string"
                                    }
                                }
                            ]
                        }
                    }
                    print(json.dumps(response), flush=True)
                    logger.debug(f"Sent response: {response}")
                    
                elif request.get("method") == "mcp/callTool":
                    logger.debug("Handling callTool request")
                    params = request.get("params", {})
                    tool_name = params.get("tool")
                    parameters = params.get("parameters", {})
                    
                    if tool_name == "hello_world":
                        name = parameters.get("name", "World")
                        result = f"Hello, {name}!"
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": result
                        }
                        print(json.dumps(response), flush=True)
                        logger.debug(f"Sent response: {response}")
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "error": {
                                "code": -32601,
                                "message": f"Tool not found: {tool_name}"
                            }
                        }
                        print(json.dumps(response), flush=True)
                        logger.debug(f"Sent error response: {response}")
                        
                else:
                    logger.debug(f"Unknown method: {request.get('method')}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {request.get('method')}"
                        }
                    }
                    print(json.dumps(response), flush=True)
                    logger.debug(f"Sent error response: {response}")
                    
            except json.JSONDecodeError:
                logger.debug(f"Failed to parse JSON: {line.strip()}")
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(response), flush=True)
                logger.debug(f"Sent error response: {response}")
                
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(response), flush=True)
            logger.debug(f"Sent error response: {response}")

if __name__ == "__main__":
    # Initialize and run the server
    print("Starting debug MCP server...", flush=True)
    logger.debug("Server initialized")
    
    # Run the stdio handler
    asyncio.run(handle_stdio())

