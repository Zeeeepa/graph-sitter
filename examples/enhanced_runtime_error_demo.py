#!/usr/bin/env python3
"""
Enhanced Runtime Error Detection Demo

This script demonstrates the comprehensive runtime error detection and analysis
capabilities of the enhanced SerenaLSPBridge with full Serena integration.
"""

import sys
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any

# Add the src directory to the path so we can import graph_sitter modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_sitter.extensions.lsp.serena_bridge import (
    SerenaLSPBridge, ErrorInfo, ErrorType, RuntimeContext, 
    RuntimeErrorCollector, DiagnosticSeverity
)


def create_test_files(repo_path: Path) -> None:
    """Create test files with various types of errors."""
    
    # File with runtime errors
    runtime_error_file = repo_path / "runtime_errors.py"
    runtime_error_file.write_text("""
def division_by_zero_error():
    \"\"\"Function that will cause a ZeroDivisionError.\"\"\"
    x = 10
    y = 0
    result = x / y  # This will cause a runtime error
    return result

def attribute_error():
    \"\"\"Function that will cause an AttributeError.\"\"\"
    obj = None
    return obj.value  # This will cause a runtime error

def index_error():
    \"\"\"Function that will cause an IndexError.\"\"\"
    my_list = [1, 2, 3]
    return my_list[10]  # This will cause a runtime error

def key_error():
    \"\"\"Function that will cause a KeyError.\"\"\"
    my_dict = {"a": 1, "b": 2}
    return my_dict["c"]  # This will cause a runtime error

def type_error():
    \"\"\"Function that will cause a TypeError.\"\"\"
    return "string" + 42  # This will cause a runtime error

def name_error():
    \"\"\"Function that will cause a NameError.\"\"\"
    return undefined_variable  # This will cause a runtime error

if __name__ == "__main__":
    # These will be caught by the runtime error collector
    try:
        division_by_zero_error()
    except:
        pass
    
    try:
        attribute_error()
    except:
        pass
    
    try:
        index_error()
    except:
        pass
""")

    # File with syntax errors (for static analysis)
    syntax_error_file = repo_path / "syntax_errors.py"
    syntax_error_file.write_text("""
def broken_function(
    # Missing closing parenthesis - syntax error
    pass

def another_broken_function():
    if True
        # Missing colon - syntax error
        pass

# Indentation error
def indentation_error():
pass
""")

    # File with good code (no errors)
    good_file = repo_path / "good_code.py"
    good_file.write_text("""
def well_written_function(x: int, y: int) -> int:
    \"\"\"A well-written function with proper error handling.\"\"\"
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x // y

def another_good_function(data: list) -> int:
    \"\"\"Another well-written function.\"\"\"
    if not data:
        return 0
    return sum(data)

class WellDesignedClass:
    \"\"\"A well-designed class.\"\"\"
    
    def __init__(self, value: int):
        self.value = value
    
    def get_value(self) -> int:
        return self.value
    
    def set_value(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Value must be an integer")
        self.value = value
""")


