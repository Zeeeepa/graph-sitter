"""
Python Language Server Implementation

Provides Python-specific error detection using Pyright through Serena's solidlsp.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from graph_sitter.shared.logging.get_logger import get_logger
from .base import BaseLanguageServer
from ..serena_bridge import ErrorInfo, DiagnosticSeverity

logger = get_logger(__name__)

# Try to import Serena components
try:
    # Add serena to path if available
    serena_path = Path(__file__).parent.parent.parent.parent.parent.parent / "serena" / "src"
    if serena_path.exists():
        sys.path.insert(0, str(serena_path))
    
    from solidlsp.language_servers.pyright_server import PyrightServer
    from solidlsp.ls_config import LanguageServerConfig, Language
    from solidlsp.ls_logger import LanguageServerLogger
    SERENA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Serena solidlsp not available for Python server: {e}")
    SERENA_AVAILABLE = False
    # Mock classes
    class PyrightServer:
        pass
    class LanguageServerConfig:
        pass
    class Language:
        pass
    class LanguageServerLogger:
        pass


class PythonLanguageServer(BaseLanguageServer):
    """Python language server using Pyright through Serena."""
    
    def __init__(self, repo_path: str):
        super().__init__(repo_path)
        self._pyright_server: Optional[PyrightServer] = None
        self._config: Optional[LanguageServerConfig] = None
        self._logger: Optional[LanguageServerLogger] = None
    
    def initialize(self) -> bool:
        """Initialize the Pyright language server."""
        if not SERENA_AVAILABLE:
            logger.warning("Serena not available - Python language server disabled")
            return False
        
        try:
            # Create configuration
            self._config = LanguageServerConfig(
                language=Language.PYTHON,
                repository_root_path=str(self.repo_path),
                use_lsp_diagnostics=True
            )
            
            # Create logger
            self._logger = LanguageServerLogger()
            
            # Create Pyright server
            self._pyright_server = PyrightServer(
                config=self._config,
                logger=self._logger,
                repository_root_path=str(self.repo_path)
            )
            
            # Start the server
            if hasattr(self._pyright_server, 'start'):
                self._pyright_server.start()
            
            self.is_initialized = True
            logger.info(f"Python language server initialized for {self.repo_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Python language server: {e}")
            return False
    
    def get_diagnostics(self) -> List[ErrorInfo]:
        """Get all Python diagnostics from Pyright."""
        if not self.is_initialized or not self._pyright_server:
            return []
        
        diagnostics = []
        
        try:
            # Get workspace diagnostics
            if hasattr(self._pyright_server, 'get_workspace_diagnostics'):
                workspace_diags = self._pyright_server.get_workspace_diagnostics()
                diagnostics.extend(self._convert_diagnostics(workspace_diags))
            
            # Get diagnostics for Python files
            python_files = list(self.repo_path.rglob("*.py"))
            for py_file in python_files[:100]:  # Limit for performance
                try:
                    if self._is_valid_python_file(py_file):
                        file_diags = self.get_file_diagnostics(str(py_file))
                        diagnostics.extend(file_diags)
                except Exception as e:
                    logger.debug(f"Error getting diagnostics for {py_file}: {e}")
            
        except Exception as e:
            logger.error(f"Error getting Python diagnostics: {e}")
        
        return diagnostics
    
    def get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get diagnostics for a specific Python file."""
        if not self.is_initialized or not self._pyright_server:
            return []
        
        if not self.supports_file(file_path):
            return []
        
        try:
            # Use Serena's file diagnostic methods
            if hasattr(self._pyright_server, 'get_file_diagnostics'):
                file_diags = self._pyright_server.get_file_diagnostics(file_path)
                return self._convert_diagnostics(file_diags, file_path)
            
            # Fallback: try to get diagnostics through LSP requests
            if hasattr(self._pyright_server, 'request_diagnostics'):
                file_diags = self._pyright_server.request_diagnostics(file_path)
                return self._convert_diagnostics(file_diags, file_path)
            
        except Exception as e:
            logger.error(f"Error getting file diagnostics for {file_path}: {e}")
        
        return []
    
    def _convert_diagnostics(self, raw_diagnostics: Any, file_path: Optional[str] = None) -> List[ErrorInfo]:
        """Convert Pyright diagnostics to ErrorInfo objects."""
        converted = []
        
        if not raw_diagnostics:
            return converted
        
        try:
            # Handle different diagnostic formats
            if isinstance(raw_diagnostics, list):
                for diag in raw_diagnostics:
                    error_info = self._convert_single_diagnostic(diag, file_path)
                    if error_info:
                        converted.append(error_info)
            elif isinstance(raw_diagnostics, dict):
                # Handle workspace diagnostics format
                for uri, diag_list in raw_diagnostics.items():
                    if isinstance(diag_list, list):
                        for diag in diag_list:
                            error_info = self._convert_single_diagnostic(diag, uri)
                            if error_info:
                                converted.append(error_info)
        
        except Exception as e:
            logger.error(f"Error converting Python diagnostics: {e}")
        
        return converted
    
    def _convert_single_diagnostic(self, diagnostic: Any, file_path: Optional[str] = None) -> Optional[ErrorInfo]:
        """Convert a single Pyright diagnostic to ErrorInfo."""
        try:
            # Extract diagnostic information
            if hasattr(diagnostic, 'range') and hasattr(diagnostic, 'message'):
                # LSP Diagnostic format
                range_obj = diagnostic.range
                start_pos = range_obj.start if hasattr(range_obj, 'start') else range_obj
                
                line = getattr(start_pos, 'line', 0)
                character = getattr(start_pos, 'character', 0)
                message = getattr(diagnostic, 'message', 'Unknown Python error')
                severity = getattr(diagnostic, 'severity', DiagnosticSeverity.ERROR)
                source = getattr(diagnostic, 'source', 'pyright')
                code = getattr(diagnostic, 'code', None)
                
                # Get file path
                if hasattr(diagnostic, 'uri'):
                    file_path = diagnostic.uri
                elif hasattr(diagnostic, 'file_path'):
                    file_path = diagnostic.file_path
                
                if file_path:
                    # Convert URI to path if needed
                    if file_path.startswith('file://'):
                        file_path = file_path[7:]
                    
                    # Make relative to repo
                    try:
                        file_path = str(Path(file_path).relative_to(self.repo_path))
                    except ValueError:
                        # If not relative to repo, use as-is
                        pass
                    
                    return ErrorInfo(
                        file_path=file_path,
                        line=line,
                        character=character,
                        message=message,
                        severity=DiagnosticSeverity(severity) if isinstance(severity, int) else severity,
                        source=source,
                        code=code
                    )
            
        except Exception as e:
            logger.error(f"Error converting single Python diagnostic: {e}")
        
        return None
    
    def _is_valid_python_file(self, file_path: Path) -> bool:
        """Check if a Python file should be analyzed."""
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            return False
        
        # Skip common non-source directories
        skip_dirs = {'__pycache__', 'venv', '.venv', 'env', '.env', 'build', 'dist'}
        if any(part in skip_dirs for part in file_path.parts):
            return False
        
        # Must be a .py file
        if file_path.suffix != '.py':
            return False
        
        # Check if file exists and is readable
        try:
            return file_path.exists() and file_path.is_file()
        except (OSError, PermissionError):
            return False
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of Python diagnostic information."""
        if not self.is_initialized or not self._pyright_server:
            return
        
        try:
            if hasattr(self._pyright_server, 'refresh_diagnostics'):
                self._pyright_server.refresh_diagnostics()
            elif hasattr(self._pyright_server, 'restart'):
                self._pyright_server.restart()
        except Exception as e:
            logger.error(f"Error refreshing Python diagnostics: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the Pyright language server."""
        if self._pyright_server:
            try:
                if hasattr(self._pyright_server, 'shutdown'):
                    self._pyright_server.shutdown()
                elif hasattr(self._pyright_server, 'stop'):
                    self._pyright_server.stop()
                logger.info("Python language server shutdown")
            except Exception as e:
                logger.error(f"Error shutting down Python language server: {e}")
        
        self._pyright_server = None
        self._config = None
        self._logger = None
        self.is_initialized = False
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of file extensions supported by Python server."""
        return ['.py', '.pyi']
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about the Python language server."""
        status = super().get_status()
        status.update({
            'language': 'python',
            'server_type': 'pyright',
            'serena_available': SERENA_AVAILABLE
        })
        return status

