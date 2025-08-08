#!/usr/bin/env python3
"""
Test the focused error analysis implementation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Test the focused error analysis."""
    print("🔍 Testing Focused Error Analysis")
    print("=" * 50)
    
    try:
        # Test direct import
        from graph_sitter.extensions.lsp.error_analysis import (
            ComprehensiveErrorAnalyzer,
            get_repo_error_analysis
        )
        print("✅ Direct imports successful")
        
        # Test via __init__
        from graph_sitter.extensions.lsp import (
            ComprehensiveErrorAnalyzer as CEA,
            get_repo_error_analysis as GREA
        )
        print("✅ Package imports successful")
        
        # Test Codebase integration
        from graph_sitter.core.codebase import Codebase
        
        # Create a small test directory
        test_dir = Path("test_focused_repo")
        test_dir.mkdir(exist_ok=True)
        
        # Create a simple Python file with errors
        test_file = test_dir / "test.py"
        test_file.write_text("""
# Test file with intentional issues
def test_function(unused_param):
    # Undefined variable
    result = undefined_var + 5
    return result

unused_variable = "not used"

def complex_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        if True:
                            return "too complex"
""")
        
        print(f"✅ Created test repository: {test_dir}")
        
        # Test codebase creation and FullErrors property
        codebase = Codebase(str(test_dir))
        print("✅ Codebase created")
        
        # Test FullErrors property
        full_errors = codebase.FullErrors
        print(f"✅ FullErrors property: {type(full_errors)}")
        
        # Test comprehensive error analysis
        errors = full_errors.get_comprehensive_errors(max_errors=10)
        print(f"✅ Comprehensive errors: {errors.get('total_count', 0)} total")
        print(f"   - Critical/Errors: {errors.get('critical_count', 0) + errors.get('error_count', 0)}")
        print(f"   - Warnings: {errors.get('warning_count', 0)}")
        print(f"   - Files analyzed: {errors.get('files_analyzed', 0)}")
        
        # Show sample errors
        all_errors = []
        errors_by_severity = errors.get('errors_by_severity', {})
        for severity_errors in errors_by_severity.values():
            all_errors.extend(severity_errors)
        
        if all_errors:
            print("\n📋 Sample Errors:")
            for i, error in enumerate(all_errors[:3]):
                file_name = error['file_path'].split('/')[-1]
                print(f"   {i+1}. [{error['severity'].upper()}] {file_name}:{error['line']}:{error['column']} - {error['message']}")
                print(f"      Category: {error['category']}")
                if error.get('suggestions'):
                    print(f"      Suggestion: {error['suggestions'][0]}")
        
        # Test error summary
        summary = full_errors.get_error_summary()
        print(f"\n📊 Error Summary:")
        print(f"   - Total errors: {summary.get('total_errors', 0)}")
        print(f"   - By category: {summary.get('errors_by_category', {})}")
        
        # Test convenience function
        direct_analysis = get_repo_error_analysis(str(test_dir), max_errors=5)
        print(f"✅ Direct analysis: {direct_analysis.get('total_count', 0)} errors")
        
        print("\n" + "=" * 50)
        print("🎉 Focused Error Analysis Test Complete!")
        print("\nUsage:")
        print("```python")
        print("from graph_sitter.core.codebase import Codebase")
        print("codebase = Codebase('path/to/repo')")
        print("errors = codebase.FullErrors.get_comprehensive_errors()")
        print("print(f'Found {errors[\"total_count\"]} errors')")
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
