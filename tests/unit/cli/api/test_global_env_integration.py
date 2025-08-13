from unittest.mock import MagicMock, patch

import pytest

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.cli.api.schemas import RunCodemodOutput
from graph_sitter.cli.env.global_env import global_env


@pytest.fixture
def api_client():
    """Create a RestAPI client with a mock auth token."""
    return RestAPI(auth_token="mock_token")


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"success": True}
    return mock


class TestGlobalEnvIntegration:
    """Test integration with the global_env module."""

    def test_debug_mode_enabled(self, api_client, mock_response):
        """Test that debug mode prints request details."""
        # Enable debug mode
        original_debug = global_env.DEBUG
        global_env.DEBUG = True
        
        try:
            # Mock the session to return a predefined response
            with patch.object(api_client._session, "request", return_value=mock_response):
                # Mock rich.print to capture output
                with patch("graph_sitter.cli.api.client.rprint") as mock_rprint:
                    # Make a request
                    api_client._make_request(
                        "GET",
                        "https://example.com/api",
                        None,
                        RunCodemodOutput,
                    )
                    
                    # Verify that debug information was printed
                    mock_rprint.assert_called()
                    
                    # Verify the first call prints the method and endpoint
                    first_call_args = mock_rprint.call_args_list[0][0][0]
                    assert "[purple]GET[/purple]" in first_call_args
                    assert "https://example.com/api" in first_call_args
        finally:
            # Restore original debug setting
            global_env.DEBUG = original_debug

    def test_debug_mode_disabled(self, api_client, mock_response):
        """Test that debug mode does not print request details when disabled."""
        # Disable debug mode
        original_debug = global_env.DEBUG
        global_env.DEBUG = False
        
        try:
            # Mock the session to return a predefined response
            with patch.object(api_client._session, "request", return_value=mock_response):
                # Mock rich.print to capture output
                with patch("graph_sitter.cli.api.client.rprint") as mock_rprint:
                    # Make a request
                    api_client._make_request(
                        "GET",
                        "https://example.com/api",
                        None,
                        RunCodemodOutput,
                    )
                    
                    # Verify that debug information was not printed
                    mock_rprint.assert_not_called()
        finally:
            # Restore original debug setting
            global_env.DEBUG = original_debug

    def test_global_env_access(self):
        """Test access to the global_env module."""
        # Verify that the global_env module is accessible
        assert hasattr(global_env, "DEBUG")
        
        # Verify that the DEBUG attribute is a boolean
        assert isinstance(global_env.DEBUG, bool)

