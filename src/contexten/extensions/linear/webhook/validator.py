"""
Linear Webhook Validator

This module provides webhook signature validation for Linear webhooks.
"""

from typing import Dict, Optional, Any
import hashlib
import hmac
import json
import logging

from ....shared.logging.get_logger import get_logger

logger = get_logger(__name__)

class WebhookValidator:
    """Linear webhook signature validator"""
    
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret
    
    def validate_signature(self, payload: Dict[str, Any], signature: Optional[str] = None) -> bool:
        """Validate webhook signature"""
        if not self.secret or not signature:
            return True  # Skip validation if no secret configured
        
        try:
            # Convert payload to JSON string
            payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False

