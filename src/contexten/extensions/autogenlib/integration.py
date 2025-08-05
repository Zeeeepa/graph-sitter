"""Integration of AutoGenLib with the broader contexten ecosystem."""

from typing import Optional, TYPE_CHECKING
import os

from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

from .core import AutoGenLibIntegration, init_autogenlib
from .config import AutoGenLibConfig, load_config

if TYPE_CHECKING:
    from contexten.extensions.events.codegen_app import CodegenApp

logger = get_logger(__name__)


class ContextenAutoGenLibIntegration:
    """Integration layer between AutoGenLib and Contexten ecosystem."""
    
    def __init__(self, codegen_app: Optional["CodegenApp"] = None, config: Optional[AutoGenLibConfig] = None):
        """Initialize the integration.
        
        Args:
            codegen_app: Optional CodegenApp instance for codebase context
            config: Optional configuration (loads from environment if not provided)
        """
        self.codegen_app = codegen_app
        self.config = config or load_config()
        self.autogenlib: Optional[AutoGenLibIntegration] = None
        
        # Initialize AutoGenLib if configuration is valid
        issues = self.config.validate()
        if not issues:
            self._initialize_autogenlib()
        else:
            logger.error("AutoGenLib configuration invalid:")
            for issue in issues:
                logger.error(f"  - {issue}")
    
    def _initialize_autogenlib(self):
        """Initialize AutoGenLib with the current configuration."""
        try:
            # Get codebase from CodegenApp if available
            codebase = None
            if self.codegen_app:
                try:
                    codebase = self.codegen_app.get_codebase()
                    logger.info("Using codebase from CodegenApp for context")
                except Exception as e:
                    logger.warning(f"Failed to get codebase from CodegenApp: {e}")
            
            # Initialize AutoGenLib
            self.autogenlib = init_autogenlib(
                description=self.config.description,
                codebase=codebase,
                codegen_org_id=self.config.codegen_org_id,
                codegen_token=self.config.codegen_token,
                claude_api_key=self.config.claude_api_key,
                enable_caching=self.config.enable_caching,
                enable_exception_handler=self.config.enable_exception_handler
            )
            
            logger.info("Successfully initialized AutoGenLib integration")
            
        except Exception as e:
            logger.error(f"Failed to initialize AutoGenLib: {e}")
            self.autogenlib = None
    
    def set_codebase(self, codebase: Codebase):
        """Update the codebase for context analysis.
        
        Args:
            codebase: New codebase to use for context
        """
        if self.autogenlib:
            self.autogenlib.set_codebase(codebase)
            logger.info("Updated AutoGenLib codebase context")
        else:
            logger.warning("AutoGenLib not initialized, cannot set codebase")
    
    def set_codegen_app(self, codegen_app: "CodegenApp"):
        """Set or update the CodegenApp instance.
        
        Args:
            codegen_app: CodegenApp instance to use
        """
        self.codegen_app = codegen_app
        
        # Update codebase if AutoGenLib is initialized
        if self.autogenlib:
            try:
                codebase = codegen_app.get_codebase()
                self.set_codebase(codebase)
            except Exception as e:
                logger.warning(f"Failed to update codebase from new CodegenApp: {e}")
    
    def is_available(self) -> bool:
        """Check if AutoGenLib is available and ready to use."""
        return self.autogenlib is not None
    
    def get_status(self) -> dict:
        """Get status information about the integration."""
        status = {
            "initialized": self.autogenlib is not None,
            "config_valid": len(self.config.validate()) == 0,
            "has_codebase": False,
            "has_codegen_app": self.codegen_app is not None,
            "available_providers": self.config.get_available_providers(),
            "cache_enabled": self.config.enable_caching
        }
        
        if self.autogenlib and self.autogenlib.codebase:
            status["has_codebase"] = True
            status["codebase_stats"] = {
                "functions": len(self.autogenlib.codebase.functions),
                "classes": len(self.autogenlib.codebase.classes),
                "files": len(self.autogenlib.codebase.files)
            }
        
        if self.autogenlib and self.autogenlib.cache:
            cache_info = self.autogenlib.cache.get_cache_info()
            status["cache_info"] = cache_info
        
        return status
    
    def clear_cache(self):
        """Clear the AutoGenLib cache."""
        if self.autogenlib:
            self.autogenlib.clear_cache()
            logger.info("Cleared AutoGenLib cache")
        else:
            logger.warning("AutoGenLib not initialized, cannot clear cache")
    
    def reload_config(self):
        """Reload configuration from environment and reinitialize."""
        logger.info("Reloading AutoGenLib configuration")
        self.config = load_config()
        
        # Reinitialize if configuration is valid
        issues = self.config.validate()
        if not issues:
            self._initialize_autogenlib()
        else:
            logger.error("New configuration invalid, keeping existing instance")
            for issue in issues:
                logger.error(f"  - {issue}")


