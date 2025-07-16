"""
Pink SDK Type Bridge

This module provides type conversion between Pink SDK (Rust) types and 
graph-sitter (Python) types to ensure compatibility and proper type handling.
"""

from pathlib import Path
from typing import Any, Optional, Union, List, TYPE_CHECKING
from graph_sitter.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from graph_sitter.core.file import File, SourceFile
    from graph_sitter.core.codebase import Codebase

logger = get_logger(__name__)

# Check if Pink SDK is available
try:
    import codegen_sdk_pink
    PINK_AVAILABLE = True
except ImportError:
    PINK_AVAILABLE = False
    logger.debug("Pink SDK not available")


class PinkFileWrapper:
    """Wrapper for Pink SDK File objects to make them compatible with graph-sitter File interface."""
    
    def __init__(self, pink_file: Any, codebase: "Codebase"):
        self._pink_file = pink_file
        self._codebase = codebase
        self._cached_content: Optional[str] = None
    
    @property
    def path(self) -> Path:
        """Get the file path."""
        if hasattr(self._pink_file, 'path'):
            return Path(self._pink_file.path)
        elif hasattr(self._pink_file, 'file_path'):
            return Path(self._pink_file.file_path)
        else:
            # Fallback - try to extract path from string representation
            return Path(str(self._pink_file))
    
    @property
    def content(self) -> str:
        """Get the file content."""
        if self._cached_content is None:
            if hasattr(self._pink_file, 'content'):
                self._cached_content = self._pink_file.content
            elif hasattr(self._pink_file, 'read'):
                self._cached_content = self._pink_file.read()
            elif hasattr(self._pink_file, 'text'):
                self._cached_content = self._pink_file.text
            else:
                # Fallback - read from filesystem
                try:
                    self._cached_content = self.path.read_text(encoding='utf-8')
                except Exception as e:
                    logger.warning(f"Failed to read file content for {self.path}: {e}")
                    self._cached_content = ""
        return self._cached_content
    
    @property
    def name(self) -> str:
        """Get the file name."""
        return self.path.name
    
    @property
    def suffix(self) -> str:
        """Get the file suffix."""
        return self.path.suffix
    
    @property
    def stem(self) -> str:
        """Get the file stem."""
        return self.path.stem
    
    def __str__(self) -> str:
        return str(self.path)
    
    def __repr__(self) -> str:
        return f"PinkFileWrapper({self.path})"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, PinkFileWrapper):
            return self.path == other.path
        elif hasattr(other, 'path'):
            return self.path == other.path
        return False
    
    def __hash__(self) -> int:
        return hash(self.path)


class PinkTypeConverter:
    """Converts Pink SDK types to graph-sitter compatible types."""
    
    def __init__(self, codebase: "Codebase"):
        self.codebase = codebase
    
    def convert_file(self, pink_file: Any) -> Optional["SourceFile"]:
        """Convert a Pink SDK file to a graph-sitter SourceFile."""
        if pink_file is None:
            return None
        
        # If it's already a graph-sitter file, return as-is
        if hasattr(pink_file, '__class__') and 'graph_sitter' in str(pink_file.__class__):
            return pink_file
        
        # Wrap the Pink file
        wrapper = PinkFileWrapper(pink_file, self.codebase)
        
        # Try to get the corresponding graph-sitter file from the context
        try:
            # First try to get from the graph
            gs_file = self.codebase.ctx.get_file(str(wrapper.path))
            if gs_file is not None:
                return gs_file
            
            # If not in graph, create a raw file
            return self.codebase.ctx._get_raw_file_from_path(wrapper.path)
        except Exception as e:
            logger.warning(f"Failed to convert Pink file {wrapper.path}: {e}")
            # Return the wrapper as a fallback
            return wrapper
    
    def convert_files(self, pink_files: List[Any]) -> List["SourceFile"]:
        """Convert a list of Pink SDK files to graph-sitter SourceFiles."""
        result = []
        for pink_file in pink_files:
            converted = self.convert_file(pink_file)
            if converted is not None:
                result.append(converted)
        return result
    
    def convert_file_list(self, pink_result: Any) -> List["SourceFile"]:
        """Convert Pink SDK file list result to graph-sitter files."""
        if pink_result is None:
            return []
        
        # Handle different Pink SDK result formats
        if hasattr(pink_result, '__iter__') and not isinstance(pink_result, str):
            return self.convert_files(list(pink_result))
        elif hasattr(pink_result, 'files'):
            return self.convert_files(pink_result.files)
        else:
            # Single file result
            converted = self.convert_file(pink_result)
            return [converted] if converted is not None else []


def create_pink_bridge(codebase: "Codebase") -> Optional[PinkTypeConverter]:
    """Create a Pink SDK type bridge for the given codebase."""
    if not PINK_AVAILABLE:
        return None
    
    return PinkTypeConverter(codebase)


def wrap_pink_method(codebase: "Codebase", method_name: str, original_method):
    """Wrap a Pink SDK method to convert types appropriately."""
    converter = create_pink_bridge(codebase)
    if converter is None:
        return original_method
    
    def wrapped_method(*args, **kwargs):
        try:
            result = original_method(*args, **kwargs)
            
            # Convert based on method name
            if method_name in ['get_file', 'file']:
                return converter.convert_file(result)
            elif method_name in ['files', 'get_files']:
                return converter.convert_file_list(result)
            else:
                return result
        except Exception as e:
            logger.error(f"Error in Pink SDK method {method_name}: {e}")
            # Fallback to original result
            return original_method(*args, **kwargs)
    
    return wrapped_method


def enhance_codebase_with_pink_bridge(codebase: "Codebase") -> None:
    """Enhance a codebase instance with Pink SDK type conversion."""
    if not PINK_AVAILABLE or codebase._pink_codebase is None:
        return
    
    # Wrap Pink SDK methods with type conversion
    if hasattr(codebase._pink_codebase, 'get_file'):
        original_get_file = codebase._pink_codebase.get_file
        codebase._pink_codebase.get_file = wrap_pink_method(
            codebase, 'get_file', original_get_file
        )
    
    if hasattr(codebase._pink_codebase, 'files'):
        original_files = codebase._pink_codebase.files
        # Handle property vs method
        if callable(original_files):
            codebase._pink_codebase.files = wrap_pink_method(
                codebase, 'files', original_files
            )
        else:
            # It's a property, need to wrap differently
            converter = create_pink_bridge(codebase)
            if converter:
                try:
                    converted_files = converter.convert_file_list(original_files)
                    codebase._pink_codebase._converted_files = converted_files
                    
                    # Replace the property
                    def get_converted_files():
                        return codebase._pink_codebase._converted_files
                    
                    type(codebase._pink_codebase).files = property(get_converted_files)
                except Exception as e:
                    logger.warning(f"Failed to wrap Pink SDK files property: {e}")
    
    logger.info("Pink SDK type bridge enabled for codebase")

