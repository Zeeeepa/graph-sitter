"""
GitHub webhook handler for PR static analysis.

This module provides a handler for GitHub webhook events,
specifically for PR events that trigger static analysis.
"""

import hashlib
import hmac
import json
from typing import Any, Callable, Dict, List, Optional, Union

from graph_sitter.git.clients.github_api_client import GitHubAPIClient
from graph_sitter.git.models.pull_request_context import PullRequestContext
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class WebhookHandler:
    """
    Handler for GitHub webhook events.
    
    This class processes GitHub webhook events, validates them,
    and routes them to the appropriate handlers based on event type.
    """
    
    _github_client: GitHubAPIClient
    _webhook_secret: str
    _event_handlers: Dict[str, List[Callable]]
    
    def __init__(
        self, 
        github_client: GitHubAPIClient,
        webhook_secret: str
    ):
        """
        Initialize the webhook handler.
        
        Args:
            github_client: GitHub API client
            webhook_secret: Secret for validating webhook signatures
        """
        self._github_client = github_client
        self._webhook_secret = webhook_secret
        self._event_handlers = {}
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: GitHub event type (e.g., "pull_request")
            handler: Function to call when event is received
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
    
    def validate_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate the webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: Signature from GitHub (X-Hub-Signature-256 header)
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not signature.startswith("sha256="):
            logger.warning("Invalid signature format")
            return False
        
        signature = signature[7:]  # Remove "sha256=" prefix
        
        # Calculate expected signature
        mac = hmac.new(
            self._webhook_secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256
        )
        expected_signature = mac.hexdigest()
        
        # Compare signatures using constant-time comparison
        return hmac.compare_digest(signature, expected_signature)
    
    def handle_webhook(
        self, 
        headers: Dict[str, str], 
        payload: bytes
    ) -> Dict[str, Any]:
        """
        Handle a webhook request.
        
        Args:
            headers: HTTP headers
            payload: Raw webhook payload
            
        Returns:
            Response data
        """
        # Validate signature
        signature = headers.get("X-Hub-Signature-256", "")
        if not self.validate_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            return {"status": "error", "message": "Invalid signature"}
        
        # Parse event type and payload
        event_type = headers.get("X-GitHub-Event", "")
        if not event_type:
            logger.warning("Missing event type")
            return {"status": "error", "message": "Missing event type"}
        
        try:
            data = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            return {"status": "error", "message": "Invalid JSON payload"}
        
        # Process event
        return self._process_event(event_type, data)
    
    def _process_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook event.
        
        Args:
            event_type: GitHub event type
            data: Event data
            
        Returns:
            Response data
        """
        logger.info(f"Processing {event_type} event")
        
        # Check if we have handlers for this event type
        handlers = self._event_handlers.get(event_type, [])
        if not handlers:
            logger.info(f"No handlers registered for event type: {event_type}")
            return {"status": "success", "message": "Event ignored (no handlers)"}
        
        # Call handlers
        results = []
        for handler in handlers:
            try:
                result = handler(data)
                results.append({"status": "success", "result": result})
            except Exception as e:
                logger.error(f"Error in handler for {event_type}: {e}")
                results.append({"status": "error", "error": str(e)})
        
        return {
            "status": "success", 
            "message": f"Processed {event_type} event",
            "results": results
        }
    
    def handle_pull_request_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a pull request event.
        
        Args:
            data: Event data
            
        Returns:
            Response data
        """
        action = data.get("action", "")
        pr_data = data.get("pull_request", {})
        
        # Only process certain actions
        if action not in ["opened", "reopened", "synchronize"]:
            logger.info(f"Ignoring pull_request.{action} event")
            return {"status": "ignored", "action": action}
        
        # Convert to PullRequestContext
        pr_context = PullRequestContext.from_payload(data)
        
        # Get repository information
        repo_name = data.get("repository", {}).get("full_name", "")
        if not repo_name:
            logger.warning("Missing repository name in webhook payload")
            return {"status": "error", "message": "Missing repository name"}
        
        return {
            "status": "success",
            "action": action,
            "pr_number": pr_context.number,
            "repository": repo_name,
            "pr_context": pr_context
        }


class WebhookServer:
    """
    Simple webhook server for local development.
    
    This class provides a simple HTTP server for receiving
    GitHub webhook events during local development.
    """
    
    _webhook_handler: WebhookHandler
    _port: int
    
    def __init__(self, webhook_handler: WebhookHandler, port: int = 8000):
        """
        Initialize the webhook server.
        
        Args:
            webhook_handler: Webhook handler
            port: Port to listen on
        """
        self._webhook_handler = webhook_handler
        self._port = port
    
    def start(self) -> None:
        """
        Start the webhook server.
        
        This method starts a simple HTTP server that listens for
        GitHub webhook events and passes them to the webhook handler.
        """
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class WebhookRequestHandler(BaseHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                self.webhook_handler = webhook_handler
                super().__init__(*args, **kwargs)
            
            def do_POST(self):
                # Read request body
                content_length = int(self.headers.get("Content-Length", 0))
                payload = self.rfile.read(content_length)
                
                # Process webhook
                response = self.webhook_handler.handle_webhook(dict(self.headers), payload)
                
                # Send response
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))
        
        # Create server
        webhook_handler = self._webhook_handler
        server = HTTPServer(("", self._port), WebhookRequestHandler)
        
        logger.info(f"Starting webhook server on port {self._port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Stopping webhook server")
            server.server_close()

