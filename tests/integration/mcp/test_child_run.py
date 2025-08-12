#!/usr/bin/env python3
"""
Test for MCP server child run functionality.

This test verifies that the MCP server can properly create and manage child runs
when using tools like ask_codegen_sdk and query_codebase.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from graph_sitter.core.codebase import Codebase
from graph_sitter.cli.mcp.server import ask_codegen_sdk
from graph_sitter.extensions.mcp.codebase_agent import query_codebase
from graph_sitter.extensions.langchain.agent import create_codebase_inspector_agent
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


class TestMCPServerChildRun:
    """Test MCP server child run functionality."""
    
    @pytest.fixture
    def sample_codebase(self):
        """Create a sample codebase for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python file
            content = """
def hello_world():
    """A simple hello world function."""
    return "Hello, World!"

def add(a, b):
    """Add two numbers."""
    return a + b
"""
            Path(temp_dir, "main.py").write_text(content)
            codebase = Codebase(temp_dir)
            yield codebase
    
    @patch('graph_sitter.cli.mcp.agent.docs_expert.create_codebase_agent')
    def test_ask_codegen_sdk_child_run(self, mock_create_agent):
        """Test that ask_codegen_sdk creates a child run."""
        # Mock the agent and its invoke method
        mock_agent = Mock()
        mock_agent.invoke.return_value = {
            "messages": [
                MagicMock(content="This is a response from the child run.")
            ]
        }
        mock_create_agent.return_value = mock_agent
        
        # Call the function
        result = ask_codegen_sdk("What is the Codegen SDK?")
        
        # Verify that the agent was created and invoked
        mock_create_agent.assert_called_once()
        mock_agent.invoke.assert_called_once()
        
        # Verify that invoke was called with the correct parameters
        args, kwargs = mock_agent.invoke.call_args
        assert args[0]["input"] == "What is the Codegen SDK?"
        assert kwargs["config"]["configurable"]["thread_id"] == 1
        
        # Verify the result
        assert result == "This is a response from the child run."
    
    @patch('graph_sitter.extensions.mcp.codebase_agent.create_codebase_inspector_agent')
    def test_query_codebase_child_run(self, mock_create_agent, sample_codebase):
        """Test that query_codebase creates a child run."""
        # Mock the agent and its invoke method
        mock_agent = Mock()
        mock_agent.invoke.return_value = {
            "messages": [
                MagicMock(content="This is a response from the child run.")
            ]
        }
        mock_create_agent.return_value = mock_agent
        
        # Call the function
        result = query_codebase(
            query="What functions are in main.py?",
            codebase_dir=str(sample_codebase.repo_path),
            codebase_language=ProgrammingLanguage.PYTHON
        )
        
        # Verify that the agent was created and invoked
        mock_create_agent.assert_called_once()
        mock_agent.invoke.assert_called_once()
        
        # Verify that invoke was called with the correct parameters
        args, kwargs = mock_agent.invoke.call_args
        assert args[0]["input"] == "What functions are in main.py?"
        assert kwargs["config"]["configurable"]["thread_id"] == 1
        
        # Verify the result
        assert result == "This is a response from the child run."
    
    @patch('graph_sitter.extensions.langchain.agent.LLM')
    @patch('graph_sitter.extensions.langchain.graph.create_react_agent')
    def test_create_codebase_inspector_agent(self, mock_create_react_agent, mock_llm, sample_codebase):
        """Test that create_codebase_inspector_agent creates an agent with the correct configuration."""
        # Mock the LLM and create_react_agent
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        mock_agent = Mock()
        mock_create_react_agent.return_value = mock_agent
        
        # Call the function
        agent = create_codebase_inspector_agent(
            codebase=sample_codebase,
            model_provider="openai",
            model_name="gpt-4o"
        )
        
        # Verify that LLM was created with the correct parameters
        mock_llm.assert_called_once_with(model_provider="openai", model_name="gpt-4o")
        
        # Verify that create_react_agent was called
        mock_create_react_agent.assert_called_once()
        
        # Verify that the agent was returned
        assert agent == mock_agent


if __name__ == "__main__":
    pytest.main(["-v", __file__])

