"""
System orchestrator for coordinating all components of the CI/CD system.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from contextlib import asynccontextmanager

from ..config import get_settings, get_database_config, get_integrations_config
from ..database import get_database_manager, TaskModel, ProjectModel, EventModel
from .error_handling import ErrorHandler, SystemError
from .performance import PerformanceMonitor

logger = logging.getLogger(__name__)


class SystemOrchestrator:
    """
    Central orchestrator for the comprehensive CI/CD system.
    
    Coordinates between database, integrations, and processing components
    to provide unified system management and cross-component communication.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.db_config = get_database_config()
        self.integrations_config = get_integrations_config()
        
        # Core components
        self.db_manager = get_database_manager()
        self.error_handler = ErrorHandler()
        self.performance_monitor = PerformanceMonitor()
        
        # Component registry
        self._components: Dict[str, Any] = {}
        self._initialized = False
        
        # Event system
        self._event_handlers: Dict[str, List[callable]] = {}
        
    async def initialize(self) -> None:
        """Initialize the orchestrator and all components."""
        if self._initialized:
            return
            
        logger.info("Initializing System Orchestrator")
        
        try:
            # Initialize database
            await self.db_manager.initialize()
            logger.info("Database initialized successfully")
            
            # Initialize performance monitoring
            await self.performance_monitor.initialize()
            logger.info("Performance monitoring initialized")
            
            # Register core components
            self._components["database"] = self.db_manager
            self._components["error_handler"] = self.error_handler
            self._components["performance_monitor"] = self.performance_monitor
            
            self._initialized = True
            logger.info("System Orchestrator initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize System Orchestrator: {e}")
            raise SystemError(f"Orchestrator initialization failed: {e}") from e
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator and cleanup resources."""
        logger.info("Shutting down System Orchestrator")
        
        try:
            # Shutdown performance monitoring
            if hasattr(self.performance_monitor, 'shutdown'):
                await self.performance_monitor.shutdown()
            
            # Close database connections
            await self.db_manager.close()
            
            self._initialized = False
            logger.info("System Orchestrator shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during orchestrator shutdown: {e}")
    
    def register_component(self, name: str, component: Any) -> None:
        """Register a component with the orchestrator."""
        self._components[name] = component
        logger.info(f"Registered component: {name}")
    
    def get_component(self, name: str) -> Optional[Any]:
        """Get a registered component by name."""
        return self._components.get(name)
    
    def register_event_handler(self, event_type: str, handler: callable) -> None:
        """Register an event handler for a specific event type."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for: {event_type}")
    
    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to all registered handlers."""
        if event_type not in self._event_handlers:
            return
        
        logger.debug(f"Emitting event: {event_type}")
        
        # Execute all handlers for this event type
        tasks = []
        for handler in self._event_handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(data))
                else:
                    # Run sync handlers in thread pool
                    tasks.append(asyncio.get_event_loop().run_in_executor(
                        None, handler, data
                    ))
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
        
        # Wait for all handlers to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    @asynccontextmanager
    async def get_db_session(self):
        """Get a database session context manager."""
        async with self.db_manager.get_session() as session:
            yield session
    
    async def create_task(self, task_data: Dict[str, Any]) -> TaskModel:
        """Create a new task in the system."""
        async with self.get_db_session() as session:
            task = TaskModel(**task_data)
            session.add(task)
            await session.flush()
            
            # Emit task created event
            await self.emit_event("task_created", {
                "task_id": str(task.id),
                "task_type": task.task_type,
                "task_data": task_data
            })
            
            return task
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[TaskModel]:
        """Update an existing task."""
        async with self.get_db_session() as session:
            task = await session.get(TaskModel, task_id)
            if not task:
                return None
            
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            await session.flush()
            
            # Emit task updated event
            await self.emit_event("task_updated", {
                "task_id": task_id,
                "updates": updates
            })
            
            return task
    
    async def create_project(self, project_data: Dict[str, Any]) -> ProjectModel:
        """Create a new project in the system."""
        async with self.get_db_session() as session:
            project = ProjectModel(**project_data)
            session.add(project)
            await session.flush()
            
            # Emit project created event
            await self.emit_event("project_created", {
                "project_id": str(project.id),
                "project_data": project_data
            })
            
            return project
    
    async def log_event(self, event_data: Dict[str, Any]) -> EventModel:
        """Log an event in the system."""
        async with self.get_db_session() as session:
            event = EventModel(**event_data)
            session.add(event)
            await session.flush()
            
            return event
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {},
            "performance": {}
        }
        
        try:
            # Check database health
            async with self.get_db_session() as session:
                # Simple query to test database connectivity
                result = await session.execute("SELECT 1")
                health_data["components"]["database"] = "healthy"
        except Exception as e:
            health_data["components"]["database"] = f"unhealthy: {e}"
            health_data["status"] = "degraded"
        
        # Get performance metrics
        if hasattr(self.performance_monitor, 'get_current_metrics'):
            try:
                metrics = await self.performance_monitor.get_current_metrics()
                health_data["performance"] = metrics
            except Exception as e:
                logger.error(f"Error getting performance metrics: {e}")
        
        return health_data
    
    async def process_with_monitoring(self, operation_name: str, operation: callable, *args, **kwargs) -> Any:
        """Execute an operation with performance monitoring and error handling."""
        start_time = datetime.utcnow()
        
        try:
            # Start performance monitoring
            monitor_context = self.performance_monitor.start_operation(operation_name)
            
            # Execute the operation
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            
            # Record success metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self.performance_monitor.record_operation(
                operation_name, duration, success=True
            )
            
            return result
            
        except Exception as e:
            # Record failure metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self.performance_monitor.record_operation(
                operation_name, duration, success=False, error=str(e)
            )
            
            # Handle the error
            await self.error_handler.handle_error(e, {
                "operation": operation_name,
                "args": args,
                "kwargs": kwargs,
                "duration": duration
            })
            
            raise
    
    def is_initialized(self) -> bool:
        """Check if the orchestrator is initialized."""
        return self._initialized

