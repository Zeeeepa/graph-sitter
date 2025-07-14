"""
Serena-Graph-Sitter LSP Bridge

This module provides a bridge between Serena's LSP capabilities and Graph-Sitter's
transaction system, enabling real-time error detection and semantic analysis that
stays synchronized with codebase changes.
"""

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from graph_sitter.codebase.diff_lite import ChangeType, DiffLite
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

# Optional imports for Serena integration
try:
    from serena.project import Project
    from serena.symbol import LanguageServerSymbolRetriever
    from solidlsp import SolidLanguageServer
    from solidlsp.ls_types import Diagnostic, DiagnosticSeverity
    SERENA_AVAILABLE = True
except ImportError:
    logger.warning("Serena dependencies not available. LSP integration disabled.")
    SERENA_AVAILABLE = False
    # Fallback types
    class Diagnostic:
        pass
    class DiagnosticSeverity(Enum):
        ERROR = 1
        WARNING = 2
        INFORMATION = 3
        HINT = 4


@dataclass
class ErrorInfo:
    """Information about a code error detected by LSP."""
    file_path: str
    line: int
    column: int
    message: str
    severity: str
    code: Optional[str] = None
    source: Optional[str] = None
    
    def get_context(self, lines_before: int = 3, lines_after: int = 3) -> str:
        """Get contextual code around the error."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = max(0, self.line - lines_before - 1)
            end_line = min(len(lines), self.line + lines_after)
            
            context_lines = []
            for i in range(start_line, end_line):
                prefix = ">>> " if i == self.line - 1 else "    "
                context_lines.append(f"{prefix}{i+1:4d}: {lines[i].rstrip()}")
            
            return "\n".join(context_lines)
        except Exception as e:
            logger.warning(f"Failed to get context for error in {self.file_path}: {e}")
            return f"Error at line {self.line}: {self.message}"


class SerenaLSPBridge:
    """Bridge between Serena's LSP and Graph-Sitter's transaction system."""
    
    def __init__(self, repo_path: Path, enable_lsp: bool = True):
        self.repo_path = repo_path
        self.enable_lsp = enable_lsp and SERENA_AVAILABLE
        self._lock = threading.RLock()
        self._diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self._lsp_server: Optional[SolidLanguageServer] = None
        self._project: Optional[Project] = None
        self._symbol_retriever: Optional[LanguageServerSymbolRetriever] = None
        
        if self.enable_lsp:
            self._initialize_lsp()
    
    def _initialize_lsp(self) -> None:
        """Initialize Serena's LSP components."""
        try:
            from serena.config.serena_config import ProjectConfig
            
            # Create project configuration
            project_config = ProjectConfig.from_path(str(self.repo_path))
            self._project = Project(str(self.repo_path), project_config)
            
            # Initialize language server
            self._lsp_server = SolidLanguageServer(
                project_root=str(self.repo_path),
                config=project_config.language_server_config
            )
            
            # Initialize symbol retriever
            self._symbol_retriever = LanguageServerSymbolRetriever(
                self._lsp_server, self._project
            )
            
            logger.info(f"Serena LSP initialized for {self.repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Serena LSP: {e}")
            self.enable_lsp = False
    
    def handle_file_change(self, diff: DiffLite) -> None:
        """Handle file changes from Graph-Sitter's transaction system."""
        if not self.enable_lsp:
            return
        
        with self._lock:
            try:
                file_path = str(diff.path)
                
                if diff.change_type == ChangeType.Added:
                    self._handle_file_added(file_path)
                elif diff.change_type == ChangeType.Modified:
                    self._handle_file_modified(file_path)
                elif diff.change_type == ChangeType.Removed:
                    self._handle_file_removed(file_path)
                elif diff.change_type == ChangeType.Renamed:
                    self._handle_file_renamed(diff.rename_from, diff.rename_to)
                
                # Invalidate diagnostics cache for affected file
                self._invalidate_diagnostics_cache(file_path)
                
            except Exception as e:
                logger.error(f"Error handling file change {diff}: {e}")
    
    def _handle_file_added(self, file_path: str) -> None:
        """Handle file addition."""
        if self._lsp_server:
            self._lsp_server.did_open_text_document(file_path)
    
    def _handle_file_modified(self, file_path: str) -> None:
        """Handle file modification."""
        if self._lsp_server:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._lsp_server.did_change_text_document(file_path, content)
            except Exception as e:
                logger.warning(f"Failed to read modified file {file_path}: {e}")
    
    def _handle_file_removed(self, file_path: str) -> None:
        """Handle file removal."""
        if self._lsp_server:
            self._lsp_server.did_close_text_document(file_path)
    
    def _handle_file_renamed(self, old_path: Optional[Path], new_path: Optional[Path]) -> None:
        """Handle file rename."""
        if old_path and new_path and self._lsp_server:
            self._lsp_server.did_close_text_document(str(old_path))
            self._lsp_server.did_open_text_document(str(new_path))
    
    def _invalidate_diagnostics_cache(self, file_path: str) -> None:
        """Invalidate diagnostics cache for a specific file."""
        self._diagnostics_cache.pop(file_path, None)
    
    def get_errors(self) -> List[ErrorInfo]:
        """Get all errors in the codebase."""
        return self._get_diagnostics_by_severity(['error'])
    
    def get_warnings(self) -> List[ErrorInfo]:
        """Get all warnings in the codebase."""
        return self._get_diagnostics_by_severity(['warning'])
    
    def get_hints(self) -> List[ErrorInfo]:
        """Get all hints in the codebase."""
        return self._get_diagnostics_by_severity(['hint', 'information'])
    
    def get_diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics (errors, warnings, hints) in the codebase."""
        return self._get_diagnostics_by_severity(['error', 'warning', 'hint', 'information'])
    
    def _get_diagnostics_by_severity(self, severities: List[str]) -> List[ErrorInfo]:
        """Get diagnostics filtered by severity levels."""
        if not self.enable_lsp:
            return []
        
        with self._lock:
            try:
                all_diagnostics = []
                
                # Get diagnostics for all files in the project
                for file_path in self._get_source_files():
                    file_diagnostics = self._get_file_diagnostics(file_path)
                    filtered_diagnostics = [
                        d for d in file_diagnostics 
                        if d.severity.lower() in severities
                    ]
                    all_diagnostics.extend(filtered_diagnostics)
                
                return all_diagnostics
                
            except Exception as e:
                logger.error(f"Error getting diagnostics: {e}")
                return []
    
    def _get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get diagnostics for a specific file, using cache when possible."""
        if file_path in self._diagnostics_cache:
            return self._diagnostics_cache[file_path]
        
        if not self._lsp_server:
            return []
        
        try:
            # Get diagnostics from LSP server
            diagnostics = self._lsp_server.get_diagnostics(file_path)
            
            error_infos = []
            for diagnostic in diagnostics:
                severity_map = {
                    DiagnosticSeverity.ERROR: 'error',
                    DiagnosticSeverity.WARNING: 'warning',
                    DiagnosticSeverity.INFORMATION: 'information',
                    DiagnosticSeverity.HINT: 'hint'
                }
                
                error_info = ErrorInfo(
                    file_path=file_path,
                    line=diagnostic.range.start.line + 1,  # Convert to 1-based
                    column=diagnostic.range.start.character + 1,
                    message=diagnostic.message,
                    severity=severity_map.get(diagnostic.severity, 'unknown'),
                    code=str(diagnostic.code) if diagnostic.code else None,
                    source=diagnostic.source
                )
                error_infos.append(error_info)
            
            # Cache the results
            self._diagnostics_cache[file_path] = error_infos
            return error_infos
            
        except Exception as e:
            logger.warning(f"Failed to get diagnostics for {file_path}: {e}")
            return []
    
    def _get_source_files(self) -> List[str]:
        """Get list of source files in the project."""
        if not self._project:
            return []
        
        try:
            source_files = []
            for file_path in self.repo_path.rglob("*"):
                if file_path.is_file() and not self._project.is_ignored(str(file_path)):
                    # Check if it's a source file based on extension
                    if file_path.suffix in ['.py', '.ts', '.js', '.tsx', '.jsx', '.go', '.rs', '.java', '.php', '.cs']:
                        source_files.append(str(file_path))
            return source_files
        except Exception as e:
            logger.error(f"Error getting source files: {e}")
            return []
    
    def shutdown(self) -> None:
        """Shutdown the LSP bridge and clean up resources."""
        with self._lock:
            if self._lsp_server:
                try:
                    self._lsp_server.shutdown()
                except Exception as e:
                    logger.warning(f"Error shutting down LSP server: {e}")
            
            self._diagnostics_cache.clear()
            self._lsp_server = None
            self._project = None
            self._symbol_retriever = None
