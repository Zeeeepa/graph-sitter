"""
Enhanced Serena LSP Bridge for Graph-Sitter

This module provides a comprehensive bridge between Serena's solidlsp implementation
and graph-sitter's codebase analysis system, with optional runtime error collection
and enhanced LSP capabilities.
"""

import os
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Callable
from enum import IntEnum

from graph_sitter.shared.logging.get_logger import get_logger
from .protocol.lsp_types import DiagnosticSeverity, Diagnostic, Position, Range
from .language_servers.base import BaseLanguageServer
from .language_servers.python_server import PythonLanguageServer

# Optional Serena imports with graceful fallback
SERENA_AVAILABLE = False
try:
    # Try to import Serena LSP components
    from solidlsp import SolidLanguageServer
    from solidlsp.ls_config import Language, LanguageServerConfig
    from solidlsp.ls_logger import LanguageServerLogger
    from solidlsp.settings import SolidLSPSettings
    from solidlsp.ls import ReferenceInSymbol as LSPReferenceInSymbol
    from solidlsp.ls_types import Position as SerenaPosition, SymbolKind, UnifiedSymbolInformation
    from solidlsp.ls import LSPFileBuffer
    from solidlsp.ls_utils import TextUtils
    
    # Try to import Serena project components
    try:
        from serena.symbol import JetBrainsSymbol, LanguageServerSymbol, LanguageServerSymbolRetriever, PositionInFile, Symbol
        from serena.project import Project
        from serena.config.serena_config import DEFAULT_TOOL_TIMEOUT, ProjectConfig
        from serena.constants import SERENA_MANAGED_DIR_IN_HOME
        from serena.text_utils import MatchedConsecutiveLines, search_files
        from serena.util.file_system import GitignoreParser, match_path
        SERENA_FULL_AVAILABLE = True
    except ImportError:
        SERENA_FULL_AVAILABLE = False
    
    SERENA_AVAILABLE = True
    logger.info("Serena LSP components available")
except ImportError:
    SERENA_AVAILABLE = False
    SERENA_FULL_AVAILABLE = False
    logger.info("Serena LSP components not available - using basic functionality")

# Optional runtime error collection
try:
    from .runtime_collector import RuntimeErrorCollector, RuntimeErrorInfo, ErrorType, RuntimeContext
    RUNTIME_COLLECTION_AVAILABLE = True
except ImportError:
    RUNTIME_COLLECTION_AVAILABLE = False
    logger.warning("Runtime error collection not available")

logger = get_logger(__name__)


# DiagnosticSeverity is now imported from protocol.lsp_types


