from unittest.mock import MagicMock, patch

import pytest

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.cli.api.schemas import CodemodRunType
from graph_sitter.cli.utils.codemods import Codemod


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
def mock_codemod():
    """Create a mock Codemod."""
    mock = MagicMock(spec=Codemod)
    mock.name = "test_codemod"
    mock.get_current_source.return_value = "def test_codemod():\n    pass"
    return mock


class TestCodemodIntegration:
    """Test integration with the Codemod class."""

    def test_run_with_codemod(self, api_client, mock_session_config, mock_codemod):
        """Test run with a Codemod."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the codemod
            api_client.run(mock_codemod)
            
            # Verify that get_current_source was called
            mock_codemod.get_current_source.assert_called_once()
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the codemod name and source
            assert input_data.input.codemod_name == "test_codemod"
            assert "def test_codemod():" in input_data.input.codemod_source

    def test_run_with_codemod_without_source(self, api_client, mock_session_config, mock_codemod):
        """Test run with a Codemod without including source."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the codemod without source
            api_client.run(mock_codemod, include_source=False)
            
            # Verify that get_current_source was not called
            mock_codemod.get_current_source.assert_not_called()
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the codemod name but not the source
            assert input_data.input.codemod_name == "test_codemod"
            assert not hasattr(input_data.input, "codemod_source") or input_data.input.codemod_source is None

    def test_run_with_codemod_and_template_context(self, api_client, mock_session_config, mock_codemod):
        """Test run with a Codemod and template context."""
        # Template context
        template_context = {"key1": "value1", "key2": "value2"}
        
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the codemod with template context
            api_client.run(mock_codemod, template_context=template_context)
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the template context
            assert input_data.input.template_context == template_context

    def test_run_with_codemod_and_run_type(self, api_client, mock_session_config, mock_codemod):
        """Test run with a Codemod and run type."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the codemod with PR run type
            api_client.run(mock_codemod, run_type=CodemodRunType.PR)
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the run type
            assert input_data.input.codemod_run_type == CodemodRunType.PR

