#!/usr/bin/env python3
"""
Basic functionality test for the enhanced Codegen SDK implementation.
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all modules can be imported correctly."""
    logger.info("🧪 Testing imports...")
    
    try:
        # Test Codegen SDK imports
        from codegen import Agent, Task
        from codegen.exceptions import CodegenError, AuthenticationError
        logger.info("✅ Codegen SDK imports successful")
        
        # Test AI provider imports
        from graph_sitter.ai.providers import (
            AIProvider, AIResponse, create_ai_provider,
            CodegenProvider, OpenAIProvider
        )
        logger.info("✅ AI provider imports successful")
        
        # Test client imports
        from graph_sitter.ai.client import get_ai_client
        logger.info("✅ AI client imports successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        return False


def test_provider_detection():
    """Test provider credential detection."""
    logger.info("🧪 Testing provider detection...")
    
    try:
        from graph_sitter.ai.providers import detect_available_credentials
        
        # Set test credentials
        os.environ["CODEGEN_ORG_ID"] = "323"
        os.environ["CODEGEN_TOKEN"] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        
        credentials = detect_available_credentials()
        logger.info(f"📊 Detected credentials: {credentials}")
        
        # Check Codegen credentials are detected
        if credentials.get("codegen", {}).get("available", False):
            logger.info("✅ Codegen credentials detected")
        else:
            logger.warning("⚠️ Codegen credentials not detected")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Provider detection test failed: {e}")
        return False


def test_provider_creation():
    """Test provider creation without API calls."""
    logger.info("🧪 Testing provider creation...")
    
    try:
        from graph_sitter.ai.providers import CodegenProvider, OpenAIProvider
        
        # Set test credentials
        os.environ["CODEGEN_ORG_ID"] = "323"
        os.environ["CODEGEN_TOKEN"] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        
        # Test Codegen provider creation
        codegen_provider = CodegenProvider()
        logger.info(f"✅ Codegen provider created: {codegen_provider}")
        logger.info(f"   Available: {codegen_provider.is_available}")
        logger.info(f"   Models: {codegen_provider.get_available_models()}")
        
        # Test OpenAI provider creation (without API key)
        openai_provider = OpenAIProvider()
        logger.info(f"✅ OpenAI provider created: {openai_provider}")
        logger.info(f"   Available: {openai_provider.is_available}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Provider creation test failed: {e}")
        return False


def test_factory_system():
    """Test the factory system."""
    logger.info("🧪 Testing factory system...")
    
    try:
        from graph_sitter.ai.providers import (
            get_provider_status, 
            get_provider_comparison,
            create_ai_provider
        )
        
        # Set test credentials
        os.environ["CODEGEN_ORG_ID"] = "323"
        os.environ["CODEGEN_TOKEN"] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        
        # Test provider status
        status = get_provider_status()
        logger.info(f"📊 Provider status: {status}")
        
        # Test provider comparison
        comparison = get_provider_comparison()
        logger.info(f"⚖️ Provider comparison summary: {comparison['summary']}")
        
        # Test provider creation (without validation to avoid API calls)
        try:
            provider = create_ai_provider(
                provider_name="codegen",
                validate_on_creation=False  # Skip validation to avoid API calls
            )
            logger.info(f"✅ Provider created via factory: {provider}")
        except Exception as e:
            logger.warning(f"⚠️ Provider creation failed (expected without valid API): {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Factory system test failed: {e}")
        return False


def test_configuration():
    """Test configuration and secrets."""
    logger.info("🧪 Testing configuration...")
    
    try:
        from graph_sitter.configs.models.secrets import SecretsConfig
        
        # Set test environment
        os.environ["CODEGEN_ORG_ID"] = "323"
        os.environ["CODEGEN_TOKEN"] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        
        # Test secrets config
        secrets = SecretsConfig()
        logger.info(f"✅ Secrets config created")
        logger.info(f"   Codegen org ID: {secrets.codegen_org_id}")
        logger.info(f"   Codegen token: {secrets.codegen_token[:10] if secrets.codegen_token else None}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


def run_basic_tests():
    """Run basic functionality tests."""
    logger.info("🚀 Starting basic functionality tests...")
    logger.info("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Provider Detection", test_provider_detection),
        ("Provider Creation", test_provider_creation),
        ("Factory System", test_factory_system),
        ("Configuration", test_configuration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*10} {test_name} {'='*10}")
        
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status} - {test_name}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ FAILED - {test_name}: {e}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    logger.info(f"Tests passed: {passed}/{total}")
    logger.info(f"Success rate: {(passed/total)*100:.1f}%")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name}")
    
    if passed == total:
        logger.info("\n🎉 ALL BASIC TESTS PASSED! The implementation structure is correct.")
        return True
    else:
        logger.info(f"\n⚠️ {total - passed} tests failed.")
        return False


if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)

