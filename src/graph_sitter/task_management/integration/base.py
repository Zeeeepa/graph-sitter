"""
Base Integration Framework

Provides the foundation for all external system integrations with
standardized interfaces and common functionality.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from pydantic import BaseModel

from ..core.task import Task, TaskStatus


logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Status of an integration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class IntegrationConfig:
    """Configuration for an integration."""
    name: str
    enabled: bool = True
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    health_check_interval: int = 60
    custom_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_config is None:
            self.custom_config = {}


class IntegrationMetrics(BaseModel):
    """Metrics for integration performance."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    uptime_percentage: float = 100.0


class IntegrationBase(ABC):
    """
    Abstract base class for all external system integrations.
    
    Provides common functionality for connection management, health monitoring,
    error handling, and metrics collection.
    """
    
    def __init__(self, config: IntegrationConfig):
        """Initialize the integration with configuration."""
        self.config = config
        self.status = IntegrationStatus.DISCONNECTED
        self.metrics = IntegrationMetrics()
        self._connection = None
        self._last_health_check = None
        self._error_count = 0
        
        logger.info(f"Initialized {self.config.name} integration")
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the external system.
        
        Returns:
            True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the external system."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Perform a health check on the integration.
        
        Returns:
            True if the integration is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_task(self, task: Task) -> Any:
        """
        Execute a task using this integration.
        
        Args:
            task: The task to execute
            
        Returns:
            The result of task execution
        """
        pass
    
    async def initialize(self) -> bool:
        """Initialize the integration and establish connection."""
        if not self.config.enabled:
            self.status = IntegrationStatus.DISABLED
            logger.info(f"{self.config.name} integration is disabled")
            return True
        
        try:
            self.status = IntegrationStatus.CONNECTING
            success = await self.connect()
            
            if success:
                self.status = IntegrationStatus.CONNECTED
                logger.info(f"{self.config.name} integration connected successfully")
                return True
            else:
                self.status = IntegrationStatus.ERROR
                logger.error(f"Failed to connect {self.config.name} integration")
                return False
                
        except Exception as e:
            self.status = IntegrationStatus.ERROR
            logger.error(f"Error initializing {self.config.name} integration: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the integration gracefully."""
        try:
            await self.disconnect()
            self.status = IntegrationStatus.DISCONNECTED
            logger.info(f"{self.config.name} integration shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down {self.config.name} integration: {e}")
    
    def is_available(self) -> bool:
        """Check if the integration is available for use."""
        return self.status == IntegrationStatus.CONNECTED
    
    def get_status(self) -> IntegrationStatus:
        """Get the current status of the integration."""
        return self.status
    
    def get_metrics(self) -> IntegrationMetrics:
        """Get performance metrics for the integration."""
        return self.metrics
    
    def _update_metrics(self, success: bool, response_time: float, error: Optional[str] = None) -> None:
        """Update integration metrics."""
        self.metrics.total_requests += 1
        self.metrics.last_request_time = datetime.utcnow()
        
        if success:
            self.metrics.successful_requests += 1
            self._error_count = 0
        else:
            self.metrics.failed_requests += 1
            self.metrics.last_error = error
            self._error_count += 1
        
        # Update average response time
        total_successful = self.metrics.successful_requests
        if total_successful > 0:
            current_avg = self.metrics.average_response_time
            self.metrics.average_response_time = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
        
        # Update uptime percentage
        if self.metrics.total_requests > 0:
            self.metrics.uptime_percentage = (
                self.metrics.successful_requests / self.metrics.total_requests * 100
            )
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle integration errors with logging and status updates."""
        error_msg = f"{self.config.name} integration error"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {error}"
        
        logger.error(error_msg)
        
        # Update status if too many consecutive errors
        if self._error_count >= self.config.retry_attempts:
            self.status = IntegrationStatus.ERROR
    
    async def retry_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation: The operation to retry
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            The result of the operation
        """
        import asyncio
        
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"{self.config.name} operation failed (attempt {attempt + 1}), "
                        f"retrying in {delay} seconds: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"{self.config.name} operation failed after {self.config.retry_attempts} attempts: {e}"
                    )
        
        raise last_exception


