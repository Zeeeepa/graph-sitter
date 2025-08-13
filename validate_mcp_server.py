import subprocess
import time
import requests
import json

def main():
    # Start the MCP server
    print("Starting MCP server...")
    server_process = subprocess.Popen(
        ["python", "test_mcp_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the server to start
    time.sleep(3)
    
    # Check if the server is running
    print("Checking if the server is running...")
    try:
        response = requests.get("http://127.0.0.1:8001")
        print(f"Server response status: {response.status_code}")
    except Exception as e:
        print(f"Error connecting to server: {e}")
    
    # Try different endpoints
    endpoints = [
        "/",
        "/mcp",
        "/mcp/manifest",
        "/manifest",
        "/tools/hello_world",
        "/resources/system://greeting"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTrying endpoint: {endpoint}")
            response = requests.get(f"http://127.0.0.1:8001{endpoint}")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.text[:100]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    # Stop the server
    print("\nStopping the server...")
    server_process.terminate()
    server_process.wait()
    
    # Print server output
    print("\nServer stdout:")
    print(server_process.stdout.read())
    
    print("\nServer stderr:")
    print(server_process.stderr.read())
    
    print("\nMCP server validation complete.")

if __name__ == "__main__":
    main()

