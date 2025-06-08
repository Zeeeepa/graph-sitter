"""Extension registry for Contexten.

This module provides the ExtensionRegistry class which manages extension
lifecycle, dependencies, and configuration.
"""

import asyncio
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Type

from .extension import (
    Extension,
    ExtensionState,
    ExtensionMetadata,
    DependencyError,
    ConfigurationError,
    LifecycleError,
)

class ExtensionRegistry:
    """Registry for managing Contexten extensions.
    
    This class handles extension registration, dependency resolution,
    lifecycle management, and configuration.
    """

    def __init__(self, app: 'ContextenApp'):
        """Initialize the registry.
        
        Args:
            app: The ContextenApp instance this registry belongs to
        """
        self.app = app
        self._extensions: Dict[str, Extension] = {}
        self._extension_types: Dict[str, Type[Extension]] = {}
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._dependents: Dict[str, Set[str]] = defaultdict(set)
        self._states: Dict[str, ExtensionState] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}

    def register_extension(
        self,
        extension_type: Type[Extension],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register an extension type.
        
        Args:
            extension_type: Extension class to register
            config: Optional configuration for the extension
            
        Raises:
            ValueError: If extension is already registered
            ConfigurationError: If configuration is invalid
        """
        # Create temporary instance to get metadata
        temp_ext = extension_type(self.app)
        metadata = temp_ext.metadata

        if metadata.name in self._extension_types:
            raise ValueError(
                f"Extension {metadata.name} is already registered"
            )

        # Validate configuration if provided
        if config:
            temp_ext.validate_config(config)
            self._configs[metadata.name] = config

        # Register extension type and dependencies
        self._extension_types[metadata.name] = extension_type
        self._states[metadata.name] = ExtensionState.REGISTERED

        # Update dependency graph
        for dep in metadata.dependencies:
            self._dependencies[metadata.name].add(dep)
            self._dependents[dep].add(metadata.name)

    async def initialize_extensions(self) -> None:
        """Initialize all registered extensions.
        
        This method resolves dependencies and initializes extensions
        in the correct order.
        
        Raises:
            DependencyError: If dependencies cannot be resolved
            ConfigurationError: If extension configuration fails
            LifecycleError: If extension initialization fails
        """
        # Check all dependencies are registered
        self._validate_dependencies()

        # Get initialization order
        init_order = self._get_initialization_order()

        # Initialize extensions in order
        for ext_name in init_order:
            await self._initialize_extension(ext_name)

    async def start_extensions(self) -> None:
        """Start all initialized extensions.
        
        Extensions are started in dependency order after initialization.
        
        Raises:
            LifecycleError: If extension startup fails
        """
        start_order = self._get_initialization_order()

        for ext_name in start_order:
            if self._states[ext_name] != ExtensionState.INITIALIZING:
                continue

            try:
                extension = self._extensions[ext_name]
                await extension.start()
                self._states[ext_name] = ExtensionState.ACTIVE
            except Exception as e:
                self._states[ext_name] = ExtensionState.ERROR
                raise LifecycleError(
                    f"Failed to start extension {ext_name}: {e}"
                )

    async def stop_extensions(self) -> None:
        """Stop all active extensions.
        
        Extensions are stopped in reverse dependency order.
        
        Raises:
            LifecycleError: If extension shutdown fails
        """
        # Get reverse initialization order
        stop_order = list(reversed(self._get_initialization_order()))

        # Stop extensions in reverse order
        for ext_name in stop_order:
            if self._states[ext_name] != ExtensionState.ACTIVE:
                continue

            try:
                extension = self._extensions[ext_name]
                self._states[ext_name] = ExtensionState.SHUTTING_DOWN
                await extension.stop()
                self._states[ext_name] = ExtensionState.SHUTDOWN
            except Exception as e:
                self._states[ext_name] = ExtensionState.ERROR
                raise LifecycleError(
                    f"Failed to stop extension {ext_name}: {e}"
                )

    def get_extension(self, name: str) -> Optional[Extension]:
        """Get an extension instance by name.
        
        Args:
            name: Name of the extension
            
        Returns:
            Extension instance or None if not found
        """
        return self._extensions.get(name)

    def get_extensions_by_type(self, extension_type: Type[Extension]) -> List[Extension]:
        """Get all extensions of a specific type.
        
        Args:
            extension_type: Type of extensions to get
            
        Returns:
            List of matching extension instances
        """
        return [
            ext for ext in self._extensions.values()
            if isinstance(ext, extension_type)
        ]

    def get_extension_state(self, name: str) -> ExtensionState:
        """Get the current state of an extension.
        
        Args:
            name: Name of the extension
            
        Returns:
            Current extension state
            
        Raises:
            KeyError: If extension is not registered
        """
        return self._states[name]

    async def _initialize_extension(self, name: str) -> None:
        """Initialize a single extension.
        
        Args:
            name: Name of the extension to initialize
            
        Raises:
            ConfigurationError: If configuration fails
            LifecycleError: If initialization fails
        """
        try:
            # Create extension instance
            ext_type = self._extension_types[name]
            config = self._configs.get(name, {})
            extension = ext_type(self.app, config)

            # Initialize extension
            self._states[name] = ExtensionState.INITIALIZING
            await extension.initialize()

            # Store initialized extension
            self._extensions[name] = extension

        except Exception as e:
            self._states[name] = ExtensionState.ERROR
            raise LifecycleError(
                f"Failed to initialize extension {name}: {e}"
            )

    def _validate_dependencies(self) -> None:
        """Validate all extension dependencies are satisfied.
        
        Raises:
            DependencyError: If dependencies cannot be satisfied
        """
        for ext_name, deps in self._dependencies.items():
            for dep in deps:
                if dep not in self._extension_types:
                    raise DependencyError(
                        f"Extension {ext_name} requires {dep} which is not registered"
                    )

    def _get_initialization_order(self) -> List[str]:
        """Get correct extension initialization order.
        
        Returns:
            List of extension names in initialization order
            
        Raises:
            DependencyError: If there are circular dependencies
        """
        # Implementation of topological sort
        visited = set()
        temp_mark = set()
        order = []

        def visit(name: str) -> None:
            if name in temp_mark:
                raise DependencyError(
                    f"Circular dependency detected involving {name}"
                )
            if name in visited:
                return

            temp_mark.add(name)

            for dep in self._dependencies[name]:
                visit(dep)

            temp_mark.remove(name)
            visited.add(name)
            order.append(name)

        for name in self._extension_types:
            if name not in visited:
                visit(name)

        return list(reversed(order))

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all extensions.
        
        Returns:
            Dict containing health status of all extensions
        """
        results = {}
        for name, extension in self._extensions.items():
            try:
                results[name] = await extension.health_check()
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "message": str(e),
                    "timestamp": self.app.current_time.isoformat()
                }
        return results

