"""
Comprehensive LSP Serena Integration

This module provides the main integration point for LSP-based Serena analysis,
combining all LSP components into a unified interface for comprehensive
code error retrieval and analysis.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union

from .lsp import (
    SerenaLSPClient,
    SerenaServerManager,
    ServerConfig,
    ErrorRetriever,
    ComprehensiveErrorList,
    CodeError,
    ErrorSeverity,
    ErrorCategory,
    RealTimeDiagnostics,
    DiagnosticFilter,
    DiagnosticStats,
    ConnectionType
)

logger = logging.getLogger(__name__)


class SerenaLSPIntegration:
    """
    Comprehensive LSP integration for Serena analysis.
    
    This class provides a unified interface for:
    - LSP server management
    - Real-time error retrieval
    - Comprehensive code analysis
    - Live error monitoring
    - Performance optimization
    
    Features:
    - Automatic server discovery and management
    - Multiple server support
    - Real-time diagnostics
    - Comprehensive error analysis
    - Performance monitoring
    - Event-driven architecture
    """
    
    def __init__(self, 
                 config_dir: Optional[str] = None,
                 auto_discover_servers: bool = True,
                 enable_real_time_diagnostics: bool = True):
        
        # Core components
        self.server_manager = SerenaServerManager(config_dir)
        self.real_time_diagnostics = RealTimeDiagnostics() if enable_real_time_diagnostics else None
        
        # State tracking
        self._active_clients: Dict[str, SerenaLSPClient] = {}
        self._error_cache: Dict[str, ComprehensiveErrorList] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        # Event handlers
        self._error_listeners: List[Callable[[List[CodeError]], None]] = []
        self._stats_listeners: List[Callable[[DiagnosticStats], None]] = []
        self._connection_listeners: List[Callable[[str, bool], None]] = []
        
        # Configuration
        self.auto_discover_servers = auto_discover_servers
        self.enable_real_time_diagnostics = enable_real_time_diagnostics
        
        # Setup server manager listeners
        self.server_manager.add_status_listener(self._handle_server_status_change)
        
        # Setup diagnostics if enabled
        if self.real_time_diagnostics:
            self.real_time_diagnostics.add_error_handler(self._handle_diagnostic_error)
            self.real_time_diagnostics.add_stats_handler(self._handle_diagnostic_stats)
        
        # Initialize
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize the LSP integration.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing Serena LSP integration...")
            
            # Discover servers if enabled
            if self.auto_discover_servers:
                await self._discover_and_register_servers()
            
            # Start configured servers
            start_results = await self.server_manager.start_all_servers()
            
            # Setup active clients
            for server_name, success in start_results.items():
                if success:
                    client = self.server_manager.get_server_client(server_name)
                    if client:
                        self._active_clients[server_name] = client
                        
                        # Setup client event handlers
                        client.add_error_listener(self._handle_client_errors)
                        client.add_connection_listener(
                            lambda connected, name=server_name: 
                            self._handle_client_connection(name, connected)
                        )
            
            # Start real-time monitoring if we have active clients
            if self._active_clients and self.real_time_diagnostics:
                await self._start_real_time_monitoring()
            
            self._initialized = True
            logger.info(f"LSP integration initialized with {len(self._active_clients)} active servers")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing LSP integration: {e}")
            return False
    
    async def get_comprehensive_errors(self, 
                                     server_name: Optional[str] = None,
                                     include_context: bool = True,
                                     include_suggestions: bool = True,
                                     max_errors: Optional[int] = None,
                                     severity_filter: Optional[List[ErrorSeverity]] = None,
                                     use_cache: bool = True) -> ComprehensiveErrorList:
        """
        Get comprehensive error list from Serena LSP servers.
        
        Args:
            server_name: Specific server to query (None for all servers)
            include_context: Include error context information
            include_suggestions: Include fix suggestions
            max_errors: Maximum number of errors to retrieve
            severity_filter: Filter by error severities
            use_cache: Use cached results if available
            
        Returns:
            Comprehensive error list with analysis
        """
        if not self._initialized:
            raise RuntimeError("LSP integration not initialized")
        
        # Check cache first
        cache_key = f"{server_name}_{include_context}_{include_suggestions}_{max_errors}_{severity_filter}"
        if use_cache and cache_key in self._error_cache:
            cached_result = self._error_cache[cache_key]
            # Return cached result if recent (within 30 seconds)
            if time.time() - cached_result.analysis_timestamp < 30:
                return cached_result
        
        start_time = time.time()
        combined_errors = ComprehensiveErrorList()
        
        # Determine which servers to query
        servers_to_query = []
        if server_name:
            if server_name in self._active_clients:
                servers_to_query = [server_name]
            else:
                logger.warning(f"Server {server_name} not found or not active")
                return combined_errors
        else:
            servers_to_query = list(self._active_clients.keys())
        
        # Query servers concurrently
        tasks = []
        for srv_name in servers_to_query:
            client = self._active_clients[srv_name]
            task = asyncio.create_task(
                client.get_comprehensive_errors(
                    include_context=include_context,
                    include_suggestions=include_suggestions,
                    max_errors=max_errors,
                    severity_filter=severity_filter
                )
            )
            tasks.append((srv_name, task))
        
        # Collect results
        for srv_name, task in tasks:
            try:
                result = await task
                combined_errors.add_errors(result.errors)
                logger.debug(f"Retrieved {len(result.errors)} errors from server {srv_name}")
            except Exception as e:
                logger.error(f"Error retrieving errors from server {srv_name}: {e}")
        
        # Update metadata
        combined_errors.analysis_duration = time.time() - start_time
        combined_errors.analysis_timestamp = time.time()
        
        # Cache result
        self._error_cache[cache_key] = combined_errors
        
        # Update real-time diagnostics
        if self.real_time_diagnostics:
            await self.real_time_diagnostics.processor.process_errors(combined_errors.errors)
        
        logger.info(f"Retrieved {combined_errors.total_count} total errors from {len(servers_to_query)} servers")
        return combined_errors
    
    async def analyze_file(self, 
                          file_path: str,
                          content: Optional[str] = None,
                          server_name: Optional[str] = None) -> List[CodeError]:
        """
        Analyze a specific file for errors.
        
        Args:
            file_path: Path to file to analyze
            content: File content (if not provided, will be read from disk)
            server_name: Specific server to use (None for best available)
            
        Returns:
            List of errors found in the file
        """
        if not self._initialized:
            raise RuntimeError("LSP integration not initialized")
        
        # Select server
        client = self._select_best_client(server_name)
        if not client:
            logger.error("No active LSP clients available")
            return []
        
        try:
            errors = await client.get_file_errors(file_path)
            
            # Update real-time diagnostics
            if self.real_time_diagnostics:
                await self.real_time_diagnostics.processor.process_errors(errors)
            
            return errors
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []
    
    async def analyze_codebase(self, 
                              root_path: str,
                              file_patterns: Optional[List[str]] = None,
                              exclude_patterns: Optional[List[str]] = None,
                              server_name: Optional[str] = None) -> ComprehensiveErrorList:
        """
        Analyze entire codebase for errors.
        
        Args:
            root_path: Root directory path
            file_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            server_name: Specific server to use (None for best available)
            
        Returns:
            Comprehensive analysis of the codebase
        """
        if not self._initialized:
            raise RuntimeError("LSP integration not initialized")
        
        # Select server
        client = self._select_best_client(server_name)
        if not client:
            logger.error("No active LSP clients available")
            return ComprehensiveErrorList()
        
        try:
            result = await client.analyze_codebase(
                root_path=root_path,
                file_patterns=file_patterns,
                exclude_patterns=exclude_patterns
            )
            
            # Update real-time diagnostics
            if self.real_time_diagnostics:
                await self.real_time_diagnostics.processor.process_errors(result.errors)
            
            logger.info(f"Analyzed codebase: {result.total_count} errors found")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing codebase {root_path}: {e}")
            return ComprehensiveErrorList()
    
    def get_real_time_stats(self) -> Optional[DiagnosticStats]:
        """Get real-time diagnostic statistics."""
        if not self.real_time_diagnostics:
            return None
        
        return self.real_time_diagnostics.get_current_stats()
    
    def get_trend_analysis(self, **kwargs) -> Optional[Dict[str, Any]]:
        """Get trend analysis from real-time diagnostics."""
        if not self.real_time_diagnostics:
            return None
        
        return self.real_time_diagnostics.get_trend_analysis(**kwargs)
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive diagnostic report."""
        report = {
            'servers': {},
            'total_errors': 0,
            'active_servers': len(self._active_clients),
            'real_time_enabled': self.real_time_diagnostics is not None
        }
        
        # Server information
        for server_name, client in self._active_clients.items():
            server_info = self.server_manager.get_server_info(server_name)
            report['servers'][server_name] = {
                'status': server_info.status.value if server_info else 'unknown',
                'connected': client.is_connected,
                'uptime': server_info.uptime if server_info else None
            }
        
        # Real-time diagnostics
        if self.real_time_diagnostics:
            rt_report = self.real_time_diagnostics.get_comprehensive_report()
            report.update(rt_report)
        
        # Cache statistics
        report['cache_entries'] = len(self._error_cache)
        
        return report
    
    def add_error_listener(self, listener: Callable[[List[CodeError]], None]):
        """Add listener for error updates."""
        self._error_listeners.append(listener)
    
    def add_stats_listener(self, listener: Callable[[DiagnosticStats], None]):
        """Add listener for statistics updates."""
        self._stats_listeners.append(listener)
    
    def add_connection_listener(self, listener: Callable[[str, bool], None]):
        """Add listener for connection status changes."""
        self._connection_listeners.append(listener)
    
    def add_diagnostic_filter(self, filter_config: DiagnosticFilter):
        """Add diagnostic filter for real-time processing."""
        if self.real_time_diagnostics:
            self.real_time_diagnostics.add_filter(filter_config)
    
    async def refresh_analysis(self, server_name: Optional[str] = None) -> bool:
        """
        Refresh analysis on servers.
        
        Args:
            server_name: Specific server to refresh (None for all)
            
        Returns:
            True if refresh successful
        """
        if not self._initialized:
            return False
        
        servers_to_refresh = []
        if server_name:
            if server_name in self._active_clients:
                servers_to_refresh = [server_name]
        else:
            servers_to_refresh = list(self._active_clients.keys())
        
        success_count = 0
        for srv_name in servers_to_refresh:
            client = self._active_clients[srv_name]
            try:
                success = await client.refresh_analysis()
                if success:
                    success_count += 1
                    # Clear cache for this server
                    self._clear_server_cache(srv_name)
            except Exception as e:
                logger.error(f"Error refreshing analysis on server {srv_name}: {e}")
        
        return success_count > 0
    
    async def shutdown(self):
        """Shutdown the LSP integration."""
        logger.info("Shutting down Serena LSP integration...")
        
        # Stop monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        
        # Cleanup real-time diagnostics
        if self.real_time_diagnostics:
            await self.real_time_diagnostics.cleanup()
        
        # Shutdown server manager
        await self.server_manager.cleanup()
        
        # Clear state
        self._active_clients.clear()
        self._error_cache.clear()
        self._monitoring_tasks.clear()
        self._error_listeners.clear()
        self._stats_listeners.clear()
        self._connection_listeners.clear()
        
        self._initialized = False
        logger.info("LSP integration shutdown complete")
    
    async def _discover_and_register_servers(self):
        """Discover and register available Serena servers."""
        logger.info("Discovering Serena LSP servers...")
        
        discovered_servers = self.server_manager.discover_servers()
        
        for config in discovered_servers:
            success = self.server_manager.register_server(config)
            if success:
                logger.info(f"Registered discovered server: {config.name}")
            else:
                logger.warning(f"Failed to register discovered server: {config.name}")
        
        # Also register default configurations
        default_configs = [
            ServerConfig(
                name="serena_stdio",
                command=["serena-lsp-server"],
                connection_type=ConnectionType.STDIO
            ),
            ServerConfig(
                name="serena_tcp",
                command=["serena-lsp-server", "--tcp", "--port", "8080"],
                connection_type=ConnectionType.TCP,
                port=8080
            )
        ]
        
        for config in default_configs:
            if config.name not in self.server_manager._server_configs:
                self.server_manager.register_server(config)
                logger.debug(f"Registered default server config: {config.name}")
    
    async def _start_real_time_monitoring(self):
        """Start real-time error monitoring."""
        if not self.real_time_diagnostics:
            return
        
        logger.info("Starting real-time error monitoring...")
        
        # Create monitoring task for each active client
        for server_name, client in self._active_clients.items():
            task = asyncio.create_task(self._monitor_client_errors(server_name, client))
            self._monitoring_tasks[server_name] = task
    
    async def _monitor_client_errors(self, server_name: str, client: SerenaLSPClient):
        """Monitor errors from a specific client."""
        try:
            while client.is_connected:
                try:
                    # Get current errors
                    error_list = await client.get_comprehensive_errors(
                        include_context=False,  # Reduce overhead for monitoring
                        include_suggestions=False
                    )
                    
                    # Process with real-time diagnostics
                    if self.real_time_diagnostics:
                        await self.real_time_diagnostics.processor.process_errors(error_list.errors)
                    
                    # Wait before next poll
                    await asyncio.sleep(10)  # Poll every 10 seconds
                    
                except Exception as e:
                    logger.error(f"Error monitoring client {server_name}: {e}")
                    await asyncio.sleep(30)  # Wait longer on error
                    
        except asyncio.CancelledError:
            logger.debug(f"Monitoring cancelled for client {server_name}")
        except Exception as e:
            logger.error(f"Unexpected error in client monitoring {server_name}: {e}")
    
    def _select_best_client(self, preferred_server: Optional[str] = None) -> Optional[SerenaLSPClient]:
        """Select the best available client."""
        if preferred_server and preferred_server in self._active_clients:
            client = self._active_clients[preferred_server]
            if client.is_connected:
                return client
        
        # Find any connected client
        for client in self._active_clients.values():
            if client.is_connected:
                return client
        
        return None
    
    def _clear_server_cache(self, server_name: str):
        """Clear cache entries for a specific server."""
        keys_to_remove = [
            key for key in self._error_cache.keys()
            if key.startswith(f"{server_name}_")
        ]
        
        for key in keys_to_remove:
            del self._error_cache[key]
    
    async def _handle_server_status_change(self, server_name: str, status):
        """Handle server status changes."""
        logger.debug(f"Server {server_name} status changed to {status.value}")
        
        # Update active clients based on status
        if status.value == "running":
            client = self.server_manager.get_server_client(server_name)
            if client:
                self._active_clients[server_name] = client
                
                # Setup client event handlers
                client.add_error_listener(self._handle_client_errors)
                client.add_connection_listener(
                    lambda connected, name=server_name: 
                    self._handle_client_connection(name, connected)
                )
                
                # Start monitoring if real-time diagnostics enabled
                if self.real_time_diagnostics:
                    task = asyncio.create_task(self._monitor_client_errors(server_name, client))
                    self._monitoring_tasks[server_name] = task
        
        elif status.value in ["stopped", "error"]:
            # Remove from active clients
            self._active_clients.pop(server_name, None)
            
            # Cancel monitoring task
            task = self._monitoring_tasks.pop(server_name, None)
            if task:
                task.cancel()
            
            # Clear cache for this server
            self._clear_server_cache(server_name)
    
    async def _handle_client_errors(self, errors: List[CodeError]):
        """Handle errors from LSP clients."""
        # Notify error listeners
        for listener in self._error_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(errors)
                else:
                    listener(errors)
            except Exception as e:
                logger.error(f"Error in error listener: {e}")
    
    async def _handle_client_connection(self, server_name: str, connected: bool):
        """Handle client connection status changes."""
        logger.debug(f"Client {server_name} connection status: {connected}")
        
        # Notify connection listeners
        for listener in self._connection_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(server_name, connected)
                else:
                    listener(server_name, connected)
            except Exception as e:
                logger.error(f"Error in connection listener: {e}")
    
    async def _handle_diagnostic_error(self, error: CodeError):
        """Handle diagnostic errors from real-time system."""
        # This could trigger additional processing or notifications
        pass
    
    async def _handle_diagnostic_stats(self, stats: DiagnosticStats):
        """Handle diagnostic statistics updates."""
        # Notify stats listeners
        for listener in self._stats_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(stats)
                else:
                    listener(stats)
            except Exception as e:
                logger.error(f"Error in stats listener: {e}")


