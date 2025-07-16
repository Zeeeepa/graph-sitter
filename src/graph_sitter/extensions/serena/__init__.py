"""
Serena LSP Integration for Graph-Sitter

This module provides comprehensive LSP capabilities inspired by Serena's architecture,
including real-time code intelligence, advanced refactoring, code generation, and more.
"""

from .core import SerenaCore
from .types import SerenaConfig, SerenaCapability, RefactoringType, RefactoringResult, CodeGenerationResult, SemanticSearchResult, SymbolInfo
from .intelligence import CodeIntelligence
from .refactoring import RefactoringEngine
from .actions import CodeActions
from .generation import CodeGenerator
from .search import SemanticSearch
from .realtime import RealtimeAnalyzer
from .symbols import SymbolIntelligence

__all__ = [
    'SerenaCore',
    'SerenaConfig',
    'SerenaCapability',
    'RefactoringType',
    'RefactoringResult',
    'CodeGenerationResult',
    'SemanticSearchResult',
    'SymbolInfo',
    'CodeIntelligence', 
    'RefactoringEngine',
    'CodeActions',
    'CodeGenerator',
    'SemanticSearch',
    'RealtimeAnalyzer',
    'SymbolIntelligence'
]

__version__ = "1.0.0"
