"""
Codegen client with pip install overlay functionality.

This module provides the core overlay mechanism that allows the extension to work
with external codegen installations while providing fallback functionality.
"""

import logging
import importlib
import sys
from typing import Any, Dict, Optional, Union, Type, cast
from .config import CodegenAgentAPIConfig, get_overlay_strategy, detect_pip_codegen
from .types import OverlayStrategy, PipPackageInfo, OverlayInfo
from .exceptions import (
    OverlayError, 
    PipPackageNotFoundError, 
    PipPackageImportError,
    OverlayStrategyError,
    FallbackError,
    wrap_network_error
)

logger = logging.getLogger(__name__)


class OverlayClient:
    """
    Client that handles overlay functionality between pip-installed codegen and local implementation.
    
    This is the core overlay mechanism that detects and uses pip-installed codegen packages
    while providing fallback functionality to local implementations.
    """
    
    def __init__(self, config: CodegenAgentAPIConfig):
        """
        Initialize overlay client.
        
        Args:
            config: Extension configuration
        """
        self.config = config
        self.strategy = get_overlay_strategy(config)
        self.pip_info = detect_pip_codegen()
        
        # Track which implementation is currently active
        self._active_implementation: Optional[str] = None
        self._pip_agent_class: Optional[Type] = None
        self._pip_task_class: Optional[Type] = None
        self._pip_codebase_ai_class: Optional[Type] = None
        self._local_implementations_loaded = False
        
        # Metrics
        self._pip_calls = 0
        self._local_calls = 0
        self._fallback_count = 0
        self._overlay_errors = 0
        
        logger.info(f"OverlayClient initialized with strategy: {self.strategy}")
        logger.info(f"Pip package available: {self.pip_info is not None}")
        
        # Initialize based on strategy
        self._initialize_implementations()
    
    def _initialize_implementations(self) -> None:
        """Initialize implementations based on overlay strategy."""
        try:
            if self.strategy in [OverlayStrategy.PIP_ONLY, OverlayStrategy.PIP_WITH_LOCAL_FALLBACK]:
                self._load_pip_implementation()
                self._active_implementation = "pip"
            elif self.strategy == OverlayStrategy.LOCAL_ONLY:
                self._load_local_implementation()
                self._active_implementation = "local"
            elif self.strategy == OverlayStrategy.LOCAL_WITH_PIP_FALLBACK:
                self._load_local_implementation()
                self._active_implementation = "local"
                # Also try to load pip as fallback
                try:
                    self._load_pip_implementation()
                except Exception as e:
                    logger.warning(f"Failed to load pip implementation for fallback: {e}")
            
        except Exception as e:
            logger.error(f"Failed to initialize implementations: {e}")
            self._overlay_errors += 1
            
            # Try fallback if available
            if self.config.fallback_to_local and self.strategy != OverlayStrategy.LOCAL_ONLY:
                try:
                    logger.info("Attempting fallback to local implementation")
                    self._load_local_implementation()
                    self._active_implementation = "local"
                    self._fallback_count += 1
                except Exception as fallback_error:
                    raise FallbackError(
                        primary_strategy=self.strategy,
                        fallback_strategy="local_only",
                        primary_error=e,
                        fallback_error=fallback_error
                    )
            else:
                raise OverlayStrategyError(
                    strategy=self.strategy,
                    reason=f"Failed to initialize and fallback disabled: {e}"
                )
    
    def _load_pip_implementation(self) -> None:
        """Load pip-installed codegen implementation."""
        if not self.pip_info:
            raise PipPackageNotFoundError(self.config.pip_package_name)
        
        try:
            # Import the pip-installed codegen package
            codegen_module = importlib.import_module(self.config.pip_package_name)
            
            # Get the main classes
            if hasattr(codegen_module, 'Agent'):
                self._pip_agent_class = codegen_module.Agent
            else:
                raise PipPackageImportError(
                    self.config.pip_package_name,
                    message=f"Pip package '{self.config.pip_package_name}' does not have 'Agent' class"
                )
            
            if hasattr(codegen_module, 'Task'):
                self._pip_task_class = codegen_module.Task
            
            if hasattr(codegen_module, 'CodebaseAI'):
                self._pip_codebase_ai_class = codegen_module.CodebaseAI
            
            logger.info(f"Successfully loaded pip implementation: {self.config.pip_package_name} v{self.pip_info.get('version', 'unknown')}")
            
        except ImportError as e:
            raise PipPackageImportError(
                self.config.pip_package_name,
                import_error=e
            )
        except Exception as e:
            raise PipPackageImportError(
                self.config.pip_package_name,
                import_error=e,
                message=f"Unexpected error loading pip package: {e}"
            )
    
    def _load_local_implementation(self) -> None:
        """Load local implementation."""
        if self._local_implementations_loaded:
            return
        
        try:
            # Import local implementations
            from .agent import Agent as LocalAgent
            from .task import Task as LocalTask
            from .codebase_ai import CodebaseAI as LocalCodebaseAI
            
            # Store references (they're already loaded as classes)
            self._local_agent_class = LocalAgent
            self._local_task_class = LocalTask
            self._local_codebase_ai_class = LocalCodebaseAI
            
            self._local_implementations_loaded = True
            logger.info("Successfully loaded local implementation")
            
        except ImportError as e:
            raise OverlayError(
                f"Failed to load local implementation: {e}",
                local_available=False
            )
    
    def create_agent(self, **kwargs) -> Any:
        """
        Create an Agent instance using the active implementation.
        
        Args:
            **kwargs: Arguments to pass to Agent constructor
            
        Returns:
            Agent instance from active implementation
        """
        # Merge config with kwargs
        agent_kwargs = {
            "org_id": self.config.org_id,
            "token": self.config.token,
            "base_url": self.config.base_url,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
            "retry_backoff_factor": self.config.retry_backoff_factor,
            "rate_limit_buffer": self.config.rate_limit_buffer,
            "enable_logging": self.config.enable_logging,
            "connection_pool_size": self.config.connection_pool_size,
            "validate_on_init": self.config.validate_on_init,
            **kwargs
        }
        
        try:
            if self._active_implementation == "pip" and self._pip_agent_class:
                self._pip_calls += 1
                return self._pip_agent_class(**agent_kwargs)
            elif self._active_implementation == "local":
                if not self._local_implementations_loaded:
                    self._load_local_implementation()
                self._local_calls += 1
                return self._local_agent_class(**agent_kwargs)
            else:
                raise OverlayError(f"No active implementation available (current: {self._active_implementation})")
                
        except Exception as e:
            self._overlay_errors += 1
            
            # Try fallback if available
            if self._should_attempt_fallback(e):
                return self._create_agent_fallback(**agent_kwargs)
            else:
                raise
    
    def create_codebase_ai(self, **kwargs) -> Any:
        """
        Create a CodebaseAI instance using the active implementation.
        
        Args:
            **kwargs: Arguments to pass to CodebaseAI constructor
            
        Returns:
            CodebaseAI instance from active implementation
        """
        # Merge config with kwargs
        codebase_ai_kwargs = {
            "org_id": self.config.org_id,
            "token": self.config.token,
            "base_url": self.config.base_url,
            "timeout": self.config.timeout,
            **kwargs
        }
        
        try:
            if self._active_implementation == "pip" and self._pip_codebase_ai_class:
                self._pip_calls += 1
                return self._pip_codebase_ai_class(**codebase_ai_kwargs)
            elif self._active_implementation == "local":
                if not self._local_implementations_loaded:
                    self._load_local_implementation()
                self._local_calls += 1
                return self._local_codebase_ai_class(**codebase_ai_kwargs)
            else:
                raise OverlayError(f"No active implementation available (current: {self._active_implementation})")
                
        except Exception as e:
            self._overlay_errors += 1
            
            # Try fallback if available
            if self._should_attempt_fallback(e):
                return self._create_codebase_ai_fallback(**codebase_ai_kwargs)
            else:
                raise
    
    def _should_attempt_fallback(self, error: Exception) -> bool:
        """Determine if fallback should be attempted based on error and strategy."""
        if not self.config.fallback_to_local:
            return False
        
        if self.strategy == OverlayStrategy.PIP_WITH_LOCAL_FALLBACK and self._active_implementation == "pip":
            return True
        elif self.strategy == OverlayStrategy.LOCAL_WITH_PIP_FALLBACK and self._active_implementation == "local":
            return True
        
        return False
    
    def _create_agent_fallback(self, **kwargs) -> Any:
        """Create Agent using fallback implementation."""
        try:
            if self._active_implementation == "pip":
                # Fallback to local
                if not self._local_implementations_loaded:
                    self._load_local_implementation()
                logger.warning("Falling back to local Agent implementation")
                self._fallback_count += 1
                self._local_calls += 1
                return self._local_agent_class(**kwargs)
            else:
                # Fallback to pip
                if not self._pip_agent_class:
                    self._load_pip_implementation()
                logger.warning("Falling back to pip Agent implementation")
                self._fallback_count += 1
                self._pip_calls += 1
                return self._pip_agent_class(**kwargs)
                
        except Exception as fallback_error:
            raise FallbackError(
                primary_strategy=self._active_implementation or "unknown",
                fallback_strategy="local" if self._active_implementation == "pip" else "pip",
                fallback_error=fallback_error
            )
    
    def _create_codebase_ai_fallback(self, **kwargs) -> Any:
        """Create CodebaseAI using fallback implementation."""
        try:
            if self._active_implementation == "pip":
                # Fallback to local
                if not self._local_implementations_loaded:
                    self._load_local_implementation()
                logger.warning("Falling back to local CodebaseAI implementation")
                self._fallback_count += 1
                self._local_calls += 1
                return self._local_codebase_ai_class(**kwargs)
            else:
                # Fallback to pip
                if not self._pip_codebase_ai_class:
                    self._load_pip_implementation()
                logger.warning("Falling back to pip CodebaseAI implementation")
                self._fallback_count += 1
                self._pip_calls += 1
                return self._pip_codebase_ai_class(**kwargs)
                
        except Exception as fallback_error:
            raise FallbackError(
                primary_strategy=self._active_implementation or "unknown",
                fallback_strategy="local" if self._active_implementation == "pip" else "pip",
                fallback_error=fallback_error
            )
    
    def get_overlay_info(self) -> OverlayInfo:
        """Get information about the current overlay configuration."""
        return {
            "strategy": self.strategy,
            "pip_available": self.pip_info is not None,
            "pip_info": self.pip_info,
            "local_available": self._local_implementations_loaded,
            "active_implementation": self._active_implementation or "none"
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get overlay metrics."""
        total_calls = self._pip_calls + self._local_calls
        
        return {
            "strategy": self.strategy,
            "pip_calls": self._pip_calls,
            "local_calls": self._local_calls,
            "total_calls": total_calls,
            "fallback_count": self._fallback_count,
            "overlay_errors": self._overlay_errors,
            "pip_usage_percentage": (self._pip_calls / max(total_calls, 1)) * 100,
            "active_implementation": self._active_implementation
        }
    
    def switch_implementation(self, implementation: str) -> None:
        """
        Manually switch to a different implementation.
        
        Args:
            implementation: "pip" or "local"
        """
        if implementation not in ["pip", "local"]:
            raise ValueError("implementation must be 'pip' or 'local'")
        
        if implementation == "pip":
            if not self._pip_agent_class:
                self._load_pip_implementation()
            self._active_implementation = "pip"
        else:
            if not self._local_implementations_loaded:
                self._load_local_implementation()
            self._active_implementation = "local"
        
        logger.info(f"Switched to {implementation} implementation")
    
    def test_implementations(self) -> Dict[str, Any]:
        """
        Test both implementations to verify they work.
        
        Returns:
            Dictionary with test results
        """
        results = {
            "pip": {"available": False, "error": None},
            "local": {"available": False, "error": None}
        }
        
        # Test pip implementation
        try:
            self._load_pip_implementation()
            # Try to create an agent (without making API calls)
            agent = self._pip_agent_class(
                org_id="test",
                token="test",
                validate_on_init=False
            )
            results["pip"]["available"] = True
        except Exception as e:
            results["pip"]["error"] = str(e)
        
        # Test local implementation
        try:
            self._load_local_implementation()
            # Try to create an agent (without making API calls)
            agent = self._local_agent_class(
                org_id="test",
                token="test",
                validate_on_init=False
            )
            results["local"]["available"] = True
        except Exception as e:
            results["local"]["error"] = str(e)
        
        return results


# Convenience functions for creating instances

def create_agent(config: Optional[CodegenAgentAPIConfig] = None, **kwargs) -> Any:
    """
    Create an Agent instance using overlay functionality.
    
    Args:
        config: Optional configuration (will use default if not provided)
        **kwargs: Additional arguments for Agent constructor
        
    Returns:
        Agent instance
    """
    if config is None:
        from .config import get_codegen_config
        config = get_codegen_config(**kwargs)
    
    client = OverlayClient(config)
    return client.create_agent(**kwargs)


def create_codebase_ai(config: Optional[CodegenAgentAPIConfig] = None, **kwargs) -> Any:
    """
    Create a CodebaseAI instance using overlay functionality.
    
    Args:
        config: Optional configuration (will use default if not provided)
        **kwargs: Additional arguments for CodebaseAI constructor
        
    Returns:
        CodebaseAI instance
    """
    if config is None:
        from .config import get_codegen_config
        config = get_codegen_config(**kwargs)
    
    client = OverlayClient(config)
    return client.create_codebase_ai(**kwargs)


# Export main classes and functions
__all__ = [
    "OverlayClient",
    "create_agent",
    "create_codebase_ai",
]

