"""
Enhanced Codegen SDK with multiple interface patterns.

Supports both Agent pattern and codebase.ai-like direct function calls.
"""

from .agent import Agent
from .task import Task
from .exceptions import (
    CodegenError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ValidationError,
    TaskError,
    TimeoutError,
    NetworkError,
    ConfigurationError
)
from .codebase_ai import (
    CodebaseAI,
    initialize_codebase_ai,
    codebase_ai,
    improve_function,
    summarize_method,
    analyze_codebase
)

__version__ = "1.1.0"
__all__ = [
    # Core classes
    "Agent",
    "Task",
    
    # Exceptions
    "CodegenError",
    "AuthenticationError", 
    "APIError",
    "RateLimitError",
    "ValidationError",
    "TaskError",
    "TimeoutError",
    "NetworkError",
    "ConfigurationError",
    
    # Codebase.AI interface
    "CodebaseAI",
    "initialize_codebase_ai",
    "codebase_ai",
    "improve_function",
    "summarize_method",
    "analyze_codebase"
]

