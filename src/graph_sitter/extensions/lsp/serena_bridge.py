"""
Enhanced Serena LSP Bridge for Graph-Sitter

This module provides a comprehensive bridge between Serena's solidlsp implementation
and graph-sitter's codebase analysis system, with runtime error collection,
advanced diagnostics, and comprehensive error analysis.
"""

import os
import sys
import threading
import time
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Callable
from enum import IntEnum
from collections import defaultdict

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.runtime_errors import RuntimeErrorCollector, RuntimeError, get_runtime_collector
from .protocol.lsp_types import DiagnosticSeverity, Diagnostic, Position, Range
from .language_servers.base import BaseLanguageServer
from .language_servers.python_server import PythonLanguageServer

# Try to import Serena components if available
try:
    from graph_sitter.extensions.serena.lsp_integration import SerenaLSPIntegration
    from graph_sitter.extensions.serena.types import SerenaConfig, SerenaCapability
    SERENA_AVAILABLE = True
except ImportError:
    SERENA_AVAILABLE = False

logger = get_logger(__name__)


# DiagnosticSeverity is now imported from protocol.lsp_types


@dataclass
class SerenaErrorInfo:
    """Enhanced error information for graph-sitter with Serena integration."""
    file_path: str
    line: int
    character: int
    message: str
    severity: DiagnosticSeverity
    source: Optional[str] = None
    code: Optional[Union[str, int]] = None
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    
    # Enhanced fields for Serena integration
    error_type: str = "static"  # static, runtime, serena
    context: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    related_symbols: List[str] = field(default_factory=list)
    fix_actions: List[Dict[str, Any]] = field(default_factory=list)
    
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
        return self.error_type == "runtime"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'file_path': self.file_path,
            'line': self.line,
            'character': self.character,
            'message': self.message,
            'severity': self.severity.name,
            'source': self.source,
            'code': self.code,
            'end_line': self.end_line,
            'end_character': self.end_character,
            'error_type': self.error_type,
            'context': self.context,
            'suggestions': self.suggestions,
            'related_symbols': self.related_symbols,
            'fix_actions': self.fix_actions
        }
    
    def __str__(self) -> str:
        severity_str = {
            DiagnosticSeverity.ERROR: "ERROR",
            DiagnosticSeverity.WARNING: "WARNING", 
            DiagnosticSeverity.INFORMATION: "INFO",
            DiagnosticSeverity.HINT: "HINT"
        }.get(self.severity, "UNKNOWN")
        
        type_indicator = f"[{self.error_type.upper()}]" if self.error_type != "static" else ""
        return f"{severity_str} {type_indicator} {self.file_path}:{self.line}:{self.character} - {self.message}"


# Keep backward compatibility
ErrorInfo = SerenaErrorInfo


