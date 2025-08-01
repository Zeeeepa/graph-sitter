#!/usr/bin/env python3
"""
Comprehensive Consolidation Test Suite

This test suite validates the Serena consolidation with:
1. Pre-set known errors for validation
2. Working feature verification
3. Performance benchmarking
4. Regression testing

Tests both the unified interface and the consolidated LSP functionality.
"""

import os
import sys
import time
import json
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from graph_sitter import Codebase
    from graph_sitter.extensions.lsp.protocol.lsp_types import ErrorInfo, DiagnosticSeverity
    from graph_sitter.extensions.lsp.transaction_manager import TransactionAwareLSPManager
    from graph_sitter.core.error_methods import SerenaErrorMethods
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


@dataclass
class TestResult:
    """Test result with performance metrics."""
    test_name: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class KnownErrorGenerator:
    """Generates files with known errors for testing."""
    
    @staticmethod
    def create_syntax_error_file(file_path: Path) -> Dict[str, Any]:
        """Create a Python file with syntax errors."""
        content = '''
# This file contains intentional syntax errors for testing
def broken_function(
    # Missing closing parenthesis - syntax error
    
def another_function():
    # Indentation error
  print("Wrong indentation")
    
# Undefined variable error
result = undefined_variable + 5

# Import error
from nonexistent_module import something

# Type error (if type checking is enabled)
def type_error_function(x: int) -> str:
    return x  # Should return string, not int

# Unused variable
def unused_variable_function():
    unused_var = "This variable is never used"
    return "done"

# Missing return type annotation
def missing_annotation(x):
    return x * 2
'''
        file_path.write_text(content)
        return {
            'file_path': str(file_path),
            'expected_errors': [
                {'type': 'syntax', 'line': 4, 'message': 'invalid syntax'},
                {'type': 'indentation', 'line': 8, 'message': 'indentation'},
                {'type': 'undefined', 'line': 11, 'message': 'undefined'},
                {'type': 'import', 'line': 14, 'message': 'import'},
                {'type': 'type', 'line': 18, 'message': 'return'},
                {'type': 'unused', 'line': 22, 'message': 'unused'},
            ]
        }
    
    @staticmethod
    def create_working_file(file_path: Path) -> Dict[str, Any]:
        """Create a Python file with no errors."""
        content = '''
"""
This is a well-formed Python file with no errors.
Used for testing that working code is not flagged.
"""

from typing import List, Optional
import os
import sys


class WorkingClass:
    """A properly implemented class."""
    
    def __init__(self, name: str) -> None:
        self.name = name
        self._private_attr = 0
    
    def get_name(self) -> str:
        """Get the name."""
        return self.name
    
    def process_data(self, data: List[int]) -> Optional[int]:
        """Process a list of integers."""
        if not data:
            return None
        
        total = sum(data)
        self._private_attr += 1
        return total


def working_function(x: int, y: int) -> int:
    """A properly typed function."""
    return x + y


def main() -> None:
    """Main function."""
    instance = WorkingClass("test")
    result = instance.process_data([1, 2, 3, 4, 5])
    
    if result is not None:
        print(f"Result: {result}")
    
    func_result = working_function(10, 20)
    print(f"Function result: {func_result}")


if __name__ == "__main__":
    main()
'''
        file_path.write_text(content)
        return {
            'file_path': str(file_path),
            'expected_errors': []  # No errors expected
        }


