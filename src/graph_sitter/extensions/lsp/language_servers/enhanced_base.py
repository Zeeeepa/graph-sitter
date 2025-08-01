"""
Enhanced Base Language Server
============================

This module provides an enhanced base language server implementation with
real LSP capabilities, comprehensive error retrieval, and proper parameter validation.
"""

import json
import os
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable

from graph_sitter.shared.logging.get_logger import get_logger
from ..protocol.lsp_types import (
    Diagnostic, CompletionItem, Hover, SignatureHelp,
    Position, Range, DiagnosticSeverity
)
from ..protocol.enhanced_types import (
    CodeAction, WorkspaceEdit, DocumentSymbol, SemanticToken,
    CallHierarchyItem, TextEdit, MarkupContent, LSPCapabilities,
    LSPErrorCodes, EnhancedDiagnostic
)
from ..protocol.lsp_constants import LSPConstants

logger = get_logger(__name__)


class LSPMessage:
    """LSP message wrapper for JSON-RPC communication."""
    
    def __init__(self, method: str, params: Dict[str, Any] = None, id: Optional[Union[str, int]] = None):
        self.method = method
        self.params = params or {}
        self.id = id
        self.jsonrpc = "2.0"
    
    def to_json(self) -> str:
        """Convert message to JSON-RPC format."""
        message = {
            "jsonrpc": self.jsonrpc,
            "method": self.method
        }
        
        if self.params:
            message["params"] = self.params
        
        if self.id is not None:
            message["id"] = self.id
        
        return json.dumps(message)
    
    def to_lsp_message(self) -> str:
        """Convert to LSP message format with Content-Length header."""
        json_content = self.to_json()
        content_length = len(json_content.encode('utf-8'))
        
        return f"Content-Length: {content_length}\r\n\r\n{json_content}"


