"""Service container for Contexten.

This module provides the ServiceContainer class which handles dependency
injection and service lifecycle management.
"""

import asyncio
from typing import Any, Dict, Optional, Type, TypeVar, get_type_hints

T = TypeVar('T')

class ServiceError(Exception):
    """Base class for service-related errors."""
    pass

class ServiceNotFoundError(ServiceError):
    """Error raised when a required service is not found."""
    pass

class ServiceDependencyError(ServiceError):
    """Error raised when service dependencies cannot be satisfied."""
    pass

class ServiceContainer:
    """Container for managing services and their dependencies.
    
    This class provides dependency injection and service lifecycle
    management capabilities.
    """

    def __init__(self, app: 'ContextenApp'):
        """Initialize the container.
        
        Args:
            app: The ContextenApp instance this container belongs to
        """
        self.app = app
        self._services: Dict[Type[Any], Any] = {}
        self._factories: Dict[Type[Any], callable] = {}
        self._singletons: Dict[Type[Any], Any] = {}
        self._initializing: Dict[Type[Any], asyncio.Event] = {}

    def register(
        self,
        service_type: Type[T],
        implementation: Optional[T] = None,
        factory: Optional[callable] = None,
        singleton: bool = True
    ) -> None:
        """Register a service.
        
        Args:
            service_type: Type/interface of the service
            implementation: Optional concrete implementation
            factory: Optional factory function to create instances
            singleton: Whether to use singleton pattern
            
        Raises:
            ValueError: If neither implementation nor factory is provided
        """
        if implementation is not None:
            if singleton:
                self._singletons[service_type] = implementation
            else:
                self._services[service_type] = implementation
        elif factory is not None:
            self._factories[service_type] = factory
        else:
            raise ValueError(
                "Either implementation or factory must be provided"
            )

    async def get(self, service_type: Type[T]) -> T:
        """Get a service instance.
        
        Args:
            service_type: Type/interface of service to get
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not registered
            ServiceDependencyError: If dependencies cannot be satisfied
        """
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]

        # Check if service is being initialized
        if service_type in self._initializing:
            await self._initializing[service_type].wait()
            if service_type in self._singletons:
                return self._singletons[service_type]

        # Create initialization event
        self._initializing[service_type] = asyncio.Event()

        try:
            # Get from services
            if service_type in self._services:
                instance = self._services[service_type]
                await self._initialize_service(instance)
                return instance

            # Create from factory
            if service_type in self._factories:
                instance = await self._create_from_factory(
                    service_type,
                    self._factories[service_type]
                )
                return instance

            raise ServiceNotFoundError(
                f"No registration found for {service_type.__name__}"
            )

        finally:
            # Signal initialization complete
            event = self._initializing.pop(service_type)
            event.set()

    async def _initialize_service(self, service: Any) -> None:
        """Initialize a service instance.
        
        Args:
            service: Service instance to initialize
            
        Raises:
            ServiceDependencyError: If dependencies cannot be satisfied
        """
        # Get service dependencies
        dependencies = get_type_hints(service.__init__)
        
        # Remove return type hint if present
        dependencies.pop('return', None)

        # Inject dependencies
        for name, dep_type in dependencies.items():
            if name == 'self':
                continue
            try:
                setattr(service, f'_{name}', await self.get(dep_type))
            except ServiceNotFoundError as e:
                raise ServiceDependencyError(
                    f"Failed to inject dependency {name}: {e}"
                )

        # Initialize if possible
        if hasattr(service, 'initialize') and callable(service.initialize):
            await service.initialize()

    async def _create_from_factory(
        self,
        service_type: Type[T],
        factory: callable
    ) -> T:
        """Create a service instance from a factory.
        
        Args:
            service_type: Type/interface of service to create
            factory: Factory function to create instance
            
        Returns:
            Created service instance
            
        Raises:
            ServiceDependencyError: If dependencies cannot be satisfied
        """
        # Get factory dependencies
        dependencies = get_type_hints(factory)
        
        # Remove return type hint
        dependencies.pop('return', None)

        # Resolve dependencies
        kwargs = {}
        for name, dep_type in dependencies.items():
            try:
                kwargs[name] = await self.get(dep_type)
            except ServiceNotFoundError as e:
                raise ServiceDependencyError(
                    f"Failed to resolve factory dependency {name}: {e}"
                )

        # Create instance
        instance = await factory(**kwargs)

        # Initialize if needed
        await self._initialize_service(instance)

        return instance

    async def start(self) -> None:
        """Start all registered services.
        
        This method calls the start() method on all services that have one.
        """
        for services in [self._services.values(), self._singletons.values()]:
            for service in services:
                if hasattr(service, 'start') and callable(service.start):
                    await service.start()

    async def stop(self) -> None:
        """Stop all registered services.
        
        This method calls the stop() method on all services that have one.
        Services are stopped in reverse registration order.
        """
        for services in [
            reversed(list(self._services.values())),
            reversed(list(self._singletons.values()))
        ]:
            for service in services:
                if hasattr(service, 'stop') and callable(service.stop):
                    await service.stop()

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all services.
        
        Returns:
            Dict containing health status of all services
        """
        results = {}
        for services in [self._services, self._singletons]:
            for type_, service in services.items():
                if hasattr(service, 'health_check'):
                    try:
                        results[type_.__name__] = await service.health_check()
                    except Exception as e:
                        results[type_.__name__] = {
                            "status": "unhealthy",
                            "message": str(e),
                            "timestamp": self.app.current_time.isoformat()
                        }
        return results

