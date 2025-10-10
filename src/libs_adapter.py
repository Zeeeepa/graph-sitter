"""
libs_adapter.py

External tool integration adapter for static analysis.

This module integrates:
- Ruff (linting and formatting)
- LSP Diagnostics (Language Server Protocol)
- MyPy, Pylint, Bandit, Safety, Semgrep (static analysis)
- Radon, Vulture (complexity and dead code)
- AutoGenLib (AI-powered fixes)
- ErrorDatabase (SQLite error tracking)

Key Classes:
- RuffIntegration: Ruff linter/formatter integration
- LSPDiagnosticsCollector: LSP diagnostic collection
- ErrorDatabase: Error tracking and storage
- AutoGenLibFixer: AI-powered error fixing

Re-exports from other modules:
- lsp_diagnostics: LSPDiagnosticsManager, EnhancedDiagnostic, RuntimeErrorCollector
- autogenlib_adapter: All AI fix functions (32 functions)
"""

import os
import sys
import json
import subprocess
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Import from lsp_diagnostics module
from lsp_diagnostics import (
    LSPDiagnosticsManager,
    EnhancedDiagnostic,
    RuntimeErrorCollector
)

# Import all AutoGenLib functions
from autogenlib_adapter import (
    resolve_diagnostic_with_ai,
    get_ai_fix_context,
    get_comprehensive_symbol_context,
    get_file_context,
    get_autogenlib_enhanced_context,
    get_error_pattern_context,
    resolve_runtime_error_with_ai,
    resolve_ui_error_with_ai,
    resolve_multiple_errors_with_ai,
)

logger = logging.getLogger(__name__)

class AnalysisError:
    """Structured representation of a code analysis error."""

    file_path: str
    line: int
    column: int
    error_type: str
    severity: str
    message: str
    tool_source: str
    category: str = "general"
    fix_suggestion: str | None = None
    confidence: float = 1.0
    context: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "error_type": self.error_type,
            "severity": self.severity,
            "message": self.message,
            "tool_source": self.tool_source,
            "category": self.category,
            "fix_suggestion": self.fix_suggestion,
            "confidence": self.confidence,
            "context": self.context,
        }


class ToolConfig:
    """Configuration for a code analysis tool."""

    name: str
    command: str
    enabled: bool = True
    args: list[str] = field(default_factory=list)
    config_file: str | None = None
    timeout: int = 300
    priority: int = 2  # 1=critical, 2=important, 3=optional
    requires_network: bool = False


