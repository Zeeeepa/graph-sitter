"""
Strands Error Handler

Comprehensive error handling for the Strands event loop system.
Based on: https://github.com/strands-agents/sdk-python/blob/main/src/strands/event_loop/error_handler.py
"""

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..types.event_loop import Message, MessageHandler, EventLoopConfig

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorInfo:
    """Information about an error."""
    error_id: str
    timestamp: float
    severity: ErrorSeverity
    error_type: str
    message: str
    traceback: str
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    resolved: bool = False


@dataclass
class ErrorStats:
    """Error handling statistics."""
    total_errors: int = 0
    errors_by_severity: Dict[ErrorSeverity, int] = field(default_factory=lambda: {
        severity: 0 for severity in ErrorSeverity
    })
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    recent_errors: List[ErrorInfo] = field(default_factory=list)
    recovery_attempts: int = 0
    successful_recoveries: int = 0


class ErrorHandler:
    """Comprehensive error handling system for Strands."""
    
    def __init__(self, config: EventLoopConfig):
        """Initialize the error handler.
        
        Args:
            config: Event loop configuration
        """
        self.config = config
        self.stats = ErrorStats()
        self.error_callbacks: List[Callable[[ErrorInfo], None]] = []
        self.recovery_strategies: Dict[str, Callable[[ErrorInfo], bool]] = {}
        
        # Circuit breaker state
        self.circuit_breaker_state: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized error handler")
    
    async def handle_error(self, 
                          error: Exception, 
                          message: Optional[Message] = None,
                          handler: Optional[MessageHandler] = None,
                          context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Handle an error with comprehensive processing.
        
        Args:
            error: The exception that occurred
            message: Optional message being processed when error occurred
            handler: Optional handler that caused the error
            context: Optional additional context
            
        Returns:
            Error information
        """
        error_info = self._create_error_info(error, message, handler, context)
        
        # Log the error
        self._log_error(error_info)
        
        # Update statistics
        self._update_stats(error_info)
        
        # Attempt recovery
        await self._attempt_recovery(error_info)
        
        # Notify callbacks
        self._notify_callbacks(error_info)
        
        # Check circuit breaker
        self._update_circuit_breaker(error_info)
        
        return error_info
    
    def add_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """Add an error callback function.
        
        Args:
            callback: Function to call when errors occur
        """
        self.error_callbacks.append(callback)
        logger.info("Added error callback")
    
    def add_recovery_strategy(self, error_type: str, strategy: Callable[[ErrorInfo], bool]):
        """Add a recovery strategy for a specific error type.
        
        Args:
            error_type: Type of error to handle
            strategy: Recovery function that returns True if recovery was successful
        """
        self.recovery_strategies[error_type] = strategy
        logger.info(f"Added recovery strategy for: {error_type}")
    
    def _create_error_info(self, 
                          error: Exception,
                          message: Optional[Message] = None,
                          handler: Optional[MessageHandler] = None,
                          context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Create error information object.
        
        Args:
            error: The exception
            message: Optional message context
            handler: Optional handler context
            context: Optional additional context
            
        Returns:
            Error information
        """
        error_id = f"error_{int(time.time() * 1000)}"
        error_type = type(error).__name__
        
        # Determine severity
        severity = self._determine_severity(error, error_type)
        
        # Build context
        error_context = context or {}
        if message:
            error_context["message_id"] = message.id
            error_context["message_type"] = message.type
        if handler:
            error_context["handler_id"] = handler.handler_id
        
        return ErrorInfo(
            error_id=error_id,
            timestamp=time.time(),
            severity=severity,
            error_type=error_type,
            message=str(error),
            traceback=traceback.format_exc(),
            context=error_context
        )
    
    def _determine_severity(self, error: Exception, error_type: str) -> ErrorSeverity:
        """Determine the severity of an error.
        
        Args:
            error: The exception
            error_type: Type of the error
            
        Returns:
            Error severity
        """
        # Critical errors
        if error_type in ["SystemExit", "KeyboardInterrupt", "MemoryError"]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if error_type in ["ConnectionError", "TimeoutError", "PermissionError"]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if error_type in ["ValueError", "TypeError", "AttributeError"]:
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _log_error(self, error_info: ErrorInfo):
        """Log an error with appropriate level.
        
        Args:
            error_info: Error information to log
        """
        log_message = f"Error {error_info.error_id}: {error_info.message}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
            logger.critical(f"Traceback: {error_info.traceback}")
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
            logger.debug(f"Traceback: {error_info.traceback}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _update_stats(self, error_info: ErrorInfo):
        """Update error statistics.
        
        Args:
            error_info: Error information
        """
        self.stats.total_errors += 1
        self.stats.errors_by_severity[error_info.severity] += 1
        
        if error_info.error_type in self.stats.errors_by_type:
            self.stats.errors_by_type[error_info.error_type] += 1
        else:
            self.stats.errors_by_type[error_info.error_type] = 1
        
        # Keep only last 100 recent errors
        self.stats.recent_errors.append(error_info)
        if len(self.stats.recent_errors) > 100:
            self.stats.recent_errors = self.stats.recent_errors[-100:]
    
    async def _attempt_recovery(self, error_info: ErrorInfo):
        """Attempt to recover from an error.
        
        Args:
            error_info: Error information
        """
        self.stats.recovery_attempts += 1
        
        # Check if we have a recovery strategy for this error type
        if error_info.error_type in self.recovery_strategies:
            try:
                strategy = self.recovery_strategies[error_info.error_type]
                
                if asyncio.iscoroutinefunction(strategy):
                    success = await strategy(error_info)
                else:
                    success = strategy(error_info)
                
                if success:
                    error_info.resolved = True
                    self.stats.successful_recoveries += 1
                    logger.info(f"Successfully recovered from error: {error_info.error_id}")
                else:
                    logger.warning(f"Recovery failed for error: {error_info.error_id}")
                    
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
    
    def _notify_callbacks(self, error_info: ErrorInfo):
        """Notify error callbacks.
        
        Args:
            error_info: Error information
        """
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as callback_error:
                logger.error(f"Error callback failed: {callback_error}")
    
    def _update_circuit_breaker(self, error_info: ErrorInfo):
        """Update circuit breaker state based on error.
        
        Args:
            error_info: Error information
        """
        error_type = error_info.error_type
        
        if error_type not in self.circuit_breaker_state:
            self.circuit_breaker_state[error_type] = {
                "failure_count": 0,
                "last_failure_time": None,
                "state": "closed"  # closed, open, half-open
            }
        
        breaker = self.circuit_breaker_state[error_type]
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = time.time()
        
        # Open circuit breaker if too many failures
        if breaker["failure_count"] >= 5 and breaker["state"] == "closed":
            breaker["state"] = "open"
            logger.warning(f"Circuit breaker opened for error type: {error_type}")
    
    def is_circuit_breaker_open(self, error_type: str) -> bool:
        """Check if circuit breaker is open for an error type.
        
        Args:
            error_type: Type of error to check
            
        Returns:
            True if circuit breaker is open
        """
        if error_type not in self.circuit_breaker_state:
            return False
        
        breaker = self.circuit_breaker_state[error_type]
        
        if breaker["state"] == "open":
            # Check if we should try half-open
            if time.time() - breaker["last_failure_time"] > 60:  # 1 minute timeout
                breaker["state"] = "half-open"
                logger.info(f"Circuit breaker half-open for error type: {error_type}")
                return False
            return True
        
        return False
    
    def reset_circuit_breaker(self, error_type: str):
        """Reset circuit breaker for an error type.
        
        Args:
            error_type: Type of error to reset
        """
        if error_type in self.circuit_breaker_state:
            self.circuit_breaker_state[error_type] = {
                "failure_count": 0,
                "last_failure_time": None,
                "state": "closed"
            }
            logger.info(f"Reset circuit breaker for error type: {error_type}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error handling statistics.
        
        Returns:
            Error statistics
        """
        return {
            "total_errors": self.stats.total_errors,
            "errors_by_severity": {
                severity.value: count 
                for severity, count in self.stats.errors_by_severity.items()
            },
            "errors_by_type": self.stats.errors_by_type,
            "recent_errors_count": len(self.stats.recent_errors),
            "recovery_attempts": self.stats.recovery_attempts,
            "successful_recoveries": self.stats.successful_recoveries,
            "recovery_success_rate": (
                self.stats.successful_recoveries / self.stats.recovery_attempts
                if self.stats.recovery_attempts > 0 else 0
            ),
            "circuit_breakers": {
                error_type: state["state"]
                for error_type, state in self.circuit_breaker_state.items()
            }
        }

