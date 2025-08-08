"""
LSP Protocol Constants

Adapted from Serena's solidlsp implementation.
"""


class LSPConstants:
    """Constants used in LSP communication."""
    
    # LSP Methods
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    SHUTDOWN = "shutdown"
    EXIT = "exit"
    
    # Text Document Methods
    TEXT_DOCUMENT_DID_OPEN = "textDocument/didOpen"
    TEXT_DOCUMENT_DID_CHANGE = "textDocument/didChange"
    TEXT_DOCUMENT_DID_CLOSE = "textDocument/didClose"
    TEXT_DOCUMENT_DID_SAVE = "textDocument/didSave"
    TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS = "textDocument/publishDiagnostics"
    TEXT_DOCUMENT_DIAGNOSTIC = "textDocument/diagnostic"
    
    # Workspace Methods
    WORKSPACE_DID_CHANGE_CONFIGURATION = "workspace/didChangeConfiguration"
    WORKSPACE_DID_CHANGE_WATCHED_FILES = "workspace/didChangeWatchedFiles"
    WORKSPACE_DIAGNOSTIC = "workspace/diagnostic"
    
    # Window Methods
    WINDOW_SHOW_MESSAGE = "window/showMessage"
    WINDOW_LOG_MESSAGE = "window/logMessage"
    
    # Error Codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # LSP Error Codes
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000
    SERVER_NOT_INITIALIZED = -32002
    UNKNOWN_ERROR_CODE = -32001
    
    # Request Failed Error Codes
    REQUEST_FAILED = -32803
    SERVER_CANCELLED = -32802
    CONTENT_MODIFIED = -32801
    REQUEST_CANCELLED = -32800
    
    # Diagnostic Severity
    DIAGNOSTIC_SEVERITY_ERROR = 1
    DIAGNOSTIC_SEVERITY_WARNING = 2
    DIAGNOSTIC_SEVERITY_INFORMATION = 3
    DIAGNOSTIC_SEVERITY_HINT = 4
    
    # Text Document Sync Kind
    TEXT_DOCUMENT_SYNC_NONE = 0
    TEXT_DOCUMENT_SYNC_FULL = 1
    TEXT_DOCUMENT_SYNC_INCREMENTAL = 2
    
    # File Change Type
    FILE_CHANGE_TYPE_CREATED = 1
    FILE_CHANGE_TYPE_CHANGED = 2
    FILE_CHANGE_TYPE_DELETED = 3

