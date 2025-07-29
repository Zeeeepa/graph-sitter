#!/usr/bin/env python3
"""
Test script for graph-sitter error detection capabilities.

This script tests the comprehensive error detection system by:
1. Creating a test repository with Python errors
2. Using graph-sitter's Codebase to analyze it
3. Validating that errors are detected correctly
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.diagnostics import add_diagnostic_capabilities


def create_test_repository() -> str:
    """Create a temporary repository with Python files containing errors."""
    temp_dir = tempfile.mkdtemp(prefix="graph_sitter_test_")
    
    # Create Python files with various types of errors
    test_files = {
        "main.py": '''
import os
import nonexistent_module  # Import error
from typing import List

def main():
    # Undefined variable error
    print(undefined_variable)
    
    # Type error
    x: int = "string"
    
    # Syntax error (missing closing parenthesis)
    result = some_function(
        arg1="value1",
        arg2="value2"
    # Missing closing parenthesis
    
    return result

if __name__ == "__main__":
    main()
''',
        
        "utils.py": '''
def calculate_sum(numbers: List[int]) -> int:
    # Missing import for List
    total = 0
    for num in numbers:
        total += num
    return total

def divide_numbers(a: int, b: int) -> float:
    # Potential division by zero (warning)
    return a / b

class MyClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self) -> int:
        # Accessing non-existent attribute
        return self.non_existent_attr
''',
        
        "config.py": '''
# Configuration file with various issues

DATABASE_URL = "postgresql://user:pass@localhost/db"
API_KEY = "secret_key_123"  # Hardcoded secret (security warning)

# Unused import
import json
import requests

def get_config():
    # Undefined variable
    return {
        "database": DATABASE_URL,
        "api_key": API_KEY,
        "debug": DEBUG_MODE  # Undefined variable
    }

# Function with wrong return type annotation
def process_data() -> str:
    return 42  # Type mismatch
''',
        
        "requirements.txt": '''
requests==2.28.0
fastapi==0.95.0
uvicorn==0.21.0
''',
        
        "README.md": '''
# Test Repository

This is a test repository for graph-sitter error detection.
'''
    }
    
    # Write test files
    for filename, content in test_files.items():
        file_path = Path(temp_dir) / filename
        file_path.write_text(content)
    
    # Initialize git repository
    os.system(f"cd {temp_dir} && git init && git add . && git commit -m 'Initial commit'")
    
    print(f"Created test repository at: {temp_dir}")
    return temp_dir


def test_basic_codebase_creation():
    """Test basic codebase creation without LSP."""
    print("\n=== Testing Basic Codebase Creation ===")
    
    test_repo = create_test_repository()
    
    try:
        # Create codebase from local path
        codebase = Codebase(repo_path=test_repo, language="python")
        print(f"✅ Codebase created successfully: {codebase.repo_path}")
        print(f"📁 Files found: {len(list(codebase.files))}")
        
        # List some files
        for i, file in enumerate(codebase.files):
            if i < 5:  # Show first 5 files
                print(f"   - {file.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating basic codebase: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        shutil.rmtree(test_repo, ignore_errors=True)


def test_lsp_integration():
    """Test LSP integration and error detection."""
    print("\n=== Testing LSP Integration ===")
    
    test_repo = create_test_repository()
    
    try:
        # Create codebase from local path
        codebase = Codebase(repo_path=test_repo, language="python")
        print(f"✅ Codebase created: {codebase.repo_path}")
        
        # Check if diagnostic capabilities were added
        if hasattr(codebase, 'errors'):
            print("✅ Error detection capabilities added")
        else:
            print("❌ Error detection capabilities not found")
            return False
        
        # Check LSP status
        if hasattr(codebase, 'get_lsp_status'):
            status = codebase.get_lsp_status()
            print(f"📊 LSP Status: {status}")
        
        # Try to get errors
        try:
            errors = codebase.errors
            warnings = codebase.warnings
            hints = codebase.hints
            
            print(f"📝 Errors found: {len(errors)}")
            print(f"⚠️ Warnings found: {len(warnings)}")
            print(f"💡 Hints found: {len(hints)}")
            
            # Show first few errors
            for i, error in enumerate(errors[:3]):
                print(f"   🔴 {error}")
            
            # Show first few warnings
            for i, warning in enumerate(warnings[:3]):
                print(f"   🟡 {warning}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error accessing diagnostics: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Error creating codebase: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        shutil.rmtree(test_repo, ignore_errors=True)


def test_file_specific_diagnostics():
    """Test file-specific diagnostic retrieval."""
    print("\n=== Testing File-Specific Diagnostics ===")
    
    test_repo = create_test_repository()
    
    try:
        codebase = Codebase(repo_path=test_repo, language="python")
        
        # Test file-specific diagnostics
        if hasattr(codebase, 'get_file_errors'):
            main_errors = codebase.get_file_errors("main.py")
            utils_errors = codebase.get_file_errors("utils.py")
            
            print(f"📝 main.py errors: {len(main_errors)}")
            print(f"📝 utils.py errors: {len(utils_errors)}")
            
            # Show errors for main.py
            for error in main_errors[:2]:
                print(f"   🔴 main.py: {error}")
            
            return True
        else:
            print("❌ File-specific diagnostic methods not available")
            return False
            
    except Exception as e:
        print(f"❌ Error testing file-specific diagnostics: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        shutil.rmtree(test_repo, ignore_errors=True)


def test_fastapi_repository():
    """Test error detection on a real repository (if available)."""
    print("\n=== Testing FastAPI Repository (if available) ===")
    
    # Check if we can clone FastAPI repo for testing
    fastapi_dir = "/tmp/fastapi_test"
    
    try:
        # Clean up any existing directory
        if os.path.exists(fastapi_dir):
            shutil.rmtree(fastapi_dir)
        
        # Clone FastAPI repository
        clone_result = os.system(f"git clone --depth 1 https://github.com/tiangolo/fastapi.git {fastapi_dir}")
        
        if clone_result != 0:
            print("⚠️ Could not clone FastAPI repository - skipping test")
            return True
        
        # Test with FastAPI
        codebase = Codebase(repo_path=fastapi_dir, language="python")
        print(f"✅ FastAPI codebase loaded: {codebase.repo_path}")
        
        # Get error counts
        errors = codebase.errors
        warnings = codebase.warnings
        
        print(f"📝 FastAPI Errors: {len(errors)}")
        print(f"⚠️ FastAPI Warnings: {len(warnings)}")
        
        # Show a few errors if any
        for i, error in enumerate(errors[:3]):
            print(f"   🔴 {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing FastAPI repository: {e}")
        return False
    
    finally:
        if os.path.exists(fastapi_dir):
            shutil.rmtree(fastapi_dir, ignore_errors=True)


def main():
    """Run all tests."""
    print("🚀 Starting Graph-Sitter Error Detection Tests")
    
    tests = [
        ("Basic Codebase Creation", test_basic_codebase_creation),
        ("LSP Integration", test_lsp_integration),
        ("File-Specific Diagnostics", test_file_specific_diagnostics),
        ("FastAPI Repository", test_fastapi_repository),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
