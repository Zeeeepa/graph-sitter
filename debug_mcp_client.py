import asyncio
import json
import subprocess
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_mcp_client")

async def main():
    # Start the MCP server in a subprocess
    logger.debug("Starting server process")
    server_process = subprocess.Popen(
        ["python", "debug_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Give the server a moment to start
    await asyncio.sleep(1)
    
    # Read and discard the startup message
    startup_message = server_process.stdout.readline()
    logger.debug(f"Server startup message: {startup_message}")
    
    try:
        # Initialize the client
        logger.debug("Sending initialize request")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
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
                    "name": "debug-client",
                    "version": "0.1.0"
                }
            }
        }
        
        # Send the initialization request
        server_process.stdin.write(json.dumps(init_request) + "\n")
        server_process.stdin.flush()
        
        # Read the initialization response
        init_response = server_process.stdout.readline()
        logger.debug(f"Initialization response: {init_response}")
        
        try:
            init_response_json = json.loads(init_response)
            if "error" in init_response_json:
                logger.debug(f"Initialization error: {init_response_json['error']}")
            else:
                logger.debug(f"Initialization successful: {init_response_json}")
                
                # Send initialized notification
                logger.debug("Sending initialized notification")
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "initialized",
                    "params": {}
                }
                
                server_process.stdin.write(json.dumps(initialized_notification) + "\n")
                server_process.stdin.flush()
                
                # List tools
                logger.debug("Sending listTools request")
                list_tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "mcp/listTools",
                    "params": {}
                }
                
                server_process.stdin.write(json.dumps(list_tools_request) + "\n")
                server_process.stdin.flush()
                
                # Read the list tools response
                list_tools_response = server_process.stdout.readline()
                logger.debug(f"List tools response: {list_tools_response}")
                
                # Call the hello_world tool
                logger.debug("Sending callTool request")
                tool_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "mcp/callTool",
                    "params": {
                        "tool": "hello_world",
                        "parameters": {
                            "name": "Graph-sitter"
                        }
                    }
                }
                
                # Send the tool request
                server_process.stdin.write(json.dumps(tool_request) + "\n")
                server_process.stdin.flush()
                
                # Read the tool response
                tool_response = server_process.stdout.readline()
                logger.debug(f"Tool response: {tool_response}")
                
                try:
                    tool_response_json = json.loads(tool_response)
                    if "error" in tool_response_json:
                        logger.debug(f"Tool error: {tool_response_json['error']}")
                    else:
                        logger.debug(f"Tool result: {tool_response_json}")
                except json.JSONDecodeError:
                    logger.debug(f"Failed to parse tool response: {tool_response}")
        except json.JSONDecodeError:
            logger.debug(f"Failed to parse initialization response: {init_response}")
        
    except Exception as e:
        logger.exception(f"Error: {e}")
    finally:
        # Terminate the server
        logger.debug("Terminating server process")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    asyncio.run(main())

