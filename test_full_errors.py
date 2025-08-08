#!/usr/bin/env python3
"""
Test script to verify the FullErrors integration works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_full_errors_integration():
    """Test the FullErrors integration with Codebase."""
    try:
        from graph_sitter.core.codebase import Codebase
        
        # Create a codebase instance
        print("Creating codebase instance...")
        codebase = Codebase(".")
        
        # Test FullErrors property
        print("Testing FullErrors property...")
        full_errors = codebase.FullErrors
        
        if full_errors is None:
            print("⚠️  FullErrors is None - Serena dependencies may not be available")
            return False
        
        print(f"✅ FullErrors property available: {type(full_errors)}")
        
        # Test getting comprehensive errors
        print("Testing comprehensive error analysis...")
        try:
            comprehensive_errors = full_errors.get_comprehensive_errors(max_errors=10)
            print(f"✅ Comprehensive errors retrieved: {comprehensive_errors.total_count} errors")
            
            # Test error summary
            summary = full_errors.get_error_summary()
            print(f"✅ Error summary generated: {summary.get('total_errors', 0)} total errors")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error during comprehensive analysis: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_diagnostics():
    """Test basic diagnostics functionality."""
    try:
        from graph_sitter.core.codebase import Codebase
        
        print("Testing basic diagnostics...")
        codebase = Codebase(".")
        
        # Test basic properties
        errors = codebase.errors
        warnings = codebase.warnings
        diagnostics = codebase.diagnostics
        
        print(f"✅ Basic diagnostics available:")
        print(f"   - Errors: {len(errors)}")
        print(f"   - Warnings: {len(warnings)}")
        print(f"   - Total diagnostics: {len(diagnostics)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during basic diagnostics test: {e}")
        return False

def main():
    """Run all tests."""
    print("🔍 Testing Graph-Sitter FullErrors Integration")
    print("=" * 60)
    
    # Test basic diagnostics first
    basic_success = test_basic_diagnostics()
    print()
    
    # Test full errors integration
    full_errors_success = test_full_errors_integration()
    print()
    
    # Summary
    print("=" * 60)
    if basic_success and full_errors_success:
        print("🎉 All tests passed! FullErrors integration is working correctly.")
        print()
        print("Usage example:")
        print("```python")
        print("from graph_sitter.core.codebase import Codebase")
        print("codebase = Codebase('path/to/repo')")
        print("full_errors = codebase.FullErrors")
        print("comprehensive_errors = full_errors.get_comprehensive_errors()")
        print("print(f'Found {comprehensive_errors.total_count} errors')")
        print("```")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
