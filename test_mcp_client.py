import json
import sys

def send_message(message):
    """Send a message to the MCP server."""
    message_json = json.dumps(message)
    content_length = len(message_json)
    print(f"Content-Length: {content_length}\r\n", file=sys.stdout, flush=True)
    print(message_json, file=sys.stdout, flush=True)

def main():
    """Main function to test the MCP server."""
    # Send a request to the hello_world tool
    request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "mcp.execute",
        "params": {
            "name": "hello_world",
            "parameters": {}
        }
    }
    send_message(request)

if __name__ == "__main__":
    main()

