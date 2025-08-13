import subprocess
import time
import threading
import json
import sys
import os

class MCPServer:
    """MCP server class."""
    
    def __init__(self, server_script="test_mcp_server.py"):
        """Initialize the MCP server."""
        self.server_script = server_script
        self.process = None
        self.output_thread = None
        self.error_thread = None
        self.running = False
    
    def start(self):
        """Start the MCP server."""
        if self.running:
            return
        
        self.process = subprocess.Popen(
            ["python", self.server_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        self.running = True
        
        # Start threads to monitor output and errors
        self.output_thread = threading.Thread(target=self._monitor_output)
        self.error_thread = threading.Thread(target=self._monitor_errors)
        
        self.output_thread.daemon = True
        self.error_thread.daemon = True
        
        self.output_thread.start()
        self.error_thread.start()
        
        # Wait for the server to initialize
        time.sleep(2)
    
    def stop(self):
        """Stop the MCP server."""
        if not self.running:
            return
        
        self.running = False
        self.process.terminate()
        
        # Wait for the process to terminate
        self.process.wait()
        
        # Wait for the monitoring threads to finish
        self.output_thread.join(timeout=1)
        self.error_thread.join(timeout=1)
    
    def _monitor_output(self):
        """Monitor the server output."""
        while self.running:
            line = self.process.stdout.readline()
            if not line:
                break
            print(f"Server: {line.strip()}")
    
    def _monitor_errors(self):
        """Monitor the server errors."""
        while self.running:
            line = self.process.stderr.readline()
            if not line:
                break
            print(f"Server ERROR: {line.strip()}")

class MCPClient:
    """MCP client class."""
    
    def __init__(self, server):
        """Initialize the MCP client."""
        self.server = server
        self.request_id = 0
    
    def send_request(self, method, params=None):
        """Send a request to the MCP server."""
        if not self.server.running:
            raise RuntimeError("Server is not running")
        
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": str(self.request_id),
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request)
        content_length = len(request_json)
        
        # Send the request to the server
        self.server.process.stdin.write(f"Content-Length: {content_length}\r\n\r\n")
        self.server.process.stdin.write(request_json + "\n")
        self.server.process.stdin.flush()
        
        print(f"Client: Sent request {self.request_id}: {method}")
        
        # Wait for the response
        time.sleep(1)
    
    def execute_tool(self, tool_name, parameters=None):
        """Execute a tool on the MCP server."""
        return self.send_request("mcp.execute", {
            "name": tool_name,
            "parameters": parameters or {}
        })

def main():
    """Main function to test the MCP orchestrator."""
    print("Starting comprehensive MCP test...")
    
    # Create the server and client
    server = MCPServer()
    client = MCPClient(server)
    
    try:
        # Start the server
        server.start()
        print("Server started.")
        
        # Execute the hello_world tool
        client.execute_tool("hello_world")
        
        # Wait for the response
        time.sleep(2)
        
        print("Test completed successfully.")
    
    finally:
        # Stop the server
        server.stop()
        print("Server stopped.")

if __name__ == "__main__":
    main()

