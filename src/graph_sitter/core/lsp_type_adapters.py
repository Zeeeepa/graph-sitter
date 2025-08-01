"""
LSP Type Adapters

This module provides adapters to convert between the unified LSP types
and the existing protocol types, ensuring backward compatibility.
"""

from typing import List, Optional, Union, Any, Dict
from dataclasses import asdict

# Import unified types
from .lsp_types import (
    ErrorInfo as UnifiedErrorInfo,
    ErrorCollection as UnifiedErrorCollection,
    ErrorSeverity as UnifiedErrorSeverity,
    ErrorType as UnifiedErrorType,
    Position as UnifiedPosition,
    Range as UnifiedRange,
    CompletionItem as UnifiedCompletionItem,
    HoverInfo as UnifiedHoverInfo
)

# Import protocol types
from ..extensions.lsp.protocol.lsp_types import (
    DiagnosticSeverity as ProtocolDiagnosticSeverity,
    Position as ProtocolPosition,
    Range as ProtocolRange,
    Diagnostic as ProtocolDiagnostic,
    CompletionItem as ProtocolCompletionItem,
    Hover as ProtocolHover
)

# Import serena bridge types
from ..extensions.lsp.serena_bridge import ErrorInfo as SerenaErrorInfo


class LSPTypeAdapter:
    """Adapter for converting between different LSP type systems."""
    
    @staticmethod
    def severity_to_unified(severity: Union[ProtocolDiagnosticSeverity, int]) -> UnifiedErrorSeverity:
        """Convert protocol severity to unified severity."""
        if isinstance(severity, int):
            severity_map = {
                1: UnifiedErrorSeverity.ERROR,
                2: UnifiedErrorSeverity.WARNING,
                3: UnifiedErrorSeverity.INFO,
                4: UnifiedErrorSeverity.HINT
            }
            return severity_map.get(severity, UnifiedErrorSeverity.ERROR)
        
        # Handle ProtocolDiagnosticSeverity enum
        severity_map = {
            ProtocolDiagnosticSeverity.ERROR: UnifiedErrorSeverity.ERROR,
            ProtocolDiagnosticSeverity.WARNING: UnifiedErrorSeverity.WARNING,
            ProtocolDiagnosticSeverity.INFORMATION: UnifiedErrorSeverity.INFO,
            ProtocolDiagnosticSeverity.HINT: UnifiedErrorSeverity.HINT
        }
        return severity_map.get(severity, UnifiedErrorSeverity.ERROR)
    
    @staticmethod
    def severity_to_protocol(severity: UnifiedErrorSeverity) -> ProtocolDiagnosticSeverity:
        """Convert unified severity to protocol severity."""
        severity_map = {
            UnifiedErrorSeverity.ERROR: ProtocolDiagnosticSeverity.ERROR,
            UnifiedErrorSeverity.WARNING: ProtocolDiagnosticSeverity.WARNING,
            UnifiedErrorSeverity.INFO: ProtocolDiagnosticSeverity.INFORMATION,
            UnifiedErrorSeverity.HINT: ProtocolDiagnosticSeverity.HINT
        }
        return severity_map.get(severity, ProtocolDiagnosticSeverity.ERROR)
    
    @staticmethod
    def position_to_unified(position: Union[ProtocolPosition, Dict[str, int]]) -> UnifiedPosition:
        """Convert protocol position to unified position."""
        if isinstance(position, dict):
            return UnifiedPosition(
                line=position.get('line', 0),
                character=position.get('character', 0)
            )
        
        return UnifiedPosition(
            line=getattr(position, 'line', 0),
            character=getattr(position, 'character', 0)
        )
    
    @staticmethod
    def position_to_protocol(position: UnifiedPosition) -> ProtocolPosition:
        """Convert unified position to protocol position."""
        return ProtocolPosition(line=position.line, character=position.character)
    
    @staticmethod
    def range_to_unified(range_obj: Union[ProtocolRange, Dict[str, Any]]) -> UnifiedRange:
        """Convert protocol range to unified range."""
        if isinstance(range_obj, dict):
            start = LSPTypeAdapter.position_to_unified(range_obj.get('start', {}))
            end = LSPTypeAdapter.position_to_unified(range_obj.get('end', {}))
            return UnifiedRange(start=start, end=end)
        
        start = LSPTypeAdapter.position_to_unified(getattr(range_obj, 'start', {}))
        end = LSPTypeAdapter.position_to_unified(getattr(range_obj, 'end', {}))
        return UnifiedRange(start=start, end=end)
    
    @staticmethod
    def range_to_protocol(range_obj: UnifiedRange) -> ProtocolRange:
        """Convert unified range to protocol range."""
        return ProtocolRange(
            start=LSPTypeAdapter.position_to_protocol(range_obj.start),
            end=LSPTypeAdapter.position_to_protocol(range_obj.end)
        )
    
    @staticmethod
    def serena_error_to_unified(error: SerenaErrorInfo) -> UnifiedErrorInfo:
        """Convert Serena ErrorInfo to unified ErrorInfo."""
        # Determine error type based on message content
        error_type = UnifiedErrorType.SEMANTIC
        if 'syntax' in error.message.lower():
            error_type = UnifiedErrorType.SYNTAX
        elif 'import' in error.message.lower():
            error_type = UnifiedErrorType.IMPORT
        elif 'type' in error.message.lower():
            error_type = UnifiedErrorType.TYPE_CHECK
        elif 'lint' in error.message.lower():
            error_type = UnifiedErrorType.LINT
        elif 'undefined' in error.message.lower():
            error_type = UnifiedErrorType.UNDEFINED
        
        # Create range from line/character positions
        start_pos = UnifiedPosition(line=error.line, character=error.character)
        end_pos = UnifiedPosition(
            line=error.end_line if error.end_line is not None else error.line,
            character=error.end_character if error.end_character is not None else error.character
        )
        range_obj = UnifiedRange(start=start_pos, end=end_pos)
        
        return UnifiedErrorInfo(
            id=f"{error.file_path}:{error.line}:{error.character}",
            message=error.message,
            severity=LSPTypeAdapter.severity_to_unified(error.severity),
            error_type=error_type,
            file_path=error.file_path,
            range=range_obj,
            source=error.source or "serena-lsp",
            code=str(error.code) if error.code else None,
            has_quick_fix=False  # Default, can be enhanced
        )
    
    @staticmethod
    def protocol_diagnostic_to_unified(diagnostic: ProtocolDiagnostic, file_path: str) -> UnifiedErrorInfo:
        """Convert protocol diagnostic to unified ErrorInfo."""
        # Determine error type based on source and message
        error_type = UnifiedErrorType.SEMANTIC
        source = getattr(diagnostic, 'source', '').lower()
        message = getattr(diagnostic, 'message', '').lower()
        
        if 'pylsp' in source or 'pyflakes' in source:
            if 'syntax' in message:
                error_type = UnifiedErrorType.SYNTAX
            elif 'import' in message:
                error_type = UnifiedErrorType.IMPORT
            elif 'undefined' in message:
                error_type = UnifiedErrorType.UNDEFINED
        elif 'mypy' in source:
            error_type = UnifiedErrorType.TYPE_CHECK
        elif 'flake8' in source or 'pylint' in source:
            error_type = UnifiedErrorType.LINT
        
        range_obj = getattr(diagnostic, 'range', None)
        start_line = 0
        start_char = 0
        end_line = None
        end_char = None
        
        if range_obj:
            start = getattr(range_obj, 'start', None)
            end = getattr(range_obj, 'end', None)
            if start:
                start_line = getattr(start, 'line', 0)
                start_char = getattr(start, 'character', 0)
            if end:
                end_line = getattr(end, 'line', None)
                end_char = getattr(end, 'character', None)
        
        # Create range from diagnostic positions
        start_pos = UnifiedPosition(line=start_line, character=start_char)
        end_pos = UnifiedPosition(
            line=end_line if end_line is not None else start_line,
            character=end_char if end_char is not None else start_char
        )
        range_obj = UnifiedRange(start=start_pos, end=end_pos)
        
        return UnifiedErrorInfo(
            id=f"{file_path}:{start_line}:{start_char}",
            message=getattr(diagnostic, 'message', ''),
            severity=LSPTypeAdapter.severity_to_unified(getattr(diagnostic, 'severity', 1)),
            error_type=error_type,
            file_path=file_path,
            range=range_obj,
            source=getattr(diagnostic, 'source', None) or "lsp-protocol",
            code=str(getattr(diagnostic, 'code', '')) if getattr(diagnostic, 'code', None) else None,
            has_quick_fix=False  # Default, can be enhanced
        )
    
    @staticmethod
    def unified_error_to_serena(error: UnifiedErrorInfo) -> SerenaErrorInfo:
        """Convert unified ErrorInfo to Serena ErrorInfo."""
        return SerenaErrorInfo(
            file_path=error.file_path,
            line=error.line,
            character=error.character,
            message=error.message,
            severity=LSPTypeAdapter.severity_to_protocol(error.severity),
            source=error.source,
            code=error.code,
            end_line=error.end_line,
            end_character=error.end_character
        )
    
    @staticmethod
    def completion_to_unified(completion: Union[ProtocolCompletionItem, Dict[str, Any]]) -> UnifiedCompletionItem:
        """Convert protocol completion item to unified completion item."""
        if isinstance(completion, dict):
            return UnifiedCompletionItem(
                label=completion.get('label', ''),
                kind=completion.get('kind', 1),
                detail=completion.get('detail'),
                documentation=completion.get('documentation'),
                sort_text=completion.get('sortText'),
                filter_text=completion.get('filterText'),
                insert_text=completion.get('insertText'),
                additional_text_edits=[]
            )
        
        return UnifiedCompletionItem(
            label=getattr(completion, 'label', ''),
            kind=getattr(completion, 'kind', 1),
            detail=getattr(completion, 'detail', None),
            documentation=getattr(completion, 'documentation', None),
            sort_text=getattr(completion, 'sort_text', None),
            filter_text=getattr(completion, 'filter_text', None),
            insert_text=getattr(completion, 'insert_text', None),
            additional_text_edits=[]
        )
    
    @staticmethod
    def hover_to_unified(hover: Union[ProtocolHover, Dict[str, Any]]) -> UnifiedHoverInfo:
        """Convert protocol hover to unified hover info."""
        if isinstance(hover, dict):
            contents = hover.get('contents', '')
            if isinstance(contents, list):
                contents = '\n'.join(str(item) for item in contents)
            
            return UnifiedHoverInfo(
                contents=str(contents),
                range=None  # Can be enhanced if range is available
            )
        
        contents = getattr(hover, 'contents', '')
        if isinstance(contents, list):
            contents = '\n'.join(str(item) for item in contents)
        
        return UnifiedHoverInfo(
            contents=str(contents),
            range=None  # Can be enhanced if range is available
        )


