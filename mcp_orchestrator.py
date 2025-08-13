import asyncio
import subprocess
import json
import sys
import logging
import time
import os
from typing import Dict, List, Optional, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_orchestrator")

class MCPServer:
    """A class to manage an MCP server process."""
    
    def __init__(self, command: str, args: List[str]):
        """Initialize the server.
        
        Args:
            command: The command to run the server.
            args: The arguments to pass to the command.
        """
        self.command = command
        self.args = args
        self.process = None
    
    async def start(self) -> None:
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
    
    async def stop(self) -> None:
        """Stop the server process."""
        if self.process:
            logger.info("Stopping server process...")
            self.process.terminate()
            await asyncio.sleep(0.5)
            if self.process.poll() is None:
                logger.info("Server process did not terminate, killing...")
                self.process.kill()
    
    def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to the server.
        
        Args:
            message: The message to send.
        
        Raises:
            RuntimeError: If the server process is not started.
        """
        if not self.process:
            raise RuntimeError("Server process not started")
        
        message_json = json.dumps(message)
        content_length = len(message_json)
        
        logger.debug(f"Sending message: {message}")
        self.process.stdin.write(f"Content-Length: {content_length}\r\n\r\n")
        self.process.stdin.write(message_json)
        self.process.stdin.flush()
    
    async def read_message(self) -> Optional[Dict[str, Any]]:
        """Read a message from the server.
        
        Returns:
            The parsed message, or None if no message could be read.
        
        Raises:
            RuntimeError: If the server process is not started.
        """
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
            logger.debug(f"Response content: {content}")
            
            try:
                response = json.loads(content)
                logger.debug(f"Parsed response: {response}")
                return response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response: {e}")
                return None
        else:
            logger.warning("No Content-Length header found")
            return None

class MCPClient:
    """A class to interact with an MCP server."""
    
    def __init__(self, server: MCPServer):
        """Initialize the client.
        
        Args:
            server: The server to interact with.
        """
        self.server = server
        self.request_id = 0
    
    def next_request_id(self) -> str:
        """Get the next request ID.
        
        Returns:
            The next request ID.
        """
        self.request_id += 1
        return str(self.request_id)
    
    async def initialize(self) -> Optional[Dict[str, Any]]:
        """Initialize the client.
        
        Returns:
            The initialization result, or None if the initialization failed.
        """
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
    
    async def list_tools(self) -> Optional[Dict[str, Any]]:
        """List the available tools.
        
        Returns:
            The list of tools, or None if the request failed.
        """
        request_id = self.next_request_id()
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/list",
            "params": {}
        }
        
        self.server.send_message(list_tools_request)
        return await self.server.read_message()
    
    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Call a tool.
        
        Args:
            name: The name of the tool to call.
            arguments: The arguments to pass to the tool.
        
        Returns:
            The tool result, or None if the request failed.
        """
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
        self.servers: Dict[str, MCPServer] = {}
        self.clients: Dict[str, MCPClient] = {}
    
    async def start_server(self, name: str, command: str, args: List[str]) -> MCPServer:
        """Start a server.
        
        Args:
            name: The name of the server.
            command: The command to run the server.
            args: The arguments to pass to the command.
        
        Returns:
            The server.
        """
        logger.info(f"Starting server {name}...")
        server = MCPServer(command, args)
        await server.start()
        self.servers[name] = server
        return server
    
    async def stop_server(self, name: str) -> None:
        """Stop a server.
        
        Args:
            name: The name of the server to stop.
        """
        if name in self.servers:
            logger.info(f"Stopping server {name}...")
            await self.servers[name].stop()
            del self.servers[name]
    
    async def stop_all_servers(self) -> None:
        """Stop all servers."""
        for name in list(self.servers.keys()):
            await self.stop_server(name)
    
    def create_client(self, name: str, server_name: str) -> MCPClient:
        """Create a client.
        
        Args:
            name: The name of the client.
            server_name: The name of the server to connect to.
        
        Returns:
            The client.
        
        Raises:
            ValueError: If the server is not found.
        """
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not found")
        
        logger.info(f"Creating client {name} for server {server_name}...")
        client = MCPClient(self.servers[server_name])
        self.clients[name] = client
        return client
    
    async def initialize_client(self, name: str) -> Optional[Dict[str, Any]]:
        """Initialize a client.
        
        Args:
            name: The name of the client to initialize.
        
        Returns:
            The initialization result, or None if the initialization failed.
        
        Raises:
            ValueError: If the client is not found.
        """
        if name not in self.clients:
            raise ValueError(f"Client {name} not found")
        
        logger.info(f"Initializing client {name}...")
        return await self.clients[name].initialize()
    
    async def list_tools(self, name: str) -> Optional[Dict[str, Any]]:
        """List the tools for a client.
        
        Args:
            name: The name of the client.
        
        Returns:
            The list of tools, or None if the request failed.
        
        Raises:
            ValueError: If the client is not found.
        """
        if name not in self.clients:
            raise ValueError(f"Client {name} not found")
        
        logger.info(f"Listing tools for client {name}...")
        return await self.clients[name].list_tools()
    
    async def call_tool(self, name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Call a tool for a client.
        
        Args:
            name: The name of the client.
            tool_name: The name of the tool to call.
            arguments: The arguments to pass to the tool.
        
        Returns:
            The tool result, or None if the request failed.
        
        Raises:
            ValueError: If the client is not found.
        """
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
        await orchestrator.start_server("test-server", "python", ["test_mcp_server_fixed.py"])
        
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

