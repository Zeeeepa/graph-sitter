"""
CircleCI Integration for Contexten

Provides CircleCI webhook handling and build monitoring integration.
"""

import logging
import os
from typing import Any, Callable, Dict, Optional, TypeVar

from pydantic import BaseModel

from contexten.extensions.modal.interface import EventHandlerManagerProtocol
from contexten.extensions.circleci.client import CircleCIClient
from contexten.extensions.circleci.types import CircleCIEvent, CircleCIBuild, CircleCIWorkflow
from contexten.extensions.circleci.webhook_processor import WebhookProcessor
from contexten.extensions.circleci.integration_agent import CircleCIIntegrationAgent
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class CircleCI(EventHandlerManagerProtocol):
    """CircleCI integration for Contexten providing build monitoring and webhook handling."""
    
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}
        self._client: Optional[CircleCIClient] = None
        self.webhook_processor: Optional[WebhookProcessor] = None
        self.integration_agent: Optional[CircleCIIntegrationAgent] = None
        
        # Initialize components if API token is available
        if os.getenv("CIRCLECI_TOKEN"):
            try:
                self._client = CircleCIClient()
                self.webhook_processor = WebhookProcessor()
                self.integration_agent = CircleCIIntegrationAgent()
                logger.info("CircleCI integration initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CircleCI integration: {e}")
        else:
            logger.warning("CIRCLECI_TOKEN not set, CircleCI integration disabled")

    @property
    def client(self) -> CircleCIClient:
        """Get the CircleCI API client."""
        if not self._client:
            if not os.getenv("CIRCLECI_TOKEN"):
                msg = "CIRCLECI_TOKEN is not set"
                logger.exception(msg)
                raise ValueError(msg)
            self._client = CircleCIClient()
        return self._client

    def unsubscribe_all_handlers(self):
        """Clear all registered handlers."""
        logger.info("[HANDLERS] Clearing all CircleCI handlers")
        self.registered_handlers.clear()

    def event(self, event_name: str):
        """Decorator for registering a CircleCI event handler.

        Example:
            @app.circleci.event('workflow-completed')
            def handle_workflow_completed(event: CircleCIWorkflow):
                logger.info(f"Workflow {event.workflow_id} completed with status {event.status}")

            @app.circleci.event('job-completed')
            def handle_job_completed(event: dict):
                logger.info(f"Job completed: {event}")
        """
        def decorator(func: Callable[[T], Any]) -> Callable[[T], Any]:
            logger.info(f"[HANDLERS] Registering CircleCI handler for event: {event_name}")
            
            if event_name not in self.registered_handlers:
                self.registered_handlers[event_name] = []
            
            self.registered_handlers[event_name].append(func)
            return func
        
        return decorator

    async def handle(self, payload: dict, request=None) -> dict:
        """Handle incoming CircleCI webhook events."""
        try:
            logger.info(f"[CIRCLECI] Received webhook payload: {payload}")
            
            # Process the webhook using the webhook processor
            if self.webhook_processor:
                processed_event = await self.webhook_processor.process_webhook(payload)
                
                # Determine event type from the payload
                event_type = payload.get("type", "unknown")
                
                # Call registered handlers
                if event_type in self.registered_handlers:
                    for handler in self.registered_handlers[event_type]:
                        try:
                            await handler(processed_event)
                        except Exception as e:
                            logger.error(f"Error in CircleCI handler for {event_type}: {e}")
                
                return {"status": "success", "processed": True}
            else:
                logger.warning("CircleCI webhook processor not initialized")
                return {"status": "error", "message": "Webhook processor not available"}
                
        except Exception as e:
            logger.error(f"Failed to handle CircleCI webhook: {e}")
            return {"status": "error", "message": str(e)}

    async def get_project_builds(self, project_slug: str, limit: int = 10) -> list[CircleCIBuild]:
        """Get recent builds for a project."""
        if not self.client:
            raise ValueError("CircleCI client not initialized")
        
        try:
            builds = await self.client.get_project_builds(project_slug, limit=limit)
            return builds
        except Exception as e:
            logger.error(f"Failed to get project builds: {e}")
            raise

    async def get_workflow_status(self, workflow_id: str) -> CircleCIWorkflow:
        """Get workflow status by ID."""
        if not self.client:
            raise ValueError("CircleCI client not initialized")
        
        try:
            workflow = await self.client.get_workflow(workflow_id)
            return workflow
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            raise

    async def trigger_pipeline(self, project_slug: str, branch: str = "main", parameters: Dict[str, Any] = None) -> dict:
        """Trigger a new pipeline for a project."""
        if not self.client:
            raise ValueError("CircleCI client not initialized")
        
        try:
            result = await self.client.trigger_pipeline(project_slug, branch, parameters or {})
            logger.info(f"Triggered pipeline for {project_slug} on {branch}")
            return result
        except Exception as e:
            logger.error(f"Failed to trigger pipeline: {e}")
            raise

    def subscribe_handler_to_webhook(self, func_name: str, modal_app, event_name):
        """Subscribe a handler to webhook events (Modal integration)."""
        # Implementation for Modal integration if needed
        pass

    def unsubscribe_handler_to_webhook(self, func_name: str, modal_app, event_name):
        """Unsubscribe a handler from webhook events (Modal integration)."""
        # Implementation for Modal integration if needed
        pass

