from unittest.mock import MagicMock, patch

import pytest

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.cli.api.schemas import CodemodRunType
from graph_sitter.cli.utils.function_finder import DecoratedFunction


@pytest.fixture
def api_client():
    """Create a RestAPI client with a mock auth token."""
    return RestAPI(auth_token="mock_token")


@pytest.fixture
def mock_session_config():
    """Mock the CliSession configuration."""
    with patch("graph_sitter.cli.api.client.CliSession") as mock_session:
        mock_session.from_active_session.return_value.config.repository.full_name = "test/repo"
        yield mock_session


@pytest.fixture
def mock_function():
    """Create a mock DecoratedFunction."""
    mock = MagicMock(spec=DecoratedFunction)
    mock.name = "test_function"
    mock.source = "def test_function():\n    pass"
    return mock


class TestDecoratedFunctionIntegration:
    """Test integration with the DecoratedFunction class."""

    def test_run_with_function(self, api_client, mock_session_config, mock_function):
        """Test run with a DecoratedFunction."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the function
            api_client.run(mock_function)
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the function name and source
            assert input_data.input.codemod_name == "test_function"
            assert "def test_function():" in input_data.input.codemod_source

    def test_run_with_function_without_source(self, api_client, mock_session_config, mock_function):
        """Test run with a DecoratedFunction without including source."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the function without source
            api_client.run(mock_function, include_source=False)
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the function name but not the source
            assert input_data.input.codemod_name == "test_function"
            assert not hasattr(input_data.input, "codemod_source") or input_data.input.codemod_source is None

    def test_run_with_function_and_template_context(self, api_client, mock_session_config, mock_function):
        """Test run with a DecoratedFunction and template context."""
        # Template context
        template_context = {"key1": "value1", "key2": "value2"}
        
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the function with template context
            api_client.run(mock_function, template_context=template_context)
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the template context
            assert input_data.input.template_context == template_context

    def test_run_with_function_and_run_type(self, api_client, mock_session_config, mock_function):
        """Test run with a DecoratedFunction and run type."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the function with PR run type
            api_client.run(mock_function, run_type=CodemodRunType.PR)
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the run type
            assert input_data.input.codemod_run_type == CodemodRunType.PR

