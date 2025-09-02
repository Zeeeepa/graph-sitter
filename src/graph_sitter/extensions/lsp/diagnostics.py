"""
LSP Diagnostics Module

This module provides diagnostics capabilities for the LSP integration,
connecting with SolidLSP to retrieve comprehensive diagnostics about the codebase.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Union

from lsprotocol import types

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.extensions.lsp.solidlsp.ls_config import Language, LanguageServerConfig
from graph_sitter.extensions.lsp.solidlsp.ls_logger import LanguageServerLogger
from graph_sitter.extensions.lsp.solidlsp.ls import SolidLanguageServer
from graph_sitter.extensions.lsp.solidlsp.settings import SolidLSPSettings

logger = get_logger(__name__)


class DiagnosticsManager:
    """
    Manages diagnostics from both normal LSP and SolidLSP.
    
    This class provides a unified interface for accessing diagnostics from both
    the normal LSP integration and SolidLSP's advanced diagnostics capabilities.
    It handles the conversion between different diagnostic formats and provides
    methods for filtering and querying diagnostics.
    """
    
    def __init__(self, codebase_path: str):
        """
        Initialize the diagnostics manager.
        
        Args:
            codebase_path: Path to the codebase
        """
        self.codebase_path = Path(codebase_path)
        self._lsp_diagnostics: Dict[str, List[types.Diagnostic]] = {}
        self._solidlsp_servers: Dict[str, SolidLanguageServer] = {}
        self._diagnostic_listeners: List[Callable[[str, List[types.Diagnostic]], None]] = []
        self._initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the diagnostics manager with SolidLSP components.
        
        Returns:
            True if initialization was successful
        """
        try:
            # Initialize SolidLSP settings
            solidlsp_settings = SolidLSPSettings()
            
            # Create language server configurations for common languages
            configs = self._create_language_server_configs()
            
            # Initialize language servers
            for lang, config in configs.items():
                try:
                    logger_instance = LanguageServerLogger(f"solidlsp_{lang}")
                    server = SolidLanguageServer.create(
                        config=config,
                        logger=logger_instance,
                        repository_root_path=str(self.codebase_path),
                        solidlsp_settings=solidlsp_settings
                    )
                    
                    # Start the server
                    server.start()
                    
                    # Store the server
                    self._solidlsp_servers[lang] = server
                    logger.info(f"Initialized SolidLSP server for {lang}")
                except Exception as e:
                    logger.error(f"Failed to initialize SolidLSP server for {lang}: {e}")
            
            self._initialized = True
            logger.info(f"Diagnostics manager initialized with {len(self._solidlsp_servers)} SolidLSP servers")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize diagnostics manager: {e}")
            return False
    
    def add_lsp_diagnostics(self, uri: str, diagnostics: List[types.Diagnostic]) -> None:
        """
        Add diagnostics from the normal LSP integration.
        
        Args:
            uri: Document URI
            diagnostics: List of LSP diagnostics
        """
        self._lsp_diagnostics[uri] = diagnostics
        
        # Notify listeners
        for listener in self._diagnostic_listeners:
            try:
                listener(uri, diagnostics)
            except Exception as e:
                logger.error(f"Error in diagnostic listener: {e}")
    
    def get_diagnostics(self, uri: Optional[str] = None) -> Dict[str, List[types.Diagnostic]]:
        """
        Get diagnostics for a specific URI or all URIs.
        
        Args:
            uri: Document URI (None for all URIs)
            
        Returns:
            Dictionary mapping URIs to diagnostics
        """
        if uri:
            return {uri: self._lsp_diagnostics.get(uri, [])}
        return self._lsp_diagnostics
    
    async def get_all_diagnostics(self, 
                                include_solidlsp: bool = True,
                                severity_filter: Optional[List[int]] = None) -> Dict[str, List[types.Diagnostic]]:
        """
        Get all diagnostics from both normal LSP and SolidLSP.
        
        Args:
            include_solidlsp: Whether to include SolidLSP diagnostics
            severity_filter: Optional list of severity levels to include
            
        Returns:
            Dictionary mapping URIs to diagnostics
        """
        result = dict(self._lsp_diagnostics)
        
        if include_solidlsp and self._initialized and self._solidlsp_servers:
            # Get diagnostics from SolidLSP servers
            for lang, server in self._solidlsp_servers.items():
                try:
                    # Get diagnostics from the server
                    diagnostics = await self._get_server_diagnostics(server)
                    
                    # Filter by severity if needed
                    if severity_filter:
                        diagnostics = {
                            uri: [d for d in diags if d.severity in severity_filter]
                            for uri, diags in diagnostics.items()
                        }
                    
                    # Merge with result
                    for uri, diags in diagnostics.items():
                        if uri not in result:
                            result[uri] = []
                        result[uri].extend(diags)
                except Exception as e:
                    logger.error(f"Error getting diagnostics from SolidLSP server for {lang}: {e}")
        
        return result
    
    async def analyze_file(self, file_path: str) -> List[types.Diagnostic]:
        """
        Analyze a specific file for errors using SolidLSP.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of diagnostics for the file
        """
        if not self._initialized or not self._solidlsp_servers:
            return []
        
        all_diagnostics = []
        
        # Determine the language based on file extension
        file_ext = Path(file_path).suffix.lower()
        lang = self._get_language_for_extension(file_ext)
        
        if lang and lang in self._solidlsp_servers:
            server = self._solidlsp_servers[lang]
            try:
                # Get diagnostics for the file
                rel_path = os.path.relpath(file_path, self.codebase_path)
                diagnostics = await self._get_file_diagnostics(server, rel_path)
                all_diagnostics.extend(diagnostics)
            except Exception as e:
                logger.error(f"Error analyzing file {file_path} with SolidLSP server for {lang}: {e}")
        
        return all_diagnostics
    
    async def analyze_codebase(self, 
                             root_path: Optional[str] = None,
                             file_patterns: Optional[List[str]] = None,
                             exclude_patterns: Optional[List[str]] = None) -> Dict[str, List[types.Diagnostic]]:
        """
        Analyze the entire codebase for errors using SolidLSP.
        
        Args:
            root_path: Root directory path (None for codebase_path)
            file_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            Dictionary mapping URIs to diagnostics
        """
        if not self._initialized or not self._solidlsp_servers:
            return {}
        
        result: Dict[str, List[types.Diagnostic]] = {}
        
        # Use all servers to analyze the codebase
        for lang, server in self._solidlsp_servers.items():
            try:
                # Get diagnostics from the server
                diagnostics = await self._get_server_diagnostics(server, file_patterns, exclude_patterns)
                
                # Merge with result
                for uri, diags in diagnostics.items():
                    if uri not in result:
                        result[uri] = []
                    result[uri].extend(diags)
            except Exception as e:
                logger.error(f"Error analyzing codebase with SolidLSP server for {lang}: {e}")
        
        return result
    
    def add_diagnostic_listener(self, listener: Callable[[str, List[types.Diagnostic]], None]) -> None:
        """
        Add a listener for diagnostic updates.
        
        Args:
            listener: Function to call when diagnostics are updated
        """
        self._diagnostic_listeners.append(listener)
    
    def remove_diagnostic_listener(self, listener: Callable[[str, List[types.Diagnostic]], None]) -> None:
        """
        Remove a diagnostic listener.
        
        Args:
            listener: Listener to remove
        """
        if listener in self._diagnostic_listeners:
            self._diagnostic_listeners.remove(listener)
    
    def get_diagnostic_stats(self) -> Dict[str, Any]:
        """
        Get diagnostic statistics.
        
        Returns:
            Dictionary with diagnostic statistics
        """
        # Basic stats from normal LSP
        total_errors = sum(len(diags) for diags in self._lsp_diagnostics.values())
        files_with_errors = len(self._lsp_diagnostics)
        
        # Count by severity
        error_count = 0
        warning_count = 0
        info_count = 0
        hint_count = 0
        
        for diags in self._lsp_diagnostics.values():
            for diag in diags:
                if diag.severity == types.DiagnosticSeverity.Error:
                    error_count += 1
                elif diag.severity == types.DiagnosticSeverity.Warning:
                    warning_count += 1
                elif diag.severity == types.DiagnosticSeverity.Information:
                    info_count += 1
                elif diag.severity == types.DiagnosticSeverity.Hint:
                    hint_count += 1
        
        return {
            "total_errors": total_errors,
            "files_with_errors": files_with_errors,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "hint_count": hint_count,
            "source": "lsp+solidlsp"
        }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        # Stop all SolidLSP servers
        for lang, server in self._solidlsp_servers.items():
            try:
                server.stop()
                logger.info(f"Stopped SolidLSP server for {lang}")
            except Exception as e:
                logger.error(f"Error stopping SolidLSP server for {lang}: {e}")
        
        self._solidlsp_servers.clear()
        self._lsp_diagnostics.clear()
        self._diagnostic_listeners.clear()
    
    def _create_language_server_configs(self) -> Dict[str, LanguageServerConfig]:
        """
        Create language server configurations for common languages.
        
        Returns:
            Dictionary mapping language IDs to configurations
        """
        configs = {}
        
        # Python configuration
        configs["python"] = LanguageServerConfig(
            code_language=Language.PYTHON,
            language_id="python",
            file_extensions=[".py"],
            workspace_folders=[str(self.codebase_path)]
        )
        
        # TypeScript configuration
        configs["typescript"] = LanguageServerConfig(
            code_language=Language.TYPESCRIPT,
            language_id="typescript",
            file_extensions=[".ts", ".tsx", ".js", ".jsx"],
            workspace_folders=[str(self.codebase_path)]
        )
        
        # Add more language configurations as needed
        
        return configs
    
    async def _get_server_diagnostics(self, 
                                    server: SolidLanguageServer,
                                    file_patterns: Optional[List[str]] = None,
                                    exclude_patterns: Optional[List[str]] = None) -> Dict[str, List[types.Diagnostic]]:
        """
        Get diagnostics from a SolidLSP server.
        
        Args:
            server: SolidLSP server
            file_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            Dictionary mapping URIs to diagnostics
        """
        result: Dict[str, List[types.Diagnostic]] = {}
        
        # Get all document symbols from the server
        try:
            # This is a workaround to get diagnostics from SolidLSP
            # SolidLSP doesn't have a direct API for getting all diagnostics,
            # but we can get them by requesting document symbols for all files
            symbols_by_file = server._document_symbols_cache
            
            for file_path, symbols in symbols_by_file.items():
                # Check if file matches patterns
                if file_patterns and not any(file_path.endswith(pattern) for pattern in file_patterns):
                    continue
                if exclude_patterns and any(file_path.endswith(pattern) for pattern in exclude_patterns):
                    continue
                
                # Get diagnostics for the file
                diagnostics = await self._get_file_diagnostics(server, file_path)
                
                # Add to result
                uri = Path(os.path.join(self.codebase_path, file_path)).as_uri()
                result[uri] = diagnostics
        except Exception as e:
            logger.error(f"Error getting diagnostics from SolidLSP server: {e}")
        
        return result
    
    async def _get_file_diagnostics(self, server: SolidLanguageServer, file_path: str) -> List[types.Diagnostic]:
        """
        Get diagnostics for a specific file from a SolidLSP server.
        
        Args:
            server: SolidLSP server
            file_path: Path to the file
            
        Returns:
            List of diagnostics for the file
        """
        diagnostics = []
        
        try:
            # Open the file in the server if not already open
            if file_path not in server._open_files:
                with open(os.path.join(self.codebase_path, file_path), "r") as f:
                    content = f.read()
                
                server.did_open(file_path, content)
            
            # Get diagnostics from the server's diagnostics cache
            if hasattr(server, "_diagnostics_by_file") and file_path in server._diagnostics_by_file:
                solidlsp_diagnostics = server._diagnostics_by_file[file_path]
                
                # Convert SolidLSP diagnostics to LSP diagnostics
                for diag in solidlsp_diagnostics:
                    lsp_diag = self._convert_solidlsp_to_lsp_diagnostic(diag)
                    diagnostics.append(lsp_diag)
        except Exception as e:
            logger.error(f"Error getting diagnostics for file {file_path}: {e}")
        
        return diagnostics
    
    def _convert_solidlsp_to_lsp_diagnostic(self, solidlsp_diag: Dict[str, Any]) -> types.Diagnostic:
        """
        Convert SolidLSP diagnostic to LSP diagnostic.
        
        Args:
            solidlsp_diag: SolidLSP diagnostic
            
        Returns:
            LSP diagnostic
        """
        # Map SolidLSP severity to LSP severity
        severity_map = {
            1: types.DiagnosticSeverity.Error,
            2: types.DiagnosticSeverity.Warning,
            3: types.DiagnosticSeverity.Information,
            4: types.DiagnosticSeverity.Hint
        }
        
        # Get severity
        severity = severity_map.get(
            solidlsp_diag.get("severity", 1),
            types.DiagnosticSeverity.Error
        )
        
        # Get range
        range_data = solidlsp_diag.get("range", {})
        start = range_data.get("start", {})
        end = range_data.get("end", {})
        
        # Create diagnostic
        return types.Diagnostic(
            range=types.Range(
                start=types.Position(
                    line=start.get("line", 0),
                    character=start.get("character", 0)
                ),
                end=types.Position(
                    line=end.get("line", 0),
                    character=end.get("character", 0)
                )
            ),
            severity=severity,
            code=solidlsp_diag.get("code"),
            source=solidlsp_diag.get("source", "solidlsp"),
            message=solidlsp_diag.get("message", "Unknown error"),
            tags=[],
            related_information=[]
        )
    
    def _get_language_for_extension(self, extension: str) -> Optional[str]:
        """
        Get language ID for a file extension.
        
        Args:
            extension: File extension
            
        Returns:
            Language ID or None if not found
        """
        extension_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "typescript",
            ".jsx": "typescript",
            # Add more mappings as needed
        }
        
        return extension_map.get(extension)

