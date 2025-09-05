import json
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


class TestRichIntegration:
    """Test integration with the rich module."""

    def test_rich_print_debug_mode(self, api_client, mock_response):
        """Test that rich.print is used in debug mode."""
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
                    
                    # Verify that rich.print was called
                    mock_rprint.assert_called()
                    
                    # Verify the first call prints the method and endpoint
                    first_call_args = mock_rprint.call_args_list[0][0][0]
                    assert "[purple]GET[/purple]" in first_call_args
                    assert "https://example.com/api" in first_call_args
        finally:
            # Restore original debug setting
            global_env.DEBUG = original_debug

    def test_rich_print_debug_mode_with_input(self, api_client, mock_response):
        """Test that rich.print is used in debug mode with input data."""
        # Enable debug mode
        original_debug = global_env.DEBUG
        global_env.DEBUG = True
        
        try:
            # Create a mock input
            mock_input = MagicMock()
            mock_input.model_dump.return_value = {"key": "value"}
            
            # Mock the session to return a predefined response
            with patch.object(api_client._session, "request", return_value=mock_response):
                # Mock rich.print to capture output
                with patch("graph_sitter.cli.api.client.rprint") as mock_rprint:
                    # Make a request with input data
                    api_client._make_request(
                        "POST",
                        "https://example.com/api",
                        mock_input,
                        RunCodemodOutput,
                    )
                    
                    # Verify that rich.print was called
                    assert mock_rprint.call_count >= 2
                    
                    # Verify the first call prints the method and endpoint
                    first_call_args = mock_rprint.call_args_list[0][0][0]
                    assert "[purple]POST[/purple]" in first_call_args
                    assert "https://example.com/api" in first_call_args
                    
                    # Verify the second call prints the input data
                    second_call_args = mock_rprint.call_args_list[1][0][0]
                    assert json.dumps({"key": "value"}, indent=4) == second_call_args
        finally:
            # Restore original debug setting
            global_env.DEBUG = original_debug

    def test_rich_print_not_used_in_normal_mode(self, api_client, mock_response):
        """Test that rich.print is not used in normal mode."""
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
                    
                    # Verify that rich.print was not called
                    mock_rprint.assert_not_called()
        finally:
            # Restore original debug setting
            global_env.DEBUG = original_debug