# Convenience functions for common conversions
def convert_serena_errors_to_unified(serena_errors: List[SerenaErrorInfo]) -> List[UnifiedErrorInfo]:
    """Convert a list of Serena errors to unified errors."""
    return [LSPTypeAdapter.serena_error_to_unified(error) for error in serena_errors]


def convert_protocol_diagnostics_to_unified(diagnostics: List[ProtocolDiagnostic], file_path: str) -> List[UnifiedErrorInfo]:
    """Convert a list of protocol diagnostics to unified errors."""
    return [LSPTypeAdapter.protocol_diagnostic_to_unified(diag, file_path) for diag in diagnostics]


def create_unified_error_collection(errors: List[UnifiedErrorInfo]) -> UnifiedErrorCollection:
    """Create a unified error collection from a list of errors."""
    error_count = sum(1 for e in errors if e.severity == UnifiedErrorSeverity.ERROR)
    warning_count = sum(1 for e in errors if e.severity == UnifiedErrorSeverity.WARNING)
    info_count = sum(1 for e in errors if e.severity == UnifiedErrorSeverity.INFO)
    hint_count = sum(1 for e in errors if e.severity == UnifiedErrorSeverity.HINT)
    
    return UnifiedErrorCollection(
        errors=errors,
        total_count=len(errors),
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        hint_count=hint_count,
        files_with_errors=len(set(e.file_path for e in errors))
    )
