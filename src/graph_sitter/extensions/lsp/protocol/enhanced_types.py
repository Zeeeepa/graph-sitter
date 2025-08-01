"""
Enhanced LSP Protocol Types
===========================

This module extends the core LSP types with additional types needed for
comprehensive error retrieval and code intelligence features.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Dict, Any, Union

# Import base types
from .lsp_types import Position, Range, DiagnosticSeverity


class CodeActionKind:
    """Code action kinds as defined by LSP."""
    EMPTY = ""
    QUICKFIX = "quickfix"
    REFACTOR = "refactor"
    REFACTOR_EXTRACT = "refactor.extract"
    REFACTOR_INLINE = "refactor.inline"
    REFACTOR_REWRITE = "refactor.rewrite"
    SOURCE = "source"
    SOURCE_ORGANIZE_IMPORTS = "source.organizeImports"
    SOURCE_FIX_ALL = "source.fixAll"


class SymbolKind(IntEnum):
    """Symbol kinds as defined by LSP."""
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26


class SemanticTokenTypes:
    """Semantic token types as defined by LSP."""
    NAMESPACE = "namespace"
    TYPE = "type"
    CLASS = "class"
    ENUM = "enum"
    INTERFACE = "interface"
    STRUCT = "struct"
    TYPE_PARAMETER = "typeParameter"
    PARAMETER = "parameter"
    VARIABLE = "variable"
    PROPERTY = "property"
    ENUM_MEMBER = "enumMember"
    EVENT = "event"
    FUNCTION = "function"
    METHOD = "method"
    MACRO = "macro"
    KEYWORD = "keyword"
    MODIFIER = "modifier"
    COMMENT = "comment"
    STRING = "string"
    NUMBER = "number"
    REGEXP = "regexp"
    OPERATOR = "operator"


class SemanticTokenModifiers:
    """Semantic token modifiers as defined by LSP."""
    DECLARATION = "declaration"
    DEFINITION = "definition"
    READONLY = "readonly"
    STATIC = "static"
    DEPRECATED = "deprecated"
    ABSTRACT = "abstract"
    ASYNC = "async"
    MODIFICATION = "modification"
    DOCUMENTATION = "documentation"
    DEFAULT_LIBRARY = "defaultLibrary"


@dataclass
class TextEdit:
    """Represents a text edit."""
    range: Range
    new_text: str


@dataclass
class WorkspaceEdit:
    """Represents a workspace edit."""
    changes: Optional[Dict[str, List[TextEdit]]] = None
    document_changes: Optional[List[Any]] = None


@dataclass
class Command:
    """Represents a command."""
    title: str
    command: str
    arguments: Optional[List[Any]] = None


@dataclass
class CodeAction:
    """Represents a code action."""
    title: str
    kind: Optional[str] = None
    diagnostics: Optional[List[Any]] = None
    is_preferred: Optional[bool] = None
    disabled: Optional[Dict[str, str]] = None
    edit: Optional[WorkspaceEdit] = None
    command: Optional[Command] = None


@dataclass
class CompletionItem:
    """Represents a completion item."""
    label: str
    kind: Optional[int] = None
    tags: Optional[List[int]] = None
    detail: Optional[str] = None
    documentation: Optional[Union[str, Dict[str, Any]]] = None
    deprecated: Optional[bool] = None
    preselect: Optional[bool] = None
    sort_text: Optional[str] = None
    filter_text: Optional[str] = None
    insert_text: Optional[str] = None
    insert_text_format: Optional[int] = None
    insert_text_mode: Optional[int] = None
    text_edit: Optional[TextEdit] = None
    additional_text_edits: Optional[List[TextEdit]] = None
    commit_characters: Optional[List[str]] = None
    command: Optional[Command] = None
    data: Optional[Any] = None


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


@dataclass
class ParameterInformation:
    """Represents parameter information."""
    label: Union[str, List[int]]
    documentation: Optional[Union[str, MarkupContent]] = None


@dataclass
class SignatureInformation:
    """Represents signature information."""
    label: str
    documentation: Optional[Union[str, MarkupContent]] = None
    parameters: Optional[List[ParameterInformation]] = None
    active_parameter: Optional[int] = None


@dataclass
class SignatureHelp:
    """Represents signature help."""
    signatures: List[SignatureInformation]
    active_signature: Optional[int] = None
    active_parameter: Optional[int] = None


@dataclass
class DocumentSymbol:
    """Represents a document symbol."""
    name: str
    detail: Optional[str]
    kind: SymbolKind
    tags: Optional[List[int]] = None
    deprecated: Optional[bool] = None
    range: Optional[Range] = None
    selection_range: Optional[Range] = None
    children: Optional[List['DocumentSymbol']] = None


@dataclass
class SymbolInformation:
    """Represents symbol information."""
    name: str
    kind: SymbolKind
    tags: Optional[List[int]] = None
    deprecated: Optional[bool] = None
    location: Optional[Dict[str, Any]] = None
    container_name: Optional[str] = None


@dataclass
class WorkspaceSymbol:
    """Represents a workspace symbol."""
    name: str
    kind: SymbolKind
    tags: Optional[List[int]] = None
    container_name: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    data: Optional[Any] = None


@dataclass
class SemanticToken:
    """Represents a semantic token."""
    line: int
    character: int
    length: int
    token_type: str
    token_modifiers: List[str] = field(default_factory=list)


@dataclass
class CallHierarchyItem:
    """Represents a call hierarchy item."""
    name: str
    kind: SymbolKind
    tags: Optional[List[int]] = None
    detail: Optional[str] = None
    uri: str
    range: Range
    selection_range: Range
    data: Optional[Any] = None


@dataclass
class CallHierarchyIncomingCall:
    """Represents an incoming call in call hierarchy."""
    from_item: CallHierarchyItem
    from_ranges: List[Range]


@dataclass
class CallHierarchyOutgoingCall:
    """Represents an outgoing call in call hierarchy."""
    to: CallHierarchyItem
    from_ranges: List[Range]


@dataclass
class RenameParams:
    """Parameters for rename operation."""
    text_document: Dict[str, str]
    position: Position
    new_name: str


@dataclass
class PrepareRenameResult:
    """Result of prepare rename operation."""
    range: Range
    placeholder: str


@dataclass
class LocationLink:
    """Represents a location link."""
    origin_selection_range: Optional[Range] = None
    target_uri: str = ""
    target_range: Range = None
    target_selection_range: Range = None


@dataclass
class DefinitionResult:
    """Result of go to definition."""
    locations: List[Union[Dict[str, Any], LocationLink]]


@dataclass
class ReferenceContext:
    """Context for find references."""
    include_declaration: bool


@dataclass
class ReferenceParams:
    """Parameters for find references."""
    text_document: Dict[str, str]
    position: Position
    context: ReferenceContext


@dataclass
class CodeActionContext:
    """Context for code actions."""
    diagnostics: List[Any]
    only: Optional[List[str]] = None
    trigger_kind: Optional[int] = None


@dataclass
class CodeActionParams:
    """Parameters for code actions."""
    text_document: Dict[str, str]
    range: Range
    context: CodeActionContext


@dataclass
class FormattingOptions:
    """Formatting options."""
    tab_size: int
    insert_spaces: bool
    trim_trailing_whitespace: Optional[bool] = None
    insert_final_newline: Optional[bool] = None
    trim_final_newlines: Optional[bool] = None


@dataclass
class DocumentFormattingParams:
    """Parameters for document formatting."""
    text_document: Dict[str, str]
    options: FormattingOptions


@dataclass
class DocumentRangeFormattingParams:
    """Parameters for document range formatting."""
    text_document: Dict[str, str]
    range: Range
    options: FormattingOptions


@dataclass
class DocumentOnTypeFormattingParams:
    """Parameters for document on type formatting."""
    text_document: Dict[str, str]
    position: Position
    ch: str
    options: FormattingOptions


@dataclass
class DiagnosticRelatedInformation:
    """Represents related information for a diagnostic."""
    location: Dict[str, Any]
    message: str


@dataclass
class EnhancedDiagnostic:
    """Enhanced diagnostic with additional information."""
    range: Range
    message: str
    severity: Optional[DiagnosticSeverity] = None
    code: Optional[Union[str, int]] = None
    code_description: Optional[Dict[str, str]] = None
    source: Optional[str] = None
    tags: Optional[List[int]] = None
    related_information: Optional[List[DiagnosticRelatedInformation]] = None
    data: Optional[Any] = None
    
    # Additional fields for enhanced error retrieval
    file_path: Optional[str] = None
    id: Optional[str] = None
    quick_fixes: Optional[List[CodeAction]] = None
    suggestions: Optional[List[str]] = None
    related_symbols: Optional[List[str]] = None


# Type aliases for convenience
CompletionList = List[CompletionItem]
DocumentSymbolList = List[DocumentSymbol]
WorkspaceSymbolList = List[WorkspaceSymbol]
SemanticTokenList = List[SemanticToken]
CodeActionList = List[CodeAction]
TextEditList = List[TextEdit]
DiagnosticList = List[EnhancedDiagnostic]


# Constants for LSP capabilities
class LSPCapabilities:
    """LSP server capabilities."""
    
    # Text document sync
    TEXT_DOCUMENT_SYNC = "textDocumentSync"
    
    # Completion
    COMPLETION_PROVIDER = "completionProvider"
    
    # Hover
    HOVER_PROVIDER = "hoverProvider"
    
    # Signature help
    SIGNATURE_HELP_PROVIDER = "signatureHelpProvider"
    
    # Go to definition
    DEFINITION_PROVIDER = "definitionProvider"
    
    # Find references
    REFERENCES_PROVIDER = "referencesProvider"
    
    # Document highlight
    DOCUMENT_HIGHLIGHT_PROVIDER = "documentHighlightProvider"
    
    # Document symbols
    DOCUMENT_SYMBOL_PROVIDER = "documentSymbolProvider"
    
    # Workspace symbols
    WORKSPACE_SYMBOL_PROVIDER = "workspaceSymbolProvider"
    
    # Code actions
    CODE_ACTION_PROVIDER = "codeActionProvider"
    
    # Code lens
    CODE_LENS_PROVIDER = "codeLensProvider"
    
    # Document formatting
    DOCUMENT_FORMATTING_PROVIDER = "documentFormattingProvider"
    
    # Document range formatting
    DOCUMENT_RANGE_FORMATTING_PROVIDER = "documentRangeFormattingProvider"
    
    # Document on type formatting
    DOCUMENT_ON_TYPE_FORMATTING_PROVIDER = "documentOnTypeFormattingProvider"
    
    # Rename
    RENAME_PROVIDER = "renameProvider"
    
    # Document link
    DOCUMENT_LINK_PROVIDER = "documentLinkProvider"
    
    # Execute command
    EXECUTE_COMMAND_PROVIDER = "executeCommandProvider"
    
    # Experimental
    EXPERIMENTAL = "experimental"
    
    # Semantic tokens
    SEMANTIC_TOKENS_PROVIDER = "semanticTokensProvider"
    
    # Call hierarchy
    CALL_HIERARCHY_PROVIDER = "callHierarchyProvider"
    
    # Diagnostics
    DIAGNOSTIC_PROVIDER = "diagnosticProvider"


# Error codes for enhanced error handling
class LSPErrorCodes:
    """Enhanced LSP error codes."""
    
    # Standard JSON-RPC errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # LSP specific errors
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000
    SERVER_NOT_INITIALIZED = -32002
    UNKNOWN_ERROR_CODE = -32001
    
    # Request specific errors
    REQUEST_CANCELLED = -32800
    CONTENT_MODIFIED = -32801
    SERVER_CANCELLED = -32802
    REQUEST_FAILED = -32803
    
    # Custom error codes for enhanced functionality
    DIAGNOSTIC_ERROR = -33000
    CODE_ACTION_ERROR = -33001
    COMPLETION_ERROR = -33002
    HOVER_ERROR = -33003
    DEFINITION_ERROR = -33004
    REFERENCES_ERROR = -33005
    RENAME_ERROR = -33006
    FORMATTING_ERROR = -33007
    SEMANTIC_TOKENS_ERROR = -33008
    CALL_HIERARCHY_ERROR = -33009
