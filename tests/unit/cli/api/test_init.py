import pytest
import requests

from graph_sitter.cli.api.client import RestAPI


class TestInit:
    """Test initialization of the RestAPI client."""

    def test_init_with_token(self):
        """Test initialization with a token."""
        # Create a client with a token
        client = RestAPI(auth_token="test_token")
        
        # Verify the token was stored
        assert client.auth_token == "test_token"

    def test_init_with_empty_token(self):
        """Test initialization with an empty token."""
        # Create a client with an empty token
        client = RestAPI(auth_token="")
        
        # Verify the token was stored
        assert client.auth_token == ""

    def test_init_with_none_token(self):
        """Test initialization with a None token."""
        # Create a client with a None token
        client = RestAPI(auth_token=None)
        
        # Verify the token was stored
        assert client.auth_token is None

    def test_session_initialization(self):
        """Test that the session is initialized."""
        # Create a client
        client = RestAPI(auth_token="test_token")
        
        # Verify the session was initialized
        assert client._session is not None
        assert isinstance(client._session, requests.Session)

    def test_multiple_clients_share_session(self):
        """Test that multiple clients share the same session."""
        # Create multiple clients
        client1 = RestAPI(auth_token="token1")
        client2 = RestAPI(auth_token="token2")
        
        # Verify they share the same session
        assert client1._session is client2._session

