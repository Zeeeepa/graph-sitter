import asyncio
import subprocess
import time
import mcp
import traceback
import sys
from mcp.client.stdio import StdioServerParameters
from mcp.client.session import ClientSession

async def main():
    """Main function to test the MCP client library."""
    print("Starting MCP client library test...")
    
    try:
        # Create the server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["test_mcp_server.py"],
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
            except asyncio.TimeoutError:
                print("Initialization timed out")
            except Exception as e:
                print(f"Initialization error: {e}")
                traceback.print_exc()
            
            print("Test completed successfully.")
    
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    
    finally:
        print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

