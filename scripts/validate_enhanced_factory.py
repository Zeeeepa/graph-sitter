#!/usr/bin/env python3
"""
Validation script for the enhanced AI provider factory system.

This script validates that the factory patterns from alternate PRs have been
successfully integrated into PR #172.
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_factory_imports():
    """Test that all factory components can be imported correctly."""
    logger.info("🧪 Testing factory imports...")
    
    try:
        # Test core factory imports
        from graph_sitter.ai.providers import (
            AIProvider, AIResponse, create_ai_provider,
            CodegenProvider, OpenAIProvider
        )
        logger.info("✅ Core factory imports successful")
        
        # Test factory functions
        from graph_sitter.ai.providers import (
            get_provider_status,
            get_provider_comparison,
            detect_available_credentials,
            get_best_provider
        )
        logger.info("✅ Factory function imports successful")
        
        # Test exceptions
        from graph_sitter.ai.providers import (
            ProviderUnavailableError,
            ProviderAuthenticationError,
            ProviderRateLimitError,
            ProviderTimeoutError
        )
        logger.info("✅ Factory exception imports successful")
        
        # Test enhanced client
        from graph_sitter.ai.client import get_ai_client, generate_ai_response
        logger.info("✅ Enhanced client imports successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Factory import test failed: {e}")
        return False


def test_provider_detection():
    """Test provider credential detection and status."""
    logger.info("🧪 Testing provider detection...")
    
    try:
        from graph_sitter.ai.providers import detect_available_credentials, get_provider_status
        
        # Set test credentials
        os.environ["CODEGEN_ORG_ID"] = "323"
        os.environ["CODEGEN_TOKEN"] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        
        # Test credential detection
        credentials = detect_available_credentials()
        logger.info(f"📊 Detected credentials: {credentials}")
        
        # Test provider status
        status = get_provider_status()
        logger.info(f"📊 Provider status: {list(status.keys())}")
        
        # Validate structure
        for provider_name, provider_status in status.items():
            required_keys = ['is_available', 'credentials', 'stats', 'provider_class']
            for key in required_keys:
                if key not in provider_status:
                    raise ValueError(f"Missing key '{key}' in {provider_name} status")
        
        logger.info("✅ Provider detection test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Provider detection test failed: {e}")
        return False


def test_factory_creation():
    """Test provider creation using factory patterns."""
    logger.info("🧪 Testing factory creation...")
    
    try:
        from graph_sitter.ai.providers import create_ai_provider, CodegenProvider, OpenAIProvider
        
        # Test automatic provider creation
        provider = create_ai_provider(
            prefer_codegen=True,
            validate_on_creation=False  # Don't validate to avoid API calls
        )
        logger.info(f"✅ Auto-created provider: {provider.provider_name}")
        
        # Test explicit provider creation
        codegen_provider = create_ai_provider(
            provider_name="codegen",
            validate_on_creation=False
        )
        logger.info(f"✅ Explicit Codegen provider: {codegen_provider.provider_name}")
        
        openai_provider = create_ai_provider(
            provider_name="openai",
            validate_on_creation=False
        )
        logger.info(f"✅ Explicit OpenAI provider: {openai_provider.provider_name}")
        
        # Test provider methods
        models = codegen_provider.get_available_models()
        logger.info(f"📋 Codegen models: {models}")
        
        models = openai_provider.get_available_models()
        logger.info(f"📋 OpenAI models: {models}")
        
        # Test stats
        stats = codegen_provider.get_stats()
        logger.info(f"📊 Codegen stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Factory creation test failed: {e}")
        return False


def test_enhanced_features():
    """Test enhanced factory features."""
    logger.info("🧪 Testing enhanced factory features...")
    
    try:
        from graph_sitter.ai.providers import (
            get_provider_comparison,
            get_best_provider,
            list_available_providers
        )
        
        # Test provider comparison
        comparison = get_provider_comparison()
        required_keys = ['providers', 'available_providers', 'total_providers', 'summary']
        for key in required_keys:
            if key not in comparison:
                raise ValueError(f"Missing key '{key}' in provider comparison")
        
        logger.info(f"📊 Provider comparison: {comparison['summary']}")
        
        # Test best provider selection
        best_provider = get_best_provider(
            task_type="code_generation",
            prefer_codegen=True,
            validate_on_creation=False
        )
        logger.info(f"🎯 Best provider for code generation: {best_provider.provider_name}")
        
        # Test available providers list
        available = list_available_providers()
        logger.info(f"📋 Available provider types: {available}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced features test failed: {e}")
        return False


def test_client_integration():
    """Test enhanced client integration."""
    logger.info("🧪 Testing client integration...")
    
    try:
        from graph_sitter.ai.client import get_ai_client, generate_ai_response
        
        # Test client creation
        client = get_ai_client(prefer_codegen=True)
        logger.info(f"✅ Client created: {client.provider_name}")
        
        # Test explicit client creation
        codegen_client = get_ai_client(provider_name="codegen")
        logger.info(f"✅ Codegen client: {codegen_client.provider_name}")
        
        openai_client = get_ai_client(provider_name="openai")
        logger.info(f"✅ OpenAI client: {openai_client.provider_name}")
        
        # Test convenience function (without actual API call)
        logger.info("✅ Convenience function available")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Client integration test failed: {e}")
        return False


def test_backward_compatibility():
    """Test backward compatibility with existing code."""
    logger.info("🧪 Testing backward compatibility...")
    
    try:
        # Test legacy function still works
        from graph_sitter.ai.client import get_openai_client
        
        # This should work without breaking existing code
        legacy_client = get_openai_client("test_key")
        logger.info(f"✅ Legacy function works: {type(legacy_client).__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Backward compatibility test failed: {e}")
        return False


def test_error_handling():
    """Test enhanced error handling."""
    logger.info("🧪 Testing error handling...")
    
    try:
        from graph_sitter.ai.providers import (
            create_ai_provider,
            ProviderUnavailableError,
            ProviderAuthenticationError,
            ProviderRateLimitError,
            ProviderTimeoutError
        )
        
        # Test invalid provider name
        try:
            create_ai_provider(
                provider_name="nonexistent",
                fallback_enabled=False
            )
            logger.error("❌ Should have raised ProviderUnavailableError")
            return False
        except ProviderUnavailableError:
            logger.info("✅ ProviderUnavailableError correctly raised")
        
        # Test exception classes exist and are usable
        test_exceptions = [
            ProviderUnavailableError("test"),
            ProviderAuthenticationError("test"),
            ProviderRateLimitError("test", retry_after=60),
            ProviderTimeoutError("test", timeout_duration=30.0)
        ]
        
        for exc in test_exceptions:
            logger.info(f"✅ Exception class works: {type(exc).__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 Enhanced Factory Pattern Validation")
    print("=" * 50)
    
    tests = [
        ("Factory Imports", test_factory_imports),
        ("Provider Detection", test_provider_detection),
        ("Factory Creation", test_factory_creation),
        ("Enhanced Features", test_enhanced_features),
        ("Client Integration", test_client_integration),
        ("Backward Compatibility", test_backward_compatibility),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Factory patterns successfully integrated.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