@dataclass
class ErrorInfo:
    """Enhanced error information for graph-sitter with optional runtime context."""
    file_path: str
    line: int
    character: int
    message: str
    severity: DiagnosticSeverity
    source: Optional[str] = None
    code: Optional[Union[str, int]] = None
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    
    # Enhanced fields for runtime error support
    error_type: Optional['ErrorType'] = None
    runtime_context: Optional['RuntimeContext'] = None
    fix_suggestions: List[str] = field(default_factory=list)
    symbol_info: Optional[Dict[str, Any]] = None
    code_context: Optional[str] = None
    
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
    
    @property
    def is_runtime_error(self) -> bool:
        """Check if this is a runtime error."""
        if RUNTIME_COLLECTION_AVAILABLE and self.error_type:
            return self.error_type == ErrorType.RUNTIME_ERROR
        return self.runtime_context is not None
    
    @property
    def is_static_error(self) -> bool:
        """Check if this is a static analysis error."""
        if RUNTIME_COLLECTION_AVAILABLE and self.error_type:
            return self.error_type == ErrorType.STATIC_ANALYSIS
        return self.runtime_context is None
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get comprehensive context information."""
        context = {
            'basic_info': {
                'file_path': self.file_path,
                'line': self.line,
                'character': self.character,
                'message': self.message,
                'severity': self.severity.name,
                'source': self.source,
                'code': self.code,
                'end_line': self.end_line,
                'end_character': self.end_character
            },
            'fix_suggestions': self.fix_suggestions,
            'code_context': self.code_context,
            'symbol_info': self.symbol_info
        }
        
        if self.error_type:
            context['basic_info']['error_type'] = self.error_type.name
        
        if self.runtime_context:
            context['runtime'] = {
                'exception_type': self.runtime_context.exception_type,
                'stack_trace': self.runtime_context.stack_trace,
                'local_variables': self.runtime_context.local_variables,
                'global_variables': self.runtime_context.global_variables,
                'execution_path': self.runtime_context.execution_path,
                'timestamp': self.runtime_context.timestamp,
                'thread_id': self.runtime_context.thread_id,
                'process_id': self.runtime_context.process_id
            }
        
        return context
    
    def __str__(self) -> str:
        severity_str = {
            DiagnosticSeverity.ERROR: "ERROR",
            DiagnosticSeverity.WARNING: "WARNING", 
            DiagnosticSeverity.INFORMATION: "INFO",
            DiagnosticSeverity.HINT: "HINT"
        }.get(self.severity, "UNKNOWN")
        
        error_type_str = ""
        if self.error_type:
            error_type_str = f"[{self.error_type.name}] "
        
        return f"{severity_str} {error_type_str}{self.file_path}:{self.line}:{self.character} - {self.message}"


class SerenaLSPBridge:
    """Enhanced bridge between Serena's LSP implementation and graph-sitter with runtime error collection."""
    
    def __init__(self, repo_path: str, enable_runtime_collection: bool = False):
        self.repo_path = Path(repo_path)
        self.language_servers: Dict[str, BaseLanguageServer] = {}
        self.diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self.is_initialized = False
        self.enable_runtime_collection = enable_runtime_collection
        self._lock = threading.RLock()
        
        # Optional runtime error collection
        self.runtime_collector: Optional['RuntimeErrorCollector'] = None
        if enable_runtime_collection and RUNTIME_COLLECTION_AVAILABLE:
            self.runtime_collector = RuntimeErrorCollector(str(repo_path))
            self.runtime_collector.start_collection()
        
        # Optional Serena components
        self.serena_project: Optional['Project'] = None
        self.serena_symbol_retriever: Optional['LanguageServerSymbolRetriever'] = None
        self.solid_language_server: Optional['SolidLanguageServer'] = None
        
        self._initialize_language_servers()
        self._initialize_serena_components()
    
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
    
    def _initialize_serena_components(self) -> None:
        """Initialize Serena LSP components if available."""
        if not SERENA_AVAILABLE:
            return
        
        try:
            # Initialize Serena project if full components are available
            if SERENA_FULL_AVAILABLE:
                try:
                    self.serena_project = Project(str(self.repo_path))
                    logger.info("Serena project initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Serena project: {e}")
                
                # Initialize symbol retriever
                try:
                    if self.serena_project:
                        self.serena_symbol_retriever = LanguageServerSymbolRetriever(self.serena_project)
                        logger.info("Serena symbol retriever initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Serena symbol retriever: {e}")
            
            # Initialize SolidLanguageServer
            try:
                config = LanguageServerConfig()
                self.solid_language_server = SolidLanguageServer(config)
                logger.info("SolidLanguageServer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize SolidLanguageServer: {e}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Serena components: {e}")
    
    def get_diagnostics(self, include_runtime: bool = True) -> List[ErrorInfo]:
        """Get all diagnostics from all language servers and optionally runtime errors."""
        all_diagnostics = []
        
        # Get static analysis diagnostics
        if self.is_initialized:
            with self._lock:
                for lang, server in self.language_servers.items():
                    try:
                        diagnostics = server.get_diagnostics()
                        # Convert to enhanced ErrorInfo if needed
                        for diag in diagnostics:
                            if not hasattr(diag, 'error_type'):
                                # Convert basic ErrorInfo to enhanced version
                                enhanced_diag = ErrorInfo(
                                    file_path=diag.file_path,
                                    line=diag.line,
                                    character=diag.character,
                                    message=diag.message,
                                    severity=diag.severity,
                                    source=diag.source,
                                    code=diag.code,
                                    end_line=diag.end_line,
                                    end_character=diag.end_character
                                )
                                if RUNTIME_COLLECTION_AVAILABLE:
                                    enhanced_diag.error_type = ErrorType.STATIC_ANALYSIS
                                all_diagnostics.append(enhanced_diag)
                            else:
                                all_diagnostics.append(diag)
                    except Exception as e:
                        logger.error(f"Error getting diagnostics from {lang} server: {e}")
        
        # Add runtime errors if requested and available
        if include_runtime and self.runtime_collector:
            try:
                runtime_errors = self.runtime_collector.get_runtime_errors()
                # Convert RuntimeErrorInfo to ErrorInfo
                for runtime_error in runtime_errors:
                    error_info = ErrorInfo(
                        file_path=runtime_error.file_path,
                        line=runtime_error.line,
                        character=runtime_error.character,
                        message=runtime_error.message,
                        severity=runtime_error.severity,
                        source=runtime_error.source,
                        code=runtime_error.code,
                        error_type=runtime_error.error_type,
                        runtime_context=runtime_error.runtime_context,
                        fix_suggestions=runtime_error.fix_suggestions
                    )
                    all_diagnostics.append(error_info)
            except Exception as e:
                logger.error(f"Error getting runtime errors: {e}")
        
        return all_diagnostics
    


    def get_static_errors(self) -> List[ErrorInfo]:
        """Get only static analysis errors (no runtime errors)."""
        return self.get_diagnostics(include_runtime=False)
    
    def get_runtime_errors(self) -> List[ErrorInfo]:
        """Get only runtime errors."""
        if not self.runtime_collector:
            return []
        
        try:
            runtime_errors = self.runtime_collector.get_runtime_errors()
            # Convert RuntimeErrorInfo to ErrorInfo
            error_infos = []
            for runtime_error in runtime_errors:
                error_info = ErrorInfo(
                    file_path=runtime_error.file_path,
                    line=runtime_error.line,
                    character=runtime_error.character,
                    message=runtime_error.message,
                    severity=runtime_error.severity,
                    source=runtime_error.source,
                    code=runtime_error.code,
                    error_type=runtime_error.error_type,
                    runtime_context=runtime_error.runtime_context,
                    fix_suggestions=runtime_error.fix_suggestions
                )
                error_infos.append(error_info)
            return error_infos
        except Exception as e:
            logger.error(f"Error getting runtime errors: {e}")
            return []
    
    def get_runtime_errors_for_file(self, file_path: str) -> List[ErrorInfo]:
        """Get runtime errors for a specific file."""
        if not self.runtime_collector:
            return []
        
        try:
            runtime_errors = self.runtime_collector.get_runtime_errors_for_file(file_path)
            # Convert RuntimeErrorInfo to ErrorInfo
            error_infos = []
            for runtime_error in runtime_errors:
                error_info = ErrorInfo(
                    file_path=runtime_error.file_path,
                    line=runtime_error.line,
                    character=runtime_error.character,
                    message=runtime_error.message,
                    severity=runtime_error.severity,
                    source=runtime_error.source,
                    code=runtime_error.code,
                    error_type=runtime_error.error_type,
                    runtime_context=runtime_error.runtime_context,
                    fix_suggestions=runtime_error.fix_suggestions
                )
                error_infos.append(error_info)
            return error_infos
        except Exception as e:
            logger.error(f"Error getting runtime errors for file {file_path}: {e}")
            return []
    
    def clear_runtime_errors(self) -> None:
        """Clear all collected runtime errors."""
        if self.runtime_collector:
            self.runtime_collector.clear_runtime_errors()
    
    def get_runtime_error_summary(self) -> Dict[str, Any]:
        """Get summary statistics about runtime errors."""
        if not self.runtime_collector:
            return {
                'total_errors': 0,
                'collection_active': False,
                'errors_by_type': {},
                'errors_by_file': {}
            }
        
        return self.runtime_collector.get_error_summary()
    
    def get_all_errors_with_context(self) -> List[Dict[str, Any]]:
        """Get all errors with comprehensive context information."""
        all_errors = self.get_diagnostics(include_runtime=True)
        return [error.get_full_context() for error in all_errors]
    
    def get_file_diagnostics(self, file_path: str, include_runtime: bool = True) -> List[ErrorInfo]:
        """Get diagnostics for a specific file."""
        file_diagnostics = []
        
        # Get static analysis diagnostics
        if self.is_initialized:
            with self._lock:
                for lang, server in self.language_servers.items():
                    try:
                        if server.supports_file(file_path):
                            diagnostics = server.get_file_diagnostics(file_path)
                            # Convert to enhanced ErrorInfo if needed
                            for diag in diagnostics:
                                if not hasattr(diag, 'error_type'):
                                    # Convert basic ErrorInfo to enhanced version
                                    enhanced_diag = ErrorInfo(
                                        file_path=diag.file_path,
                                        line=diag.line,
                                        character=diag.character,
                                        message=diag.message,
                                        severity=diag.severity,
                                        source=diag.source,
                                        code=diag.code,
                                        end_line=diag.end_line,
                                        end_character=diag.end_character
                                    )
                                    if RUNTIME_COLLECTION_AVAILABLE:
                                        enhanced_diag.error_type = ErrorType.STATIC_ANALYSIS
                                    file_diagnostics.append(enhanced_diag)
                                else:
                                    file_diagnostics.append(diag)
                    except Exception as e:
                        logger.error(f"Error getting file diagnostics from {lang} server: {e}")
        
        # Add runtime errors for this file if requested
        if include_runtime:
            runtime_errors = self.get_runtime_errors_for_file(file_path)
            file_diagnostics.extend(runtime_errors)
        
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
        """Shutdown all language servers and clean up resources."""
        with self._lock:
            # Shutdown language servers
            for lang, server in self.language_servers.items():
                try:
                    server.shutdown()
                    logger.info(f"Shutdown {lang} language server")
                except Exception as e:
                    logger.error(f"Error shutting down {lang} server: {e}")
            
            # Shutdown runtime collector
            if self.runtime_collector:
                try:
                    self.runtime_collector.shutdown()
                    logger.info("Runtime error collector shutdown")
                except Exception as e:
                    logger.error(f"Error shutting down runtime collector: {e}")
            
            # Shutdown Serena components
            if self.solid_language_server:
                try:
                    # SolidLanguageServer shutdown if it has a shutdown method
                    if hasattr(self.solid_language_server, 'shutdown'):
                        self.solid_language_server.shutdown()
                    logger.info("SolidLanguageServer shutdown")
                except Exception as e:
                    logger.error(f"Error shutting down SolidLanguageServer: {e}")
            
            # Clear all resources
            self.language_servers.clear()
            self.diagnostics_cache.clear()
            self.runtime_collector = None
            self.serena_project = None
            self.serena_symbol_retriever = None
            self.solid_language_server = None
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
        """Get comprehensive status information about the LSP bridge."""
        server_status = {}
        for lang, server in self.language_servers.items():
            server_status[lang] = server.get_status()
        
        # Runtime collection status
        runtime_status = {
            'available': RUNTIME_COLLECTION_AVAILABLE,
            'enabled': self.enable_runtime_collection,
            'active': self.runtime_collector is not None,
            'summary': self.get_runtime_error_summary() if self.runtime_collector else {}
        }
        
        # Serena component status
        serena_status = {
            'solidlsp_available': SERENA_AVAILABLE,
            'serena_full_available': SERENA_FULL_AVAILABLE,
            'solid_language_server': self.solid_language_server is not None,
            'serena_project': self.serena_project is not None,
            'symbol_retriever': self.serena_symbol_retriever is not None
        }
        
        return {
            'initialized': self.is_initialized,
            'language_servers': list(self.language_servers.keys()),
            'repo_path': str(self.repo_path),
            'server_details': server_status,
            'runtime_collection': runtime_status,
            'serena_components': serena_status,
            'capabilities': {
                'static_analysis': self.is_initialized,
                'runtime_errors': self.runtime_collector is not None,
                'serena_integration': SERENA_AVAILABLE,
                'symbol_retrieval': self.serena_symbol_retriever is not None,
                'enhanced_diagnostics': True
            }
        }
