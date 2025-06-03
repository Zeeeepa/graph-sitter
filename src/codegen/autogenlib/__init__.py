"""Autogenlib - Codegen SDK Integration Module.

This module provides a comprehensive integration layer between graph-sitter's
codebase analysis capabilities and Codegen SDK for AI-powered software engineering.

Key Features:
- Codegen SDK client with authentication and configuration
- Context enhancement using existing codebase analysis
- Performance optimization and caching layers
- Asynchronous processing and queue management
- Integration interfaces for contexten orchestrator
"""

from .client import AutogenClient
from .config import AutogenConfig
from .context import ContextEnhancer
from .interfaces import OrchestratorInterface, SimpleInterface
from .models import TaskRequest, TaskResponse, TaskStatus
from .integration import CodegenAppIntegration, create_autogenlib_integration

__version__ = "0.1.0"

__all__ = [
    "AutogenClient",
    "AutogenConfig", 
    "ContextEnhancer",
    "OrchestratorInterface",
    "SimpleInterface",
    "TaskRequest",
    "TaskResponse", 
    "TaskStatus",
    "CodegenAppIntegration",
    "create_autogenlib_integration",
]

