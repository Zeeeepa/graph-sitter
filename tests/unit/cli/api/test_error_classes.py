import pytest

from graph_sitter.cli.errors import InvalidTokenError, ServerError


class TestErrorClasses:
    """Test error classes used by the API client."""

    def test_invalid_token_error(self):
        """Test the InvalidTokenError class."""
        # Create an error
        error = InvalidTokenError("Invalid token")
        
        # Verify the error message
        assert str(error) == "Invalid token"
        
        # Verify the error is an Exception
        assert isinstance(error, Exception)

    def test_server_error(self):
        """Test the ServerError class."""
        # Create an error
        error = ServerError("Server error")
        
        # Verify the error message
        assert str(error) == "Server error"
        
        # Verify the error is an Exception
        assert isinstance(error, Exception)

    def test_invalid_token_error_inheritance(self):
        """Test that InvalidTokenError inherits from Exception."""
        # Create an error
        error = InvalidTokenError("Invalid token")
        
        # Verify the error inheritance
        assert isinstance(error, Exception)
        
        # Verify the error can be caught as an Exception
        try:
            raise error
        except Exception as e:
            assert e is error

    def test_server_error_inheritance(self):
        """Test that ServerError inherits from Exception."""
        # Create an error
        error = ServerError("Server error")
        
        # Verify the error inheritance
        assert isinstance(error, Exception)
        
        # Verify the error can be caught as an Exception
        try:
            raise error
        except Exception as e:
            assert e is error

    def test_error_with_details(self):
        """Test creating errors with detailed messages."""
        # Create errors with detailed messages
        invalid_token_error = InvalidTokenError("Invalid token: Token expired")
        server_error = ServerError("Server error: Internal server error")
        
        # Verify the error messages
        assert str(invalid_token_error) == "Invalid token: Token expired"
        assert str(server_error) == "Server error: Internal server error"

