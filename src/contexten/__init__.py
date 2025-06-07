"""Contexten package - AI agent extensions and tools."""

try:
    from .extensions.contexten_app.contexten_app import ContextenApp
    __all__ = ["ContextenApp"]
except ImportError:
    # ContextenApp requires optional dependencies like fastapi
    __all__ = []

