"""
Base Language Server Implementation

Provides common functionality for all language server integrations.
"""

import abc
from pathlib import Path
from typing import List, Optional, Dict, Any

from graph_sitter.shared.logging.get_logger import get_logger
from ..serena_bridge import ErrorInfo

logger = get_logger(__name__)


class BaseLanguageServer(abc.ABC):
    """Base class for language server implementations."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.is_initialized = False
        self._server = None
    
    @abc.abstractmethod
    def initialize(self) -> bool:
        """Initialize the language server. Returns True if successful."""
        pass
    
    @abc.abstractmethod
    def get_diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics from the language server."""
        pass
    
    @abc.abstractmethod
    def get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get diagnostics for a specific file."""
        pass
    
    @abc.abstractmethod
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        pass
    
    @abc.abstractmethod
    def shutdown(self) -> None:
        """Shutdown the language server."""
        pass
    
    @abc.abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get list of file extensions supported by this server."""
        pass
    
    def supports_file(self, file_path: str) -> bool:
        """Check if this server supports the given file."""
        file_ext = Path(file_path).suffix
        return file_ext in self.get_supported_extensions()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about the language server."""
        return {
            'initialized': self.is_initialized,
            'repo_path': str(self.repo_path),
            'supported_extensions': self.get_supported_extensions()
        }

