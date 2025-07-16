"""
Grainchain Integration for Graph-Sitter

This module integrates Grainchain's sandbox capabilities with graph-sitter,
enabling code execution and testing in isolated environments.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

# Optional grainchain import
try:
    from grainchain import Sandbox, SandboxConfig, Providers, create_sandbox
    from grainchain.core.exceptions import GrainchainError, SandboxError, TimeoutError
    GRAINCHAIN_AVAILABLE = True
except ImportError:
    logger.info("Grainchain not available. Install with: pip install grainchain")
    GRAINCHAIN_AVAILABLE = False
    # Mock classes for type hints
    class Sandbox:
        pass
    class SandboxConfig:
        pass
    class Providers:
        LOCAL = "local"
        E2B = "e2b"
        DAYTONA = "daytona"
        MORPH = "morph"
        MODAL = "modal"
    class GrainchainError(Exception):
        pass
    class SandboxError(Exception):
        pass
    class TimeoutError(Exception):
        pass


@dataclass
class ExecutionResult:
    """Result of code execution in sandbox."""
    stdout: str
    stderr: str
    return_code: int
    success: bool
    duration: float
    provider: str
    
    @property
    def output(self) -> str:
        """Combined stdout and stderr output."""
        return f"{self.stdout}\n{self.stderr}".strip()


class GrainchainIntegration:
    """
    Integration between Graph-Sitter and Grainchain for sandbox execution.
    
    This class provides methods to execute code snippets, run tests, and
    perform other operations in isolated sandbox environments.
    """
    
    def __init__(self, codebase=None, default_provider: str = "local", **config_kwargs):
        """
        Initialize Grainchain integration.
        
        Args:
            codebase: Graph-sitter codebase instance (optional)
            default_provider: Default sandbox provider to use
            **config_kwargs: Additional configuration for sandbox
        """
        self.codebase = codebase
        self.default_provider = default_provider
        self.config_kwargs = config_kwargs
        self._active_sandboxes: Dict[str, Sandbox] = {}
        
        if not GRAINCHAIN_AVAILABLE:
            logger.warning("Grainchain integration disabled - grainchain not installed")
    
    def is_available(self) -> bool:
        """Check if Grainchain integration is available."""
        return GRAINCHAIN_AVAILABLE
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        provider: Optional[str] = None,
        timeout: int = 60,
        working_directory: Optional[str] = None,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute code in a sandbox environment.
        
        Args:
            code: Code to execute
            language: Programming language (python, javascript, etc.)
            provider: Sandbox provider to use (defaults to default_provider)
            timeout: Execution timeout in seconds
            working_directory: Working directory for execution
            environment_vars: Environment variables to set
            
        Returns:
            ExecutionResult with execution details
            
        Raises:
            RuntimeError: If grainchain is not available
            SandboxError: If sandbox execution fails
        """
        if not GRAINCHAIN_AVAILABLE:
            raise RuntimeError("Grainchain integration not available")
        
        provider = provider or self.default_provider
        
        # Prepare sandbox configuration
        config_kwargs = {
            "timeout": timeout,
            **self.config_kwargs
        }
        
        if working_directory:
            config_kwargs["working_directory"] = working_directory
        if environment_vars:
            config_kwargs["environment_vars"] = environment_vars
        
        # Create sandbox
        sandbox = create_sandbox(provider, **config_kwargs)
        
        try:
            async with sandbox:
                # Determine execution command based on language
                if language.lower() == "python":
                    command = f"python -c \"{code.replace('\"', '\\\"')}\""
                elif language.lower() in ["javascript", "js", "node"]:
                    command = f"node -e \"{code.replace('\"', '\\\"')}\""
                elif language.lower() == "bash":
                    command = code
                else:
                    # Default to treating as shell command
                    command = code
                
                # Execute code
                import time
                start_time = time.time()
                
                try:
                    result = await sandbox.execute(command)
                    duration = time.time() - start_time
                    
                    return ExecutionResult(
                        stdout=result.stdout or "",
                        stderr=result.stderr or "",
                        return_code=result.return_code,
                        success=result.return_code == 0,
                        duration=duration,
                        provider=provider
                    )
                    
                except TimeoutError as e:
                    duration = time.time() - start_time
                    return ExecutionResult(
                        stdout="",
                        stderr=f"Execution timed out after {timeout}s: {e}",
                        return_code=-1,
                        success=False,
                        duration=duration,
                        provider=provider
                    )
                    
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return ExecutionResult(
                stdout="",
                stderr=f"Sandbox error: {e}",
                return_code=-1,
                success=False,
                duration=0.0,
                provider=provider
            )
    
    async def execute_file(
        self,
        file_path: Union[str, Path],
        provider: Optional[str] = None,
        timeout: int = 60,
        **kwargs
    ) -> ExecutionResult:
        """
        Execute a file in sandbox environment.
        
        Args:
            file_path: Path to file to execute
            provider: Sandbox provider to use
            timeout: Execution timeout in seconds
            **kwargs: Additional configuration
            
        Returns:
            ExecutionResult with execution details
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ExecutionResult(
                stdout="",
                stderr=f"File not found: {file_path}",
                return_code=1,
                success=False,
                duration=0.0,
                provider=provider or self.default_provider
            )
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr=f"Failed to read file: {e}",
                return_code=1,
                success=False,
                duration=0.0,
                provider=provider or self.default_provider
            )
        
        # Determine language from file extension
        language = self._detect_language(file_path)
        
        return await self.execute_code(
            code=code,
            language=language,
            provider=provider,
            timeout=timeout,
            working_directory=str(file_path.parent),
            **kwargs
        )
    
    async def run_tests(
        self,
        test_command: str = "python -m pytest",
        provider: Optional[str] = None,
        timeout: int = 300,
        **kwargs
    ) -> ExecutionResult:
        """
        Run tests in sandbox environment.
        
        Args:
            test_command: Command to run tests
            provider: Sandbox provider to use
            timeout: Test timeout in seconds
            **kwargs: Additional configuration
            
        Returns:
            ExecutionResult with test results
        """
        return await self.execute_code(
            code=test_command,
            language="bash",
            provider=provider,
            timeout=timeout,
            **kwargs
        )
    
    async def install_dependencies(
        self,
        requirements: Union[str, List[str]],
        provider: Optional[str] = None,
        package_manager: str = "pip",
        timeout: int = 300
    ) -> ExecutionResult:
        """
        Install dependencies in sandbox environment.
        
        Args:
            requirements: Package requirements (string or list)
            provider: Sandbox provider to use
            package_manager: Package manager to use (pip, npm, etc.)
            timeout: Installation timeout in seconds
            
        Returns:
            ExecutionResult with installation results
        """
        if isinstance(requirements, list):
            requirements = " ".join(requirements)
        
        if package_manager == "pip":
            command = f"pip install {requirements}"
        elif package_manager == "npm":
            command = f"npm install {requirements}"
        elif package_manager == "yarn":
            command = f"yarn add {requirements}"
        else:
            command = f"{package_manager} {requirements}"
        
        return await self.execute_code(
            code=command,
            language="bash",
            provider=provider,
            timeout=timeout
        )
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        extension = file_path.suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'javascript',
            '.jsx': 'javascript',
            '.tsx': 'javascript',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.fish': 'bash',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php',
        }
        
        return language_map.get(extension, 'bash')
    
    async def create_persistent_sandbox(
        self,
        name: str,
        provider: Optional[str] = None,
        **config_kwargs
    ) -> Optional[Sandbox]:
        """
        Create a persistent sandbox that can be reused.
        
        Args:
            name: Name for the sandbox
            provider: Sandbox provider to use
            **config_kwargs: Additional configuration
            
        Returns:
            Sandbox instance or None if creation failed
        """
        if not GRAINCHAIN_AVAILABLE:
            logger.error("Cannot create persistent sandbox - grainchain not available")
            return None
        
        provider = provider or self.default_provider
        
        try:
            config = {**self.config_kwargs, **config_kwargs}
            sandbox = create_sandbox(provider, **config)
            
            # Store for later use
            self._active_sandboxes[name] = sandbox
            
            logger.info(f"Created persistent sandbox '{name}' with provider '{provider}'")
            return sandbox
            
        except Exception as e:
            logger.error(f"Failed to create persistent sandbox '{name}': {e}")
            return None
    
    async def get_sandbox(self, name: str) -> Optional[Sandbox]:
        """Get a persistent sandbox by name."""
        return self._active_sandboxes.get(name)
    
    async def cleanup_sandbox(self, name: str) -> bool:
        """Clean up a persistent sandbox."""
        if name in self._active_sandboxes:
            try:
                sandbox = self._active_sandboxes[name]
                if hasattr(sandbox, 'cleanup'):
                    await sandbox.cleanup()
                del self._active_sandboxes[name]
                logger.info(f"Cleaned up sandbox '{name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to cleanup sandbox '{name}': {e}")
                return False
        return False
    
    async def cleanup_all_sandboxes(self) -> None:
        """Clean up all persistent sandboxes."""
        for name in list(self._active_sandboxes.keys()):
            await self.cleanup_sandbox(name)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available sandbox providers."""
        if not GRAINCHAIN_AVAILABLE:
            return []
        
        return [
            Providers.LOCAL,
            Providers.E2B,
            Providers.DAYTONA,
            Providers.MORPH,
            Providers.MODAL,
        ]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about available providers."""
        if not GRAINCHAIN_AVAILABLE:
            return {"available": False, "providers": []}
        
        try:
            from grainchain import get_providers_info
            return {
                "available": True,
                "providers": get_providers_info(),
                "default_provider": self.default_provider
            }
        except ImportError:
            return {
                "available": True,
                "providers": self.get_available_providers(),
                "default_provider": self.default_provider
            }


# Convenience function for codebase integration
def add_grainchain_capabilities(codebase, **kwargs) -> None:
    """
    Add Grainchain sandbox capabilities to a codebase instance.
    
    Args:
        codebase: Graph-sitter codebase instance
        **kwargs: Configuration for GrainchainIntegration
    """
    if hasattr(codebase, '_grainchain'):
        # Already has grainchain integration
        return
    
    # Create integration instance
    integration = GrainchainIntegration(codebase=codebase, **kwargs)
    codebase._grainchain = integration
    
    # Add methods to codebase
    codebase.execute_code = integration.execute_code
    codebase.execute_file = integration.execute_file
    codebase.run_tests = integration.run_tests
    codebase.install_dependencies = integration.install_dependencies
    codebase.create_sandbox = integration.create_persistent_sandbox
    codebase.get_sandbox = integration.get_sandbox
    codebase.cleanup_sandbox = integration.cleanup_sandbox
    codebase.cleanup_all_sandboxes = integration.cleanup_all_sandboxes
    
    # Add properties
    codebase.available_providers = property(lambda self: self._grainchain.get_available_providers())
    codebase.provider_info = property(lambda self: self._grainchain.get_provider_info())
    
    logger.info(f"Grainchain capabilities added to codebase: {codebase.repo_path}")

