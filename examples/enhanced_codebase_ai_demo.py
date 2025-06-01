"""
Enhanced Codebase AI Demo

Demonstrates the new AI-powered features with context-aware analysis,
supporting both OpenAI and Codegen SDK backends.
"""

import asyncio
from graph_sitter import Codebase


async def demo_enhanced_ai_features():
    """Demonstrate the enhanced AI features with rich context"""
    
    # Initialize codebase (you can use any repository)
    codebase = Codebase(".")  # Current directory
    
    # Option 1: Set OpenAI credentials
    # codebase.set_ai_key("your-openai-api-key")
    
    # Option 2: Set Codegen SDK credentials (preferred)
    # codebase.set_codegen_credentials("your-org-id", "your-token")
    
    print("🚀 Enhanced Codebase AI Demo")
    print("=" * 50)
    
    # Demo 1: Code Analysis with Context
    print("\n📊 1. Code Analysis with Rich Context")
    try:
        # Find a function to analyze
        functions = codebase.functions
        if functions:
            target_function = functions[0]
            print(f"Analyzing function: {target_function.name}")
            
            analysis = await codebase.ai(
                "Analyze this function for potential improvements and suggest optimizations",
                target=target_function,
                include_context=True
            )
            print(f"Analysis result:\n{analysis[:500]}...")
        else:
            print("No functions found in codebase")
    except Exception as e:
        print(f"Analysis demo failed: {e}")
    
    # Demo 2: Code Generation with Context
    print("\n🔧 2. Code Generation with Context")
    try:
        new_code = await codebase.ai(
            "Create a utility function to validate email addresses",
            context={
                "style": "defensive programming",
                "return_type": "bool",
                "include_docstring": True,
                "language": "python"
            }
        )
        print(f"Generated code:\n{new_code}")
    except Exception as e:
        print(f"Code generation demo failed: {e}")
    
    # Demo 3: Documentation Generation
    print("\n📚 3. Documentation Generation")
    try:
        classes = codebase.classes
        if classes:
            target_class = classes[0]
            print(f"Generating documentation for class: {target_class.name}")
            
            documentation = await codebase.ai(
                "Generate comprehensive documentation for this class",
                target=target_class,
                context={"style": "Google docstring format", "include_examples": True}
            )
            print(f"Generated documentation:\n{documentation[:500]}...")
        else:
            print("No classes found in codebase")
    except Exception as e:
        print(f"Documentation demo failed: {e}")
    
    # Demo 4: Refactoring with Full Context
    print("\n🔄 4. Contextual Refactoring")
    try:
        if functions:
            target_function = functions[0]
            print(f"Refactoring function: {target_function.name}")
            
            refactored = await codebase.ai(
                "Refactor this function to improve readability and performance",
                target=target_function,
                context={
                    "maintain_compatibility": True,
                    "focus_on": "readability",
                    "preserve_behavior": True
                }
            )
            print(f"Refactored code:\n{refactored[:500]}...")
    except Exception as e:
        print(f"Refactoring demo failed: {e}")
    
    # Demo 5: Code Quality Analysis
    print("\n🔍 5. Code Quality Analysis")
    try:
        # Analyze multiple functions
        if len(functions) > 1:
            quality_analysis = await codebase.ai(
                "Analyze the code quality of this codebase and identify potential issues",
                context={
                    "functions": functions[:5],  # First 5 functions
                    "focus_areas": ["complexity", "maintainability", "security"]
                }
            )
            print(f"Quality analysis:\n{quality_analysis[:500]}...")
    except Exception as e:
        print(f"Quality analysis demo failed: {e}")


def demo_synchronous_usage():
    """Demonstrate synchronous usage patterns"""
    
    print("\n⚡ 6. Synchronous Usage")
    
    codebase = Codebase(".")
    
    # Set credentials (choose one)
    # codebase.set_ai_key("your-openai-api-key")
    # codebase.set_codegen_credentials("your-org-id", "your-token")
    
    try:
        # Use the synchronous version
        result = codebase.ai_sync(
            "Suggest best practices for this codebase",
            context={"focus": "maintainability and scalability"}
        )
        print(f"Best practices:\n{result[:300]}...")
    except Exception as e:
        print(f"Synchronous demo failed: {e}")


def demo_context_gathering():
    """Demonstrate advanced context gathering"""
    
    print("\n🧠 7. Advanced Context Gathering")
    
    codebase = Codebase(".")
    
    # Get a function for context demonstration
    functions = codebase.functions
    if functions:
        function = functions[0]
        
        # Gather comprehensive context
        from graph_sitter.ai.context_gatherer import ContextGatherer
        
        gatherer = ContextGatherer(codebase)
        context = gatherer.gather_context(
            target=function,
            include_call_sites=True,
            include_dependencies=True,
            include_usages=True,
            include_related_symbols=True
        )
        
        print("Gathered context structure:")
        for key, value in context.items():
            if isinstance(value, dict):
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {type(value).__name__}")
        
        # Format for AI consumption
        formatted_context = gatherer.format_context_for_ai(context)
        print(f"\nFormatted context preview:\n{formatted_context[:300]}...")


def demo_provider_selection():
    """Demonstrate AI provider selection"""
    
    print("\n🔄 8. AI Provider Selection")
    
    codebase = Codebase(".")
    
    # Check available providers
    from graph_sitter.ai.ai_client_factory import AIClientFactory
    
    available_providers = AIClientFactory.get_available_providers(codebase.ctx.secrets)
    print(f"Available AI providers: {available_providers}")
    
    if not available_providers:
        print("No AI providers configured. Please set credentials:")
        print("- OpenAI: codebase.set_ai_key('your-api-key')")
        print("- Codegen SDK: codebase.set_codegen_credentials('org-id', 'token')")
        return
    
    # Try different providers
    for provider in available_providers:
        try:
            print(f"\nTesting {provider} provider...")
            result = codebase.ai_sync(
                "What programming languages are used in this codebase?",
                provider=provider
            )
            print(f"{provider} result: {result[:200]}...")
        except Exception as e:
            print(f"{provider} failed: {e}")


if __name__ == "__main__":
    print("Enhanced Codebase AI Demo")
    print("This demo showcases the new AI-powered features with rich context")
    print("Make sure to set your AI credentials before running!")
    print()
    
    # Run async demos
    asyncio.run(demo_enhanced_ai_features())
    
    # Run sync demos
    demo_synchronous_usage()
    demo_context_gathering()
    demo_provider_selection()
    
    print("\n✅ Demo completed!")
    print("\nNext steps:")
    print("1. Set your AI credentials (OpenAI or Codegen SDK)")
    print("2. Try the examples with your own codebase")
    print("3. Explore the rich context features for better AI responses")

