import asyncio
import sys
import mcp
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
from mcp.shared.message import SessionMessage
import traceback

async def main():
    """Main function to test the MCP stdio server library."""
    print("Starting MCP stdio server library test...", file=sys.stderr)
    
    try:
        # Create a FastMCP server
        mcp_server = FastMCP("test-mcp", instructions="Test MCP server")
        
        # Register a tool
        @mcp_server.tool()
        def hello_world():
            """Say hello to the world."""
            return "Hello, world!"
        
        # Start the server
        print("Starting stdio server...", file=sys.stderr)
        async with stdio_server() as (read_stream, write_stream):
            print("Server started.", file=sys.stderr)
            
            # Process messages
            print("Processing messages...", file=sys.stderr)
            try:
                async for message in read_stream:
                    print(f"Received message: {message}", file=sys.stderr)
                    
                    if isinstance(message, Exception):
                        print(f"Error message: {message}", file=sys.stderr)
                        continue
                    
                    if isinstance(message, SessionMessage):
                        # Process the message
                        print(f"Processing message: {message.message.method}", file=sys.stderr)
                        
                        # Send a response
                        response = SessionMessage.create_response(
                            message.message,
                            {"result": "Hello, world!"}
                        )
                        await write_stream.send(response)
                        print(f"Sent response: {response}", file=sys.stderr)
            except Exception as e:
                print(f"Error processing messages: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
        
        print("Test completed successfully.", file=sys.stderr)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    
    finally:
        print("Test finished.", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())

