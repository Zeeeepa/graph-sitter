"""Error handling and recovery for Grainchain integration.

This module provides comprehensive error handling, retry mechanisms,
circuit breakers, and recovery procedures for Grainchain operations.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from .grainchain_types import GrainchainEvent, GrainchainEventType, IntegrationStatus

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categories of errors for better handling."""
    PROVIDER = "provider"
    NETWORK = "network"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Context information for errors."""
    error: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    provider: Optional[str] = None
    operation: Optional[str] = None
    resource_id: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    reset_timeout: float = 60.0  # seconds
    half_open_timeout: float = 30.0  # seconds
    min_throughput: int = 10
    error_percentage_threshold: float = 50.0

class CircuitBreakerState(Enum):
    """States for circuit breaker."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker."""
    total_requests: int = 0
    failed_requests: int = 0
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    error_percentage: float = 0.0
    last_state_change: Optional[datetime] = None

class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, config: Optional[CircuitBreakerConfig] = None) -> None:
        """Initialize circuit breaker."""
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                else:
                    raise CircuitBreakerError("Circuit breaker is open")

            try:
                result = await func(*args, **kwargs)
                await self._handle_success()
                return cast(T, result)
            except Exception as e:
                await self._handle_failure(e)
                raise

    async def _handle_success(self) -> None:
        """Handle successful call."""
        self.metrics.total_requests += 1
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.metrics.consecutive_failures = 0
            self.metrics.last_state_change = datetime.now(UTC)

    async def _handle_failure(self, error: Exception) -> None:
        """Handle failed call."""
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.last_failure_time = datetime.now(UTC)
        self.metrics.error_percentage = (
            (self.metrics.failed_requests / self.metrics.total_requests) * 100
            if self.metrics.total_requests > 0 else 0
        )

        if self._should_trip():
            self.state = CircuitBreakerState.OPEN
            self.metrics.last_state_change = datetime.now(UTC)

    def _should_trip(self) -> bool:
        """Check if circuit breaker should trip."""
        return (
            self.metrics.consecutive_failures >= self.config.failure_threshold or
            (self.metrics.total_requests >= self.config.min_throughput and
             self.metrics.error_percentage >= self.config.error_percentage_threshold)
        )

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if not self.metrics.last_state_change:
            return False
        elapsed = (datetime.now(UTC) - self.metrics.last_state_change).total_seconds()
        return elapsed >= self.config.reset_timeout

class RetryConfig:
    """Configuration for retry mechanism."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ) -> None:
        """Initialize retry configuration."""
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

class RetryableError(Exception):
    """Base class for retryable errors."""
    pass

class CircuitBreakerError(Exception):
    """Error raised when circuit breaker is open."""
    pass

class ErrorHandler:
    """Central error handler for Grainchain operations."""

    def __init__(self) -> None:
        """Initialize error handler."""
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._error_handlers: Dict[ErrorCategory, List[Callable[[ErrorContext], None]]] = {}
        self._recovery_procedures: Dict[ErrorCategory, List[Callable[[], None]]] = {}

    def create_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Create a new circuit breaker."""
        breaker = CircuitBreaker(config)
        self._circuit_breakers[name] = breaker
        return breaker

    def register_error_handler(
        self,
        category: ErrorCategory,
        handler: Callable[[ErrorContext], None]
    ) -> None:
        """Register an error handler for a category."""
        if category not in self._error_handlers:
            self._error_handlers[category] = []
        self._error_handlers[category].append(handler)

    def register_recovery_procedure(
        self,
        category: ErrorCategory,
        procedure: Callable[[], None]
    ) -> None:
        """Register a recovery procedure for a category."""
        if category not in self._recovery_procedures:
            self._recovery_procedures[category] = []
        self._recovery_procedures[category].append(procedure)

    def handle_error(self, error: Exception, context: ErrorContext) -> None:
        """Handle an error with context."""
        # Log error with context
        logger.error(
            "Error in Grainchain operation",
            extra={
                "error_type": type(error).__name__,
                "severity": context.severity.value,
                "category": context.category.value,
                "provider": context.provider,
                "operation": context.operation,
                "resource_id": context.resource_id,
                "retry_count": context.retry_count,
                "metadata": context.metadata
            },
            exc_info=error
        )

        # Execute category-specific handlers
        handlers = self._error_handlers.get(context.category, [])
        for handler in handlers:
            try:
                handler(context)
            except Exception as e:
                logger.exception(f"Error handler failed: {e}")

        # Execute recovery procedures
        procedures = self._recovery_procedures.get(context.category, [])
        for procedure in procedures:
            try:
                procedure()
            except Exception as e:
                logger.exception(f"Recovery procedure failed: {e}")

def with_retry(
    retry_config: Optional[RetryConfig] = None,
    retryable_errors: Optional[List[type[Exception]]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying operations with exponential backoff."""
    config = retry_config or RetryConfig()
    errors = retryable_errors or [RetryableError]

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Optional[Exception] = None
            attempt = 0

            while attempt < config.max_attempts:
                try:
                    return await func(*args, **kwargs)
                except tuple(errors) as e:  # type: ignore
                    last_error = e
                    attempt += 1

                    if attempt == config.max_attempts:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )

                    # Add jitter if enabled
                    if config.jitter:
                        delay *= (0.5 + time.random())

                    logger.warning(
                        f"Operation failed (attempt {attempt}/{config.max_attempts}), "
                        f"retrying in {delay:.2f}s",
                        exc_info=e
                    )

                    await asyncio.sleep(delay)

            if last_error:
                raise last_error
            raise RuntimeError("Retry loop completed without error or success")

        return wrapper

    return decorator

# Example usage:
# @with_retry(RetryConfig(max_attempts=3))
# async def fetch_data() -> str:
#     # ... implementation ...
#     pass

