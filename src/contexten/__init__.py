"""Contexten package - AI agent extensions and tools."""

# Lazy import to avoid circular dependencies
def get_contexten_app():
    """Get ContextenApp class with lazy loading."""
    from .extensions.contexten_app.contexten_app import ContextenApp
    return ContextenApp

# For backward compatibility, but avoid direct import
__all__ = ["get_contexten_app"]
