import asyncio
import subprocess
import json
import sys
import logging
import time
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_orchestrator")

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

class MCPOrchestrator:
    """A class to orchestrate MCP servers and clients."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.servers = {}
        self.clients = {}
    
    async def start_server(self, name, command, args):
        """Start a server."""
        logger.info(f"Starting server {name}...")
        server = MCPServer(command, args)
        await server.start()
        self.servers[name] = server
        return server
    
    async def stop_server(self, name):
        """Stop a server."""
        if name in self.servers:
            logger.info(f"Stopping server {name}...")
            await self.servers[name].stop()
            del self.servers[name]
    
    async def stop_all_servers(self):
        """Stop all servers."""
        for name in list(self.servers.keys()):
            await self.stop_server(name)
    
    def create_client(self, name, server_name):
        """Create a client."""
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not found")
        
        logger.info(f"Creating client {name} for server {server_name}...")
        client = MCPClient(self.servers[server_name])
        self.clients[name] = client
        return client
    
    async def initialize_client(self, name):
        """Initialize a client."""
        if name not in self.clients:
            raise ValueError(f"Client {name} not found")
        
        logger.info(f"Initializing client {name}...")
        return await self.clients[name].initialize()
    
    async def list_tools(self, name):
        """List the tools for a client."""
        if name not in self.clients:
            raise ValueError(f"Client {name} not found")
        
        logger.info(f"Listing tools for client {name}...")
        return await self.clients[name].list_tools()
    
    async def call_tool(self, name, tool_name, arguments=None):
        """Call a tool for a client."""
        if name not in self.clients:
            raise ValueError(f"Client {name} not found")
        
        logger.info(f"Calling tool {tool_name} for client {name}...")
        return await self.clients[name].call_tool(tool_name, arguments)

async def main():
    """Main function to test the MCP orchestrator."""
    logger.info("Starting MCP orchestrator test...")
    
    try:
        # Create an orchestrator
        orchestrator = MCPOrchestrator()
        
        # Start a server
        await orchestrator.start_server("test-server", "python", ["test_mcp_fastmcp.py"])
        
        # Create a client
        orchestrator.create_client("test-client", "test-server")
        
        # Initialize the client
        logger.info("Initializing client...")
        try:
            # Set a timeout for the initialization
            async with asyncio.timeout(5):
                result = await orchestrator.initialize_client("test-client")
                logger.info(f"Initialization result: {result}")
                
                # List the tools
                logger.info("Listing tools...")
                tools = await orchestrator.list_tools("test-client")
                logger.info(f"Tools: {tools}")
                
                # Call the hello_world tool
                logger.info("Calling hello_world tool...")
                result = await orchestrator.call_tool("test-client", "hello_world")
                logger.info(f"Tool result: {result}")
        except asyncio.TimeoutError:
            logger.error("Operation timed out")
        except Exception as e:
            logger.error(f"Operation error: {e}")
            import traceback
            traceback.print_exc()
        
        # Stop all servers
        await orchestrator.stop_all_servers()
        
        logger.info("Test completed successfully.")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.info("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())

