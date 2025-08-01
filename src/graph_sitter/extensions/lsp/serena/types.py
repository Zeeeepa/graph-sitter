"""
Enhanced Types for Serena LSP Integration

This module contains comprehensive types and enums used across all Serena modules
including LSP integration, refactoring, symbol intelligence, and code actions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Callable
from pathlib import Path
import time


class SerenaCapability(Enum):
    """Available Serena capabilities."""
    ERROR_ANALYSIS = "error_analysis"
    REFACTORING = "refactoring"
    SYMBOL_INTELLIGENCE = "symbol_intelligence"
    CODE_ACTIONS = "code_actions"
    REAL_TIME_ANALYSIS = "real_time_analysis"
    SEMANTIC_SEARCH = "semantic_search"
    CODE_GENERATION = "code_generation"
    HOVER_INFO = "hover_info"
    COMPLETIONS = "completions"


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


class ChangeType(Enum):
    """Types of changes in refactoring operations."""
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    MOVE = "move"


class ConflictType(Enum):
    """Types of conflicts in refactoring operations."""
    NAME_COLLISION = "name_collision"
    SCOPE_CONFLICT = "scope_conflict"
    TYPE_MISMATCH = "type_mismatch"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    SYNTAX_ERROR = "syntax_error"


@dataclass
class SerenaConfig:
    """Configuration for Serena integration."""
    # Core capabilities
    enabled_capabilities: List[SerenaCapability] = field(default_factory=lambda: [
        SerenaCapability.ERROR_ANALYSIS,
        SerenaCapability.SYMBOL_INTELLIGENCE,
        SerenaCapability.CODE_ACTIONS
    ])
    
    # LSP configuration
    lsp_server_command: Optional[List[str]] = None
    lsp_server_host: str = "localhost"
    lsp_server_port: int = 8080
    lsp_connection_timeout: float = 30.0
    lsp_auto_reconnect: bool = True
    
    # Real-time analysis
    realtime_analysis: bool = True
    file_watch_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.js", "*.ts"])
    analysis_debounce_ms: int = 500
    
    # Refactoring
    enable_refactoring_preview: bool = True
    enable_refactoring_safety_checks: bool = True
    max_refactoring_file_changes: int = 100
    
    # Performance
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    
    # Logging
    log_level: str = "INFO"
    log_lsp_communication: bool = False


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
    change_type: ChangeType = ChangeType.REPLACE
    description: Optional[str] = None
    
    @property
    def is_insertion(self) -> bool:
        """Check if this is an insertion change."""
        return self.change_type == ChangeType.INSERT
    
    @property
    def is_deletion(self) -> bool:
        """Check if this is a deletion change."""
        return self.change_type == ChangeType.DELETE
    
    @property
    def line_count_delta(self) -> int:
        """Calculate the change in line count."""
        old_lines = self.old_text.count('\n')
        new_lines = self.new_text.count('\n')
        return new_lines - old_lines


@dataclass
class RefactoringConflict:
    """Represents a conflict that prevents a refactoring operation."""
    file_path: str
    line_number: int
    character: int
    conflict_type: ConflictType
    description: str
    severity: str = "error"  # error, warning, info
    suggested_resolution: Optional[str] = None
    
    @property
    def is_blocking(self) -> bool:
        """Check if this conflict blocks the refactoring."""
        return self.severity == "error"


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
    preview_available: bool = True
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    @property
    def has_conflicts(self) -> bool:
        """Check if there are any conflicts."""
        return len(self.conflicts) > 0
    
    @property
    def has_blocking_conflicts(self) -> bool:
        """Check if there are any blocking conflicts."""
        return any(conflict.is_blocking for conflict in self.conflicts)
    
    @property
    def files_changed(self) -> List[str]:
        """Get list of files that would be changed."""
        return list(set(change.file_path for change in self.changes))
    
    @property
    def total_changes(self) -> int:
        """Get total number of changes."""
        return len(self.changes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RefactoringResult to dictionary."""
        return {
            'success': self.success,
            'refactoring_type': self.refactoring_type.value if self.refactoring_type else None,
            'changes': [
                {
                    'file_path': change.file_path,
                    'start_line': change.start_line,
                    'start_character': change.start_character,
                    'end_line': change.end_line,
                    'end_character': change.end_character,
                    'old_text': change.old_text,
                    'new_text': change.new_text,
                    'change_type': change.change_type.value,
                    'description': change.description
                }
                for change in self.changes
            ],
            'conflicts': [
                {
                    'file_path': conflict.file_path,
                    'line_number': conflict.line_number,
                    'character': conflict.character,
                    'conflict_type': conflict.conflict_type.value,
                    'description': conflict.description,
                    'severity': conflict.severity,
                    'suggested_resolution': conflict.suggested_resolution
                }
                for conflict in self.conflicts
            ],
            'message': self.message,
            'metadata': self.metadata or {},
            'warnings': self.warnings or [],
            'preview_available': self.preview_available,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'files_changed': self.files_changed,
            'total_changes': self.total_changes,
            'has_conflicts': self.has_conflicts,
            'has_blocking_conflicts': self.has_blocking_conflicts
        }


