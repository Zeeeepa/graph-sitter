#!/usr/bin/env python3
"""
Pytest Configuration and Fixtures for Graph-Sitter Tests

This file provides common fixtures and configuration for all test suites,
including setup for the unified error interface testing.
"""

import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Add the src directory to the path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test markers
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_python_files():
    """Provide sample Python files with various types of errors."""
    return {
        "syntax_error.py": '''
def broken_function(
    print("Missing closing parenthesis")
    return "syntax error"
''',
        "import_error.py": '''
import nonexistent_module
from another_fake_module import something

def test_function():
    return something
''',
        "type_error.py": '''
def add_numbers(a: int, b: int) -> int:
    return a + b

# Type error: passing string to int function
result = add_numbers("hello", 42)
''',
        "undefined_variable.py": '''
def use_undefined():
    print(undefined_variable)  # NameError
    return some_other_undefined_var
''',
        "valid_file.py": '''
"""A valid Python file with no errors."""

def hello_world():
    """Print hello world."""
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
''',
        "complex_errors.py": '''
import os
import sys
from typing import List, Dict

class TestClass:
    def __init__(self):
        self.value = undefined_var  # NameError
    
    def method_with_issues(self, param):
        # Multiple issues in one method
        result = param + "string"  # Potential type error
        return result.nonexistent_method()  # AttributeError
    
    def unused_method(self):
        """This method is never called."""
        pass

def function_with_many_params(a, b, c, d, e, f, g, h, i, j):
    """Function with too many parameters."""
    return a + b + c + d + e + f + g + h + i + j

# Missing docstring
def no_docstring():
    pass
'''
    }


@pytest.fixture
def temp_project_with_errors(temp_dir, sample_python_files):
    """Create a temporary project directory with test files containing errors."""
    project_dir = Path(temp_dir)
    
    for filename, content in sample_python_files.items():
        (project_dir / filename).write_text(content)
    
    return str(project_dir)


@pytest.fixture
def mock_lsp_diagnostics():
    """Provide mock LSP diagnostic responses."""
    return [
        {
            'file_path': 'test.py',
            'line': 10,
            'character': 5,
            'message': 'Undefined variable: test_var',
            'severity': 'error',
            'source': 'pylsp',
            'code': 'undefined-variable',
            'has_fix': True,
            'range': {
                'start': {'line': 9, 'character': 5},
                'end': {'line': 9, 'character': 13}
            }
        },
        {
            'file_path': 'test.py',
            'line': 15,
            'character': 0,
            'message': 'Missing import: os',
            'severity': 'warning',
            'source': 'pylsp',
            'code': 'missing-import',
            'has_fix': True,
            'range': {
                'start': {'line': 14, 'character': 0},
                'end': {'line': 14, 'character': 10}
            }
        },
        {
            'file_path': 'another.py',
            'line': 5,
            'character': 10,
            'message': 'Line too long (85 > 79 characters)',
            'severity': 'info',
            'source': 'flake8',
            'code': 'E501',
            'has_fix': False,
            'range': {
                'start': {'line': 4, 'character': 0},
                'end': {'line': 4, 'character': 85}
            }
        },
        {
            'file_path': 'type_issues.py',
            'line': 20,
            'character': 15,
            'message': 'Argument of type "str" cannot be assigned to parameter of type "int"',
            'severity': 'error',
            'source': 'mypy',
            'code': 'assignment',
            'has_fix': False,
            'range': {
                'start': {'line': 19, 'character': 15},
                'end': {'line': 19, 'character': 22}
            }
        }
    ]


@pytest.fixture
def mock_error_context():
    """Provide mock error context data."""
    return {
        'surrounding_code': '''
def test_function():
    print("Before error")
    undefined_variable = some_var  # Error line
    print("After error")
''',
        'function_context': 'test_function',
        'class_context': None,
        'imports': ['os', 'sys', 'typing'],
        'related_symbols': ['some_var', 'test_function'],
        'file_info': {
            'total_lines': 50,
            'functions': 5,
            'classes': 2,
            'complexity_score': 3.2
        }
    }


