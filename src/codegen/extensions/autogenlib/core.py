"""Core AutoGenLib integration with enhanced context and multiple AI providers."""

import sys
import os
from typing import Optional, Dict, Any
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import ModuleSpec
import importlib.util

from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

from .generator import CodeGenerator, CodegenSDKProvider, ClaudeProvider
from .context import GraphSitterContextProvider
from .finder import AutoGenLibFinder
from .cache import CodeCache

logger = get_logger(__name__)


class AutoGenLibIntegration:
    """Main integration class that orchestrates autogenlib functionality with enhanced context."""
    
    def __init__(
        self,
        description: str = "Dynamic code generation library",
        codebase: Optional[Codebase] = None,
        codegen_org_id: Optional[str] = None,
        codegen_token: Optional[str] = None,
        claude_api_key: Optional[str] = None,
        enable_caching: bool = False,
        enable_exception_handler: bool = True
    ):
        """Initialize the AutoGenLib integration.
        
        Args:
            description: Description of the library functionality
            codebase: Graph-sitter codebase for context analysis
            codegen_org_id: Codegen SDK organization ID
            codegen_token: Codegen SDK authentication token
            claude_api_key: Claude API key for fallback
            enable_caching: Whether to cache generated code
            enable_exception_handler: Whether to enable exception handling
        """
        self.description = description
        self.codebase = codebase
        self.enable_caching = enable_caching
        self.enable_exception_handler = enable_exception_handler
        
        # Initialize cache
        self.cache = CodeCache(enabled=enable_caching)
        
        # Initialize context provider
        self.context_provider = GraphSitterContextProvider(codebase) if codebase else None
        
        # Initialize code generator with multiple providers
        providers = []
        
        # Add Codegen SDK provider if credentials available
        if codegen_org_id and codegen_token:
            providers.append(CodegenSDKProvider(
                org_id=codegen_org_id,
                token=codegen_token
            ))
            logger.info("Initialized Codegen SDK provider")
        
        # Add Claude provider if API key available
        if claude_api_key:
            providers.append(ClaudeProvider(api_key=claude_api_key))
            logger.info("Initialized Claude provider")
        
        # Fallback to environment variables
        if not providers:
            # Try Codegen SDK from environment
            env_org_id = os.environ.get("CODEGEN_ORG_ID")
            env_token = os.environ.get("CODEGEN_TOKEN")
            if env_org_id and env_token:
                providers.append(CodegenSDKProvider(
                    org_id=env_org_id,
                    token=env_token
                ))
                logger.info("Initialized Codegen SDK provider from environment")
            
            # Try Claude from environment
            env_claude_key = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
            if env_claude_key:
                providers.append(ClaudeProvider(api_key=env_claude_key))
                logger.info("Initialized Claude provider from environment")
        
        if not providers:
            logger.warning("No AI providers configured. AutoGenLib will not function.")
            
        self.generator = CodeGenerator(providers=providers)
        
        # Set up the module finder
        self.finder = AutoGenLibFinder(self)
        
        # Install the finder if not already present
        self._install_finder()
        
        # Set up exception handler if enabled
        if self.enable_exception_handler:
            self._setup_exception_handler()
    
    def _install_finder(self):
        """Install the custom module finder in sys.meta_path."""
        # Remove any existing AutoGenLibFinder instances
        sys.meta_path = [finder for finder in sys.meta_path 
                        if not isinstance(finder, AutoGenLibFinder)]
        
        # Insert our finder at the beginning
        sys.meta_path.insert(0, self.finder)
        logger.debug("Installed AutoGenLib module finder")
    
    def _setup_exception_handler(self):
        """Set up global exception handler for better error messages."""
        # This would integrate with autogenlib's exception handling
        # For now, we'll keep it simple
        pass
    
    def generate_module(
        self,
        fullname: str,
        description: Optional[str] = None,
        existing_code: Optional[str] = None,
        caller_info: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Generate code for a module using the configured providers.
        
        Args:
            fullname: Full module name (e.g., 'autogenlib.tokens.generate_token')
            description: Description of what to generate
            existing_code: Existing module code to extend
            caller_info: Information about the calling code
            
        Returns:
            Generated Python code or None if generation failed
        """
        # Check cache first
        if self.enable_caching:
            cached_code = self.cache.get(fullname)
            if cached_code:
                logger.debug(f"Retrieved cached code for {fullname}")
                return cached_code
        
        # Gather context from graph-sitter if available
        context = {}
        if self.context_provider:
            try:
                context = self.context_provider.get_context(fullname, caller_info)
                logger.debug(f"Gathered graph-sitter context for {fullname}")
            except Exception as e:
                logger.warning(f"Failed to gather context for {fullname}: {e}")
        
        # Generate code using the configured providers
        try:
            code = self.generator.generate_code(
                description=description or self.description,
                fullname=fullname,
                existing_code=existing_code,
                caller_info=caller_info,
                context=context
            )
            
            if code and self.enable_caching:
                self.cache.set(fullname, code)
                logger.debug(f"Cached generated code for {fullname}")
            
            return code
            
        except Exception as e:
            logger.error(f"Failed to generate code for {fullname}: {e}")
            return None
    
    def set_codebase(self, codebase: Codebase):
        """Update the codebase for context analysis."""
        self.codebase = codebase
        self.context_provider = GraphSitterContextProvider(codebase)
        logger.info("Updated codebase for context analysis")
    
    def add_provider(self, provider):
        """Add a new code generation provider."""
        self.generator.add_provider(provider)
        logger.info(f"Added provider: {provider.__class__.__name__}")
    
    def clear_cache(self):
        """Clear the code generation cache."""
        self.cache.clear()
        logger.info("Cleared code generation cache")


# Global instance for backward compatibility
_global_integration: Optional[AutoGenLibIntegration] = None


def init_autogenlib(
    description: str = "Dynamic code generation library",
    codebase: Optional[Codebase] = None,
    codegen_org_id: Optional[str] = None,
    codegen_token: Optional[str] = None,
    claude_api_key: Optional[str] = None,
    enable_caching: bool = False,
    enable_exception_handler: bool = True
) -> AutoGenLibIntegration:
    """Initialize AutoGenLib with enhanced context and multiple AI providers.
    
    This function creates a global AutoGenLib integration instance that can be
    used throughout the application.
    
    Args:
        description: Description of the library functionality
        codebase: Graph-sitter codebase for context analysis
        codegen_org_id: Codegen SDK organization ID
        codegen_token: Codegen SDK authentication token
        claude_api_key: Claude API key for fallback
        enable_caching: Whether to cache generated code
        enable_exception_handler: Whether to enable exception handling
        
    Returns:
        The initialized AutoGenLib integration instance
    """
    global _global_integration
    
    _global_integration = AutoGenLibIntegration(
        description=description,
        codebase=codebase,
        codegen_org_id=codegen_org_id,
        codegen_token=codegen_token,
        claude_api_key=claude_api_key,
        enable_caching=enable_caching,
        enable_exception_handler=enable_exception_handler
    )
    
    logger.info("Initialized AutoGenLib integration")
    return _global_integration


def get_integration() -> Optional[AutoGenLibIntegration]:
    """Get the global AutoGenLib integration instance."""
    return _global_integration

