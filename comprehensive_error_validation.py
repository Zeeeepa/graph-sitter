#!/usr/bin/env python3
"""
COMPREHENSIVE ERROR VALIDATION SUITE

This creates test files with KNOWN errors and validates that our error detection
system can find them. This is the ONLY way to properly test error detection.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

def create_test_files_with_known_errors():
    """Create test files with specific, known errors for validation."""
    
    # Create a temporary test directory
    test_dir = Path("test_error_validation")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    print(f"🔧 Creating test files with known errors in: {test_dir}")
    
    # Test file 1: Syntax errors
    syntax_errors_file = test_dir / "syntax_errors.py"
    syntax_errors_content = '''#!/usr/bin/env python3
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
    syntax_errors_file.write_text(syntax_errors_content)
    
    # Test file 2: Import and name errors
    import_errors_file = test_dir / "import_errors.py"
    import_errors_content = '''#!/usr/bin/env python3
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
    import_errors_file.write_text(import_errors_content)
    
    # Test file 3: Type errors
    type_errors_file = test_dir / "type_errors.py"
    type_errors_content = '''#!/usr/bin/env python3
"""File with type errors for testing."""

# Error 1: String + int
def string_plus_int():
    return "hello" + 5

# Error 2: Division by zero
def division_by_zero():
    return 10 / 0

# Error 3: Calling non-callable
def call_non_callable():
    x = 5
    return x()

# Error 4: Index error
def index_error():
    lst = [1, 2, 3]
    return lst[10]

# Error 5: Key error
def key_error():
    d = {"a": 1, "b": 2}
    return d["non_existent_key"]

# Error 6: Attribute error
def attribute_error():
    x = 5
    return x.non_existent_method()
'''
    type_errors_file.write_text(type_errors_content)
    
    # Test file 4: Valid Python (should have 0 errors)
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
    
    # Expected error counts for validation
    expected_errors = {
        "syntax_errors.py": {
            "expected_count": 5,
            "error_types": ["syntax_error", "indentation_error", "invalid_syntax"]
        },
        "import_errors.py": {
            "expected_count": 6,
            "error_types": ["import_error", "name_error", "undefined_variable"]
        },
        "type_errors.py": {
            "expected_count": 6,
            "error_types": ["type_error", "zero_division_error", "attribute_error"]
        },
        "valid_code.py": {
            "expected_count": 0,
            "error_types": []
        }
    }
    
    # Save expected results
    expected_file = test_dir / "expected_errors.json"
    with open(expected_file, 'w') as f:
        json.dump(expected_errors, f, indent=2)
    
    print(f"✅ Created test files:")
    print(f"   📄 {syntax_errors_file} - Expected: 5 syntax errors")
    print(f"   📄 {import_errors_file} - Expected: 6 import/name errors")  
    print(f"   📄 {type_errors_file} - Expected: 6 type errors")
    print(f"   📄 {valid_file} - Expected: 0 errors")
    print(f"   📋 {expected_file} - Expected results for validation")
    
    return test_dir, expected_errors


def test_python_syntax_validation():
    """Test Python's built-in syntax validation first."""
    print("\n🐍 TESTING PYTHON BUILT-IN SYNTAX VALIDATION")
    print("=" * 60)
    
    test_dir = Path("test_error_validation")
    results = {}
    
    for py_file in test_dir.glob("*.py"):
        if py_file.name == "valid_code.py":
            continue
            
        print(f"\n📄 Testing {py_file.name} with Python syntax check...")
        
        # Try to compile the file
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Try to compile - this will catch syntax errors
            try:
                compile(content, py_file.name, 'exec')
                print(f"   ✅ Python compilation: PASSED (no syntax errors)")
                results[py_file.name] = {"python_syntax_errors": 0}
            except SyntaxError as e:
                print(f"   ❌ Python compilation: FAILED - {e}")
                results[py_file.name] = {"python_syntax_errors": 1, "error": str(e)}
            
        except Exception as e:
            print(f"   ⚠️  Error reading file: {e}")
            results[py_file.name] = {"error": f"File read error: {e}"}
    
    return results


