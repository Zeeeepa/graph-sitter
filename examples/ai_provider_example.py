#!/usr/bin/env python3
"""
Enhanced example demonstrating the AI provider factory system in graph-sitter.

This example shows how to:
1. Use automatic provider selection with factory patterns
2. Explicitly choose providers using the factory
3. Handle different response types and errors
4. Work with both OpenAI and Codegen SDK
5. Monitor provider status and performance
6. Use advanced factory features
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter import Codebase
from graph_sitter.ai.client import get_ai_client, generate_ai_response
from graph_sitter.ai.providers import (
    create_ai_provider,
    get_provider_status,
    get_provider_comparison,
    detect_available_credentials,
    get_best_provider,
    ProviderUnavailableError,
    ProviderRateLimitError,
    ProviderTimeoutError
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Demonstrate enhanced AI provider factory usage."""
    
    # Initialize codebase
    codebase = Codebase(".")
    
    print("🤖 Enhanced AI Provider Factory System Demo")
    print("=" * 60)
    
    # 1. Provider Status and Monitoring
    print("\n1. Provider Status and Monitoring")
    print("-" * 40)
    
    try:
        # Check provider status
        status = get_provider_status()
        print("📊 Provider Status:")
        for provider_name, provider_status in status.items():
            if provider_status['is_available']:
                print(f"  ✅ {provider_name}: Available")
                stats = provider_status.get('stats', {})
                if stats.get('request_count', 0) > 0:
                    print(f"     Requests: {stats['request_count']}, Errors: {stats['error_count']}")
            else:
                print(f"  ❌ {provider_name}: {provider_status.get('error', 'Not available')}")
        
        # Get detailed comparison
        comparison = get_provider_comparison()
        print(f"\n🎯 Recommended provider: {comparison['summary']['recommended_provider']}")
        print(f"📈 Available providers: {len(comparison['available_providers'])}/{comparison['total_providers']}")
        
        # Check credentials
        credentials = detect_available_credentials()
        print("\n🔑 Credential Status:")
        for provider_name, cred_info in credentials.items():
            status_icon = "✅" if cred_info['available'] else "❌"
            print(f"  {status_icon} {provider_name}: {cred_info['details']}")
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
    
    # 2. Factory Pattern - Automatic Provider Selection
    print("\n2. Factory Pattern - Automatic Provider Selection")
    print("-" * 50)
    
    try:
        # Create provider with factory (automatic selection)
        provider = create_ai_provider(prefer_codegen=True)
        print(f"✅ Auto-selected provider: {provider.provider_name}")
        
        # Generate response using factory-created provider
        response = provider.generate_response(
            prompt="Explain what this codebase does in one sentence",
            system_prompt="You are a code analysis expert",
            model="gpt-4o",
            temperature=0.0
        )
        print(f"📝 Response: {response.content[:100]}...")
        print(f"   Provider: {response.provider_name}, Model: {response.model}")
        print(f"   Response time: {response.response_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Auto-selection failed: {e}")
    
    # 3. Factory Pattern - Explicit Provider Selection
    print("\n3. Factory Pattern - Explicit Provider Selection")
    print("-" * 50)
    
    # Try Codegen SDK with factory
    try:
        codegen_provider = create_ai_provider(
            provider_name="codegen",
            fallback_enabled=False,
            validate_on_creation=True
        )
        print(f"✅ Codegen provider created: {codegen_provider}")
        
        response = codegen_provider.generate_response(
            prompt="List the main components of this codebase",
            priority="normal",
            tags=["analysis", "components"]
        )
        print(f"📝 Codegen response: {response.content[:100]}...")
        print(f"   Task ID: {response.request_id}")
        
    except ProviderUnavailableError as e:
        print(f"⚠️ Codegen provider not available: {e}")
    except Exception as e:
        print(f"❌ Codegen provider failed: {e}")
    
    # Try OpenAI with factory
    try:
        openai_provider = create_ai_provider(
            provider_name="openai",
            fallback_enabled=False,
            validate_on_creation=True
        )
        print(f"✅ OpenAI provider created: {openai_provider}")
        
        response = openai_provider.generate_response(
            prompt="What programming languages are used in this project?",
            system_prompt="You are a helpful coding assistant",
            model="gpt-4o",
            temperature=0.0
        )
        print(f"📝 OpenAI response: {response.content[:100]}...")
        if response.usage:
            print(f"   Tokens: {response.usage['total_tokens']}")
        
    except ProviderUnavailableError as e:
        print(f"⚠️ OpenAI provider not available: {e}")
    except Exception as e:
        print(f"❌ OpenAI provider failed: {e}")
    
    # 4. Task-Specific Provider Selection
    print("\n4. Task-Specific Provider Selection")
    print("-" * 40)
    
    try:
        # Get best provider for code generation
        code_provider = get_best_provider(
            task_type="code_generation",
            prefer_codegen=True
        )
        print(f"🔧 Best provider for code generation: {code_provider.provider_name}")
        
        # Get best provider for documentation
        doc_provider = get_best_provider(
            task_type="documentation",
            prefer_codegen=False
        )
        print(f"📚 Best provider for documentation: {doc_provider.provider_name}")
        
    except Exception as e:
        print(f"❌ Task-specific selection failed: {e}")
    
    # 5. Enhanced Error Handling
    print("\n5. Enhanced Error Handling")
    print("-" * 30)
    
    try:
        # Demonstrate error handling with factory
        provider = create_ai_provider(
            provider_name="nonexistent",
            fallback_enabled=True
        )
        print(f"✅ Fallback provider selected: {provider.provider_name}")
        
    except ProviderUnavailableError as e:
        print(f"❌ No providers available: {e}")
    except ProviderRateLimitError as e:
        print(f"⏱️ Rate limited: {e}, retry after: {e.retry_after}")
    except ProviderTimeoutError as e:
        print(f"⏰ Timeout: {e}, duration: {e.timeout_duration}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # 6. Convenience Functions
    print("\n6. Convenience Functions")
    print("-" * 25)
    
    try:
        # Use convenience function for quick responses
        response = generate_ai_response(
            prompt="Generate a simple test function",
            system_prompt="You are a test writing expert",
            provider_name=None,  # Auto-select
            model="gpt-4o"
        )
        print(f"✅ Convenience function response: {response.content[:100]}...")
        print(f"   Used provider: {response.provider_name}")
        
    except Exception as e:
        print(f"❌ Convenience function failed: {e}")
    
    # 7. Provider Statistics and Monitoring
    print("\n7. Provider Statistics and Monitoring")
    print("-" * 40)
    
    try:
        # Get updated provider status after usage
        final_status = get_provider_status()
        print("📊 Final Provider Statistics:")
        
        for provider_name, provider_status in final_status.items():
            if provider_status['is_available']:
                stats = provider_status.get('stats', {})
                enhanced_stats = provider_status.get('enhanced_stats', {})
                
                print(f"  📈 {provider_name}:")
                print(f"     Requests: {stats.get('request_count', 0)}")
                print(f"     Errors: {stats.get('error_count', 0)}")
                if stats.get('request_count', 0) > 0:
                    print(f"     Success rate: {(1 - stats['error_rate']) * 100:.1f}%")
                    print(f"     Avg response time: {stats.get('average_response_time', 0):.2f}s")
                
                # Show enhanced stats if available
                if enhanced_stats:
                    if 'task_count' in enhanced_stats:
                        print(f"     Tasks: {enhanced_stats['task_count']}")
                    if 'success_rate' in enhanced_stats:
                        print(f"     Enhanced success rate: {enhanced_stats['success_rate']:.2%}")
        
    except Exception as e:
        print(f"❌ Statistics retrieval failed: {e}")
    
    # 8. Working with Codebase Integration
    print("\n8. Codebase Integration")
    print("-" * 25)
    
    try:
        # Use the enhanced system with codebase
        functions = codebase.get_functions()
        if functions:
            target_function = functions[0]
            
            # This now uses the enhanced provider system automatically
            result = codebase.ai(
                "Suggest improvements for this function",
                target=target_function
            )
            
            print(f"✅ Codebase AI analysis: {result[:100]}...")
            print(f"   Analyzed function: {target_function.name}")
        else:
            print("ℹ️ No functions found in codebase for analysis")
            
    except Exception as e:
        print(f"❌ Codebase integration failed: {e}")
    
    print("\n🎉 Enhanced Factory Demo completed!")
    print("\n💡 Key Benefits:")
    print("   • Intelligent provider selection with fallback")
    print("   • Comprehensive error handling and recovery")
    print("   • Detailed monitoring and statistics")
    print("   • Task-specific provider optimization")
    print("   • Backward compatibility with existing code")
    print("   • Production-ready robustness")


if __name__ == "__main__":
    main()
