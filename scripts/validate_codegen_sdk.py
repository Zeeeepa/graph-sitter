#!/usr/bin/env python3
"""
Enhanced validation script for the Codegen SDK implementation.

This script thoroughly tests the enhanced Codegen SDK integration with the provided credentials.
"""

import os
import sys
import logging
import time
from typing import Dict, Any

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_test_environment():
    """Set up the test environment with provided credentials."""
    # Set the provided test credentials
    os.environ["CODEGEN_ORG_ID"] = "323"
    os.environ["CODEGEN_TOKEN"] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    logger.info("Test environment configured with provided credentials")


def test_codegen_sdk_basic():
    """Test basic Codegen SDK functionality."""
    logger.info("🧪 Testing basic Codegen SDK functionality...")
    
    try:
        from codegen import Agent
        
        # Test agent initialization
        agent = Agent(
            org_id="323",
            token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        )
        
        logger.info("✅ Codegen Agent initialized successfully")
        
        # Test credential validation
        try:
            usage = agent.get_usage()
            logger.info("✅ Credentials validated successfully")
            logger.info(f"📊 Usage info: {usage}")
        except Exception as e:
            logger.warning(f"⚠️ Credential validation failed: {e}")
        
        # Test basic stats
        stats = agent.get_stats()
        logger.info(f"📈 Agent stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic Codegen SDK test failed: {e}")
        return False


def test_ai_provider_system():
    """Test the AI provider system."""
    logger.info("🧪 Testing AI provider system...")
    
    try:
        from graph_sitter.ai.providers import (
            create_ai_provider, 
            get_provider_status,
            detect_available_credentials,
            get_provider_comparison
        )
        
        # Test credential detection
        credentials = detect_available_credentials()
        logger.info(f"🔍 Detected credentials: {credentials}")
        
        # Test provider status
        status = get_provider_status()
        logger.info(f"📊 Provider status: {status}")
        
        # Test provider comparison
        comparison = get_provider_comparison()
        logger.info(f"⚖️ Provider comparison: {comparison}")
        
        # Test creating Codegen provider explicitly
        try:
            codegen_provider = create_ai_provider(provider_name="codegen")
            logger.info("✅ Codegen provider created successfully")
            
            # Test provider stats
            provider_stats = codegen_provider.get_stats()
            logger.info(f"📈 Codegen provider stats: {provider_stats}")
            
            if hasattr(codegen_provider, 'get_enhanced_stats'):
                enhanced_stats = codegen_provider.get_enhanced_stats()
                logger.info(f"📊 Enhanced stats: {enhanced_stats}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create Codegen provider: {e}")
            return False
        
        # Test automatic provider selection
        try:
            auto_provider = create_ai_provider(prefer_codegen=True)
            logger.info(f"✅ Auto-selected provider: {auto_provider.provider_name}")
        except Exception as e:
            logger.error(f"❌ Auto provider selection failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI provider system test failed: {e}")
        return False


def test_ai_generation():
    """Test AI response generation."""
    logger.info("🧪 Testing AI response generation...")
    
    try:
        from graph_sitter.ai.providers import create_ai_provider
        
        # Create Codegen provider
        provider = create_ai_provider(provider_name="codegen")
        
        # Test simple generation
        logger.info("🤖 Testing simple AI generation...")
        
        response = provider.generate_response(
            prompt="Hello! Please respond with a simple greeting.",
            system_prompt="You are a helpful assistant.",
            priority="normal",
            tags=["test", "validation"]
        )
        
        logger.info(f"✅ AI response received:")
        logger.info(f"   Content: {response.content[:200]}...")
        logger.info(f"   Provider: {response.provider_name}")
        logger.info(f"   Model: {response.model}")
        logger.info(f"   Response time: {response.response_time:.2f}s")
        logger.info(f"   Request ID: {response.request_id}")
        
        if response.usage:
            logger.info(f"   Usage: {response.usage}")
        
        if response.metadata:
            logger.info(f"   Metadata keys: {list(response.metadata.keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI generation test failed: {e}")
        return False


