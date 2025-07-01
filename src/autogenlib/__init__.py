"""
Enhanced Autogenlib Module with Codegen SDK Integration

This module provides intelligent code generation capabilities by integrating
with the Codegen SDK and leveraging graph_sitter's codebase analysis.

Key Features:
- Proper org_id and token configuration for Codegen SDK
- Context-aware code generation using codebase analysis
- Multi-level caching for performance optimization
- Cost management and usage tracking
- Batch processing capabilities
- Integration with contexten orchestrator
"""

from .core.client import AutogenClient
from .core.config import AutogenConfig
from .generators.dynamic_generator import DynamicGenerator
from .generators.batch_generator import BatchGenerator
from .context.codebase_analyzer import CodebaseAnalyzer
from .monitoring.usage_tracker import UsageTracker

__version__ = "2.0.0"
__all__ = [
    "AutogenClient",
    "AutogenConfig", 
    "DynamicGenerator",
    "BatchGenerator",
    "CodebaseAnalyzer",
    "UsageTracker"
]

# Default client instance for backward compatibility
_default_client = None

def initialize(org_id: str, token: str, codebase_path: str = None, **kwargs):
    """Initialize the default autogenlib client"""
    global _default_client
    
    config = AutogenConfig(
        org_id=org_id,
        token=token,
        codebase_path=codebase_path,
        **kwargs
    )
    
    _default_client = AutogenClient(config)
    return _default_client

def get_client() -> AutogenClient:
    """Get the default client instance"""
    if _default_client is None:
        raise RuntimeError("Autogenlib not initialized. Call initialize() first.")
    return _default_client

# Convenience functions for backward compatibility
async def generate_code(module_path: str, function_name: str, **kwargs):
    """Generate code using the default client"""
    client = get_client()
    return await client.generate_code(module_path, function_name, **kwargs)

async def generate_batch(requests: list, **kwargs):
    """Generate multiple code pieces using batch processing"""
    client = get_client()
    return await client.generate_batch(requests, **kwargs)

