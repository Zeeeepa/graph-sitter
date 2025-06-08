"""Main Contexten application class.

This module provides the ContextenApp class which serves as the central
point of integration for all Contexten components.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

from .core.extension import Extension
from .core.registry import ExtensionRegistry
from .core.container import ServiceContainer
from .core.events.bus import EventBus
from .core.state.manager import StateManager

logger = logging.getLogger(__name__)

class ContextenApp:
    """Main Contexten application class.
    
    This class integrates all core components and provides the main
    application lifecycle management.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the application.
        
        Args:
            config: Optional application configuration
        """
        self.config = config or {}
        
        # Core components
        self.extension_registry = ExtensionRegistry(self)
        self.service_container = ServiceContainer(self)
        self.event_bus = EventBus(self)
        self.state_manager = StateManager(self)
        
        # State
        self._running = False
        self._startup_complete = False
        self._shutdown_complete = False

        # Auto-register available extensions
        self._auto_register_extensions()

    @property
    def current_time(self) -> datetime:
        """Get current time in UTC.
        
        Returns:
            Current UTC datetime
        """
        return datetime.now(timezone.utc)

    def _auto_register_extensions(self) -> None:
        """Auto-register available extensions."""
        try:
            # GitHub Extension
            from .extensions.github.github import GitHubExtension
            github_config = self.config.get('github', {})
            if github_config.get('token'):
                self.register_extension(GitHubExtension, github_config)
        except ImportError:
            logger.warning("GitHub extension not available")

        try:
            # Linear Extension
            from .extensions.linear.linear import LinearExtension
            linear_config = self.config.get('linear', {})
            if linear_config.get('api_key'):
                self.register_extension(LinearExtension, linear_config)
        except ImportError:
            logger.warning("Linear extension not available")

        try:
            # Codegen Extension
            from .extensions.codegen.codegen import CodegenExtension
            codegen_config = self.config.get('codegen', {})
            if codegen_config.get('org_id') and codegen_config.get('token'):
                self.register_extension(CodegenExtension, codegen_config)
        except ImportError:
            logger.warning("Codegen extension not available")

        try:
            # Flow Orchestrator Extension
            from .extensions.flows.orchestrator import FlowOrchestrator
            flow_config = self.config.get('flows', {})
            self.register_extension(FlowOrchestrator, flow_config)
        except ImportError:
            logger.warning("Flow orchestrator extension not available")

        try:
            # Dashboard Extension
            from .extensions.dashboard.dashboard_extension import DashboardExtension
            dashboard_config = self.config.get('dashboard', {})
            self.register_extension(DashboardExtension, dashboard_config)
        except ImportError:
            logger.warning("Dashboard extension not available")

        try:
            # Slack Extension
            from .extensions.slack.slack import SlackExtension
            slack_config = self.config.get('slack', {})
            if slack_config.get('token'):
                self.register_extension(SlackExtension, slack_config)
        except ImportError:
            logger.warning("Slack extension not available")

        try:
            # CircleCI Extension
            from .extensions.circleci.circleci import CircleCIExtension
            circleci_config = self.config.get('circleci', {})
            if circleci_config.get('token'):
                self.register_extension(CircleCIExtension, circleci_config)
        except ImportError:
            logger.warning("CircleCI extension not available")

    def register_extension(
        self,
        extension_type: Type[Extension],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register an extension.
        
        Args:
            extension_type: Extension class to register
            config: Optional extension configuration
        """
        self.extension_registry.register_extension(extension_type, config)

    def register_service(
        self,
        service_type: Type[Any],
        implementation: Optional[Any] = None,
        factory: Optional[callable] = None,
        singleton: bool = True
    ) -> None:
        """Register a service.
        
        Args:
            service_type: Service type/interface
            implementation: Optional service implementation
            factory: Optional factory function
            singleton: Whether to use singleton pattern
        """
        self.service_container.register(
            service_type,
            implementation,
            factory,
            singleton
        )

    async def get_service(self, service_type: Type[Any]) -> Any:
        """Get a service instance.
        
        Args:
            service_type: Type of service to get
            
        Returns:
            Service instance
        """
        return await self.service_container.get(service_type)

    def has_extension(self, name: str) -> bool:
        """Check if an extension is registered.
        
        Args:
            name: Name of extension
            
        Returns:
            True if extension is registered
        """
        return self.extension_registry.get_extension(name) is not None

    def get_extension(self, name: str) -> Optional[Extension]:
        """Get an extension instance.
        
        Args:
            name: Name of extension
            
        Returns:
            Extension instance or None
        """
        return self.extension_registry.get_extension(name)

    async def start(self) -> None:
        """Start the application.
        
        This initializes and starts all components in the correct order.
        """
        if self._running:
            return

        try:
            logger.info("Starting Contexten application")
            self._running = True

            # Start core components
            await self.event_bus.start()
            await self.state_manager.load_state()

            # Initialize extensions
            logger.info("Initializing extensions")
            await self.extension_registry.initialize_extensions()

            # Start services
            logger.info("Starting services")
            await self.service_container.start()

            # Start extensions
            logger.info("Starting extensions")
            await self.extension_registry.start_extensions()

            self._startup_complete = True
            logger.info("Contexten application started successfully")

            # Log registered extensions
            extensions = list(self.extension_registry._extensions.keys())
            logger.info(f"Active extensions: {', '.join(extensions)}")

        except Exception as e:
            logger.error(f"Failed to start application: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the application.
        
        This stops all components in the correct order.
        """
        if not self._running:
            return

        try:
            logger.info("Stopping Contexten application")
            self._running = False

            # Stop extensions
            logger.info("Stopping extensions")
            await self.extension_registry.stop_extensions()

            # Stop services
            logger.info("Stopping services")
            await self.service_container.stop()

            # Stop core components
            await self.event_bus.stop()

            self._shutdown_complete = True
            logger.info("Contexten application stopped")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check application health.
        
        Returns:
            Dict containing health status of all components
        """
        status = "healthy"
        components = {}

        try:
            # Check core components
            components["event_bus"] = await self.event_bus.health_check()
            components["state_manager"] = await self.state_manager.health_check()
            components["service_container"] = await self.service_container.health_check()
            components["extensions"] = await self.extension_registry.health_check()

            # Determine overall status
            for component in components.values():
                if isinstance(component, dict) and component.get("status") != "healthy":
                    status = "degraded"
                    break

        except Exception as e:
            status = "unhealthy"
            logger.error(f"Health check failed: {e}", exc_info=True)

        return {
            "status": status,
            "running": self._running,
            "startup_complete": self._startup_complete,
            "shutdown_complete": self._shutdown_complete,
            "components": components,
            "timestamp": self.current_time.isoformat(),
        }
