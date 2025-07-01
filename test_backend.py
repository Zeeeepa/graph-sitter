#!/usr/bin/env python3
"""
Test script for the enhanced codebase analytics backend.
"""

import requests
import json
import sys

def test_health_endpoint():
    """Test the health check endpoint."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to backend: {e}")
        return False

def test_analyze_endpoint():
    """Test the analyze repository endpoint."""
    try:
        # Test with a small repository
        test_repo = "codegen-sh/graph-sitter"
        
        print(f"🔍 Testing analysis of repository: {test_repo}")
        
        response = requests.post(
            "http://localhost:8000/analyze_repo",
            json={"repo_url": test_repo},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Analysis endpoint working")
            print(f"📊 Found {data['basic_metrics']['files']} files")
            print(f"🔧 Found {data['basic_metrics']['functions']} functions")
            print(f"🏗️ Found {data['basic_metrics']['classes']} classes")
            print(f"🐛 Found {data['issues_summary']['total']} total issues")
            return True
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not test analysis endpoint: {e}")
        return False

def main():
    print("🧪 Testing Enhanced Codebase Analytics Backend")
    print("=" * 50)
    
    # Test health endpoint
    if not test_health_endpoint():
        print("\n💡 Make sure the backend is running:")
        print("   python start_backend.py")
        sys.exit(1)
    
    print()
    
    # Test analysis endpoint
    if not test_analyze_endpoint():
        sys.exit(1)
    
    print("\n🎉 All tests passed! Backend is working correctly.")

if __name__ == "__main__":
    main()

