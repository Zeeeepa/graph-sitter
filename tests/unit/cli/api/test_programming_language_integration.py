from unittest.mock import MagicMock, patch

import pytest

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


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


class TestProgrammingLanguageIntegration:
    """Test integration with the ProgrammingLanguage enum."""

    def test_create_with_programming_language(self, api_client, mock_session_config):
        """Test create with ProgrammingLanguage."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Create codemod
            api_client.create("example_codemod", "Create a codemod that does X")
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the language
            assert input_data.input.language == ProgrammingLanguage.PYTHON

    def test_improve_codemod_with_programming_language(self, api_client):
        """Test improve_codemod with ProgrammingLanguage."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Improve codemod
            api_client.improve_codemod(
                codemod="def original_codemod():\n    pass",
                task="Improve the codemod to print something",
                concerns=["Doesn't do anything"],
                context={"file1.py": "def example():\n    pass"},
                language=ProgrammingLanguage.PYTHON,
            )
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the language
            assert input_data.input.language == ProgrammingLanguage.PYTHON

    def test_programming_language_from_string(self, api_client, mock_session_config):
        """Test ProgrammingLanguage conversion from string."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Create codemod
            api_client.create("example_codemod", "Create a codemod that does X")
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data includes the language
            assert input_data.input.language == ProgrammingLanguage.PYTHON
            
            # Verify the language was converted from a string
            mock_session_config.from_active_session.return_value.config.repository.language = "python"
            assert ProgrammingLanguage(mock_session_config.from_active_session.return_value.config.repository.language) == ProgrammingLanguage.PYTHON

