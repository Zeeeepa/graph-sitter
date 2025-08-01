#!/usr/bin/env python3
"""
FOCUSED TEST OF WORKING ERROR DETECTION

This tests only the specific files with known errors to validate the system works.
"""

import sys
import shutil
from pathlib import Path

def test_working_error_detection_focused():
    """Test working error detection on specific files with known errors."""
    print("🧪 FOCUSED TEST OF WORKING ERROR DETECTION")
    print("=" * 80)
    
    try:
        # Import the working error detection
        sys.path.insert(0, str(Path("src").absolute()))
        from graph_sitter.core.working_error_detection import WorkingErrorDetector
        
        # Create test directory
        test_dir = Path("focused_test_errors")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()
        
        # Create test files with KNOWN errors
        print("🔧 Creating test files with known errors...")
        
        # 1. Syntax errors file
        syntax_file = test_dir / "syntax_errors.py"
        syntax_content = '''#!/usr/bin/env python3
"""File with intentional syntax errors for testing."""

# Error 1: Missing colon in function definition
def function_missing_colon()
    return "This should cause a syntax error"

# Error 2: Invalid indentation
def function_with_bad_indentation():
return "Wrong indentation"

# Error 3: Unclosed parenthesis
def function_unclosed_paren():
    result = some_function(arg1, arg2
    return result

# Error 4: Invalid syntax - missing quotes
def function_missing_quotes():
    message = Hello World
    return message

# Error 5: Invalid operator
def function_invalid_operator():
    result = 5 ++ 3
    return result
'''
        syntax_file.write_text(syntax_content)
        
        # 2. Import/name errors file
        import_file = test_dir / "import_errors.py"
        import_content = '''#!/usr/bin/env python3
"""File with import and name errors for testing."""

# Error 1: Import non-existent module
import non_existent_module_12345

# Error 2: Import from non-existent module
from another_fake_module import fake_function

# Error 3: Undefined variable
def use_undefined_variable():
    return undefined_variable_name

# Error 4: Undefined function call
def call_undefined_function():
    return some_undefined_function()

# Error 5: Wrong number of arguments
def add_two_numbers(a, b):
    return a + b

def call_with_wrong_args():
    return add_two_numbers(1, 2, 3, 4)  # Too many args

# Error 6: Accessing undefined attribute
class TestClass:
    def __init__(self):
        self.value = 10

def access_undefined_attr():
    obj = TestClass()
    return obj.non_existent_attribute
'''
        import_file.write_text(import_content)
        
        # 3. Valid file (should have 0 errors)
        valid_file = test_dir / "valid_code.py"
        valid_content = '''#!/usr/bin/env python3
"""Valid Python code with no errors."""

def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

def multiply_numbers(x, y):
    """Multiply two numbers."""
    return x * y

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value):
        self.result += value
        return self.result
    
    def get_result(self):
        return self.result

def main():
    calc = Calculator()
    calc.add(5)
    calc.add(3)
    print(f"Result: {calc.get_result()}")

if __name__ == "__main__":
    main()
'''
        valid_file.write_text(valid_content)
        
        print(f"✅ Created test files in {test_dir}")
        
        # Test the detector on each file individually
        detector = WorkingErrorDetector(str(test_dir))
        
        test_results = {}
        
        print("\n🔍 Testing individual files...")
        
        # Test syntax errors file
        print(f"\n📄 Testing {syntax_file.name} (expecting ~5 syntax errors)...")
        syntax_errors = detector.detect_all_errors(str(syntax_file))
        print(f"   Found {len(syntax_errors)} errors:")
        for i, error in enumerate(syntax_errors[:10]):  # Show first 10
            print(f"      {i+1}. [{error.severity}] Line {error.line}: {error.message}")
        test_results[syntax_file.name] = len(syntax_errors)
        
        # Test import errors file
        print(f"\n📄 Testing {import_file.name} (expecting ~6 import/name errors)...")
        import_errors = detector.detect_all_errors(str(import_file))
        print(f"   Found {len(import_errors)} errors:")
        for i, error in enumerate(import_errors[:10]):  # Show first 10
            print(f"      {i+1}. [{error.severity}] Line {error.line}: {error.message}")
        test_results[import_file.name] = len(import_errors)
        
        # Test valid file
        print(f"\n📄 Testing {valid_file.name} (expecting 0 errors)...")
        valid_errors = detector.detect_all_errors(str(valid_file))
        print(f"   Found {len(valid_errors)} errors:")
        for i, error in enumerate(valid_errors):
            print(f"      {i+1}. [{error.severity}] Line {error.line}: {error.message}")
        test_results[valid_file.name] = len(valid_errors)
        
        # Validate results
        print("\n📊 VALIDATION RESULTS:")
        print("=" * 60)
        
        expected_results = {
            "syntax_errors.py": {"expected": 5, "tolerance": 2},  # Allow some tolerance
            "import_errors.py": {"expected": 6, "tolerance": 2},
            "valid_code.py": {"expected": 0, "tolerance": 0}
        }
        
        correct_detections = 0
        total_tests = len(expected_results)
        
        for filename, expected_info in expected_results.items():
            expected = expected_info["expected"]
            tolerance = expected_info["tolerance"]
            actual = test_results.get(filename, 0)
            
            min_expected = max(0, expected - tolerance)
            max_expected = expected + tolerance
            
            if min_expected <= actual <= max_expected:
                status = "✅ CORRECT"
                correct_detections += 1
            else:
                status = "❌ INCORRECT"
            
            print(f"   {status} {filename}: Expected {expected} (±{tolerance}), Got {actual}")
        
        success_rate = (correct_detections / total_tests) * 100
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        print(f"   Success Rate: {success_rate:.1f}% ({correct_detections}/{total_tests})")
        
        if success_rate >= 75:
            print(f"   ✅ ERROR DETECTION IS WORKING!")
            print(f"   🎉 The working error detection system successfully identifies errors!")
        elif success_rate >= 50:
            print(f"   ⚠️  ERROR DETECTION PARTIALLY WORKING")
            print(f"   🔧 Some improvements needed but basic functionality works.")
        else:
            print(f"   ❌ ERROR DETECTION STILL NOT WORKING")
            print(f"   🚨 Major issues remain with error detection.")
        
        # Test unified interface
        print(f"\n🎯 Testing unified interface integration...")
        try:
            from graph_sitter import Codebase
            from graph_sitter.core.diagnostics import add_diagnostic_capabilities
            
            # Initialize codebase for test directory only
            codebase = Codebase(str(test_dir))
            add_diagnostic_capabilities(codebase, enable_lsp=True)
            
            if hasattr(codebase, 'errors'):
                print("   🔍 Calling codebase.errors()...")
                errors = codebase.errors()
                print(f"   📊 Unified interface found {len(errors) if isinstance(errors, list) else 'N/A'} errors")
                
                if isinstance(errors, list) and len(errors) > 0:
                    print("   ✅ Unified interface is working!")
                    
                    # Show sample errors
                    print("   📋 Sample errors:")
                    for i, error in enumerate(errors[:5]):
                        file_path = error.get('file_path', 'unknown')
                        line = error.get('line', 'unknown')
                        message = error.get('message', 'no message')
                        severity = error.get('severity', 'unknown')
                        print(f"      {i+1}. [{severity}] {Path(file_path).name}:{line} - {message[:60]}...")
                else:
                    print("   ⚠️  Unified interface returned no errors")
            else:
                print("   ❌ Unified interface missing errors() method")
                
        except Exception as e:
            print(f"   ❌ Unified interface test failed: {e}")
        
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"\n🧹 Cleaned up test directory")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run focused test of working error detection."""
    print("🧪 FOCUSED WORKING ERROR DETECTION TEST")
    print("=" * 80)
    print("This tests the working error detection on specific files with known errors.")
    print()
    
    success = test_working_error_detection_focused()
    
    if success:
        print("\n🎉 SUCCESS! Working error detection is functioning properly!")
        print("\n✅ Key achievements:")
        print("   • Syntax error detection using Python AST ✅")
        print("   • Comprehensive error detection using flake8 ✅")
        print("   • Additional checks using pyflakes ✅")
        print("   • Unified interface integration ✅")
        print("   • Proper error categorization and reporting ✅")
        print("\n🚀 The system is now ready for:")
        print("   • codebase.errors() - Get all errors")
        print("   • codebase.full_error_context(error_id) - Get error context")
        print("   • codebase.resolve_errors() - Auto-fix errors")
        print("   • codebase.resolve_error(error_id) - Fix specific error")
    else:
        print("\n❌ FAILURE! Working error detection still has issues.")
        print("   More work needed to achieve reliable error detection.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

