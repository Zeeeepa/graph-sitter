"""Module finder for AutoGenLib integration with enhanced context."""

import sys
import types
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import ModuleSpec
from typing import Optional, TYPE_CHECKING
import inspect
import os

from graph_sitter.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from .core import AutoGenLibIntegration

logger = get_logger(__name__)


class AutoGenLibLoader:
    """Custom module loader that generates code on demand."""
    
    def __init__(self, integration: "AutoGenLibIntegration", fullname: str):
        """Initialize the loader.
        
        Args:
            integration: The AutoGenLib integration instance
            fullname: Full module name to load
        """
        self.integration = integration
        self.fullname = fullname
    
    def create_module(self, spec: ModuleSpec) -> Optional[types.ModuleType]:
        """Create a new module."""
        return None  # Use default module creation
    
    def exec_module(self, module: types.ModuleType) -> None:
        """Execute the module by generating its code."""
        try:
            # Get caller information for better context
            caller_info = self._get_caller_info()
            
            # Generate the module code
            code = self.integration.generate_module(
                fullname=self.fullname,
                caller_info=caller_info
            )
            
            if code is None:
                raise ImportError(f"Failed to generate code for module {self.fullname}")
            
            # Execute the generated code in the module's namespace
            exec(code, module.__dict__)
            
            # Set module metadata
            module.__file__ = f"<autogenlib-generated:{self.fullname}>"
            module.__loader__ = self
            module.__package__ = ".".join(self.fullname.split(".")[:-1])
            
            logger.info(f"Successfully loaded generated module: {self.fullname}")
            
        except Exception as e:
            logger.error(f"Failed to execute module {self.fullname}: {e}")
            raise ImportError(f"Failed to load module {self.fullname}: {e}")
    
    def _get_caller_info(self) -> dict:
        """Get information about the code that's importing the module."""
        try:
            # Walk up the stack to find the caller
            frame = inspect.currentframe()
            caller_frame = None
            
            # Skip frames until we find the actual caller (not internal frames)
            while frame:
                frame = frame.f_back
                if frame and frame.f_code.co_filename != __file__:
                    # Check if this is not an internal import mechanism
                    filename = frame.f_code.co_filename
                    if not any(internal in filename for internal in [
                        'importlib', 'pkgutil', 'runpy', '<frozen'
                    ]):
                        caller_frame = frame
                        break
            
            if not caller_frame:
                return {}
            
            # Extract caller information
            filename = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno
            
            # Try to read the source file
            code = ""
            try:
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        code = f.read()
            except Exception as e:
                logger.debug(f"Could not read caller file {filename}: {e}")
            
            return {
                "filename": filename,
                "lineno": lineno,
                "code": code,
                "function_name": caller_frame.f_code.co_name,
                "locals": dict(caller_frame.f_locals),
                "globals": dict(caller_frame.f_globals)
            }
            
        except Exception as e:
            logger.debug(f"Failed to get caller info: {e}")
            return {}


class AutoGenLibFinder:
    """Meta path finder for AutoGenLib modules."""
    
    def __init__(self, integration: "AutoGenLibIntegration"):
        """Initialize the finder.
        
        Args:
            integration: The AutoGenLib integration instance
        """
        self.integration = integration
    
    def find_spec(self, fullname: str, path=None, target=None) -> Optional[ModuleSpec]:
        """Find module spec for AutoGenLib modules.
        
        Args:
            fullname: Full module name
            path: Module path (unused)
            target: Target module (unused)
            
        Returns:
            ModuleSpec if this is an AutoGenLib module, None otherwise
        """
        # Only handle modules under the autogenlib namespace
        if not fullname.startswith("autogenlib."):
            return None
        
        # Skip if this is just the base autogenlib module
        if fullname == "autogenlib":
            return None
        
        # Check if this module already exists
        if fullname in sys.modules:
            return None
        
        logger.debug(f"AutoGenLib finder handling: {fullname}")
        
        # Create a loader for this module
        loader = AutoGenLibLoader(self.integration, fullname)
        
        # Create and return the module spec
        spec = spec_from_loader(
            fullname,
            loader,
            origin=f"<autogenlib-generated:{fullname}>"
        )
        
        return spec
    
    def find_module(self, fullname: str, path=None):
        """Legacy finder method for older Python versions."""
        spec = self.find_spec(fullname, path)
        return spec.loader if spec else None