class TaskHandler(ABC):
    """
    Abstract base class for task handlers within integrations.
    
    Task handlers are responsible for executing specific types of tasks
    using the capabilities of their associated integration.
    """
    
    def __init__(self, integration: IntegrationBase):
        """Initialize the task handler with its integration."""
        self.integration = integration
        self.supported_task_types = set()
    
    @abstractmethod
    async def handle_task(self, task: Task) -> Any:
        """
        Handle execution of a specific task.
        
        Args:
            task: The task to handle
            
        Returns:
            The result of task execution
        """
        pass
    
    def can_handle(self, task: Task) -> bool:
        """
        Check if this handler can handle the given task.
        
        Args:
            task: The task to check
            
        Returns:
            True if this handler can handle the task
        """
        return task.task_type in self.supported_task_types
    
    def validate_task(self, task: Task) -> List[str]:
        """
        Validate that a task is properly configured for this handler.
        
        Args:
            task: The task to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.can_handle(task):
            errors.append(f"Task type {task.task_type} not supported by this handler")
        
        if not self.integration.is_available():
            errors.append(f"Integration {self.integration.config.name} is not available")
        
        return errors
    
    async def execute_with_monitoring(self, task: Task) -> Any:
        """
        Execute a task with comprehensive monitoring and error handling.
        
        Args:
            task: The task to execute
            
        Returns:
            The result of task execution
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate task
            validation_errors = self.validate_task(task)
            if validation_errors:
                raise ValueError(f"Task validation failed: {', '.join(validation_errors)}")
            
            # Execute task
            result = await self.handle_task(task)
            
            # Update metrics
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self.integration._update_metrics(True, response_time)
            
            logger.info(f"Task {task.id} completed successfully via {self.integration.config.name}")
            return result
            
        except Exception as e:
            # Update metrics
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self.integration._update_metrics(False, response_time, str(e))
            
            # Handle error
            self.integration._handle_error(e, f"executing task {task.id}")
            raise


class IntegrationManager:
    """
    Manages multiple integrations and provides a unified interface
    for task execution across different external systems.
    """
    
    def __init__(self):
        """Initialize the integration manager."""
        self.integrations: Dict[str, IntegrationBase] = {}
        self.task_handlers: Dict[str, List[TaskHandler]] = {}
        
    def register_integration(self, integration: IntegrationBase) -> None:
        """Register an integration with the manager."""
        self.integrations[integration.config.name] = integration
        logger.info(f"Registered integration: {integration.config.name}")
    
    def register_task_handler(self, handler: TaskHandler) -> None:
        """Register a task handler with the manager."""
        integration_name = handler.integration.config.name
        
        if integration_name not in self.task_handlers:
            self.task_handlers[integration_name] = []
        
        self.task_handlers[integration_name].append(handler)
        logger.info(f"Registered task handler for {integration_name}")
    
    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all registered integrations."""
        results = {}
        
        for name, integration in self.integrations.items():
            try:
                success = await integration.initialize()
                results[name] = success
            except Exception as e:
                logger.error(f"Failed to initialize integration {name}: {e}")
                results[name] = False
        
        return results
    
    async def shutdown_all(self) -> None:
        """Shutdown all integrations."""
        for integration in self.integrations.values():
            try:
                await integration.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down integration {integration.config.name}: {e}")
    
    def get_integration(self, name: str) -> Optional[IntegrationBase]:
        """Get an integration by name."""
        return self.integrations.get(name)
    
    def get_available_integrations(self) -> List[str]:
        """Get list of available integration names."""
        return [
            name for name, integration in self.integrations.items()
            if integration.is_available()
        ]
    
    def find_handler_for_task(self, task: Task) -> Optional[TaskHandler]:
        """Find a suitable task handler for the given task."""
        for handlers in self.task_handlers.values():
            for handler in handlers:
                if handler.can_handle(task) and handler.integration.is_available():
                    return handler
        
        return None
    
    async def execute_task(self, task: Task) -> Any:
        """
        Execute a task using the most appropriate integration.
        
        Args:
            task: The task to execute
            
        Returns:
            The result of task execution
        """
        handler = self.find_handler_for_task(task)
        
        if not handler:
            raise RuntimeError(f"No available handler found for task {task.id} of type {task.task_type}")
        
        return await handler.execute_with_monitoring(task)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status for all integrations."""
        status = {
            "total_integrations": len(self.integrations),
            "available_integrations": len(self.get_available_integrations()),
            "integrations": {}
        }
        
        for name, integration in self.integrations.items():
            status["integrations"][name] = {
                "status": integration.get_status().value,
                "metrics": integration.get_metrics().dict(),
            }
        
        return status

