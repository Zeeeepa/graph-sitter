import asyncio
import mcp
from mcp.client.stdio import StdioServerParameters
from mcp.client.session import ClientSession
import traceback

async def main():
    """Main function to test the MCP stdio client."""
    print("Starting MCP stdio client test...")
    
    try:
        # Create the server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["test_mcp_fastmcp.py"],
            encoding="utf-8"
        )
        
        # Create the client
        print("Creating client...")
        async with mcp.stdio_client(server_params) as (read_stream, write_stream):
            # Create a client session
            print("Creating client session...")
            client = ClientSession(read_stream, write_stream)
            
            # Initialize the client with a timeout
            print("Initializing client...")
            try:
                # Set a timeout for the initialization
                async with asyncio.timeout(5):
                    result = await client.initialize()
                    print(f"Initialization result: {result}")
                    
                    # List the tools
                    print("Listing tools...")
                    tools = await client.list_tools()
                    print(f"Tools: {tools}")
                    
                    # Call the hello_world tool
                    print("Calling hello_world tool...")
                    result = await client.call_tool("hello_world")
                    print(f"Tool result: {result}")
            except asyncio.TimeoutError:
                print("Operation timed out")
            except Exception as e:
                print(f"Operation error: {e}")
                traceback.print_exc()
            
            print("Test completed successfully.")
    
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    
    finally:
        print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

