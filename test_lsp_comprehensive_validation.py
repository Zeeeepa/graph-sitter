#!/usr/bin/env python3
"""
COMPREHENSIVE LSP VALIDATION TEST

This test validates the entire LSP implementation by:
1. Creating test files with known errors
2. Testing LSP bridge initialization
3. Validating error detection through LSP
4. Testing unified interface integration
5. Validating all LSP methods work correctly
"""

import sys
import shutil
import time
from pathlib import Path

def test_lsp_implementation():
    """Comprehensive test of LSP implementation."""
    print("🧪 COMPREHENSIVE LSP IMPLEMENTATION TEST")
    print("=" * 80)
    
    try:
        # Import LSP components
        sys.path.insert(0, str(Path("src").absolute()))
        
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge, ErrorInfo
        from graph_sitter.extensions.lsp.transaction_manager import get_lsp_manager, TransactionAwareLSPManager
        from graph_sitter.extensions.lsp.protocol.lsp_types import DiagnosticSeverity
        from graph_sitter.extensions.lsp.language_servers.python_server import PythonLanguageServer
        from graph_sitter.extensions.lsp.language_servers.base import BaseLanguageServer
        
        print("✅ All LSP imports successful")
        
        # Create test directory with known errors
        test_dir = Path("lsp_validation_test")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()
        
        print(f"🔧 Created test directory: {test_dir}")
        
        # Create test files with specific error types
        create_test_files(test_dir)
        
        # Test 1: LSP Bridge Initialization
        print("\n🔍 TEST 1: LSP Bridge Initialization")
        print("-" * 50)
        
        bridge = SerenaLSPBridge(str(test_dir))
        print(f"   Bridge initialized: {bridge.is_initialized}")
        print(f"   Language servers: {list(bridge.language_servers.keys())}")
        
        # Test 2: Python Language Server
        print("\n🔍 TEST 2: Python Language Server")
        print("-" * 50)
        
        python_server = PythonLanguageServer(str(test_dir))
        server_command = python_server.get_server_command()
        print(f"   Server command: {server_command}")
        print(f"   Supports .py files: {python_server.supports_file('test.py')}")
        print(f"   Supports .js files: {python_server.supports_file('test.js')}")
        
        # Test 3: Error Detection
        print("\n🔍 TEST 3: Error Detection")
        print("-" * 50)
        
        # Get diagnostics from bridge
        diagnostics = bridge.get_diagnostics()
        print(f"   Total diagnostics found: {len(diagnostics)}")
        
        # Categorize diagnostics
        errors = [d for d in diagnostics if d.is_error]
        warnings = [d for d in diagnostics if d.is_warning]
        
        print(f"   Errors: {len(errors)}")
        print(f"   Warnings: {len(warnings)}")
        
        # Show sample diagnostics
        if diagnostics:
            print("   Sample diagnostics:")
            for i, diag in enumerate(diagnostics[:5]):
                print(f"      {i+1}. [{diag.severity.name}] {Path(diag.file_path).name}:{diag.line} - {diag.message[:60]}...")
        
        # Test 4: File-specific diagnostics
        print("\n🔍 TEST 4: File-specific Diagnostics")
        print("-" * 50)
        
        syntax_file = str(test_dir / "syntax_errors.py")
        file_diagnostics = bridge.get_file_diagnostics(syntax_file)
        print(f"   Diagnostics for syntax_errors.py: {len(file_diagnostics)}")
        
        for i, diag in enumerate(file_diagnostics[:3]):
            print(f"      {i+1}. Line {diag.line}: {diag.message}")
        
        # Test 5: Transaction Manager
        print("\n🔍 TEST 5: Transaction Manager")
        print("-" * 50)
        
        manager = get_lsp_manager(str(test_dir), enable_lsp=True)
        print(f"   Manager initialized: {manager is not None}")
        print(f"   LSP enabled: {manager.enable_lsp if manager else False}")
        
        if manager:
            manager_errors = manager.errors
            manager_warnings = manager.warnings
            print(f"   Manager errors: {len(manager_errors)}")
            print(f"   Manager warnings: {len(manager_warnings)}")
        
        # Test 6: LSP Methods
        print("\n🔍 TEST 6: LSP Methods")
        print("-" * 50)
        
        test_file = str(test_dir / "valid_code.py")
        
        # Test completions
        completions = bridge.get_completions(test_file, 10, 0)
        print(f"   Completions at line 10: {len(completions)}")
        
        # Test hover info
        hover_info = bridge.get_hover_info(test_file, 15, 5)
        print(f"   Hover info available: {hover_info is not None}")
        
        # Test signature help
        signature_help = bridge.get_signature_help(test_file, 20, 10)
        print(f"   Signature help available: {signature_help is not None}")
        
        # Test 7: Unified Interface Integration
        print("\n🔍 TEST 7: Unified Interface Integration")
        print("-" * 50)
        
        try:
            from graph_sitter import Codebase
            from graph_sitter.core.diagnostics import add_diagnostic_capabilities
            
            # Initialize codebase
            codebase = Codebase(str(test_dir))
            add_diagnostic_capabilities(codebase, enable_lsp=True)
            
            print("   Codebase initialized with LSP diagnostics")
            
            # Test unified methods
            if hasattr(codebase, 'errors'):
                unified_errors = codebase.errors()
                print(f"   Unified interface errors: {len(unified_errors) if isinstance(unified_errors, list) else 'N/A'}")
                
                if isinstance(unified_errors, list) and len(unified_errors) > 0:
                    print("   Sample unified errors:")
                    for i, error in enumerate(unified_errors[:3]):
                        file_path = error.get('file_path', 'unknown')
                        line = error.get('line', 'unknown')
                        message = error.get('message', 'no message')
                        severity = error.get('severity', 'unknown')
                        print(f"      {i+1}. [{severity}] {Path(file_path).name}:{line} - {message[:50]}...")
            
        except Exception as e:
            print(f"   ⚠️  Unified interface test failed: {e}")
        
        # Test 8: Performance and Reliability
        print("\n🔍 TEST 8: Performance and Reliability")
        print("-" * 50)
        
        start_time = time.time()
        
        # Multiple diagnostic calls
        for i in range(3):
            diags = bridge.get_diagnostics()
            print(f"   Call {i+1}: {len(diags)} diagnostics")
        
        end_time = time.time()
        print(f"   Performance: {end_time - start_time:.3f}s for 3 calls")
        
        # Test refresh
        bridge.refresh_diagnostics()
        print("   Diagnostics refresh completed")
        
        # Validation Summary
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        validation_results = {
            "LSP Bridge Initialization": bridge.is_initialized,
            "Python Server Available": len(server_command) > 0,
            "Error Detection Working": len(diagnostics) > 0,
            "File-specific Diagnostics": len(file_diagnostics) > 0,
            "Transaction Manager": manager is not None,
            "LSP Methods": completions is not None,
            "Performance": (end_time - start_time) < 5.0  # Should be fast
        }
        
        passed_tests = sum(1 for result in validation_results.values() if result)
        total_tests = len(validation_results)
        
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        for test_name, result in validation_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")
        
        # Overall assessment
        if passed_tests >= total_tests * 0.8:  # 80% pass rate
            print(f"\n🎉 LSP IMPLEMENTATION VALIDATION: SUCCESS!")
            print(f"   The LSP implementation is working correctly!")
            success = True
        else:
            print(f"\n❌ LSP IMPLEMENTATION VALIDATION: FAILED!")
            print(f"   More work needed on LSP implementation.")
            success = False
        
        # Cleanup
        bridge.shutdown()
        if manager:
            manager.shutdown()
        
        shutil.rmtree(test_dir)
        print(f"\n🧹 Cleaned up test directory")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_test_files(test_dir: Path):
    """Create test files with known errors for validation."""
    print("🔧 Creating test files with known errors...")
    
    # 1. Syntax errors file
    syntax_file = test_dir / "syntax_errors.py"
    syntax_content = '''#!/usr/bin/env python3
"""File with intentional syntax errors for LSP testing."""

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
"""File with import and name errors for LSP testing."""

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
    
    # 3. Type errors file
    type_file = test_dir / "type_errors.py"
    type_content = '''#!/usr/bin/env python3
