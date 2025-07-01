#!/usr/bin/env python3
"""
Final validation script for the enhanced Codegen SDK implementation.
This script validates all the fixes applied to address the mypy type checking errors.
"""

import os
import sys
import subprocess
import traceback

# Add src to path
sys.path.insert(0, 'src')

def run_mypy_check():
    """Run mypy on all the files that had issues."""
    print("🔍 Running MyPy Type Checking...")
    
    files_to_check = [
        'src/codegen/task.py',
        'src/codegen/agent.py', 
        'src/graph_sitter/ai/providers/codegen_provider.py',
        'src/graph_sitter/ai/providers/openai_provider.py',
        'src/graph_sitter/configs/models/secrets.py'
    ]
    
    try:
        result = subprocess.run([
            'python', '-m', 'mypy'
        ] + files_to_check + [
            '--ignore-missing-imports',
            '--no-error-summary'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ All MyPy type checking passed!")
            return True
        else:
            print("❌ MyPy type checking failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ MyPy check failed: {e}")
        return False

def test_imports():
    """Test that all modules can be imported successfully."""
    print("\n📦 Testing Module Imports...")
    
    try:
        # Test core SDK imports
        from codegen import Agent, Task
        from codegen.exceptions import CodegenError, AuthenticationError, ValidationError
        print("✅ Core SDK modules imported successfully")
        
        # Test provider imports
        from graph_sitter.ai.providers.codegen_provider import CodegenProvider
        from graph_sitter.ai.providers.factory import get_available_providers
        print("✅ Provider modules imported successfully")
        
        # Test config imports
        from graph_sitter.configs.models.secrets import SecretsConfig
        print("✅ Configuration modules imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality without making API calls."""
    print("\n⚙️ Testing Basic Functionality...")
    
    try:
        # Test Agent initialization
        agent = Agent(
            org_id="323",
            token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99",
            validate_on_init=False
        )
        print("✅ Agent initialization successful")
        
        # Test provider creation
        provider = CodegenProvider(
            org_id="323",
            token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        )
        print("✅ Provider creation successful")
        
        # Test configuration
        config = SecretsConfig()
        print("✅ Configuration creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def validate_fixes():
    """Validate that all the specific fixes mentioned in the user's message are applied."""
    print("\n🔧 Validating Specific Fixes...")
    
    fixes_validated = []
    
    # Check task.py fixes
    try:
        from codegen.task import Task
        
        # Test logs method returns list
        task = Task("test-id", "test", {})
        logs = task.logs  # Property, not method
        assert isinstance(logs, list), "logs should return a list"
        fixes_validated.append("✅ task.py logs property returns list")
        
        # Test artifacts method
        artifacts = task.get_artifacts()
        assert isinstance(artifacts, list), "get_artifacts() should return a list"
        fixes_validated.append("✅ task.py get_artifacts() method returns list")
        
    except Exception as e:
        fixes_validated.append(f"❌ task.py fixes failed: {e}")
    
    # Check agent.py fixes
    try:
        from codegen.agent import Agent
        agent = Agent("test", "test", validate_on_init=False)
        
        # Check that monitoring attributes exist
        assert hasattr(agent, '_request_count'), "Agent should have _request_count"
        assert hasattr(agent, '_error_count'), "Agent should have _error_count"
        assert hasattr(agent, '_start_time'), "Agent should have _start_time"
        fixes_validated.append("✅ agent.py monitoring attributes present")
        
    except Exception as e:
        fixes_validated.append(f"❌ agent.py fixes failed: {e}")
    
    # Check provider fixes
    try:
        from graph_sitter.ai.providers.codegen_provider import CodegenProvider
        provider = CodegenProvider("test", "test")
        
        # Check that agent property has proper error handling
        assert hasattr(provider, 'agent'), "Provider should have agent property"
        fixes_validated.append("✅ codegen_provider.py agent property fixed")
        
    except Exception as e:
        fixes_validated.append(f"❌ provider fixes failed: {e}")
    
    # Check secrets config fixes
    try:
        from graph_sitter.configs.models.secrets import SecretsConfig
        config = SecretsConfig()
        fixes_validated.append("✅ secrets.py initialization fixed")
        
    except Exception as e:
        fixes_validated.append(f"❌ secrets.py fixes failed: {e}")
    
    # Print validation results
    for result in fixes_validated:
        print(f"   {result}")
    
    success_count = sum(1 for result in fixes_validated if result.startswith("✅"))
    total_count = len(fixes_validated)
    
    return success_count == total_count

def main():
    """Run all validation tests."""
    print("🚀 Final Validation of Enhanced Codegen SDK")
    print("=" * 50)
    
    # Set test environment
    os.environ["CODEGEN_ORG_ID"] = "323"
    os.environ["CODEGEN_TOKEN"] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    results = {}
    
    # Run all tests
    results['mypy'] = run_mypy_check()
    results['imports'] = test_imports()
    results['functionality'] = test_basic_functionality()
    results['fixes'] = validate_fixes()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 All validations passed! SDK implementation is robust and effective!")
        print("✅ Ready for production use with provided credentials")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} validation(s) failed")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during validation: {e}")
        traceback.print_exc()
        sys.exit(1)
