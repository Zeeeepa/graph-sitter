"""Graph Sitter AI Integration Module.

This module provides AI integration capabilities for the graph-sitter project,
including client management, context gathering, and utility functions.

Main Components:
- AIClientFactory: Unified client creation with multi-provider support
- ContextGatherer: Rich context extraction from codebase analysis
- AbstractAIHelper: Base class for AI helper implementations
- Token utilities: Efficient token counting and text processing

Example Usage:
    from graph_sitter.ai import AIClientFactory, ContextGatherer
    
    # Create AI client
    client, provider = AIClientFactory.create_client(
        openai_api_key="your-key",
        prefer_codegen=True
    )
    
    # Gather context for analysis
    gatherer = ContextGatherer(codebase)
    context = gatherer.gather_target_context(target)
"""

# Core client management
from .client_factory import (
    AIClientFactory,
    CodegenAIClient,
    CircuitBreaker,
    RateLimiter,
    get_ai_metrics,
    reset_ai_metrics,
    ai_metrics
)

# Context gathering
from .context_gatherer import ContextGatherer

# AI helpers and abstractions
from .helpers import (
    AbstractAIHelper,
    OpenAIHelper,
    CodegenHelper,
    create_ai_helper
)

# Utilities
from .utils import (
    count_tokens,
    estimate_tokens_fast,
    get_encoder,
    validate_token_limit,
    truncate_to_token_limit,
    clear_encoder_cache,
    get_cache_info
)

# Legacy support (deprecated)
from .client import get_openai_client

__all__ = [
    # Client management
    "AIClientFactory",
    "CodegenAIClient",
    "CircuitBreaker", 
    "RateLimiter",
    "get_ai_metrics",
    "reset_ai_metrics",
    "ai_metrics",
    
    # Context gathering
    "ContextGatherer",
    
    # AI helpers
    "AbstractAIHelper",
    "OpenAIHelper", 
    "CodegenHelper",
    "create_ai_helper",
    
    # Utilities
    "count_tokens",
    "estimate_tokens_fast",
    "get_encoder",
    "validate_token_limit",
    "truncate_to_token_limit",
    "clear_encoder_cache",
    "get_cache_info",
    
    # Legacy (deprecated)
    "get_openai_client"
]

# Version info
__version__ = "1.0.0"
__author__ = "Graph Sitter Team"
__description__ = "AI integration module for graph-sitter codebase analysis"