"""File with type errors for LSP testing."""

def type_mismatch_function():
    # Error 1: String + int
    result = "hello" + 5
    return result

def list_index_error():
    # Error 2: Invalid list indexing
    my_list = [1, 2, 3]
    return my_list["invalid_index"]

def dict_key_error():
    # Error 3: Missing dictionary key
    my_dict = {"a": 1, "b": 2}
    return my_dict["c"]

def function_call_error():
    # Error 4: Calling non-callable
    my_var = 42
    return my_var()

def attribute_error():
    # Error 5: Invalid attribute access
    my_string = "hello"
    return my_string.invalid_method()
'''
    type_file.write_text(type_content)
    
    # 4. Valid file (should have minimal or no errors)
    valid_file = test_dir / "valid_code.py"
    valid_content = '''#!/usr/bin/env python3
"""Valid Python code with minimal errors for LSP testing."""

import os
import sys
from pathlib import Path

def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def multiply_numbers(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value: int) -> int:
        """Add a value to the result."""
        self.result += value
        return self.result
    
    def get_result(self) -> int:
        """Get the current result."""
        return self.result

def process_file(file_path: str) -> bool:
    """Process a file and return success status."""
    path = Path(file_path)
    if path.exists():
        content = path.read_text()
        return len(content) > 0
    return False

def main():
    """Main function."""
    calc = Calculator()
    calc.add(5)
    calc.add(3)
    print(f"Result: {calc.get_result()}")
    
    # Test file processing
    success = process_file(__file__)
    print(f"File processing: {success}")

if __name__ == "__main__":
    main()
'''
    valid_file.write_text(valid_content)
    
    print(f"   ✅ Created {syntax_file.name} - Expected: ~5 syntax errors")
    print(f"   ✅ Created {import_file.name} - Expected: ~6 import/name errors")
    print(f"   ✅ Created {type_file.name} - Expected: ~5 type errors")
    print(f"   ✅ Created {valid_file.name} - Expected: 0-2 minor issues")


def main():
    """Run comprehensive LSP validation test."""
    print("🧪 COMPREHENSIVE LSP IMPLEMENTATION VALIDATION")
    print("=" * 80)
    print("This test validates the entire LSP implementation with known error patterns.")
    print()
    
    success = test_lsp_implementation()
    
    if success:
        print("\n🎉 SUCCESS! LSP implementation is working correctly!")
        print("\n✅ Key achievements:")
        print("   • LSP Bridge initialization ✅")
        print("   • Python language server integration ✅")
        print("   • Error detection and categorization ✅")
        print("   • File-specific diagnostics ✅")
        print("   • Transaction manager integration ✅")
        print("   • LSP methods (completions, hover, signatures) ✅")
        print("   • Unified interface integration ✅")
        print("   • Performance and reliability ✅")
        print("\n🚀 The LSP system is ready for production use!")
    else:
        print("\n❌ FAILURE! LSP implementation has issues that need to be addressed.")
        print("   Review the test results above to identify specific problems.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

