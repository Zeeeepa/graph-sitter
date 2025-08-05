#!/usr/bin/env python3
"""
Test script to verify the consolidated dashboard works correctly
"""

import asyncio
import httpx
import time
import subprocess
import threading
import sys
from pathlib import Path

def test_backend_api(backend_port: int = 8000):
    """Test the backend API endpoints"""
    print(f"🧪 Testing backend API on port {backend_port}...")
    
    async def run_tests():
        base_url = f"http://localhost:{backend_port}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # Test health check
                print("1️⃣ Testing API health...")
                response = await client.get(f"{base_url}/docs")
                if response.status_code == 200:
                    print("✅ API documentation accessible")
                else:
                    print(f"❌ API docs failed: {response.status_code}")
                    return False
                
                # Test analysis endpoint
                print("2️⃣ Starting test analysis...")
                response = await client.post(
                    f"{base_url}/analyze",
                    json={"repo_url": "https://github.com/Zeeeepa/graph-sitter", "language": "python"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis_id = result["analysis_id"]
                    print(f"✅ Analysis started: {analysis_id}")
                    
                    # Poll for completion
                    print("3️⃣ Waiting for analysis completion...")
                    for i in range(30):
                        await asyncio.sleep(2)
                        status_response = await client.get(f"{base_url}/analysis/{analysis_id}/status")
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get("status", "unknown")
                            progress = status_data.get("progress", 0)
                            print(f"📊 Status: {status} - Progress: {progress}%")
                            
                            if status == "completed":
                                print("🎉 Analysis completed!")
                                
                                # Test results endpoints
                                print("4️⃣ Testing results endpoints...")
                                
                                # Test summary
                                summary_response = await client.get(f"{base_url}/analysis/{analysis_id}/summary")
                                if summary_response.status_code == 200:
                                    summary_data = summary_response.json()
                                    stats = summary_data["stats"]
                                    print(f"📊 Files: {stats['total_files']}, Functions: {stats['total_functions']}")
                                    print(f"📊 Classes: {stats['total_classes']}, Issues: {stats['total_issues']}")
                                
                                # Test tree
                                tree_response = await client.get(f"{base_url}/analysis/{analysis_id}/tree")
                                if tree_response.status_code == 200:
                                    tree_data = tree_response.json()
                                    print(f"🌳 Tree structure: {tree_data['tree']['name']}")
                                
                                # Test issues
                                issues_response = await client.get(f"{base_url}/analysis/{analysis_id}/issues")
                                if issues_response.status_code == 200:
                                    issues_data = issues_response.json()
                                    print(f"🐛 Issues found: {issues_data['total_issues']}")
                                
                                print("✅ All API endpoints working!")
                                return True
                                
                            elif status == "error":
                                print(f"❌ Analysis failed: {status_data.get('error', 'Unknown')}")
                                return False
                    
                    print("⏰ Analysis timed out")
                    return False
                else:
                    print(f"❌ Failed to start analysis: {response.status_code}")
                    print(response.text)
                    return False
                    
            except Exception as e:
                print(f"❌ API test failed: {e}")
                return False
    
    return asyncio.run(run_tests())

def main():
    """Main test function"""
    print("🔥 TESTING CONSOLIDATED DASHBOARD")
    print("=" * 50)
    
    # Import and test the app
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import app
        
        print("✅ App imports successfully")
        
        # Find free port
        backend_port = app.find_free_port(8000)
        print(f"🔧 Using backend port: {backend_port}")
        
        # Start backend in thread
        print("🚀 Starting backend for testing...")
        backend_thread = threading.Thread(
            target=app.start_backend, 
            args=(backend_port,), 
            daemon=True
        )
        backend_thread.start()
        
        # Wait for backend to start
        time.sleep(5)
        
        # Test the API
        success = test_backend_api(backend_port)
        
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            print(f"🌐 Backend running on: http://localhost:{backend_port}")
            print(f"📚 API docs: http://localhost:{backend_port}/docs")
            print("\n🚀 To run the full dashboard:")
            print("   cd dashboard")
            print("   python app.py")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
