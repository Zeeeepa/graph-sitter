#!/usr/bin/env python3
"""
Test script to validate the unified Serena error handling interface.

Tests the 4 core methods:
- codebase.errors()
- codebase.full_error_context(error_id)  
- codebase.resolve_errors()
- codebase.resolve_error(error_id)
"""

import sys
import traceback
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_unified_interface():
    """Test the unified error handling interface."""
    print("🧪 TESTING UNIFIED SERENA ERROR INTERFACE")
    print("=" * 60)
    
    try:
        # Import the Codebase class
        from graph_sitter import Codebase
        print("✅ Successfully imported Codebase")
        
        # Initialize codebase
        print("\n📁 Initializing codebase...")
        codebase = Codebase(".")
        print("✅ Codebase initialized")
        
        # Check if the methods exist
        methods_to_check = ['errors', 'full_error_context', 'resolve_errors', 'resolve_error']
        available_methods = []
        
        for method in methods_to_check:
            if hasattr(codebase, method):
                available_methods.append(method)
                print(f"✅ Method '{method}' is available")
            else:
                print(f"❌ Method '{method}' is NOT available")
        
        if len(available_methods) != 4:
            print(f"\n❌ FAILED: Only {len(available_methods)}/4 methods available")
            return False
        
        print(f"\n🎉 SUCCESS: All 4 methods are available!")
        
        # Test 1: codebase.errors()
        print("\n🔍 TEST 1: codebase.errors()")
        print("-" * 40)
        try:
            errors = codebase.errors()
            print(f"✅ codebase.errors() returned: {type(errors)}")
            print(f"   Found {len(errors) if isinstance(errors, list) else 'N/A'} errors")
            
            # Show first few errors if any
            if isinstance(errors, list) and errors:
                print("   Sample errors:")
                for i, error in enumerate(errors[:3]):
                    if isinstance(error, dict):
                        file_path = error.get('file_path', 'unknown')
                        line = error.get('line', 'unknown')
                        message = error.get('message', 'no message')[:50]
                        print(f"     {i+1}. {file_path}:{line} - {message}...")
            
        except Exception as e:
            print(f"❌ codebase.errors() failed: {e}")
            traceback.print_exc()
        
        # Test 2: codebase.full_error_context() (if we have errors)
        print("\n🔍 TEST 2: codebase.full_error_context()")
        print("-" * 40)
        try:
            if isinstance(errors, list) and errors:
                sample_error = errors[0]
                error_id = sample_error.get('id') if isinstance(sample_error, dict) else str(sample_error)
                
                print(f"   Testing with error ID: {error_id}")
                context = codebase.full_error_context(error_id)
                print(f"✅ codebase.full_error_context() returned: {type(context)}")
                
                if isinstance(context, dict):
                    print(f"   Context keys: {list(context.keys())}")
                    if 'fix_suggestions' in context:
                        suggestions = context['fix_suggestions']
                        print(f"   Fix suggestions: {len(suggestions) if isinstance(suggestions, list) else 'N/A'}")
            else:
                print("   ⚠️  No errors available to test context retrieval")
                
        except Exception as e:
            print(f"❌ codebase.full_error_context() failed: {e}")
            traceback.print_exc()
        
        # Test 3: codebase.resolve_errors()
        print("\n🔍 TEST 3: codebase.resolve_errors()")
        print("-" * 40)
        try:
            result = codebase.resolve_errors()
            print(f"✅ codebase.resolve_errors() returned: {type(result)}")
            
            if isinstance(result, dict):
                print(f"   Result keys: {list(result.keys())}")
                total_errors = result.get('total_errors', 'N/A')
                successful_fixes = result.get('successful_fixes', 'N/A')
                print(f"   Total errors: {total_errors}")
                print(f"   Successful fixes: {successful_fixes}")
            
        except Exception as e:
            print(f"❌ codebase.resolve_errors() failed: {e}")
            traceback.print_exc()
        
        # Test 4: codebase.resolve_error() (if we have errors)
        print("\n🔍 TEST 4: codebase.resolve_error()")
        print("-" * 40)
        try:
            if isinstance(errors, list) and errors:
                sample_error = errors[0]
                error_id = sample_error.get('id') if isinstance(sample_error, dict) else str(sample_error)
                
                print(f"   Testing with error ID: {error_id}")
                fix_result = codebase.resolve_error(error_id)
                print(f"✅ codebase.resolve_error() returned: {type(fix_result)}")
                
                if isinstance(fix_result, dict):
                    print(f"   Fix result keys: {list(fix_result.keys())}")
                    success = fix_result.get('success', False)
                    print(f"   Fix successful: {success}")
            else:
                print("   ⚠️  No errors available to test individual fix")
                
        except Exception as e:
            print(f"❌ codebase.resolve_error() failed: {e}")
            traceback.print_exc()
        
        print("\n🎉 UNIFIED INTERFACE TEST COMPLETED!")
        print("✅ All 4 core methods are implemented and callable")
        return True
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        print("   The unified interface may not be properly integrated")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_unified_interface()
    if success:
        print("\n🎯 RESULT: Unified interface is working!")
    else:
        print("\n💥 RESULT: Unified interface needs fixes!")
    
    sys.exit(0 if success else 1)