def test_graph_sitter_error_detection():
    """Test our graph-sitter error detection system."""
    print("\n🔍 TESTING GRAPH-SITTER ERROR DETECTION")
    print("=" * 60)
    
    try:
        from graph_sitter import Codebase
        from graph_sitter.core.diagnostics import add_diagnostic_capabilities
        
        # Initialize codebase pointing to our test directory
        test_dir = Path("test_error_validation")
        print(f"🔧 Initializing codebase for test directory: {test_dir}")
        
        codebase = Codebase(str(test_dir))
        add_diagnostic_capabilities(codebase, enable_lsp=True)
        
        print("✅ Codebase initialized with diagnostic capabilities")
        
        # Test each file individually
        results = {}
        
        for py_file in test_dir.glob("*.py"):
            if py_file.name == "expected_errors.json":
                continue
                
            print(f"\n📄 Testing error detection for: {py_file.name}")
            
            # Test direct file diagnostics
            try:
                file_path = str(py_file.relative_to(test_dir))
                diagnostics = codebase.get_file_diagnostics(file_path)
                
                if isinstance(diagnostics, dict) and diagnostics.get('success'):
                    diag_list = diagnostics.get('diagnostics', [])
                    error_count = len(diag_list)
                    print(f"   📊 Found {error_count} diagnostics")
                    
                    # Show diagnostic details
                    for i, diag in enumerate(diag_list[:5]):  # Show first 5
                        severity = diag.get('severity', 'unknown')
                        message = diag.get('message', 'no message')
                        line = diag.get('range', {}).get('start', {}).get('line', 'unknown')
                        print(f"      {i+1}. [{severity}] Line {line}: {message}")
                    
                    results[py_file.name] = {
                        "diagnostics_count": error_count,
                        "diagnostics": diag_list[:10]  # Store first 10 for analysis
                    }
                    
                elif isinstance(diagnostics, list):
                    error_count = len(diagnostics)
                    print(f"   📊 Found {error_count} diagnostics (list format)")
                    results[py_file.name] = {
                        "diagnostics_count": error_count,
                        "diagnostics": diagnostics[:10]
                    }
                else:
                    print(f"   ⚠️  Unexpected diagnostics format: {type(diagnostics)}")
                    results[py_file.name] = {
                        "diagnostics_count": 0,
                        "error": f"Unexpected format: {type(diagnostics)}"
                    }
                    
            except Exception as e:
                print(f"   ❌ Error getting diagnostics: {e}")
                results[py_file.name] = {
                    "diagnostics_count": 0,
                    "error": str(e)
                }
        
        # Test unified interface
        print(f"\n🎯 Testing unified interface methods...")
        
        try:
            all_errors = codebase.errors()
            if isinstance(all_errors, list):
                print(f"   📊 codebase.errors() returned {len(all_errors)} errors")
                results["unified_interface"] = {
                    "errors_count": len(all_errors),
                    "errors_sample": all_errors[:5] if all_errors else []
                }
            else:
                print(f"   ⚠️  codebase.errors() returned unexpected type: {type(all_errors)}")
                results["unified_interface"] = {
                    "errors_count": 0,
                    "error": f"Unexpected type: {type(all_errors)}"
                }
        except Exception as e:
            print(f"   ❌ Error with unified interface: {e}")
            results["unified_interface"] = {
                "errors_count": 0,
                "error": str(e)
            }
        
        return results
        
    except ImportError as e:
        print(f"❌ Failed to import graph-sitter components: {e}")
        return {"import_error": str(e)}
    except Exception as e:
        print(f"❌ Error in graph-sitter testing: {e}")
        return {"error": str(e)}


