"""
Enhanced Error Types for Comprehensive LSP Error Handling

This module defines the enhanced error types that provide rich context, reasoning,
and impact analysis for every LSP error. These types support the unified error
interface: codebase.errors(), codebase.full_error_context(), etc.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Union
import time
from pathlib import Path


class ErrorSeverity(Enum):
    """Error severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ErrorCategory(Enum):
    """Error categories for classification."""
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    TYPE = "type"
    IMPORT = "import"
    LINTING = "linting"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"


class FixDifficulty(Enum):
    """Difficulty level for auto-fixing errors."""
    TRIVIAL = "trivial"      # Simple fixes like adding colons, fixing typos
    EASY = "easy"            # Straightforward fixes like adding imports
    MEDIUM = "medium"        # Requires some logic like type annotations
    HARD = "hard"            # Complex refactoring needed
    IMPOSSIBLE = "impossible" # Cannot be automatically fixed


@dataclass
class CodeLocation:
    """Represents a location in code with rich context."""
    file_path: str
    line: int  # 1-based
    character: int  # 0-based
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    
    @property
    def range_str(self) -> str:
        """String representation of the location range."""
        if self.end_line and self.end_character:
            return f"{self.line}:{self.character}-{self.end_line}:{self.end_character}"
        return f"{self.line}:{self.character}"
    
    @property
    def file_name(self) -> str:
        """Get just the filename without path."""
        return Path(self.file_path).name


@dataclass
class SymbolInfo:
    """Information about a code symbol."""
    name: str
    symbol_type: str  # function, class, variable, import, etc.
    definition_location: Optional[CodeLocation] = None
    documentation: Optional[str] = None
    signature: Optional[str] = None
    return_type: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    scope: Optional[str] = None


@dataclass
class ErrorContext:
    """Rich context information for an error."""
    surrounding_code: str = ""  # ±10 lines around the error
    symbol_definitions: List[SymbolInfo] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    usage_patterns: List[Dict[str, Any]] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    ast_context: Optional[Dict[str, Any]] = None
    
    @property
    def has_rich_context(self) -> bool:
        """Check if this context has rich information."""
        return bool(
            self.symbol_definitions or 
            self.dependency_chain or 
            self.usage_patterns or
            self.related_files
        )


@dataclass
class ErrorReasoning:
    """Reasoning about why an error occurred."""
    root_cause: str = ""  # Primary reason for the error
    why_occurred: str = ""  # Detailed explanation
    semantic_analysis: Optional[str] = None
    causal_chain: List[str] = field(default_factory=list)
    similar_errors: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    
    @property
    def has_deep_analysis(self) -> bool:
        """Check if this reasoning has deep analysis."""
        return bool(
            self.semantic_analysis or 
            self.causal_chain or 
            self.similar_errors
        )


@dataclass
class ImpactAnalysis:
    """Analysis of how an error affects the codebase."""
    affected_symbols: List[str] = field(default_factory=list)
    cascading_effects: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    test_failures: List[str] = field(default_factory=list)
    dependent_files: List[str] = field(default_factory=list)
    severity_justification: Optional[str] = None
    
    @property
    def impact_score(self) -> float:
        """Calculate impact score (0.0 to 1.0)."""
        score = 0.0
        score += len(self.affected_symbols) * 0.1
        score += len(self.cascading_effects) * 0.2
        score += len(self.breaking_changes) * 0.3
        score += len(self.test_failures) * 0.2
        score += len(self.dependent_files) * 0.05
        return min(score, 1.0)


@dataclass
class FixSuggestion:
    """A suggested fix for an error."""
    fix_type: str  # add_import, fix_typo, add_type_annotation, etc.
    description: str  # Human-readable description
    code_change: Optional[str] = None  # Actual code to apply
    file_changes: Dict[str, str] = field(default_factory=dict)  # file -> new content
    confidence: float = 0.0  # 0.0 to 1.0
    difficulty: FixDifficulty = FixDifficulty.MEDIUM
    prerequisites: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    validation_steps: List[str] = field(default_factory=list)
    
    @property
    def is_safe(self) -> bool:
        """Check if this fix is safe to apply automatically."""
        return (
            self.confidence >= 0.8 and 
            self.difficulty in [FixDifficulty.TRIVIAL, FixDifficulty.EASY] and
            len(self.side_effects) == 0
        )