# Global integration instance
_global_integration: Optional[ContextenAutoGenLibIntegration] = None


def get_contexten_autogenlib() -> Optional[ContextenAutoGenLibIntegration]:
    """Get the global contexten AutoGenLib integration instance."""
    return _global_integration


def init_contexten_autogenlib(
    codegen_app: Optional["CodegenApp"] = None,
    config: Optional[AutoGenLibConfig] = None
) -> ContextenAutoGenLibIntegration:
    """Initialize the global contexten AutoGenLib integration.
    
    Args:
        codegen_app: Optional CodegenApp instance
        config: Optional configuration
        
    Returns:
        The initialized integration instance
    """
    global _global_integration
    
    _global_integration = ContextenAutoGenLibIntegration(
        codegen_app=codegen_app,
        config=config
    )
    
    return _global_integration


def setup_autogenlib_for_codegen_app(codegen_app: "CodegenApp") -> bool:
    """Set up AutoGenLib for a CodegenApp instance.
    
    This is a convenience function that can be called from CodegenApp
    to automatically set up AutoGenLib integration.
    
    Args:
        codegen_app: The CodegenApp instance to integrate with
        
    Returns:
        True if setup was successful, False otherwise
    """
    try:
        # Initialize the integration
        integration = init_contexten_autogenlib(codegen_app=codegen_app)
        
        if integration.is_available():
            logger.info("AutoGenLib successfully set up for CodegenApp")
            return True
        else:
            logger.warning("AutoGenLib setup completed but not available (check configuration)")
            return False
            
    except Exception as e:
        logger.error(f"Failed to set up AutoGenLib for CodegenApp: {e}")
        return False


# Monkey patch to add AutoGenLib support to CodegenApp
def _patch_codegen_app():
    """Add AutoGenLib support to CodegenApp class."""
    try:
        from contexten.extensions.events.codegen_app import CodegenApp
        
        # Add AutoGenLib integration to CodegenApp
        def setup_autogenlib(self, config: Optional[AutoGenLibConfig] = None) -> bool:
            """Set up AutoGenLib integration for this CodegenApp instance."""
            return setup_autogenlib_for_codegen_app(self)
        
        def get_autogenlib_status(self) -> dict:
            """Get AutoGenLib integration status."""
            integration = get_contexten_autogenlib()
            if integration:
                return integration.get_status()
            return {"initialized": False, "error": "AutoGenLib not initialized"}
        
        def clear_autogenlib_cache(self):
            """Clear AutoGenLib cache."""
            integration = get_contexten_autogenlib()
            if integration:
                integration.clear_cache()
        
        # Add methods to CodegenApp
        CodegenApp.setup_autogenlib = setup_autogenlib
        CodegenApp.get_autogenlib_status = get_autogenlib_status
        CodegenApp.clear_autogenlib_cache = clear_autogenlib_cache
        
        logger.debug("Successfully patched CodegenApp with AutoGenLib support")
        
    except ImportError:
        logger.debug("CodegenApp not available, skipping monkey patch")
    except Exception as e:
        logger.warning(f"Failed to patch CodegenApp: {e}")


# Apply the monkey patch when this module is imported
_patch_codegen_app()

