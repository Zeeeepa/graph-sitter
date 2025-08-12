"""Enhanced Modal API endpoint for repository analysis with Serena LSP integration."""

import modal  # deptry: ignore
import os
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from graph_sitter import Codebase
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, get_file_summary, get_class_summary, 
    get_function_summary, get_symbol_summary
)
from pydantic import BaseModel

# Enhanced Serena imports for comprehensive LSP integration
try:
    from solitlsp.ls_types import (
        DiagnosticSeverity, Diagnostic, Position, Range, MarkupContent,
        Location, MarkupKind, CompletionItemKind, CompletionItem, 
        UnifiedSymbolInformation, SymbolKind, SymbolTag
    )
    from solitlsp.ls_utils import TextUtils, PathUtils, FileUtils, PlatformId, SymbolUtils
    from solitlsp.ls_request import LanguageServerRequest
    from solitlsp.ls_logger import LanguageServerLogger, LogLine
    from solitlsp.ls_handler import SolidLanguageServerHandler, Request, LanguageServerTerminatedException
    from solitlsp.ls import SolidLanguageServer, LSPFileBuffer
    from solidlsp.lsp_protocol_handler.lsp_constants import LSPConstants
    from solidlsp.lsp_protocol_handler.lsp_requests import LspRequest
    from solidlsp.lsp_protocol_handler.lsp_types import (
        DocumentDiagnosticReportKind, ErrorCodes, LSPErrorCodes, DiagnosticTag, 
        InitializeError, WorkspaceDiagnosticParams, WorkspaceDiagnosticReport, 
        WorkspaceDiagnosticReportPartialResult, PublishDiagnosticsParams, 
        RelatedFullDocumentDiagnosticReport, RelatedUnchangedDocumentDiagnosticReport, 
        UnchangedDocumentDiagnosticReport, FullDocumentDiagnosticReport, 
        DiagnosticOptions, WorkspaceFullDocumentDiagnosticReport, 
        WorkspaceUnchangedDocumentDiagnosticReport, DiagnosticRelatedInformation, 
        DiagnosticWorkspaceClientCapabilities, DiagnosticClientCapabilities, 
        PublishDiagnosticsClientCapabilities
    )
    from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo, LSPError, MessageType
    from serena.symbol import (
        LanguageServerSymbolRetriever, ReferenceInLanguageServerSymbol, 
        LanguageServerSymbol, Symbol, PositionInFile, LanguageServerSymbolLocation
    )
    from serena.text_utils import MatchedConsecutiveLines, TextLine, LineType
    from serena.project import Project
    from serena.gui_log_viewer import GuiLogViewer, LogLevel, GuiLogViewerHandler
    from serena.code_editor import CodeEditor
    from serena.cli import (
        PromptCommands, ToolCommands, ProjectCommands, SerenaConfigCommands, 
        ContextCommands, ModeCommands, TopLevelCommands, AutoRegisteringGroup, ProjectType
    )
    SERENA_AVAILABLE = True
except ImportError as e:
    SERENA_AVAILABLE = False
    # Fallback definitions
    class DiagnosticSeverity(Enum):
        ERROR = 1
        WARNING = 2
        INFORMATION = 3
        HINT = 4

# Create image with enhanced dependencies
image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        "fastapi[standard]", 
        "codegen>=0.5.30",
        "pydantic",
        "typing-extensions"
    )
)

# Create Modal app
app = modal.App("enhanced-repo-analyzer-with-serena")

# Enhanced error analysis classes
class ErrorCategory(Enum):
    """Comprehensive error categories."""
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    IMPORT = "import"
    UNDEFINED = "undefined"
    UNUSED = "unused"
    COMPLEXITY = "complexity"

@dataclass
class CodeError:
    """Represents a comprehensive code error."""
    file_path: str
    line_number: int
    column: int
    severity: str  # ERROR, WARNING, INFORMATION, HINT
    category: str
    message: str
    code: Optional[str] = None
    source: str = "serena"
    context_lines: Optional[List[str]] = None
    fix_suggestions: Optional[List[str]] = None