@pytest.fixture
def mock_codebase():
    """Create a mock codebase for testing."""
    mock_codebase = Mock()
    mock_codebase.repo_path = "/tmp/test_repo"
    mock_codebase.files = []
    
    # Mock file objects
    mock_file1 = Mock()
    mock_file1.file_path = "test1.py"
    mock_file1.functions = []
    mock_file1.classes = []
    mock_file1.imports = []
    
    mock_file2 = Mock()
    mock_file2.file_path = "test2.py"
    mock_file2.functions = []
    mock_file2.classes = []
    mock_file2.imports = []
    
    mock_codebase.files = [mock_file1, mock_file2]
    mock_codebase.get_file = Mock(return_value=mock_file1)
    
    return mock_codebase


@pytest.fixture
def mock_lsp_integration():
    """Create a mock LSP integration for testing."""
    mock_integration = Mock()
    mock_integration.get_all_diagnostics = Mock(return_value=[])
    mock_integration.get_file_diagnostics = Mock(return_value={'success': True, 'diagnostics': []})
    mock_integration.get_code_actions = Mock(return_value=[])
    mock_integration.apply_code_action = Mock(return_value={'success': True})
    return mock_integration


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure clean state
    import gc
    gc.collect()
    
    yield
    
    # Cleanup after test
    gc.collect()


class TestDataGenerator:
    """Helper class for generating test data."""
    
    @staticmethod
    def create_python_file_with_errors(error_types: List[str]) -> str:
        """Create Python file content with specific error types."""
        content_parts = [
            '"""Test file with various errors."""',
            '',
            'import os',
            'import sys',
            ''
        ]
        
        if 'undefined_variable' in error_types:
            content_parts.extend([
                'def function_with_undefined_var():',
                '    return undefined_variable  # NameError',
                ''
            ])
        
        if 'import_error' in error_types:
            content_parts.extend([
                'from nonexistent_module import something',
                ''
            ])
        
        if 'type_error' in error_types:
            content_parts.extend([
                'def type_error_function():',
                '    return "string" + 42  # TypeError',
                ''
            ])
        
        if 'syntax_error' in error_types:
            content_parts.extend([
                'def syntax_error_function():',
                '    if True',  # Missing colon
                '        return "syntax error"',
                ''
            ])
        
        if 'attribute_error' in error_types:
            content_parts.extend([
                'def attribute_error_function():',
                '    return "string".nonexistent_method()  # AttributeError',
                ''
            ])
        
        return '\n'.join(content_parts)
    
    @staticmethod
    def create_large_file_content(num_functions: int, errors_per_function: int) -> str:
        """Create large Python file with many functions and errors."""
        content_parts = [
            '"""Large test file for performance testing."""',
            '',
            'import os',
            'import sys',
            'from typing import List, Dict, Any',
            ''
        ]
        
        for i in range(num_functions):
            content_parts.extend([
                f'def function_{i}():',
                f'    """Function {i} with {errors_per_function} errors."""'
            ])
            
            for j in range(errors_per_function):
                content_parts.append(f'    undefined_var_{i}_{j} = some_undefined_variable_{j}  # NameError')
            
            content_parts.extend([
                f'    return "function_{i}_result"',
                ''
            ])
        
        return '\n'.join(content_parts)


@pytest.fixture
def test_data_generator():
    """Provide TestDataGenerator instance."""
    return TestDataGenerator()


# Skip tests if required dependencies are not available
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle missing dependencies."""
    try:
        import graph_sitter
        graph_sitter_available = True
    except ImportError:
        graph_sitter_available = False
    
    if not graph_sitter_available:
        skip_graph_sitter = pytest.mark.skip(reason="graph-sitter not available")
        for item in items:
            if "graph_sitter" in str(item.fspath):
                item.add_marker(skip_graph_sitter)
    
    # Skip performance tests by default unless explicitly requested
    if not config.getoption("-m"):
        skip_performance = pytest.mark.skip(reason="performance tests skipped by default")
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_performance)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--run-performance",
        action="store_true", 
        default=False,
        help="run performance tests"
    )


def pytest_runtest_setup(item):
    """Setup for individual test runs."""
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("need --run-slow option to run")
    
    if "performance" in item.keywords and not item.config.getoption("--run-performance"):
        pytest.skip("need --run-performance option to run")

