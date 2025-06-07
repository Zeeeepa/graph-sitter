"""
Modal Extension for Contexten

Provides Modal.com integration for serverless function execution and event routing.
"""

from .base import CodebaseEventsApp, EventRouterMixin
from .linear_client import LinearClient
from .request_util import RequestUtil
from .interface import EventHandlerManagerProtocol

__version__ = "1.0.0"
__all__ = [
    "CodebaseEventsApp",
    "EventRouterMixin", 
    "LinearClient",
    "RequestUtil",
    "EventHandlerManagerProtocol"
]

