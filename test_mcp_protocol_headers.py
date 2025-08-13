import asyncio
import subprocess
import time
import json
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_protocol")

async def main():
    """Main function to test the MCP protocol with headers."""
    logger.info("Starting MCP protocol headers test...")
    
    try:
        # Start the server process
        logger.info("Starting server process...")
        server_process = subprocess.Popen(
            ["python", "test_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Wait for the server to start
        logger.info("Waiting for server to start...")
        await asyncio.sleep(1)
        
        # Send an initialize request with headers
        logger.info("Sending initialize request...")
        initialize_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "0.1.0"
                }
            }
        }
        
        request_json = json.dumps(initialize_request)
        content_length = len(request_json)
        
        # Send the headers and request
        server_process.stdin.write(f"Content-Length: {content_length}\r\n\r\n")
        server_process.stdin.write(request_json)
        server_process.stdin.flush()
        
        # Read the response
        logger.info("Reading response...")
        
        # Read headers
        headers = {}
        while True:
            line = server_process.stdout.readline().strip()
            logger.info(f"Header line: '{line}'")
            
            if not line:
                break
            
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        
        # Read content based on Content-Length
        content_length = int(headers.get("Content-Length", 0))
        if content_length > 0:
            content = server_process.stdout.read(content_length)
            logger.info(f"Response content: {content}")
            
            try:
                response = json.loads(content)
                logger.info(f"Parsed response: {response}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response: {e}")
        else:
            logger.warning("No Content-Length header found")
        
        # Terminate the server
        logger.info("Terminating server...")
        server_process.terminate()
        
        logger.info("Test completed successfully.")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.info("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

