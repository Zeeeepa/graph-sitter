"""
Base Language Server implementation.

This module provides the abstract base class for all language server implementations.
"""

import os
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from graph_sitter.shared.logging.get_logger import get_logger
from ..protocol.lsp_types import (
    Diagnostic, CompletionItem, Hover, SignatureHelp,
    Position, Range, TextEdit, WorkspaceEdit
)

logger = get_logger(__name__)


class BaseLanguageServer(ABC):
    """Abstract base class for language server implementations."""
    
    def __init__(self, workspace_path: str, language: str):
        self.workspace_path = Path(workspace_path)
        self.language = language
        self.is_running = False
        self.process: Optional[subprocess.Popen] = None
        self._lock = threading.RLock()
        self._diagnostics_cache: Dict[str, List[Diagnostic]] = {}
        
    @abstractmethod
    def get_server_command(self) -> List[str]:
        """Get the command to start the language server."""
        pass
    
    @abstractmethod
    def supports_file(self, file_path: str) -> bool:
        """Check if this server supports the given file."""
        pass
    
    def initialize(self) -> bool:
        """Initialize the language server."""
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
                self.process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.workspace_path),
                    text=True
                )
                
                # Send initialize request
                if self._send_initialize_request():
                    self.is_running = True
                    logger.info(f"Successfully initialized {self.language} language server")
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
                timeout=5
            )
            return result.returncode == 0 or result.returncode == 1  # Some servers return 1 for --help
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _send_initialize_request(self) -> bool:
        """Send LSP initialize request."""
        # This is a simplified implementation
        # In a real implementation, you'd send proper LSP JSON-RPC messages
        try:
            if self.process and self.process.stdin:
                # Simplified initialization - in reality this would be JSON-RPC
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to send initialize request: {e}")
            return False
    
    def get_completions(self, file_path: str, line: int, character: int) -> List[CompletionItem]:
        """Get code completions at the specified position."""
        if not self.is_running:
            return []
        
        try:
            # This is a placeholder implementation
            # In a real implementation, you'd send LSP textDocument/completion request
            return self._get_mock_completions(file_path, line, character)
        except Exception as e:
            logger.error(f"Error getting completions: {e}")
            return []
    
    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Hover]:
        """Get hover information at the specified position."""
        if not self.is_running:
            return None
        
        try:
            # This is a placeholder implementation
            # In a real implementation, you'd send LSP textDocument/hover request
            return self._get_mock_hover(file_path, line, character)
        except Exception as e:
            logger.error(f"Error getting hover info: {e}")
            return None
    
    def get_signature_help(self, file_path: str, line: int, character: int) -> Optional[SignatureHelp]:
        """Get signature help at the specified position."""
        if not self.is_running:
            return None
        
        try:
            # This is a placeholder implementation
            # In a real implementation, you'd send LSP textDocument/signatureHelp request
            return self._get_mock_signature_help(file_path, line, character)
        except Exception as e:
            logger.error(f"Error getting signature help: {e}")
            return None
    
    def get_diagnostics(self) -> List[Diagnostic]:
        """Get all diagnostics from the language server."""
        if not self.is_running:
            return []
        
        with self._lock:
            all_diagnostics = []
            for file_diagnostics in self._diagnostics_cache.values():
                all_diagnostics.extend(file_diagnostics)
            return all_diagnostics
    
    def get_file_diagnostics(self, file_path: str) -> List[Diagnostic]:
        """Get diagnostics for a specific file."""
        if not self.is_running:
            return []
        
        with self._lock:
            return self._diagnostics_cache.get(file_path, [])
    
    def refresh_diagnostics(self) -> None:
        """Refresh diagnostic information."""
        if not self.is_running:
            return
        
        try:
            # This is a placeholder implementation
            # In a real implementation, you'd request fresh diagnostics from the server
            self._update_diagnostics_cache()
        except Exception as e:
            logger.error(f"Error refreshing diagnostics: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the language server."""
        with self._lock:
            if self.process:
                try:
                    # Send shutdown request
                    if self.process.stdin:
                        self.process.stdin.close()
                    
                    # Wait for process to terminate
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                except Exception as e:
                    logger.error(f"Error during shutdown: {e}")
                finally:
                    self._cleanup_process()
    
    def _cleanup_process(self) -> None:
        """Clean up the language server process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception:
                pass
            finally:
                self.process = None
        
        self.is_running = False
        self._diagnostics_cache.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about the language server."""
        return {
            'language': self.language,
            'running': self.is_running,
            'workspace_path': str(self.workspace_path),
            'process_id': self.process.pid if self.process else None,
            'diagnostics_count': sum(len(diags) for diags in self._diagnostics_cache.values())
        }
    
    # Mock implementations for testing - these would be replaced with real LSP communication
    
    def _get_mock_completions(self, file_path: str, line: int, character: int) -> List[CompletionItem]:
        """Mock completion implementation."""
        from ..protocol.lsp_types import CompletionItem, CompletionItemKind
        
        return [
            CompletionItem(
                label="mock_function",
                kind=CompletionItemKind.FUNCTION,
                detail="Mock function for testing",
                documentation="This is a mock completion item for testing purposes"
            ),
            CompletionItem(
                label="mock_variable",
                kind=CompletionItemKind.VARIABLE,
                detail="Mock variable",
                documentation="This is a mock variable completion"
            )
        ]
    
    def _get_mock_hover(self, file_path: str, line: int, character: int) -> Optional[Hover]:
        """Mock hover implementation."""
        from ..protocol.lsp_types import Hover, MarkupContent
        
        return Hover(
            contents=MarkupContent(
                kind="markdown",
                value=f"**Mock Hover Information**\\n\\nFile: {file_path}\\nPosition: {line}:{character}\\n\\nThis is mock hover information for testing."
            )
        )
    
    def _get_mock_signature_help(self, file_path: str, line: int, character: int) -> Optional[SignatureHelp]:
        """Mock signature help implementation."""
        from ..protocol.lsp_types import SignatureHelp, SignatureInformation, ParameterInformation
        
        return SignatureHelp(
            signatures=[
                SignatureInformation(
                    label="mock_function(param1: str, param2: int) -> bool",
                    documentation="Mock function signature for testing",
                    parameters=[
                        ParameterInformation(
                            label="param1: str",
                            documentation="First parameter"
                        ),
                        ParameterInformation(
                            label="param2: int", 
                            documentation="Second parameter"
                        )
                    ]
                )
            ],
            active_signature=0,
            active_parameter=0
        )
    
    def _update_diagnostics_cache(self) -> None:
        """Update the diagnostics cache with mock data."""
        # This is a mock implementation
        # In a real implementation, this would parse diagnostics from the language server
        pass

