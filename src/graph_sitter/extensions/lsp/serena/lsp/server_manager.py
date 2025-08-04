"""
Serena LSP Server Management

This module provides server management capabilities for Serena LSP servers,
including server discovery, configuration, lifecycle management, and health monitoring.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
import psutil

from .client import SerenaLSPClient, ConnectionType

logger = logging.getLogger(__name__)


class ServerStatus(Enum):
    """Server status states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ServerConfig:
    """Configuration for a Serena LSP server."""
    name: str
    command: List[str]
    working_directory: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    connection_type: str = ConnectionType.STDIO
    host: str = "localhost"
    port: int = 8080
    auto_start: bool = True
    auto_restart: bool = True
    max_restart_attempts: int = 3
    health_check_interval: float = 30.0
    startup_timeout: float = 60.0
    shutdown_timeout: float = 30.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'command': self.command,
            'working_directory': self.working_directory,
            'environment': self.environment,
            'connection_type': self.connection_type,
            'host': self.host,
            'port': self.port,
            'auto_start': self.auto_start,
            'auto_restart': self.auto_restart,
            'max_restart_attempts': self.max_restart_attempts,
            'health_check_interval': self.health_check_interval,
            'startup_timeout': self.startup_timeout,
            'shutdown_timeout': self.shutdown_timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ServerInfo:
    """Information about a running server."""
    config: ServerConfig
    status: ServerStatus
    process_id: Optional[int] = None
    start_time: Optional[float] = None
    last_health_check: Optional[float] = None
    restart_count: int = 0
    error_message: Optional[str] = None
    client: Optional[SerenaLSPClient] = None
    
    @property
    def uptime(self) -> Optional[float]:
        """Get server uptime in seconds."""
        if self.start_time:
            return time.time() - self.start_time
        return None
    
    @property
    def is_healthy(self) -> bool:
        """Check if server is healthy."""
        return (
            self.status == ServerStatus.RUNNING and
            self.process_id is not None and
            self._is_process_running()
        )
    
    def _is_process_running(self) -> bool:
        """Check if the process is still running."""
        if not self.process_id:
            return False
        
        try:
            process = psutil.Process(self.process_id)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False


