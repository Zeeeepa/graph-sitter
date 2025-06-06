#!/usr/bin/env python3
"""
Test script to validate both dashboard launchers work correctly.
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def test_launcher(script_name, description):
    """Test a dashboard launcher script."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing {description}")
    print('='*60)
    
    try:
        # Start the launcher
        print(f"Starting {script_name}...")
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Server started successfully")
            
            # Test endpoints
            endpoints = ['/health', '/api/health', '/api/projects']
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f'http://localhost:8000{endpoint}', timeout=2)
                    if response.status_code == 200:
                        print(f"✅ Endpoint {endpoint} - WORKING")
                    else:
                        print(f"❌ Endpoint {endpoint} - HTTP {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"❌ Endpoint {endpoint} - ERROR: {e}")
            
            # Kill the process
            process.terminate()
            process.wait(timeout=5)
            print("✅ Server stopped cleanly")
            return True
            
        else:
            stdout, stderr = process.communicate()
            print("❌ Server failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run tests for both launchers."""
    print("🚀 TESTING BOTH DASHBOARD LAUNCHERS")
    print("=" * 60)
    print("This script tests both the original and standalone launchers.")
    
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent
    import os
    os.chdir(dashboard_dir)
    
    results = []
    
    # Test standalone launcher
    results.append((
        "Standalone Launcher",
        test_launcher("start_dashboard_standalone.py", "Standalone Launcher")
    ))
    
    # Test consolidated launcher
    results.append((
        "Consolidated Launcher", 
        test_launcher("start_consolidated_dashboard.py", "Consolidated Launcher (Fixed)")
    ))
    
    # Print summary
    print(f"\n{'='*60}")
    print("🎯 TEST SUMMARY")
    print('='*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        if result:
            print(f"✅ {test_name} - PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} - FAILED")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} launchers working")
    
    if passed == total:
        print("🎉 ALL LAUNCHERS WORKING - Both original and standalone work!")
    elif passed > 0:
        print("⚠️  PARTIAL SUCCESS - At least one launcher works")
    else:
        print("❌ ALL LAUNCHERS FAILED - Need more fixes")

if __name__ == "__main__":
    main()