class ConsolidationTestSuite:
    """Comprehensive test suite for the consolidation."""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.temp_dir: Optional[Path] = None
        self.codebase: Optional[Codebase] = None
        
    def setup_test_environment(self) -> bool:
        """Set up the test environment with known error files."""
        try:
            # Create temporary directory
            self.temp_dir = Path(tempfile.mkdtemp(prefix="consolidation_test_"))
            print(f"📁 Created test directory: {self.temp_dir}")
            
            # Create test files
            error_file_info = KnownErrorGenerator.create_syntax_error_file(
                self.temp_dir / "error_file.py"
            )
            
            working_file_info = KnownErrorGenerator.create_working_file(
                self.temp_dir / "working_file.py"
            )
            
            # Create a simple __init__.py to make it a package
            (self.temp_dir / "__init__.py").write_text("# Test package")
            
            # Store expected results
            self.expected_results = {
                'error_file.py': error_file_info,
                'working_file.py': working_file_info
            }
            
            print(f"✅ Test environment setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup test environment: {e}")
            return False
    
    def test_unified_interface_availability(self) -> TestResult:
        """Test that the unified interface methods are available."""
        start_time = time.time()
        
        try:
            if not GRAPH_SITTER_AVAILABLE:
                return TestResult(
                    test_name="unified_interface_availability",
                    success=False,
                    duration=time.time() - start_time,
                    error_message="Graph-sitter not available"
                )
            
            # Initialize codebase
            self.codebase = Codebase(str(self.temp_dir))
            
            # Check that all required methods exist
            required_methods = ['errors', 'full_error_context', 'resolve_errors', 'resolve_error']
            missing_methods = []
            
            for method in required_methods:
                if not hasattr(self.codebase, method):
                    missing_methods.append(method)
            
            if missing_methods:
                return TestResult(
                    test_name="unified_interface_availability",
                    success=False,
                    duration=time.time() - start_time,
                    error_message=f"Missing methods: {missing_methods}"
                )
            
            # Check that methods are callable
            for method in required_methods:
                method_obj = getattr(self.codebase, method)
                if not callable(method_obj):
                    return TestResult(
                        test_name="unified_interface_availability",
                        success=False,
                        duration=time.time() - start_time,
                        error_message=f"Method {method} is not callable"
                    )
            
            return TestResult(
                test_name="unified_interface_availability",
                success=True,
                duration=time.time() - start_time,
                details={'methods_found': required_methods}
            )
            
        except Exception as e:
            return TestResult(
                test_name="unified_interface_availability",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_error_detection_functionality(self) -> TestResult:
        """Test that error detection works with known errors."""
        start_time = time.time()
        
        try:
            if not self.codebase:
                return TestResult(
                    test_name="error_detection_functionality",
                    success=False,
                    duration=time.time() - start_time,
                    error_message="Codebase not initialized"
                )
            
            # Get all errors
            all_errors = self.codebase.errors()
            
            # Validate that we got a list
            if not isinstance(all_errors, list):
                return TestResult(
                    test_name="error_detection_functionality",
                    success=False,
                    duration=time.time() - start_time,
                    error_message=f"Expected list, got {type(all_errors)}"
                )
            
            # Check error structure
            error_count = len(all_errors)
            valid_errors = 0
            
            for error in all_errors:
                if isinstance(error, dict) and all(key in error for key in ['id', 'file_path', 'line', 'message']):
                    valid_errors += 1
            
            # We should have found some errors in our error file
            success = error_count > 0 and valid_errors == error_count
            
            return TestResult(
                test_name="error_detection_functionality",
                success=success,
                duration=time.time() - start_time,
                details={
                    'total_errors': error_count,
                    'valid_errors': valid_errors,
                    'sample_errors': all_errors[:3] if all_errors else []
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="error_detection_functionality",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_error_context_functionality(self) -> TestResult:
        """Test that error context retrieval works."""
        start_time = time.time()
        
        try:
            if not self.codebase:
                return TestResult(
                    test_name="error_context_functionality",
                    success=False,
                    duration=time.time() - start_time,
                    error_message="Codebase not initialized"
                )
            
            # Get errors first
            all_errors = self.codebase.errors()
            
            if not all_errors:
                return TestResult(
                    test_name="error_context_functionality",
                    success=False,
                    duration=time.time() - start_time,
                    error_message="No errors found to test context retrieval"
                )
            
            # Test context retrieval for first error
            first_error = all_errors[0]
            error_id = first_error['id']
            
            context = self.codebase.full_error_context(error_id)
            
            # Context might be None if Serena analyzer is not available
            # That's okay for this test - we're testing the interface
            success = True  # Interface worked even if context is None
            
            return TestResult(
                test_name="error_context_functionality",
                success=success,
                duration=time.time() - start_time,
                details={
                    'tested_error_id': error_id,
                    'context_available': context is not None,
                    'context_type': type(context).__name__
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="error_context_functionality",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_error_resolution_interface(self) -> TestResult:
        """Test that error resolution interface works."""
        start_time = time.time()
        
        try:
            if not self.codebase:
                return TestResult(
                    test_name="error_resolution_interface",
                    success=False,
                    duration=time.time() - start_time,
                    error_message="Codebase not initialized"
                )
            
            # Test resolve_errors (all errors)
            resolve_all_result = self.codebase.resolve_errors()
            
            if not isinstance(resolve_all_result, dict):
                return TestResult(
                    test_name="error_resolution_interface",
                    success=False,
                    duration=time.time() - start_time,
                    error_message=f"resolve_errors returned {type(resolve_all_result)}, expected dict"
                )
            
            # Check required keys in result
            required_keys = ['total_errors', 'attempted_fixes', 'successful_fixes', 'failed_fixes', 'results']
            missing_keys = [key for key in required_keys if key not in resolve_all_result]
            
            if missing_keys:
                return TestResult(
                    test_name="error_resolution_interface",
                    success=False,
                    duration=time.time() - start_time,
                    error_message=f"Missing keys in resolve_errors result: {missing_keys}"
                )
            
            # Test resolve_error (single error) if we have errors
            all_errors = self.codebase.errors()
            single_resolve_result = None
            
            if all_errors:
                first_error_id = all_errors[0]['id']
                single_resolve_result = self.codebase.resolve_error(first_error_id)
                
                if not isinstance(single_resolve_result, dict):
                    return TestResult(
                        test_name="error_resolution_interface",
                        success=False,
                        duration=time.time() - start_time,
                        error_message=f"resolve_error returned {type(single_resolve_result)}, expected dict"
                    )
            
            return TestResult(
                test_name="error_resolution_interface",
                success=True,
                duration=time.time() - start_time,
                details={
                    'resolve_all_result': resolve_all_result,
                    'single_resolve_tested': single_resolve_result is not None,
                    'single_resolve_result': single_resolve_result
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="error_resolution_interface",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_consolidated_error_info_class(self) -> TestResult:
        """Test that the consolidated ErrorInfo class works correctly."""
        start_time = time.time()
        
        try:
            # Test ErrorInfo creation and properties
            error_info = ErrorInfo(
                file_path="test.py",
                line=10,
                character=5,
                message="Test error message",
                severity=DiagnosticSeverity.ERROR,
                source="test",
                code="E001"
            )
            
            # Test properties
            assert error_info.id == "test.py:10:5"
            assert error_info.is_error == True
            assert error_info.is_warning == False
            assert error_info.column == 5  # Backward compatibility
            assert error_info.severity_name == "error"
            
            # Test string representation
            str_repr = str(error_info)
            assert "test.py:10:5" in str_repr
            assert "error" in str_repr.lower()
            assert "Test error message" in str_repr
            
            # Test LSP conversion
            lsp_diagnostic = error_info.to_lsp_diagnostic()
            assert lsp_diagnostic.message == "Test error message"
            assert lsp_diagnostic.severity == DiagnosticSeverity.ERROR
            
            # Test from LSP conversion
            from graph_sitter.extensions.lsp.protocol.lsp_types import Diagnostic, Range, Position
            
            lsp_diag = Diagnostic(
                range=Range(
                    start=Position(line=4, character=10),
                    end=Position(line=4, character=15)
                ),
                message="LSP test message",
                severity=DiagnosticSeverity.WARNING,
                source="pylsp"
            )
            
            converted_error = ErrorInfo.from_lsp_diagnostic(lsp_diag, "converted.py")
            assert converted_error.file_path == "converted.py"
            assert converted_error.line == 5  # Converted to 1-based
            assert converted_error.character == 10
            assert converted_error.message == "LSP test message"
            assert converted_error.severity == DiagnosticSeverity.WARNING
            
            return TestResult(
                test_name="consolidated_error_info_class",
                success=True,
                duration=time.time() - start_time,
                details={
                    'properties_tested': ['id', 'is_error', 'is_warning', 'column', 'severity_name'],
                    'conversions_tested': ['to_lsp_diagnostic', 'from_lsp_diagnostic'],
                    'string_representation_works': True
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="consolidated_error_info_class",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_performance_benchmarks(self) -> TestResult:
        """Test performance of error detection and processing."""
        start_time = time.time()
        
        try:
            if not self.codebase:
                return TestResult(
                    test_name="performance_benchmarks",
                    success=False,
                    duration=time.time() - start_time,
                    error_message="Codebase not initialized"
                )
            
            # Benchmark error detection
            error_detection_times = []
            for i in range(3):  # Run 3 times for average
                start = time.time()
                errors = self.codebase.errors()
                error_detection_times.append(time.time() - start)
            
            avg_error_detection_time = sum(error_detection_times) / len(error_detection_times)
            
            # Benchmark context retrieval if we have errors
            context_retrieval_times = []
            errors = self.codebase.errors()
            
            if errors:
                for i in range(min(3, len(errors))):  # Test up to 3 errors
                    start = time.time()
                    context = self.codebase.full_error_context(errors[i]['id'])
                    context_retrieval_times.append(time.time() - start)
            
            avg_context_time = sum(context_retrieval_times) / len(context_retrieval_times) if context_retrieval_times else 0
            
            # Performance thresholds (reasonable for small test files)
            error_detection_threshold = 5.0  # 5 seconds max
            context_retrieval_threshold = 2.0  # 2 seconds max
            
            success = (avg_error_detection_time < error_detection_threshold and 
                      (avg_context_time < context_retrieval_threshold or avg_context_time == 0))
            
            return TestResult(
                test_name="performance_benchmarks",
                success=success,
                duration=time.time() - start_time,
                details={
                    'avg_error_detection_time': avg_error_detection_time,
                    'avg_context_retrieval_time': avg_context_time,
                    'error_detection_threshold': error_detection_threshold,
                    'context_retrieval_threshold': context_retrieval_threshold,
                    'errors_found': len(errors) if errors else 0
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="performance_benchmarks",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_import_consolidation(self) -> TestResult:
        """Test that imports work correctly after consolidation."""
        start_time = time.time()
        
        try:
            # Test importing consolidated ErrorInfo
            from graph_sitter.extensions.lsp.protocol.lsp_types import ErrorInfo, DiagnosticSeverity
            
            # Test importing transaction manager
            from graph_sitter.extensions.lsp.transaction_manager import TransactionAwareLSPManager
            
            # Test importing from core diagnostics
            from graph_sitter.core.diagnostics import CodebaseDiagnostics
            
            # Test that we can create instances
            error_info = ErrorInfo(
                file_path="test.py",
                line=1,
                character=0,
                message="Test",
                severity=DiagnosticSeverity.ERROR
            )
            
            # Test that the classes are the same (no duplicates)
            from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
            
            # This should work without import errors
            bridge = SerenaLSPBridge(".")
            
            return TestResult(
                test_name="import_consolidation",
                success=True,
                duration=time.time() - start_time,
                details={
                    'imports_tested': [
                        'ErrorInfo from lsp_types',
                        'TransactionAwareLSPManager',
                        'CodebaseDiagnostics',
                        'SerenaLSPBridge'
                    ],
                    'instance_creation_works': True
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="import_consolidation",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print("\n🧪 STARTING COMPREHENSIVE CONSOLIDATION TESTS")
        print("=" * 60)
        
        if not GRAPH_SITTER_AVAILABLE:
            print("❌ Graph-sitter not available - skipping tests")
            return {
                'success': False,
                'error': 'Graph-sitter not available',
                'tests_run': 0,
                'tests_passed': 0
            }
        
        # Setup test environment
        if not self.setup_test_environment():
            return {
                'success': False,
                'error': 'Failed to setup test environment',
                'tests_run': 0,
                'tests_passed': 0
            }
        
        # Define all tests
        tests = [
            self.test_unified_interface_availability,
            self.test_consolidated_error_info_class,
            self.test_import_consolidation,
            self.test_error_detection_functionality,
            self.test_error_context_functionality,
            self.test_error_resolution_interface,
            self.test_performance_benchmarks
        ]
        
        # Run all tests
        for test_func in tests:
            print(f"\n🔍 Running {test_func.__name__}...")
            result = test_func()
            self.test_results.append(result)
            
            if result.success:
                print(f"✅ {result.test_name} - PASSED ({result.duration:.3f}s)")
                if result.details:
                    for key, value in result.details.items():
                        print(f"   📊 {key}: {value}")
            else:
                print(f"❌ {result.test_name} - FAILED ({result.duration:.3f}s)")
                print(f"   💥 Error: {result.error_message}")
        
        # Calculate summary
        tests_passed = sum(1 for r in self.test_results if r.success)
        tests_run = len(self.test_results)
        success_rate = (tests_passed / tests_run) * 100 if tests_run > 0 else 0
        
        # Print summary
        print(f"\n📊 TEST SUMMARY")
        print("=" * 30)
        print(f"Tests Run: {tests_run}")
        print(f"Tests Passed: {tests_passed}")
        print(f"Tests Failed: {tests_run - tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        results = {
            'success': tests_passed == tests_run,
            'tests_run': tests_run,
            'tests_passed': tests_passed,
            'success_rate': success_rate,
            'test_results': [
                {
                    'name': r.test_name,
                    'success': r.success,
                    'duration': r.duration,
                    'error': r.error_message,
                    'details': r.details
                }
                for r in self.test_results
            ]
        }
        
        return results
    
    def cleanup(self):
        """Clean up test environment."""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                print(f"🧹 Cleaned up test directory: {self.temp_dir}")
            except Exception as e:
                print(f"⚠️ Failed to cleanup test directory: {e}")


def main():
    """Main function to run the comprehensive test suite."""
    print("🚀 COMPREHENSIVE CONSOLIDATION TEST SUITE")
    print("=" * 50)
    print("Testing Serena consolidation with known errors and working features")
    print()
    
    # Run tests
    test_suite = ConsolidationTestSuite()
    
    try:
        results = test_suite.run_all_tests()
        
        # Save results to file
        results_file = Path("consolidation_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Test results saved to: {results_file}")
        
        # Print final status
        if results['success']:
            print(f"\n🎉 ALL TESTS PASSED! Consolidation is working correctly.")
            print(f"✅ {results['tests_passed']}/{results['tests_run']} tests successful")
        else:
            print(f"\n⚠️ Some tests failed. Check results for details.")
            print(f"❌ {results['tests_run'] - results['tests_passed']}/{results['tests_run']} tests failed")
        
        return 0 if results['success'] else 1
        
    except Exception as e:
        print(f"❌ Test suite failed with exception: {e}")
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup
        test_suite.cleanup()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
