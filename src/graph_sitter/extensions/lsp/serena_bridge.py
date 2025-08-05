"""
Serena LSP Bridge for Graph-Sitter

This module provides a bridge between Serena's solidlsp implementation
and graph-sitter's codebase analysis system.
"""

import os
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from enum import IntEnum

from graph_sitter.shared.logging.get_logger import get_logger
from .protocol.lsp_types import DiagnosticSeverity, Diagnostic, Position, Range
from .language_servers.base import BaseLanguageServer
from .language_servers.python_server import PythonLanguageServer

logger = get_logger(__name__)


# DiagnosticSeverity is now imported from protocol.lsp_types


@dataclass
class ErrorInfo:
    """Standardized error information for graph-sitter."""
    file_path: str
    line: int
    character: int
    message: str
    severity: DiagnosticSeverity
    source: Optional[str] = None
    code: Optional[Union[str, int]] = None
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error (not warning or hint)."""
        return self.severity == DiagnosticSeverity.ERROR
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning."""
        return self.severity == DiagnosticSeverity.WARNING
    
    @property
    def is_hint(self) -> bool:
        """Check if this is a hint."""
        return self.severity == DiagnosticSeverity.HINT
    
    def get_context(self, lines_before: int = 2, lines_after: int = 2) -> str:
        """
        Get context lines around the error location.
        
        Args:
            lines_before: Number of lines to include before the error line
            lines_after: Number of lines to include after the error line
            
        Returns:
            Formatted string with context lines and error highlighting
        """
        try:
            file_path = Path(self.file_path)
            if not file_path.exists():
                return f"File not found: {self.file_path}"
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Calculate line range (convert to 0-based indexing)
            error_line_idx = max(0, self.line - 1)
            start_idx = max(0, error_line_idx - lines_before)
            end_idx = min(len(lines), error_line_idx + lines_after + 1)
            
            # Build context with line numbers
            context_lines = []
            for i in range(start_idx, end_idx):
                line_num = i + 1
                line_content = lines[i].rstrip('\n\r')
                
                # Highlight the error line
                if i == error_line_idx:
                    # Add error indicator and highlight
                    context_lines.append(f">>> {line_num:4d}: {line_content}")
                    
                    # Add character position indicator if available
                    if self.character > 0:
                        spaces = " " * (8 + self.character - 1)  # Account for line number prefix
                        context_lines.append(f"{spaces}^")
                else:
                    context_lines.append(f"    {line_num:4d}: {line_content}")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"Failed to get context for {self.file_path}:{self.line}: {e}")
            return f"Error reading context: {e}"
    
    def get_detailed_context(self, lines_before: int = 5, lines_after: int = 5) -> Dict[str, Any]:
        """
        Get detailed context information including metadata.
        
        Args:
            lines_before: Number of lines to include before the error line
            lines_after: Number of lines to include after the error line
            
        Returns:
            Dictionary with detailed context information
        """
        try:
            file_path = Path(self.file_path)
            if not file_path.exists():
                return {
                    "error": f"File not found: {self.file_path}",
                    "context_lines": [],
                    "error_line": self.line,
                    "character": self.character
                }
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Calculate line range
            error_line_idx = max(0, self.line - 1)
            start_idx = max(0, error_line_idx - lines_before)
            end_idx = min(len(lines), error_line_idx + lines_after + 1)
            
            # Build context data
            context_lines = []
            for i in range(start_idx, end_idx):
                line_num = i + 1
                line_content = lines[i].rstrip('\n\r')
                
                context_lines.append({
                    "line_number": line_num,
                    "content": line_content,
                    "is_error_line": i == error_line_idx,
                    "character_position": self.character if i == error_line_idx else None
                })
            
            return {
                "file_path": str(file_path),
                "error_line": self.line,
                "character": self.character,
                "context_lines": context_lines,
                "total_lines": len(lines),
                "context_range": {
                    "start": start_idx + 1,
                    "end": end_idx
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get detailed context for {self.file_path}:{self.line}: {e}")
            return {
                "error": str(e),
                "file_path": self.file_path,
                "error_line": self.line,
                "character": self.character,
                "context_lines": []
            }
    
    def __str__(self) -> str:
        severity_str = {
            DiagnosticSeverity.ERROR: "ERROR",
            DiagnosticSeverity.WARNING: "WARNING", 
            DiagnosticSeverity.INFORMATION: "INFO",
            DiagnosticSeverity.HINT: "HINT"
        }.get(self.severity, "UNKNOWN")
        
        return f"{severity_str} {self.file_path}:{self.line}:{self.character} - {self.message}"


class SerenaLSPBridge:
    """Bridge between Serena's LSP implementation and graph-sitter."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.language_servers: Dict[str, BaseLanguageServer] = {}
        self.diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self.is_initialized = False
        self._lock = threading.RLock()
        
        self._initialize_language_servers()
    
    def _initialize_language_servers(self) -> None:
        """Initialize language servers for detected languages."""
        try:
            # Detect Python files
            if self._has_python_files():
                self._initialize_python_server()
            
            # TODO: Add TypeScript, JavaScript, etc.
            
            self.is_initialized = len(self.language_servers) > 0
            logger.info(f"LSP bridge initialized for {self.repo_path} with {len(self.language_servers)} servers")
            
        except Exception as e:
            logger.error(f"Failed to initialize LSP bridge: {e}")
    
    def _has_python_files(self) -> bool:
        """Check if repository contains Python files."""
        for py_file in self.repo_path.rglob("*.py"):
            if not any(part.startswith('.') for part in py_file.parts):
                return True
        return False
    
    def _initialize_python_server(self) -> None:
        """Initialize Python language server."""
        try:
            server = PythonLanguageServer(str(self.repo_path))
            if server.initialize():
                self.language_servers['python'] = server
                logger.info("Python language server initialized")
            else:
                logger.warning("Failed to initialize Python language server")
            
        except Exception as e:
            logger.error(f"Failed to initialize Python language server: {e}")
    
    def get_diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics from all language servers."""
        if not self.is_initialized:
            return []
        
        all_diagnostics = []
        
        with self._lock:
            for lang, server in self.language_servers.items():
                try:
                    diagnostics = server.get_diagnostics()
                    all_diagnostics.extend(diagnostics)
                except Exception as e:
                    logger.error(f"Error getting diagnostics from {lang} server: {e}")
        
        return all_diagnostics
    


    
    def get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get diagnostics for a specific file."""
        if not self.is_initialized:
            return []
        
        file_diagnostics = []
        
        with self._lock:
            for lang, server in self.language_servers.items():
                try:
                    if server.supports_file(file_path):
                        diagnostics = server.get_file_diagnostics(file_path)
                        file_diagnostics.extend(diagnostics)
                except Exception as e:
                    logger.error(f"Error getting file diagnostics from {lang} server: {e}")
        
        return file_diagnostics
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        if not self.is_initialized:
            return
        
        with self._lock:
            self.diagnostics_cache.clear()
            
            for lang, server in self.language_servers.items():
                try:
                    server.refresh_diagnostics()
                except Exception as e:
                    logger.error(f"Error refreshing diagnostics for {lang} server: {e}")
    
    def shutdown(self) -> None:
        """Shutdown all language servers."""
        with self._lock:
            for lang, server in self.language_servers.items():
                try:
                    server.shutdown()
                    logger.info(f"Shutdown {lang} language server")
                except Exception as e:
                    logger.error(f"Error shutting down {lang} server: {e}")
            
            self.language_servers.clear()
            self.diagnostics_cache.clear()
            self.is_initialized = False
    
    def get_completions(self, file_path: str, line: int, character: int) -> List[Any]:
        """Get code completions at the specified position."""
        if not self.is_initialized:
            return []
        
        # Find appropriate language server
        for server in self.language_servers.values():
            if server.supports_file(file_path):
                return server.get_completions(file_path, line, character)
        
        return []
    
    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Any]:
        """Get hover information at the specified position."""
        if not self.is_initialized:
            return None
        
        # Find appropriate language server
        for server in self.language_servers.values():
            if server.supports_file(file_path):
                return server.get_hover_info(file_path, line, character)
        
        return None
    
    def get_signature_help(self, file_path: str, line: int, character: int) -> Optional[Any]:
        """Get signature help at the specified position."""
        if not self.is_initialized:
            return None
        
        # Find appropriate language server
        for server in self.language_servers.values():
            if server.supports_file(file_path):
                return server.get_signature_help(file_path, line, character)
        
        return None
    
    def initialize_language_servers(self) -> None:
        """Initialize all language servers."""
        with self._lock:
            for server in self.language_servers.values():
                if not server.is_running:
                    server.initialize()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about the LSP bridge."""
        server_status = {}
        for lang, server in self.language_servers.items():
            server_status[lang] = server.get_status()
        
        return {
            'initialized': self.is_initialized,
            'language_servers': list(self.language_servers.keys()),
            'repo_path': str(self.repo_path),
            'server_details': server_status
        }
