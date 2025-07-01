import logging
from typing import Any, Callable, TypeVar, Optional

from pydantic import BaseModel

from contexten.extensions.events.interface import EventHandlerManagerProtocol
from contexten.extensions.Linear.types import LinearEvent
from contexten.extensions.Linear.config import get_linear_config
from contexten.extensions.Linear.integration_agent import LinearIntegrationAgent
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class Linear(EventHandlerManagerProtocol):
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}
        
        # Initialize comprehensive Linear integration
        self.config = get_linear_config()
        self.integration_agent: Optional[LinearIntegrationAgent] = None
        
        # Initialize agent if enabled
        if self.config.enabled:
            try:
                self.integration_agent = LinearIntegrationAgent(self.config)
                logger.info("Comprehensive Linear integration initialized")
            except Exception as e:
                logger.error(f"Failed to initialize comprehensive Linear integration: {e}")
                self.integration_agent = None
        else:
            logger.info("Linear integration is disabled")

    async def initialize_agent(self) -> bool:
        """Initialize the integration agent"""
        if not self.integration_agent:
            return False
        
        try:
            success = await self.integration_agent.initialize()
            if success:
                await self.integration_agent.start_monitoring()
                logger.info("Linear integration agent started successfully")
            return success
        except Exception as e:
            logger.error(f"Failed to initialize Linear integration agent: {e}")
            return False

    def unsubscribe_all_handlers(self):
        logger.info("[HANDLERS] Clearing all handlers")
        self.registered_handlers.clear()

    def event(self, event_name: str):
        """Decorator for registering a Linear event handler.

        Args:
            event_name: The type of event to handle (e.g. 'Issue', 'Comment')
        """
        logger.info(f"[EVENT] Registering handler for {event_name}")

        def register_handler(func: Callable[[LinearEvent], Any]):
            func_name = func.__qualname__
            logger.info(f"[EVENT] Registering function {func_name} for {event_name}")

            def new_func(raw_event: dict):
                # Get event type from payload
                event_type = raw_event.get("type")
                if event_type != event_name:
                    logger.info(f"[HANDLER] Event type mismatch: expected {event_name}, got {event_type}")
                    return None

                # Parse event into LinearEvent type
                event = LinearEvent.model_validate(raw_event)
                return func(event)

            self.registered_handlers[event_name] = new_func
            return func

        return register_handler

    async def handle(self, event: dict) -> dict:
        """Handle incoming Linear events.

        Args:
            event: The event payload from Linear

        Returns:
            Response dictionary
        """
        logger.info("[HANDLER] Handling Linear event")

        try:
            # First, try to process with comprehensive integration agent
            if self.integration_agent:
                try:
                    success = await self.integration_agent.process_event_directly(event)
                    if success:
                        logger.info("[HANDLER] Event processed by comprehensive integration")
                    else:
                        logger.warning("[HANDLER] Comprehensive integration failed to process event")
                except Exception as e:
                    logger.error(f"[HANDLER] Error in comprehensive integration: {e}")
            
            # Then process with legacy handlers for backward compatibility
            event_type = event.get("type")
            if not event_type:
                logger.info("[HANDLER] No event type found in payload")
                return {"message": "Event type not found"}

            if event_type not in self.registered_handlers:
                logger.info(f"[HANDLER] No legacy handler found for event type: {event_type}")
                return {"message": "Event handled successfully"}
            else:
                logger.info(f"[HANDLER] Handling event with legacy handler: {event_type}")
                handler = self.registered_handlers[event_type]
                result = handler(event)
                if hasattr(result, "__await__"):
                    result = await result
                return result

        except Exception as e:
            logger.exception(f"Error handling Linear event: {e}")
            return {"error": f"Failed to handle event: {e!s}"}

    async def get_integration_status(self) -> dict:
        """Get status of the Linear integration"""
        if not self.integration_agent:
            return {
                "enabled": self.config.enabled,
                "comprehensive_integration": False,
                "status": "disabled" if not self.config.enabled else "not_initialized"
            }
        
        try:
            status = await self.integration_agent.get_integration_status()
            return {
                "enabled": self.config.enabled,
                "comprehensive_integration": True,
                "status": "running" if status.initialized else "failed",
                "initialized": status.initialized,
                "monitoring_active": status.monitoring_active,
                "last_sync": status.last_sync.isoformat() if status.last_sync else None,
                "active_tasks": status.active_tasks,
                "processed_events": status.processed_events,
                "failed_events": status.failed_events,
                "last_error": status.last_error
            }
        except Exception as e:
            logger.error(f"Error getting integration status: {e}")
            return {
                "enabled": self.config.enabled,
                "comprehensive_integration": True,
                "status": "error",
                "error": str(e)
            }

    async def get_metrics(self) -> dict:
        """Get comprehensive integration metrics"""
        if not self.integration_agent:
            return {"error": "Integration agent not available"}
        
        try:
            metrics = await self.integration_agent.get_metrics()
            return {
                "status": {
                    "initialized": metrics.status.initialized,
                    "monitoring_active": metrics.status.monitoring_active,
                    "active_tasks": metrics.status.active_tasks,
                    "processed_events": metrics.status.processed_events,
                    "failed_events": metrics.status.failed_events
                },
                "client_stats": {
                    "requests_made": metrics.client_stats.requests_made,
                    "requests_successful": metrics.client_stats.requests_successful,
                    "requests_failed": metrics.client_stats.requests_failed,
                    "cache_hits": metrics.client_stats.cache_hits,
                    "cache_misses": metrics.client_stats.cache_misses,
                    "uptime_seconds": metrics.client_stats.uptime_seconds
                },
                "webhook_stats": {
                    "requests_made": metrics.webhook_stats.requests_made,
                    "requests_successful": metrics.webhook_stats.requests_successful,
                    "requests_failed": metrics.webhook_stats.requests_failed,
                    "uptime_seconds": metrics.webhook_stats.uptime_seconds
                },
                "assignment_stats": {
                    "requests_made": metrics.assignment_stats.requests_made,
                    "requests_successful": metrics.assignment_stats.requests_successful,
                    "requests_failed": metrics.assignment_stats.requests_failed,
                    "uptime_seconds": metrics.assignment_stats.uptime_seconds
                },
                "workflow_stats": {
                    "requests_made": metrics.workflow_stats.requests_made,
                    "requests_successful": metrics.workflow_stats.requests_successful,
                    "requests_failed": metrics.workflow_stats.requests_failed,
                    "uptime_seconds": metrics.workflow_stats.uptime_seconds
                },
                "collected_at": metrics.collected_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup Linear integration resources"""
        if self.integration_agent:
            try:
                await self.integration_agent.cleanup()
                logger.info("Linear integration cleanup completed")
            except Exception as e:
                logger.error(f"Error during Linear integration cleanup: {e}")

    # Backward compatibility methods
    async def sync_with_linear(self) -> bool:
        """Sync with Linear (backward compatibility)"""
        if self.integration_agent:
            return await self.integration_agent.sync_with_linear()
        return False

    def get_active_tasks(self) -> dict:
        """Get active tasks (backward compatibility)"""
        if self.integration_agent:
            return self.integration_agent.workflow_automation.get_active_tasks()
        return {}

    async def handle_webhook(self, payload: bytes, signature: str, headers: dict = None) -> bool:
        """Handle webhook (backward compatibility)"""
        if self.integration_agent:
            return await self.integration_agent.handle_webhook(payload, signature, headers)
        return False
