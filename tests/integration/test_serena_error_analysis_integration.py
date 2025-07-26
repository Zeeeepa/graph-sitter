#!/usr/bin/env python3
"""
Integration Tests for Serena Error Analysis

These tests demonstrate actual usage of the error analysis system with real codebases
and validate end-to-end functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena import (
    SerenaAPI,
    ComprehensiveErrorAnalyzer,
    get_codebase_error_analysis,
    analyze_file_errors,
    find_function_relationships,
    create_serena_api
)


class TestRealWorldErrorAnalysis:
    """Integration tests with realistic code scenarios."""
    
    @pytest.fixture
    def realistic_python_project(self):
        """Create a realistic Python project with various error types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create project structure
            (project_root / "src").mkdir()
            (project_root / "tests").mkdir()
            (project_root / "src" / "myproject").mkdir()
            
            # Main module with various issues
            main_py = '''
"""Main application module."""
import os
import sys
from typing import List, Dict, Optional
from .utils import process_data, validate_input
from .database import DatabaseManager

class DataProcessor:
    """Process data with various methods."""
    
    def __init__(self, config_path: str, unused_param: str = None):
        """Initialize processor."""
        self.config_path = config_path
        # unused_param is not used - should be detected
        self.db_manager = DatabaseManager()
    
    def process_file(self, file_path: str, options: Dict, extra_param: str) -> List[str]:
        """Process a file with options."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Unused parameter 'extra_param' should be detected
        results = []
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Call to undefined function - should be detected
        processed = undefined_function(content)  # Error here
        
        # Call to utils function
        validated_data = validate_input(processed)
        final_data = process_data(validated_data, options)
        
        return final_data
    
    def batch_process(self, files: List[str]) -> Dict[str, List[str]]:
        """Process multiple files."""
        results = {}
        for file_path in files:
            try:
                # Missing required parameter - should be detected
                result = self.process_file(file_path, {})  # Missing extra_param
                results[file_path] = result
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                results[file_path] = []
        return results
    
    def complex_analysis(self, data, param1, param2, param3, param4, param5, param6, param7):
        """Function with too many parameters - code smell."""
        return data + param1 + param2 + param3 + param4 + param5 + param6 + param7
'''
            
            # Utils module
            utils_py = '''
"""Utility functions."""
import json
from typing import Any, Dict, List

def validate_input(data: Any) -> Dict:
    """Validate input data."""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {"raw": data}
    return {"data": data}

def process_data(data: Dict, options: Dict) -> List[str]:
    """Process validated data."""
    results = []
    
    # Access undefined variable - should be detected
    if enable_debug:  # Error: enable_debug not defined
        print(f"Processing data: {data}")
    
    for key, value in data.items():
        if key in options.get("include_keys", []):
            results.append(f"{key}: {value}")
    
    return results

def unused_function(param1, param2):
    """This function is never called - should be detected."""
    return param1 + param2
'''
            
            # Database module
            database_py = '''
"""Database management."""
import sqlite3
from typing import Optional, List, Dict

class DatabaseManager:
    """Manage database connections and operations."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        self.db_path = db_path or ":memory:"
        self.connection = None
    
    def connect(self):
        """Connect to database."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            return True
        except sqlite3.Error as e:
            # Undefined variable in error handling
            logger.error(f"Database connection failed: {e}")  # Error: logger not defined
            return False
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a database query."""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Fetch results
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        return results
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
'''
            
            # Test file with issues
            test_main_py = '''
"""Tests for main module."""
import unittest
from unittest.mock import Mock, patch
from src.myproject.main import DataProcessor

class TestDataProcessor(unittest.TestCase):
    """Test the DataProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Unused parameter in constructor call
        self.processor = DataProcessor("/tmp/config.json", "unused_value")
    
    def test_process_file(self):
        """Test file processing."""
        # Missing import - should be detected
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='{"test": "data"}')):
                # This will fail due to undefined_function
                result = self.processor.process_file("test.txt", {"include_keys": ["test"]}, "extra")
                self.assertIsInstance(result, list)
    
    def test_batch_process(self):
        """Test batch processing."""
        files = ["file1.txt", "file2.txt"]
        results = self.processor.batch_process(files)
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), 2)

if __name__ == '__main__':
    unittest.main()
'''
            
            # Write all files
            (project_root / "src" / "myproject" / "__init__.py").write_text("")
            (project_root / "src" / "myproject" / "main.py").write_text(main_py)
            (project_root / "src" / "myproject" / "utils.py").write_text(utils_py)
            (project_root / "src" / "myproject" / "database.py").write_text(database_py)
            (project_root / "tests" / "__init__.py").write_text("")
            (project_root / "tests" / "test_main.py").write_text(test_main_py)
            
            # Create requirements.txt
            (project_root / "requirements.txt").write_text("requests>=2.25.0\npytest>=6.0.0\n")
            
            # Create setup.py with issues
            setup_py = '''
from setuptools import setup, find_packages

# Missing import - should be detected
version = get_version()  # Error: get_version not defined

setup(
    name="myproject",
    version=version,
    packages=find_packages(),
    install_requires=[
        "requests",
        "pytest",
    ],
    # Unused parameter in function call
    author_email="test@example.com",
    description="A test project with various issues",
)
'''
            (project_root / "setup.py").write_text(setup_py)
            
            yield project_root
    
    def test_comprehensive_project_analysis(self, realistic_python_project):
        """Test comprehensive analysis of a realistic project."""
        # Create codebase
        codebase = Codebase(str(realistic_python_project))
        
        # Create analyzer
        analyzer = ComprehensiveErrorAnalyzer(codebase, enable_lsp=False)
        
        # Test that analyzer initializes without errors
        assert analyzer is not None
        assert analyzer.codebase == codebase
        
        # Test error summary generation
        summary = analyzer.get_error_summary()
        assert isinstance(summary, dict)
        assert 'total_errors' in summary
        assert 'errors_by_file' in summary
        assert 'errors_by_type' in summary
    
    def test_serena_api_with_realistic_project(self, realistic_python_project):
        """Test SerenaAPI with a realistic project."""
        # Create codebase
        codebase = Codebase(str(realistic_python_project))
        
        # Create API
        api = create_serena_api(codebase, enable_lsp=False)
        
        try:
            # Test basic functionality
            status = api.get_status()
            assert isinstance(status, dict)
            assert 'error_analyzer_initialized' in status
            
            # Test getting all errors
            errors = api.get_all_errors()
            assert isinstance(errors, list)
            
            # Test dependency graph
            dep_graph = api.get_dependency_graph()
            assert isinstance(dep_graph, dict)
            
            # Should have Python files in the graph
            python_files = [f for f in dep_graph.keys() if f.endswith('.py')]
            assert len(python_files) > 0
            
        finally:
            api.shutdown()
    
    def test_parameter_analysis_realistic(self, realistic_python_project):
        """Test parameter analysis with realistic code."""
        codebase = Codebase(str(realistic_python_project))
        api = create_serena_api(codebase, enable_lsp=False)
        
        try:
            # Test unused parameter detection
            unused_params = api.get_unused_parameters()
            assert isinstance(unused_params, list)
            
            # Test wrong parameter detection
            wrong_params = api.get_wrong_parameters()
            assert isinstance(wrong_params, list)
            
        finally:
            api.shutdown()
    
    def test_function_relationship_analysis(self, realistic_python_project):
        """Test function relationship analysis with realistic code."""
        codebase = Codebase(str(realistic_python_project))
        api = create_serena_api(codebase, enable_lsp=False)
        
        try:
            # Test finding function callers
            callers = api.get_function_callers('process_data')
            assert isinstance(callers, list)
            
            # Test symbol usage
            usage = api.find_symbol_usage('DataProcessor')
            assert isinstance(usage, list)
            
            # Test related symbols
            related = api.get_related_symbols('validate_input')
            assert isinstance(related, list)
            
        finally:
            api.shutdown()
    
    def test_file_specific_analysis(self, realistic_python_project):
        """Test file-specific error analysis."""
        codebase = Codebase(str(realistic_python_project))
        
        # Test analyzing specific file
        main_file = "src/myproject/main.py"
        result = analyze_file_errors(codebase, main_file)
        
        assert isinstance(result, dict)
        assert 'file_path' in result
        assert 'errors' in result
        assert 'error_contexts' in result
        assert 'dependencies' in result
        assert result['file_path'] == main_file
    
    def test_convenience_function_integration(self, realistic_python_project):
        """Test convenience functions with realistic project."""
        codebase = Codebase(str(realistic_python_project))
        
        # Test comprehensive analysis
        analysis = get_codebase_error_analysis(codebase)
        
        assert isinstance(analysis, dict)
        assert 'error_summary' in analysis
        assert 'all_errors_with_context' in analysis
        assert 'unused_parameters' in analysis
        assert 'wrong_parameters' in analysis
        assert 'dependency_graph' in analysis
        assert 'status' in analysis
        
        # Verify structure of error summary
        error_summary = analysis['error_summary']
        assert 'total_errors' in error_summary
        assert 'total_warnings' in error_summary
        assert 'errors_by_file' in error_summary
        assert 'errors_by_type' in error_summary
    
    def test_function_relationships_integration(self, realistic_python_project):
        """Test function relationship analysis integration."""
        codebase = Codebase(str(realistic_python_project))
        
        # Test finding relationships for a known function
        relationships = find_function_relationships(codebase, 'process_data')
        
        assert isinstance(relationships, dict)
        assert 'function_name' in relationships
        assert 'callers' in relationships
        assert 'calls' in relationships
        assert 'symbol_usage' in relationships
        assert 'related_symbols' in relationships
        assert relationships['function_name'] == 'process_data'


