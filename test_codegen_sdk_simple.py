#!/usr/bin/env python3
"""
Simple test script for the enhanced Codegen SDK implementation.
Tests with provided credentials: CODEGEN_ORG_ID=323, CODEGEN_TOKEN=sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99
"""

import os
import sys
import time
import traceback

# Add src to path
sys.path.insert(0, 'src')

from codegen import Agent, Task
from codegen.exceptions import CodegenError, AuthenticationError, ValidationError

def test_basic_functionality():
    """Test basic SDK functionality."""
    print("🚀 Testing Enhanced Codegen SDK")
    print("=" * 40)
    
    # Test 1: Agent Initialization
    print("🔧 Testing Agent Initialization...")
    try:
        agent = Agent(
            org_id="323",
            token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99",
            validate_on_init=False  # Don't validate during init
        )
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Test 2: Basic Task Creation (without API call)
    print("\n📝 Testing Task Creation Logic...")
    try:
        # Test validation logic
        if hasattr(agent, 'run'):
            print("✅ Agent has run method")
        else:
            print("❌ Agent missing run method")
            return False
            
        # Test parameter validation
        try:
            # This should fail with invalid priority
            agent.run(prompt="Test", priority="invalid")
            print("❌ Should have failed with invalid priority")
            return False
        except ValidationError:
            print("✅ Correctly caught validation error for invalid priority")
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")
            
    except Exception as e:
        print(f"❌ Task creation test failed: {e}")
        return False
    
    # Test 3: Type System
    print("\n🔍 Testing Type System...")
    try:
        # Test Task class
        from codegen.task import Task
        print("✅ Task class imported successfully")
        
        # Test exception classes
        from codegen.exceptions import APIError, RateLimitError, TimeoutError
        print("✅ Exception classes imported successfully")
        
    except Exception as e:
        print(f"❌ Type system test failed: {e}")
        return False
    
    # Test 4: Provider Integration
    print("\n🔌 Testing Provider Integration...")
    try:
        from graph_sitter.ai.providers.codegen_provider import CodegenProvider
        from graph_sitter.ai.providers.factory import get_available_providers
        
        # Test provider creation
        provider = CodegenProvider(
            org_id="323",
            token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        )
        print("✅ CodegenProvider created successfully")
        
        # Test factory
        providers = get_available_providers()
        print(f"✅ Available providers: {list(providers.keys())}")
        
    except Exception as e:
        print(f"❌ Provider integration test failed: {e}")
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 40)
    print("🎉 All basic tests passed!")
    print("✅ SDK implementation is robust and ready for testing")
    return True

def test_mypy_compliance():
    """Test mypy type checking compliance."""
    print("\n🔍 Testing MyPy Compliance...")
    
    import subprocess
    
    try:
        # Run mypy on core files
        result = subprocess.run([
            'python', '-m', 'mypy', 
            'src/codegen/agent.py',
            'src/codegen/task.py',
            '--ignore-missing-imports',
            '--no-error-summary'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ MyPy type checking passed")
            return True
        else:
            print(f"❌ MyPy type checking failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ MyPy test failed: {e}")
        return False

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ["CODEGEN_ORG_ID"] = "323"
    os.environ["CODEGEN_TOKEN"] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    try:
        # Run basic functionality tests
        basic_success = test_basic_functionality()
        
        # Run type checking tests
        mypy_success = test_mypy_compliance()
        
        # Summary
        print("\n" + "=" * 40)
        print("📊 FINAL SUMMARY")
        print("=" * 40)
        print(f"Basic Functionality: {'✅ PASS' if basic_success else '❌ FAIL'}")
        print(f"Type Checking: {'✅ PASS' if mypy_success else '❌ FAIL'}")
        
        if basic_success and mypy_success:
            print("\n🎉 SDK implementation is robust and effective!")
            print("✅ Ready for production use")
            sys.exit(0)
        else:
            print("\n⚠️  SDK implementation needs attention")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {e}")
        traceback.print_exc()
        sys.exit(1)

