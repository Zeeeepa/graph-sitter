"""Legacy AI client module - DEPRECATED.

This module is deprecated in favor of client_factory.py which provides
better error handling, caching, and multi-provider support.

Use AIClientFactory.create_client() instead of get_openai_client().
"""

import warnings
from openai import OpenAI


def get_openai_client(key: str) -> OpenAI:
    """Create OpenAI client - DEPRECATED.
    
    Args:
        key: OpenAI API key
        
    Returns:
        OpenAI client instance
        
    Deprecated:
        Use AIClientFactory.create_client() instead for better functionality.
    """
    warnings.warn(
        "get_openai_client() is deprecated. Use AIClientFactory.create_client() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to the factory for consistency
    from graph_sitter.ai.client_factory import AIClientFactory
    client, _ = AIClientFactory.create_client(openai_api_key=key)
    return client

