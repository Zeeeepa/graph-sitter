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
    
    def notify_file_changes(self, file_paths: List[str]) -> None:
        """Notify language servers of file changes."""
        if not self.is_initialized:
            return
        
        with self._lock:
            for file_path in file_paths:
                # Clear cached diagnostics for changed files
                if file_path in self.diagnostics_cache:
                    del self.diagnostics_cache[file_path]
                
                # Notify appropriate language servers
                for server in self.language_servers.values():
                    if server.supports_file(file_path):
                        try:
                            server.notify_file_change(file_path)
                        except Exception as e:
                            logger.error(f"Error notifying server of file change {file_path}: {e}")
    
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
