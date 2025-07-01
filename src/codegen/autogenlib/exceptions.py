"""Custom exceptions for autogenlib module."""


class AutogenLibError(Exception):
    """Base exception for autogenlib module."""
    pass


class ConfigurationError(AutogenLibError):
    """Raised when there's a configuration error."""
    pass


class AuthenticationError(AutogenLibError):
    """Raised when authentication fails."""
    pass


class APIError(AutogenLibError):
    """Raised when API calls fail."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class TaskError(AutogenLibError):
    """Raised when task execution fails."""
    
    def __init__(self, message: str, task_id: str = None):
        super().__init__(message)
        self.task_id = task_id


class ContextError(AutogenLibError):
    """Raised when context enhancement fails."""
    pass


class CacheError(AutogenLibError):
    """Raised when cache operations fail."""
    pass


class RetryExhaustedError(AutogenLibError):
    """Raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, attempts: int = None, last_error: Exception = None):
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


class TimeoutError(AutogenLibError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str, timeout: float = None):
        super().__init__(message)
        self.timeout = timeout


class UsageLimitError(AutogenLibError):
    """Raised when usage limits are exceeded."""
    
    def __init__(self, message: str, current_usage: float = None, limit: float = None):
        super().__init__(message)
        self.current_usage = current_usage
        self.limit = limit

