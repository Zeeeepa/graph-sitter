"""
Exception classes for the Codegen SDK.
"""


class CodegenError(Exception):
    """Base exception class for all Codegen SDK errors."""
    pass


class AuthenticationError(CodegenError):
    """Raised when authentication fails."""
    pass


class TaskError(CodegenError):
    """Raised when there's an error with task operations."""
    pass


class APIError(CodegenError):
    """Raised when the API returns an error."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass


class ValidationError(CodegenError):
    """Raised when input validation fails."""
    pass

