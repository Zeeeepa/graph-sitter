"""
Refactoring System for Serena LSP Integration

This module provides comprehensive refactoring capabilities including:
- Rename refactoring
- Extract method/variable
- Inline method/variable  
- Move symbol/file
- Organize imports

All refactoring operations include safety checks, conflict detection, and preview capabilities.
"""

from .refactoring_engine import RefactoringEngine, RefactoringConfig
from .rename_refactor import RenameRefactor
from .extract_refactor import ExtractRefactor
from .inline_refactor import InlineRefactor
from .move_refactor import MoveRefactor

__all__ = [
    'RefactoringEngine',
    'RefactoringConfig',
    'RenameRefactor',
    'ExtractRefactor', 
    'InlineRefactor',
    'MoveRefactor'
]

