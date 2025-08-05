"""Webhook service for GitHub and Linear event handling."""

import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from ..models.webhook import WebhookConfiguration, WebhookDelivery, WebhookEvent, WebhookEventType
from ..utils.cache import CacheManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WebhookService:
    """Service for managing webhooks and processing events."""
    
    def __init__(self):
        """Initialize webhook service."""
        self.cache = CacheManager()
        self.webhook_configs: Dict[str, WebhookConfiguration] = {}
        
    async def register_webhook(self, 
                             project_id: str,
                             webhook_url: str,
                             events: List[WebhookEventType],
                             secret: Optional[str] = None) -> WebhookConfiguration:
        """Register a webhook for a project.
        
        Args:
            project_id: Project ID to register webhook for
            webhook_url: URL to send webhook events to
            events: List of event types to subscribe to
            secret: Optional webhook secret for verification
            
        Returns:
            Webhook configuration object
        """
        config = WebhookConfiguration(
            project_id=project_id,
            webhook_url=webhook_url,
            events=events,
            secret=secret,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.webhook_configs[project_id] = config
        logger.info(f"Registered webhook for project {project_id}")
        
        return config
    
    async def unregister_webhook(self, project_id: str) -> bool:
        """Unregister a webhook for a project.
        
        Args:
            project_id: Project ID to unregister webhook for
            
        Returns:
            True if webhook was removed, False if not found
        """
        if project_id in self.webhook_configs:
            del self.webhook_configs[project_id]
            logger.info(f"Unregistered webhook for project {project_id}")
            return True
        return False
    
    async def process_github_webhook(self, 
                                   payload: Dict[str, Any],
                                   headers: Dict[str, str],
                                   project_id: Optional[str] = None) -> Optional[WebhookEvent]:
        """Process a GitHub webhook event.
        
        Args:
            payload: Webhook payload
            headers: Request headers
            project_id: Project ID (extracted from payload if not provided)
            
        Returns:
            Processed webhook event or None if invalid
        """
        try:
            # Extract event information
            event_type = headers.get("X-GitHub-Event")
            action = payload.get("action", "")
            
            # Determine project ID from payload if not provided
            if not project_id:
                repository = payload.get("repository", {})
                project_id = str(repository.get("id", ""))
                
            if not project_id or not event_type:
                logger.warning("Invalid GitHub webhook: missing project_id or event_type")
                return None
                
            # Verify webhook signature if secret is configured
            config = self.webhook_configs.get(project_id)
            if config and config.secret:
                signature = headers.get("X-Hub-Signature-256", "")
                if not self._verify_github_signature(payload, signature, config.secret):
                    logger.warning(f"Invalid GitHub webhook signature for project {project_id}")
                    return None
                    
            # Create webhook event
            event = WebhookEvent(
                id=f"gh_{project_id}_{datetime.utcnow().timestamp()}",
                event_type=WebhookEventType(event_type),
                action=action,
                repository_id=project_id,
                repository_name=payload.get("repository", {}).get("full_name", ""),
                sender=payload.get("sender", {}).get("login", ""),
                payload=payload,
                received_at=datetime.utcnow(),
            )
            
            # Process the event
            await self._process_webhook_event(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error processing GitHub webhook: {e}")
            return None
    
    async def process_linear_webhook(self, 
                                   payload: Dict[str, Any],
                                   headers: Dict[str, str]) -> Optional[WebhookEvent]:
        """Process a Linear webhook event.
        
        Args:
            payload: Webhook payload
            headers: Request headers
            
        Returns:
            Processed webhook event or None if invalid
        """
        try:
            # Extract event information
            event_type = payload.get("type", "")
            action = payload.get("action", "")
            data = payload.get("data", {})
            
            # Create webhook event
            event = WebhookEvent(
                id=f"linear_{datetime.utcnow().timestamp()}",
                event_type=WebhookEventType.ISSUES,  # Map Linear events to GitHub equivalents
                action=action,
                repository_id="linear",
                repository_name="Linear",
                sender=data.get("updatedBy", {}).get("name", ""),
                payload=payload,
                received_at=datetime.utcnow(),
            )
            
            # Process the event
            await self._process_webhook_event(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error processing Linear webhook: {e}")
            return None
    
    async def get_webhook_events(self, 
                               project_id: Optional[str] = None,
                               event_type: Optional[WebhookEventType] = None,
                               limit: int = 100) -> List[WebhookEvent]:
        """Get webhook events with optional filtering.
        
        Args:
            project_id: Filter by project ID
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of webhook events
        """
        cache_key = f"webhook_events_{project_id}_{event_type}_{limit}"
        cached_events = await self.cache.get(cache_key)
        
        if cached_events:
            return cached_events
            
        # In a real implementation, this would query a database
        # For now, return empty list
        events = []
        
        # Cache for 1 minute
        await self.cache.set(cache_key, events, ttl=60)
        return events
    
    async def get_webhook_config(self, project_id: str) -> Optional[WebhookConfiguration]:
        """Get webhook configuration for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Webhook configuration or None if not found
        """
        return self.webhook_configs.get(project_id)
    
    async def update_webhook_config(self, 
                                  project_id: str,
                                  webhook_url: Optional[str] = None,
                                  events: Optional[List[WebhookEventType]] = None,
                                  active: Optional[bool] = None) -> Optional[WebhookConfiguration]:
        """Update webhook configuration for a project.
        
        Args:
            project_id: Project ID
            webhook_url: New webhook URL
            events: New event types
            active: New active status
            
        Returns:
            Updated webhook configuration or None if not found
        """
        config = self.webhook_configs.get(project_id)
        if not config:
            return None
            
        if webhook_url:
            config.webhook_url = webhook_url
        if events:
            config.events = events
        if active is not None:
            config.active = active
            
        config.updated_at = datetime.utcnow()
        
        logger.info(f"Updated webhook config for project {project_id}")
        return config
    
    async def deliver_webhook(self, 
                            config: WebhookConfiguration,
                            event: WebhookEvent) -> WebhookDelivery:
        """Deliver a webhook event to the configured URL.
        
        Args:
            config: Webhook configuration
            event: Event to deliver
            
        Returns:
            Delivery result
        """
        delivery = WebhookDelivery(
            id=f"delivery_{event.id}_{datetime.utcnow().timestamp()}",
            webhook_config_id=config.project_id,
            event_id=event.id,
            url=config.webhook_url,
            payload=event.payload,
            delivered_at=datetime.utcnow(),
        )
        
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Graph-Sitter-Webhook/1.0",
                "X-Event-Type": event.event_type.value,
                "X-Event-Action": event.action,
            }
            
            # Add signature if secret is configured
            if config.secret:
                payload_str = json.dumps(event.payload)
                signature = self._generate_signature(payload_str, config.secret)
                headers["X-Hub-Signature-256"] = f"sha256={signature}"
                
            delivery.headers = headers
            
            start_time = datetime.utcnow()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.webhook_url,
                    json=event.payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    end_time = datetime.utcnow()
                    
                    delivery.status_code = response.status
                    delivery.response_headers = dict(response.headers)
                    delivery.response_body = await response.text()
                    delivery.response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                    delivery.success = 200 <= response.status < 300
                    
                    if not delivery.success:
                        delivery.error_message = f"HTTP {response.status}: {delivery.response_body}"
                        
        except Exception as e:
            delivery.success = False
            delivery.error_message = str(e)
            logger.error(f"Webhook delivery failed: {e}")
            
        # Update config statistics
        config.total_deliveries += 1
        config.last_delivery = delivery.delivered_at
        
        if delivery.success:
            config.successful_deliveries += 1
        else:
            config.failed_deliveries += 1
            
        return delivery
    
    async def _process_webhook_event(self, event: WebhookEvent) -> None:
        """Process a webhook event and trigger appropriate actions.
        
        Args:
            event: Webhook event to process
        """
        try:
            event.processing_status = "processing"
            
            # Get webhook configuration for the project
            config = self.webhook_configs.get(event.repository_id)
            
            if config and config.active and event.event_type in config.events:
                # Deliver webhook
                delivery = await self.deliver_webhook(config, event)
                logger.info(f"Webhook delivered: {delivery.success}")
                
            # Trigger notifications based on event type
            if event.notify_linear:
                await self._notify_linear(event)
                
            if event.notify_slack:
                await self._notify_slack(event)
                
            event.processing_status = "completed"
            event.processed_at = datetime.utcnow()
            
        except Exception as e:
            event.processing_status = "failed"
            event.error_message = str(e)
            logger.error(f"Error processing webhook event: {e}")
    
    async def _notify_linear(self, event: WebhookEvent) -> None:
        """Send notification to Linear about the webhook event.
        
        Args:
            event: Webhook event
        """
        # Implementation would integrate with Linear API
        # to create issues, comments, or updates
        logger.info(f"Linear notification for event {event.id}")
    
    async def _notify_slack(self, event: WebhookEvent) -> None:
        """Send notification to Slack about the webhook event.
        
        Args:
            event: Webhook event
        """
        # Implementation would integrate with Slack API
        # to send messages to channels
        logger.info(f"Slack notification for event {event.id}")
    
    def _verify_github_signature(self, payload: Dict[str, Any], signature: str, secret: str) -> bool:
        """Verify GitHub webhook signature.
        
        Args:
            payload: Webhook payload
            signature: Signature from headers
            secret: Webhook secret
            
        Returns:
            True if signature is valid
        """
        if not signature.startswith("sha256="):
            return False
            
        expected_signature = self._generate_signature(json.dumps(payload), secret)
        received_signature = signature[7:]  # Remove "sha256=" prefix
        
        return hmac.compare_digest(expected_signature, received_signature)
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload.
        
        Args:
            payload: Payload string
            secret: Webhook secret
            
        Returns:
            HMAC signature
        """
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