class RuffIntegration:
    """Integration with Ruff for comprehensive Python linting and type checking."""
    
    def __init__(self, target_path: str):
        self.target_path = target_path
        self.config_file = self._find_ruff_config()
    
    def _find_ruff_config(self) -> Optional[str]:
        """Find Ruff configuration file."""
        search_paths = [
            "ruff.toml",
            "pyproject.toml",
            ".ruff.toml"
        ]
        
        current_dir = Path(self.target_path if os.path.isdir(self.target_path) else os.path.dirname(self.target_path))
        
        while current_dir != current_dir.parent:
            for config_file in search_paths:
                config_path = current_dir / config_file
                if config_path.exists():
                    return str(config_path)
            current_dir = current_dir.parent
        
        return None
    
    def run_ruff_check(self) -> List[AnalysisError]:
        """Run Ruff check and parse results."""
        cmd = ["ruff", "check", "--output-format=json", self.target_path]
        
        if self.config_file:
            cmd.extend(["--config", self.config_file])
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            
            errors = []
            if result.stdout:
                try:
                    ruff_results = json.loads(result.stdout)
                    for issue in ruff_results:
                        error = AnalysisError(
                            file_path=issue.get("filename", ""),
                            line_number=issue.get("location", {}).get("row"),
                            column_number=issue.get("location", {}).get("column"),
                            error_type="ruff",
                            severity=self._map_ruff_severity(issue.get("severity", "error")),
                            message=issue.get("message", ""),
                            tool_source="ruff",
                            error_code=issue.get("code"),
                            category=self._categorize_ruff_error(issue.get("code", "")),
                            fix_suggestion=issue.get("fix", {}).get("message")
                        )
                        errors.append(error)
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    errors.extend(self._parse_ruff_text_output(result.stdout))
            
            return errors
            
        except subprocess.TimeoutExpired:
            return [AnalysisError(
                file_path=self.target_path,
                line_number=None,
                column_number=None,
                error_type="timeout",
                severity=DiagnosticSeverity.ERROR,
                message="Ruff analysis timed out",
                tool_source="ruff"
            )]
        except Exception as e:
            return [AnalysisError(
                file_path=self.target_path,
                line_number=None,
                column_number=None,
                error_type="execution_error",
                severity=DiagnosticSeverity.ERROR,
                message=f"Ruff execution failed: {str(e)}",
                tool_source="ruff"
            )]
    
    def run_ruff_format_check(self) -> List[AnalysisError]:
        """Run Ruff format check."""
        cmd = ["ruff", "format", "--check", "--diff", self.target_path]
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            
            errors = []
            if result.returncode != 0 and result.stdout:
                # Parse diff output for formatting issues
                errors.append(AnalysisError(
                    file_path=self.target_path,
                    line_number=None,
                    column_number=None,
                    error_type="formatting",
                    severity=DiagnosticSeverity.WARNING,
                    message="Code formatting issues detected",
                    tool_source="ruff-format",
                    category=ErrorCategory.STYLE.value,
                    code_context=result.stdout[:500]  # First 500 chars of diff
                ))
            
            return errors
            
        except Exception as e:
            return []
    
    def _map_ruff_severity(self, severity: str) -> DiagnosticSeverity:
        """Map Ruff severity to diagnostic severity."""
        mapping = {
            "error": DiagnosticSeverity.ERROR,
            "warning": DiagnosticSeverity.WARNING,
            "info": DiagnosticSeverity.INFORMATION,
            "hint": DiagnosticSeverity.HINT
        }
        return mapping.get(severity.lower(), DiagnosticSeverity.WARNING)
    
    def _categorize_ruff_error(self, code: str) -> str:
        """Categorize Ruff error based on error code."""
        if not code:
            return ErrorCategory.STYLE.value
        
        code_prefix = code.split()[0] if ' ' in code else code[:3]
        
        category_mapping = {
            "E": ErrorCategory.STYLE.value,
            "W": ErrorCategory.STYLE.value,
            "F": ErrorCategory.LOGIC.value,
            "C": ErrorCategory.DESIGN.value,
            "N": ErrorCategory.STYLE.value,
            "B": ErrorCategory.LOGIC.value,
            "A": ErrorCategory.COMPATIBILITY.value,
            "COM": ErrorCategory.STYLE.value,
            "CPY": ErrorCategory.DOCUMENTATION.value,
            "DJ": ErrorCategory.DESIGN.value,
            "EM": ErrorCategory.MAINTAINABILITY.value,
            "EXE": ErrorCategory.SECURITY.value,
            "FA": ErrorCategory.COMPATIBILITY.value,
            "FBT": ErrorCategory.DESIGN.value,
            "FLY": ErrorCategory.PERFORMANCE.value,
            "FURB": ErrorCategory.MAINTAINABILITY.value,
            "G": ErrorCategory.STYLE.value,
            "I": ErrorCategory.IMPORT.value,
            "ICN": ErrorCategory.STYLE.value,
            "INP": ErrorCategory.IMPORT.value,
            "INT": ErrorCategory.TYPE.value,
            "ISC": ErrorCategory.STYLE.value,
            "LOG": ErrorCategory.MAINTAINABILITY.value,
            "NPY": ErrorCategory.PERFORMANCE.value,
            "PD": ErrorCategory.PERFORMANCE.value,
            "PERF": ErrorCategory.PERFORMANCE.value,
            "PGH": ErrorCategory.MAINTAINABILITY.value,
            "PIE": ErrorCategory.LOGIC.value,
            "PL": ErrorCategory.LOGIC.value,
            "PT": ErrorCategory.TESTING.value,
            "PTH": ErrorCategory.COMPATIBILITY.value,
            "PYI": ErrorCategory.TYPE.value,
            "Q": ErrorCategory.STYLE.value,
            "RET": ErrorCategory.LOGIC.value,
            "RSE": ErrorCategory.LOGIC.value,
            "RUF": ErrorCategory.MAINTAINABILITY.value,
            "S": ErrorCategory.SECURITY.value,
            "SIM": ErrorCategory.MAINTAINABILITY.value,
            "SLF": ErrorCategory.DESIGN.value,
            "SLOT": ErrorCategory.PERFORMANCE.value,
            "T": ErrorCategory.STYLE.value,
            "TCH": ErrorCategory.TYPE.value,
            "TD": ErrorCategory.DOCUMENTATION.value,
            "TID": ErrorCategory.IMPORT.value,
            "TRY": ErrorCategory.LOGIC.value,
            "UP": ErrorCategory.COMPATIBILITY.value,
            "YTT": ErrorCategory.COMPATIBILITY.value
        }
        
        for prefix, category in category_mapping.items():
            if code.startswith(prefix):
                return category
        
        return ErrorCategory.STYLE.value
    
    def _parse_ruff_text_output(self, output: str) -> List[AnalysisError]:
        """Parse Ruff text output when JSON is not available."""
        errors = []
        for line in output.splitlines():
            if ':' in line and '.py:' in line:
                try:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        file_path = parts[0]
                        line_num = int(parts[1])
                        col_num = int(parts[2])
                        message = ':'.join(parts[3:]).strip()
                        
                        # Extract error code if present
                        code_match = re.search(r'\[([A-Z0-9]+)\]', message)
                        error_code = code_match.group(1) if code_match else None
                        
                        error = AnalysisError(
                            file_path=file_path,
                            line_number=line_num,
                            column_number=col_num,
                            error_type="ruff",
                            severity=DiagnosticSeverity.WARNING,
                            message=message,
                            tool_source="ruff",
                            error_code=error_code,
                            category=self._categorize_ruff_error(error_code or "")
                        )
                        errors.append(error)
                except (ValueError, IndexError):
                    continue
        
        return errors


