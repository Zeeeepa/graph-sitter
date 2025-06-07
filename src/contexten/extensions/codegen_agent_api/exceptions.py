"""
Enhanced exception classes for the Codegen Agent API extension.

Includes overlay-specific exceptions and comprehensive error handling.
"""

from typing import Dict, Any, Optional
from .types import ErrorCode


class CodegenError(Exception):
    """Base exception for Codegen SDK errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[ErrorCode] = None, 
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.request_id = request_id
        
        # Add timestamp
        import time
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_code": self.error_code,
            "message": str(self),
            "details": self.details,
            "request_id": self.request_id,
            "timestamp": self.timestamp
        }


class AuthenticationError(CodegenError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code=ErrorCode.AUTH_ERROR, **kwargs)


class APIError(CodegenError):
    """Raised when API requests fail."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None, 
        response_data: Optional[Dict] = None, 
        **kwargs
    ):
        super().__init__(message, error_code=ErrorCode.API_ERROR, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}
        
        # Add status code to details
        if status_code:
            self.details["status_code"] = status_code
        if response_data:
            self.details["response_data"] = response_data


class RateLimitError(APIError):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded", 
        retry_after: Optional[int] = None, 
        **kwargs
    ):
        super().__init__(message, error_code=ErrorCode.RATE_LIMIT, **kwargs)
        self.retry_after = retry_after
        
        if retry_after:
            self.details["retry_after"] = retry_after


class ValidationError(CodegenError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, error_code=ErrorCode.VALIDATION_ERROR, **kwargs)
        self.field = field
        
        if field:
            self.details["field"] = field


class TaskError(CodegenError):
    """Raised when task operations fail."""
    
    def __init__(
        self, 
        message: str, 
        task_id: Optional[str] = None, 
        task_status: Optional[str] = None, 
        **kwargs
    ):
        super().__init__(message, error_code=ErrorCode.TASK_ERROR, **kwargs)
        self.task_id = task_id
        self.task_status = task_status
        
        if task_id:
            self.details["task_id"] = task_id
        if task_status:
            self.details["task_status"] = task_status


class TimeoutError(CodegenError):
    """Raised when operations timeout."""
    
    def __init__(
        self, 
        message: str = "Operation timed out", 
        timeout_duration: Optional[float] = None, 
        **kwargs
    ):
        super().__init__(message, error_code=ErrorCode.TIMEOUT_ERROR, **kwargs)
        self.timeout_duration = timeout_duration
        
        if timeout_duration:
            self.details["timeout_duration"] = timeout_duration


class NetworkError(CodegenError):
    """Raised when network operations fail."""
    
    def __init__(
        self, 
        message: str, 
        original_error: Optional[Exception] = None, 
        **kwargs
    ):
        super().__init__(message, error_code=ErrorCode.NETWORK_ERROR, **kwargs)
        self.original_error = original_error
        
        if original_error:
            self.details["original_error"] = str(original_error)
            self.details["original_error_type"] = type(original_error).__name__


class ConfigurationError(CodegenError):
    """Raised when configuration is invalid."""
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None, 
        **kwargs
    ):
        super().__init__(message, error_code=ErrorCode.CONFIG_ERROR, **kwargs)
        self.config_key = config_key
        
        if config_key:
            self.details["config_key"] = config_key


class OverlayError(CodegenError):
    """Raised when overlay operations fail."""
    
    def __init__(
        self, 
        message: str, 
        overlay_strategy: Optional[str] = None,
        pip_available: Optional[bool] = None,
        local_available: Optional[bool] = None,
        **kwargs
    ):
        super().__init__(message, error_code=ErrorCode.OVERLAY_ERROR, **kwargs)
        self.overlay_strategy = overlay_strategy
        self.pip_available = pip_available
        self.local_available = local_available
        
        # Add overlay info to details
        overlay_info = {}
        if overlay_strategy is not None:
            overlay_info["strategy"] = overlay_strategy
        if pip_available is not None:
            overlay_info["pip_available"] = pip_available
        if local_available is not None:
            overlay_info["local_available"] = local_available
        
        if overlay_info:
            self.details["overlay_info"] = overlay_info


class PipPackageNotFoundError(OverlayError):
    """Raised when pip package is not found but required."""
    
    def __init__(
        self, 
        package_name: str = "codegen",
        message: Optional[str] = None,
        **kwargs
    ):
        if message is None:
            message = f"Required pip package '{package_name}' not found"
        
        super().__init__(message, **kwargs)
        self.package_name = package_name
        self.details["package_name"] = package_name


