"""
LSP Protocol Types

This module defines the core LSP types used throughout the Serena integration.
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
    line: int  # 0-based
    character: int  # 0-based
    
    def __str__(self) -> str:
        return f"{self.line}:{self.character}"


@dataclass
class Range:
    """Represents a range in a text document."""
    start: Position
    end: Position
    
    def __str__(self) -> str:
        return f"{self.start}-{self.end}"


@dataclass
class Location:
    """Represents a location in a text document."""
    uri: str
    range: Range
    
    def __str__(self) -> str:
        return f"{self.uri}@{self.range}"


@dataclass
class Diagnostic:
    """Represents a diagnostic message."""
    range: Range
    message: str
    severity: Optional[DiagnosticSeverity] = None
    code: Optional[Union[str, int]] = None
    source: Optional[str] = None
    related_information: Optional[List[Dict[str, Any]]] = None
    
    def __str__(self) -> str:
        severity_str = {
            DiagnosticSeverity.ERROR: "ERROR",
            DiagnosticSeverity.WARNING: "WARNING",
            DiagnosticSeverity.INFORMATION: "INFO",
            DiagnosticSeverity.HINT: "HINT"
        }.get(self.severity, "UNKNOWN")
        
        return f"{severity_str} {self.range}: {self.message}"


@dataclass
class TextEdit:
    """Represents a text edit operation."""
    range: Range
    new_text: str


@dataclass
class WorkspaceEdit:
    """Represents a workspace edit operation."""
    changes: Optional[Dict[str, List[TextEdit]]] = None
    document_changes: Optional[List[Dict[str, Any]]] = None


@dataclass
class CompletionItem:
    """Represents a completion item."""
    label: str
    kind: Optional[CompletionItemKind] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None
    sort_text: Optional[str] = None
    filter_text: Optional[str] = None
    insert_text: Optional[str] = None
    text_edit: Optional[TextEdit] = None
    additional_text_edits: Optional[List[TextEdit]] = None
    data: Optional[Any] = None


@dataclass
class ParameterInformation:
    """Represents parameter information in a signature."""
    label: str
    documentation: Optional[str] = None


@dataclass
class SignatureInformation:
    """Represents signature information."""
    label: str
    documentation: Optional[str] = None
    parameters: Optional[List[ParameterInformation]] = None


@dataclass
class SignatureHelp:
    """Represents signature help information."""
    signatures: List[SignatureInformation]
    active_signature: Optional[int] = None
    active_parameter: Optional[int] = None


@dataclass
class MarkupContent:
    """Represents markup content."""
    kind: str  # "plaintext" or "markdown"
    value: str


@dataclass
class Hover:
    """Represents hover information."""
    contents: Union[str, MarkupContent, List[Union[str, MarkupContent]]]
    range: Optional[Range] = None


# Utility functions for working with LSP types

def position_from_line_char(line: int, character: int) -> Position:
    """Create a Position from line and character numbers."""
    return Position(line=line, character=character)


def range_from_positions(start_line: int, start_char: int, 
                        end_line: int, end_char: int) -> Range:
    """Create a Range from start and end positions."""
    return Range(
        start=Position(line=start_line, character=start_char),
        end=Position(line=end_line, character=end_char)
    )


def diagnostic_from_error(file_path: str, line: int, character: int,
                         message: str, severity: DiagnosticSeverity = DiagnosticSeverity.ERROR,
                         source: Optional[str] = None) -> Diagnostic:
    """Create a Diagnostic from error information."""
    return Diagnostic(
        range=Range(
            start=Position(line=line, character=character),
            end=Position(line=line, character=character + 1)
        ),
        message=message,
        severity=severity,
        source=source
    )

