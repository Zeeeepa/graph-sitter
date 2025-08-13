from unittest.mock import MagicMock, patch

import pytest

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.cli.codemod.convert import convert_to_ui


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


class TestConversion:
    """Test conversion utilities used by the API client."""

    def test_convert_to_ui_integration(self, api_client, mock_session_config):
        """Test integration with convert_to_ui."""
        # Create a mock codemod
        mock_codemod = MagicMock()
        mock_codemod.name = "test_codemod"
        mock_codemod.get_current_source.return_value = "def test_codemod():\n    pass"
        
        # Mock convert_to_ui to return a modified source
        with patch("graph_sitter.cli.api.client.convert_to_ui") as mock_convert_to_ui:
            mock_convert_to_ui.return_value = "def test_codemod():\n    # Converted for UI\n    pass"
            
            # Mock the _make_request method to return the input data
            with patch.object(api_client, "_make_request") as mock_make_request:
                # Run the codemod
                api_client.run(mock_codemod)
                
                # Verify that convert_to_ui was called with the codemod source
                mock_convert_to_ui.assert_called_once_with("def test_codemod():\n    pass")
                
                # Verify the input data
                mock_make_request.assert_called_once()
                call_args = mock_make_request.call_args[0]
                input_data = call_args[2]
                
                # Verify the input data includes the converted source
                assert input_data.input.codemod_source == "def test_codemod():\n    # Converted for UI\n    pass"

    def test_convert_to_ui_direct(self):
        """Test convert_to_ui directly."""
        # Test with a simple source
        source = "def test_function():\n    pass"
        converted = convert_to_ui(source)
        
        # Verify the conversion
        assert converted == source

    def test_convert_to_ui_with_complex_source(self):
        """Test convert_to_ui with a more complex source."""
        # Test with a more complex source
        source = """def test_function():
    """
        # Add a triple-quoted string
        source += '    """'
        source += """
    This is a docstring.
    """
        source += '    """'
        source += """
    # This is a comment
    return "Hello, world!"
"""
        
        converted = convert_to_ui(source)
        
        # Verify the conversion
        assert converted == source