class PipPackageImportError(OverlayError):
    """Raised when pip package cannot be imported."""
    
    def __init__(
        self, 
        package_name: str = "codegen",
        import_error: Optional[Exception] = None,
        message: Optional[str] = None,
        **kwargs
    ):
        if message is None:
            message = f"Failed to import pip package '{package_name}'"
            if import_error:
                message += f": {import_error}"
        
        super().__init__(message, **kwargs)
        self.package_name = package_name
        self.import_error = import_error
        
        self.details["package_name"] = package_name
        if import_error:
            self.details["import_error"] = str(import_error)
            self.details["import_error_type"] = type(import_error).__name__


class OverlayStrategyError(OverlayError):
    """Raised when overlay strategy is invalid or cannot be executed."""
    
    def __init__(
        self, 
        strategy: str,
        reason: str,
        **kwargs
    ):
        message = f"Overlay strategy '{strategy}' failed: {reason}"
        super().__init__(message, overlay_strategy=strategy, **kwargs)
        self.strategy = strategy
        self.reason = reason
        self.details["reason"] = reason


class FallbackError(OverlayError):
    """Raised when fallback mechanism fails."""
    
    def __init__(
        self, 
        primary_strategy: str,
        fallback_strategy: str,
        primary_error: Optional[Exception] = None,
        fallback_error: Optional[Exception] = None,
        **kwargs
    ):
        message = f"Both primary strategy '{primary_strategy}' and fallback strategy '{fallback_strategy}' failed"
        
        super().__init__(message, **kwargs)
        self.primary_strategy = primary_strategy
        self.fallback_strategy = fallback_strategy
        self.primary_error = primary_error
        self.fallback_error = fallback_error
        
        # Add error details
        error_details = {
            "primary_strategy": primary_strategy,
            "fallback_strategy": fallback_strategy
        }
        
        if primary_error:
            error_details["primary_error"] = str(primary_error)
            error_details["primary_error_type"] = type(primary_error).__name__
        
        if fallback_error:
            error_details["fallback_error"] = str(fallback_error)
            error_details["fallback_error_type"] = type(fallback_error).__name__
        
        self.details["error_details"] = error_details


# Exception hierarchy for easy catching
class ExtensionError(CodegenError):
    """Base class for extension-specific errors."""
    pass


class IntegrationError(ExtensionError):
    """Raised when integration operations fail."""
    
    def __init__(
        self, 
        message: str,
        integration_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.integration_name = integration_name
        
        if integration_name:
            self.details["integration_name"] = integration_name


class WebhookError(ExtensionError):
    """Raised when webhook operations fail."""
    
    def __init__(
        self, 
        message: str,
        webhook_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.webhook_id = webhook_id
        self.webhook_url = webhook_url
        
        webhook_info = {}
        if webhook_id:
            webhook_info["webhook_id"] = webhook_id
        if webhook_url:
            webhook_info["webhook_url"] = webhook_url
        
        if webhook_info:
            self.details["webhook_info"] = webhook_info


# Utility functions for exception handling

def handle_api_error(response) -> None:
    """Handle API response and raise appropriate exception."""
    if response.status_code == 401:
        raise AuthenticationError("Authentication failed - invalid token")
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
    elif response.status_code >= 400:
        error_data = {}
        try:
            error_data = response.json()
        except (ValueError, KeyError):
            pass
        
        error_message = error_data.get("error", f"HTTP {response.status_code}")
        raise APIError(
            error_message, 
            status_code=response.status_code, 
            response_data=error_data
        )


def wrap_network_error(func):
    """Decorator to wrap network errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, CodegenError):
                raise  # Re-raise our own exceptions
            
            # Wrap other exceptions as NetworkError
            import requests
            if isinstance(e, requests.exceptions.Timeout):
                raise TimeoutError(f"Request timed out: {e}")
            elif isinstance(e, requests.exceptions.ConnectionError):
                raise NetworkError(f"Connection failed: {e}", original_error=e)
            elif isinstance(e, requests.RequestException):
                raise NetworkError(f"Request failed: {e}", original_error=e)
            else:
                raise NetworkError(f"Unexpected error: {e}", original_error=e)
    
    return wrapper


def create_error_context(
    operation: str,
    **context_data
) -> Dict[str, Any]:
    """Create error context for debugging."""
    import time
    
    return {
        "operation": operation,
        "timestamp": time.time(),
        "context": context_data
    }


# Export all exceptions
__all__ = [
    # Base exceptions
    "CodegenError",
    "ExtensionError",
    
    # Core exceptions
    "AuthenticationError",
    "APIError", 
    "RateLimitError",
    "ValidationError",
    "TaskError",
    "TimeoutError",
    "NetworkError",
    "ConfigurationError",
    
    # Overlay exceptions
    "OverlayError",
    "PipPackageNotFoundError",
    "PipPackageImportError",
    "OverlayStrategyError",
    "FallbackError",
    
    # Extension exceptions
    "IntegrationError",
    "WebhookError",
    
    # Utility functions
    "handle_api_error",
    "wrap_network_error",
    "create_error_context",
]

