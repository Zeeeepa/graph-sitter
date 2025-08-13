import asyncio
import subprocess
import json
import sys
import logging
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_protocol")

class MCPServer:
    """A class to manage an MCP server process."""
    
    def __init__(self, command, args):
        """Initialize the server."""
        self.command = command
        self.args = args
        self.process = None
    
    async def start(self):
        """Start the server process."""
        logger.info(f"Starting server process: {self.command} {' '.join(self.args)}")
        self.process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Wait for the server to start
        logger.info("Waiting for server to start...")
        await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the server process."""
        if self.process:
            logger.info("Stopping server process...")
            self.process.terminate()
            await asyncio.sleep(0.5)
            if self.process.poll() is None:
                logger.info("Server process did not terminate, killing...")
                self.process.kill()
    
    def send_message(self, message):
        """Send a message to the server."""
        if not self.process:
            raise RuntimeError("Server process not started")
        
        message_json = json.dumps(message)
        content_length = len(message_json)
        
        logger.info(f"Sending message: {message}")
        self.process.stdin.write(f"Content-Length: {content_length}\r\n\r\n")
        self.process.stdin.write(message_json)
        self.process.stdin.flush()
    
    async def read_message(self):
        """Read a message from the server."""
        if not self.process:
            raise RuntimeError("Server process not started")
        
        # Read headers
        headers = {}
        while True:
            line = self.process.stdout.readline().strip()
            logger.debug(f"Header line: '{line}'")
            
            if not line:
                break
            
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        
        # Read content based on Content-Length
        content_length = int(headers.get("Content-Length", 0))
        if content_length > 0:
            content = self.process.stdout.read(content_length)
            logger.info(f"Response content: {content}")
            
            try:
                response = json.loads(content)
                logger.info(f"Parsed response: {response}")
                return response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response: {e}")
                return None
        else:
            logger.warning("No Content-Length header found")
            return None

class MCPClient:
    """A class to interact with an MCP server."""
    
    def __init__(self, server):
        """Initialize the client."""
        self.server = server
        self.request_id = 0
    
    def next_request_id(self):
        """Get the next request ID."""
        self.request_id += 1
        return str(self.request_id)
    
    async def initialize(self):
        """Initialize the client."""
        request_id = self.next_request_id()
        initialize_request = {
            "jsonrpc": "2.0",
            "id": request_id,
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
        
        self.server.send_message(initialize_request)
        return await self.server.read_message()
    
    async def list_tools(self):
        """List the available tools."""
        request_id = self.next_request_id()
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/list",
            "params": {}
        }
        
        self.server.send_message(list_tools_request)
        return await self.server.read_message()
    
    async def call_tool(self, name, arguments=None):
        """Call a tool."""
        request_id = self.next_request_id()
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments or {}
            }
        }
        
        self.server.send_message(call_tool_request)
        return await self.server.read_message()

async def main():
    """Main function to test the MCP protocol."""
    logger.info("Starting MCP protocol test...")
    
    try:
        # Start the server
        server = MCPServer("python", ["test_mcp_fastmcp.py"])
        await server.start()
        
        # Create a client
        client = MCPClient(server)
        
        # Initialize the client
        logger.info("Initializing client...")
        try:
            # Set a timeout for the initialization
            async with asyncio.timeout(5):
                result = await client.initialize()
                logger.info(f"Initialization result: {result}")
                
                # List the tools
                logger.info("Listing tools...")
                tools = await client.list_tools()
                logger.info(f"Tools: {tools}")
                
                # Call the hello_world tool
                logger.info("Calling hello_world tool...")
                result = await client.call_tool("hello_world")
                logger.info(f"Tool result: {result}")
        except asyncio.TimeoutError:
            logger.error("Operation timed out")
        except Exception as e:
            logger.error(f"Operation error: {e}")
            import traceback
            traceback.print_exc()
        
        # Stop the server
        await server.stop()
        
        logger.info("Test completed successfully.")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.info("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