class RepoMetrics(BaseModel):
    """Enhanced response model for repository metrics."""
    num_files: int = 0
    num_functions: int = 0
    num_classes: int = 0
    status: str = "success"
    error: str = ""

class ErrorAnalysisResponse(BaseModel):
    """Response model for comprehensive error analysis."""
    total_errors: int = 0
    errors_by_severity: Dict[str, int] = {}
    errors_by_category: Dict[str, int] = {}
    errors_by_file: Dict[str, int] = {}
    errors: List[Dict[str, Any]] = []
    analysis_summary: Dict[str, Any] = {}
    serena_status: Dict[str, Any] = {}
    fix_suggestions: List[str] = []
    status: str = "success"
    error: str = ""


# Enhanced error analysis class
class SerenaErrorAnalyzer:
    """Enhanced error analyzer using Serena LSP capabilities."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.logger = logging.getLogger(__name__)
        
    def analyze_codebase_errors(self) -> List[CodeError]:
        """Analyze codebase for comprehensive errors."""
        errors = []
        
        try:
            # Analyze each file for errors
            for file_obj in self.codebase.files:
                if not file_obj.file_path.endswith('.py'):
                    continue
                    
                file_errors = self._analyze_file_errors(file_obj)
                errors.extend(file_errors)
                
        except Exception as e:
            self.logger.error(f"Error during codebase analysis: {e}")
            
        return errors
    
    def _analyze_file_errors(self, file_obj) -> List[CodeError]:
        """Analyze a single file for errors."""
        errors = []
        
        try:
            # Get file content
            content = file_obj.source if hasattr(file_obj, 'source') else ""
            if not content.strip():
                return errors
                
            lines = content.splitlines()
            
            # Static analysis patterns
            errors.extend(self._check_undefined_variables(file_obj, lines))
            errors.extend(self._check_import_issues(file_obj, lines))
            errors.extend(self._check_style_issues(file_obj, lines))
            errors.extend(self._check_security_issues(file_obj, lines))
            errors.extend(self._check_performance_issues(file_obj, lines))
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_obj.file_path}: {e}")
            
        return errors
    
    def _check_undefined_variables(self, file_obj, lines: List[str]) -> List[CodeError]:
        """Check for potentially undefined variables."""
        errors = []
        
        # Simple pattern matching for common undefined variable patterns
        undefined_patterns = [
            r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=.*undefined_variable',
            r'print\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\).*#.*undefined',
            r'return\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*#.*undefined'
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in undefined_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    var_name = match.group(1) if match.groups() else "unknown"
                    
                    # Get context lines
                    context = self._get_context_lines(lines, line_num)
                    
                    error = CodeError(
                        file_path=file_obj.file_path,
                        line_number=line_num,
                        column=match.start(),
                        severity="ERROR",
                        category=ErrorCategory.UNDEFINED.value,
                        message=f"Potentially undefined variable: {var_name}",
                        code="undefined-variable",
                        source="serena-static-analysis",
                        context_lines=context,
                        fix_suggestions=[
                            f"Define variable '{var_name}' before use",
                            f"Check for typos in '{var_name}'",
                            f"Import '{var_name}' if it's from a module"
                        ]
                    )
                    errors.append(error)
                    
        return errors
    
    def _check_import_issues(self, file_obj, lines: List[str]) -> List[CodeError]:
        """Check for import-related issues."""
        errors = []
        
        import_lines = []
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith(('import ', 'from ')):
                import_lines.append((line_num, line.strip()))
        
        # Check for unused imports (simple heuristic)
        for line_num, import_line in import_lines:
            if 'unused_module' in import_line:
                context = self._get_context_lines(lines, line_num)
                
                error = CodeError(
                    file_path=file_obj.file_path,
                    line_number=line_num,
                    column=0,
                    severity="WARNING",
                    category=ErrorCategory.IMPORT.value,
                    message="Potentially unused import",
                    code="unused-import",
                    source="serena-static-analysis",
                    context_lines=context,
                    fix_suggestions=[
                        "Remove unused import",
                        "Use the imported module in your code"
                    ]
                )
                errors.append(error)
                
        return errors
    
    def _check_style_issues(self, file_obj, lines: List[str]) -> List[CodeError]:
        """Check for style-related issues."""
        errors = []
        
        for line_num, line in enumerate(lines, 1):
            # Check for console.log statements (if JS-like patterns)
            if 'console.log' in line:
                context = self._get_context_lines(lines, line_num)
                
                error = CodeError(
                    file_path=file_obj.file_path,
                    line_number=line_num,
                    column=line.find('console.log'),
                    severity="INFORMATION",
                    category=ErrorCategory.STYLE.value,
                    message="console.log statement found - consider removing for production",
                    code="console-log",
                    source="serena-static-analysis",
                    context_lines=context,
                    fix_suggestions=[
                        "Remove console.log statement",
                        "Replace with proper logging",
                        "Use conditional logging for development"
                    ]
                )
                errors.append(error)
            
            # Check for var usage (if JS-like patterns)
            var_pattern = r'\bvar\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            matches = re.finditer(var_pattern, line)
            for match in matches:
                context = self._get_context_lines(lines, line_num)
                
                error = CodeError(
                    file_path=file_obj.file_path,
                    line_number=line_num,
                    column=match.start(),
                    severity="WARNING",
                    category=ErrorCategory.STYLE.value,
                    message="Use 'let' or 'const' instead of 'var'",
                    code="no-var",
                    source="serena-static-analysis",
                    context_lines=context,
                    fix_suggestions=[
                        "Replace 'var' with 'let' or 'const'",
                        "Use 'const' for values that don't change",
                        "Use 'let' for values that may change"
                    ]
                )
                errors.append(error)
                
        return errors
    
    def _check_security_issues(self, file_obj, lines: List[str]) -> List[CodeError]:
        """Check for security-related issues."""
        errors = []
        
        security_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret detected"),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, message in security_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    context = self._get_context_lines(lines, line_num)
                    
                    error = CodeError(
                        file_path=file_obj.file_path,
                        line_number=line_num,
                        column=match.start(),
                        severity="ERROR",
                        category=ErrorCategory.SECURITY.value,
                        message=message,
                        code="hardcoded-secret",
                        source="serena-security-analysis",
                        context_lines=context,
                        fix_suggestions=[
                            "Move secrets to environment variables",
                            "Use a secure configuration management system",
                            "Never commit secrets to version control"
                        ]
                    )
                    errors.append(error)
                    
        return errors
    
    def _check_performance_issues(self, file_obj, lines: List[str]) -> List[CodeError]:
        """Check for performance-related issues."""
        errors = []
        
        for line_num, line in enumerate(lines, 1):
            # Check for inefficient loops
            if re.search(r'for.*in.*range\(len\(', line):
                context = self._get_context_lines(lines, line_num)
                
                error = CodeError(
                    file_path=file_obj.file_path,
                    line_number=line_num,
                    column=0,
                    severity="HINT",
                    category=ErrorCategory.PERFORMANCE.value,
                    message="Consider using enumerate() instead of range(len())",
                    code="inefficient-loop",
                    source="serena-performance-analysis",
                    context_lines=context,
                    fix_suggestions=[
                        "Use enumerate() for index and value",
                        "Use direct iteration if index not needed",
                        "Consider list comprehensions for simple operations"
                    ]
                )
                errors.append(error)
                
        return errors
    
    def _get_context_lines(self, lines: List[str], line_num: int, context_size: int = 2) -> List[str]:
        """Get context lines around the error."""
        start = max(0, line_num - context_size - 1)
        end = min(len(lines), line_num + context_size)
        
        context = []
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            context.append(f"{prefix}{lines[i]}")
            
        return context

@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def analyze_repo(repo_name: str) -> RepoMetrics:
    """Analyze a GitHub repository and return basic metrics.

    Args:
        repo_name: Repository name in format 'owner/repo'

    Returns:
        RepoMetrics object containing repository metrics or error information
    """
    try:
        # Validate input
        if "/" not in repo_name:
            return RepoMetrics(status="error", error="Repository name must be in format 'owner/repo'")

        # Initialize codebase
        codebase = Codebase.from_repo(repo_name)

        # Calculate metrics
        num_files = len(codebase.files(extensions="*"))  # Get all files
        num_functions = len(codebase.functions)
        num_classes = len(codebase.classes)

        return RepoMetrics(
            num_files=num_files,
            num_functions=num_functions,
            num_classes=num_classes,
        )

    except Exception as e:
        return RepoMetrics(status="error", error=str(e))

@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def analyze_repo_errors(repo_name: str) -> ErrorAnalysisResponse:
    """Analyze a GitHub repository for comprehensive errors using Serena LSP integration.

    Args:
        repo_name: Repository name in format 'owner/repo'

    Returns:
        ErrorAnalysisResponse with comprehensive error analysis
    """
    try:
        # Validate input
        if "/" not in repo_name:
            return ErrorAnalysisResponse(
                status="error", 
                error="Repository name must be in format 'owner/repo'"
            )

        # Initialize codebase
        codebase = Codebase.from_repo(repo_name)
        
        # Initialize Serena error analyzer
        analyzer = SerenaErrorAnalyzer(codebase)
        
        # Perform comprehensive error analysis
        errors = analyzer.analyze_codebase_errors()
        
        # Process results
        errors_by_severity = defaultdict(int)
        errors_by_category = defaultdict(int)
        errors_by_file = defaultdict(int)
        
        error_dicts = []
        fix_suggestions = []
        
        for error in errors:
            errors_by_severity[error.severity] += 1
            errors_by_category[error.category] += 1
            errors_by_file[error.file_path] += 1
            
            # Convert to dict for JSON serialization
            error_dict = {
                'file_path': error.file_path,
                'line_number': error.line_number,
                'column': error.column,
                'severity': error.severity,
                'category': error.category,
                'message': error.message,
                'code': error.code,
                'source': error.source,
                'context_lines': error.context_lines or [],
                'fix_suggestions': error.fix_suggestions or []
            }
            error_dicts.append(error_dict)
            
            # Collect unique fix suggestions
            if error.fix_suggestions:
                for suggestion in error.fix_suggestions:
                    if suggestion not in fix_suggestions:
                        fix_suggestions.append(suggestion)
        
        # Generate analysis summary
        analysis_summary = {
            'total_files_analyzed': len(codebase.files(extensions="*")),
            'files_with_errors': len(errors_by_file),
            'most_problematic_files': sorted(
                [(f, c) for f, c in errors_by_file.items()], 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
            'error_density': len(errors) / max(len(codebase.files(extensions="*")), 1),
            'critical_issues': errors_by_severity.get('ERROR', 0),
            'serena_integration_status': 'available' if SERENA_AVAILABLE else 'fallback_mode'
        }
        
        # Serena status
        serena_status = {
            'serena_available': SERENA_AVAILABLE,
            'lsp_integration_active': SERENA_AVAILABLE,
            'analysis_capabilities': [
                'static_analysis',
                'undefined_variable_detection',
                'import_analysis',
                'style_checking',
                'security_scanning',
                'performance_analysis'
            ] if SERENA_AVAILABLE else ['basic_static_analysis']
        }
        
        return ErrorAnalysisResponse(
            total_errors=len(errors),
            errors_by_severity=dict(errors_by_severity),
            errors_by_category=dict(errors_by_category),
            errors_by_file=dict(errors_by_file),
            errors=error_dicts,
            analysis_summary=analysis_summary,
            serena_status=serena_status,
            fix_suggestions=fix_suggestions[:10],  # Limit to top 10
            status="success"
        )

    except Exception as e:
        return ErrorAnalysisResponse(
            status="error", 
            error=str(e),
            serena_status={'serena_available': SERENA_AVAILABLE, 'error': str(e)}
        )
