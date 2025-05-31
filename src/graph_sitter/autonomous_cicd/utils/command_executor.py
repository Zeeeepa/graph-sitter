"""Command execution utility with timeout and error handling."""

import asyncio
import logging
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    command: str


class CommandExecutor:
    """Utility for executing shell commands with proper error handling."""

    def __init__(self, default_timeout: int = 300):
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(__name__)

    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = True
    ) -> CommandResult:
        """
        Execute a shell command asynchronously.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            cwd: Working directory
            env: Environment variables
            shell: Whether to use shell
            
        Returns:
            CommandResult with execution details
        """
        timeout = timeout or self.default_timeout
        start_time = asyncio.get_event_loop().time()
        
        self.logger.info(f"Executing command: {command}")
        
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            success = process.returncode == 0
            
            if success:
                self.logger.info(f"Command completed successfully in {execution_time:.2f}s")
            else:
                self.logger.error(f"Command failed with exit code {process.returncode}")
            
            return CommandResult(
                success=success,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                execution_time=execution_time,
                command=command
            )
            
        except asyncio.TimeoutError:
            self.logger.error(f"Command timed out after {timeout} seconds")
            
            # Kill the process if it's still running
            try:
                process.kill()
                await process.wait()
            except:
                pass
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                execution_time=execution_time,
                command=command
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"Command execution failed: {e}")
            
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                command=command
            )

    async def execute_multiple(
        self,
        commands: List[str],
        stop_on_failure: bool = True,
        **kwargs
    ) -> List[CommandResult]:
        """
        Execute multiple commands in sequence.
        
        Args:
            commands: List of commands to execute
            stop_on_failure: Whether to stop on first failure
            **kwargs: Additional arguments for execute()
            
        Returns:
            List of CommandResult objects
        """
        results = []
        
        for command in commands:
            result = await self.execute(command, **kwargs)
            results.append(result)
            
            if not result.success and stop_on_failure:
                self.logger.error(f"Stopping execution due to failure: {command}")
                break
        
        return results

    async def execute_parallel(
        self,
        commands: List[str],
        max_concurrent: int = 4,
        **kwargs
    ) -> List[CommandResult]:
        """
        Execute multiple commands in parallel.
        
        Args:
            commands: List of commands to execute
            max_concurrent: Maximum number of concurrent executions
            **kwargs: Additional arguments for execute()
            
        Returns:
            List of CommandResult objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(command: str) -> CommandResult:
            async with semaphore:
                return await self.execute(command, **kwargs)
        
        tasks = [execute_with_semaphore(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed CommandResult objects
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(CommandResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=str(result),
                    execution_time=0,
                    command=commands[i]
                ))
            else:
                processed_results.append(result)
        
        return processed_results