@dataclass
class EnhancedErrorInfo:
    """
    Enhanced error information with comprehensive context and reasoning.
    
    This is the primary error type returned by codebase.errors() and used
    throughout the enhanced error handling system.
    """
    # Basic error information
    id: str  # Unique identifier
    location: CodeLocation
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    error_type: str  # Specific error type (E001, S001, T001, etc.)
    source: str  # LSP server that detected this (pylsp, mypy, etc.)
    code: Optional[Union[str, int]] = None
    
    # Enhanced context and analysis
    context: ErrorContext = field(default_factory=ErrorContext)
    reasoning: ErrorReasoning = field(default_factory=ErrorReasoning)
    impact_analysis: ImpactAnalysis = field(default_factory=ImpactAnalysis)
    suggested_fixes: List[FixSuggestion] = field(default_factory=list)
    
    # Confidence and validation
    confidence_score: float = 1.0  # 0.0 to 1.0
    false_positive_likelihood: float = 0.0  # 0.0 to 1.0
    validation_status: str = "unvalidated"  # unvalidated, validated, false_positive
    
    # Metadata
    detected_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    related_errors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error (vs warning/info/hint)."""
        return self.severity == ErrorSeverity.ERROR
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning."""
        return self.severity == ErrorSeverity.WARNING
    
    @property
    def has_fix(self) -> bool:
        """Check if this error has suggested fixes."""
        return len(self.suggested_fixes) > 0
    
    @property
    def has_safe_fix(self) -> bool:
        """Check if this error has safe auto-fixes."""
        return any(fix.is_safe for fix in self.suggested_fixes)
    
    @property
    def is_likely_false_positive(self) -> bool:
        """Check if this is likely a false positive."""
        return self.false_positive_likelihood > 0.5
    
    @property
    def reliability_score(self) -> float:
        """Overall reliability score combining confidence and false positive likelihood."""
        return self.confidence_score * (1.0 - self.false_positive_likelihood)
    
    @property
    def display_name(self) -> str:
        """Human-readable display name for the error."""
        return f"{self.error_type}: {self.message}"
    
    @property
    def short_location(self) -> str:
        """Short location string for display."""
        return f"{self.location.file_name}:{self.location.line}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'location': {
                'file_path': self.location.file_path,
                'line': self.location.line,
                'character': self.location.character,
                'end_line': self.location.end_line,
                'end_character': self.location.end_character,
            },
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'error_type': self.error_type,
            'source': self.source,
            'code': self.code,
            'context': {
                'surrounding_code': self.context.surrounding_code,
                'symbol_definitions': [
                    {
                        'name': sym.name,
                        'type': sym.symbol_type,
                        'signature': sym.signature,
                        'documentation': sym.documentation,
                    }
                    for sym in self.context.symbol_definitions
                ],
                'dependency_chain': self.context.dependency_chain,
                'usage_patterns': self.context.usage_patterns,
                'related_files': self.context.related_files,
            },
            'reasoning': {
                'root_cause': self.reasoning.root_cause,
                'why_occurred': self.reasoning.why_occurred,
                'semantic_analysis': self.reasoning.semantic_analysis,
                'causal_chain': self.reasoning.causal_chain,
                'similar_errors': self.reasoning.similar_errors,
                'common_mistakes': self.reasoning.common_mistakes,
            },
            'impact_analysis': {
                'affected_symbols': self.impact_analysis.affected_symbols,
                'cascading_effects': self.impact_analysis.cascading_effects,
                'breaking_changes': self.impact_analysis.breaking_changes,
                'test_failures': self.impact_analysis.test_failures,
                'dependent_files': self.impact_analysis.dependent_files,
                'impact_score': self.impact_analysis.impact_score,
            },
            'suggested_fixes': [
                {
                    'fix_type': fix.fix_type,
                    'description': fix.description,
                    'code_change': fix.code_change,
                    'confidence': fix.confidence,
                    'difficulty': fix.difficulty.value,
                    'is_safe': fix.is_safe,
                    'prerequisites': fix.prerequisites,
                    'side_effects': fix.side_effects,
                }
                for fix in self.suggested_fixes
            ],
            'confidence_score': self.confidence_score,
            'false_positive_likelihood': self.false_positive_likelihood,
            'reliability_score': self.reliability_score,
            'has_fix': self.has_fix,
            'has_safe_fix': self.has_safe_fix,
            'is_likely_false_positive': self.is_likely_false_positive,
            'detected_at': self.detected_at,
            'last_updated': self.last_updated,
            'related_errors': self.related_errors,
            'tags': self.tags,
        }
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.severity.value.upper()} {self.short_location}: {self.message}"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"EnhancedErrorInfo(id='{self.id}', "
            f"location='{self.short_location}', "
            f"severity={self.severity.value}, "
            f"category={self.category.value}, "
            f"confidence={self.confidence_score:.2f}, "
            f"has_fix={self.has_fix})"
        )


@dataclass
class ErrorResolutionResult:
    """Result of attempting to resolve an error."""
    error_id: str
    success: bool
    applied_fixes: List[FixSuggestion] = field(default_factory=list)
    remaining_errors: List[str] = field(default_factory=list)
    new_errors: List[str] = field(default_factory=list)
    changes_made: Dict[str, str] = field(default_factory=dict)  # file -> changes
    execution_time: float = 0.0
    error_message: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None
    
    @property
    def was_successful(self) -> bool:
        """Check if resolution was successful."""
        return self.success and len(self.new_errors) == 0
    
    @property
    def caused_new_errors(self) -> bool:
        """Check if resolution caused new errors."""
        return len(self.new_errors) > 0


@dataclass
class BatchErrorResolutionResult:
    """Result of batch error resolution."""
    total_errors: int
    successful_fixes: int
    failed_fixes: int
    skipped_errors: int
    new_errors_introduced: int
    execution_time: float
    individual_results: List[ErrorResolutionResult] = field(default_factory=list)
    summary: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_errors == 0:
            return 0.0
        return self.successful_fixes / self.total_errors
    
    @property
    def overall_success(self) -> bool:
        """Check if batch resolution was overall successful."""
        return (
            self.success_rate >= 0.8 and 
            self.new_errors_introduced == 0
        )


# Type aliases for convenience
ErrorList = List[EnhancedErrorInfo]
ErrorDict = Dict[str, EnhancedErrorInfo]
FixList = List[FixSuggestion]
