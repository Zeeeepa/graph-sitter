"""Shared utilities for code analysis.

This module provides common data structures, helper functions, and utilities
used across all analysis modules. It eliminates code duplication and establishes
a foundation for the refactored architecture.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AnalysisError:
    """Standardized error representation for all analysis tools.
    
    This data structure is compatible with LSP diagnostics and provides
    a unified interface for error handling across ruff, mypy, pylint,
    and graph-sitter analysis.
    """
    
    file_path: str
    line: int
    column: int
    error_type: str
    severity: str  # 'error', 'warning', 'info', 'hint'
    message: str
    tool_source: str  # 'ruff', 'mypy', 'pylint', 'pyright', 'lsp', 'graph-sitter'
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


@dataclass
class ToolConfig:
    """Configuration for external analysis tools."""
    
    name: str
    command: str
    enabled: bool = True
    args: list[str] = field(default_factory=list)
    config_file: str | None = None
    timeout: int = 300
    priority: int = 2  # 1=critical, 2=important, 3=optional
    requires_network: bool = False


# Severity mapping utilities
SEVERITY_LEVELS = {
    "error": 4,
    "warning": 3,
    "info": 2,
    "hint": 1,
}


def severity_to_level(severity: str) -> int:
    """Convert severity string to numeric level for sorting."""
    return SEVERITY_LEVELS.get(severity.lower(), 0)


def level_to_severity(level: int) -> str:
    """Convert numeric level back to severity string."""
    for sev, lev in SEVERITY_LEVELS.items():
        if lev == level:
            return sev
    return "info"


# File path utilities
def normalize_path(path: str, base_path: str = "") -> str:
    """Normalize file path relative to base directory."""
    import os
    
    if base_path:
        try:
            return os.path.relpath(path, base_path)
        except ValueError:
            # Paths on different drives (Windows)
            return path
    return os.path.normpath(path)


def is_python_file(path: str) -> bool:
    """Check if file is a Python source file."""
    return path.endswith(('.py', '.pyi'))


def is_test_file(path: str) -> bool:
    """Check if file is a test file."""
    return 'test' in path.lower() or path.startswith('tests/')


# String formatting utilities
def truncate_message(message: str, max_length: int = 200) -> str:
    """Truncate long messages with ellipsis."""
    if len(message) <= max_length:
        return message
    return message[:max_length-3] + "..."


def format_location(file_path: str, line: int, column: int) -> str:
    """Format file location as standard string."""
    return f"{file_path}:{line}:{column}"


# Error categorization
ERROR_CATEGORIES = {
    # Style and formatting
    "E": "style",
    "W": "style",
    "C": "style",
    "F": "error",
    
    # Type checking
    "type": "type_error",
    "import": "import_error",
    "name": "name_error",
    
    # Runtime
    "runtime": "runtime_error",
    "ui": "ui_error",
}


def categorize_error_code(error_code: str) -> str:
    """Categorize error based on error code prefix."""
    if not error_code:
        return "general"
    
    # Check for exact match first
    if error_code in ERROR_CATEGORIES:
        return ERROR_CATEGORIES[error_code]
    
    # Check prefix match
    prefix = error_code[0] if error_code else ""
    return ERROR_CATEGORIES.get(prefix, "general")


# Logging configuration
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

