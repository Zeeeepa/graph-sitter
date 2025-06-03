"""Retry logic and error handling for autogenlib."""

import logging
import time
from typing import Any, Callable, TypeVar

from .config import AutogenConfig
from .exceptions import APIError, RetryExhaustedError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryHandler:
    """Handles retry logic with exponential backoff."""
    
    def __init__(self, config: AutogenConfig):
        """Initialize the retry handler.
        
        Args:
            config: Configuration object.
        """
        self.config = config
    
    def execute_with_retry(self, func: Callable[[], T]) -> T:
        """Execute a function with retry logic.
        
        Args:
            func: Function to execute.
            
        Returns:
            Result of the function.
            
        Raises:
            RetryExhaustedError: If all retry attempts are exhausted.
        """
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                result = func()
                if attempt > 0:
                    logger.info(f"Function succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                last_error = e
                
                # Don't retry on certain types of errors
                if self._should_not_retry(e):
                    logger.error(f"Non-retryable error: {e}")
                    raise e
                
                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_retries + 1} attempts failed")
        
        raise RetryExhaustedError(
            f"All retry attempts exhausted. Last error: {last_error}",
            attempts=self.config.max_retries + 1,
            last_error=last_error
        )
    
    def _should_not_retry(self, error: Exception) -> bool:
        """Determine if an error should not be retried.
        
        Args:
            error: The error that occurred.
            
        Returns:
            True if the error should not be retried.
        """
        # Don't retry authentication errors
        if "authentication" in str(error).lower() or "unauthorized" in str(error).lower():
            return True
        
        # Don't retry validation errors
        if "validation" in str(error).lower() or "invalid" in str(error).lower():
            return True
        
        # Don't retry if it's an API error with a 4xx status code (client error)
        if isinstance(error, APIError) and error.status_code and 400 <= error.status_code < 500:
            return True
        
        return False
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate the delay for the next retry attempt.
        
        Args:
            attempt: Current attempt number (0-based).
            
        Returns:
            Delay in seconds.
        """
        return self.config.retry_delay * (self.config.retry_backoff ** attempt)

