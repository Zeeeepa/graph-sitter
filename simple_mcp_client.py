import asyncio
import json
import subprocess
import sys
import time

async def main():
    # Start the MCP server in a subprocess
    server_process = subprocess.Popen(
        ["python", "test_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Give the server a moment to start and consume the startup message
    await asyncio.sleep(1)
    
    # Read and discard the startup message
    startup_message = server_process.stdout.readline()
    print(f"Server startup message: {startup_message}")
    
    try:
        # First, initialize the client
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                }
            }
        }
        
        # Send the initialization request
        server_process.stdin.write(json.dumps(init_request) + "\n")
        server_process.stdin.flush()
        
        # Read the initialization response
        init_response = server_process.stdout.readline()
        print(f"Initialization response: {init_response}")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        server_process.stdin.write(json.dumps(initialized_notification) + "\n")
        server_process.stdin.flush()
        
        # Call the hello_world tool
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
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
        print(f"Tool response: {tool_response}")
        
        # Parse the response
        try:
            response_json = json.loads(tool_response)
            print(f"Parsed tool response: {response_json}")
        except json.JSONDecodeError:
            print(f"Failed to parse tool response: {tool_response}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Terminate the server
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    asyncio.run(main())