class SerenaLSPBridge:
    """Enhanced bridge between Serena's LSP implementation and graph-sitter with runtime error collection."""
    
    def __init__(self, repo_path: str, enable_runtime_collection: bool = True, enable_serena_integration: bool = True):
        self.repo_path = Path(repo_path)
        self.language_servers: Dict[str, BaseLanguageServer] = {}
        self.diagnostics_cache: Dict[str, List[SerenaErrorInfo]] = {}
        self.is_initialized = False
        self._lock = threading.RLock()
        
        # Runtime error collection
        self.enable_runtime_collection = enable_runtime_collection
        self.runtime_collector: Optional[RuntimeErrorCollector] = None
        
        # Serena integration
        self.enable_serena_integration = enable_serena_integration and SERENA_AVAILABLE
        self.serena_integration: Optional[SerenaLSPIntegration] = None
        
        # Enhanced diagnostics
        self.error_handlers: List[Callable[[SerenaErrorInfo], None]] = []
        self.diagnostic_filters: Dict[str, Callable[[SerenaErrorInfo], bool]] = {}
        
        # Performance tracking
        self.performance_stats = {
            'diagnostics_retrieved': 0,
            'runtime_errors_collected': 0,
            'serena_analyses_performed': 0,
            'last_refresh_time': 0.0,
            'average_response_time': 0.0
        }
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all components: language servers, runtime collection, and Serena integration."""
        try:
            # Initialize language servers
            self._initialize_language_servers()
            
            # Initialize runtime error collection
            if self.enable_runtime_collection:
                self._initialize_runtime_collection()
            
            # Initialize Serena integration
            if self.enable_serena_integration:
                self._initialize_serena_integration()
            
            self.is_initialized = (
                len(self.language_servers) > 0 or 
                self.runtime_collector is not None or 
                self.serena_integration is not None
            )
            
            logger.info(f"Enhanced LSP bridge initialized for {self.repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced LSP bridge: {e}")
    
    def _initialize_runtime_collection(self) -> None:
        """Initialize runtime error collection."""
        try:
            self.runtime_collector = get_runtime_collector(str(self.repo_path))
            
            # Add handler to integrate runtime errors with diagnostics
            def runtime_error_handler(runtime_error: RuntimeError):
                """Convert runtime error to SerenaErrorInfo and add to diagnostics."""
                try:
                    severity_map = {
                        "critical": DiagnosticSeverity.ERROR,
                        "error": DiagnosticSeverity.ERROR,
                        "warning": DiagnosticSeverity.WARNING,
                        "info": DiagnosticSeverity.INFORMATION,
                        "hint": DiagnosticSeverity.HINT
                    }
                    
                    error_info = SerenaErrorInfo(
                        file_path=runtime_error.file_path,
                        line=runtime_error.line,
                        character=runtime_error.character,
                        message=runtime_error.message,
                        severity=severity_map.get(runtime_error.severity, DiagnosticSeverity.ERROR),
                        source="runtime_collector",
                        error_type="runtime",
                        context=runtime_error.context.to_dict(),
                        suggestions=self._generate_runtime_error_suggestions(runtime_error)
                    )
                    
                    self._add_runtime_diagnostic(error_info)
                    self.performance_stats['runtime_errors_collected'] += 1
                    
                except Exception as e:
                    logger.error(f"Error handling runtime error: {e}")
            
            self.runtime_collector.add_error_handler(runtime_error_handler)
            logger.info("Runtime error collection initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize runtime error collection: {e}")
            self.enable_runtime_collection = False
    
    def _initialize_serena_integration(self) -> None:
        """Initialize Serena LSP integration."""
        try:
            if SERENA_AVAILABLE:
                config = SerenaConfig(
                    repo_path=str(self.repo_path),
                    capabilities=[
                        SerenaCapability.DIAGNOSTICS,
                        SerenaCapability.COMPLETIONS,
                        SerenaCapability.HOVER,
                        SerenaCapability.SYMBOLS,
                        SerenaCapability.REFACTORING
                    ]
                )
                
                self.serena_integration = SerenaLSPIntegration(config)
                logger.info("Serena LSP integration initialized")
            else:
                logger.warning("Serena components not available")
                
        except Exception as e:
            logger.error(f"Failed to initialize Serena integration: {e}")
            self.enable_serena_integration = False
    
    def _generate_runtime_error_suggestions(self, runtime_error: RuntimeError) -> List[str]:
        """Generate suggestions for runtime errors."""
        suggestions = []
        
        exception_type = runtime_error.context.exception_type
        message = runtime_error.message.lower()
        
        # Common suggestions based on exception type
        if exception_type == "NameError":
            suggestions.extend([
                "Check if the variable is defined before use",
                "Verify import statements",
                "Check for typos in variable names"
            ])
        elif exception_type == "AttributeError":
            suggestions.extend([
                "Verify the object has the expected attribute",
                "Check if the object is None",
                "Ensure proper initialization"
            ])
        elif exception_type == "TypeError":
            suggestions.extend([
                "Check argument types",
                "Verify function signature",
                "Ensure proper type conversion"
            ])
        elif exception_type == "IndexError":
            suggestions.extend([
                "Check list/array bounds",
                "Verify index is within range",
                "Add bounds checking"
            ])
        elif exception_type == "KeyError":
            suggestions.extend([
                "Check if key exists in dictionary",
                "Use dict.get() with default value",
                "Verify key spelling"
            ])
        
        # Context-specific suggestions
        if "division by zero" in message:
            suggestions.append("Add check for zero before division")
        elif "none" in message:
            suggestions.append("Add None check before accessing attributes")
        
        return suggestions
    
    def _add_runtime_diagnostic(self, error_info: SerenaErrorInfo) -> None:
        """Add runtime diagnostic to cache."""
        with self._lock:
            if error_info.file_path not in self.diagnostics_cache:
                self.diagnostics_cache[error_info.file_path] = []
            
            self.diagnostics_cache[error_info.file_path].append(error_info)
            
            # Notify error handlers
            for handler in self.error_handlers:
                try:
                    handler(error_info)
                except Exception as e:
                    logger.error(f"Error in error handler: {e}")
    
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
    
    def get_diagnostics(self, include_runtime: bool = True, include_serena: bool = True) -> List[SerenaErrorInfo]:
        """Get all diagnostics from all sources: language servers, runtime errors, and Serena analysis."""
        if not self.is_initialized:
            return []
        
        start_time = time.time()
        all_diagnostics = []
        
        with self._lock:
            # Get static analysis diagnostics from language servers
            for lang, server in self.language_servers.items():
                try:
                    diagnostics = server.get_diagnostics()
                    # Convert to SerenaErrorInfo format
                    for diag in diagnostics:
                        if isinstance(diag, SerenaErrorInfo):
                            all_diagnostics.append(diag)
                        else:
                            # Convert legacy ErrorInfo to SerenaErrorInfo
                            enhanced_diag = SerenaErrorInfo(
                                file_path=diag.file_path,
                                line=diag.line,
                                character=diag.character,
                                message=diag.message,
                                severity=diag.severity,
                                source=diag.source,
                                code=diag.code,
                                end_line=diag.end_line,
                                end_character=diag.end_character,
                                error_type="static"
                            )
                            all_diagnostics.append(enhanced_diag)
                except Exception as e:
                    logger.error(f"Error getting diagnostics from {lang} server: {e}")
            
            # Add runtime errors if requested
            if include_runtime and self.runtime_collector:
                try:
                    # Get runtime errors from collector
                    runtime_errors = self.runtime_collector.get_runtime_errors()
                    for runtime_error in runtime_errors:
                        severity_map = {
                            "critical": DiagnosticSeverity.ERROR,
                            "error": DiagnosticSeverity.ERROR,
                            "warning": DiagnosticSeverity.WARNING,
                            "info": DiagnosticSeverity.INFORMATION,
                            "hint": DiagnosticSeverity.HINT
                        }
                        
                        error_info = SerenaErrorInfo(
                            file_path=runtime_error.file_path,
                            line=runtime_error.line,
                            character=runtime_error.character,
                            message=runtime_error.message,
                            severity=severity_map.get(runtime_error.severity, DiagnosticSeverity.ERROR),
                            source="runtime_collector",
                            error_type="runtime",
                            context=runtime_error.context.to_dict(),
                            suggestions=self._generate_runtime_error_suggestions(runtime_error)
                        )
                        all_diagnostics.append(error_info)
                        
                except Exception as e:
                    logger.error(f"Error getting runtime diagnostics: {e}")
            
            # Add Serena diagnostics if requested and available
            if include_serena and self.serena_integration:
                try:
                    serena_diagnostics = self.serena_integration.get_comprehensive_diagnostics()
                    for diag in serena_diagnostics:
                        # Convert Serena diagnostic to SerenaErrorInfo
                        error_info = SerenaErrorInfo(
                            file_path=diag.get('file_path', ''),
                            line=diag.get('line', 1),
                            character=diag.get('character', 0),
                            message=diag.get('message', ''),
                            severity=DiagnosticSeverity[diag.get('severity', 'ERROR')],
                            source="serena",
                            error_type="serena",
                            context=diag.get('context', {}),
                            suggestions=diag.get('suggestions', []),
                            related_symbols=diag.get('related_symbols', []),
                            fix_actions=diag.get('fix_actions', [])
                        )
                        all_diagnostics.append(error_info)
                        
                    self.performance_stats['serena_analyses_performed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error getting Serena diagnostics: {e}")
            
            # Add cached diagnostics
            for file_diagnostics in self.diagnostics_cache.values():
                all_diagnostics.extend(file_diagnostics)
        
        # Apply diagnostic filters
        filtered_diagnostics = []
        for diagnostic in all_diagnostics:
            include_diagnostic = True
            for filter_name, filter_func in self.diagnostic_filters.items():
                try:
                    if not filter_func(diagnostic):
                        include_diagnostic = False
                        break
                except Exception as e:
                    logger.error(f"Error in diagnostic filter {filter_name}: {e}")
            
            if include_diagnostic:
                filtered_diagnostics.append(diagnostic)
        
        # Update performance stats
        analysis_time = time.time() - start_time
        self.performance_stats['diagnostics_retrieved'] += 1
        self.performance_stats['last_refresh_time'] = time.time()
        
        # Update average response time
        if self.performance_stats['average_response_time'] == 0:
            self.performance_stats['average_response_time'] = analysis_time
        else:
            self.performance_stats['average_response_time'] = (
                self.performance_stats['average_response_time'] * 0.8 + analysis_time * 0.2
            )
        
        return filtered_diagnostics
    


    
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
    
    def start_runtime_collection(self) -> bool:
        """Start runtime error collection."""
        if self.runtime_collector:
            try:
                self.runtime_collector.start_collection()
                return True
            except Exception as e:
                logger.error(f"Failed to start runtime collection: {e}")
                return False
        return False
    
    def stop_runtime_collection(self) -> bool:
        """Stop runtime error collection."""
        if self.runtime_collector:
            try:
                self.runtime_collector.stop_collection()
                return True
            except Exception as e:
                logger.error(f"Failed to stop runtime collection: {e}")
                return False
        return False
    
    def get_runtime_errors(self) -> List[RuntimeError]:
        """Get all runtime errors."""
        if self.runtime_collector:
            return self.runtime_collector.get_runtime_errors()
        return []
    
    def get_runtime_error_summary(self) -> Dict[str, Any]:
        """Get runtime error summary."""
        if self.runtime_collector:
            return self.runtime_collector.get_error_summary()
        return {'runtime_collection_enabled': False}
    
    def add_diagnostic_filter(self, name: str, filter_func: Callable[[SerenaErrorInfo], bool]) -> None:
        """Add a diagnostic filter."""
        self.diagnostic_filters[name] = filter_func
    
    def remove_diagnostic_filter(self, name: str) -> None:
        """Remove a diagnostic filter."""
        self.diagnostic_filters.pop(name, None)
    
    def add_error_handler(self, handler: Callable[[SerenaErrorInfo], None]) -> None:
        """Add an error handler."""
        self.error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable[[SerenaErrorInfo], None]) -> None:
        """Remove an error handler."""
        if handler in self.error_handlers:
            self.error_handlers.remove(handler)
    
    def get_enhanced_diagnostics(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Get enhanced diagnostics with comprehensive analysis."""
        diagnostics = self.get_diagnostics()
        
        if file_path:
            diagnostics = [d for d in diagnostics if d.file_path == file_path]
        
        # Group by type and severity
        by_type = defaultdict(list)
        by_severity = defaultdict(list)
        by_source = defaultdict(list)
        
        for diag in diagnostics:
            by_type[diag.error_type].append(diag)
            by_severity[diag.severity.name].append(diag)
            by_source[diag.source or 'unknown'].append(diag)
        
        return {
            'total_count': len(diagnostics),
            'by_type': {k: len(v) for k, v in by_type.items()},
            'by_severity': {k: len(v) for k, v in by_severity.items()},
            'by_source': {k: len(v) for k, v in by_source.items()},
            'diagnostics': [d.to_dict() for d in diagnostics],
            'performance_stats': self.performance_stats.copy()
        }
    
    async def get_comprehensive_analysis(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive analysis including Serena insights."""
        analysis = {
            'diagnostics': self.get_enhanced_diagnostics(file_path),
            'runtime_errors': self.get_runtime_error_summary(),
            'performance_stats': self.performance_stats.copy()
        }
        
        # Add Serena analysis if available
        if self.serena_integration:
            try:
                if file_path:
                    serena_analysis = await self.serena_integration.analyze_file(file_path)
                else:
                    serena_analysis = await self.serena_integration.analyze_codebase()
                
                analysis['serena_analysis'] = serena_analysis
                
            except Exception as e:
                logger.error(f"Error getting Serena analysis: {e}")
                analysis['serena_analysis'] = {'error': str(e)}
        
        return analysis
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information about the enhanced LSP bridge."""
        server_status = {}
        for lang, server in self.language_servers.items():
            server_status[lang] = server.get_status()
        
        # Get runtime collection status
        runtime_status = {}
        if self.runtime_collector:
            runtime_status = self.runtime_collector.get_error_summary()
        
        # Get Serena integration status
        serena_status = {
            'available': SERENA_AVAILABLE,
            'enabled': self.enable_serena_integration,
            'initialized': self.serena_integration is not None
        }
        
        if self.serena_integration:
            try:
                serena_status.update(self.serena_integration.get_status())
            except Exception as e:
                serena_status['error'] = str(e)
        
        return {
            'initialized': self.is_initialized,
            'language_servers': list(self.language_servers.keys()),
            'repo_path': str(self.repo_path),
            'server_details': server_status,
            'runtime_collection': {
                'enabled': self.enable_runtime_collection,
                'status': runtime_status
            },
            'serena_integration': serena_status,
            'performance_stats': self.performance_stats.copy(),
            'diagnostic_filters': list(self.diagnostic_filters.keys()),
            'error_handlers': len(self.error_handlers)
        }


# Convenience functions for easy integration
def create_serena_bridge(repo_path: str, **kwargs) -> SerenaLSPBridge:
    """Create and return a Serena LSP bridge for a repository."""
    return SerenaLSPBridge(repo_path, **kwargs)


def get_enhanced_diagnostics(repo_path: str, file_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Get enhanced diagnostics for a repository."""
    bridge = SerenaLSPBridge(repo_path, **kwargs)
    try:
        return bridge.get_enhanced_diagnostics(file_path)
    finally:
        bridge.shutdown()


async def get_comprehensive_analysis(repo_path: str, file_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Get comprehensive analysis for a repository."""
    bridge = SerenaLSPBridge(repo_path, **kwargs)
    try:
        return await bridge.get_comprehensive_analysis(file_path)
    finally:
        bridge.shutdown()


def start_runtime_error_collection(repo_path: str) -> RuntimeErrorCollector:
    """Start runtime error collection for a repository."""
    from graph_sitter.core.runtime_errors import start_runtime_collection
    return start_runtime_collection(repo_path)


def stop_runtime_error_collection(repo_path: str) -> None:
    """Stop runtime error collection for a repository."""
    from graph_sitter.core.runtime_errors import stop_runtime_collection
    stop_runtime_collection(repo_path)
