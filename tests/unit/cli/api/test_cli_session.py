from unittest.mock import MagicMock, patch

import pytest

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.cli.auth.session import CliSession


@pytest.fixture
def api_client():
    """Create a RestAPI client with a mock auth token."""
    return RestAPI(auth_token="mock_token")


@pytest.fixture
def mock_session_config():
    """Mock the CliSession configuration."""
    with patch("graph_sitter.cli.api.client.CliSession") as mock_session:
        mock_session.from_active_session.return_value.config.repository.full_name = "test/repo"
        mock_session.from_active_session.return_value.config.repository.language = "python"
        yield mock_session


class TestCliSession:
    """Test CLI session integration in the RestAPI client."""

    def test_run_uses_cli_session(self, api_client, mock_session_config):
        """Test that the run method uses the CLI session."""
        # Create a mock codemod
        mock_codemod = MagicMock()
        mock_codemod.name = "test_codemod"
        mock_codemod.get_current_source.return_value = "def test_codemod():\n    pass"
        
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the codemod
            api_client.run(mock_codemod)
            
            # Verify that CliSession.from_active_session was called
            mock_session_config.from_active_session.assert_called_once()
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the repository full name from the CLI session
            assert input_data.input.repo_full_name == "test/repo"

    def test_get_docs_uses_cli_session(self, api_client, mock_session_config):
        """Test that the get_docs method uses the CLI session."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Get docs
            api_client.get_docs()
            
            # Verify that CliSession.from_active_session was called
            mock_session_config.from_active_session.assert_called_once()
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the repository full name from the CLI session
            assert input_data.docs_input.repo_full_name == "test/repo"

    def test_create_uses_cli_session(self, api_client, mock_session_config):
        """Test that the create method uses the CLI session."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Create codemod
            api_client.create("example_codemod", "Create a codemod that does X")
            
            # Verify that CliSession.from_active_session was called
            mock_session_config.from_active_session.assert_called_once()
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the language from the CLI session
            assert input_data.input.language == "python"

    def test_deploy_uses_cli_session(self, api_client, mock_session_config):
        """Test that the deploy method uses the CLI session."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Deploy codemod
            api_client.deploy(
                codemod_name="example_codemod",
                codemod_source="def example_codemod():\n    pass",
            )
            
            # Verify that CliSession.from_active_session was called
            mock_session_config.from_active_session.assert_called_once()
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the repository full name from the CLI session
            assert input_data.input.repo_full_name == "test/repo"

    def test_lookup_uses_cli_session(self, api_client, mock_session_config):
        """Test that the lookup method uses the CLI session."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Lookup codemod
            api_client.lookup("example_codemod")
            
            # Verify that CliSession.from_active_session was called
            mock_session_config.from_active_session.assert_called_once()
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the repository full name from the CLI session
            assert input_data.input.repo_full_name == "test/repo"

    def test_cli_session_error_handling(self, api_client):
        """Test error handling when the CLI session is not available."""
        # Mock CliSession.from_active_session to raise an exception
        with patch("graph_sitter.cli.api.client.CliSession") as mock_session:
            mock_session.from_active_session.side_effect = Exception("CLI session not available")
            
            # Mock the _make_request method to return the input data
            with patch.object(api_client, "_make_request") as mock_make_request:
                # Attempt to run a method that uses the CLI session
                with pytest.raises(Exception, match="CLI session not available"):
                    api_client.get_docs()
                
                # Verify that CliSession.from_active_session was called
                mock_session.from_active_session.assert_called_once()
                
                # Verify that _make_request was not called
                mock_make_request.assert_not_called()

