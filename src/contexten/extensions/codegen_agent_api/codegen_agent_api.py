"""
Main Codegen Agent API extension class.

Provides the primary interface for the codegen agent API extension with overlay functionality.
"""

import logging
from typing import Dict, Any, Optional, Union, List

from .config import CodegenAgentAPIConfig, get_codegen_config
from .client import OverlayClient
from .integration_agent import CodegenIntegrationAgent
from .webhook_processor import WebhookProcessor
from .types import CodegenAgentAPIMetrics, OverlayInfo
from .exceptions import ConfigurationError, ExtensionError

logger = logging.getLogger(__name__)


class CodegenAgentAPI:
    """
    Main Codegen Agent API extension class.
    
    Provides a unified interface for:
    - Agent and CodebaseAI creation with overlay functionality
    - Integration with contexten ecosystem
    - Webhook processing
    - Configuration management
    - Metrics and monitoring
    """
    
    def __init__(
        self, 
        config: Optional[CodegenAgentAPIConfig] = None,
        **config_kwargs
    ):
        """
        Initialize the Codegen Agent API extension.
        
        Args:
            config: Optional configuration object
            **config_kwargs: Configuration parameters (if config not provided)
        """
        # Get or create configuration
        if config is None:
            try:
                self.config = get_codegen_config(**config_kwargs)
            except Exception as e:
                raise ConfigurationError(f"Failed to create configuration: {e}")
        else:
            self.config = config
        
        # Initialize components
        try:
            self.overlay_client = OverlayClient(self.config)
            self.integration_agent = CodegenIntegrationAgent(self.config)
            
            # Initialize webhook processor if webhook settings are configured
            webhook_secret = self.config.webhook_secret
            self.webhook_processor = WebhookProcessor(secret=webhook_secret)
            
            # Connect webhook processor to integration agent
            self._setup_webhook_integration()
            
        except Exception as e:
            raise ExtensionError(f"Failed to initialize extension components: {e}")
        
        logger.info(f"CodegenAgentAPI extension initialized for org {self.config.org_id}")
    
    def _setup_webhook_integration(self) -> None:
        """Set up integration between webhook processor and integration agent."""
        # Register webhook processor with integration agent
        self.integration_agent.register_event_handler(
            "webhook_received",
            self._handle_webhook_event
        )
        
        # Register webhook handlers for common events
        from .types import WebhookEventType
        
        for event_type in WebhookEventType:
            self.webhook_processor.register_handler(
                event_type,
                lambda event: self.integration_agent.process_webhook(event.__dict__)
            )
    
    def _handle_webhook_event(self, event: Dict[str, Any]) -> None:
        """Handle webhook events from integration agent."""
        logger.debug(f"Handling webhook event: {event['event_type']}")
    
    def create_agent(self, **kwargs) -> Any:
        """
        Create an Agent instance using overlay functionality.
        
        Args:
            **kwargs: Additional arguments for Agent constructor
            
        Returns:
            Agent instance from active implementation
        """
        return self.integration_agent.create_agent(**kwargs)
    
    def create_codebase_ai(self, **kwargs) -> Any:
        """
        Create a CodebaseAI instance using overlay functionality.
        
        Args:
            **kwargs: Additional arguments for CodebaseAI constructor
            
        Returns:
            CodebaseAI instance from active implementation
        """
        return self.integration_agent.create_codebase_ai(**kwargs)
    
    def get_overlay_info(self) -> OverlayInfo:
        """Get information about the current overlay configuration."""
        return self.overlay_client.get_overlay_info()
    
    def get_metrics(self) -> CodegenAgentAPIMetrics:
        """Get comprehensive extension metrics."""
        return self.integration_agent.get_metrics()
    
    def get_config(self) -> CodegenAgentAPIConfig:
        """Get the current configuration."""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """
        Update configuration parameters.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        # Create new config with updates
        config_dict = self.config.to_dict()
        config_dict.update(kwargs)
        
        try:
            new_config = CodegenAgentAPIConfig.from_dict(config_dict)
            new_config.validate()
            
            # Update configuration
            self.config = new_config
            
            # Reinitialize components if necessary
            if any(key in kwargs for key in ['org_id', 'token', 'base_url', 'overlay_priority']):
                logger.info("Reinitializing components due to configuration change")
                self.overlay_client = OverlayClient(self.config)
                self.integration_agent = CodegenIntegrationAgent(self.config)
            
        except Exception as e:
            raise ConfigurationError(f"Failed to update configuration: {e}")
    
    def switch_overlay_implementation(self, implementation: str) -> None:
        """
        Switch to a different overlay implementation.
        
        Args:
            implementation: "pip" or "local"
        """
        try:
            self.overlay_client.switch_implementation(implementation)
            logger.info(f"Switched to {implementation} implementation")
        except Exception as e:
            raise ExtensionError(f"Failed to switch implementation: {e}")
    
    def test_implementations(self) -> Dict[str, Any]:
        """Test both pip and local implementations."""
        return self.overlay_client.test_implementations()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        try:
            # Get health from integration agent
            health = self.integration_agent.health_check()
            
            # Add extension-specific health info
            health["extension"] = {
                "name": "codegen_agent_api",
                "version": "1.0.0",
                "config_valid": True,
                "overlay_info": self.get_overlay_info()
            }
            
            # Test implementations
            impl_tests = self.test_implementations()
            health["implementation_tests"] = impl_tests
            
            # Check if any critical components are unhealthy
            unhealthy_components = [
                name for name, info in health["components"].items()
                if info.get("status") == "unhealthy"
            ]
            
            if unhealthy_components:
                health["overall"] = "degraded"
                health["unhealthy_components"] = unhealthy_components
            
            return health
            
        except Exception as e:
            return {
                "overall": "unhealthy",
                "error": str(e),
                "timestamp": self.integration_agent.health_check().get("timestamp")
            }
    
    def register_webhook_handler(self, event_type, handler) -> None:
        """
        Register a webhook handler.
        
        Args:
            event_type: WebhookEventType to handle
            handler: Handler function
        """
        self.webhook_processor.register_handler(event_type, handler)
    
    def process_webhook(self, payload: str, signature: Optional[str] = None) -> Dict[str, Any]:
        """
        Process incoming webhook.
        
        Args:
            payload: Webhook payload
            signature: Optional signature for verification
            
        Returns:
            Processing result
        """
        return self.webhook_processor.process_webhook(payload, signature)
    
    def get_webhook_metrics(self) -> Dict[str, Any]:
        """Get webhook processing metrics."""
        return self.webhook_processor.get_metrics()
    
    def shutdown(self) -> None:
        """Shutdown the extension."""
        logger.info("Shutting down CodegenAgentAPI extension")
        
        try:
            self.integration_agent.shutdown()
        except Exception as e:
            logger.error(f"Error during integration agent shutdown: {e}")
        
        logger.info("CodegenAgentAPI extension shutdown complete")
    
    def __str__(self) -> str:
        """String representation."""
        return f"CodegenAgentAPI(org_id={self.config.org_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        overlay_info = self.get_overlay_info()
        return (f"CodegenAgentAPI(org_id={self.config.org_id}, "
                f"strategy={overlay_info['strategy']}, "
                f"active={overlay_info['active_implementation']})")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Convenience functions for creating extension instances

def create_codegen_extension(
    org_id: Optional[str] = None,
    token: Optional[str] = None,
    config: Optional[CodegenAgentAPIConfig] = None,
    **kwargs
) -> CodegenAgentAPI:
    """
    Create a CodegenAgentAPI extension instance.
    
    Args:
        org_id: Organization ID (required if config not provided)
        token: API token (required if config not provided)
        config: Optional configuration object
        **kwargs: Additional configuration parameters
        
    Returns:
        CodegenAgentAPI instance
    """
    if config is None:
        if org_id and token:
            kwargs.update({"org_id": org_id, "token": token})
        config = get_codegen_config(**kwargs)
    
    return CodegenAgentAPI(config)


def create_agent_with_overlay(
    org_id: Optional[str] = None,
    token: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create an Agent instance directly with overlay functionality.
    
    Args:
        org_id: Organization ID
        token: API token
        **kwargs: Additional configuration and Agent parameters
        
    Returns:
        Agent instance
    """
    extension = create_codegen_extension(org_id, token, **kwargs)
    return extension.create_agent(**kwargs)


def create_codebase_ai_with_overlay(
    org_id: Optional[str] = None,
    token: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a CodebaseAI instance directly with overlay functionality.
    
    Args:
        org_id: Organization ID
        token: API token
        **kwargs: Additional configuration and CodebaseAI parameters
        
    Returns:
        CodebaseAI instance
    """
    extension = create_codegen_extension(org_id, token, **kwargs)
    return extension.create_codebase_ai(**kwargs)


# Export main classes and functions
__all__ = [
    "CodegenAgentAPI",
    "create_codegen_extension",
    "create_agent_with_overlay",
    "create_codebase_ai_with_overlay",
]

