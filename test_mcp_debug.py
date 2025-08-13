import asyncio
import subprocess
import time
import mcp
import traceback
import sys
import logging
from mcp.client.stdio import StdioServerParameters

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_debug")

async def main():
    """Main function to test the MCP stdio client with debugging."""
    logger.info("Starting MCP debug test...")
    
    try:
        # Create the server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["test_mcp_server.py"],
            encoding="utf-8"
        )
        
        # Start the server process manually
        logger.info("Starting server process...")
        server_process = subprocess.Popen(
            ["python", "test_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Read some output from the server
        logger.info("Reading server output...")
        for _ in range(5):
            line = server_process.stdout.readline()
            if line:
                logger.info(f"Server output: {line.strip()}")
            else:
                logger.info("No output from server")
            await asyncio.sleep(0.5)
        
        # Try to send a message to the server
        logger.info("Sending message to server...")
        message = '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test-client","version":"0.1.0"}}}\n'
        server_process.stdin.write(message)
        server_process.stdin.flush()
        
        # Read the response
        logger.info("Reading server response...")
        for _ in range(5):
            line = server_process.stdout.readline()
            if line:
                logger.info(f"Server response: {line.strip()}")
            else:
                logger.info("No response from server")
            await asyncio.sleep(0.5)
        
        # Terminate the server
        logger.info("Terminating server...")
        server_process.terminate()
        
        logger.info("Test completed successfully.")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        traceback.print_exc()
    
    finally:
        logger.info("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

