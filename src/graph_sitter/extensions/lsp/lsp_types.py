"""
LSP Protocol Types for Graph-Sitter

This module defines the core LSP types used throughout the runtime error collection system.
Based on the Language Server Protocol specification.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Dict, Any, Union


class DiagnosticSeverity(IntEnum):
    """Diagnostic severity levels as defined by LSP."""
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class CompletionItemKind(IntEnum):
    """Completion item kinds as defined by LSP."""
    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    UNIT = 11
    VALUE = 12
    ENUM = 13
    KEYWORD = 14
    SNIPPET = 15
    COLOR = 16
    FILE = 17
    REFERENCE = 18
    FOLDER = 19
    ENUM_MEMBER = 20
    CONSTANT = 21
    STRUCT = 22
    EVENT = 23
    OPERATOR = 24
    TYPE_PARAMETER = 25


@dataclass
class Position:
    """Represents a position in a text document."""
    line: int
    character: int


@dataclass
class Range:
    """Represents a range in a text document."""
    start: Position
    end: Position


@dataclass
class Diagnostic:
    """Represents a diagnostic, such as a compiler error or warning."""
    range: Range
    message: str
    severity: Optional[DiagnosticSeverity] = None
    code: Optional[Union[str, int]] = None
    source: Optional[str] = None
    related_information: Optional[List[Any]] = None
    tags: Optional[List[int]] = None
    data: Optional[Any] = None


@dataclass
class Location:
    """Represents a location inside a resource, such as a line inside a text file."""
    uri: str
    range: Range


@dataclass
class TextEdit:
    """A textual edit applicable to a text document."""
    range: Range
    new_text: str


@dataclass
class WorkspaceEdit:
    """A workspace edit represents changes to many resources managed in the workspace."""
    changes: Optional[Dict[str, List[TextEdit]]] = None
    document_changes: Optional[List[Any]] = None


@dataclass
class Command:
    """Represents a reference to a command."""
    title: str
    command: str
    arguments: Optional[List[Any]] = None


@dataclass
class CodeAction:
    """A code action represents a change that can be performed in code."""
    title: str
    kind: Optional[str] = None
    diagnostics: Optional[List[Diagnostic]] = None
    is_preferred: Optional[bool] = None
    disabled: Optional[Dict[str, str]] = None
    edit: Optional[WorkspaceEdit] = None
    command: Optional[Command] = None
    data: Optional[Any] = None


# Error type enumeration for runtime error classification
class ErrorType(IntEnum):
    """Types of errors that can be detected."""
    STATIC_ANALYSIS = 1  # Syntax, import, type errors from static analysis
    RUNTIME_ERROR = 2    # Errors that occur during execution
    LINTING = 3         # Code style and quality issues
    SECURITY = 4        # Security vulnerabilities
    PERFORMANCE = 5     # Performance issues

