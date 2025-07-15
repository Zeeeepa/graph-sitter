"""
LSP Protocol Types

Adapted from Serena's solidlsp implementation for graph-sitter integration.
Provides core LSP types for diagnostic and error handling.
"""

from __future__ import annotations

from enum import IntEnum
from typing import List, Optional, Union, Any, Dict
from typing_extensions import TypedDict, NotRequired

URI = str
DocumentUri = str
Uint = int


class Position(TypedDict):
    """Position in a text document expressed as zero-based line and character offset."""
    line: Uint
    """Line position in a document (zero-based)."""
    character: Uint
    """Character offset on a line in a document (zero-based)."""


class Range(TypedDict):
    """A range in a text document expressed as (zero-based) start and end positions."""
    start: Position
    """The range's start position."""
    end: Position
    """The range's end position."""


class Location(TypedDict):
    """Represents a location inside a resource, such as a line inside a text file."""
    uri: DocumentUri
    range: Range
    absolutePath: NotRequired[str]
    relativePath: NotRequired[str]


class DiagnosticSeverity(IntEnum):
    """The diagnostic's severity."""
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4


class DiagnosticTag(IntEnum):
    """The diagnostic tags."""
    Unnecessary = 1
    Deprecated = 2


class DiagnosticRelatedInformation(TypedDict):
    """Represents a related message and source code location for a diagnostic."""
    location: Location
    """The location of this related diagnostic information."""
    message: str
    """The message of this related diagnostic information."""


class CodeDescription(TypedDict):
    """Structure to capture a description for an error code."""
    href: URI
    """An URI to open with more information about the diagnostic error."""


class Diagnostic(TypedDict):
    """Represents a diagnostic, such as a compiler error or warning."""
    range: Range
    """The range at which the message applies."""
    severity: NotRequired[DiagnosticSeverity]
    """The diagnostic's severity. Can be omitted."""
    code: NotRequired[Union[int, str]]
    """The diagnostic's code, which usually appear in the user interface."""
    codeDescription: NotRequired[CodeDescription]
    """An optional property to describe the error code."""
    source: NotRequired[str]
    """A human-readable string describing the source of this diagnostic."""
    message: str
    """The diagnostic's message. It usually appears in the user interface."""
    tags: NotRequired[List[DiagnosticTag]]
    """Additional metadata about the diagnostic."""
    relatedInformation: NotRequired[List[DiagnosticRelatedInformation]]
    """An array of related diagnostic information."""
    data: NotRequired[Any]
    """A data entry field that is preserved between a textDocument/publishDiagnostics notification and textDocument/codeAction request."""


class PublishDiagnosticsParams(TypedDict):
    """The publish diagnostic notification's parameters."""
    uri: DocumentUri
    """The URI for which diagnostic information is reported."""
    version: NotRequired[int]
    """Optional the version number of the document the diagnostics are published for."""
    diagnostics: List[Diagnostic]
    """An array of diagnostic information items."""


class DocumentDiagnosticParams(TypedDict):
    """Parameters for the document diagnostic request."""
    textDocument: "TextDocumentIdentifier"
    """The text document."""
    identifier: NotRequired[str]
    """The additional identifier provided during registration."""
    previousResultId: NotRequired[str]
    """The result id of a previous response if provided."""


class WorkspaceDiagnosticParams(TypedDict):
    """Parameters for the workspace diagnostic request."""
    identifier: NotRequired[str]
    """The additional identifier provided during registration."""
    previousResultIds: NotRequired[List["PreviousResultId"]]
    """The currently known result ids."""


class TextDocumentIdentifier(TypedDict):
    """A literal to identify a text document in the client."""
    uri: DocumentUri
    """The text document's uri."""


class PreviousResultId(TypedDict):
    """A previous result id in a workspace pull request."""
    uri: DocumentUri
    """The URI for which the client knowns a result id."""
    value: str
    """The value of the previous result id."""


class DocumentDiagnosticReport(TypedDict):
    """The result of a document diagnostic pull request."""
    kind: str
    """A document diagnostic report indicating no changes to the last result."""
    resultId: NotRequired[str]
    """A result id which will be sent on the next diagnostic request for the same document."""
    items: NotRequired[List[Diagnostic]]
    """The actual items."""


class WorkspaceDiagnosticReport(TypedDict):
    """A workspace diagnostic report."""
    items: List["WorkspaceDocumentDiagnosticReport"]


class WorkspaceDocumentDiagnosticReport(TypedDict):
    """A diagnostic report for a workspace document."""
    uri: DocumentUri
    """The URI for which diagnostic information is reported."""
    version: NotRequired[int]
    """The version number for which the diagnostics are reported."""
    kind: str
    """The document diagnostic report kind."""
    resultId: NotRequired[str]
    """An optional result id."""
    items: NotRequired[List[Diagnostic]]
    """The actual items."""