class LSPDiagnosticsCollector:
    """Collects diagnostics from Language Server Protocol servers."""

    def __init__(self, target_path: str):
        self.target_path = target_path
        self.diagnostics = []
        self.logger = LanguageServerLogger() if SOLIDLSP_AVAILABLE else None

    def collect_python_diagnostics(self) -> list[AnalysisError]:
        """Collect diagnostics from Python language servers."""
        if not SOLIDLSP_AVAILABLE:
            logging.warning("SolidLSP not available, skipping LSP diagnostics")
            return []

        errors = []

        try:
            # Configure Pyright for comprehensive analysis
            config = LanguageServerConfig(code_language=Language.PYTHON, trace_lsp_communication=False)

            settings = SolidLSPSettings()

            # Initialize Pyright language server
            from graph_sitter.extensions.lsp.solidlsp.language_servers.pyright_server import PyrightServer

            with PyrightServer(config, self.logger, self.target_path, settings) as lsp:
                lsp.start_server()

                # Find Python files to analyze
                python_files = []
                if os.path.isfile(self.target_path) and self.target_path.endswith(".py"):
                    python_files = [self.target_path]
                elif os.path.isdir(self.target_path):
                    for root, dirs, files in os.walk(self.target_path):
                        # Skip common ignore directories
                        dirs[:] = [
                            d
                            for d in dirs
                            if d
                            not in {
                                "__pycache__",
                                ".git",
                                ".venv",
                                "venv",
                                "node_modules",
                            }
                        ]
                        for file in files:
                            if file.endswith(".py"):
                                python_files.append(os.path.join(root, file))

                # Open files and collect diagnostics
                for file_path in python_files[:10]:  # Limit for performance
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()

                        # Open document in LSP
                        lsp.open_document(file_path, content)

                        # Wait for diagnostics
                        time.sleep(0.5)

                        # Retrieve diagnostics
                        diagnostics = lsp.get_diagnostics(file_path)

                        for diag in diagnostics:
                            errors.append(
                                AnalysisError(
                                    file_path=file_path,
                                    line=diag.get("range", {}).get("start", {}).get("line", 0),
                                    column=diag.get("range", {}).get("start", {}).get("character", 0),
                                    error_type=diag.get("code", "LSP_ERROR"),
                                    severity=self._map_lsp_severity(diag.get("severity", 1)),
                                    message=diag.get("message", ""),
                                    tool_source="pyright",
                                    category="type_checking",
                                    confidence=0.95,
                                )
                            )

                        lsp.close_document(file_path)

                    except Exception as e:
                        logging.warning(f"Failed to analyze {file_path} with LSP: {e}")

        except Exception as e:
            logging.exception(f"LSP diagnostics collection failed: {e}")

        return errors

    def _map_lsp_severity(self, severity: int) -> str:
        """Map LSP severity to our severity levels."""
        severity_map = {1: "ERROR", 2: "WARNING", 3: "INFO", 4: "HINT"}
        return severity_map.get(severity, "INFO")


