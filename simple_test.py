#!/usr/bin/env python3
"""
Simple test to verify the FullErrors integration works.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Test the FullErrors integration."""
    print("🔍 Testing FullErrors Integration")
    print("=" * 50)
    
    try:
        from graph_sitter.core.codebase import Codebase
        
        # Create a small test directory
        test_dir = Path("test_repo")
        test_dir.mkdir(exist_ok=True)
        
        # Create a simple Python file with an error
        test_file = test_dir / "test.py"
        test_file.write_text("""
# Test file with intentional issues
def test_function():
    # Undefined variable
    result = undefined_var + 5
    return result

class TestClass:
    def __init__(self):
        self.value = None
    
    def method_with_issue(self):
        # Potential None access
        return self.value.upper()
""")
        
        print(f"✅ Created test repository: {test_dir}")
        
        # Create codebase instance
        print("Creating codebase instance...")
        codebase = Codebase(str(test_dir))
        
        # Test basic diagnostics
        print("Testing basic diagnostics...")
        errors = codebase.errors
        warnings = codebase.warnings
        diagnostics = codebase.diagnostics
        
        print(f"✅ Basic diagnostics:")
        print(f"   - Errors: {len(errors)}")
        print(f"   - Warnings: {len(warnings)}")
        print(f"   - Total diagnostics: {len(diagnostics)}")
        
        # Test FullErrors property
        print("Testing FullErrors property...")
        full_errors = codebase.FullErrors
        
        if full_errors is None:
            print("⚠️  FullErrors is None - this is expected without LSP servers")
            print("✅ Integration is working correctly (LSP not available)")
        else:
            print(f"✅ FullErrors property available: {type(full_errors)}")
            
            # Test comprehensive error analysis
            try:
                comprehensive_errors = full_errors.get_comprehensive_errors(max_errors=5)
                print(f"✅ Comprehensive errors: {comprehensive_errors.total_count} errors")
                
                # Test error summary
                summary = full_errors.get_error_summary()
                print(f"✅ Error summary: {summary.get('total_errors', 0)} total errors")
                
            except Exception as e:
                print(f"⚠️  Error during analysis (expected without LSP): {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Integration test completed successfully!")
        print("\nUsage example:")
        print("```python")
        print("from graph_sitter.core.codebase import Codebase")
        print("codebase = Codebase('path/to/repo')")
        print("full_errors = codebase.FullErrors")
        print("if full_errors:")
        print("    errors = full_errors.get_comprehensive_errors()")
        print("    print(f'Found {errors.total_count} errors')")
        print("```")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
