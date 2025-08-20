#!/usr/bin/env python3
"""
Test script for project_analysis_full_scope.py

This script runs the codebase analyzer on various edge cases and validates the results.
"""

import os
import sys
import json
import tempfile
import subprocess
import shutil
from pathlib import Path

# Add parent directory to path so we can import the analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the analyzer
try:
    from project_analysis_full_scope import ComprehensiveCodebaseAnalyzer
except ImportError:
    print("Error: Could not import ComprehensiveCodebaseAnalyzer. Make sure project_analysis_full_scope.py is in the parent directory.")
    sys.exit(1)

# Test case directory
TEST_DIR = Path(__file__).parent

def create_test_repo(name, files):
    """Create a test repository with the given files."""
    repo_dir = TEST_DIR / name
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True)
    
    for file_path, content in files.items():
        file_path = repo_dir / file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
    
    return repo_dir

def run_analyzer(repo_dir, output_file=None):
    """Run the analyzer on the given repository."""
    analyzer = ComprehensiveCodebaseAnalyzer(str(repo_dir))
    results = analyzer.run_comprehensive_analysis()
    report = analyzer.generate_report(results)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
    
    return results, report

def validate_results(results, expected):
    """Validate the analysis results against expected values."""
    validation = {
        "passed": True,
        "failures": []
    }
    
    # Check summary stats
    summary = results.summary_stats
    for key, expected_value in expected.get('summary', {}).items():
        if key in summary:
            actual_value = summary[key]
            if actual_value != expected_value:
                validation["passed"] = False
                validation["failures"].append({
                    "type": "summary",
                    "key": key,
                    "expected": expected_value,
                    "actual": actual_value
                })
    
    # Check entrypoints
    if 'entrypoints' in expected:
        expected_count = expected['entrypoints']
        actual_count = len(results.entrypoints)
        if actual_count != expected_count:
            validation["passed"] = False
            validation["failures"].append({
                "type": "entrypoints",
                "expected": expected_count,
                "actual": actual_count
            })
    
    # Check dead code
    if 'dead_code' in expected:
        expected_count = expected['dead_code']
        actual_count = len(results.dead_code)
        if actual_count != expected_count:
            validation["passed"] = False
            validation["failures"].append({
                "type": "dead_code",
                "expected": expected_count,
                "actual": actual_count
            })
    
    # Check issues
    if 'issues' in expected:
        expected_count = expected['issues']
        actual_count = len(results.issues)
        if actual_count != expected_count:
            validation["passed"] = False
            validation["failures"].append({
                "type": "issues",
                "expected": expected_count,
                "actual": actual_count
            })
    
    # Check import cycles
    if 'import_cycles' in expected:
        expected_count = expected['import_cycles']
        actual_count = summary.get('import_cycles', 0)
        if actual_count != expected_count:
            validation["passed"] = False
            validation["failures"].append({
                "type": "import_cycles",
                "expected": expected_count,
                "actual": actual_count
            })
    
    return validation

def run_test_case(name, files, expected):
    """Run a test case and validate the results."""
    print(f"Running test case: {name}")
    repo_dir = create_test_repo(name, files)
    results, report = run_analyzer(repo_dir)
    validation = validate_results(results, expected)
    
    if validation["passed"]:
        print(f"✅ Test case {name} passed!")
    else:
        print(f"❌ Test case {name} failed!")
        for failure in validation["failures"]:
            print(f"  - {failure['type']}: expected {failure['expected']}, got {failure['actual']}")
    
    return validation["passed"]

def test_empty_repo():
    """Test case for an empty repository."""
    return run_test_case(
        "empty_repo",
        {},
        {
            "summary": {
                "total_files": 0,
                "total_functions": 0,
                "total_classes": 0,
                "total_issues": 0,
                "dead_code_items": 0,
                "entry_points": 0,
                "import_cycles": 0
            },
            "entrypoints": 0,
            "dead_code": 0,
            "issues": 0,
            "import_cycles": 0
        }
    )

def test_single_file():
    """Test case for a repository with a single file."""
    return run_test_case(
        "single_file",
        {
            "main.py": """
def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()
"""
        },
        {
            "summary": {
                "total_files": 1,
                "total_functions": 1,
                "total_classes": 0,
                "total_issues": 0,
                "dead_code_items": 0,
                "entry_points": 1,
                "import_cycles": 0
            },
            "entrypoints": 1,
            "dead_code": 0,
            "issues": 0,
            "import_cycles": 0
        }
    )

def test_circular_imports():
    """Test case for a repository with circular imports."""
    return run_test_case(
        "circular_imports",
        {
            "module_a.py": """
from module_b import function_b

def function_a():
    return function_b()
""",
            "module_b.py": """
from module_a import function_a

def function_b():
    return function_a()
"""
        },
        {
            "summary": {
                "total_files": 2,
                "total_functions": 2,
                "total_classes": 0,
                "import_cycles": 1
            },
            "issues": 2,  # Two files in import cycle
            "import_cycles": 1
        }
    )

def test_dead_code():
    """Test case for a repository with dead code."""
    return run_test_case(
        "dead_code",
        {
            "main.py": """
def main():
    print("Hello, world!")

def unused_function():
    print("This function is never called")

if __name__ == "__main__":
    main()
"""
        },
        {
            "summary": {
                "total_files": 1,
                "total_functions": 2,
                "total_classes": 0,
                "dead_code_items": 1
            },
            "entrypoints": 1,
            "dead_code": 1,  # unused_function
            "issues": 0
        }
    )

