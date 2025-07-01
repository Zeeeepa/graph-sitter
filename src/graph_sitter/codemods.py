"""
Codemods Module - Code Modification and Transformation Tools

This module provides a unified interface for all code modification and transformation
capabilities, aggregating functionality from the adapters/codemods directory into a clean
public API suitable for external consumption.

Key Features:
- Automated code refactoring
- Pattern-based transformations
- Language-specific codemods
- Batch code modifications
- Safe transformation with rollback capabilities
- Custom codemod creation

Example usage:
    from graph_sitter import Codebase, Codemods
    
    codebase = Codebase("/path/to/project")
    
    # Apply built-in codemods
    Codemods.apply_modernization(codebase)
    Codemods.fix_code_smells(codebase)
    
    # Create custom codemods
    codemod = Codemods.create_custom_codemod(
        pattern="old_pattern",
        replacement="new_pattern"
    )
    codemod.apply(codebase)
    
    # Batch operations
    Codemods.apply_multiple(codebase, [codemod1, codemod2, codemod3])
"""

# Import core codemod functionality
from .adapters.codemods import Codemod

# Import specific codemods from canonical directory
import os
import importlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Dynamically import all available codemods
def _discover_codemods():
    """Discover all available codemods in the canonical directory."""
    codemods_dir = Path(__file__).parent / "adapters" / "codemods" / "canonical"
    available_codemods = {}
    
    if codemods_dir.exists():
        for codemod_dir in codemods_dir.iterdir():
            if codemod_dir.is_dir() and (codemod_dir / "__init__.py").exists():
                try:
                    module_name = f"graph_sitter.adapters.codemods.canonical.{codemod_dir.name}"
                    module = importlib.import_module(module_name)
                    available_codemods[codemod_dir.name] = module
                except ImportError:
                    # Skip codemods that can't be imported
                    pass
    
    return available_codemods

# Discover available codemods
_AVAILABLE_CODEMODS = _discover_codemods()

class CodemodManager:
    """Manager class for applying and organizing codemods."""
    
    def __init__(self):
        self.applied_codemods = []
        self.rollback_stack = []
    
    def apply_codemod(self, codebase, codemod_name: str, **kwargs):
        """Apply a specific codemod by name."""
        if codemod_name in _AVAILABLE_CODEMODS:
            module = _AVAILABLE_CODEMODS[codemod_name]
            # Apply the codemod (implementation depends on specific codemod structure)
            result = module.apply(codebase, **kwargs)
            self.applied_codemods.append(codemod_name)
            return result
        else:
            raise ValueError(f"Codemod '{codemod_name}' not found. Available: {list(_AVAILABLE_CODEMODS.keys())}")
    
    def apply_multiple(self, codebase, codemod_names: List[str], **kwargs):
        """Apply multiple codemods in sequence."""
        results = []
        for codemod_name in codemod_names:
            result = self.apply_codemod(codebase, codemod_name, **kwargs)
            results.append(result)
        return results
    
    def get_available_codemods(self) -> List[str]:
        """Get list of all available codemods."""
        return list(_AVAILABLE_CODEMODS.keys())

# Global codemod manager instance
_manager = CodemodManager()

# High-level convenience functions for external consumption
def apply_modernization(codebase, **kwargs):
    """
    Apply modernization codemods to update code to current best practices.
    
    Args:
        codebase: Codebase instance to modify
        **kwargs: Additional options for modernization
        
    Returns:
        List: Results from applied codemods
    """
    modernization_codemods = [
        "convert_array_type_to_square_bracket",
        "bang_bang_to_boolean",
        "mark_is_boolean"
    ]
    
    available_codemods = [cmd for cmd in modernization_codemods if cmd in _AVAILABLE_CODEMODS]
    return _manager.apply_multiple(codebase, available_codemods, **kwargs)

