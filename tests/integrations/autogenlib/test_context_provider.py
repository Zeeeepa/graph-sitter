"""Tests for GraphSitterContextProvider."""

import pytest
import ast
from unittest.mock import Mock, patch
from graph_sitter.integrations.autogenlib import (
    GraphSitterContextProvider,
    AutogenLibConfig
)


class TestGraphSitterContextProvider:
    """Test cases for GraphSitterContextProvider."""
    
    def test_init_without_codebase(self):
        """Test initialization without codebase."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        assert provider.config == config
        assert provider.codebase is None
        
    def test_init_with_codebase(self):
        """Test initialization with codebase."""
        config = AutogenLibConfig()
        mock_codebase = Mock()
        provider = GraphSitterContextProvider(config, mock_codebase)
        
        assert provider.config == config
        assert provider.codebase == mock_codebase
        
    def test_get_enhanced_context_basic(self):
        """Test getting enhanced context with basic parameters."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        context = provider.get_enhanced_context(
            module_name="test.module",
            function_name="test_function"
        )
        
        assert context["module_name"] == "test.module"
        assert context["function_name"] == "test_function"
        assert "graph_sitter_analysis" in context
        assert "symbol_information" in context
        assert "dependencies" in context
        assert "patterns" in context
        assert "caller_analysis" in context
        
    def test_analyze_caller_code_simple(self):
        """Test analyzing simple caller code."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        caller_info = {
            "filename": "test.py",
            "code": """
import os
from typing import Optional

def main():
    result = test_function("hello")
    print(result)
