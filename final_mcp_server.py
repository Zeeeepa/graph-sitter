import asyncio
import json
import logging
import sys
from typing import Annotated, Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

class MCPServer:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.version = "0.1.0"
        self.tools = {}
        self.resources = {}
        
    def tool(self, name: str, description: str):
        """Decorator to register a tool."""
        def decorator(func):
            self.tools[name] = {
                "func": func,
                "description": description,
                "parameters": self._get_parameters(func)
            }
            return func
        return decorator
        
    def resource(self, path: str, mime_type: str):
        """Decorator to register a resource."""
        def decorator(func):
            self.resources[path] = {
                "func": func,
                "mime_type": mime_type
            }
            return func
        return decorator
    
    def _get_parameters(self, func):
        """Extract parameter information from function annotations."""
        import inspect
        sig = inspect.signature(func)
        parameters = {}
        required = []
        
        for name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                if hasattr(param.annotation, "__metadata__"):
                    # Handle Annotated type
                    param_type = param.annotation.__origin__.__name__
                    description = param.annotation.__metadata__[0]
                else:
                    # Handle regular type annotation
                    param_type = param.annotation.__name__
                    description = ""
                
                parameters[name] = {
                    "type": param_type,
                    "description": description
                }
                
                if param.default == inspect.Parameter.empty:
                    required.append(name)
        
        return {
            "type": "object",
            "properties": parameters,
            "required": required
        }
    
    async def handle_request(self, request):
        """Handle a JSON-RPC request."""
        try:
            if request.get("method") == "initialize":
                return self._handle_initialize(request)
            elif request.get("method") == "initialized":
                # No response needed for notifications
                return None
            elif request.get("method") == "mcp/listTools":
                return self._handle_list_tools(request)
            elif request.get("method") == "mcp/callTool":
                return await self._handle_call_tool(request)
            elif request.get("method") == "mcp/listResources":
                return self._handle_list_resources(request)
            elif request.get("method") == "mcp/readResource":
                return await self._handle_read_resource(request)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {request.get('method')}"
                    }
                }
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def _handle_initialize(self, request):
        """Handle initialize request."""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "server_info": {
                    "name": self.name,
                    "version": self.version
                }
            }
        }
    
    def _handle_list_tools(self, request):
        """Handle listTools request."""
        tools_list = []
        for name, tool in self.tools.items():
            tools_list.append({
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"],
                "returns": {
                    "type": "string"
                }
            })
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": tools_list
            }
        }
    
    async def _handle_call_tool(self, request):
        """Handle callTool request."""
        params = request.get("params", {})
        tool_name = params.get("tool")
        parameters = params.get("parameters", {})
        
        if tool_name not in self.tools:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            }
        
        tool = self.tools[tool_name]
        try:
            # Call the tool function
            result = tool["func"](**parameters)
            
            # Handle async functions
            if asyncio.iscoroutine(result):
                result = await result
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        except Exception as e:
            logger.exception(f"Error calling tool {tool_name}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            }
    
    def _handle_list_resources(self, request):
        """Handle listResources request."""
        resources_list = []
        for path, resource in self.resources.items():
            resources_list.append({
                "path": path,
                "mime_type": resource["mime_type"]
            })
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "resources": resources_list
            }
        }
    
    async def _handle_read_resource(self, request):
        """Handle readResource request."""
        params = request.get("params", {})
        path = params.get("path")
        
        if path not in self.resources:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Resource not found: {path}"
                }
            }
        
        resource = self.resources[path]
        try:
            # Call the resource function
            result = resource["func"]()
            
            # Handle async functions
            if asyncio.iscoroutine(result):
                result = await result
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": result,
                    "mime_type": resource["mime_type"]
                }
            }
        except Exception as e:
            logger.exception(f"Error reading resource {path}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Resource read error: {str(e)}"
                }
            }
    
    async def run(self, transport="stdio"):
        """Run the server with the specified transport."""
        if transport == "stdio":
            await self._run_stdio()
        else:
            raise ValueError(f"Unsupported transport: {transport}")
    
    async def _run_stdio(self):
        """Run the server using stdio transport."""
        print(f"Starting {self.name}...", flush=True)
        
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    logger.debug("Empty line received, exiting")
                    break
                
                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    
                    if response is not None:
                        print(json.dumps(response), flush=True)
                        
                except json.JSONDecodeError:
                    logger.debug(f"Failed to parse JSON: {line.strip()}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(response), flush=True)
                    
            except Exception as e:
                logger.exception(f"Error handling request: {e}")
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(response), flush=True)

# Create an instance of the MCP server
server = MCPServer(
    name="graph-sitter-mcp-server",
    description="MCP server for graph-sitter"
)

@server.tool(name="hello_world", description="A simple hello world tool")
def hello_world(name: Annotated[str, "Your name"]) -> str:
    return f"Hello, {name}!"

@server.tool(name="parse_code", description="Parse code using graph-sitter")
def parse_code(code: Annotated[str, "Code to parse"], language: Annotated[str, "Programming language"]) -> str:
    return f"Parsed {len(code)} characters of {language} code"

@server.resource("system://manifest", mime_type="application/json")
def get_service_config() -> dict:
    """Get the service config."""
    return {
        "name": server.name,
        "version": server.version,
        "description": server.description,
    }

if __name__ == "__main__":
    asyncio.run(server.run())

