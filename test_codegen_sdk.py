#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced Codegen SDK implementation.
Tests with provided credentials: CODEGEN_ORG_ID=323, CODEGEN_TOKEN=sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99
"""

import os
import sys
import time
import traceback
from typing import Dict, Any

# Add src to path
sys.path.insert(0, 'src')

from codegen import Agent, Task
from codegen.exceptions import CodegenError, AuthenticationError, ValidationError

def test_agent_initialization():
    """Test agent initialization with provided credentials."""
    print("🔧 Testing Agent Initialization...")
    
    try:
        # Test with provided credentials
        agent = Agent(
            org_id="323",
            token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        )
        print("✅ Agent initialized successfully")
        return agent
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        traceback.print_exc()
        return None

def test_agent_validation(agent: Agent):
    """Test agent credential validation."""
    print("\n🔐 Testing Credential Validation...")
    
    try:
        # Test validation
        is_valid = agent.validate_credentials()
        if is_valid:
            print("✅ Credentials validated successfully")
        else:
            print("❌ Credential validation failed")
        return is_valid
    except Exception as e:
        print(f"❌ Validation error: {e}")
        traceback.print_exc()
        return False

def test_task_creation(agent: Agent):
    """Test task creation with various parameters."""
    print("\n📝 Testing Task Creation...")
    
    try:
        # Test basic task creation
        task = agent.run(
            prompt="Test task: Analyze the current codebase structure",
            priority="normal"
        )
        
        print(f"✅ Task created successfully: {task.id}")
        print(f"   Status: {task.status}")
        print(f"   Priority: {task.priority}")
        
        return task
    except Exception as e:
        print(f"❌ Task creation failed: {e}")
        traceback.print_exc()
        return None

def test_task_monitoring(task: Task):
    """Test task monitoring and status updates."""
    print("\n📊 Testing Task Monitoring...")
    
    try:
        # Monitor task for a short period
        max_checks = 5
        check_count = 0
        
        while check_count < max_checks:
            print(f"   Check {check_count + 1}: Status = {task.status}")
            
            if task.status in ["completed", "failed", "cancelled"]:
                break
                
            time.sleep(2)
            task.refresh()
            check_count += 1
        
        print(f"✅ Task monitoring completed. Final status: {task.status}")
        
        # Test logs access
        logs = task.logs()
        print(f"   Logs available: {len(logs)} entries")
        
        return True
    except Exception as e:
        print(f"❌ Task monitoring failed: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling scenarios."""
    print("\n🚨 Testing Error Handling...")
    
    try:
        # Test invalid credentials
        print("   Testing invalid credentials...")
        try:
            invalid_agent = Agent(org_id="invalid", token="invalid")
            invalid_agent.validate_credentials()
            print("❌ Should have failed with invalid credentials")
        except AuthenticationError:
            print("✅ Correctly caught authentication error")
        except Exception as e:
            print(f"⚠️  Unexpected error type: {e}")
        
        # Test invalid priority
        print("   Testing invalid priority...")
        try:
            agent = Agent(org_id="323", token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99")
            agent.run(prompt="Test", priority="invalid")
            print("❌ Should have failed with invalid priority")
        except ValidationError:
            print("✅ Correctly caught validation error")
        except Exception as e:
            print(f"⚠️  Unexpected error type: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        traceback.print_exc()
        return False

def test_provider_integration():
    """Test provider integration functionality."""
    print("\n🔌 Testing Provider Integration...")
    
    try:
        from graph_sitter.ai.providers.codegen_provider import CodegenProvider
        from graph_sitter.ai.providers.factory import get_provider_status, get_recommended_provider
        
        # Test provider creation
        provider = CodegenProvider(
            org_id="323",
            token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        )
        print("✅ CodegenProvider created successfully")
        
        # Test provider validation
        is_valid = provider.validate_credentials()
        print(f"   Credential validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        # Test provider status
        status = get_provider_status()
        print(f"   Provider status retrieved: {len(status)} providers")
        
        # Test recommended provider
        recommended = get_recommended_provider()
        print(f"   Recommended provider: {recommended}")
        
        return True
    except Exception as e:
        print(f"❌ Provider integration test failed: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("🚀 Starting Comprehensive Codegen SDK Test")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Agent Initialization
    agent = test_agent_initialization()
    results['initialization'] = agent is not None
    
    if not agent:
        print("\n❌ Cannot continue tests without valid agent")
        return results
    
    # Test 2: Credential Validation
    results['validation'] = test_agent_validation(agent)
    
    # Test 3: Task Creation
    task = test_task_creation(agent)
    results['task_creation'] = task is not None
    
    # Test 4: Task Monitoring (if task was created)
    if task:
        results['task_monitoring'] = test_task_monitoring(task)
    else:
        results['task_monitoring'] = False
    
    # Test 5: Error Handling
    results['error_handling'] = test_error_handling()
    
    # Test 6: Provider Integration
    results['provider_integration'] = test_provider_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    success_rate = (passed_tests / total_tests) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 SDK implementation is robust and ready for production!")
    elif success_rate >= 60:
        print("⚠️  SDK implementation needs minor improvements")
    else:
        print("❌ SDK implementation needs significant improvements")
    
    return results

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ["CODEGEN_ORG_ID"] = "323"
    os.environ["CODEGEN_TOKEN"] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    try:
        results = run_comprehensive_test()
        
        # Exit with appropriate code
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        success_rate = (passed_tests / total_tests) * 100
        
        if success_rate >= 80:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {e}")
        traceback.print_exc()
        sys.exit(1)