# Convenience functions for easy integration

async def create_serena_lsp_integration(**kwargs) -> SerenaLSPIntegration:
    """
    Create and initialize a Serena LSP integration.
    
    Returns:
        Initialized LSP integration instance
    """
    integration = SerenaLSPIntegration(**kwargs)
    success = await integration.initialize()
    
    if not success:
        await integration.shutdown()
        raise RuntimeError("Failed to initialize Serena LSP integration")
    
    return integration


async def get_comprehensive_code_errors(root_path: str, **kwargs) -> ComprehensiveErrorList:
    """
    Quick function to get comprehensive code errors from a codebase.
    
    Args:
        root_path: Root path of codebase to analyze
        **kwargs: Additional arguments for analysis
        
    Returns:
        Comprehensive error list
    """
    integration = await create_serena_lsp_integration()
    
    try:
        return await integration.analyze_codebase(root_path, **kwargs)
    finally:
        await integration.shutdown()


async def analyze_file_errors(file_path: str, **kwargs) -> List[CodeError]:
    """
    Quick function to analyze a single file for errors.
    
    Args:
        file_path: Path to file to analyze
        **kwargs: Additional arguments for analysis
        
    Returns:
        List of errors found in the file
    """
    integration = await create_serena_lsp_integration()
    
    try:
        return await integration.analyze_file(file_path, **kwargs)
    finally:
        await integration.shutdown()