class EnhancedBaseLanguageServer(ABC):
    """Enhanced base class for language server implementations with real LSP capabilities."""
    
    def __init__(self, workspace_path: str, language: str):
        self.workspace_path = Path(workspace_path)
        self.language = language
        self.is_running = False
        self.is_initialized = False
        self.process: Optional[subprocess.Popen] = None
        self._lock = threading.RLock()
        self._message_id = 0
        self._pending_requests: Dict[int, Callable] = {}
        
        # Diagnostic caching
        self._diagnostics_cache: Dict[str, List[EnhancedDiagnostic]] = {}
        self._last_diagnostic_refresh = 0.0
        
        # Server capabilities
        self.server_capabilities: Dict[str, Any] = {}
        
        # Communication buffers
        self._stdout_buffer = ""
        self._stderr_buffer = ""
        
        # Shutdown flag
        self._shutdown = False
    
    @abstractmethod
    def get_server_command(self) -> List[str]:
        """Get the command to start the language server."""
        pass
    
    @abstractmethod
    def supports_file(self, file_path: str) -> bool:
        """Check if this server supports the given file."""
        pass
    
    def initialize(self) -> bool:
        """Initialize the language server with enhanced capabilities."""
        try:
            command = self.get_server_command()
            if not command:
                logger.warning(f"No server command available for {self.language}")
                return False
            
            # Check if the server executable exists
            if not self._check_server_availability():
                logger.warning(f"Language server for {self.language} is not available")
                return False
            
            with self._lock:
                # Start the language server process
                self.process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.workspace_path),
                    text=True,
                    bufsize=0  # Unbuffered for real-time communication
                )
                
                # Start communication threads
                self._start_communication_threads()
                
                # Send initialize request
                if self._send_initialize_request():
                    self.is_running = True
                    self.is_initialized = True
                    logger.info(f"Successfully initialized {self.language} language server")
                    
                    # Request initial diagnostics
                    self._request_diagnostics()
                    
                    return True
                else:
                    self._cleanup_process()
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to initialize {self.language} language server: {e}")
            self._cleanup_process()
            return False
    
    def _check_server_availability(self) -> bool:
        """Check if the language server is available."""
        command = self.get_server_command()
        if not command:
            return False
        
        try:
            # Try to run the server with --help or --version
            result = subprocess.run(
                [command[0], '--help'],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode in [0, 1]  # Some servers return 1 for --help
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _start_communication_threads(self) -> None:
        """Start threads for handling server communication."""
        # Thread for reading stdout
        stdout_thread = threading.Thread(
            target=self._read_stdout,
            daemon=True,
            name=f"{self.language}-stdout"
        )
        stdout_thread.start()
        
        # Thread for reading stderr
        stderr_thread = threading.Thread(
            target=self._read_stderr,
            daemon=True,
            name=f"{self.language}-stderr"
        )
        stderr_thread.start()
    
    def _read_stdout(self) -> None:
        """Read and process stdout from the language server."""
        try:
            while self.is_running and self.process and not self._shutdown:
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        self._process_server_message(line.strip())
                    else:
                        # EOF reached
                        break
                else:
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error reading stdout from {self.language} server: {e}")
    
    def _read_stderr(self) -> None:
        """Read and process stderr from the language server."""
        try:
            while self.is_running and self.process and not self._shutdown:
                if self.process.stderr:
                    line = self.process.stderr.readline()
                    if line:
                        logger.debug(f"{self.language} server stderr: {line.strip()}")
                    else:
                        # EOF reached
                        break
                else:
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error reading stderr from {self.language} server: {e}")
    
    def _process_server_message(self, message: str) -> None:
        """Process a message received from the language server."""
        try:
            # Handle LSP message format (Content-Length header + JSON)
            if message.startswith("Content-Length:"):
                # Extract content length
                content_length = int(message.split(":")[1].strip())
                
                # Read the JSON content
                if self.process and self.process.stdout:
                    # Skip the empty line
                    self.process.stdout.readline()
                    
                    # Read the JSON content
                    json_content = self.process.stdout.read(content_length)
                    
                    # Parse and handle the JSON message
                    self._handle_json_message(json_content)
            
        except Exception as e:
            logger.error(f"Error processing server message: {e}")
    
    def _handle_json_message(self, json_content: str) -> None:
        """Handle a JSON message from the language server."""
        try:
            message = json.loads(json_content)
            
            # Handle different message types
            if "method" in message:
                # This is a notification or request from server
                self._handle_server_notification(message)
            elif "id" in message:
                # This is a response to our request
                self._handle_server_response(message)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            logger.error(f"Error handling JSON message: {e}")
    
    def _handle_server_notification(self, message: Dict[str, Any]) -> None:
        """Handle notifications from the language server."""
        method = message.get("method")
        params = message.get("params", {})
        
        if method == LSPConstants.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS:
            # Handle diagnostic notifications
            self._handle_diagnostic_notification(params)
        elif method == LSPConstants.WINDOW_LOG_MESSAGE:
            # Handle log messages
            logger.debug(f"{self.language} server log: {params.get('message', '')}")
        elif method == LSPConstants.WINDOW_SHOW_MESSAGE:
            # Handle show message notifications
            logger.info(f"{self.language} server message: {params.get('message', '')}")
    
    def _handle_server_response(self, message: Dict[str, Any]) -> None:
        """Handle responses from the language server."""
        request_id = message.get("id")
        
        if request_id in self._pending_requests:
            callback = self._pending_requests.pop(request_id)
            
            if "error" in message:
                logger.error(f"Server error for request {request_id}: {message['error']}")
                callback(None, message["error"])
            else:
                callback(message.get("result"), None)
    
    def _handle_diagnostic_notification(self, params: Dict[str, Any]) -> None:
        """Handle diagnostic notifications from the server."""
        try:
            uri = params.get("uri", "")
            diagnostics = params.get("diagnostics", [])
            
            # Convert URI to file path
            file_path = uri.replace("file://", "")
            
            # Convert diagnostics to EnhancedDiagnostic objects
            enhanced_diagnostics = []
            for diag in diagnostics:
                enhanced_diag = self._convert_to_enhanced_diagnostic(diag, file_path)
                if enhanced_diag:
                    enhanced_diagnostics.append(enhanced_diag)
            
            # Update cache
            with self._lock:
                self._diagnostics_cache[file_path] = enhanced_diagnostics
                self._last_diagnostic_refresh = time.time()
            
            logger.debug(f"Updated diagnostics for {file_path}: {len(enhanced_diagnostics)} items")
            
        except Exception as e:
            logger.error(f"Error handling diagnostic notification: {e}")
    
    def _convert_to_enhanced_diagnostic(self, diagnostic: Dict[str, Any], file_path: str) -> Optional[EnhancedDiagnostic]:
        """Convert LSP diagnostic to EnhancedDiagnostic."""
        try:
            # Extract range information
            range_info = diagnostic.get("range", {})
            start_pos = range_info.get("start", {})
            end_pos = range_info.get("end", {})
            
            range_obj = Range(
                start=Position(
                    line=start_pos.get("line", 0),
                    character=start_pos.get("character", 0)
                ),
                end=Position(
                    line=end_pos.get("line", 0),
                    character=end_pos.get("character", 0)
                )
            )
            
            # Create enhanced diagnostic
            enhanced_diag = EnhancedDiagnostic(
                range=range_obj,
                message=diagnostic.get("message", ""),
                severity=DiagnosticSeverity(diagnostic.get("severity", DiagnosticSeverity.ERROR)),
                code=diagnostic.get("code"),
                source=diagnostic.get("source", self.language),
                tags=diagnostic.get("tags"),
                file_path=file_path,
                id=f"{self.language}_{hash(str(file_path) + '_' + str(range_obj.start.line) + '_' + diagnostic.get('message', ''))}",
                quick_fixes=[],  # Will be populated by code actions
                suggestions=[],  # Will be populated by analysis
                related_symbols=[]  # Will be populated by symbol analysis
            )
            
            return enhanced_diag
            
        except Exception as e:
            logger.error(f"Error converting diagnostic: {e}")
            return None
    
    def _send_initialize_request(self) -> bool:
        """Send LSP initialize request."""
        try:
            # Prepare initialization parameters
            init_params = {
                "processId": os.getpid(),
                "rootPath": str(self.workspace_path),
                "rootUri": f"file://{self.workspace_path}",
                "capabilities": {
                    "textDocument": {
                        "publishDiagnostics": {
                            "relatedInformation": True,
                            "versionSupport": False,
                            "tagSupport": {
                                "valueSet": [1, 2]  # Unnecessary and Deprecated
                            },
                            "codeDescriptionSupport": True,
                            "dataSupport": True
                        },
                        "completion": {
                            "dynamicRegistration": True,
                            "completionItem": {
                                "snippetSupport": True,
                                "commitCharactersSupport": True,
                                "documentationFormat": ["markdown", "plaintext"],
                                "deprecatedSupport": True,
                                "preselectSupport": True
                            }
                        },
                        "hover": {
                            "dynamicRegistration": True,
                            "contentFormat": ["markdown", "plaintext"]
                        },
                        "signatureHelp": {
                            "dynamicRegistration": True,
                            "signatureInformation": {
                                "documentationFormat": ["markdown", "plaintext"],
                                "parameterInformation": {
                                    "labelOffsetSupport": True
                                }
                            }
                        },
                        "definition": {
                            "dynamicRegistration": True,
                            "linkSupport": True
                        },
                        "references": {
                            "dynamicRegistration": True
                        },
                        "documentSymbol": {
                            "dynamicRegistration": True,
                            "symbolKind": {
                                "valueSet": list(range(1, 27))  # All symbol kinds
                            },
                            "hierarchicalDocumentSymbolSupport": True
                        },
                        "codeAction": {
                            "dynamicRegistration": True,
                            "codeActionLiteralSupport": {
                                "codeActionKind": {
                                    "valueSet": [
                                        "quickfix",
                                        "refactor",
                                        "refactor.extract",
                                        "refactor.inline",
                                        "refactor.rewrite",
                                        "source",
                                        "source.organizeImports",
                                        "source.fixAll"
                                    ]
                                }
                            },
                            "isPreferredSupport": True,
                            "disabledSupport": True,
                            "dataSupport": True,
                            "resolveSupport": {
                                "properties": ["edit"]
                            }
                        },
                        "formatting": {
                            "dynamicRegistration": True
                        },
                        "rangeFormatting": {
                            "dynamicRegistration": True
                        },
                        "rename": {
                            "dynamicRegistration": True,
                            "prepareSupport": True
                        }
                    },
                    "workspace": {
                        "applyEdit": True,
                        "workspaceEdit": {
                            "documentChanges": True,
                            "resourceOperations": ["create", "rename", "delete"],
                            "failureHandling": "textOnlyTransactional"
                        },
                        "didChangeConfiguration": {
                            "dynamicRegistration": True
                        },
                        "didChangeWatchedFiles": {
                            "dynamicRegistration": True
                        },
                        "symbol": {
                            "dynamicRegistration": True,
                            "symbolKind": {
                                "valueSet": list(range(1, 27))
                            }
                        },
                        "executeCommand": {
                            "dynamicRegistration": True
                        }
                    }
                },
                "initializationOptions": self._get_initialization_options(),
                "workspaceFolders": [
                    {
                        "uri": f"file://{self.workspace_path}",
                        "name": self.workspace_path.name
                    }
                ]
            }
            
            # Send initialize request
            response = self._send_request(LSPConstants.INITIALIZE, init_params)
            
            if response:
                # Store server capabilities
                self.server_capabilities = response.get("capabilities", {})
                
                # Send initialized notification
                self._send_notification(LSPConstants.INITIALIZED, {})
                
                logger.info(f"Successfully initialized {self.language} language server")
                return True
            else:
                logger.error(f"Failed to initialize {self.language} language server")
                return False
                
        except Exception as e:
            logger.error(f"Error sending initialize request: {e}")
            return False
    
    @abstractmethod
    def _get_initialization_options(self) -> Dict[str, Any]:
        """Get language-specific initialization options."""
        return {}
    
    def _send_request(self, method: str, params: Dict[str, Any], timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """Send a request to the language server and wait for response."""
        if not self.is_running or not self.process:
            return None
        
        try:
            with self._lock:
                request_id = self._message_id
                self._message_id += 1
            
            # Create response event
            response_event = threading.Event()
            response_data = {"result": None, "error": None}
            
            def response_callback(result, error):
                response_data["result"] = result
                response_data["error"] = error
                response_event.set()
            
            # Store callback
            self._pending_requests[request_id] = response_callback
            
            # Send request
            message = LSPMessage(method, params, request_id)
            lsp_message = message.to_lsp_message()
            
            if self.process.stdin:
                self.process.stdin.write(lsp_message)
                self.process.stdin.flush()
            
            # Wait for response
            if response_event.wait(timeout):
                if response_data["error"]:
                    logger.error(f"Server error: {response_data['error']}")
                    return None
                return response_data["result"]
            else:
                # Timeout
                self._pending_requests.pop(request_id, None)
                logger.warning(f"Request timeout for method {method}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending request {method}: {e}")
            return None
    
    def _send_notification(self, method: str, params: Dict[str, Any]) -> bool:
        """Send a notification to the language server."""
        if not self.is_running or not self.process:
            return False
        
        try:
            message = LSPMessage(method, params)
            lsp_message = message.to_lsp_message()
            
            if self.process.stdin:
                self.process.stdin.write(lsp_message)
                self.process.stdin.flush()
                return True
            
        except Exception as e:
            logger.error(f"Error sending notification {method}: {e}")
        
        return False
    
    def _request_diagnostics(self) -> None:
        """Request diagnostics for all supported files in the workspace."""
        try:
            for file_path in self.workspace_path.rglob("*"):
                if file_path.is_file() and self.supports_file(str(file_path)):
                    # Send textDocument/didOpen notification
                    self._notify_document_opened(str(file_path))
        except Exception as e:
            logger.error(f"Error requesting diagnostics: {e}")
    
    def _notify_document_opened(self, file_path: str) -> None:
        """Notify the server that a document was opened."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            params = {
                "textDocument": {
                    "uri": f"file://{file_path}",
                    "languageId": self.language,
                    "version": 1,
                    "text": content
                }
            }
            
            self._send_notification(LSPConstants.TEXT_DOCUMENT_DID_OPEN, params)
            
        except Exception as e:
            logger.error(f"Error notifying document opened {file_path}: {e}")
    
    def _cleanup_process(self) -> None:
        """Clean up the language server process."""
        try:
            self._shutdown = True
            self.is_running = False
            self.is_initialized = False
            
            if self.process:
                # Send shutdown request
                try:
                    self._send_request(LSPConstants.SHUTDOWN, {}, timeout=5.0)
                    self._send_notification(LSPConstants.EXIT, {})
                except:
                    pass  # Ignore errors during shutdown
                
                # Terminate process
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                except:
                    pass
                
                self.process = None
            
            # Clear caches
            self._diagnostics_cache.clear()
            self._pending_requests.clear()
            
        except Exception as e:
            logger.error(f"Error cleaning up process: {e}")
    
    # Public API for diagnostic retrieval
    
    def get_diagnostics(self, file_path: Optional[str] = None) -> List[EnhancedDiagnostic]:
        """Get diagnostics for a specific file or all files."""
        with self._lock:
            if file_path:
                return self._diagnostics_cache.get(file_path, [])
            else:
                # Return all diagnostics
                all_diagnostics = []
                for diagnostics in self._diagnostics_cache.values():
                    all_diagnostics.extend(diagnostics)
                return all_diagnostics
    
    def get_errors(self, file_path: Optional[str] = None) -> List[EnhancedDiagnostic]:
        """Get only error-level diagnostics."""
        diagnostics = self.get_diagnostics(file_path)
        return [d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR]
    
    def get_warnings(self, file_path: Optional[str] = None) -> List[EnhancedDiagnostic]:
        """Get only warning-level diagnostics."""
        diagnostics = self.get_diagnostics(file_path)
        return [d for d in diagnostics if d.severity == DiagnosticSeverity.WARNING]
    
    def refresh_diagnostics(self) -> bool:
        """Force refresh of diagnostics."""
        try:
            self._request_diagnostics()
            return True
        except Exception as e:
            logger.error(f"Error refreshing diagnostics: {e}")
            return False
    
    # LSP method implementations (to be overridden by subclasses)
    
    def get_completions(self, file_path: str, line: int, character: int) -> List[CompletionItem]:
        """Get completions at the specified position."""
        # Default implementation - subclasses should override
        return []
    
    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Hover]:
        """Get hover information at the specified position."""
        # Default implementation - subclasses should override
        return None
    
    def get_signature_help(self, file_path: str, line: int, character: int) -> Optional[SignatureHelp]:
        """Get signature help at the specified position."""
        # Default implementation - subclasses should override
        return None
    
    def get_definition(self, file_path: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get definition locations for the symbol at the specified position."""
        # Default implementation - subclasses should override
        return []
    
    def get_references(self, file_path: str, line: int, character: int, include_declaration: bool = True) -> List[Dict[str, Any]]:
        """Get reference locations for the symbol at the specified position."""
        # Default implementation - subclasses should override
        return []
    
    def get_document_symbols(self, file_path: str) -> List[DocumentSymbol]:
        """Get document symbols for the specified file."""
        # Default implementation - subclasses should override
        return []
    
    def get_code_actions(self, file_path: str, start_line: int, start_char: int, end_line: int, end_char: int) -> List[CodeAction]:
        """Get code actions for the specified range."""
        # Default implementation - subclasses should override
        return []
    
    def format_document(self, file_path: str) -> List[TextEdit]:
        """Format the entire document."""
        # Default implementation - subclasses should override
        return []
    
    def format_range(self, file_path: str, start_line: int, start_char: int, end_line: int, end_char: int) -> List[TextEdit]:
        """Format the specified range."""
        # Default implementation - subclasses should override
        return []
    
    def rename_symbol(self, file_path: str, line: int, character: int, new_name: str) -> Optional[WorkspaceEdit]:
        """Rename the symbol at the specified position."""
        # Default implementation - subclasses should override
        return None
    
    def shutdown(self) -> None:
        """Shutdown the language server."""
        self._cleanup_process()
        logger.info(f"{self.language} language server shut down")