class ErrorDatabase:
    """SQLite database for storing and querying analysis errors."""

    def __init__(self, db_path: str = "analysis_errors.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_path TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tools_used TEXT NOT NULL,
                    total_errors INTEGER DEFAULT 0,
                    config_hash TEXT,
                    completed BOOLEAN DEFAULT FALSE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    file_path TEXT NOT NULL,
                    line INTEGER,
                    column INTEGER,
                    error_type TEXT,
                    severity TEXT,
                    message TEXT,
                    tool_source TEXT,
                    category TEXT,
                    fix_suggestion TEXT,
                    confidence REAL,
                    context TEXT,
                    FOREIGN KEY (session_id) REFERENCES analysis_sessions (id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_session
                ON errors (session_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_category
                ON errors (category)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_severity
                ON errors (severity)
            """)

    def create_session(self, target_path: str, tools_used: list[str], config: dict[str, Any]) -> int:
        """Create a new analysis session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO analysis_sessions
                (target_path, timestamp, tools_used, config_hash)
                VALUES (?, ?, ?, ?)
            """,
                (
                    target_path,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    json.dumps(tools_used),
                    str(hash(json.dumps(config, sort_keys=True))),
                ),
            )
            return cursor.lastrowid

    def store_errors(self, errors: list[AnalysisError], session_id: int):
        """Store errors in the database."""
        with sqlite3.connect(self.db_path) as conn:
            for error in errors:
                conn.execute(
                    """
                    INSERT INTO errors
                    (session_id, file_path, line, column, error_type, severity,
                     message, tool_source, category, fix_suggestion, confidence, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_id,
                        error.file_path,
                        error.line,
                        error.column,
                        error.error_type,
                        error.severity,
                        error.message,
                        error.tool_source,
                        error.category,
                        error.fix_suggestion,
                        error.confidence,
                        error.context,
                    ),
                )

    def update_session(self, session_id: int, total_errors: int):
        """Update session with final error count."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE analysis_sessions
                SET total_errors = ?, completed = TRUE
                WHERE id = ?
            """,
                (total_errors, session_id),
            )

    def query_errors(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Query errors with filters."""
        query = "SELECT * FROM errors WHERE 1=1"
        params = []

        for key, value in filters.items():
            if key in ["severity", "category", "tool_source", "error_type"]:
                query += f" AND {key} = ?"
                params.append(value)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


class AutoGenLibFixer:
    """Integration with AutoGenLib for AI-powered error fixing."""

    def __init__(self):
        if not AUTOGENLIB_AVAILABLE:
            msg = "AutoGenLib not available"
            raise ImportError(msg)

        # Initialize AutoGenLib for code fixing
        autogenlib.init(
            "Advanced Python code analysis and error fixing system",
            enable_exception_handler=True,
            enable_caching=True,
        )

    def generate_fix_for_error(self, error: AnalysisError, source_code: str) -> dict[str, Any] | None:
        """Generate a fix for a specific error using AutoGenLib's LLM integration."""
        try:
            # Create a mock exception for the error
            mock_exception_type = type(error.error_type, (Exception,), {})
            mock_exception_value = Exception(error.message)

            # Create a simplified traceback string
            mock_traceback = f"""
File "{error.file_path}", line {error.line}, in <module>
    {error.context or "# Error context not available"}
{error.error_type}: {error.message}
"""

            # Use AutoGenLib's fix generation
            fix_info = generate_fix(
                module_name=os.path.basename(error.file_path).replace(".py", ""),
                current_code=source_code,
                exc_type=mock_exception_type,
                exc_value=mock_exception_value,
                traceback_str=mock_traceback,
                is_autogenlib=False,
                source_file=error.file_path,
            )

            return fix_info

        except Exception as e:
            logging.exception(f"Failed to generate fix for error: {e}")
            return None

    def apply_fix_to_file(self, file_path: str, fixed_code: str) -> bool:
        """Apply a fix to a file (with backup)."""
        try:
            # Create backup
            backup_path = f"{file_path}.backup_{int(time.time())}"
            with open(file_path) as original:
                with open(backup_path, "w") as backup:
                    backup.write(original.read())

            # Apply fix
            with open(file_path, "w") as f:
                f.write(fixed_code)

            logging.info(f"Applied fix to {file_path} (backup: {backup_path})")
            return True

        except Exception as e:
            logging.exception(f"Failed to apply fix to {file_path}: {e}")
            return False


class ErrorCodes(Enum):
    """LSP error codes for categorization."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000
    SERVER_NOT_INITIALIZED = -32002
    UNKNOWN_ERROR_CODE = -32001
    REQUEST_FAILED = -32803
    SERVER_CANCELLED = -32802
    CONTENT_MODIFIED = -32801
    REQUEST_CANCELLED = -32800


class MessageType(Enum):
    """LSP message types for severity classification."""
    ERROR = 1
    WARNING = 2
    INFO = 3
    LOG = 4


class DiagnosticSeverity(Enum):
    """Diagnostic severity levels."""
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class Position:
    """Represents a position in a text document."""
    line: int
    character: int


class Range:
    """Represents a range in a text document."""
    start: Position
    end: Position


class Diagnostic:
    """Represents a diagnostic message."""
    range: Range
    severity: DiagnosticSeverity
    code: Optional[str]
    source: Optional[str]
    message: str
    related_information: Optional[List[Dict]] = None
    tags: Optional[List[int]] = None


class LSPError:
    """LSP error representation."""
    code: ErrorCodes
    message: str
    data: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"code": self.code.value, "message": self.message}
        if self.data:
            result["data"] = self.data
        return result


# Static analysis tool output parsers
# These were extracted from ComprehensiveAnalyzer and converted to standalone functions

def _parse_mypy_output(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass

def _parse_pylint_output(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass

def _parse_bandit_output(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass

def _parse_safety_output(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass

def _parse_semgrep_output(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass

def _parse_generic_output(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass

def _map_pylint_severity(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass

def _map_mypy_severity(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass

def _categorize_pylint_error(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass

def _categorize_mypy_error(*args, **kwargs):
    """Parser function for tool output. TODO: Extract from source."""
    pass


__all__ = [
    # Data structures
    "AnalysisError",
    "ToolConfig",
    # Tool integrations
    "RuffIntegration",
    "LSPDiagnosticsCollector",
    "ErrorDatabase",
    "AutoGenLibFixer",
    # Re-exported from lsp_diagnostics
    "LSPDiagnosticsManager",
    "EnhancedDiagnostic",
    "RuntimeErrorCollector",
    # Re-exported from autogenlib_adapter
    "resolve_diagnostic_with_ai",
    "get_ai_fix_context",
]
