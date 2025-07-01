#!/usr/bin/env python3
"""
Example demonstrating the AI provider system in graph-sitter.

This example shows how to:
1. Use automatic provider selection
2. Explicitly choose providers
3. Handle different response types
4. Work with both OpenAI and Codegen SDK
"""

import os
from graph_sitter import Codebase
from graph_sitter.ai.client import get_ai_client
from graph_sitter.ai.providers import create_ai_provider


def main():
    """Demonstrate AI provider usage."""
    
    # Initialize codebase
    codebase = Codebase(".")
    
    print("🤖 AI Provider System Demo")
    print("=" * 50)
    
    # 1. Automatic provider selection
    print("\n1. Automatic Provider Selection")
    print("-" * 30)
    
    try:
        # This will automatically choose the best available provider
        result = codebase.ai(
            "Explain what this codebase does in one sentence",
            model="gpt-4o"
        )
        print(f"✅ Auto-selected provider response: {result[:100]}...")
    except Exception as e:
        print(f"❌ Auto-selection failed: {e}")
    
    # 2. Explicit provider selection
    print("\n2. Explicit Provider Selection")
    print("-" * 30)
    
    # Try Codegen SDK
    try:
        codegen_client = get_ai_client(provider_name="codegen")
        response = codegen_client.generate_response(
            prompt="List the main components of this codebase",
            system_prompt="You are a code analysis expert",
            model="gpt-4o",
            temperature=0.0
        )
        print(f"✅ Codegen SDK response: {response.content[:100]}...")
        print(f"   Provider: {response.provider_name}, Model: {response.model}")
    except Exception as e:
        print(f"❌ Codegen SDK failed: {e}")
    
    # Try OpenAI
    try:
        openai_client = get_ai_client(provider_name="openai")
        response = openai_client.generate_response(
            prompt="What programming languages are used in this project?",
            system_prompt="You are a helpful coding assistant",
            model="gpt-4o",
            temperature=0.0
        )
        print(f"✅ OpenAI response: {response.content[:100]}...")
        print(f"   Provider: {response.provider_name}, Model: {response.model}")
    except Exception as e:
        print(f"❌ OpenAI failed: {e}")
    
    # 3. Provider factory with preferences
    print("\n3. Provider Factory with Preferences")
    print("-" * 30)
    
    try:
        # Create provider with specific preferences
        provider = create_ai_provider(
            prefer_codegen=True,  # Prefer Codegen SDK
            model="gpt-4o"
        )
        
        response = provider.generate_response(
            prompt="Generate a simple test function",
            system_prompt="You are a test writing expert",
            temperature=0.1
        )
        
        print(f"✅ Factory provider response: {response.content[:100]}...")
        print(f"   Selected provider: {response.provider_name}")
    except Exception as e:
        print(f"❌ Factory provider failed: {e}")
    
    # 4. Configuration check
    print("\n4. Configuration Status")
    print("-" * 30)
    
    # Check which providers are configured
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_codegen = bool(os.getenv("CODEGEN_ORG_ID") and os.getenv("CODEGEN_TOKEN"))
    
    print(f"OpenAI configured: {'✅' if has_openai else '❌'}")
    print(f"Codegen SDK configured: {'✅' if has_codegen else '❌'}")
    
    if not (has_openai or has_codegen):
        print("\n⚠️  No AI providers configured!")
        print("Please set up at least one provider:")
        print("  - OpenAI: export OPENAI_API_KEY='your_key'")
        print("  - Codegen: export CODEGEN_ORG_ID='your_org' CODEGEN_TOKEN='your_token'")
    
    # 5. Working with code targets
    print("\n5. Working with Code Targets")
    print("-" * 30)
    
    try:
        # Find a function to analyze
        functions = codebase.get_functions()
        if functions:
            target_function = functions[0]
            
            result = codebase.ai(
                "Suggest improvements for this function",
                target=target_function,
                model="gpt-4o"
            )
            
            print(f"✅ Function analysis: {result[:100]}...")
            print(f"   Analyzed function: {target_function.name}")
        else:
            print("❌ No functions found in codebase")
    except Exception as e:
        print(f"❌ Function analysis failed: {e}")
    
    print("\n🎉 Demo completed!")


if __name__ == "__main__":
    main()

