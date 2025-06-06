#!/usr/bin/env python3
"""
Test script to demonstrate enhanced issue logging capabilities.
"""

import os
import sys

# Add the src directory to the path
sys.path.insert(0, 'src')

def test_function_with_issues(param1, param2, param3, param4, param5, param6, param7, param8):
    """Function with too many parameters and other issues."""
    # String concatenation in loop (performance issue)
    result = ""
    for i in range(100):
        result += str(i)
    
    # Use of eval (security issue)
    eval("print('hello')")
    
    # Deep nesting (maintainability issue)
    if param1:
        if param2:
            if param3:
                if param4:
                    if param5:
                        print("Too deep!")
    
    return result

class TestClass:
    """Class without proper docstring."""
    
    def method_without_docstring(self, badParamName):
        pass
    
    def method_with_mutable_default(self, items=[]):
        items.append("bad")
        return items

def function_without_type_hints(name, age, active):
    return f"{name} is {age} years old"

# Missing docstring function
def undocumented_function():
    pass

if __name__ == "__main__":
    print("🧪 Testing enhanced issue detection...")
    
    # Import and run the analyzer
    try:
        from graph_sitter.adapters.analyze_codebase import ComprehensiveCodebaseAnalyzer
        
        analyzer = ComprehensiveCodebaseAnalyzer(use_graph_sitter=False)  # Use AST fallback for testing
        
        # Analyze this test file
        result = analyzer.analyze_codebase(".", extensions=[".py"])
        
        print(f"\n📊 Analysis Results:")
        print(f"   Files analyzed: {result.total_files}")
        print(f"   Functions found: {result.total_functions}")
        print(f"   Issues found: {len(result.issues)}")
        
        if hasattr(result, 'detailed_issues'):
            print(f"   Detailed issues: {len(result.detailed_issues)}")
            
            # Show some example issues
            for issue in result.detailed_issues[:5]:  # Show first 5 issues
                print(f"\n🔸 {issue.message}")
                print(f"   📁 {issue.file_path}:{issue.line_start}")
                print(f"   🏷️ {issue.type} ({issue.severity})")
                if issue.suggestion:
                    print(f"   💡 {issue.suggestion}")
        
        print(f"\n✅ Enhanced issue detection test completed!")
        
    except ImportError as e:
        print(f"❌ Could not import analyzer: {e}")
        print("Make sure you're running from the project root directory.")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