# Additional types for initialization
class InitializeParams(TypedDict):
    """The initialize request parameters."""
    processId: NotRequired[int]
    """The process Id of the parent process that started the server."""
    clientInfo: NotRequired["ClientInfo"]
    """Information about the client."""
    locale: NotRequired[str]
    """The locale the client is currently showing the user interface in."""
    rootPath: NotRequired[str]
    """The rootPath of the workspace. Is null if no folder is open."""
    rootUri: NotRequired[DocumentUri]
    """The rootUri of the workspace."""
    capabilities: "ClientCapabilities"
    """The capabilities provided by the client (editor or tool)."""
    initializationOptions: NotRequired[Any]
    """User provided initialization options."""
    trace: NotRequired[str]
    """The initial trace setting."""
    workspaceFolders: NotRequired[List["WorkspaceFolder"]]
    """The workspace folders configured in the client when the server starts."""


class ClientInfo(TypedDict):
    """Information about the client."""
    name: str
    """The name of the client as defined by the client."""
    version: NotRequired[str]
    """The client's version as defined by the client."""


class WorkspaceFolder(TypedDict):
    """A workspace folder."""
    uri: DocumentUri
    """The associated URI for this workspace folder."""
    name: str
    """The name of the workspace folder."""


class ClientCapabilities(TypedDict):
    """Client capabilities."""
    workspace: NotRequired["WorkspaceClientCapabilities"]
    """Workspace specific client capabilities."""
    textDocument: NotRequired["TextDocumentClientCapabilities"]
    """Text document specific client capabilities."""
    notebookDocument: NotRequired[Any]
    """Capabilities specific to the notebook document support."""
    window: NotRequired[Any]
    """Window specific client capabilities."""
    general: NotRequired[Any]
    """General client capabilities."""
    experimental: NotRequired[Any]
    """Experimental client capabilities."""


class WorkspaceClientCapabilities(TypedDict):
    """Workspace specific client capabilities."""
    applyEdit: NotRequired[bool]
    """The client supports applying batch edits to the workspace."""
    workspaceEdit: NotRequired[Any]
    """Capabilities specific to `WorkspaceEdit`s."""
    didChangeConfiguration: NotRequired[Any]
    """Capabilities specific to the `workspace/didChangeConfiguration` notification."""
    didChangeWatchedFiles: NotRequired[Any]
    """Capabilities specific to the `workspace/didChangeWatchedFiles` notification."""
    symbol: NotRequired[Any]
    """Capabilities specific to the `workspace/symbol` request."""
    executeCommand: NotRequired[Any]
    """Capabilities specific to the `workspace/executeCommand` request."""
    workspaceFolders: NotRequired[bool]
    """The client has support for workspace folders."""
    configuration: NotRequired[bool]
    """The client supports `workspace/configuration` requests."""
    semanticTokens: NotRequired[Any]
    """Capabilities specific to the semantic token requests scoped to the workspace."""
    codeLens: NotRequired[Any]
    """Capabilities specific to the code lens requests scoped to the workspace."""
    fileOperations: NotRequired[Any]
    """The client has support for file requests/notifications."""
    inlineValue: NotRequired[Any]
    """Capabilities specific to the inline values requests scoped to the workspace."""
    inlayHint: NotRequired[Any]
    """Capabilities specific to the inlay hint requests scoped to the workspace."""
    diagnostics: NotRequired[Any]
    """Capabilities specific to the diagnostic requests scoped to the workspace."""


class TextDocumentClientCapabilities(TypedDict):
    """Text document specific client capabilities."""
    synchronization: NotRequired[Any]
    """Defines which synchronization capabilities the client supports."""
    completion: NotRequired[Any]
    """Capabilities specific to the `textDocument/completion` request."""
    hover: NotRequired[Any]
    """Capabilities specific to the `textDocument/hover` request."""
    signatureHelp: NotRequired[Any]
    """Capabilities specific to the `textDocument/signatureHelp` request."""
    declaration: NotRequired[Any]
    """Capabilities specific to the `textDocument/declaration` request."""
    definition: NotRequired[Any]
    """Capabilities specific to the `textDocument/definition` request."""
    typeDefinition: NotRequired[Any]
    """Capabilities specific to the `textDocument/typeDefinition` request."""
    implementation: NotRequired[Any]
    """Capabilities specific to the `textDocument/implementation` request."""
    references: NotRequired[Any]
    """Capabilities specific to the `textDocument/references` request."""
    documentHighlight: NotRequired[Any]
    """Capabilities specific to the `textDocument/documentHighlight` request."""
    documentSymbol: NotRequired[Any]
    """Capabilities specific to the `textDocument/documentSymbol` request."""
    codeAction: NotRequired[Any]
    """Capabilities specific to the `textDocument/codeAction` request."""
    codeLens: NotRequired[Any]
    """Capabilities specific to the `textDocument/codeLens` request."""
    documentLink: NotRequired[Any]
    """Capabilities specific to the `textDocument/documentLink` request."""
    colorProvider: NotRequired[Any]
    """Capabilities specific to the `textDocument/documentColor` and the `textDocument/colorPresentation` request."""
    formatting: NotRequired[Any]
    """Capabilities specific to the `textDocument/formatting` request."""
    rangeFormatting: NotRequired[Any]
    """Capabilities specific to the `textDocument/rangeFormatting` request."""
    onTypeFormatting: NotRequired[Any]
    """Capabilities specific to the `textDocument/onTypeFormatting` request."""
    rename: NotRequired[Any]
    """Capabilities specific to the `textDocument/rename` request."""
    publishDiagnostics: NotRequired[Any]
    """Capabilities specific to the `textDocument/publishDiagnostics` notification."""
    foldingRange: NotRequired[Any]
    """Capabilities specific to the `textDocument/foldingRange` request."""
    selectionRange: NotRequired[Any]
    """Capabilities specific to the `textDocument/selectionRange` request."""
    linkedEditingRange: NotRequired[Any]
    """Capabilities specific to the `textDocument/linkedEditingRange` request."""
    callHierarchy: NotRequired[Any]
    """Capabilities specific to the various call hierarchy requests."""
    semanticTokens: NotRequired[Any]
    """Capabilities specific to the various semantic token request."""
    moniker: NotRequired[Any]
    """Capabilities specific to the `textDocument/moniker` request."""
    typeHierarchy: NotRequired[Any]
    """Capabilities specific to the various type hierarchy requests."""
    inlineValue: NotRequired[Any]
    """Capabilities specific to the `textDocument/inlineValue` request."""
    inlayHint: NotRequired[Any]
    """Capabilities specific to the `textDocument/inlayHint` request."""
    diagnostic: NotRequired[Any]
    """Capabilities specific to the diagnostic pull model."""