def validate_results(graph_sitter_results, expected_errors):
    """Validate that our error detection found the expected errors."""
    print("\n📊 VALIDATING ERROR DETECTION RESULTS")
    print("=" * 60)
    
    validation_results = {
        "total_files_tested": 0,
        "files_with_correct_detection": 0,
        "files_with_incorrect_detection": 0,
        "detailed_results": {}
    }
    
    for filename, expected in expected_errors.items():
        validation_results["total_files_tested"] += 1
        expected_count = expected["expected_count"]
        
        print(f"\n📄 Validating {filename}:")
        print(f"   🎯 Expected errors: {expected_count}")
        
        if filename in graph_sitter_results:
            actual_count = graph_sitter_results[filename].get("diagnostics_count", 0)
            print(f"   📊 Detected errors: {actual_count}")
            
            if actual_count == expected_count:
                print(f"   ✅ CORRECT: Detection matches expectation")
                validation_results["files_with_correct_detection"] += 1
                validation_results["detailed_results"][filename] = {
                    "status": "correct",
                    "expected": expected_count,
                    "actual": actual_count
                }
            else:
                print(f"   ❌ INCORRECT: Expected {expected_count}, got {actual_count}")
                validation_results["files_with_incorrect_detection"] += 1
                validation_results["detailed_results"][filename] = {
                    "status": "incorrect",
                    "expected": expected_count,
                    "actual": actual_count,
                    "difference": actual_count - expected_count
                }
        else:
            print(f"   ❌ MISSING: No results found for this file")
            validation_results["files_with_incorrect_detection"] += 1
            validation_results["detailed_results"][filename] = {
                "status": "missing",
                "expected": expected_count,
                "actual": 0
            }
    
    # Calculate success rate
    total_files = validation_results["total_files_tested"]
    correct_files = validation_results["files_with_correct_detection"]
    success_rate = (correct_files / total_files * 100) if total_files > 0 else 0
    
    print(f"\n📈 VALIDATION SUMMARY:")
    print(f"   📊 Total files tested: {total_files}")
    print(f"   ✅ Correct detections: {correct_files}")
    print(f"   ❌ Incorrect detections: {validation_results['files_with_incorrect_detection']}")
    print(f"   📊 Success rate: {success_rate:.1f}%")
    
    validation_results["success_rate"] = success_rate
    
    return validation_results


def main():
    """Run comprehensive error validation suite."""
    print("🧪 COMPREHENSIVE ERROR VALIDATION SUITE")
    print("=" * 80)
    print("This test creates files with KNOWN errors and validates detection.")
    print()
    
    # Step 1: Create test files with known errors
    test_dir, expected_errors = create_test_files_with_known_errors()
    
    # Step 2: Test Python's built-in syntax validation
    python_results = test_python_syntax_validation()
    
    # Step 3: Test our graph-sitter error detection
    graph_sitter_results = test_graph_sitter_error_detection()
    
    # Step 4: Validate results against expectations
    validation_results = validate_results(graph_sitter_results, expected_errors)
    
    # Step 5: Generate comprehensive report
    print("\n📋 GENERATING COMPREHENSIVE REPORT")
    print("=" * 60)
    
    report = {
        "test_summary": {
            "test_directory": str(test_dir),
            "total_test_files": len(expected_errors),
            "expected_total_errors": sum(e["expected_count"] for e in expected_errors.values())
        },
        "expected_errors": expected_errors,
        "python_syntax_results": python_results,
        "graph_sitter_results": graph_sitter_results,
        "validation_results": validation_results
    }
    
    # Save report
    report_file = Path("comprehensive_error_validation_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 Comprehensive report saved: {report_file}")
    
    # Final assessment
    success_rate = validation_results.get("success_rate", 0)
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    if success_rate >= 75:
        print(f"   ✅ ERROR DETECTION IS WORKING (Success rate: {success_rate:.1f}%)")
        print(f"   🎉 The error detection system is properly identifying known errors!")
    elif success_rate >= 50:
        print(f"   ⚠️  ERROR DETECTION PARTIALLY WORKING (Success rate: {success_rate:.1f}%)")
        print(f"   🔧 Some improvements needed in error detection accuracy.")
    else:
        print(f"   ❌ ERROR DETECTION IS NOT WORKING (Success rate: {success_rate:.1f}%)")
        print(f"   🚨 Major issues with error detection - needs immediate attention!")
    
    print(f"\n📊 DETAILED BREAKDOWN:")
    for filename, result in validation_results["detailed_results"].items():
        status_emoji = "✅" if result["status"] == "correct" else "❌"
        print(f"   {status_emoji} {filename}: Expected {result['expected']}, Got {result.get('actual', 0)}")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test directory: {test_dir}")
    try:
        shutil.rmtree(test_dir)
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    return success_rate >= 75


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