class TestErrorAnalysisPerformance:
    """Test performance characteristics of error analysis."""
    
    @pytest.fixture
    def large_codebase(self):
        """Create a larger codebase for performance testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create multiple modules with various patterns
            for i in range(10):
                module_content = f'''
"""Module {i} with various patterns."""
import os
import sys
from typing import List, Dict

class Class{i}:
    """Class {i} with methods."""
    
    def __init__(self, param1, unused_param_{i}):
        """Initialize with unused parameter."""
        self.param1 = param1
        # unused_param_{i} not used
    
    def method_{i}(self, data: Dict, options: List, extra1, extra2, extra3):
        """Method with multiple parameters."""
        results = []
        
        # Undefined variable
        if debug_mode_{i}:  # Error: not defined
            print(f"Processing in method {i}")
        
        for item in data.get("items", []):
            results.append(f"{{i}}: {{item}}")
        
        return results
    
    def call_other_methods(self):
        """Call methods from other classes."""
        # This creates cross-references
        if {i} > 0:
            prev_class = Class{i-1}("test", "unused")
            return prev_class.method_{i-1}({{"items": ["test"]}}, [], "a", "b", "c")
        return []

def function_{i}(param1, param2, unused_param):
    """Function {i} with unused parameter."""
    return param1 + param2

def caller_function_{i}():
    """Function that calls other functions."""
    obj = Class{i}("test", "unused_value")
    result1 = obj.method_{i}({{"items": ["a", "b"]}}, [], "x", "y", "z")
    result2 = function_{i}("hello", "world", "unused")
    return result1, result2
'''
                (project_root / f"module_{i}.py").write_text(module_content)
            
            yield project_root
    
    def test_analysis_performance(self, large_codebase):
        """Test that analysis completes in reasonable time."""
        import time
        
        codebase = Codebase(str(large_codebase))
        
        # Time the analysis
        start_time = time.time()
        api = create_serena_api(codebase, enable_lsp=False)
        
        try:
            # Perform various analyses
            status = api.get_status()
            errors = api.get_all_errors()
            unused_params = api.get_unused_parameters()
            dep_graph = api.get_dependency_graph()
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            # Should complete within reasonable time (adjust as needed)
            assert analysis_time < 30.0, f"Analysis took too long: {analysis_time:.2f}s"
            
            # Verify we got results
            assert isinstance(status, dict)
            assert isinstance(errors, list)
            assert isinstance(unused_params, list)
            assert isinstance(dep_graph, dict)
            
        finally:
            api.shutdown()
    
    def test_caching_effectiveness(self, large_codebase):
        """Test that caching improves performance."""
        import time
        
        codebase = Codebase(str(large_codebase))
        analyzer = ComprehensiveErrorAnalyzer(codebase, enable_lsp=False)
        
        # Create a mock error for testing
        from graph_sitter.extensions.lsp.serena_bridge import ErrorInfo
        from graph_sitter.core.diagnostics import DiagnosticSeverity
        
        test_error = ErrorInfo(
            file_path="module_0.py",
            line=10,
            character=5,
            message="Test error for caching",
            severity=DiagnosticSeverity.ERROR,
            source="test",
            code="T001"
        )
        
        # First analysis (should populate cache)
        start_time = time.time()
        context1 = analyzer.analyze_error_context(test_error)
        first_time = time.time() - start_time
        
        # Second analysis (should use cache)
        start_time = time.time()
        context2 = analyzer.analyze_error_context(test_error)
        second_time = time.time() - start_time
        
        # Second call should be faster (cached)
        assert second_time < first_time, "Caching should improve performance"
        assert context1 is context2, "Should return cached object"


class TestErrorAnalysisAccuracy:
    """Test accuracy of error analysis results."""
    
    @pytest.fixture
    def accuracy_test_codebase(self):
        """Create codebase with known, specific issues for accuracy testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # File with exactly 2 unused parameters
            unused_params_file = '''
def function_with_unused_params(used_param, unused1, unused2):
    """Function with exactly 2 unused parameters."""
    return used_param * 2

def caller():
    return function_with_unused_params("test", "not_used1", "not_used2")
'''
            
            # File with exactly 3 undefined variables
            undefined_vars_file = '''
def function_with_undefined_vars():
    """Function with exactly 3 undefined variables."""
    result1 = undefined_var_1  # Error 1
    result2 = undefined_var_2  # Error 2
    result3 = undefined_var_3  # Error 3
    return result1 + result2 + result3
'''
            
            # File with exactly 2 import errors
            import_errors_file = '''
import os  # Valid import
import sys  # Valid import
import nonexistent_module1  # Error 1
import nonexistent_module2  # Error 2
from nonexistent_package import something  # Error 3 (but different type)

def use_imports():
    return os.path.exists("/tmp") and len(sys.argv) > 0
'''
            
            (project_root / "unused_params.py").write_text(unused_params_file)
            (project_root / "undefined_vars.py").write_text(undefined_vars_file)
            (project_root / "import_errors.py").write_text(import_errors_file)
            
            yield project_root
    
    def test_unused_parameter_detection_accuracy(self, accuracy_test_codebase):
        """Test accuracy of unused parameter detection."""
        codebase = Codebase(str(accuracy_test_codebase))
        analyzer = ComprehensiveErrorAnalyzer(codebase, enable_lsp=False)
        
        # Test parameter analysis for the file with known unused parameters
        param_issues = analyzer._analyze_parameters_via_ast("unused_params.py", 2)
        
        # Should detect exactly the unused parameters
        unused_issues = [issue for issue in param_issues if issue.get('issue_type') == 'unused']
        
        # We expect to find the unused parameters
        assert len(unused_issues) >= 1, "Should detect unused parameters"
        
        # Check parameter names
        param_names = [issue.get('parameter_name') for issue in unused_issues]
        expected_unused = ['unused1', 'unused2']
        
        # At least one of the expected unused parameters should be detected
        assert any(param in param_names for param in expected_unused), \
            f"Should detect unused parameters from {expected_unused}, got {param_names}"
    
    def test_function_call_detection_accuracy(self, accuracy_test_codebase):
        """Test accuracy of function call detection."""
        codebase = Codebase(str(accuracy_test_codebase))
        analyzer = ComprehensiveErrorAnalyzer(codebase, enable_lsp=False)
        
        # Test finding callers of function_with_unused_params
        callers = analyzer._find_callers_via_ast("unused_params.py", 2)
        
        # Should find the caller function
        assert len(callers) >= 1, "Should find function callers"
        
        # Check that we found the expected caller
        caller_names = [caller.get('function_name') for caller in callers]
        assert 'caller' in caller_names, f"Should find 'caller' function, got {caller_names}"
    
    def test_dependency_detection_accuracy(self, accuracy_test_codebase):
        """Test accuracy of dependency detection."""
        codebase = Codebase(str(accuracy_test_codebase))
        analyzer = ComprehensiveErrorAnalyzer(codebase, enable_lsp=False)
        
        # Test dependency detection for import_errors.py
        deps = analyzer._build_dependency_chain("import_errors.py")
        
        # Should detect the valid imports
        assert len(deps) >= 2, "Should detect dependencies"
        assert 'os' in deps, "Should detect 'os' import"
        assert 'sys' in deps, "Should detect 'sys' import"
    
    def test_code_context_accuracy(self, accuracy_test_codebase):
        """Test accuracy of code context extraction."""
        codebase = Codebase(str(accuracy_test_codebase))
        analyzer = ComprehensiveErrorAnalyzer(codebase, enable_lsp=False)
        
        # Test code context for line 4 in undefined_vars.py
        context = analyzer._get_code_context("undefined_vars.py", 4)
        
        assert context is not None, "Should extract code context"
        assert "undefined_var_1" in context, "Should include the error line content"
        assert ">>>" in context, "Should highlight the error line"
        
        # Should include surrounding lines
        lines = context.split('\n')
        assert len(lines) >= 5, "Should include context lines around error"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
