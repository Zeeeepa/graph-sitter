"""
Comprehensive Error Analysis for Graph-Sitter

This module provides comprehensive error analysis capabilities by integrating
with existing LSP infrastructure and graph-sitter context analysis.
"""

import ast
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ErrorCategory(Enum):
    """Comprehensive error categories."""
    # Core Language
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    RUNTIME = "runtime"
    
    # Code Quality
    STYLE = "style"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    
    # Security & Safety
    SECURITY = "security"
    VULNERABILITY = "vulnerability"
    SAFETY = "safety"
    
    # Performance
    PERFORMANCE = "performance"
    MEMORY = "memory"
    OPTIMIZATION = "optimization"
    
    # Dependencies
    DEPENDENCY = "dependency"
    IMPORT = "import"
    COMPATIBILITY = "compatibility"
    
    # Code Organization
    UNUSED = "unused"
    DUPLICATE = "duplicate"
    DEAD_CODE = "dead_code"
    
    # Documentation & Testing
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    
    # Unknown
    UNKNOWN = "unknown"


@dataclass
class ErrorLocation:
    """Error location information."""
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    @property
    def range_text(self) -> str:
        """Get human-readable range text."""
        if self.end_line and self.end_column:
            return f"{self.line}:{self.column}-{self.end_line}:{self.end_column}"
        return f"{self.line}:{self.column}"
    
    @property
    def file_name(self) -> str:
        """Get just the filename."""
        return Path(self.file_path).name


@dataclass
class ErrorInfo:
    """Comprehensive error information."""
    id: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    location: ErrorLocation
    code: Optional[str] = None
    source: str = "graph_sitter"
    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    related_errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    @property
    def is_critical(self) -> bool:
        """Check if error is critical."""
        return self.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR]
    
    @property
    def display_text(self) -> str:
        """Get formatted display text."""
        return f"[{self.severity.value.upper()}] {self.location.file_name}:{self.location.range_text} - {self.message}"