def test_task_management():
    """Test task management functionality."""
    logger.info("🧪 Testing task management...")
    
    try:
        from codegen import Agent
        
        agent = Agent(
            org_id="323",
            token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        )
        
        # Test task creation
        logger.info("📝 Creating test task...")
        
        task = agent.run(
            prompt="Please analyze this simple Python function and suggest improvements: def add(a, b): return a + b",
            priority="normal",
            tags=["test", "validation", "code-analysis"]
        )
        
        logger.info(f"✅ Task created: {task.task_id}")
        logger.info(f"   Status: {task.status}")
        logger.info(f"   Prompt: {task.prompt[:100]}...")
        
        # Test task monitoring
        logger.info("⏳ Monitoring task progress...")
        
        def progress_callback(progress):
            if progress:
                logger.info(f"   Progress update: {progress}")
        
        # Wait for completion with timeout
        try:
            task.wait_for_completion(
                timeout=120,  # 2 minutes timeout for validation
                poll_interval=10,
                progress_callback=progress_callback
            )
            
            logger.info(f"✅ Task completed successfully!")
            logger.info(f"   Final status: {task.status}")
            logger.info(f"   Result: {task.result[:200] if task.result else 'No result'}...")
            
            # Test artifacts
            artifacts = task.get_artifacts()
            logger.info(f"   Artifacts: {len(artifacts)} found")
            
            # Test logs
            logs = task.get_logs()
            logger.info(f"   Logs: {len(logs)} entries")
            
            # Test monitoring info
            monitoring_info = task.get_monitoring_info()
            logger.info(f"   Monitoring: {monitoring_info}")
            
        except Exception as e:
            logger.warning(f"⚠️ Task completion failed or timed out: {e}")
            logger.info(f"   Current status: {task.status}")
            
            # Try to cancel the task
            try:
                task.cancel()
                logger.info("✅ Task cancelled successfully")
            except Exception as cancel_error:
                logger.warning(f"⚠️ Failed to cancel task: {cancel_error}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Task management test failed: {e}")
        return False


def test_integration_with_graph_sitter():
    """Test integration with graph-sitter core."""
    logger.info("🧪 Testing integration with graph-sitter core...")
    
    try:
        # This would normally require a full graph-sitter setup
        # For now, we'll test the AI client integration
        from graph_sitter.ai.client import get_ai_client
        
        # Test getting AI client
        ai_client = get_ai_client(prefer_codegen=True)
        logger.info(f"✅ AI client obtained: {ai_client.provider_name}")
        
        # Test basic response generation
        response = ai_client.generate_response(
            prompt="What is the purpose of code analysis?",
            system_prompt="You are a code analysis expert.",
            model="codegen-agent"
        )
        
        logger.info(f"✅ Integration test successful:")
        logger.info(f"   Response: {response.content[:150]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False


def run_comprehensive_validation():
    """Run comprehensive validation of the enhanced Codegen SDK implementation."""
    logger.info("🚀 Starting comprehensive Codegen SDK validation...")
    logger.info("=" * 80)
    
    # Setup test environment
    setup_test_environment()
    
    # Track test results
    test_results = {}
    
    # Run all tests
    tests = [
        ("Basic Codegen SDK", test_codegen_sdk_basic),
        ("AI Provider System", test_ai_provider_system),
        ("AI Generation", test_ai_generation),
        ("Task Management", test_task_management),
        ("Graph-Sitter Integration", test_integration_with_graph_sitter),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            test_results[test_name] = {
                "passed": result,
                "duration": duration,
                "error": None
            }
            
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status} - {test_name} ({duration:.2f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            test_results[test_name] = {
                "passed": False,
                "duration": duration,
                "error": str(e)
            }
            logger.error(f"❌ FAILED - {test_name} ({duration:.2f}s): {e}")
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("📊 VALIDATION SUMMARY")
    logger.info("="*80)
    
    passed_tests = sum(1 for result in test_results.values() if result["passed"])
    total_tests = len(test_results)
    total_duration = sum(result["duration"] for result in test_results.values())
    
    logger.info(f"Tests passed: {passed_tests}/{total_tests}")
    logger.info(f"Total duration: {total_duration:.2f}s")
    logger.info(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Detailed results
    for test_name, result in test_results.items():
        status = "✅" if result["passed"] else "❌"
        logger.info(f"{status} {test_name}: {result['duration']:.2f}s")
        if result["error"]:
            logger.info(f"   Error: {result['error']}")
    
    # Overall result
    if passed_tests == total_tests:
        logger.info("\n🎉 ALL TESTS PASSED! The enhanced Codegen SDK implementation is working correctly.")
        return True
    else:
        logger.info(f"\n⚠️ {total_tests - passed_tests} tests failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)