def demonstrate_runtime_error_collection(repo_path: Path) -> None:
    """Demonstrate runtime error collection capabilities."""
    print("🔥 Runtime Error Collection Demo")
    print("=" * 50)
    
    # Initialize the enhanced LSP bridge
    bridge = SerenaLSPBridge(str(repo_path), enable_runtime_collection=True)
    
    print(f"✅ Enhanced LSP Bridge initialized for: {repo_path}")
    print(f"🔍 Runtime collection enabled: {bridge.enable_runtime_collection}")
    print(f"🏗️  Serena available: {hasattr(bridge, 'serena_project')}")
    
    # Get initial status
    status = bridge.get_status()
    print(f"\n📊 Initial Status:")
    print(f"   - Language servers: {status['language_servers']}")
    print(f"   - Runtime collection: {status['runtime_collection_enabled']}")
    print(f"   - Total diagnostics: {status['diagnostic_counts']['total_diagnostics']}")
    
    # Trigger some runtime errors by importing and running the error file
    print(f"\n🚨 Triggering runtime errors...")
    
    try:
        # Import the runtime error module to trigger errors
        import importlib.util
        spec = importlib.util.spec_from_file_location("runtime_errors", repo_path / "runtime_errors.py")
        runtime_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime_module)
        
        # Execute functions that will cause errors
        error_functions = [
            runtime_module.division_by_zero_error,
            runtime_module.attribute_error,
            runtime_module.index_error,
            runtime_module.key_error,
            runtime_module.type_error,
            runtime_module.name_error
        ]
        
        for func in error_functions:
            try:
                func()
            except Exception as e:
                print(f"   ⚡ Caught {type(e).__name__}: {e}")
        
    except Exception as e:
        print(f"   ❌ Error importing module: {e}")
    
    # Give some time for error collection
    time.sleep(0.5)
    
    # Get runtime errors
    runtime_errors = bridge.get_runtime_errors()
    print(f"\n📋 Runtime Errors Collected: {len(runtime_errors)}")
    
    for i, error in enumerate(runtime_errors[:5], 1):  # Show first 5 errors
        print(f"\n   🔸 Error {i}:")
        print(f"      File: {error.file_path}")
        print(f"      Line: {error.line + 1}")  # Convert back to 1-based
        print(f"      Type: {error.error_type.name}")
        print(f"      Message: {error.message}")
        
        if error.runtime_context:
            print(f"      Exception: {error.runtime_context.exception_type}")
            print(f"      Stack frames: {len(error.runtime_context.stack_trace)}")
            if error.runtime_context.local_variables:
                print(f"      Local vars: {list(error.runtime_context.local_variables.keys())[:3]}")
        
        if error.fix_suggestions:
            print(f"      Suggestions: {error.fix_suggestions[0]}")
    
    # Get runtime error summary
    summary = bridge.get_runtime_error_summary()
    print(f"\n📈 Runtime Error Summary:")
    print(f"   - Total errors: {summary.get('total_errors', 0)}")
    print(f"   - Collection active: {summary.get('collection_active', False)}")
    print(f"   - Errors by type: {summary.get('errors_by_type', {})}")
    print(f"   - Errors by file: {summary.get('errors_by_file', {})}")
    
    # Demonstrate file-specific error retrieval
    print(f"\n📁 File-Specific Errors:")
    for file_name in ["runtime_errors.py", "syntax_errors.py", "good_code.py"]:
        file_errors = bridge.get_file_diagnostics(file_name, include_runtime=True)
        runtime_only = bridge.get_runtime_errors_for_file(file_name)
        static_only = bridge.get_file_diagnostics(file_name, include_runtime=False)
        
        print(f"   📄 {file_name}:")
        print(f"      Total diagnostics: {len(file_errors)}")
        print(f"      Runtime errors: {len(runtime_only)}")
        print(f"      Static errors: {len(static_only)}")
    
    # Demonstrate comprehensive error context
    print(f"\n🔍 Detailed Error Context:")
    errors_with_context = bridge.get_all_errors_with_context()
    
    for i, error_context in enumerate(errors_with_context[:2], 1):  # Show first 2
        print(f"\n   🔸 Error Context {i}:")
        basic_info = error_context.get('basic_info', {})
        print(f"      File: {basic_info.get('file_path', 'unknown')}")
        print(f"      Line: {basic_info.get('line', 0) + 1}")
        print(f"      Severity: {basic_info.get('severity', 'unknown')}")
        print(f"      Type: {basic_info.get('error_type', 'unknown')}")
        
        if 'runtime' in error_context:
            runtime_info = error_context['runtime']
            print(f"      Exception: {runtime_info.get('exception_type', 'unknown')}")
            print(f"      Timestamp: {runtime_info.get('timestamp', 0)}")
        
        if 'code_context' in error_context:
            context_lines = error_context['code_context'].split('\n')[:3]
            print(f"      Code context: {len(context_lines)} lines")
        
        if 'fix_suggestions' in error_context:
            suggestions = error_context['fix_suggestions']
            if suggestions:
                print(f"      Fix suggestion: {suggestions[0]}")
    
    # Final status
    final_status = bridge.get_status()
    print(f"\n📊 Final Status:")
    print(f"   - Total diagnostics: {final_status['diagnostic_counts']['total_diagnostics']}")
    print(f"   - Runtime errors: {final_status['diagnostic_counts']['runtime_errors']}")
    print(f"   - Static diagnostics: {final_status['diagnostic_counts']['static_diagnostics']}")
    print(f"   - Errors: {final_status['diagnostic_counts']['errors']}")
    print(f"   - Warnings: {final_status['diagnostic_counts']['warnings']}")
    
    # Cleanup
    bridge.shutdown()
    print(f"\n✅ Enhanced LSP Bridge shutdown complete")


