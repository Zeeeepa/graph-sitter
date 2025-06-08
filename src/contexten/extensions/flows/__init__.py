"""Flow Orchestration Extensions.

This package contains flow orchestration extensions for:
- Prefect flows
- ControlFlow systems
- Strands workflows
- MCP (Model Context Protocol) flows
"""

from typing import Dict, List, Type

from ...core.extension import Extension

# Flow extension registry
FLOW_EXTENSIONS: Dict[str, Type[Extension]] = {}

def register_flow_extension(name: str, extension_class: Type[Extension]) -> None:
    """Register a flow extension.
    
    Args:
        name: Extension name
        extension_class: Extension class
    """
    FLOW_EXTENSIONS[name] = extension_class

def get_flow_extension(name: str) -> Type[Extension]:
    """Get a flow extension class by name.
    
    Args:
        name: Extension name
        
    Returns:
        Extension class
        
    Raises:
        KeyError: If extension is not found
    """
    return FLOW_EXTENSIONS[name]

def list_flow_extensions() -> List[str]:
    """List all available flow extensions.
    
    Returns:
        List of extension names
    """
    return list(FLOW_EXTENSIONS.keys())

# Auto-import flow extensions
def _auto_import_flow_extensions():
    """Auto-import all available flow extensions."""
    try:
        from .prefect_flow import PrefectFlowExtension
        register_flow_extension("prefect", PrefectFlowExtension)
    except ImportError:
        pass
    
    try:
        from .controlflow_extension import ControlFlowExtension
        register_flow_extension("controlflow", ControlFlowExtension)
    except ImportError:
        pass
    
    try:
        from .strands_extension import StrandsExtension
        register_flow_extension("strands", StrandsExtension)
    except ImportError:
        pass
    
    try:
        from .mcp_extension import MCPExtension
        register_flow_extension("mcp", MCPExtension)
    except ImportError:
        pass

# Auto-import on module load
_auto_import_flow_extensions()

