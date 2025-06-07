"""
Integration agent for Codegen Agent API extension.

Provides contexten-specific integration components that connect the codegen functionality
with the broader contexten ecosystem.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone

from .config import CodegenAgentAPIConfig
from .client import OverlayClient
from .types import (
    IntegrationEvent, IntegrationStatus, ComponentStats, 
    CodegenAgentAPIMetrics, WebhookEvent, WebhookEventType
)
from .exceptions import IntegrationError, WebhookError

logger = logging.getLogger(__name__)


class CodegenIntegrationAgent:
    """
    Integration agent that connects codegen functionality with the contexten ecosystem.
    
    Provides:
    - Event handling and webhook processing
    - Integration with other contexten extensions
    - Metrics collection and monitoring
    - Workflow automation
    """
    
    def __init__(self, config: CodegenAgentAPIConfig):
        """
        Initialize the integration agent.
        
        Args:
            config: Extension configuration
        """
        self.config = config
        self.overlay_client = OverlayClient(config)
        
        # Integration state
        self._start_time = time.time()
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._webhook_handlers: Dict[WebhookEventType, List[Callable]] = {}
        self._integration_status: Dict[str, IntegrationStatus] = {}
        self._component_stats: Dict[str, ComponentStats] = {}
        
        # Metrics
        self._events_processed = 0
        self._webhooks_processed = 0
        self._integration_errors = 0
        
        logger.info("CodegenIntegrationAgent initialized")
        
        # Initialize component stats
        self._initialize_component_stats()
    
    def _initialize_component_stats(self) -> None:
        """Initialize component statistics."""
        components = [
            "overlay_client",
            "event_processor", 
            "webhook_processor",
            "metrics_collector",
            "integration_manager"
        ]
        
        for component in components:
            self._component_stats[component] = {
                "component_name": component,
                "uptime_seconds": 0.0,
                "operation_count": 0,
                "error_count": 0,
                "last_operation": None
            }
    
    def register_event_handler(self, event_type: str, handler: Callable[[IntegrationEvent], None]) -> None:
        """
        Register an event handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when event occurs
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for {event_type}")
    
    def register_webhook_handler(
        self, 
        webhook_event: WebhookEventType, 
        handler: Callable[[WebhookEvent], None]
    ) -> None:
        """
        Register a webhook handler for a specific webhook event type.
        
        Args:
            webhook_event: Type of webhook event to handle
            handler: Function to call when webhook event occurs
        """
        if webhook_event not in self._webhook_handlers:
            self._webhook_handlers[webhook_event] = []
        
        self._webhook_handlers[webhook_event].append(handler)
        logger.info(f"Registered webhook handler for {webhook_event.value}")
    
    def emit_event(self, event: IntegrationEvent) -> None:
        """
        Emit an integration event to registered handlers.
        
        Args:
            event: Event to emit
        """
        try:
            self._update_component_stats("event_processor")
            
            event_type = event["event_type"]
            handlers = self._event_handlers.get(event_type, [])
            
            logger.debug(f"Emitting event {event_type} to {len(handlers)} handlers")
            
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Event handler failed for {event_type}: {e}")
                    self._integration_errors += 1
            
            self._events_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
            self._integration_errors += 1
            self._component_stats["event_processor"]["error_count"] += 1
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> None:
        """
        Process incoming webhook data.
        
        Args:
            webhook_data: Raw webhook data
        """
        try:
            self._update_component_stats("webhook_processor")
            
            # Parse webhook event
            webhook_event = self._parse_webhook_event(webhook_data)
            
            # Get handlers for this event type
            handlers = self._webhook_handlers.get(webhook_event.event_type, [])
            
            logger.debug(f"Processing webhook {webhook_event.event_type.value} to {len(handlers)} handlers")
            
            for handler in handlers:
                try:
                    handler(webhook_event)
                except Exception as e:
                    logger.error(f"Webhook handler failed for {webhook_event.event_type.value}: {e}")
                    self._integration_errors += 1
            
            self._webhooks_processed += 1
            
            # Emit integration event
            integration_event: IntegrationEvent = {
                "event_type": "webhook_received",
                "source": "codegen_agent_api",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "webhook_event_type": webhook_event.event_type.value,
                    "task_id": webhook_event.task_id,
                    "org_id": webhook_event.org_id
                }
            }
            self.emit_event(integration_event)
            
        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")
            self._integration_errors += 1
            self._component_stats["webhook_processor"]["error_count"] += 1
            raise WebhookError(f"Failed to process webhook: {e}")
    
    def _parse_webhook_event(self, webhook_data: Dict[str, Any]) -> WebhookEvent:
        """Parse raw webhook data into WebhookEvent."""
        try:
            event_type_str = webhook_data.get("event_type", "")
            event_type = WebhookEventType(event_type_str)
            
            return WebhookEvent(
                event_type=event_type,
                task_id=webhook_data.get("task_id", ""),
                org_id=webhook_data.get("org_id", ""),
                timestamp=datetime.now(timezone.utc),
                data=webhook_data.get("data", {}),
                webhook_id=webhook_data.get("webhook_id")
            )
            
        except (ValueError, KeyError) as e:
            raise WebhookError(f"Invalid webhook data: {e}")
    
    def create_agent(self, **kwargs) -> Any:
        """Create an Agent instance using overlay functionality."""
        try:
            self._update_component_stats("overlay_client")
            agent = self.overlay_client.create_agent(**kwargs)
            
            # Emit integration event
            integration_event: IntegrationEvent = {
                "event_type": "agent_created",
                "source": "codegen_agent_api",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "org_id": kwargs.get("org_id", self.config.org_id),
                    "overlay_strategy": self.overlay_client.strategy.value
                }
            }
            self.emit_event(integration_event)
            
            return agent
            
        except Exception as e:
            self._component_stats["overlay_client"]["error_count"] += 1
            raise
    
    def create_codebase_ai(self, **kwargs) -> Any:
        """Create a CodebaseAI instance using overlay functionality."""
        try:
            self._update_component_stats("overlay_client")
            codebase_ai = self.overlay_client.create_codebase_ai(**kwargs)
            
            # Emit integration event
            integration_event: IntegrationEvent = {
                "event_type": "codebase_ai_created",
                "source": "codegen_agent_api",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "org_id": kwargs.get("org_id", self.config.org_id),
                    "overlay_strategy": self.overlay_client.strategy.value
                }
            }
            self.emit_event(integration_event)
            
            return codebase_ai
            
        except Exception as e:
            self._component_stats["overlay_client"]["error_count"] += 1
            raise
    
    def get_integration_status(self) -> List[IntegrationStatus]:
        """Get status of all integrations."""
        self._update_component_stats("integration_manager")
        
        # Update overlay integration status
        overlay_info = self.overlay_client.get_overlay_info()
        self._integration_status["overlay"] = {
            "name": "overlay",
            "active": overlay_info["pip_available"] or overlay_info["local_available"],
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "error_count": self.overlay_client._overlay_errors,
            "success_count": self.overlay_client._pip_calls + self.overlay_client._local_calls
        }
        
        # Update event processing status
        self._integration_status["event_processing"] = {
            "name": "event_processing",
            "active": True,
            "last_activity": datetime.now(timezone.utc).isoformat() if self._events_processed > 0 else None,
            "error_count": self._integration_errors,
            "success_count": self._events_processed
        }
        
        # Update webhook processing status
        self._integration_status["webhook_processing"] = {
            "name": "webhook_processing",
            "active": True,
            "last_activity": datetime.now(timezone.utc).isoformat() if self._webhooks_processed > 0 else None,
            "error_count": self._component_stats["webhook_processor"]["error_count"],
            "success_count": self._webhooks_processed
        }
        
        return list(self._integration_status.values())
    
    def get_component_stats(self) -> List[ComponentStats]:
        """Get statistics for all components."""
        self._update_component_stats("metrics_collector")
        
        # Update uptime for all components
        current_time = time.time()
        for stats in self._component_stats.values():
            stats["uptime_seconds"] = current_time - self._start_time
        
        return list(self._component_stats.values())
    
    def get_metrics(self) -> CodegenAgentAPIMetrics:
        """Get comprehensive extension metrics."""
        overlay_info = self.overlay_client.get_overlay_info()
        overlay_metrics = self.overlay_client.get_metrics()
        
        # Create agent metrics (if we have an agent instance)
        agent_metrics = {
            "start_time": self._start_time,
            "request_count": 0,
            "error_count": 0,
            "rate_limit_count": 0,
            "last_request_time": None,
            "rate_limit_reset_time": None
        }
        
        # Create extension metrics
        extension_metrics = {
            "overlay_strategy": overlay_metrics["strategy"],
            "pip_calls": overlay_metrics["pip_calls"],
            "local_calls": overlay_metrics["local_calls"],
            "fallback_count": overlay_metrics["fallback_count"],
            "overlay_errors": overlay_metrics["overlay_errors"]
        }
        
        return {
            "extension_name": "codegen_agent_api",
            "version": "1.0.0",
            "uptime_seconds": time.time() - self._start_time,
            "overlay_info": overlay_info,
            "agent_metrics": agent_metrics,
            "extension_metrics": extension_metrics,
            "integration_status": self.get_integration_status(),
            "component_stats": self.get_component_stats()
        }
    
    def _update_component_stats(self, component_name: str) -> None:
        """Update statistics for a component."""
        if component_name in self._component_stats:
            stats = self._component_stats[component_name]
            stats["operation_count"] += 1
            stats["last_operation"] = datetime.now(timezone.utc).isoformat()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        health_status = {
            "overall": "healthy",
            "components": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Check overlay client
        try:
            overlay_info = self.overlay_client.get_overlay_info()
            health_status["components"]["overlay_client"] = {
                "status": "healthy" if overlay_info["pip_available"] or overlay_info["local_available"] else "degraded",
                "details": overlay_info
            }
        except Exception as e:
            health_status["components"]["overlay_client"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "degraded"
        
        # Check event processing
        health_status["components"]["event_processing"] = {
            "status": "healthy",
            "events_processed": self._events_processed,
            "handlers_registered": sum(len(handlers) for handlers in self._event_handlers.values())
        }
        
        # Check webhook processing
        health_status["components"]["webhook_processing"] = {
            "status": "healthy",
            "webhooks_processed": self._webhooks_processed,
            "handlers_registered": sum(len(handlers) for handlers in self._webhook_handlers.values())
        }
        
        return health_status
    
    def shutdown(self) -> None:
        """Shutdown the integration agent."""
        logger.info("Shutting down CodegenIntegrationAgent")
        
        # Emit shutdown event
        integration_event: IntegrationEvent = {
            "event_type": "integration_shutdown",
            "source": "codegen_agent_api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "uptime_seconds": time.time() - self._start_time,
                "events_processed": self._events_processed,
                "webhooks_processed": self._webhooks_processed
            }
        }
        self.emit_event(integration_event)
        
        # Clear handlers
        self._event_handlers.clear()
        self._webhook_handlers.clear()
        
        logger.info("CodegenIntegrationAgent shutdown complete")
    
    def __str__(self) -> str:
        """String representation."""
        return f"CodegenIntegrationAgent(org_id={self.config.org_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"CodegenIntegrationAgent(org_id={self.config.org_id}, "
                f"events={self._events_processed}, webhooks={self._webhooks_processed})")


def create_integration_agent(config: Optional[CodegenAgentAPIConfig] = None, **kwargs) -> CodegenIntegrationAgent:
    """
    Create a CodegenIntegrationAgent instance.
    
    Args:
        config: Optional configuration (will use default if not provided)
        **kwargs: Additional configuration overrides
        
    Returns:
        CodegenIntegrationAgent instance
    """
    if config is None:
        from .config import get_codegen_config
        config = get_codegen_config(**kwargs)
    
    return CodegenIntegrationAgent(config)


# Export main classes and functions
__all__ = [
    "CodegenIntegrationAgent",
    "create_integration_agent",
]

