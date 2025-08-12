#!/usr/bin/env python3
"""
Test and demonstration script for the Enhanced Analytics API

This script demonstrates how to use the enhanced analytics API with Serena LSP integration
for comprehensive codebase analysis including both metrics and error detection.
"""

import asyncio
import json
import requests
from typing import Dict, Any
from enhanced_analytics_api import (
    SerenaErrorAnalyzer, 
    CodeError, 
    DiagnosticSeverity, 
    ErrorCategory,
    EnhancedRepoAnalysis
)

async def test_serena_error_analyzer():
    """Test the SerenaErrorAnalyzer directly."""
    print("🔍 Testing SerenaErrorAnalyzer...")
    
    analyzer = SerenaErrorAnalyzer()
    
    # Test with current repository
    errors = await analyzer.analyze_codebase_errors(".")
    
    print(f"✅ Found {len(errors)} errors in codebase")
    
    # Display first few errors
    for i, error in enumerate(errors[:5], 1):
        print(f"\n📍 Error {i}:")
        print(f"   File: {error.file_path}")
        print(f"   Line: {error.line_number}, Column: {error.column}")
        print(f"   Severity: {error.severity.name}")
        print(f"   Category: {error.category.value}")
        print(f"   Message: {error.message}")
        if error.context_lines:
            print(f"   Context: {' | '.join(error.context_lines[:2])}")
        if error.fix_suggestions:
            print(f"   Suggestions: {', '.join(error.fix_suggestions)}")
    
    return errors

def test_api_endpoints_locally():
    """Test the API endpoints if running locally."""
    print("\n🌐 Testing API endpoints locally...")
    
    # This would work if the FastAPI server is running
    base_url = "http://localhost:8000"
    
    test_repo = {"repo_url": "octocat/Hello-World"}
    
    try:
        # Test original endpoint
        response = requests.post(f"{base_url}/analyze_repo", json=test_repo, timeout=30)
        if response.status_code == 200:
            print("✅ Original /analyze_repo endpoint working")
            data = response.json()
            print(f"   Files: {data.get('num_files', 0)}")
            print(f"   Functions: {data.get('num_functions', 0)}")
        else:
            print(f"❌ Original endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test original endpoint: {e}")
    
    try:
        # Test enhanced endpoint
        response = requests.post(f"{base_url}/analyze_repo_enhanced", json=test_repo, timeout=30)
        if response.status_code == 200:
            print("✅ Enhanced /analyze_repo_enhanced endpoint working")
            data = response.json()
            print(f"   Total errors: {data.get('error_analysis', {}).get('total_errors', 0)}")
            print(f"   Error categories: {list(data.get('error_analysis', {}).get('errors_by_category', {}).keys())}")
        else:
            print(f"❌ Enhanced endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test enhanced endpoint: {e}")
    
    try:
        # Test error-focused endpoint
        response = requests.post(f"{base_url}/analyze_errors", json=test_repo, timeout=30)
        if response.status_code == 200:
            print("✅ Error-focused /analyze_errors endpoint working")
            data = response.json()
            print(f"   {data.get('title', 'No title')}")
            errors = data.get('errors', [])
            if errors:
                print(f"   First error: {errors[0].get('message', 'No message')}")
        else:
            print(f"❌ Error-focused endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test error-focused endpoint: {e}")

def demonstrate_error_formatting():
    """Demonstrate the error formatting as requested by the user."""
    print("\n📋 Demonstrating Error Formatting...")
    
    # Create sample errors
    sample_errors = [
        CodeError(
            file_path="src/main.py",
            line_number=42,
            column=10,
            severity=DiagnosticSeverity.ERROR,
            category=ErrorCategory.UNDEFINED,
            message="Undefined variable 'undefined_var'",
            context_lines=["def main():", "    result = undefined_var + 1", "    return result"],
            fix_suggestions=["Define 'undefined_var' before use", "Check for typos in variable name"]
        ),
        CodeError(
            file_path="src/utils.py",
            line_number=15,
            column=0,
            severity=DiagnosticSeverity.WARNING,
            category=ErrorCategory.IMPORT,
            message="Unused import 'os'",
            context_lines=["import os", "import sys", "from typing import Dict"],
            fix_suggestions=["Remove unused import"]
        ),
        CodeError(
            file_path="src/app.js",
            line_number=23,
            column=4,
            severity=DiagnosticSeverity.INFORMATION,
            category=ErrorCategory.STYLE,
            message="console.log statement found",
            context_lines=["function debug() {", "    console.log('Debug info');", "}"],
            fix_suggestions=["Remove console.log for production", "Use proper logging framework"]
        )
    ]
    
    # Format as requested: "Errors in Codebase [count]"
    print(f"Errors in Codebase [{len(sample_errors)}]")
    
    for i, error in enumerate(sample_errors, 1):
        context_preview = " | ".join(error.context_lines[:2]) if error.context_lines else "No context"
        print(f"{i}. {error.file_path} '{error.message}' '{error.severity.name}' '{error.category.value}' 'Line {error.line_number}' '{context_preview}'")

def create_usage_example():
    """Create a usage example file."""
    example_code = '''
"""
Enhanced Analytics API Usage Example

This example shows how to use the enhanced analytics API with error detection.
"""

import asyncio
import json
from enhanced_analytics_api import SerenaErrorAnalyzer, RepoRequest

async def analyze_repository(repo_url: str):
    """Analyze a repository for both metrics and errors."""
    
    # Method 1: Direct error analysis
    print(f"🔍 Analyzing {repo_url} for errors...")
    analyzer = SerenaErrorAnalyzer()
    errors = await analyzer.analyze_codebase_errors(repo_url)
    
    print(f"Errors in Codebase [{len(errors)}]")
    for i, error in enumerate(errors[:10], 1):  # Show first 10 errors
        context = " | ".join(error.context_lines[:2]) if error.context_lines else "No context"
        print(f"{i}. {error.file_path} '{error.message}' '{error.severity.name}' '{error.category.value}' 'Line {error.line_number}' '{context}'")
    
    # Method 2: Using the API endpoints (if server is running)
    # This would be done via HTTP requests to the FastAPI server
    
    return errors

# Example usage
if __name__ == "__main__":
    # Analyze a sample repository
    repo_url = "octocat/Hello-World"  # Small test repository
    errors = asyncio.run(analyze_repository(repo_url))
    
    print(f"\\n✅ Analysis complete! Found {len(errors)} total errors.")
'''
    
    with open("example_usage.py", "w") as f:
        f.write(example_code)
    
    print("📝 Created example_usage.py")

async def main():
    """Main test function."""
    print("🚀 Enhanced Analytics API Test Suite")
    print("=" * 50)
    
    # Test 1: Direct analyzer testing
    errors = await test_serena_error_analyzer()
    
    # Test 2: API endpoint testing (if server is running)
    test_api_endpoints_locally()
    
    # Test 3: Demonstrate error formatting
    demonstrate_error_formatting()
    
    # Test 4: Create usage example
    create_usage_example()
    
    print("\n🎉 Test suite complete!")
    print(f"📊 Summary:")
    print(f"   - Found {len(errors)} errors in current codebase")
    print(f"   - Created usage examples")
    print(f"   - Demonstrated error formatting")
    
    # Show error breakdown
    if errors:
        severity_counts = {}
        category_counts = {}
        
        for error in errors:
            severity_counts[error.severity.name] = severity_counts.get(error.severity.name, 0) + 1
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
        
        print(f"\n📈 Error Breakdown:")
        print(f"   By Severity: {severity_counts}")
        print(f"   By Category: {category_counts}")

if __name__ == "__main__":
    asyncio.run(main())