@dataclass
class SymbolInfo:
    """Information about a code symbol."""
    name: str
    symbol_type: str  # function, class, variable, etc.
    file_path: str
    line_number: int
    character: int
    scope: Optional[str] = None
    namespace: Optional[str] = None
    signature: Optional[str] = None
    documentation: Optional[str] = None
    references: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    usages: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def qualified_name(self) -> str:
        """Get fully qualified symbol name."""
        parts = []
        if self.namespace:
            parts.append(self.namespace)
        if self.scope:
            parts.append(self.scope)
        parts.append(self.name)
        return ".".join(parts)


@dataclass
class CodeAction:
    """Represents a code action that can be applied."""
    id: str
    title: str
    kind: str  # quickfix, refactor, source, etc.
    description: Optional[str] = None
    is_preferred: bool = False
    disabled_reason: Optional[str] = None
    edit: Optional[Dict[str, Any]] = None
    command: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    
    @property
    def is_available(self) -> bool:
        """Check if the action is available (not disabled)."""
        return self.disabled_reason is None


@dataclass
class CodeGenerationResult:
    """Result of code generation operation."""
    success: bool
    generated_code: str
    file_path: Optional[str] = None
    insertion_point: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None
    suggestions: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'generated_code': self.generated_code,
            'file_path': self.file_path,
            'insertion_point': self.insertion_point,
            'metadata': self.metadata or {},
            'suggestions': self.suggestions,
            'error_message': self.error_message
        }


@dataclass
class SemanticSearchResult:
    """Result of semantic search operation."""
    query: str
    results: List[Dict[str, Any]]
    total_count: int
    search_time: float
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'results': self.results,
            'total_count': self.total_count,
            'search_time': self.search_time,
            'metadata': self.metadata or {}
        }


@dataclass
class HoverInfo:
    """Information displayed on hover."""
    content: str
    content_type: str = "markdown"  # markdown, plaintext
    range: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'content': self.content,
            'content_type': self.content_type,
            'range': self.range
        }


@dataclass
class CompletionItem:
    """Code completion item."""
    label: str
    kind: str
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None
    sort_text: Optional[str] = None
    filter_text: Optional[str] = None
    is_preselect: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'label': self.label,
            'kind': self.kind,
            'detail': self.detail,
            'documentation': self.documentation,
            'insert_text': self.insert_text or self.label,
            'sort_text': self.sort_text,
            'filter_text': self.filter_text,
            'is_preselect': self.is_preselect
        }


@dataclass
class AnalysisContext:
    """Context for analysis operations."""
    file_path: str
    content: Optional[str] = None
    cursor_position: Optional[Dict[str, int]] = None
    selection_range: Optional[Dict[str, Any]] = None
    include_dependencies: bool = True
    include_references: bool = True
    max_depth: int = 3
    
    @property
    def has_selection(self) -> bool:
        """Check if there's a selection range."""
        return self.selection_range is not None
    
    @property
    def has_cursor(self) -> bool:
        """Check if there's a cursor position."""
        return self.cursor_position is not None


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    cache_hits: int = 0
    cache_misses: int = 0
    
    @classmethod
    def start_timing(cls, operation_name: str) -> 'PerformanceMetrics':
        """Start timing an operation."""
        start_time = time.time()
        return cls(
            operation_name=operation_name,
            start_time=start_time,
            end_time=0.0,
            duration=0.0
        )
    
    def finish_timing(self) -> None:
        """Finish timing the operation."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation_name': self.operation_name,
            'duration': self.duration,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0
        }


# Event system types
EventHandler = Callable[[str, Any], None]
AsyncEventHandler = Callable[[str, Any], Any]  # Can be async


@dataclass
class EventSubscription:
    """Event subscription information."""
    event_type: str
    handler: Union[EventHandler, AsyncEventHandler]
    is_async: bool
    priority: int = 0
    
    def __post_init__(self):
        """Determine if handler is async."""
        import asyncio
        self.is_async = asyncio.iscoroutinefunction(self.handler)


# Utility functions for type validation and conversion
def validate_refactoring_type(value: str) -> RefactoringType:
    """Validate and convert string to RefactoringType."""
    try:
        return RefactoringType(value)
    except ValueError:
        raise ValueError(f"Invalid refactoring type: {value}. Valid types: {[t.value for t in RefactoringType]}")


def validate_capability(value: str) -> SerenaCapability:
    """Validate and convert string to SerenaCapability."""
    try:
        return SerenaCapability(value)
    except ValueError:
        raise ValueError(f"Invalid capability: {value}. Valid capabilities: {[c.value for c in SerenaCapability]}")


def create_default_config() -> SerenaConfig:
    """Create default Serena configuration."""
    return SerenaConfig()


def merge_configs(base: SerenaConfig, override: SerenaConfig) -> SerenaConfig:
    """Merge two configurations, with override taking precedence."""
    merged = SerenaConfig()
    
    # Use dataclass fields to merge all attributes
    for field_info in merged.__dataclass_fields__.values():
        field_name = field_info.name
        
        # Get values from both configs
        override_value = getattr(override, field_name, None)
        base_value = getattr(base, field_name, None)
        
        # Use override if available, otherwise base
        if override_value is not None:
            setattr(merged, field_name, override_value)
        elif base_value is not None:
            setattr(merged, field_name, base_value)
    
    return merged

