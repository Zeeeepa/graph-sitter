"""Base classes and protocols for Contexten extensions.

This module provides the foundational classes and protocols for building
Contexten extensions, including lifecycle management and dependency handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type

class ExtensionState(Enum):
    """Possible states of an extension."""
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

@dataclass
class ExtensionMetadata:
    """Metadata for a Contexten extension."""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    required: bool = False
    config_schema: Optional[Dict[str, Any]] = None
    tags: Set[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()

class ExtensionError(Exception):
    """Base class for extension-related errors."""
    pass

class DependencyError(ExtensionError):
    """Error raised when extension dependencies cannot be satisfied."""
    pass

class ConfigurationError(ExtensionError):
    """Error raised when extension configuration is invalid."""
    pass

class LifecycleError(ExtensionError):
    """Error raised when extension lifecycle operations fail."""
    pass

class Extension(ABC):
    """Base class for all Contexten extensions.
    
    This class defines the interface that all extensions must implement,
    including lifecycle hooks and dependency management.
    """

    def __init__(self, app: 'ContextenApp', config: Optional[Dict[str, Any]] = None):
        """Initialize the extension.
        
        Args:
            app: The ContextenApp instance this extension belongs to
            config: Optional configuration dictionary for the extension
        """
        self.app = app
        self.config = config or {}
        self.state = ExtensionState.UNREGISTERED
        self._metadata = None

    @property
    @abstractmethod
    def metadata(self) -> ExtensionMetadata:
        """Get extension metadata.
        
        Returns:
            ExtensionMetadata: The extension's metadata
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the extension.
        
        This method is called during system startup after all extensions
        have been registered but before they are activated.
        
        Raises:
            ConfigurationError: If configuration is invalid
            DependencyError: If dependencies cannot be satisfied
            LifecycleError: If initialization fails
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the extension.
        
        This method is called to activate the extension after initialization
        and after all dependencies have been started.
        
        Raises:
            LifecycleError: If startup fails
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the extension.
        
        This method is called during system shutdown. Extensions should
        cleanup resources and gracefully terminate operations.
        
        Raises:
            LifecycleError: If shutdown fails
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """Check extension health.
        
        Returns:
            Dict[str, Any]: Health check results with at least:
                - status: str ("healthy", "degraded", "unhealthy")
                - message: str (description of health state)
                - timestamp: str (ISO format)
        """
        return {
            "status": "healthy",
            "message": "Extension is running",
            "timestamp": self.app.current_time.isoformat()
        }

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate extension configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.metadata.config_schema:
            return
            
        try:
            # TODO: Implement config validation against schema
            pass
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}")

    def check_dependencies(self) -> None:
        """Check if extension dependencies are satisfied.
        
        Raises:
            DependencyError: If dependencies cannot be satisfied
        """
        for dep in self.metadata.dependencies:
            if not self.app.has_extension(dep):
                raise DependencyError(
                    f"Missing required dependency: {dep}"
                )

class EventHandlerExtension(Extension):
    """Base class for extensions that handle events.
    
    This class extends the base Extension class with event handling
    capabilities, including event registration and routing.
    """

    def __init__(self, app: 'ContextenApp', config: Optional[Dict[str, Any]] = None):
        super().__init__(app, config)
        self._event_handlers = {}

    def register_event_handler(self, event_type: str, handler: callable) -> None:
        """Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Async callable to handle the event
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def handle_event(self, event_type: str, event_data: Any) -> None:
        """Handle an event.
        
        Args:
            event_type: Type of event to handle
            event_data: Event data to process
        """
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    await handler(event_data)
                except Exception as e:
                    self.app.logger.error(
                        f"Error handling event {event_type}: {e}",
                        exc_info=True
                    )

class ServiceExtension(Extension):
    """Base class for extensions that provide services.
    
    This class extends the base Extension class with service registration
    and dependency injection capabilities.
    """

    def __init__(self, app: 'ContextenApp', config: Optional[Dict[str, Any]] = None):
        super().__init__(app, config)
        self._services = {}

    def register_service(self, service_type: Type[Any], implementation: Any) -> None:
        """Register a service implementation.
        
        Args:
            service_type: Type/interface of the service
            implementation: Service implementation
        """
        self._services[service_type] = implementation

    def get_service(self, service_type: Type[Any]) -> Any:
        """Get a service implementation.
        
        Args:
            service_type: Type/interface of the service to get
            
        Returns:
            Service implementation
            
        Raises:
            KeyError: If service type is not registered
        """
        return self._services[service_type]

    def has_service(self, service_type: Type[Any]) -> bool:
        """Check if a service type is registered.
        
        Args:
            service_type: Type/interface to check
            
        Returns:
            bool: True if service type is registered
        """
        return service_type in self._services