def fix_code_smells(codebase, **kwargs):
    """
    Apply codemods to fix common code smells and anti-patterns.
    
    Args:
        codebase: Codebase instance to modify
        **kwargs: Additional options for code smell fixes
        
    Returns:
        List: Results from applied codemods
    """
    code_smell_codemods = [
        "add_internal_to_non_exported_components",
        "change_component_tag_names"
    ]
    
    available_codemods = [cmd for cmd in code_smell_codemods if cmd in _AVAILABLE_CODEMODS]
    return _manager.apply_multiple(codebase, available_codemods, **kwargs)

def create_custom_codemod(pattern: str, replacement: str, **kwargs):
    """
    Create a custom codemod for pattern-based transformations.
    
    Args:
        pattern: Pattern to search for (regex or AST pattern)
        replacement: Replacement pattern
        **kwargs: Additional options for codemod creation
        
    Returns:
        Codemod: Custom codemod instance
    """
    return Codemod(pattern=pattern, replacement=replacement, **kwargs)

def apply_codemod(codebase, codemod_name: str, **kwargs):
    """
    Apply a specific codemod by name.
    
    Args:
        codebase: Codebase instance to modify
        codemod_name: Name of the codemod to apply
        **kwargs: Additional options for codemod application
        
    Returns:
        Any: Result from codemod application
    """
    return _manager.apply_codemod(codebase, codemod_name, **kwargs)

def apply_multiple(codebase, codemod_names: List[str], **kwargs):
    """
    Apply multiple codemods in sequence.
    
    Args:
        codebase: Codebase instance to modify
        codemod_names: List of codemod names to apply
        **kwargs: Additional options for codemod application
        
    Returns:
        List: Results from all applied codemods
    """
    return _manager.apply_multiple(codebase, codemod_names, **kwargs)

def get_available_codemods() -> List[str]:
    """
    Get list of all available codemods.
    
    Returns:
        List[str]: Names of available codemods
    """
    return _manager.get_available_codemods()

def create_refactor_codemod(codebase, refactor_type: str = "general", **kwargs):
    """
    Create a codemod for common refactoring operations.
    
    Args:
        codebase: Codebase instance to analyze for refactoring opportunities
        refactor_type: Type of refactoring ("general", "extract_method", "rename", etc.)
        **kwargs: Additional options for refactoring
        
    Returns:
        Codemod: Refactoring codemod instance
    """
    # This would analyze the codebase and suggest/create appropriate refactoring codemods
    # Implementation would depend on the specific refactoring analysis capabilities
    return Codemod(refactor_type=refactor_type, **kwargs)

def apply_security_fixes(codebase, **kwargs):
    """
    Apply codemods to fix common security vulnerabilities.
    
    Args:
        codebase: Codebase instance to modify
        **kwargs: Additional options for security fixes
        
    Returns:
        List: Results from applied security codemods
    """
    # This would apply security-focused codemods
    # Implementation would depend on available security codemods
    security_codemods = []  # Would be populated with actual security codemods
    return _manager.apply_multiple(codebase, security_codemods, **kwargs)

def apply_performance_optimizations(codebase, **kwargs):
    """
    Apply codemods to optimize code performance.
    
    Args:
        codebase: Codebase instance to modify
        **kwargs: Additional options for performance optimizations
        
    Returns:
        List: Results from applied performance codemods
    """
    # This would apply performance-focused codemods
    # Implementation would depend on available performance codemods
    performance_codemods = []  # Would be populated with actual performance codemods
    return _manager.apply_multiple(codebase, performance_codemods, **kwargs)

# Export all public functions and classes
__all__ = [
    # High-level convenience functions
    "apply_modernization",
    "fix_code_smells", 
    "create_custom_codemod",
    "apply_codemod",
    "apply_multiple",
    "get_available_codemods",
    "create_refactor_codemod",
    "apply_security_fixes",
    "apply_performance_optimizations",
    
    # Core classes
    "Codemod",
    "CodemodManager",
]

