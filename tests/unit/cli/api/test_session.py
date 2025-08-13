from unittest.mock import MagicMock, patch

import pytest
import requests

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.cli.api.schemas import RunCodemodOutput


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


class TestSession:
    """Test session management in the RestAPI client."""

    def test_session_reuse(self, api_client, mock_response):
        """Test that the same session is reused for multiple requests."""
        # Mock the session's request method
        with patch.object(requests.Session, "request", return_value=mock_response) as mock_request:
            # Make multiple requests
            api_client._make_request(
                "GET",
                "https://example.com/api/1",
                None,
                RunCodemodOutput,
            )
            api_client._make_request(
                "GET",
                "https://example.com/api/2",
                None,
                RunCodemodOutput,
            )
            
            # Verify that the session's request method was called twice
            assert mock_request.call_count == 2
            
            # Verify that the same session was used for both requests
            first_call_self = mock_request.call_args_list[0][0][0]
            second_call_self = mock_request.call_args_list[1][0][0]
            assert first_call_self is second_call_self

    def test_session_class_variable(self):
        """Test that the session is a class variable."""
        # Create two API clients
        client1 = RestAPI(auth_token="token1")
        client2 = RestAPI(auth_token="token2")
        
        # Verify that they share the same session object
        assert client1._session is client2._session

    def test_session_request_method(self, api_client, mock_response):
        """Test that the session's request method is called with the correct arguments."""
        # Mock the session's request method
        with patch.object(requests.Session, "request", return_value=mock_response) as mock_request:
            # Make a request
            api_client._make_request(
                "GET",
                "https://example.com/api",
                None,
                RunCodemodOutput,
            )
            
            # Verify that the session's request method was called with the correct arguments
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            assert call_args["method"] == "GET"
            assert call_args["url"] == "https://example.com/api"
            assert call_args["json"] is None
            assert call_args["headers"] == {"Authorization": "Bearer mock_token"}

