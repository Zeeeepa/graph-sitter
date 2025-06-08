"""Extension Registry for Contexten Extensions.

This module provides a centralized registry for managing extension discovery,
registration, and capability advertisement in the unified extension system.
"""

import asyncio
import logging
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Set, Type, Union
from pathlib import Path
import importlib
import inspect

from pydantic import BaseModel, Field

from .connection import ConnectionManager, ExtensionConnection
from .capabilities import ExtensionCapability, CapabilityType
from .extension_base import ExtensionBase, ExtensionMetadata, ExtensionStatus

logger = logging.getLogger(__name__)


class ExtensionRegistration(BaseModel):
    """Extension registration information."""
    metadata: ExtensionMetadata
    instance: Optional[ExtensionBase] = None
    capabilities: List[ExtensionCapability] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    dependents: Set[str] = Field(default_factory=set)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_health_check: Optional[datetime] = None
    status: ExtensionStatus = ExtensionStatus.REGISTERED


class ExtensionRegistry:
    """Central registry for managing extensions."""

    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        """Initialize extension registry.
        
        Args:
            connection_manager: Optional connection manager instance
        """
        self._extensions: Dict[str, ExtensionRegistration] = {}
        self._capabilities: Dict[str, List[str]] = {}  # capability -> extension names
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._connection_manager = connection_manager or ConnectionManager()
        self._event_handlers: Dict[str, List[Any]] = {}
        self._auto_discovery_paths: List[Path] = []
        self._startup_order: List[str] = []
        
    def add_discovery_path(self, path: Union[str, Path]) -> None:
        """Add path for automatic extension discovery.
        
        Args:
            path: Path to search for extensions
        """
        path_obj = Path(path)
        if path_obj.exists() and path_obj.is_dir():
            self._auto_discovery_paths.append(path_obj)
            logger.info(f"Added discovery path: {path_obj}")
        else:
            logger.warning(f"Discovery path does not exist: {path_obj}")

    async def discover_extensions(self) -> List[str]:
        """Automatically discover extensions in configured paths.
        
        Returns:
            List of discovered extension names
        """
        discovered = []
        
        for path in self._auto_discovery_paths:
            try:
                for item in path.iterdir():
                    if item.is_dir() and not item.name.startswith('_'):
                        # Look for extension module
                        init_file = item / "__init__.py"
                        if init_file.exists():
                            try:
                                # Try to import and find extension class
                                module_name = f"contexten.extensions.{item.name}"
                                module = importlib.import_module(module_name)
                                
                                # Look for classes that inherit from ExtensionBase
                                for name, obj in inspect.getmembers(module):
                                    if (inspect.isclass(obj) and 
                                        issubclass(obj, ExtensionBase) and 
                                        obj != ExtensionBase):
                                        
                                        # Auto-register discovered extension
                                        extension_name = item.name
                                        if extension_name not in self._extensions:
                                            await self._auto_register_extension(
                                                extension_name, obj
                                            )
                                            discovered.append(extension_name)
                                            break
                                            
                            except Exception as e:
                                logger.warning(
                                    f"Failed to discover extension in {item}: {e}"
                                )
                                
            except Exception as e:
                logger.error(f"Error discovering extensions in {path}: {e}")
                
        logger.info(f"Discovered {len(discovered)} extensions: {discovered}")
        return discovered

    async def _auto_register_extension(
        self, 
        name: str, 
        extension_class: Type[ExtensionBase]
    ) -> None:
        """Auto-register discovered extension.
        
        Args:
            name: Extension name
            extension_class: Extension class
        """
        try:
            # Create metadata from class
            metadata = ExtensionMetadata(
                name=name,
                version=getattr(extension_class, '__version__', '1.0.0'),
                description=getattr(extension_class, '__doc__', ''),
                author=getattr(extension_class, '__author__', 'Unknown'),
                capabilities=getattr(extension_class, '_capabilities', []),
                dependencies=getattr(extension_class, '_dependencies', [])
            )
            
            await self.register_extension(metadata, extension_class)
            
        except Exception as e:
            logger.error(f"Failed to auto-register extension {name}: {e}")

    async def register_extension(
        self,
        metadata: ExtensionMetadata,
        extension_class: Optional[Type[ExtensionBase]] = None,
        instance: Optional[ExtensionBase] = None
    ) -> bool:
        """Register an extension.
        
        Args:
            metadata: Extension metadata
            extension_class: Extension class (if not providing instance)
            instance: Extension instance (if not providing class)
            
        Returns:
            True if registration successful, False otherwise
        """
        if metadata.name in self._extensions:
            logger.warning(f"Extension {metadata.name} already registered")
            return False
            
        try:
            # Create instance if not provided
            if instance is None and extension_class is not None:
                instance = extension_class()
            elif instance is None:
                logger.error(f"Must provide either extension_class or instance")
                return False
                
            # Validate dependencies
            missing_deps = []
            for dep in metadata.dependencies:
                if dep not in self._extensions:
                    missing_deps.append(dep)
                    
            if missing_deps:
                logger.warning(
                    f"Extension {metadata.name} has missing dependencies: {missing_deps}"
                )
                # Could choose to defer registration until dependencies are available
                
            # Create registration
            registration = ExtensionRegistration(
                metadata=metadata,
                instance=instance,
                capabilities=metadata.capabilities,
                dependencies=metadata.dependencies
            )
            
            # Update dependency graph
            self._dependency_graph[metadata.name] = set(metadata.dependencies)
            for dep in metadata.dependencies:
                if dep in self._extensions:
                    self._extensions[dep].dependents.add(metadata.name)
                    
            # Register capabilities
            for capability in metadata.capabilities:
                cap_name = capability.name if hasattr(capability, 'name') else str(capability)
                if cap_name not in self._capabilities:
                    self._capabilities[cap_name] = []
                self._capabilities[cap_name].append(metadata.name)
                
            # Store registration
            self._extensions[metadata.name] = registration
            
            # Add to connection manager if extension has connections
            if hasattr(instance, 'get_connections'):
                connections = await instance.get_connections()
                for conn_name, connection in connections.items():
                    self._connection_manager._connections[f"{metadata.name}.{conn_name}"] = connection
                    
            logger.info(f"Registered extension: {metadata.name} v{metadata.version}")
            
            # Emit registration event
            await self._emit_event('extension.registered', {
                'extension_name': metadata.name,
                'metadata': metadata.dict(),
                'timestamp': datetime.now(UTC).isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register extension {metadata.name}: {e}")
            return False

    async def unregister_extension(self, name: str) -> bool:
        """Unregister an extension.
        
        Args:
            name: Extension name
            
        Returns:
            True if unregistration successful, False otherwise
        """
        if name not in self._extensions:
            logger.warning(f"Extension {name} not registered")
            return False
            
        try:
            registration = self._extensions[name]
            
            # Check for dependents
            if registration.dependents:
                logger.error(
                    f"Cannot unregister {name}, has dependents: {registration.dependents}"
                )
                return False
                
            # Stop extension if running
            if registration.instance and registration.status == ExtensionStatus.RUNNING:
                await registration.instance.stop()
                
            # Remove from dependency graph
            del self._dependency_graph[name]
            for dep in registration.dependencies:
                if dep in self._extensions:
                    self._extensions[dep].dependents.discard(name)
                    
            # Remove capabilities
            for capability in registration.capabilities:
                cap_name = capability.name if hasattr(capability, 'name') else str(capability)
                if cap_name in self._capabilities:
                    self._capabilities[cap_name].remove(name)
                    if not self._capabilities[cap_name]:
                        del self._capabilities[cap_name]
                        
            # Remove from registry
            del self._extensions[name]
            
            logger.info(f"Unregistered extension: {name}")
            
            # Emit unregistration event
            await self._emit_event('extension.unregistered', {
                'extension_name': name,
                'timestamp': datetime.now(UTC).isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister extension {name}: {e}")
            return False

    def get_extension(self, name: str) -> Optional[ExtensionRegistration]:
        """Get extension registration by name.
        
        Args:
            name: Extension name
            
        Returns:
            Extension registration if found, None otherwise
        """
        return self._extensions.get(name)

    def list_extensions(self) -> List[str]:
        """List all registered extension names.
        
        Returns:
            List of extension names
        """
        return list(self._extensions.keys())

    def find_extensions_by_capability(self, capability: str) -> List[str]:
        """Find extensions that provide a specific capability.
        
        Args:
            capability: Capability name
            
        Returns:
            List of extension names that provide the capability
        """
        return self._capabilities.get(capability, [])

    async def get_extension_status(self, name: str) -> Optional[ExtensionStatus]:
        """Get extension status.
        
        Args:
            name: Extension name
            
        Returns:
            Extension status if found, None otherwise
        """
        registration = self._extensions.get(name)
        if registration and registration.instance:
            # Update status from instance
            registration.status = await registration.instance.get_status()
            return registration.status
        return None

    async def start_extension(self, name: str) -> bool:
        """Start an extension.
        
        Args:
            name: Extension name
            
        Returns:
            True if started successfully, False otherwise
        """
        registration = self._extensions.get(name)
        if not registration or not registration.instance:
            logger.error(f"Extension {name} not found or has no instance")
            return False
            
        try:
            # Check dependencies are running
            for dep in registration.dependencies:
                dep_status = await self.get_extension_status(dep)
                if dep_status != ExtensionStatus.RUNNING:
                    logger.error(f"Dependency {dep} not running for {name}")
                    return False
                    
            await registration.instance.start()
            registration.status = ExtensionStatus.RUNNING
            
            logger.info(f"Started extension: {name}")
            
            # Emit start event
            await self._emit_event('extension.started', {
                'extension_name': name,
                'timestamp': datetime.now(UTC).isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start extension {name}: {e}")
            registration.status = ExtensionStatus.ERROR
            return False

    async def stop_extension(self, name: str) -> bool:
        """Stop an extension.
        
        Args:
            name: Extension name
            
        Returns:
            True if stopped successfully, False otherwise
        """
        registration = self._extensions.get(name)
        if not registration or not registration.instance:
            logger.error(f"Extension {name} not found or has no instance")
            return False
            
        try:
            # Check no dependents are running
            for dependent in registration.dependents:
                dep_status = await self.get_extension_status(dependent)
                if dep_status == ExtensionStatus.RUNNING:
                    logger.error(f"Cannot stop {name}, dependent {dependent} is running")
                    return False
                    
            await registration.instance.stop()
            registration.status = ExtensionStatus.STOPPED
            
            logger.info(f"Stopped extension: {name}")
            
            # Emit stop event
            await self._emit_event('extension.stopped', {
                'extension_name': name,
                'timestamp': datetime.now(UTC).isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop extension {name}: {e}")
            registration.status = ExtensionStatus.ERROR
            return False

    async def start_all_extensions(self) -> Dict[str, bool]:
        """Start all extensions in dependency order.
        
        Returns:
            Dictionary of extension names to start success status
        """
        # Calculate startup order based on dependencies
        startup_order = self._calculate_startup_order()
        results = {}
        
        for name in startup_order:
            results[name] = await self.start_extension(name)
            if not results[name]:
                logger.error(f"Failed to start {name}, stopping startup process")
                break
                
        return results

    async def stop_all_extensions(self) -> Dict[str, bool]:
        """Stop all extensions in reverse dependency order.
        
        Returns:
            Dictionary of extension names to stop success status
        """
        # Calculate shutdown order (reverse of startup)
        shutdown_order = list(reversed(self._calculate_startup_order()))
        results = {}
        
        for name in shutdown_order:
            if name in self._extensions:
                results[name] = await self.stop_extension(name)
                
        return results

    def _calculate_startup_order(self) -> List[str]:
        """Calculate extension startup order based on dependencies.
        
        Returns:
            List of extension names in startup order
        """
        if self._startup_order:
            return self._startup_order
            
        # Topological sort of dependency graph
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {name}")
            if name in visited:
                return
                
            temp_visited.add(name)
            
            # Visit dependencies first
            for dep in self._dependency_graph.get(name, []):
                if dep in self._extensions:
                    visit(dep)
                    
            temp_visited.remove(name)
            visited.add(name)
            order.append(name)
            
        # Visit all extensions
        for name in self._extensions:
            if name not in visited:
                visit(name)
                
        self._startup_order = order
        return order

    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all extensions.
        
        Returns:
            Dictionary of extension names to health status
        """
        results = {}
        
        for name, registration in self._extensions.items():
            if registration.instance:
                try:
                    is_healthy = await registration.instance.health_check()
                    results[name] = is_healthy
                    registration.last_health_check = datetime.now(UTC)
                    
                    if not is_healthy:
                        await self._emit_event('extension.health.failed', {
                            'extension_name': name,
                            'timestamp': datetime.now(UTC).isoformat()
                        })
                        
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {e}")
                    results[name] = False
                    
        return results

    def add_event_handler(self, event_type: str, handler: Any) -> None:
        """Add event handler for registry events.
        
        Args:
            event_type: Event type to handle
            handler: Event handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit registry event.
        
        Args:
            event_type: Event type
            data: Event data
        """
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics.
        
        Returns:
            Dictionary of registry statistics
        """
        status_counts = {}
        for registration in self._extensions.values():
            status = registration.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
        return {
            'total_extensions': len(self._extensions),
            'status_counts': status_counts,
            'total_capabilities': len(self._capabilities),
            'dependency_graph_size': len(self._dependency_graph),
            'discovery_paths': [str(p) for p in self._auto_discovery_paths]
        }

