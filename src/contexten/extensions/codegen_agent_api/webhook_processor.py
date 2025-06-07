"""
Webhook processor for Codegen Agent API extension.

Handles incoming webhooks from Codegen API and processes them for contexten integration.
"""

import logging
import hmac
import hashlib
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone
from flask import Flask, request, jsonify

from .types import WebhookEvent, WebhookEventType, IntegrationEvent
from .exceptions import WebhookError, ValidationError

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Processes incoming webhooks from Codegen API.
    
    Features:
    - Webhook signature verification
    - Event parsing and validation
    - Event routing to handlers
    - Integration with contexten event system
    """
    
    def __init__(self, secret: Optional[str] = None):
        """
        Initialize webhook processor.
        
        Args:
            secret: Optional webhook secret for signature verification
        """
        self.secret = secret
        self._event_handlers: Dict[WebhookEventType, List[Callable[[WebhookEvent], None]]] = {}
        self._raw_handlers: List[Callable[[Dict[str, Any]], None]] = []
        
        # Metrics
        self._webhooks_processed = 0
        self._webhooks_failed = 0
        self._signature_failures = 0
        
        logger.info("WebhookProcessor initialized")
    
    def register_handler(
        self, 
        event_type: WebhookEventType, 
        handler: Callable[[WebhookEvent], None]
    ) -> None:
        """
        Register a handler for a specific webhook event type.
        
        Args:
            event_type: Type of webhook event to handle
            handler: Function to call when event occurs
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        logger.info(f"Registered webhook handler for {event_type.value}")
    
    def register_raw_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a handler for raw webhook data (before parsing).
        
        Args:
            handler: Function to call with raw webhook data
        """
        self._raw_handlers.append(handler)
        logger.info("Registered raw webhook handler")
    
    def remove_handler(
        self, 
        event_type: WebhookEventType, 
        handler: Callable[[WebhookEvent], None]
    ) -> None:
        """Remove a specific handler."""
        if event_type in self._event_handlers:
            if handler in self._event_handlers[event_type]:
                self._event_handlers[event_type].remove(handler)
                logger.info(f"Removed webhook handler for {event_type.value}")
    
    def process_webhook(
        self, 
        payload: str, 
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process incoming webhook payload.
        
        Args:
            payload: Raw webhook payload (JSON string)
            signature: Optional webhook signature for verification
            headers: Optional HTTP headers
            
        Returns:
            Processing result
            
        Raises:
            WebhookError: If webhook processing fails
            ValidationError: If payload is invalid
        """
        try:
            # Verify signature if secret is configured
            if self.secret and signature:
                if not self._verify_signature(payload, signature):
                    self._signature_failures += 1
                    raise WebhookError("Invalid webhook signature")
            
            # Parse payload
            try:
                webhook_data = json.loads(payload)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON payload: {e}")
            
            # Call raw handlers first
            for handler in self._raw_handlers:
                try:
                    handler(webhook_data)
                except Exception as e:
                    logger.error(f"Raw webhook handler failed: {e}")
            
            # Parse webhook event
            webhook_event = self._parse_webhook_event(webhook_data, headers)
            
            # Route to specific handlers
            handlers = self._event_handlers.get(webhook_event.event_type, [])
            
            logger.info(f"Processing webhook {webhook_event.event_type.value} for task {webhook_event.task_id}")
            
            results = []
            for handler in handlers:
                try:
                    result = handler(webhook_event)
                    results.append({"handler": handler.__name__, "result": result})
                except Exception as e:
                    logger.error(f"Webhook handler {handler.__name__} failed: {e}")
                    results.append({"handler": handler.__name__, "error": str(e)})
            
            self._webhooks_processed += 1
            
            return {
                "status": "success",
                "event_type": webhook_event.event_type.value,
                "task_id": webhook_event.task_id,
                "handlers_called": len(handlers),
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self._webhooks_failed += 1
            logger.error(f"Webhook processing failed: {e}")
            raise WebhookError(f"Failed to process webhook: {e}")
    
    def _verify_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Raw payload string
            signature: Signature to verify
            
        Returns:
            True if signature is valid
        """
        if not self.secret:
            return True  # No secret configured, skip verification
        
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def _parse_webhook_event(
        self, 
        webhook_data: Dict[str, Any], 
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookEvent:
        """
        Parse raw webhook data into WebhookEvent.
        
        Args:
            webhook_data: Raw webhook data
            headers: Optional HTTP headers
            
        Returns:
            Parsed WebhookEvent
            
        Raises:
            ValidationError: If webhook data is invalid
        """
        try:
            # Extract event type
            event_type_str = webhook_data.get("event", webhook_data.get("event_type", ""))
            if not event_type_str:
                raise ValidationError("Missing event type in webhook data")
            
            try:
                event_type = WebhookEventType(event_type_str)
            except ValueError:
                raise ValidationError(f"Unknown event type: {event_type_str}")
            
            # Extract required fields
            task_id = webhook_data.get("task_id", webhook_data.get("data", {}).get("task_id", ""))
            if not task_id:
                raise ValidationError("Missing task_id in webhook data")
            
            org_id = webhook_data.get("org_id", webhook_data.get("data", {}).get("org_id", ""))
            if not org_id:
                raise ValidationError("Missing org_id in webhook data")
            
            # Extract timestamp
            timestamp_str = webhook_data.get("timestamp", webhook_data.get("created_at"))
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            
            # Create webhook event
            return WebhookEvent(
                event_type=event_type,
                task_id=task_id,
                org_id=org_id,
                timestamp=timestamp,
                data=webhook_data.get("data", webhook_data),
                webhook_id=webhook_data.get("webhook_id")
            )
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to parse webhook event: {e}")
    
    def create_flask_endpoint(self, app: Flask, endpoint: str = "/webhooks/codegen") -> None:
        """
        Create a Flask endpoint for receiving webhooks.
        
        Args:
            app: Flask application
            endpoint: Endpoint path
        """
        @app.route(endpoint, methods=['POST'])
        def handle_webhook():
            try:
                # Get payload and signature
                payload = request.get_data(as_text=True)
                signature = request.headers.get('X-Signature-256', request.headers.get('X-Hub-Signature-256'))
                headers = dict(request.headers)
                
                # Process webhook
                result = self.process_webhook(payload, signature, headers)
                
                return jsonify(result), 200
                
            except WebhookError as e:
                logger.error(f"Webhook error: {e}")
                return jsonify({"error": str(e)}), 400
            except ValidationError as e:
                logger.error(f"Validation error: {e}")
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return jsonify({"error": "Internal server error"}), 500
        
        logger.info(f"Created Flask webhook endpoint at {endpoint}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get webhook processing metrics."""
        total_webhooks = self._webhooks_processed + self._webhooks_failed
        success_rate = (self._webhooks_processed / max(total_webhooks, 1)) * 100
        
        return {
            "webhooks_processed": self._webhooks_processed,
            "webhooks_failed": self._webhooks_failed,
            "total_webhooks": total_webhooks,
            "success_rate": success_rate,
            "signature_failures": self._signature_failures,
            "handlers_registered": sum(len(handlers) for handlers in self._event_handlers.values()),
            "raw_handlers_registered": len(self._raw_handlers)
        }
    
    def get_handler_info(self) -> Dict[str, Any]:
        """Get information about registered handlers."""
        handler_info = {}
        
        for event_type, handlers in self._event_handlers.items():
            handler_info[event_type.value] = [
                {
                    "name": handler.__name__,
                    "module": handler.__module__,
                    "doc": handler.__doc__
                }
                for handler in handlers
            ]
        
        return {
            "event_handlers": handler_info,
            "raw_handlers": [
                {
                    "name": handler.__name__,
                    "module": handler.__module__,
                    "doc": handler.__doc__
                }
                for handler in self._raw_handlers
            ]
        }
    
    def test_webhook(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test webhook processing with sample data.
        
        Args:
            test_data: Test webhook data
            
        Returns:
            Test result
        """
        try:
            payload = json.dumps(test_data)
            result = self.process_webhook(payload)
            
            return {
                "status": "success",
                "test_result": result,
                "message": "Test webhook processed successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Test webhook processing failed"
            }
    
    def __str__(self) -> str:
        """String representation."""
        return f"WebhookProcessor(handlers={len(self._event_handlers)})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"WebhookProcessor(handlers={len(self._event_handlers)}, "
                f"processed={self._webhooks_processed}, failed={self._webhooks_failed})")


# Convenience functions for common webhook event handlers

def create_task_completion_handler(callback: Callable[[str, str], None]) -> Callable[[WebhookEvent], None]:
    """
    Create a handler for task completion events.
    
    Args:
        callback: Function to call with (task_id, result)
        
    Returns:
        Webhook event handler
    """
    def handler(event: WebhookEvent) -> None:
        if event.event_type == WebhookEventType.TASK_COMPLETED:
            result = event.data.get("result", "")
            callback(event.task_id, result)
    
    return handler


def create_task_failure_handler(callback: Callable[[str, str], None]) -> Callable[[WebhookEvent], None]:
    """
    Create a handler for task failure events.
    
    Args:
        callback: Function to call with (task_id, error)
        
    Returns:
        Webhook event handler
    """
    def handler(event: WebhookEvent) -> None:
        if event.event_type == WebhookEventType.TASK_FAILED:
            error = event.data.get("error", "Unknown error")
            callback(event.task_id, error)
    
    return handler


def create_progress_handler(callback: Callable[[str, Dict[str, Any]], None]) -> Callable[[WebhookEvent], None]:
    """
    Create a handler for task progress events.
    
    Args:
        callback: Function to call with (task_id, progress_data)
        
    Returns:
        Webhook event handler
    """
    def handler(event: WebhookEvent) -> None:
        if event.event_type == WebhookEventType.TASK_PROGRESS:
            progress = event.data.get("progress", {})
            callback(event.task_id, progress)
    
    return handler


# Export main classes and functions
__all__ = [
    "WebhookProcessor",
    "create_task_completion_handler",
    "create_task_failure_handler", 
    "create_progress_handler",
]

