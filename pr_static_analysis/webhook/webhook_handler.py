import json
import logging
import hmac
import hashlib
from typing import Dict, Any, Callable, Optional, List, Union
from fastapi import Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Handler for GitHub webhook events.
    """
    
    def __init__(self, secret: Optional[str] = None):
        """
        Initialize the webhook handler.
        
        Args:
            secret: GitHub webhook secret for signature verification
        """
        self.secret = secret
        self.event_handlers = {}
    
    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: Type of event to handle (e.g., "pull_request", "push")
            handler: Function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the webhook signature.
        
        Args:
            payload: Raw request payload
            signature: Signature from the X-Hub-Signature-256 header
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not self.secret:
            # If no secret is configured, skip verification
            return True
        
        if not signature:
            logger.warning("No signature provided")
            return False
        
        # Remove 'sha256=' prefix
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        # Calculate expected signature
        mac = hmac.new(self.secret.encode(), msg=payload, digestmod=hashlib.sha256)
        expected = mac.hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected, signature)
    
    async def handle_webhook(self, request: Request) -> JSONResponse:
        """
        Handle a webhook request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            JSONResponse: Response to the webhook
        """
        # Get event type from headers
        event_type = request.headers.get("X-GitHub-Event")
        if not event_type:
            logger.warning("No event type provided")
            raise HTTPException(status_code=400, detail="No event type provided")
        
        # Get signature from headers
        signature = request.headers.get("X-Hub-Signature-256")
        
        # Read and parse payload
        payload_bytes = await request.body()
        
        # Verify signature if secret is configured
        if self.secret and not self.verify_signature(payload_bytes, signature):
            logger.warning("Invalid signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse payload
        try:
            payload = json.loads(payload_bytes)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON payload")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Get action from payload
        action = payload.get("action")
        
        # Route event to appropriate handlers
        result = await self.route_event(event_type, action, payload)
        
        return JSONResponse(content={"status": "success", "event": event_type, "action": action, "result": result})
    
    async def route_event(self, event_type: str, action: Optional[str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route an event to the appropriate handlers.
        
        Args:
            event_type: Type of event (e.g., "pull_request", "push")
            action: Action of the event (e.g., "opened", "synchronize")
            payload: Event payload
            
        Returns:
            Dict[str, Any]: Results from the handlers
        """
        results = {}
        
        # Validate event data
        if not self.validate_event(payload):
            logger.warning("Invalid event data")
            return {"error": "Invalid event data"}
        
        # Handle specific event type
        if event_type == "pull_request":
            results = await self.handle_pr_event(payload)
        elif event_type == "push":
            results = await self.handle_push_event(payload)
        elif event_type == "pull_request_review":
            results = await self.handle_review_event(payload)
        
        # Call registered handlers
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler_result = handler(payload)
                    results[handler.__name__] = handler_result
                except Exception as e:
                    logger.exception(f"Error in handler {handler.__name__}: {e}")
                    results[handler.__name__] = {"error": str(e)}
        
        # Call handlers for specific event type and action
        if action and f"{event_type}.{action}" in self.event_handlers:
            for handler in self.event_handlers[f"{event_type}.{action}"]:
                try:
                    handler_result = handler(payload)
                    results[handler.__name__] = handler_result
                except Exception as e:
                    logger.exception(f"Error in handler {handler.__name__}: {e}")
                    results[handler.__name__] = {"error": str(e)}
        
        return results
    
    def validate_event(self, payload: Dict[str, Any]) -> bool:
        """
        Validate event data.
        
        Args:
            payload: Event payload
            
        Returns:
            bool: True if event data is valid, False otherwise
        """
        # Basic validation - ensure payload is not empty
        if not payload:
            return False
        
        # Ensure repository information is present
        if "repository" not in payload:
            return False
        
        return True
    
    async def handle_pr_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a pull request event.
        
        Args:
            payload: Event payload
            
        Returns:
            Dict[str, Any]: Results from handling the event
        """
        action = payload.get("action")
        pr_number = payload.get("number")
        
        logger.info(f"Handling PR event: {action} for PR #{pr_number}")
        
        # Additional processing can be added here
        
        return {
            "action": action,
            "pr_number": pr_number,
            "status": "processed"
        }
    
    async def handle_push_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a push event.
        
        Args:
            payload: Event payload
            
        Returns:
            Dict[str, Any]: Results from handling the event
        """
        ref = payload.get("ref")
        before = payload.get("before")
        after = payload.get("after")
        
        logger.info(f"Handling push event: {ref} from {before} to {after}")
        
        # Additional processing can be added here
        
        return {
            "ref": ref,
            "before": before,
            "after": after,
            "status": "processed"
        }
    
    async def handle_review_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a pull request review event.
        
        Args:
            payload: Event payload
            
        Returns:
            Dict[str, Any]: Results from handling the event
        """
        action = payload.get("action")
        pr_number = payload.get("pull_request", {}).get("number")
        
        logger.info(f"Handling review event: {action} for PR #{pr_number}")
        
        # Additional processing can be added here
        
        return {
            "action": action,
            "pr_number": pr_number,
            "status": "processed"
        }

