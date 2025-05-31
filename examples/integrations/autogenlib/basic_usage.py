#!/usr/bin/env python3
"""
Basic usage example for AutogenLib integration with graph-sitter.

This example demonstrates how to use the AutogenLib integration to generate
code dynamically with enhanced context from graph-sitter analysis.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from graph_sitter.integrations.autogenlib import (
    AutogenLibIntegration,
    AutogenLibConfig,
    GenerationRequest
)


def main():
    """Demonstrate basic AutogenLib integration usage."""
    
    print("🚀 AutogenLib Integration Example")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY=your-openai-api-key")
        return
    
    # Configure the integration
    config = AutogenLibConfig(
        enabled=True,
        openai_api_key=api_key,
        openai_model="gpt-4",
        use_graph_sitter_context=True,
        enable_caching=True,
        max_context_size=8000,
        temperature=0.1,
        allowed_namespaces=["autogenlib.examples", "autogenlib.generated"]
    )
    
    print("📋 Configuration:")
    print(f"   Model: {config.openai_model}")
    print(f"   Context: {'✅' if config.use_graph_sitter_context else '❌'}")
    print(f"   Caching: {'✅' if config.enable_caching else '❌'}")
    print()
    
    # Initialize the integration
    try:
        integration = AutogenLibIntegration(config)
        
        if not integration.is_enabled():
            print("❌ Integration failed to initialize")
            return
            
        print("✅ Integration initialized successfully")
        
        # Validate configuration
        validation = integration.validate_configuration()
        if not validation["valid"]:
            print("❌ Configuration validation failed:")
            for error in validation["errors"]:
                print(f"   - {error}")
            return
            
        if validation["warnings"]:
            print("⚠️  Configuration warnings:")
            for warning in validation["warnings"]:
                print(f"   - {warning}")
        
        print()
        
    except Exception as e:
        print(f"❌ Failed to initialize integration: {e}")
        return
    
    # Example 1: Generate a utility function
    print("📝 Example 1: Generate utility function")
    print("-" * 30)
    
    result1 = integration.generate_missing_implementation(
        module_name="autogenlib.examples.utils",
        function_name="format_currency",
        description="Format a number as currency with proper locale formatting"
    )
    
    if result1.success:
        print("✅ Generation successful!")
        print(f"⏱️  Time: {result1.generation_time:.2f}s")
        print("\nGenerated code:")
        print("```python")
        print(result1.code)
        print("```")
    else:
        print(f"❌ Generation failed: {result1.error}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Generate a data class using template
    print("📝 Example 2: Generate data class template")
    print("-" * 30)
    
    result2 = integration.generate_template_code(
        template_type="data_model",
        parameters={
            "module_name": "autogenlib.examples.models",
            "class_name": "UserProfile",
            "fields": ["name", "email", "age", "created_at"],
            "validation": True,
            "serialization": True
        }
    )
    
    if result2.success:
        print("✅ Template generation successful!")
        print(f"⏱️  Time: {result2.generation_time:.2f}s")
        print("\nGenerated code:")
        print("```python")
        print(result2.code)
        print("```")
    else:
        print(f"❌ Template generation failed: {result2.error}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Code completion suggestions
    print("📝 Example 3: Code completion suggestions")
    print("-" * 30)
    
    context_code = """
def process_user_data(users):
    \"\"\"Process a list of user data.\"\"\"
    results = []
    for user in users:
        # Need to validate and format user data
        
"""
    
    suggestions = integration.suggest_code_completion(
        context=context_code,
        cursor_position=len(context_code) - 10,
        max_suggestions=3
    )
    
    if suggestions:
        print("✅ Code completion suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion['type']}: {suggestion['description']}")
            print(f"   Confidence: {suggestion.get('confidence', 'N/A')}")
            if 'text' in suggestion:
                print(f"   Code: {suggestion['text'][:100]}...")
    else:
        print("ℹ️  No completion suggestions available")
    
    print("\n" + "="*50 + "\n")
    
    # Example 4: Refactoring suggestions
    print("📝 Example 4: Refactoring suggestions")
    print("-" * 30)
    
    code_to_refactor = """
def complex_function(data):
    if data is not None:
        if len(data) > 0:
            if isinstance(data, list):
                result = []
                for item in data:
                    if item is not None:
                        if hasattr(item, 'value'):
                            if item.value > 0:
                                result.append(item.value * 2)
                return result
    return None
"""
    
    refactor_suggestions = integration.generate_refactoring_suggestions(
        code=code_to_refactor
    )
    
    if refactor_suggestions:
        print("✅ Refactoring suggestions:")
        for i, suggestion in enumerate(refactor_suggestions, 1):
            print(f"\n{i}. {suggestion['type']}: {suggestion['description']}")
            print(f"   Confidence: {suggestion.get('confidence', 'N/A')}")
            if 'details' in suggestion:
                print(f"   Details: {suggestion['details']}")
    else:
        print("ℹ️  No refactoring suggestions available")
    
    print("\n" + "="*50 + "\n")
    
    # Show statistics
    print("📊 Integration Statistics")
    print("-" * 30)
    
    stats = integration.get_statistics()
    print(f"Status: {'✅ Enabled' if stats['enabled'] else '❌ Disabled'}")
    
    if stats.get('total_generations') is not None:
        print(f"Total Generations: {stats['total_generations']}")
        print(f"Successful: {stats.get('successful_generations', 0)}")
        print(f"Failed: {stats.get('failed_generations', 0)}")
        
        if stats['total_generations'] > 0:
            success_rate = (stats.get('successful_generations', 0) / stats['total_generations']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
    
    print("\n🎉 Example completed successfully!")


if __name__ == "__main__":
    main()

