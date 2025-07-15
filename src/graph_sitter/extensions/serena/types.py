"""
Shared types for Serena LSP integration.

This module contains common types and enums used across Serena modules
to avoid circular imports.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


class RefactoringType(Enum):
    """Types of refactoring operations."""
    RENAME = "rename"
    EXTRACT_METHOD = "extract_method"
    EXTRACT_VARIABLE = "extract_variable"
    INLINE_METHOD = "inline_method"
    INLINE_VARIABLE = "inline_variable"
    MOVE_SYMBOL = "move_symbol"
    MOVE_FILE = "move_file"
    ORGANIZE_IMPORTS = "organize_imports"


@dataclass
class RefactoringChange:
    """Represents a single change in a refactoring operation."""
    file_path: str
    start_line: int
    start_character: int
    end_line: int
    end_character: int
    old_text: str
    new_text: str
    description: Optional[str] = None


@dataclass
class RefactoringConflict:
    """Represents a conflict that prevents a refactoring operation."""
    file_path: str
    line: int
    character: int
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class RefactoringResult:
    """Result of a refactoring operation."""
    success: bool
    refactoring_type: RefactoringType
    changes: List[RefactoringChange]
    conflicts: List[RefactoringConflict]
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None
    preview_available: Optional[bool] = None
    error_message: Optional[str] = None
    
    @property
    def has_conflicts(self) -> bool:
        """Check if there are any conflicts."""
        return len(self.conflicts) > 0
    
    @property
    def files_changed(self) -> List[str]:
        """Get list of files that would be changed."""
        return list(set(change.file_path for change in self.changes))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RefactoringResult to dictionary."""
        return {
            'success': self.success,
            'refactoring_type': self.refactoring_type.value if self.refactoring_type else None,
            'changes': [
                {
                    'file_path': getattr(change, 'file_path', change.get('file_path', 'unknown') if isinstance(change, dict) else 'unknown'),
                    'start_line': getattr(change, 'start_line', change.get('start_line', 0) if isinstance(change, dict) else 0),
                    'end_line': getattr(change, 'end_line', change.get('end_line', 0) if isinstance(change, dict) else 0),
                    'old_content': getattr(change, 'old_content', change.get('old_content', '') if isinstance(change, dict) else ''),
                    'new_content': getattr(change, 'new_content', change.get('new_content', '') if isinstance(change, dict) else ''),
                    'change_type': getattr(change, 'change_type', change.get('change_type', None) if isinstance(change, dict) else None)
                }
                for change in self.changes
            ],
            'conflicts': [
                {
                    'file_path': getattr(conflict, 'file_path', conflict.get('file_path', 'unknown') if isinstance(conflict, dict) else 'unknown'),
                    'line_number': getattr(conflict, 'line_number', conflict.get('line_number', 0) if isinstance(conflict, dict) else 0),
                    'conflict_type': getattr(conflict, 'conflict_type', conflict.get('conflict_type', None) if isinstance(conflict, dict) else None),
                    'description': getattr(conflict, 'description', conflict.get('description', '') if isinstance(conflict, dict) else ''),
                    'suggested_resolution': getattr(conflict, 'suggested_resolution', conflict.get('suggested_resolution', '') if isinstance(conflict, dict) else '')
                }
                for conflict in self.conflicts
            ],
            'message': self.message,
            'metadata': self.metadata or {},
            'warnings': self.warnings or [],
            'preview_available': self.preview_available,
            'error_message': self.error_message,
            'has_conflicts': self.has_conflicts,
            'files_changed': self.files_changed
        }


@dataclass
class CodeGenerationResult:
    """Result of a code generation operation."""
    success: bool
    generated_code: str
    file_path: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SemanticSearchResult:
    """Result of a semantic search operation."""
    symbol_name: str
    file_path: str
    line_number: int
    symbol_type: str
    relevance_score: float
    context_snippet: str
    documentation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SymbolInfo:
    """Information about a code symbol."""
    name: str
    kind: str  # function, class, variable, etc.
    file_path: str
    line: int
    character: int
    definition_range: Optional[Dict[str, int]] = None
    documentation: Optional[str] = None
    type_annotation: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class CompletionContext:
    """Context information for code completions."""
    file_path: str
    line: int
    character: int
    prefix: str
    trigger_character: Optional[str] = None
    is_incomplete: bool = False


@dataclass
class HoverContext:
    """Context information for hover requests."""
    file_path: str
    line: int
    character: int
    symbol_name: Optional[str] = None
    symbol_kind: Optional[str] = None


@dataclass
class SignatureContext:
    """Context information for signature help."""
    file_path: str
    line: int
    character: int
    function_name: Optional[str] = None
    parameter_index: int = 0


class SerenaCapability(Enum):
    """Serena capabilities that can be enabled/disabled."""
    CODE_INTELLIGENCE = "code_intelligence"
    INTELLIGENCE = "intelligence"  # Alias for CODE_INTELLIGENCE
    REFACTORING = "refactoring"
    CODE_ACTIONS = "code_actions"
    ACTIONS = "actions"  # Alias for CODE_ACTIONS
    CODE_GENERATION = "code_generation"
    GENERATION = "generation"  # Alias for CODE_GENERATION
    SEMANTIC_SEARCH = "semantic_search"
    SEARCH = "search"  # Alias for SEMANTIC_SEARCH
    SYMBOL_INTELLIGENCE = "symbol_intelligence"
    SYMBOLS = "symbols"  # Alias for SYMBOL_INTELLIGENCE
    REALTIME_ANALYSIS = "realtime_analysis"
    REALTIME = "realtime"  # Alias for REALTIME_ANALYSIS
    ANALYSIS = "analysis"  # New capability for real-time analysis


@dataclass
class SerenaConfig:
    """Configuration for Serena LSP integration."""
    enabled_capabilities: Optional[List[SerenaCapability]] = None
    realtime_analysis: bool = True
    cache_enabled: bool = True
    max_cache_size: int = 1000
    background_processing: bool = True
    performance_mode: bool = False
    debug_mode: bool = False
    
    def __post_init__(self):
        """Set default capabilities if none provided."""
        if not self.enabled_capabilities:
            self.enabled_capabilities = [
                SerenaCapability.CODE_INTELLIGENCE,
                SerenaCapability.REFACTORING,
                SerenaCapability.CODE_ACTIONS,
                SerenaCapability.CODE_GENERATION,
                SerenaCapability.SEMANTIC_SEARCH,
                SerenaCapability.SYMBOL_INTELLIGENCE,
                SerenaCapability.REALTIME_ANALYSIS
            ]
    
    def is_capability_enabled(self, capability: SerenaCapability) -> bool:
        """Check if a capability is enabled."""
        return capability in self.enabled_capabilities
    
    def enable_capability(self, capability: SerenaCapability) -> None:
        """Enable a capability."""
        if capability not in self.enabled_capabilities:
            self.enabled_capabilities.append(capability)
    
    def disable_capability(self, capability: SerenaCapability) -> None:
        """Disable a capability."""
        if capability in self.enabled_capabilities:
            self.enabled_capabilities.remove(capability)
