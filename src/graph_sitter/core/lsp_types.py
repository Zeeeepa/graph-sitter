"""
Unified LSP Response Types

This module provides standardized response types for all LSP operations
to ensure consistency across the unified API.
"""

from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ErrorSeverity(Enum):
    """Error severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ErrorType(Enum):
    """Types of errors."""
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    LINT = "lint"
    TYPE_CHECK = "type_check"
    IMPORT = "import"
    UNDEFINED = "undefined"


@dataclass
class Position:
    """Represents a position in a text document."""
    line: int
    character: int
    
    def to_dict(self) -> Dict[str, int]:
        return {"line": self.line, "character": self.character}


@dataclass
class Range:
    """Represents a range in a text document."""
    start: Position
    end: Position
    
    def to_dict(self) -> Dict[str, Dict[str, int]]:
        return {
            "start": self.start.to_dict(),
            "end": self.end.to_dict()
        }


@dataclass
class ErrorInfo:
    """Represents a single error or diagnostic."""
    id: str
    message: str
    severity: ErrorSeverity
    error_type: ErrorType
    file_path: str
    range: Range
    source: str = "serena-lsp"
    code: Optional[str] = None
    has_quick_fix: bool = False
    related_symbols: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "message": self.message,
            "severity": self.severity.value,
            "error_type": self.error_type.value,
            "file_path": self.file_path,
            "range": self.range.to_dict(),
            "source": self.source,
            "code": self.code,
            "has_quick_fix": self.has_quick_fix,
            "related_symbols": self.related_symbols,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ErrorCollection:
    """Collection of errors with metadata."""
    errors: List[ErrorInfo]
    total_count: int
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    hint_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Calculate counts after initialization."""
        self.total_count = len(self.errors)
        self.error_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.ERROR)
        self.warning_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.WARNING)
        self.info_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.INFO)
        self.hint_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.HINT)
    
    def filter_by_severity(self, severity: ErrorSeverity) -> 'ErrorCollection':
        """Filter errors by severity."""
        filtered = [e for e in self.errors if e.severity == severity]
        return ErrorCollection(errors=filtered, total_count=len(filtered))
    
    def filter_by_file(self, file_path: str) -> 'ErrorCollection':
        """Filter errors by file path."""
        filtered = [e for e in self.errors if e.file_path == file_path]
        return ErrorCollection(errors=filtered, total_count=len(filtered))
    
    def filter_by_type(self, error_type: ErrorType) -> 'ErrorCollection':
        """Filter errors by type."""
        filtered = [e for e in self.errors if e.error_type == error_type]
        return ErrorCollection(errors=filtered, total_count=len(filtered))


@dataclass
class ErrorSummary:
    """Summary statistics of errors."""
    total_errors: int
    error_count: int
    warning_count: int
    info_count: int
    hint_count: int
    files_with_errors: int
    most_common_error_types: List[Dict[str, Any]]
    error_distribution: Dict[str, int]
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorContext:
    """Full context information for a specific error."""
    error: ErrorInfo
    surrounding_code: str
    related_errors: List[ErrorInfo]
    symbol_context: Dict[str, Any]
    fix_suggestions: List[str]
    impact_analysis: Dict[str, Any]
    similar_errors: List[ErrorInfo] = field(default_factory=list)


@dataclass
class QuickFix:
    """Represents a quick fix for an error."""
    id: str
    title: str
    description: str
    edit_operations: List[Dict[str, Any]]
    confidence: float = 1.0


@dataclass
class CompletionItem:
    """Code completion item."""
    label: str
    kind: str
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None
    sort_text: Optional[str] = None


@dataclass
class HoverInfo:
    """Hover information result."""
    contents: str
    range: Optional[Range] = None


@dataclass
class SignatureHelp:
    """Signature help information."""
    signatures: List[Dict[str, Any]]
    active_signature: int = 0
    active_parameter: int = 0


@dataclass
class SymbolInfo:
    """Symbol information."""
    name: str
    kind: str
    location: Dict[str, Any]
    container_name: Optional[str] = None


@dataclass
class LSPCapabilities:
    """LSP server capabilities."""
    completion: bool = False
    hover: bool = False
    signature_help: bool = False
    definition: bool = False
    references: bool = False
    document_symbols: bool = False
    workspace_symbols: bool = False
    code_actions: bool = False
    rename: bool = False
    diagnostics: bool = False


@dataclass
class LSPStatus:
    """LSP server status."""
    is_running: bool
    server_info: Dict[str, Any]
    capabilities: LSPCapabilities
    last_heartbeat: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


@dataclass
class HealthCheck:
    """Overall codebase health check result."""
    overall_score: float  # 0.0 to 1.0
    error_score: float
    warning_score: float
    code_quality_score: float
    lsp_health: bool
    recommendations: List[str]
    last_check: datetime = field(default_factory=datetime.now)


# Type aliases for convenience
ErrorCallback = Callable[[ErrorCollection], None]
ErrorStream = Callable[[], ErrorCollection]


class LSPResponse:
    """Base class for all LSP responses."""
    
    def __init__(self, success: bool = True, error_message: Optional[str] = None):
        self.success = success
        self.error_message = error_message
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat()
        }


# Export all types
__all__ = [
    'ErrorSeverity', 'ErrorType', 'Position', 'Range', 'ErrorInfo', 
    'ErrorCollection', 'ErrorSummary', 'ErrorContext', 'QuickFix',
    'CompletionItem', 'HoverInfo', 'SignatureHelp', 'SymbolInfo',
    'LSPCapabilities', 'LSPStatus', 'HealthCheck', 'LSPResponse',
    'ErrorCallback', 'ErrorStream'
]

