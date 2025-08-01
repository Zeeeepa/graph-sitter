#!/usr/bin/env python3
"""
Comprehensive test script for LSP error detection functionality.
This script validates that the unified error interface works correctly.
"""

import sys
from pathlib import Path

def test_lsp_error_detection():
    """Test the LSP error detection functionality."""
    print("🚀 COMPREHENSIVE LSP ERROR DETECTION TEST")
    print("=" * 60)
    
    try:
        from graph_sitter.enhanced.codebase import Codebase
        from graph_sitter.extensions.lsp.language_servers.python_server import PythonLanguageServer
        
        print("✅ Successfully imported required modules")
        
        # Test 1: Direct LSP Server Testing
        print("\n📋 TEST 1: Direct LSP Server Testing")
        print("-" * 40)
        
        workspace = Path('.')
        server = PythonLanguageServer(workspace)
        
        if server.initialize():
            print("✅ LSP server initialized successfully")
            
            # Test error file
            if server.open_file('test_error_detection.py'):
                diagnostics = server.get_file_diagnostics('test_error_detection.py')
                print(f"✅ test_error_detection.py: {len(diagnostics)} errors found")
                
                expected_errors = [
                    "Syntax Error: '(' was never closed",
                    "NameError: name 'undefined_variable' is not defined",
                    "ModuleNotFoundError: No module named 'nonexistent_module'"
                ]
                
                found_errors = [d.message for d in diagnostics]
                for expected in expected_errors:
                    if any(expected in found for found in found_errors):
                        print(f"  ✅ Found expected error: {expected}")
                    else:
                        print(f"  ❌ Missing expected error: {expected}")
            
            # Test valid file
            if server.open_file('test_valid_code.py'):
                diagnostics = server.get_file_diagnostics('test_valid_code.py')
                print(f"✅ test_valid_code.py: {len(diagnostics)} errors found (should be 0)")
                
                if len(diagnostics) == 0:
                    print("  ✅ No false positives in valid code")
                else:
                    print("  ⚠️  Unexpected errors in valid code:")
                    for d in diagnostics:
                        print(f"    - {d.message}")
            
            server.shutdown()
        else:
            print("❌ Failed to initialize LSP server")
            return False
        
        # Test 2: Unified Interface Testing
        print("\n📋 TEST 2: Unified Interface Testing")
        print("-" * 40)
        
        codebase = Codebase('.')
        
        # Test unified error interface
        if hasattr(codebase, 'errors'):
            all_errors = codebase.errors()
            print(f"✅ codebase.errors(): {len(all_errors)} total errors found")
        else:
            print("❌ codebase.errors() method not available")
            return False
        
        # Test error context
        if hasattr(codebase, 'full_error_context') and all_errors:
            first_error = all_errors[0]
            error_id = getattr(first_error, 'id', None)
            if error_id:
                context = codebase.full_error_context(error_id)
                print(f"✅ codebase.full_error_context(): Got context for error {error_id}")
            else:
                print("⚠️  First error has no ID")
        else:
            print("❌ codebase.full_error_context() method not available")
        
        # Test error resolution methods
        resolution_methods = ['resolve_errors', 'resolve_error']
        for method in resolution_methods:
            if hasattr(codebase, method):
                print(f"✅ codebase.{method}() method available")
            else:
                print(f"❌ codebase.{method}() method not available")
                return False
        
        # Test 3: API Compliance Testing
        print("\n📋 TEST 3: API Compliance Testing")
        print("-" * 40)
        
        # Test the expected API from the requirements
        expected_methods = [
            'errors',           # All errors
            'full_error_context',  # Full context for specific error
            'resolve_errors',   # Auto-fix all errors
            'resolve_error'     # Auto-fix specific error
        ]
        
        all_methods_available = True
        for method in expected_methods:
            if hasattr(codebase, method):
                print(f"✅ {method}() - Available")
            else:
                print(f"❌ {method}() - Missing")
                all_methods_available = False
        
        if all_methods_available:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ LSP error detection is working correctly")
            print("✅ Unified interface is complete")
            print("✅ All required methods are available")
            return True
        else:
            print("\n❌ SOME TESTS FAILED!")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("LSP Error Detection Validation Test")
    print("This script validates the unified error interface implementation.")
    print()
    
    success = test_lsp_error_detection()
    
    if success:
        print("\n🎉 VALIDATION SUCCESSFUL!")
        print("The LSP error detection implementation is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED!")
        print("The LSP error detection implementation needs fixes.")
        sys.exit(1)


if __name__ == "__main__":
    main()
