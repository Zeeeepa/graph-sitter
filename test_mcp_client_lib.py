import asyncio
import httpx

async def main():
    # Create a client
    async with httpx.AsyncClient() as client:
        # Try with SSE headers
        print("Trying with SSE headers...")
        headers = {
            "Accept": "text/event-stream"
        }
        try:
            response = await client.get("http://127.0.0.1:8001/mcp", headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.text[:100]}...")
        except Exception as e:
            print(f"Error: {e}")
        
        # Try with JSON headers
        print("\nTrying with JSON headers...")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        try:
            response = await client.post(
                "http://127.0.0.1:8001/mcp",
                headers=headers,
                json={"type": "manifest"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.text[:100]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

