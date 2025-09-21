#!/usr/bin/env python3
"""
LSP Diagnostics Integration

Integrates Language Server Protocol diagnostics into the analysis system.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from ..database import AnalysisError

try:
    from ...lsp.solidlsp.client import LSPClient
    from ...lsp.solidlsp.types import Diagnostic, DiagnosticSeverity
    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False
    LSPClient = None
    Diagnostic = None
    DiagnosticSeverity = None


class LSPDiagnosticsRunner:
    """Runner for LSP-based diagnostics."""
    
    def __init__(self):
        self.lsp_available = LSP_AVAILABLE
        self.active_clients: Dict[str, Any] = {}
    
    async def run_lsp_analysis(self, file_path: str, language: str = "python") -> List[AnalysisError]:
        """Run LSP diagnostics on a file."""
        if not self.lsp_available:
            logging.warning("LSP integration not available - skipping LSP diagnostics")
            return []
        
        try:
            # Get or create LSP client for this language
            client = await self._get_lsp_client(language)
            if not client:
                return []
            
            # Open document and get diagnostics
            diagnostics = await self._get_diagnostics(client, file_path)
            
            # Convert diagnostics to AnalysisError format
            errors = []
            for diagnostic in diagnostics:
                errors.append(self._convert_diagnostic_to_error(diagnostic, file_path))
            
            return errors
            
        except Exception as e:
            logging.error(f"LSP analysis failed for {file_path}: {e}")
            return []
    
    async def _get_lsp_client(self, language: str) -> Optional[Any]:
        """Get or create an LSP client for the given language."""
        if not self.lsp_available:
            return None
        
        if language in self.active_clients:
            return self.active_clients[language]
        
        # Create new client based on language
        try:
            if language == "python":
                client = await self._create_python_lsp_client()
            else:
                logging.warning(f"LSP client for {language} not implemented")
                return None
            
            if client:
                self.active_clients[language] = client
            return client
            
        except Exception as e:
            logging.error(f"Failed to create LSP client for {language}: {e}")
            return None
    
    async def _create_python_lsp_client(self) -> Optional[Any]:
        """Create Python LSP client (pylsp, pyright, etc.)."""
        if not LSPClient:
            return None
        
        try:
            # Try to create pylsp client first
            client = LSPClient()
            await client.start("pylsp")  # Python LSP Server
            return client
        except Exception:
            try:
                # Fallback to pyright
                client = LSPClient()
                await client.start("pyright-langserver", ["--stdio"])
                return client
            except Exception as e:
                logging.error(f"Failed to start Python LSP server: {e}")
                return None
    
    async def _get_diagnostics(self, client: Any, file_path: str) -> List[Any]:
        """Get diagnostics from LSP client."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Open document in LSP
            uri = Path(file_path).as_uri()
            await client.did_open(uri, content, language_id="python")
            
            # Wait for diagnostics (LSP servers usually send diagnostics automatically)
            await asyncio.sleep(1.0)  # Give LSP time to analyze
            
            # Get diagnostics
            diagnostics = await client.get_diagnostics(uri)
            return diagnostics or []
            
        except Exception as e:
            logging.error(f"Failed to get LSP diagnostics: {e}")
            return []
    
    def _convert_diagnostic_to_error(self, diagnostic: Any, file_path: str) -> AnalysisError:
        """Convert LSP diagnostic to AnalysisError."""
        # Handle case where LSP types are not available
        if not Diagnostic or not hasattr(diagnostic, 'range'):
            return AnalysisError(
                file_path=file_path,
                line=0,
                column=0,
                error_type="lsp-error",
                severity="INFO",
                message=str(diagnostic),
                tool_source="lsp",
                category="general",
                confidence=0.8
            )
        
        # Convert LSP severity to our severity
        severity_map = {
            1: "ERROR",    # DiagnosticSeverity.Error
            2: "WARNING",  # DiagnosticSeverity.Warning
            3: "INFO",     # DiagnosticSeverity.Information
            4: "HINT",     # DiagnosticSeverity.Hint
        }
        
        severity = "INFO"
        if hasattr(diagnostic, 'severity') and diagnostic.severity:
            severity = severity_map.get(diagnostic.severity, "INFO")
        
        # Extract position information
        line = 0
        column = 0
        if hasattr(diagnostic, 'range') and diagnostic.range:
            if hasattr(diagnostic.range, 'start'):
                line = getattr(diagnostic.range.start, 'line', 0) + 1  # LSP is 0-indexed
                column = getattr(diagnostic.range.start, 'character', 0) + 1
        
        # Determine error category based on source
        category = "general"
        if hasattr(diagnostic, 'source') and diagnostic.source:
            source = diagnostic.source.lower()
            if "type" in source or "mypy" in source:
                category = "type_checking"
            elif "lint" in source or "flake8" in source or "pylint" in source:
                category = "code_quality"
            elif "format" in source or "black" in source:
                category = "style_formatting"
            elif "import" in source:
                category = "imports"
        
        return AnalysisError(
            file_path=file_path,
            line=line,
            column=column,
            error_type=f"lsp-{getattr(diagnostic, 'source', 'unknown')}",
            severity=severity,
            message=getattr(diagnostic, 'message', 'LSP diagnostic'),
            tool_source=f"lsp-{getattr(diagnostic, 'source', 'unknown')}",
            category=category,
            confidence=0.8
        )
    
    async def cleanup(self):
        """Clean up LSP clients."""
        for language, client in self.active_clients.items():
            try:
                if hasattr(client, 'shutdown'):
                    await client.shutdown()
                if hasattr(client, 'exit'):
                    await client.exit()
            except Exception as e:
                logging.error(f"Failed to cleanup LSP client for {language}: {e}")
        
        self.active_clients.clear()


def run_lsp_diagnostics_sync(file_path: str, language: str = "python") -> List[AnalysisError]:
    """Synchronous wrapper for LSP diagnostics."""
    runner = LSPDiagnosticsRunner()
    
    try:
        # Run async LSP analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            errors = loop.run_until_complete(runner.run_lsp_analysis(file_path, language))
            loop.run_until_complete(runner.cleanup())
            return errors
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"LSP diagnostics sync wrapper failed: {e}")
        return []