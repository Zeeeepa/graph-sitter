"""
Enhanced exception classes for the Codegen SDK with detailed error information.
"""

from typing import Dict, Any, Optional


class CodegenError(Exception):
    """Base exception for Codegen SDK errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(CodegenError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTH_ERROR", **kwargs)


class APIError(CodegenError):
    """Raised when API requests fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}


class RateLimitError(APIError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, error_code="RATE_LIMIT", **kwargs)
        self.retry_after = retry_after


class ValidationError(CodegenError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field


class TaskError(CodegenError):
    """Raised when task operations fail."""
    
    def __init__(self, message: str, task_id: Optional[str] = None, task_status: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="TASK_ERROR", **kwargs)
        self.task_id = task_id
        self.task_status = task_status


class TimeoutError(CodegenError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str = "Operation timed out", timeout_duration: Optional[float] = None, **kwargs):
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)
        self.timeout_duration = timeout_duration


class NetworkError(CodegenError):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None, **kwargs):
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)
        self.original_error = original_error


class ConfigurationError(CodegenError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_key = config_key

