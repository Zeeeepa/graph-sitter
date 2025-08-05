#!/usr/bin/env python3
"""
Demo script showing the enhanced analytics API with actual error detection
"""

import asyncio
import tempfile
import os
from pathlib import Path
from enhanced_analytics_api import SerenaErrorAnalyzer

async def create_test_repo_with_errors():
    """Create a temporary repository with intentional errors for testing."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_repo_")
    print(f"📁 Created test repository at: {temp_dir}")
    
    # Create Python file with errors
    python_file = Path(temp_dir) / "main.py"
    python_code = '''
import os
import sys
import unused_module

def main():
    # Undefined variable error
    result = undefined_variable + 1
    
    # Another undefined variable
    data = some_other_undefined_var
    
    # Unused import above (os, unused_module)
    print("Hello World")
    
    return result

def unused_function():
    pass

if __name__ == "__main__":
    main()
'''
    python_file.write_text(python_code)
    
    # Create JavaScript file with errors
    js_file = Path(temp_dir) / "app.js"
    js_code = '''
var oldStyleVar = "should use let or const";

function debugFunction() {
    console.log("Debug statement - should be removed");
    console.log("Another debug statement");
    
    var anotherOldVar = "more old style";
    
    return oldStyleVar + anotherOldVar;
}

// More console.log statements
console.log("Global debug statement");
'''
    js_file.write_text(js_code)
    
    # Create another Python file with different errors
    utils_file = Path(temp_dir) / "utils.py"
    utils_code = '''
import json
import re
import datetime
from typing import Dict

# Only json is actually used, others are unused imports

def process_data(data):
    return json.dumps(data)

def another_function():
    # Undefined variable
    return missing_var * 2
'''
    utils_file.write_text(utils_code)
    
    return temp_dir

async def demo_error_analysis():
    """Demonstrate comprehensive error analysis."""
    print("🚀 Enhanced Analytics API - Error Detection Demo")
    print("=" * 60)
    
    # Create test repository
    test_repo = await create_test_repo_with_errors()
    
    try:
        # Analyze the test repository
        print("\n🔍 Analyzing test repository for errors...")
        
        # Set up logging to see what's happening
        import logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        
        analyzer = SerenaErrorAnalyzer()
        errors = await analyzer.analyze_codebase_errors(test_repo)
        
        # Display results in the requested format
        print(f"\nErrors in Codebase [{len(errors)}]")
        print("-" * 40)
        
        for i, error in enumerate(errors, 1):
            context = " | ".join(error.context_lines[:2]) if error.context_lines else "No context"
            print(f"{i}. {error.file_path} '{error.message}' '{error.severity.name}' '{error.category.value}' 'Line {error.line_number}' '{context}'")
        
        # Show error breakdown
        if errors:
            print(f"\n📊 Error Analysis Summary:")
            
            # Count by severity
            severity_counts = {}
            category_counts = {}
            file_counts = {}
            
            for error in errors:
                severity_counts[error.severity.name] = severity_counts.get(error.severity.name, 0) + 1
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
                file_counts[error.file_path] = file_counts.get(error.file_path, 0) + 1
            
            print(f"   By Severity: {severity_counts}")
            print(f"   By Category: {category_counts}")
            print(f"   By File: {file_counts}")
            
            # Show fix suggestions
            print(f"\n💡 Fix Suggestions:")
            for error in errors:
                if error.fix_suggestions:
                    print(f"   {error.file_path}:{error.line_number} - {', '.join(error.fix_suggestions)}")
        
        else:
            print("✅ No errors found in the test repository!")
            
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_repo)
        print(f"\n🧹 Cleaned up test repository")

if __name__ == "__main__":
    asyncio.run(demo_error_analysis())
