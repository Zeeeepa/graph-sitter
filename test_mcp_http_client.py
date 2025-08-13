import requests
import json

def main():
    base_url = "http://127.0.0.1:8000"
    
    # Try the /mcp endpoint with different headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    print("Trying /mcp endpoint with JSON headers...")
    response = requests.get(f"{base_url}/mcp", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text[:100]}...")
    
    # Try with text/event-stream header for SSE
    headers = {
        "Accept": "text/event-stream"
    }
    
    print("\nTrying /mcp endpoint with SSE headers...")
    response = requests.get(f"{base_url}/mcp", headers=headers, stream=True)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Streaming response received. First few events:")
        for i, line in enumerate(response.iter_lines()):
            if line:
                print(f"Event {i}: {line.decode('utf-8')}")
            if i >= 5:  # Only show first few events
                print("...")
                break
        response.close()
    
    # Try POST request to /mcp
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    print("\nTrying POST to /mcp endpoint...")
    data = {
        "type": "manifest"
    }
    response = requests.post(f"{base_url}/mcp", headers=headers, json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text[:100]}...")

if __name__ == "__main__":
    main()