class SerenaServerManager:
    """
    Comprehensive server management for Serena LSP servers.
    
    Features:
    - Server discovery and configuration
    - Lifecycle management (start, stop, restart)
    - Health monitoring and auto-recovery
    - Multiple server support
    - Configuration persistence
    - Resource monitoring
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or os.path.expanduser("~/.serena/servers"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Server registry
        self._servers: Dict[str, ServerInfo] = {}
        self._server_configs: Dict[str, ServerConfig] = {}
        
        # Monitoring
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._status_listeners: List[Callable[[str, ServerStatus], None]] = []
        
        # Load existing configurations
        self._load_configurations()
    
    def register_server(self, config: ServerConfig) -> bool:
        """
        Register a new server configuration.
        
        Args:
            config: Server configuration
            
        Returns:
            True if registration successful
        """
        try:
            self._server_configs[config.name] = config
            self._servers[config.name] = ServerInfo(
                config=config,
                status=ServerStatus.STOPPED
            )
            
            # Save configuration
            self._save_configuration(config)
            
            logger.info(f"Registered server: {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering server {config.name}: {e}")
            return False
    
    def unregister_server(self, server_name: str) -> bool:
        """
        Unregister a server.
        
        Args:
            server_name: Name of server to unregister
            
        Returns:
            True if unregistration successful
        """
        try:
            # Stop server if running
            if server_name in self._servers:
                asyncio.create_task(self.stop_server(server_name))
            
            # Remove from registry
            self._servers.pop(server_name, None)
            self._server_configs.pop(server_name, None)
            
            # Remove configuration file
            config_file = self.config_dir / f"{server_name}.json"
            if config_file.exists():
                config_file.unlink()
            
            logger.info(f"Unregistered server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering server {server_name}: {e}")
            return False
    
    async def start_server(self, server_name: str) -> bool:
        """
        Start a server.
        
        Args:
            server_name: Name of server to start
            
        Returns:
            True if start successful
        """
        if server_name not in self._servers:
            logger.error(f"Server not found: {server_name}")
            return False
        
        server_info = self._servers[server_name]
        config = server_info.config
        
        if server_info.status == ServerStatus.RUNNING:
            logger.info(f"Server {server_name} is already running")
            return True
        
        try:
            # Update status
            await self._update_server_status(server_name, ServerStatus.STARTING)
            
            # Create and configure client
            client = SerenaLSPClient(
                server_command=config.command,
                server_host=config.host,
                server_port=config.port,
                connection_type=config.connection_type,
                auto_reconnect=config.auto_restart
            )
            
            # Connect to server
            success = await asyncio.wait_for(
                client.connect(),
                timeout=config.startup_timeout
            )
            
            if success:
                # Update server info
                server_info.client = client
                server_info.start_time = time.time()
                server_info.restart_count = 0
                server_info.error_message = None
                
                # Get process ID if available
                if hasattr(client, '_server_process') and client._server_process:
                    server_info.process_id = client._server_process.pid
                
                await self._update_server_status(server_name, ServerStatus.RUNNING)
                
                # Start health monitoring
                self._start_health_monitoring(server_name)
                
                logger.info(f"Successfully started server: {server_name}")
                return True
            else:
                await self._update_server_status(server_name, ServerStatus.ERROR)
                server_info.error_message = "Failed to connect to server"
                return False
                
        except asyncio.TimeoutError:
            await self._update_server_status(server_name, ServerStatus.ERROR)
            server_info.error_message = "Server startup timeout"
            logger.error(f"Server {server_name} startup timeout")
            return False
            
        except Exception as e:
            await self._update_server_status(server_name, ServerStatus.ERROR)
            server_info.error_message = str(e)
            logger.error(f"Error starting server {server_name}: {e}")
            return False
    
    async def stop_server(self, server_name: str) -> bool:
        """
        Stop a server.
        
        Args:
            server_name: Name of server to stop
            
        Returns:
            True if stop successful
        """
        if server_name not in self._servers:
            logger.error(f"Server not found: {server_name}")
            return False
        
        server_info = self._servers[server_name]
        
        if server_info.status == ServerStatus.STOPPED:
            logger.info(f"Server {server_name} is already stopped")
            return True
        
        try:
            # Update status
            await self._update_server_status(server_name, ServerStatus.STOPPING)
            
            # Stop health monitoring
            self._stop_health_monitoring(server_name)
            
            # Disconnect client
            if server_info.client:
                await asyncio.wait_for(
                    server_info.client.disconnect(),
                    timeout=server_info.config.shutdown_timeout
                )
                server_info.client = None
            
            # Clean up server info
            server_info.process_id = None
            server_info.start_time = None
            server_info.last_health_check = None
            server_info.error_message = None
            
            await self._update_server_status(server_name, ServerStatus.STOPPED)
            
            logger.info(f"Successfully stopped server: {server_name}")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Server {server_name} shutdown timeout")
            # Force kill if needed
            await self._force_kill_server(server_name)
            return True
            
        except Exception as e:
            logger.error(f"Error stopping server {server_name}: {e}")
            await self._update_server_status(server_name, ServerStatus.ERROR)
            return False
    
    async def restart_server(self, server_name: str) -> bool:
        """
        Restart a server.
        
        Args:
            server_name: Name of server to restart
            
        Returns:
            True if restart successful
        """
        logger.info(f"Restarting server: {server_name}")
        
        # Stop server
        stop_success = await self.stop_server(server_name)
        if not stop_success:
            logger.error(f"Failed to stop server {server_name} for restart")
            return False
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Start server
        start_success = await self.start_server(server_name)
        if start_success:
            # Increment restart count
            if server_name in self._servers:
                self._servers[server_name].restart_count += 1
        
        return start_success
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """
        Start all registered servers with auto_start enabled.
        
        Returns:
            Dictionary mapping server names to start success status
        """
        results = {}
        
        for server_name, config in self._server_configs.items():
            if config.auto_start:
                results[server_name] = await self.start_server(server_name)
            else:
                results[server_name] = None  # Not started (auto_start disabled)
        
        return results
    
    async def stop_all_servers(self) -> Dict[str, bool]:
        """
        Stop all running servers.
        
        Returns:
            Dictionary mapping server names to stop success status
        """
        results = {}
        
        for server_name in self._servers:
            results[server_name] = await self.stop_server(server_name)
        
        return results
    
    def get_server_info(self, server_name: str) -> Optional[ServerInfo]:
        """Get information about a server."""
        return self._servers.get(server_name)
    
    def get_all_servers(self) -> Dict[str, ServerInfo]:
        """Get information about all servers."""
        return self._servers.copy()
    
    def get_running_servers(self) -> Dict[str, ServerInfo]:
        """Get information about running servers."""
        return {
            name: info for name, info in self._servers.items()
            if info.status == ServerStatus.RUNNING
        }
    
    def get_server_client(self, server_name: str) -> Optional[SerenaLSPClient]:
        """Get LSP client for a server."""
        server_info = self._servers.get(server_name)
        return server_info.client if server_info else None
    
    def add_status_listener(self, listener: Callable[[str, ServerStatus], None]):
        """Add listener for server status changes."""
        self._status_listeners.append(listener)
    
    def remove_status_listener(self, listener: Callable[[str, ServerStatus], None]):
        """Remove status listener."""
        if listener in self._status_listeners:
            self._status_listeners.remove(listener)
    
    def discover_servers(self, search_paths: Optional[List[str]] = None) -> List[ServerConfig]:
        """
        Discover available Serena LSP servers.
        
        Args:
            search_paths: Paths to search for servers
            
        Returns:
            List of discovered server configurations
        """
        discovered = []
        
        if not search_paths:
            search_paths = [
                "/usr/local/bin",
                "/usr/bin",
                os.path.expanduser("~/.local/bin"),
                os.path.expanduser("~/bin")
            ]
        
        # Common server executable names
        server_names = [
            "serena-lsp-server",
            "serena-server",
            "serena-language-server",
            "serena"
        ]
        
        for search_path in search_paths:
            path = Path(search_path)
            if not path.exists():
                continue
            
            for server_name in server_names:
                server_path = path / server_name
                if server_path.exists() and server_path.is_file():
                    # Check if executable
                    if os.access(server_path, os.X_OK):
                        config = ServerConfig(
                            name=f"discovered_{server_name}",
                            command=[str(server_path)]
                        )
                        discovered.append(config)
        
        return discovered
    
    def _start_health_monitoring(self, server_name: str):
        """Start health monitoring for a server."""
        if server_name in self._monitoring_tasks:
            return  # Already monitoring
        
        task = asyncio.create_task(self._health_monitor_loop(server_name))
        self._monitoring_tasks[server_name] = task
    
    def _stop_health_monitoring(self, server_name: str):
        """Stop health monitoring for a server."""
        task = self._monitoring_tasks.pop(server_name, None)
        if task:
            task.cancel()
    
    async def _health_monitor_loop(self, server_name: str):
        """Health monitoring loop for a server."""
        server_info = self._servers.get(server_name)
        if not server_info:
            return
        
        config = server_info.config
        
        try:
            while server_info.status == ServerStatus.RUNNING:
                # Perform health check
                is_healthy = await self._perform_health_check(server_name)
                server_info.last_health_check = time.time()
                
                if not is_healthy:
                    logger.warning(f"Health check failed for server {server_name}")
                    
                    if config.auto_restart and server_info.restart_count < config.max_restart_attempts:
                        logger.info(f"Auto-restarting unhealthy server: {server_name}")
                        await self.restart_server(server_name)
                        return  # Exit this monitoring loop, new one will start
                    else:
                        await self._update_server_status(server_name, ServerStatus.ERROR)
                        server_info.error_message = "Health check failed"
                        return
                
                # Wait for next check
                await asyncio.sleep(config.health_check_interval)
                
        except asyncio.CancelledError:
            logger.debug(f"Health monitoring cancelled for server {server_name}")
        except Exception as e:
            logger.error(f"Error in health monitoring for {server_name}: {e}")
    
    async def _perform_health_check(self, server_name: str) -> bool:
        """Perform health check on a server."""
        server_info = self._servers.get(server_name)
        if not server_info or not server_info.client:
            return False
        
        try:
            # Check if client is connected
            if not server_info.client.is_connected:
                return False
            
            # Try to send a simple request
            # This would be a ping or capabilities request
            # For now, we'll just check connection status
            return True
            
        except Exception as e:
            logger.error(f"Health check error for {server_name}: {e}")
            return False
    
    async def _force_kill_server(self, server_name: str):
        """Force kill a server process."""
        server_info = self._servers.get(server_name)
        if not server_info or not server_info.process_id:
            return
        
        try:
            process = psutil.Process(server_info.process_id)
            process.terminate()
            
            # Wait for termination
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                process.kill()
            
            logger.info(f"Force killed server process: {server_name}")
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error force killing server {server_name}: {e}")
    
    async def _update_server_status(self, server_name: str, status: ServerStatus):
        """Update server status and notify listeners."""
        if server_name in self._servers:
            old_status = self._servers[server_name].status
            self._servers[server_name].status = status
            
            # Notify listeners
            for listener in self._status_listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(server_name, status)
                    else:
                        listener(server_name, status)
                except Exception as e:
                    logger.error(f"Error in status listener: {e}")
            
            logger.debug(f"Server {server_name} status: {old_status.value} -> {status.value}")
    
    def _load_configurations(self):
        """Load server configurations from disk."""
        try:
            for config_file in self.config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        data = json.load(f)
                    
                    config = ServerConfig.from_dict(data)
                    self._server_configs[config.name] = config
                    self._servers[config.name] = ServerInfo(
                        config=config,
                        status=ServerStatus.STOPPED
                    )
                    
                    logger.debug(f"Loaded server configuration: {config.name}")
                    
                except Exception as e:
                    logger.error(f"Error loading config {config_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
    
    def _save_configuration(self, config: ServerConfig):
        """Save server configuration to disk."""
        try:
            config_file = self.config_dir / f"{config.name}.json"
            with open(config_file, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            logger.debug(f"Saved server configuration: {config.name}")
            
        except Exception as e:
            logger.error(f"Error saving config for {config.name}: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        # Stop all servers
        await self.stop_all_servers()
        
        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        self._monitoring_tasks.clear()
        self._status_listeners.clear()

