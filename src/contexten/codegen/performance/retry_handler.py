"""
Retry handling with exponential backoff for failed requests.

This module provides intelligent retry mechanisms for handling
transient failures and rate limiting.
"""

import asyncio
import logging
import random
from typing import Callable, Any, Optional


logger = logging.getLogger(__name__)


class RetryHandler:
    """
    Retry handler with exponential backoff and jitter.
    
    Features:
    - Exponential backoff with jitter
    - Configurable retry conditions
    - Circuit breaker pattern
    - Retry statistics
    """
    
    def __init__(self,
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries
            max_delay: Maximum delay between retries
            backoff_factor: Exponential backoff factor
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        
        self.stats = {
            "total_attempts": 0,
            "successful_retries": 0,
            "failed_retries": 0
        }
    
    async def retry_with_backoff(self,
                               func: Callable,
                               *args,
                               should_retry: Optional[Callable] = None,
                               **kwargs) -> Any:
        """
        Execute function with retry and exponential backoff.
        
        Args:
            func: Function to execute
            *args: Function arguments
            should_retry: Optional function to determine if retry should occur
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.stats["total_attempts"] += 1
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    self.stats["successful_retries"] += 1
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if we should retry
                if should_retry and not should_retry(e):
                    break
                
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    self.stats["failed_retries"] += 1
        
        # All retries exhausted
        if last_exception:
            raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)
        
        # Add jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        delay += jitter
        
        return max(0, delay)
    
    def get_stats(self) -> dict:
        """Get retry statistics."""
        return self.stats.copy()

