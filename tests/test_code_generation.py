#!/usr/bin/env python3
"""
Test Code Generation Implementation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena.core import SerenaCore, SerenaCapability
from graph_sitter.extensions.serena.types import SerenaConfig

def test_code_generation():
    """Test that code generation works."""
    
    print("🧪 Testing Code Generation...")
    
    try:
        # Initialize codebase
        print("   📁 Loading codebase...")
        codebase = Codebase(".")
        print(f"   ✅ Loaded {len(codebase.files)} files with {len(codebase.symbols)} symbols")
        
        # Initialize Serena with intelligence capability
        print("   ⚙️ Initializing Serena...")
        config = SerenaConfig(enabled_capabilities=[SerenaCapability.INTELLIGENCE])
        serena = SerenaCore(codebase, config)
        print("   ✅ Serena initialized")
        
        # Test code generation with different prompts
        test_prompts = [
            "Create a function to validate email addresses",
            "Generate a class for user management",
            "Write code to process data"
        ]
        
        for prompt in test_prompts:
            print(f"   🔧 Generating code for: '{prompt}'...")
            result = serena.generate_code(prompt)
            
            if result and result.success:
                metadata = result.metadata or {}
                confidence = metadata.get('confidence_score', 0.0)
                print(f"      ✅ Generated code (confidence: {confidence:.2f}):")
                # Show first few lines of generated code
                code_lines = result.generated_code.split('\n')[:3]
                for line in code_lines:
                    print(f"         {line}")
                
                suggestions = metadata.get('suggestions', [])
                print(f"      📝 Suggestions: {len(suggestions)}")
                for suggestion in suggestions[:2]:
                    print(f"         - {suggestion}")
                
                imports_needed = metadata.get('imports_needed', [])
                print(f"      📦 Imports needed: {len(imports_needed)}")
                for imp in imports_needed:
                    print(f"         - {imp}")
                
                # Validate result structure
                assert isinstance(result.success, bool)
                assert isinstance(result.generated_code, str)
                assert isinstance(result.message, (str, type(None)))
                assert isinstance(result.metadata, (dict, type(None)))
                
                print(f"      ✅ Code generation result structure is valid")
                break
        else:
            print("   ❌ No code generation results")
            return False
        
        # Test with context
        print("   🔧 Testing code generation with context...")
        context = {"file_path": "test.py", "language": "python"}
        result_with_context = serena.generate_code("Create a helper function", context=context)
        
        if result_with_context and result_with_context.success:
            metadata = result_with_context.metadata or {}
            confidence = metadata.get('confidence_score', 0.0)
            context_used = metadata.get('context_used', {})
            print(f"      ✅ Generated code with context (confidence: {confidence:.2f})")
            print(f"      📋 Context used: {context_used}")
        
        print("🎉 All code generation tests passed!")
        return True
            
    except Exception as e:
        print(f"   ❌ Error during code generation test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            if 'serena' in locals():
                serena.shutdown()
        except:
            pass

if __name__ == "__main__":
    success = test_code_generation()
    sys.exit(0 if success else 1)
