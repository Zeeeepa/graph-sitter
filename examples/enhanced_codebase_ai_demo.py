#!/usr/bin/env python3
"""
Enhanced Codebase AI Demo

This example demonstrates the new enhanced codebase AI functionality with:
- Dual AI backend support (Codegen SDK + OpenAI)
- Rich context awareness
- Async/sync methods
- Structured responses with metadata
"""

import asyncio
from graph_sitter import Codebase


async def main():
    """Demonstrate the enhanced codebase AI functionality."""
    
    # Initialize codebase
    codebase = Codebase(".")
    
    print("🚀 Enhanced Codebase AI Demo")
    print("=" * 50)
    
    # Example 1: Set credentials (choose one)
    print("\n1. Setting AI Credentials")
    print("-" * 30)
    
    # Option A: Use Codegen SDK (preferred)
    # codebase.set_codegen_credentials("your-org-id", "your-token")
    
    # Option B: Use OpenAI API
    # codebase.set_ai_key("your-openai-api-key")
    
    print("✅ Credentials configured (uncomment above to use)")
    
    # Example 2: Simple AI query
    print("\n2. Simple AI Query")
    print("-" * 30)
    
    try:
        # This would work with actual credentials
        # result = await codebase.ai("What does this codebase do?")
        # print(f"Response: {result}")
        # print(f"Provider: {result.provider}")
        # print(f"Response time: {result.response_time:.2f}s")
        print("✅ Simple query example (requires credentials)")
    except Exception as e:
        print(f"⚠️  Skipped (no credentials): {e}")
    
    # Example 3: Context-aware analysis
    print("\n3. Context-Aware Analysis")
    print("-" * 30)
    
    # Find a function to analyze
    if codebase.functions:
        function = codebase.functions[0]
        print(f"Found function: {function.name}")
        
        try:
            # This would work with actual credentials
            # analysis = await codebase.ai(
            #     "Analyze this function for potential improvements",
            #     target=function  # Automatically includes call sites, dependencies, etc.
            # )
            # print(f"Analysis: {analysis}")
            print("✅ Context-aware analysis example (requires credentials)")
        except Exception as e:
            print(f"⚠️  Skipped (no credentials): {e}")
    else:
        print("⚠️  No functions found in codebase")
    
    # Example 4: Code generation with context
    print("\n4. Code Generation with Context")
    print("-" * 30)
    
    try:
        # This would work with actual credentials
        # new_code = await codebase.ai(
        #     "Create a helper function to validate input data",
        #     context={
        #         "style": "defensive programming",
        #         "return_type": "bool",
        #         "include_docstring": True
        #     }
        # )
        # print(f"Generated code: {new_code}")
        print("✅ Code generation example (requires credentials)")
    except Exception as e:
        print(f"⚠️  Skipped (no credentials): {e}")
    
    # Example 5: Documentation generation
    print("\n5. Documentation Generation")
    print("-" * 30)
    
    if codebase.classes:
        class_def = codebase.classes[0]
        print(f"Found class: {class_def.name}")
        
        if hasattr(class_def, 'methods') and class_def.methods:
            method = class_def.methods[0]
            print(f"Found method: {method.name}")
            
            try:
                # This would work with actual credentials
                # docstring = await codebase.ai(
                #     "Generate a docstring describing this method",
                #     target=method,
                #     context={"style": "Google docstring format"}
                # )
                # print(f"Generated docstring: {docstring}")
                print("✅ Documentation generation example (requires credentials)")
            except Exception as e:
                print(f"⚠️  Skipped (no credentials): {e}")
        else:
            print("⚠️  No methods found in class")
    else:
        print("⚠️  No classes found in codebase")
    
    # Example 6: Sync method usage
    print("\n6. Sync Method Usage")
    print("-" * 30)
    
    try:
        # For non-async contexts, use ai_sync
        # result = codebase.ai_sync("What are the main components of this codebase?")
        # print(f"Sync result: {result}")
        print("✅ Sync method example (requires credentials)")
    except Exception as e:
        print(f"⚠️  Skipped (no credentials): {e}")
    
    # Example 7: Codebase statistics
    print("\n7. Codebase Statistics")
    print("-" * 30)
    
    print(f"📊 Total files: {len(codebase.files)}")
    print(f"📊 Total classes: {len(codebase.classes)}")
    print(f"📊 Total functions: {len(codebase.functions)}")
    
    # Show some file types
    file_extensions = set()
    for file in codebase.files[:20]:  # Sample first 20 files
        if '.' in file.filepath:
            ext = file.filepath.split('.')[-1]
            file_extensions.add(ext)
    
    print(f"📊 File types: {', '.join(sorted(file_extensions))}")
    
    print("\n🎉 Demo completed!")
    print("\nTo use the enhanced AI features:")
    print("1. Set your credentials using set_codegen_credentials() or set_ai_key()")
    print("2. Use await codebase.ai() for async contexts")
    print("3. Use codebase.ai_sync() for sync contexts")
    print("4. Enjoy rich context awareness and structured responses!")


def sync_demo():
    """Demonstrate sync usage."""
    codebase = Codebase(".")
    
    print("\n🔄 Sync Demo")
    print("-" * 20)
    
    # Example of sync usage
    try:
        # result = codebase.ai_sync("Analyze this codebase structure")
        # print(f"Sync result: {result}")
        print("✅ Sync demo (requires credentials)")
    except Exception as e:
        print(f"⚠️  Skipped (no credentials): {e}")


if __name__ == "__main__":
    # Run async demo
    asyncio.run(main())
    
    # Run sync demo
    sync_demo()

