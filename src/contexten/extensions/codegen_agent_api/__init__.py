"""
Codegen Agent API Overlay Extension for Contexten

This extension provides overlay functionality for the pip-installed codegen package,
enhancing it with contexten ecosystem integration while preserving the original API.

Usage:
    # Apply the overlay
    from contexten.extensions.codegen_agent_api import apply_codegen_overlay
    overlay = apply_codegen_overlay()
    
    # Now use codegen normally with enhanced functionality
    from codegen.agents.agent import Agent
    agent = Agent(org_id="11", token="your_token")
    
    # The agent now has contexten integration!
    task = agent.run("Your prompt here")

Features:
- Preserves original codegen API (from codegen.agents.agent import Agent)
- Adds contexten ecosystem integration
- Enhanced monitoring and metrics
- Event handling and callbacks
- Health checks and debugging tools
- Automatic overlay detection and application
"""

from .apply import (
    apply_codegen_overlay,
    get_overlay_instance,
    register_event_handler,
    get_overlay_metrics,
    CodegenOverlayError,
    CodegenOverlayApplicator,
    ContextenIntegration
)

__version__ = "1.0.0"
__author__ = "Contexten Team"

__all__ = [
    # Main functions
    "apply_codegen_overlay",
    "get_overlay_instance", 
    "register_event_handler",
    "get_overlay_metrics",
    
    # Classes
    "CodegenOverlayApplicator",
    "ContextenIntegration",
    
    # Exceptions
    "CodegenOverlayError",
]

# Extension metadata for contexten
EXTENSION_INFO = {
    "name": "codegen_agent_api",
    "version": __version__,
    "description": "Overlay extension for pip-installed codegen package with contexten integration",
    "author": __author__,
    "main_module": "apply",
    "overlay_support": True,
    "target_package": "codegen",
    "preserves_api": True,
    "dependencies": ["codegen"],
    "contexten_version": ">=1.0.0"
}


def get_extension_info() -> dict:
    """Get extension metadata."""
    return EXTENSION_INFO.copy()


def get_version() -> str:
    """Get extension version."""
    return __version__


def auto_apply_overlay():
    """Automatically apply the overlay if codegen package is detected."""
    try:
        return apply_codegen_overlay()
    except CodegenOverlayError:
        # Codegen package not found, skip auto-apply
        return None


# Auto-apply overlay on import (optional)
# Uncomment the next line to automatically apply overlay when extension is imported
# auto_apply_overlay()