def demonstrate_error_analysis_features(repo_path: Path) -> None:
    """Demonstrate advanced error analysis features."""
    print(f"\n🧠 Advanced Error Analysis Demo")
    print("=" * 50)
    
    bridge = SerenaLSPBridge(str(repo_path), enable_runtime_collection=True)
    
    # Create a specific error scenario
    error_context = RuntimeContext(
        exception_type="AttributeError",
        stack_trace=[
            "  File \"runtime_errors.py\", line 12, in attribute_error",
            "    return obj.value",
            "AttributeError: 'NoneType' object has no attribute 'value'"
        ],
        local_variables={"obj": "None"},
        execution_path=["main", "attribute_error"]
    )
    
    test_error = ErrorInfo(
        file_path="runtime_errors.py",
        line=11,  # 0-based
        character=11,
        message="AttributeError: 'NoneType' object has no attribute 'value'",
        severity=DiagnosticSeverity.ERROR,
        error_type=ErrorType.RUNTIME_ERROR,
        runtime_context=error_context
    )
    
    # Demonstrate fix suggestion generation
    suggestions = bridge._generate_fix_suggestions(test_error)
    print(f"🔧 Fix Suggestions for AttributeError:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion}")
    
    # Demonstrate code context retrieval
    code_context = bridge._get_enhanced_code_context("runtime_errors.py", 11)
    if code_context:
        print(f"\n📝 Code Context:")
        for line in code_context.split('\n')[:10]:  # Show first 10 lines
            print(f"   {line}")
    
    # Demonstrate comprehensive error context
    full_context = test_error.get_full_context()
    print(f"\n🔍 Full Error Context Keys:")
    for key in full_context.keys():
        print(f"   - {key}")
    
    bridge.shutdown()


def main():
    """Main demonstration function."""
    print("🚀 Enhanced Serena LSP Bridge - Runtime Error Detection Demo")
    print("=" * 70)
    
    # Create a temporary repository for testing
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        print(f"📁 Using temporary repository: {repo_path}")
        
        # Create test files
        create_test_files(repo_path)
        print(f"📝 Created test files with various error types")
        
        # Demonstrate runtime error collection
        demonstrate_runtime_error_collection(repo_path)
        
        # Demonstrate advanced error analysis
        demonstrate_error_analysis_features(repo_path)
    
    print(f"\n🎉 Demo completed successfully!")
    print(f"\n💡 Key Features Demonstrated:")
    print(f"   ✅ Runtime error collection during execution")
    print(f"   ✅ Comprehensive error context with stack traces")
    print(f"   ✅ Variable state capture at error time")
    print(f"   ✅ Intelligent fix suggestions")
    print(f"   ✅ File-specific error filtering")
    print(f"   ✅ Mixed static/runtime error handling")
    print(f"   ✅ Enhanced LSP integration with Serena")
    print(f"   ✅ Comprehensive error analysis and reporting")


if __name__ == "__main__":
    main()

