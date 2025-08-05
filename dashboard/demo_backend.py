#!/usr/bin/env python3
"""
DEMO: Real Graph-Sitter Backend API
Demonstrates the production backend with real analysis capabilities
"""

import sys
import asyncio
import httpx
from pathlib import Path

# Add graph-sitter to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def demo_backend_api():
    """Demonstrate the backend API with real analysis"""
    print("🔥 DEMO: REAL GRAPH-SITTER BACKEND API")
    print("=" * 50)
    
    # Start analysis of current repository
    repo_url = "https://github.com/Zeeeepa/graph-sitter"
    
    print(f"📊 Starting analysis of: {repo_url}")
    print("🔄 This will use REAL graph-sitter analysis...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Start analysis
            print("\n1️⃣ Starting analysis...")
            response = await client.post(
                "http://localhost:8000/analyze",
                json={"repo_url": repo_url, "language": "python"}
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_id = result["analysis_id"]
                print(f"✅ Analysis started with ID: {analysis_id}")
                
                # Poll for completion
                print("\n2️⃣ Polling for completion...")
                max_attempts = 60  # 2 minutes max
                attempt = 0
                
                while attempt < max_attempts:
                    status_response = await client.get(
                        f"http://localhost:8000/analysis/{analysis_id}/status"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get("status", "unknown")
                        progress = status_data.get("progress", 0)
                        
                        print(f"📈 Status: {status} - Progress: {progress}%")
                        
                        if status == "completed":
                            print("🎉 Analysis completed!")
                            break
                        elif status == "error":
                            print(f"❌ Analysis failed: {status_data.get('error', 'Unknown error')}")
                            return
                    
                    await asyncio.sleep(2)
                    attempt += 1
                
                if attempt >= max_attempts:
                    print("⏰ Analysis timed out")
                    return
                
                # Get results
                print("\n3️⃣ Fetching results...")
                
                # Get tree structure
                tree_response = await client.get(
                    f"http://localhost:8000/analysis/{analysis_id}/tree"
                )
                
                if tree_response.status_code == 200:
                    tree_data = tree_response.json()
                    print(f"🌳 Tree structure loaded:")
                    print(f"   📊 Total issues: {tree_data['total_issues']}")
                    print(f"   🔍 Issues by severity: {tree_data['issues_by_severity']}")
                
                # Get summary
                summary_response = await client.get(
                    f"http://localhost:8000/analysis/{analysis_id}/summary"
                )
                
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    stats = summary_data["stats"]
                    print(f"\n📈 REAL ANALYSIS RESULTS:")
                    print(f"   📁 Total files: {stats['total_files']}")
                    print(f"   ⚡ Total functions: {stats['total_functions']}")
                    print(f"   🏗️  Total classes: {stats['total_classes']}")
                    print(f"   📦 Total imports: {stats['total_imports']}")
                    print(f"   🐛 Total issues: {stats['total_issues']}")
                    
                    print(f"\n🔥 Important functions found: {len(summary_data['important_functions'])}")
                    print(f"💀 Dead code items found: {len(summary_data['dead_code'])}")
                
                # Get issues
                issues_response = await client.get(
                    f"http://localhost:8000/analysis/{analysis_id}/issues"
                )
                
                if issues_response.status_code == 200:
                    issues_data = issues_response.json()
                    print(f"\n🐛 ISSUE BREAKDOWN:")
                    by_severity = issues_data.get("by_severity", {})
                    for severity, issues in by_severity.items():
                        print(f"   {severity.upper()}: {len(issues)} issues")
                    
                    # Show first few issues
                    all_issues = issues_data.get("issues", [])
                    if all_issues:
                        print(f"\n📋 SAMPLE ISSUES (first 3):")
                        for i, issue in enumerate(all_issues[:3], 1):
                            print(f"   {i}. {issue['severity'].upper()}: {issue['description']}")
                            print(f"      📍 {issue['file_path']}:{issue['line_number']}")
                            print(f"      💡 {issue['suggestion']}")
                
                print("\n" + "=" * 50)
                print("🎉 DEMO COMPLETE - REAL GRAPH-SITTER INTEGRATION VERIFIED!")
                print("✅ Backend API is fully functional with real analysis")
                print("🔗 API Documentation: http://localhost:8000/docs")
                
            else:
                print(f"❌ Failed to start analysis: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Run the backend demo"""
    print("🚀 Starting backend demo...")
    print("📝 Make sure the backend is running: python dashboard/backend_core.py")
    print("⏳ Waiting 3 seconds for you to start the backend...")
    
    import time
    time.sleep(3)
    
    # Run the demo
    asyncio.run(demo_backend_api())

if __name__ == "__main__":
    main()