@dataclass
class ComprehensiveErrorList:
    """Comprehensive list of errors with metadata."""
    errors: List[ErrorInfo] = field(default_factory=list)
    total_count: int = 0
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    files_analyzed: Set[str] = field(default_factory=set)
    analysis_timestamp: float = field(default_factory=time.time)
    analysis_duration: float = 0.0
    
    def __post_init__(self):
        """Calculate counts after initialization."""
        self._update_counts()
    
    def _update_counts(self):
        """Update error counts."""
        self.total_count = len(self.errors)
        self.critical_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.CRITICAL)
        self.error_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.ERROR)
        self.warning_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.WARNING)
        self.info_count = sum(1 for e in self.errors if e.severity in [ErrorSeverity.INFO, ErrorSeverity.HINT])
        self.files_analyzed = {e.location.file_path for e in self.errors}
    
    def add_error(self, error: ErrorInfo):
        """Add an error to the list."""
        self.errors.append(error)
        self._update_counts()
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorInfo]:
        """Get errors filtered by severity."""
        return [e for e in self.errors if e.severity == severity]
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorInfo]:
        """Get errors filtered by category."""
        return [e for e in self.errors if e.category == category]
    
    def get_errors_by_file(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        return [e for e in self.errors if e.location.file_path == file_path]
    
    def get_critical_errors(self) -> List[ErrorInfo]:
        """Get only critical errors."""
        return [e for e in self.errors if e.is_critical]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = len(self.get_errors_by_category(category))
        
        return {
            'total_errors': self.total_count,
            'critical_errors': self.critical_count,
            'errors': self.error_count,
            'warnings': self.warning_count,
            'info_hints': self.info_count,
            'files_with_errors': len(self.files_analyzed),
            'category_breakdown': category_counts,
            'analysis_timestamp': self.analysis_timestamp,
            'analysis_duration': self.analysis_duration
        }


class ComprehensiveErrorAnalyzer:
    """
    Comprehensive error analyzer that provides advanced error detection
    and analysis capabilities for graph-sitter codebases.
    """
    
    def __init__(self, codebase, enable_advanced_analysis: bool = True):
        self.codebase = codebase
        self.enable_advanced_analysis = enable_advanced_analysis
        self._error_cache: Dict[str, List[ErrorInfo]] = {}
        
        logger.info("Comprehensive error analyzer initialized")
    
    def get_comprehensive_errors(
        self,
        max_errors: Optional[int] = None,
        severity_filter: Optional[List[ErrorSeverity]] = None,
        include_context: bool = True,
        include_suggestions: bool = True
    ) -> ComprehensiveErrorList:
        """
        Get comprehensive error analysis for the entire codebase.
        
        Args:
            max_errors: Maximum number of errors to return
            severity_filter: Filter by error severities
            include_context: Whether to include error context
            include_suggestions: Whether to include fix suggestions
            
        Returns:
            Comprehensive error list with analysis
        """
        start_time = time.time()
        error_list = ComprehensiveErrorList()
        
        try:
            # Analyze all Python files in the codebase
            for file_obj in self.codebase.files:
                if not file_obj.file_path.endswith('.py'):
                    continue
                
                file_errors = self._analyze_file(
                    file_obj,
                    include_context=include_context,
                    include_suggestions=include_suggestions
                )
                
                for error in file_errors:
                    # Apply severity filter
                    if severity_filter and error.severity not in severity_filter:
                        continue
                    
                    error_list.add_error(error)
                    
                    # Apply max errors limit
                    if max_errors and len(error_list.errors) >= max_errors:
                        break
                
                if max_errors and len(error_list.errors) >= max_errors:
                    break
            
            error_list.analysis_duration = time.time() - start_time
            logger.info(f"Comprehensive analysis completed: {error_list.total_count} errors in {error_list.analysis_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Error during comprehensive analysis: {e}")
            error_list.analysis_duration = time.time() - start_time
        
        return error_list
    
    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        try:
            # Check cache first
            if file_path in self._error_cache:
                return self._error_cache[file_path]
            
            # Find file object
            file_obj = None
            for f in self.codebase.files:
                if f.file_path == file_path or f.name == file_path:
                    file_obj = f
                    break
            
            if not file_obj:
                return []
            
            # Analyze file
            errors = self._analyze_file(file_obj)
            self._error_cache[file_path] = errors
            
            return errors
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all errors in the codebase."""
        try:
            comprehensive_errors = self.get_comprehensive_errors()
            
            # Group errors by file
            errors_by_file = defaultdict(list)
            for error in comprehensive_errors.errors:
                errors_by_file[error.location.file_path].append(error)
            
            # Group errors by type
            errors_by_type = defaultdict(int)
            for error in comprehensive_errors.errors:
                errors_by_type[error.category.value] += 1
            
            return {
                'total_errors': comprehensive_errors.total_count,
                'critical_errors': comprehensive_errors.critical_count,
                'errors': comprehensive_errors.error_count,
                'warnings': comprehensive_errors.warning_count,
                'info_hints': comprehensive_errors.info_count,
                'files_with_errors': len(comprehensive_errors.files_analyzed),
                'errors_by_file': dict(errors_by_file),
                'errors_by_category': dict(errors_by_type),
                'most_problematic_files': self._get_most_problematic_files(errors_by_file),
                'analysis_duration': comprehensive_errors.analysis_duration
            }
            
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return {'error': str(e)}
    
    def _analyze_file(
        self,
        file_obj,
        include_context: bool = True,
        include_suggestions: bool = True
    ) -> List[ErrorInfo]:
        """Analyze a single file for errors."""
        errors = []
        
        try:
            # Parse the file content
            try:
                tree = ast.parse(file_obj.content)
            except SyntaxError as e:
                # Syntax error
                error = ErrorInfo(
                    id=f"syntax_{file_obj.file_path}_{e.lineno}",
                    message=f"Syntax error: {e.msg}",
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.SYNTAX,
                    location=ErrorLocation(
                        file_path=file_obj.file_path,
                        line=e.lineno or 1,
                        column=e.offset or 1
                    ),
                    suggestions=["Check for missing parentheses, brackets, or quotes", "Verify proper indentation"]
                )
                errors.append(error)
                return errors
            
            # Analyze AST for various error types
            errors.extend(self._analyze_ast(file_obj, tree, include_context, include_suggestions))
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_obj.file_path}: {e}")
        
        return errors
    
    def _analyze_ast(
        self,
        file_obj,
        tree: ast.AST,
        include_context: bool,
        include_suggestions: bool
    ) -> List[ErrorInfo]:
        """Analyze AST for various error types."""
        errors = []
        
        # Track variables and their usage
        defined_vars = set()
        used_vars = set()
        imports = set()
        
        for node in ast.walk(tree):
            # Track imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                for alias in node.names:
                    imports.add(alias.name)
            
            # Track variable definitions
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_vars.add(target.id)
            
            elif isinstance(node, ast.FunctionDef):
                defined_vars.add(node.name)
                # Check for unused parameters
                for arg in node.args.args:
                    param_name = arg.arg
                    if not self._is_param_used(node, param_name) and not param_name.startswith('_'):
                        error = ErrorInfo(
                            id=f"unused_param_{file_obj.file_path}_{node.lineno}_{param_name}",
                            message=f"Unused parameter '{param_name}' in function '{node.name}'",
                            severity=ErrorSeverity.WARNING,
                            category=ErrorCategory.UNUSED,
                            location=ErrorLocation(
                                file_path=file_obj.file_path,
                                line=node.lineno,
                                column=node.col_offset
                            ),
                            suggestions=[f"Remove unused parameter '{param_name}'", f"Prefix with underscore: '_{param_name}'"]
                        )
                        errors.append(error)
            
            elif isinstance(node, ast.ClassDef):
                defined_vars.add(node.name)
            
            # Track variable usage
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_vars.add(node.id)
        
        # Check for undefined variables
        undefined_vars = used_vars - defined_vars - imports - {'__name__', '__file__', '__doc__'}
        for var in undefined_vars:
            # Find the line where this variable is used
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == var and isinstance(node.ctx, ast.Load):
                    error = ErrorInfo(
                        id=f"undefined_{file_obj.file_path}_{node.lineno}_{var}",
                        message=f"Undefined variable '{var}'",
                        severity=ErrorSeverity.ERROR,
                        category=ErrorCategory.LOGIC,
                        location=ErrorLocation(
                            file_path=file_obj.file_path,
                            line=node.lineno,
                            column=node.col_offset
                        ),
                        suggestions=[f"Define variable '{var}' before use", f"Check for typos in '{var}'", f"Import '{var}' if it's from a module"]
                    )
                    errors.append(error)
                    break
        
        # Check for unused variables
        unused_vars = defined_vars - used_vars
        for var in unused_vars:
            if not var.startswith('_'):  # Skip variables that start with underscore
                # Find the line where this variable is defined
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == var:
                                error = ErrorInfo(
                                    id=f"unused_var_{file_obj.file_path}_{node.lineno}_{var}",
                                    message=f"Unused variable '{var}'",
                                    severity=ErrorSeverity.WARNING,
                                    category=ErrorCategory.UNUSED,
                                    location=ErrorLocation(
                                        file_path=file_obj.file_path,
                                        line=node.lineno,
                                        column=node.col_offset
                                    ),
                                    suggestions=[f"Remove unused variable '{var}'", f"Use variable '{var}' in your code", f"Prefix with underscore: '_{var}'"]
                                )
                                errors.append(error)
                                break
        
        # Check for complexity issues
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10:  # High complexity threshold
                    error = ErrorInfo(
                        id=f"complexity_{file_obj.file_path}_{node.lineno}_{node.name}",
                        message=f"Function '{node.name}' has high complexity ({complexity})",
                        severity=ErrorSeverity.WARNING,
                        category=ErrorCategory.COMPLEXITY,
                        location=ErrorLocation(
                            file_path=file_obj.file_path,
                            line=node.lineno,
                            column=node.col_offset
                        ),
                        suggestions=[f"Break down function '{node.name}' into smaller functions", "Reduce nested conditions and loops", "Extract complex logic into separate methods"]
                    )
                    errors.append(error)
        
        return errors
    
    def _is_param_used(self, func_node: ast.FunctionDef, param_name: str) -> bool:
        """Check if a parameter is used in the function body."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Name) and node.id == param_name and isinstance(node.ctx, ast.Load):
                return True
        return False
    
    def _calculate_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _get_most_problematic_files(self, errors_by_file: Dict[str, List[ErrorInfo]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get the files with the most errors."""
        file_error_counts = [(file_path, len(errors)) for file_path, errors in errors_by_file.items()]
        file_error_counts.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {'file_path': file_path, 'error_count': count}
            for file_path, count in file_error_counts[:limit]
        ]


# Add FullErrors property to Codebase class
def add_full_errors_to_codebase():
    """Add FullErrors property to Codebase class."""
    try:
        from graph_sitter.core.codebase import Codebase
        
        def _get_full_errors(self):
            """Get comprehensive error analysis."""
            if not hasattr(self, '_full_errors_analyzer'):
                self._full_errors_analyzer = ComprehensiveErrorAnalyzer(self)
            return self._full_errors_analyzer
        
        # Add property to Codebase class
        Codebase.FullErrors = property(_get_full_errors)
        
        logger.info("FullErrors property added to Codebase class")
        
    except ImportError:
        logger.warning("Could not add FullErrors property - Codebase class not available")
    except Exception as e:
        logger.error(f"Failed to add FullErrors property: {e}")


# Auto-add FullErrors property when module is imported
add_full_errors_to_codebase()


# Convenience functions
def analyze_codebase_errors(codebase, **kwargs) -> ComprehensiveErrorAnalyzer:
    """Create and return a comprehensive error analyzer for a codebase."""
    return ComprehensiveErrorAnalyzer(codebase, **kwargs)


def get_repo_error_analysis(repo_path: str, **kwargs) -> ComprehensiveErrorList:
    """Get comprehensive error analysis for a repository by path."""
    try:
        from graph_sitter.core.codebase import Codebase
        
        codebase = Codebase(repo_path)
        analyzer = ComprehensiveErrorAnalyzer(codebase)
        return analyzer.get_comprehensive_errors(**kwargs)
        
    except Exception as e:
        logger.error(f"Error analyzing repository {repo_path}: {e}")
        return ComprehensiveErrorList()
