"""Contexten Extensions Package.

This package contains all extensions for the Contexten system, including:
- Core integrations (GitHub, Linear, Slack)
- Development tools (Codegen, Graph Sitter)
- CI/CD integrations (CircleCI)
- Dashboard and UI components
- Workflow orchestration tools
"""

from typing import Dict, List, Type

from ..core.extension import Extension

# Extension registry
AVAILABLE_EXTENSIONS: Dict[str, Type[Extension]] = {}

def register_extension(name: str, extension_class: Type[Extension]) -> None:
    """Register an extension.
    
    Args:
        name: Extension name
        extension_class: Extension class
    """
    AVAILABLE_EXTENSIONS[name] = extension_class

def get_extension(name: str) -> Type[Extension]:
    """Get an extension class by name.
    
    Args:
        name: Extension name
        
    Returns:
        Extension class
        
    Raises:
        KeyError: If extension is not found
    """
    return AVAILABLE_EXTENSIONS[name]

def list_extensions() -> List[str]:
    """List all available extensions.
    
    Returns:
        List of extension names
    """
    return list(AVAILABLE_EXTENSIONS.keys())

# Auto-import all extensions
def _auto_import_extensions():
    """Auto-import all available extensions."""
    try:
        from .github.github import GitHubExtension
        register_extension("github", GitHubExtension)
    except ImportError:
        pass
    
    try:
        from .linear.linear import LinearExtension
        register_extension("linear", LinearExtension)
    except ImportError:
        pass
    
    try:
        from .slack.slack import SlackExtension
        register_extension("slack", SlackExtension)
    except ImportError:
        pass
    
    try:
        from .dashboard.dashboard import DashboardExtension
        register_extension("dashboard", DashboardExtension)
    except ImportError:
        pass
    
    try:
        from .codegen.codegen import CodegenExtension
        register_extension("codegen", CodegenExtension)
    except ImportError:
        pass
    
    try:
        from .graph_sitter.graph_sitter import GraphSitterExtension
        register_extension("graph_sitter", GraphSitterExtension)
    except ImportError:
        pass
    
    try:
        from .circleci.circleci import CircleCIExtension
        register_extension("circleci", CircleCIExtension)
    except ImportError:
        pass

# Auto-import on module load
_auto_import_extensions()