"""
        }
        
        analysis = provider._analyze_caller_code(caller_info)
        
        assert analysis["filename"] == "test.py"
        assert len(analysis["imports"]) == 2
        assert any(imp["module"] == "os" for imp in analysis["imports"])
        assert any(imp["module"] == "typing" for imp in analysis["imports"])
        assert len(analysis["function_calls"]) >= 1
        assert any(call["function"] == "test_function" for call in analysis["function_calls"])
        
    def test_analyze_caller_code_with_syntax_error(self):
        """Test analyzing caller code with syntax error."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        caller_info = {
            "filename": "test.py",
            "code": "def invalid_syntax( # missing closing parenthesis"
        }
        
        analysis = provider._analyze_caller_code(caller_info)
        
        assert "parse_error" in analysis
        assert analysis["filename"] == "test.py"
        
    def test_analyze_existing_code_functions_and_classes(self):
        """Test analyzing existing code with functions and classes."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        code = '''
"""Module docstring."""

import json
from typing import List

CONSTANT_VALUE = 42

class TestClass:
    """Test class."""
    
    def __init__(self, value: int):
        self.value = value
        
    def get_value(self) -> int:
        """Get the value."""
        return self.value

def helper_function(data: List[str]) -> dict:
    """Helper function."""
    return {"count": len(data)}
'''
        
        analysis = provider._analyze_existing_code(code)
        
        assert len(analysis["functions"]) == 2  # __init__ and helper_function
        assert len(analysis["classes"]) == 1
        assert analysis["classes"][0]["name"] == "TestClass"
        assert len(analysis["constants"]) == 1
        assert analysis["constants"][0]["name"] == "CONSTANT_VALUE"
        assert analysis["complexity"] > 0
        
    def test_analyze_existing_code_with_syntax_error(self):
        """Test analyzing existing code with syntax error."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        code = "def invalid_syntax( # missing closing parenthesis"
        
        analysis = provider._analyze_existing_code(code)
        
        assert "parse_error" in analysis
        
    def test_get_codebase_analysis_without_codebase(self):
        """Test getting codebase analysis without codebase."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        analysis = provider._get_codebase_analysis("test.module")
        
        assert analysis == {}
        
    def test_get_codebase_analysis_with_codebase(self):
        """Test getting codebase analysis with mock codebase."""
        config = AutogenLibConfig(use_graph_sitter_context=True)
        mock_codebase = Mock()
        
        # Mock modules
        mock_module = Mock()
        mock_module.name = "test.utils"
        mock_module.path = "/path/to/test/utils.py"
        mock_module.symbols = [Mock(), Mock()]  # 2 symbols
        
        mock_codebase.get_modules.return_value = [mock_module]
        
        provider = GraphSitterContextProvider(config, mock_codebase)
        
        analysis = provider._get_codebase_analysis("utils")
        
        assert "related_modules" in analysis
        assert len(analysis["related_modules"]) == 1
        assert analysis["related_modules"][0]["name"] == "test.utils"
        assert analysis["related_modules"][0]["symbols"] == 2
        
    def test_get_symbol_information_without_codebase(self):
        """Test getting symbol information without codebase."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        symbols = provider._get_symbol_information("test.module", "test_function")
        
        assert symbols == {}
        
    def test_get_symbol_information_with_codebase(self):
        """Test getting symbol information with mock codebase."""
        config = AutogenLibConfig()
        mock_codebase = Mock()
        
        # Mock symbols
        mock_symbol1 = Mock()
        mock_symbol1.name = "test_function"
        mock_symbol1.type = "function"
        mock_symbol1.module = "test.module"
        mock_symbol1.signature = "test_function(arg1: str) -> str"
        
        mock_symbol2 = Mock()
        mock_symbol2.name = "other_function"
        mock_symbol2.type = "function"
        
        mock_codebase.get_symbols.return_value = [mock_symbol1, mock_symbol2]
        
        provider = GraphSitterContextProvider(config, mock_codebase)
        
        symbols = provider._get_symbol_information("test.module", "test_function")
        
        assert "similar_functions" in symbols
        assert "available_symbols" in symbols
        assert len(symbols["similar_functions"]) == 1
        assert symbols["similar_functions"][0]["name"] == "test_function"
        assert len(symbols["available_symbols"]) == 2
        
    def test_get_pattern_suggestions_function_patterns(self):
        """Test getting pattern suggestions for different function types."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        # Test getter pattern
        patterns = provider._get_pattern_suggestions("test.module", "get_value")
        assert "getter_pattern" in patterns["common_patterns"]
        
        # Test setter pattern
        patterns = provider._get_pattern_suggestions("test.module", "set_value")
        assert "setter_pattern" in patterns["common_patterns"]
        
        # Test predicate pattern
        patterns = provider._get_pattern_suggestions("test.module", "is_valid")
        assert "predicate_pattern" in patterns["common_patterns"]
        
        # Test factory pattern
        patterns = provider._get_pattern_suggestions("test.module", "create_instance")
        assert "factory_pattern" in patterns["common_patterns"]
        
    def test_get_pattern_suggestions_module_patterns(self):
        """Test getting pattern suggestions for different module types."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        # Test utility module
        patterns = provider._get_pattern_suggestions("test.utils", None)
        assert "utility_module" in patterns["common_patterns"]
        
        # Test config module
        patterns = provider._get_pattern_suggestions("test.config", None)
        assert "configuration_module" in patterns["common_patterns"]
        
        # Test client module
        patterns = provider._get_pattern_suggestions("test.client", None)
        assert "client_module" in patterns["common_patterns"]
        
    def test_format_context_for_autogenlib_empty(self):
        """Test formatting empty context for autogenlib."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        context = {}
        formatted = provider.format_context_for_autogenlib(context)
        
        assert formatted == ""
        
    def test_format_context_for_autogenlib_full(self):
        """Test formatting full context for autogenlib."""
        config = AutogenLibConfig()
        provider = GraphSitterContextProvider(config)
        
        context = {
            "graph_sitter_analysis": {
                "related_modules": [
                    {"name": "test.utils", "symbols": 5},
                    {"name": "test.helpers", "symbols": 3}
                ]
            },
            "symbol_information": {
                "similar_functions": [
                    {"name": "similar_func", "type": "function", "signature": "similar_func() -> str"}
                ]
            },
            "caller_analysis": {
                "function_calls": [
                    {"function": "test_func", "args": 2, "kwargs": 1}
                ]
            },
            "patterns": {
                "common_patterns": ["getter_pattern", "utility_module"]
            }
        }
        
        formatted = provider.format_context_for_autogenlib(context)
        
        assert "## Graph-Sitter Analysis" in formatted
        assert "### Related Modules:" in formatted
        assert "test.utils: 5 symbols" in formatted
        assert "### Similar Functions:" in formatted
        assert "similar_func (function)" in formatted
        assert "### Function Usage Patterns:" in formatted
        assert "test_func(2 args, 1 kwargs)" in formatted
        assert "### Detected Patterns:" in formatted
        assert "getter_pattern" in formatted
        assert "utility_module" in formatted