class InitializeResult(TypedDict):
    """The result returned from an initialize request."""
    capabilities: "ServerCapabilities"
    """The capabilities the language server provides."""
    serverInfo: NotRequired["ServerInfo"]
    """Information about the server."""


class ServerCapabilities(TypedDict):
    """Server capabilities."""
    positionEncoding: NotRequired[str]
    """The position encoding the server picked from the encodings offered by the client via the client capability `general.positionEncodings`."""
    textDocumentSync: NotRequired[Any]
    """Defines how text documents are synced."""
    notebookDocumentSync: NotRequired[Any]
    """Defines how notebook documents are synced."""
    completionProvider: NotRequired[Any]
    """The server provides completion support."""
    hoverProvider: NotRequired[Any]
    """The server provides hover support."""
    signatureHelpProvider: NotRequired[Any]
    """The server provides signature help support."""
    declarationProvider: NotRequired[Any]
    """The server provides Goto Declaration support."""
    definitionProvider: NotRequired[Any]
    """The server provides goto definition support."""
    typeDefinitionProvider: NotRequired[Any]
    """The server provides Goto Type Definition support."""
    implementationProvider: NotRequired[Any]
    """The server provides goto implementation support."""
    referencesProvider: NotRequired[Any]
    """The server provides find references support."""
    documentHighlightProvider: NotRequired[Any]
    """The server provides document highlight support."""
    documentSymbolProvider: NotRequired[Any]
    """The server provides document symbol support."""
    codeActionProvider: NotRequired[Any]
    """The server provides code actions."""
    codeLensProvider: NotRequired[Any]
    """The server provides code lens."""
    documentLinkProvider: NotRequired[Any]
    """The server provides document link support."""
    colorProvider: NotRequired[Any]
    """The server provides color provider support."""
    documentFormattingProvider: NotRequired[Any]
    """The server provides document formatting."""
    documentRangeFormattingProvider: NotRequired[Any]
    """The server provides document range formatting."""
    documentOnTypeFormattingProvider: NotRequired[Any]
    """The server provides document formatting on typing."""
    renameProvider: NotRequired[Any]
    """The server provides rename support."""
    foldingRangeProvider: NotRequired[Any]
    """The server provides folding provider support."""
    executeCommandProvider: NotRequired[Any]
    """The server provides execute command support."""
    selectionRangeProvider: NotRequired[Any]
    """The server provides selection range support."""
    linkedEditingRangeProvider: NotRequired[Any]
    """The server provides linked editing range support."""
    callHierarchyProvider: NotRequired[Any]
    """The server provides call hierarchy support."""
    semanticTokensProvider: NotRequired[Any]
    """The server provides semantic tokens support."""
    monikerProvider: NotRequired[Any]
    """The server provides moniker support."""
    typeHierarchyProvider: NotRequired[Any]
    """The server provides type hierarchy support."""
    inlineValueProvider: NotRequired[Any]
    """The server provides inline values."""
    inlayHintProvider: NotRequired[Any]
    """The server provides inlay hints."""
    diagnosticProvider: NotRequired[Any]
    """The server has support for pull model diagnostics."""
    workspaceSymbolProvider: NotRequired[Any]
    """The server provides workspace symbol support."""
    workspace: NotRequired[Any]
    """Workspace specific server capabilities."""
    experimental: NotRequired[Any]
    """Experimental server capabilities."""


class ServerInfo(TypedDict):
    """Information about the server."""
    name: str
    """The name of the server as defined by the server."""
    version: NotRequired[str]
    """The server's version as defined by the server."""

