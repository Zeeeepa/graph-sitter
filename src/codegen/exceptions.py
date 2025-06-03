"""
Exception classes for the Codegen SDK.
"""


class CodegenError(Exception):
    """Base exception for Codegen SDK errors."""
    pass


class AuthenticationError(CodegenError):
    """Raised when authentication fails."""
    pass


class APIError(CodegenError):
    """Raised when API requests fail."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class RateLimitError(APIError):
    """Raised when rate limits are exceeded."""
    pass


class ValidationError(CodegenError):
    """Raised when input validation fails."""
    pass


class TaskError(CodegenError):
    """Raised when task operations fail."""
    pass