def test_complex_inheritance():
    """Test case for a repository with complex inheritance."""
    return run_test_case(
        "complex_inheritance",
        {
            "inheritance.py": """
class BaseClass:
    def base_method(self):
        pass

class ChildClass(BaseClass):
    def child_method(self):
        pass

class GrandchildClass(ChildClass):
    def grandchild_method(self):
        pass

class MultipleInheritance(BaseClass, GrandchildClass):
    def multiple_method(self):
        pass
"""
        },
        {
            "summary": {
                "total_files": 1,
                "total_functions": 4,
                "total_classes": 4
            },
            "entrypoints": 4  # All classes should be detected as entry points
        }
    )

def test_syntax_error():
    """Test case for a repository with syntax errors."""
    return run_test_case(
        "syntax_error",
        {
            "error.py": """
def function_with_error(
    print("This has a syntax error")
"""
        },
        {
            "summary": {
                "total_files": 1,
                "total_functions": 0,  # No functions should be detected due to syntax error
                "total_classes": 0
            },
            "entrypoints": 0,
            "dead_code": 0,
            "issues": 0  # Syntax errors are not currently detected as issues
        }
    )

def test_large_file():
    """Test case for a repository with a large file."""
    # Generate a large file with many functions
    large_file_content = "# Large file with many functions\n\n"
    for i in range(100):
        large_file_content += f"""
def function_{i}():
    print("Function {i}")
"""
    
    return run_test_case(
        "large_file",
        {
            "large.py": large_file_content
        },
        {
            "summary": {
                "total_files": 1,
                "total_functions": 100,
                "total_classes": 0
            },
            "entrypoints": 0,
            "dead_code": 100,  # All functions should be detected as dead code
            "issues": 0
        }
    )

def test_mixed_languages():
    """Test case for a repository with mixed languages."""
    return run_test_case(
        "mixed_languages",
        {
            "main.py": """
def main():
    print("Hello from Python!")

if __name__ == "__main__":
    main()
""",
            "script.js": """
function hello() {
    console.log("Hello from JavaScript!");
}

hello();
""",
            "style.css": """
body {
    font-family: sans-serif;
    margin: 0;
    padding: 0;
}
"""
        },
        {
            "summary": {
                "total_files": 1,  # Only Python files should be analyzed
                "total_functions": 1,
                "total_classes": 0
            },
            "entrypoints": 1,
            "dead_code": 0,
            "issues": 0
        }
    )

def test_nested_directories():
    """Test case for a repository with nested directories."""
    return run_test_case(
        "nested_directories",
        {
            "src/main.py": """
from src.utils.helper import helper_function

def main():
    helper_function()

if __name__ == "__main__":
    main()
""",
            "src/utils/helper.py": """
def helper_function():
    print("Helper function")

def unused_helper():
    print("Unused helper")
"""
        },
        {
            "summary": {
                "total_files": 2,
                "total_functions": 3,
                "total_classes": 0
            },
            "entrypoints": 1,
            "dead_code": 1,  # unused_helper
            "issues": 0
        }
    )

def test_dynamic_imports():
    """Test case for a repository with dynamic imports."""
    return run_test_case(
        "dynamic_imports",
        {
            "dynamic.py": """
def dynamic_import(module_name):
    module = __import__(module_name)
    return module

def main():
    math = dynamic_import('math')
    print(math.sqrt(16))

if __name__ == "__main__":
    main()
"""
        },
        {
            "summary": {
                "total_files": 1,
                "total_functions": 2,
                "total_classes": 0
            },
            "entrypoints": 1,
            "dead_code": 0,
            "issues": 0
        }
    )

def test_metaclasses():
    """Test case for a repository with metaclasses."""
    return run_test_case(
        "metaclasses",
        {
            "meta.py": """
class Meta(type):
    def __new__(mcs, name, bases, namespace):
        return super().__new__(mcs, name, bases, namespace)

class WithMeta(metaclass=Meta):
    def method(self):
        pass
"""
        },
        {
            "summary": {
                "total_files": 1,
                "total_functions": 1,
                "total_classes": 2
            },
            "entrypoints": 2,  # Both classes should be detected as entry points
            "dead_code": 0,
            "issues": 0
        }
    )

def test_decorators():
    """Test case for a repository with decorators."""
    return run_test_case(
        "decorators",
        {
            "decorators.py": """
def decorator(func):
    def wrapper(*args, **kwargs):
        print("Before function call")
        result = func(*args, **kwargs)
        print("After function call")
        return result
    return wrapper

@decorator
def decorated_function():
    print("Inside decorated function")

def main():
    decorated_function()

if __name__ == "__main__":
    main()
"""
        },
        {
            "summary": {
                "total_files": 1,
                "total_functions": 4,
                "total_classes": 0
            },
            "entrypoints": 1,
            "dead_code": 0,
            "issues": 0
        }
    )

def run_all_tests():
    """Run all test cases."""
    tests = [
        test_empty_repo,
        test_single_file,
        test_circular_imports,
        test_dead_code,
        test_complex_inheritance,
        test_syntax_error,
        test_large_file,
        test_mixed_languages,
        test_nested_directories,
        test_dynamic_imports,
        test_metaclasses,
        test_decorators
    ]
    
    results = []
    for test in tests:
        try:
            passed = test()
            results.append((test.__name__, passed))
        except Exception as e:
            print(f"Error running test {test.__name__}: {e}")
            results.append((test.__name__, False))
    
    print("\nTest Results:")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    for name, result in results:
        status = "✅ Passed" if result else "❌ Failed"
        print(f"{status}: {name}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
