"""
Comprehensive error handling and recovery system.
"""

import asyncio
import logging
import traceback
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    SYSTEM = "system"
    DATABASE = "database"
    INTEGRATION = "integration"
    VALIDATION = "validation"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USER_INPUT = "user_input"
    EXTERNAL_SERVICE = "external_service"


class SystemError(Exception):
    """Base exception for system errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.recoverable = recoverable
        self.timestamp = datetime.utcnow()


class RecoverableError(SystemError):
    """Exception for errors that can be automatically recovered from."""
    
    def __init__(self, message: str, recovery_action: Optional[str] = None, **kwargs):
        super().__init__(message, recoverable=True, **kwargs)
        self.recovery_action = recovery_action


class ErrorHandler:
    """Comprehensive error handling and recovery system."""
    
    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.recovery_strategies: Dict[str, callable] = {}
        self.error_patterns: Dict[str, int] = {}
        
        # Register default recovery strategies
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """Register default error recovery strategies."""
        self.recovery_strategies.update({
            "database_connection": self._recover_database_connection,
            "api_timeout": self._recover_api_timeout,
            "rate_limit": self._recover_rate_limit,
            "memory_limit": self._recover_memory_limit,
        })
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        attempt_recovery: bool = True
    ) -> Dict[str, Any]:
        """
        Handle an error with logging, classification, and optional recovery.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            attempt_recovery: Whether to attempt automatic recovery
            
        Returns:
            Dictionary with error handling results
        """
        context = context or {}
        
        # Classify the error
        error_info = self._classify_error(error, context)
        
        # Log the error
        self._log_error(error_info)
        
        # Store error in history
        self.error_history.append(error_info)
        
        # Update error patterns
        self._update_error_patterns(error_info)
        
        # Attempt recovery if enabled and error is recoverable
        recovery_result = None
        if attempt_recovery and error_info.get("recoverable", False):
            recovery_result = await self._attempt_recovery(error_info)
        
        return {
            "error_id": error_info["id"],
            "category": error_info["category"],
            "severity": error_info["severity"],
            "recoverable": error_info["recoverable"],
            "recovery_attempted": recovery_result is not None,
            "recovery_successful": recovery_result.get("success", False) if recovery_result else False,
            "recovery_details": recovery_result
        }
    
    def _classify_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify an error and extract relevant information."""
        error_id = f"err_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(error)}"
        
        # Default classification
        error_info = {
            "id": error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
            "category": ErrorCategory.SYSTEM,
            "severity": ErrorSeverity.MEDIUM,
            "recoverable": False
        }
        
        # Handle SystemError instances
        if isinstance(error, SystemError):
            error_info.update({
                "category": error.category,
                "severity": error.severity,
                "recoverable": error.recoverable,
                "context": {**context, **error.context}
            })
        else:
            # Classify based on error type and message
            error_info.update(self._auto_classify_error(error, context))
        
        return error_info
    
    def _auto_classify_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically classify an error based on type and message."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        classification = {
            "category": ErrorCategory.SYSTEM,
            "severity": ErrorSeverity.MEDIUM,
            "recoverable": False
        }
        
        # Database errors
        if any(keyword in error_message for keyword in ["database", "connection", "sql", "postgres", "sqlite"]):
            classification.update({
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.HIGH,
                "recoverable": True
            })
        
        # Integration errors
        elif any(keyword in error_message for keyword in ["api", "http", "request", "timeout", "github", "linear", "slack"]):
            classification.update({
                "category": ErrorCategory.INTEGRATION,
                "severity": ErrorSeverity.MEDIUM,
                "recoverable": True
            })
        
        # Performance errors
        elif any(keyword in error_message for keyword in ["memory", "timeout", "performance", "slow"]):
            classification.update({
                "category": ErrorCategory.PERFORMANCE,
                "severity": ErrorSeverity.HIGH,
                "recoverable": True
            })
        
        # Validation errors
        elif any(keyword in error_message for keyword in ["validation", "invalid", "required", "missing"]):
            classification.update({
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "recoverable": False
            })
        
        # Security errors
        elif any(keyword in error_message for keyword in ["permission", "unauthorized", "forbidden", "security"]):
            classification.update({
                "category": ErrorCategory.SECURITY,
                "severity": ErrorSeverity.CRITICAL,
                "recoverable": False
            })
        
        return classification
    
    def _log_error(self, error_info: Dict[str, Any]) -> None:
        """Log error information with appropriate level."""
        severity = error_info["severity"]
        message = f"[{error_info['id']}] {error_info['category']}: {error_info['message']}"
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(message, extra={"error_info": error_info})
        elif severity == ErrorSeverity.HIGH:
            logger.error(message, extra={"error_info": error_info})
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(message, extra={"error_info": error_info})
        else:
            logger.info(message, extra={"error_info": error_info})
    
    def _update_error_patterns(self, error_info: Dict[str, Any]) -> None:
        """Update error pattern tracking."""
        pattern_key = f"{error_info['category']}:{error_info['type']}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1
    
    async def _attempt_recovery(self, error_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Attempt to recover from an error."""
        category = error_info["category"]
        error_type = error_info["type"]
        
        # Determine recovery strategy
        strategy_key = None
        if category == ErrorCategory.DATABASE:
            strategy_key = "database_connection"
        elif "timeout" in error_info["message"].lower():
            strategy_key = "api_timeout"
        elif "rate limit" in error_info["message"].lower():
            strategy_key = "rate_limit"
        elif "memory" in error_info["message"].lower():
            strategy_key = "memory_limit"
        
        if not strategy_key or strategy_key not in self.recovery_strategies:
            logger.info(f"No recovery strategy available for error: {error_info['id']}")
            return None
        
        try:
            logger.info(f"Attempting recovery for error {error_info['id']} using strategy: {strategy_key}")
            recovery_func = self.recovery_strategies[strategy_key]
            
            if asyncio.iscoroutinefunction(recovery_func):
                result = await recovery_func(error_info)
            else:
                result = recovery_func(error_info)
            
            logger.info(f"Recovery attempt completed for error {error_info['id']}: {result}")
            return result
            
        except Exception as recovery_error:
            logger.error(f"Recovery failed for error {error_info['id']}: {recovery_error}")
            return {
                "success": False,
                "error": str(recovery_error),
                "strategy": strategy_key
            }
    
    async def _recover_database_connection(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from database connection errors."""
        try:
            # Wait a bit before retrying
            await asyncio.sleep(1)
            
            # Try to reinitialize database connection
            from ..database import get_database_manager
            db_manager = get_database_manager()
            await db_manager.close()
            await db_manager.initialize()
            
            return {"success": True, "strategy": "database_connection", "action": "reconnected"}
        except Exception as e:
            return {"success": False, "strategy": "database_connection", "error": str(e)}
    
    async def _recover_api_timeout(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from API timeout errors."""
        try:
            # Implement exponential backoff
            await asyncio.sleep(2)
            return {"success": True, "strategy": "api_timeout", "action": "backoff_applied"}
        except Exception as e:
            return {"success": False, "strategy": "api_timeout", "error": str(e)}
    
    async def _recover_rate_limit(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from rate limit errors."""
        try:
            # Wait longer for rate limits
            await asyncio.sleep(60)
            return {"success": True, "strategy": "rate_limit", "action": "rate_limit_wait"}
        except Exception as e:
            return {"success": False, "strategy": "rate_limit", "error": str(e)}
    
    async def _recover_memory_limit(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from memory limit errors."""
        try:
            # Force garbage collection
            import gc
            gc.collect()
            return {"success": True, "strategy": "memory_limit", "action": "garbage_collected"}
        except Exception as e:
            return {"success": False, "strategy": "memory_limit", "error": str(e)}
    
    def register_recovery_strategy(self, name: str, strategy: callable) -> None:
        """Register a custom recovery strategy."""
        self.recovery_strategies[name] = strategy
        logger.info(f"Registered recovery strategy: {name}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and patterns."""
        total_errors = len(self.error_history)
        
        if total_errors == 0:
            return {"total_errors": 0}
        
        # Calculate statistics
        categories = {}
        severities = {}
        recoverable_count = 0
        
        for error in self.error_history:
            category = error.get("category", "unknown")
            severity = error.get("severity", "unknown")
            
            categories[category] = categories.get(category, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
            
            if error.get("recoverable", False):
                recoverable_count += 1
        
        return {
            "total_errors": total_errors,
            "categories": categories,
            "severities": severities,
            "recoverable_percentage": (recoverable_count / total_errors) * 100,
            "error_patterns": self.error_patterns,
            "recent_errors": self.error_history[-10:]  # Last 10 errors
        }

