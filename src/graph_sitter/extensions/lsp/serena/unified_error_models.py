"""
Unified Error Models for Serena LSP Integration

This module defines the standardized error data models used throughout
the unified error interface. These models provide consistent structure
for all error-related operations.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import List, Optional, Dict, Any, Union, Set
from pathlib import Path
import time


class ErrorSeverity(IntEnum):
    """Standardized error severity levels."""
    ERROR = 1
    WARNING = 2
    INFO = 3
    HINT = 4


class ErrorCategory(Enum):
    """Error categories for better organization."""
    SYNTAX = "syntax"
    TYPE = "type"
    IMPORT = "import"
    UNDEFINED = "undefined"
    UNUSED = "unused"
    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    LOGIC = "logic"
    COMPATIBILITY = "compatibility"
    OTHER = "other"


class FixConfidence(Enum):
    """Confidence level for automatic fixes."""
    HIGH = "high"      # Safe to auto-apply
    MEDIUM = "medium"  # Requires user confirmation
    LOW = "low"        # Suggestion only
    NONE = "none"      # No fix available


@dataclass
class ErrorLocation:
    """Precise error location information."""
    file_path: str
    line: int           # 1-based line number
    character: int      # 0-based character position
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    
    @property
    def range_text(self) -> str:
        """Get human-readable range text."""
        if self.end_line is not None and self.end_character is not None:
            if self.line == self.end_line:
                return f"{self.line}:{self.character}-{self.end_character}"
            else:
                return f"{self.line}:{self.character}-{self.end_line}:{self.end_character}"
        return f"{self.line}:{self.character}"
    
    def __str__(self) -> str:
        return f"{self.file_path}:{self.range_text}"


@dataclass
class ErrorFix:
    """Represents a potential fix for an error."""
    id: str
    title: str
    description: str
    confidence: FixConfidence
    changes: List[Dict[str, Any]] = field(default_factory=list)
    requires_user_input: bool = False
    estimated_impact: str = "low"  # low, medium, high
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'confidence': self.confidence.value,
            'changes': self.changes,
            'requires_user_input': self.requires_user_input,
            'estimated_impact': self.estimated_impact
        }


@dataclass
class RelatedSymbol:
    """Information about symbols related to an error."""
    name: str
    symbol_type: str  # function, class, variable, etc.
    file_path: str
    line: int
    relationship: str  # "defines", "uses", "calls", "inherits", etc.
    
    def __str__(self) -> str:
        return f"{self.symbol_type} {self.name} ({self.relationship})"


@dataclass
class UnifiedError:
    """
    Unified error representation that consolidates all error information
    from different sources (LSP, static analysis, etc.).
    """
    id: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    location: ErrorLocation
    source: str  # "pylsp", "mypy", "ruff", etc.
    code: Optional[str] = None
    
    # Context information
    context_lines: List[str] = field(default_factory=list)
    related_symbols: List[RelatedSymbol] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    
    # Fix information
    fixes: List[ErrorFix] = field(default_factory=list)
    has_auto_fix: bool = False
    
    # Metadata
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    occurrence_count: int = 1
    tags: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        # Determine if we have auto-fixes
        self.has_auto_fix = any(
            fix.confidence in [FixConfidence.HIGH, FixConfidence.MEDIUM] 
            for fix in self.fixes
        )
        
        # Auto-categorize based on message if not set
        if self.category == ErrorCategory.OTHER:
            self.category = self._auto_categorize()
    
    def _auto_categorize(self) -> ErrorCategory:
        """Automatically categorize error based on message content."""
        message_lower = self.message.lower()
        
        if any(word in message_lower for word in ['syntax', 'invalid syntax', 'unexpected']):
            return ErrorCategory.SYNTAX
        elif any(word in message_lower for word in ['type', 'incompatible', 'expected']):
            return ErrorCategory.TYPE
        elif any(word in message_lower for word in ['import', 'module', 'cannot import']):
            return ErrorCategory.IMPORT
        elif any(word in message_lower for word in ['undefined', 'not defined', 'name error']):
            return ErrorCategory.UNDEFINED
        elif any(word in message_lower for word in ['unused', 'not used']):
            return ErrorCategory.UNUSED
        elif any(word in message_lower for word in ['style', 'format', 'convention']):
            return ErrorCategory.STYLE
        elif any(word in message_lower for word in ['security', 'vulnerable', 'unsafe']):
            return ErrorCategory.SECURITY
        elif any(word in message_lower for word in ['performance', 'slow', 'inefficient']):
            return ErrorCategory.PERFORMANCE
        
        return ErrorCategory.OTHER
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error (not warning/hint)."""
        return self.severity == ErrorSeverity.ERROR
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning."""
        return self.severity == ErrorSeverity.WARNING
    
    @property
    def is_fixable(self) -> bool:
        """Check if this error has available fixes."""
        return len(self.fixes) > 0
    
    @property
    def auto_fixable(self) -> bool:
        """Check if this error can be automatically fixed."""
        return self.has_auto_fix
    
    def add_fix(self, fix: ErrorFix) -> None:
        """Add a fix to this error."""
        self.fixes.append(fix)
        self.has_auto_fix = any(
            f.confidence in [FixConfidence.HIGH, FixConfidence.MEDIUM] 
            for f in self.fixes
        )
    
    def update_occurrence(self) -> None:
        """Update occurrence tracking."""
        self.last_seen = time.time()
        self.occurrence_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'message': self.message,
            'severity': self.severity.value,
            'severity_name': self.severity.name.lower(),
            'category': self.category.value,
            'location': {
                'file_path': self.location.file_path,
                'line': self.location.line,
                'character': self.location.character,
                'end_line': self.location.end_line,
                'end_character': self.location.end_character,
                'range_text': self.location.range_text
            },
            'source': self.source,
            'code': self.code,
            'context_lines': self.context_lines,
            'related_symbols': [
                {
                    'name': sym.name,
                    'type': sym.symbol_type,
                    'file_path': sym.file_path,
                    'line': sym.line,
                    'relationship': sym.relationship
                }
                for sym in self.related_symbols
            ],
            'dependency_chain': self.dependency_chain,
            'fixes': [fix.to_dict() for fix in self.fixes],
            'has_auto_fix': self.has_auto_fix,
            'is_fixable': self.is_fixable,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'occurrence_count': self.occurrence_count,
            'tags': list(self.tags)
        }
    
    def __str__(self) -> str:
        severity_name = self.severity.name
        return f"{severity_name} {self.location}: {self.message}"


@dataclass
class ErrorContext:
    """
    Comprehensive context information for an error.
    This is returned by the full_error_context() method.
    """
    error: UnifiedError
    
    # Code context
    surrounding_code: str = ""
    function_context: Optional[Dict[str, Any]] = None
    class_context: Optional[Dict[str, Any]] = None
    
    # Symbol analysis
    symbol_definitions: List[Dict[str, Any]] = field(default_factory=list)
    symbol_usages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Related errors
    related_errors: List[UnifiedError] = field(default_factory=list)
    similar_errors: List[UnifiedError] = field(default_factory=list)
    
    # Impact analysis
    affected_functions: List[str] = field(default_factory=list)
    affected_classes: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    
    # Fix recommendations
    recommended_fixes: List[ErrorFix] = field(default_factory=list)
    fix_priority: str = "medium"  # low, medium, high, critical
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'error': self.error.to_dict(),
            'surrounding_code': self.surrounding_code,
            'function_context': self.function_context,
            'class_context': self.class_context,
            'symbol_definitions': self.symbol_definitions,
            'symbol_usages': self.symbol_usages,
            'related_errors': [e.to_dict() for e in self.related_errors],
            'similar_errors': [e.to_dict() for e in self.similar_errors],
            'affected_functions': self.affected_functions,
            'affected_classes': self.affected_classes,
            'affected_files': self.affected_files,
            'recommended_fixes': [fix.to_dict() for fix in self.recommended_fixes],
            'fix_priority': self.fix_priority
        }


@dataclass
class ErrorResolutionResult:
    """Result of error resolution attempt."""
    error_id: str
    success: bool
    message: str
    applied_fixes: List[str] = field(default_factory=list)
    remaining_issues: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'error_id': self.error_id,
            'success': self.success,
            'message': self.message,
            'applied_fixes': self.applied_fixes,
            'remaining_issues': self.remaining_issues,
            'files_modified': self.files_modified
        }


@dataclass
class ErrorSummary:
    """Summary of all errors in the codebase."""
    total_errors: int = 0
    total_warnings: int = 0
    total_info: int = 0
    total_hints: int = 0
    
    # By category
    by_category: Dict[str, int] = field(default_factory=dict)
    
    # By file
    by_file: Dict[str, int] = field(default_factory=dict)
    
    # By source
    by_source: Dict[str, int] = field(default_factory=dict)
    
    # Fixable errors
    auto_fixable: int = 0
    manually_fixable: int = 0
    unfixable: int = 0
    
    # Top issues
    most_common_errors: List[Dict[str, Any]] = field(default_factory=list)
    error_hotspots: List[Dict[str, Any]] = field(default_factory=list)  # Files with most errors
    
    @property
    def total_issues(self) -> int:
        """Total number of issues."""
        return self.total_errors + self.total_warnings + self.total_info + self.total_hints
    
    @property
    def critical_issues(self) -> int:
        """Number of critical issues (errors only)."""
        return self.total_errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_errors': self.total_errors,
            'total_warnings': self.total_warnings,
            'total_info': self.total_info,
            'total_hints': self.total_hints,
            'total_issues': self.total_issues,
            'critical_issues': self.critical_issues,
            'by_category': self.by_category,
            'by_file': self.by_file,
            'by_source': self.by_source,
            'auto_fixable': self.auto_fixable,
            'manually_fixable': self.manually_fixable,
            'unfixable': self.unfixable,
            'most_common_errors': self.most_common_errors,
            'error_hotspots': self.error_hotspots
        }

