"""
Serena Protocol Extensions for Graph-Sitter LSP

This module provides protocol extensions for Serena LSP communication,
including custom message handlers and error retrieval protocols.
"""

import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from graph_sitter.shared.logging.get_logger import get_logger
from .serena_bridge import ErrorInfo, SerenaLSPBridge, ErrorType

# Import DiagnosticSeverity with fallback
try:
    from solidlsp.ls_types import DiagnosticSeverity
except ImportError:
    from enum import IntEnum
    class DiagnosticSeverity(IntEnum):
        ERROR = 1
        WARNING = 2
        INFORMATION = 3
        HINT = 4

logger = get_logger(__name__)


class SerenaProtocolHandler:
    """
    Protocol handler for Serena-specific LSP extensions.
    
    This class handles custom LSP messages and provides structured
    communication with Serena LSP servers.
    """
    
    def __init__(self, bridge: SerenaLSPBridge):
        self.bridge = bridge
        self.message_handlers: Dict[str, callable] = {}
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup message handlers for Serena protocol extensions."""
        self.message_handlers.update({
            'serena/getRuntimeErrors': self._handle_get_runtime_errors,
            'serena/getStaticErrors': self._handle_get_static_errors,
            'serena/getAllErrors': self._handle_get_all_errors,
            'serena/getErrorSummary': self._handle_get_error_summary,
            'serena/clearErrors': self._handle_clear_errors,
            'serena/refreshDiagnostics': self._handle_refresh_diagnostics,
            'serena/configureCollection': self._handle_configure_collection,
            'serena/getPerformanceStats': self._handle_get_performance_stats,
            'serena/getFileErrors': self._handle_get_file_errors,
        })
    
    def handle_message(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle incoming Serena protocol messages.
        
        Args:
            method: The LSP method name
            params: Optional parameters for the method
            
        Returns:
            Response dictionary with result or error
        """
        try:
            if method in self.message_handlers:
                handler = self.message_handlers[method]
                result = handler(params or {})
                return {
                    'result': result,
                    'error': None
                }
            else:
                return {
                    'result': None,
                    'error': {
                        'code': -32601,  # Method not found
                        'message': f'Unknown method: {method}'
                    }
                }
        
        except Exception as e:
            logger.error(f"Error handling Serena protocol message {method}: {e}")
            return {
                'result': None,
                'error': {
                    'code': -32603,  # Internal error
                    'message': f'Internal error: {str(e)}'
                }
            }
    
    def _handle_get_runtime_errors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle serena/getRuntimeErrors request."""
        file_path = params.get('filePath')
        
        if file_path:
            errors = [error for error in self.bridge.get_runtime_errors() 
                     if error.file_path == file_path]
        else:
            errors = self.bridge.get_runtime_errors()
        
        return {
            'errors': [self._serialize_error(error) for error in errors],
            'count': len(errors),
            'timestamp': time.time()
        }
    
    def _handle_get_static_errors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle serena/getStaticErrors request."""
        file_path = params.get('filePath')
        
        if file_path:
            errors = [error for error in self.bridge.get_static_errors() 
                     if error.file_path == file_path]
        else:
            errors = self.bridge.get_static_errors()
        
        return {
            'errors': [self._serialize_error(error) for error in errors],
            'count': len(errors),
            'timestamp': time.time()
        }
    
    def _handle_get_all_errors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle serena/getAllErrors request."""
        file_path = params.get('filePath')
        include_context = params.get('includeContext', True)
        include_suggestions = params.get('includeSuggestions', True)
        
        if file_path:
            errors = self.bridge.get_file_errors(file_path)
        else:
            errors = self.bridge.get_all_errors()
        
        # Filter based on parameters
        serialized_errors = []
        for error in errors:
            serialized = self._serialize_error(error, include_context, include_suggestions)
            serialized_errors.append(serialized)
        
        return {
            'errors': serialized_errors,
            'count': len(errors),
            'timestamp': time.time(),
            'bridge_status': {
                'initialized': self.bridge.is_initialized,
                'runtime_collection_active': (
                    self.bridge.runtime_collector.is_active 
                    if self.bridge.runtime_collector else False
                ),
                'serena_available': hasattr(self.bridge, 'serena_server') and self.bridge.serena_server is not None
            }
        }
    
    def _handle_get_error_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle serena/getErrorSummary request."""
        return self.bridge.get_error_summary()
    
    def _handle_clear_errors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle serena/clearErrors request."""
        error_type = params.get('type', 'all')  # 'runtime', 'static', or 'all'
        
        if error_type == 'runtime':
            self.bridge.clear_runtime_errors()
        elif error_type == 'static':
            self.bridge.clear_static_errors()
        else:
            self.bridge.clear_all_errors()
        
        return {
            'success': True,
            'cleared': error_type,
            'timestamp': time.time()
        }
    
    def _handle_refresh_diagnostics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle serena/refreshDiagnostics request."""
        self.bridge.refresh_diagnostics()
        
        return {
            'success': True,
            'timestamp': time.time(),
            'error_count': len(self.bridge.get_all_errors())
        }
    
    def _handle_configure_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle serena/configureCollection request."""
        try:
            # Extract configuration parameters
            config_params = {}
            
            if 'maxErrors' in params:
                config_params['max_errors'] = params['maxErrors']
            if 'maxStackDepth' in params:
                config_params['max_stack_depth'] = params['maxStackDepth']
            if 'collectVariables' in params:
                config_params['collect_variables'] = params['collectVariables']
            if 'variableMaxLength' in params:
                config_params['variable_max_length'] = params['variableMaxLength']
            
            self.bridge.configure_runtime_collection(**config_params)
            
            return {
                'success': True,
                'configured_params': config_params,
                'timestamp': time.time()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _handle_get_performance_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle serena/getPerformanceStats request."""
        return self.bridge.get_performance_stats()
    
    def _handle_get_file_errors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle serena/getFileErrors request."""
        file_path = params.get('filePath')
        if not file_path:
            return {
                'errors': [],
                'error': 'filePath parameter is required'
            }
        
        errors = self.bridge.get_file_errors(file_path)
        
        return {
            'errors': [self._serialize_error(error) for error in errors],
            'count': len(errors),
            'filePath': file_path,
            'timestamp': time.time()
        }
    
    def _serialize_error(self, error: ErrorInfo, include_context: bool = True, 
                        include_suggestions: bool = True) -> Dict[str, Any]:
        """
        Serialize an ErrorInfo object for protocol transmission.
        
        Args:
            error: The ErrorInfo object to serialize
            include_context: Whether to include runtime context
            include_suggestions: Whether to include fix suggestions
            
        Returns:
            Serialized error dictionary
        """
        serialized = {
            'filePath': error.file_path,
            'line': error.line,
            'character': error.character,
            'message': error.message,
            'severity': error.severity.value,
            'severityName': error.severity.name,
            'errorType': error.error_type.value,
            'errorTypeName': error.error_type.name,
            'source': error.source,
            'code': error.code,
            'endLine': error.end_line,
            'endCharacter': error.end_character,
            'isError': error.is_error,
            'isWarning': error.is_warning,
            'isHint': error.is_hint,
            'isRuntimeError': error.is_runtime_error,
            'hasRuntimeContext': error.has_runtime_context,
            'hasSuggestions': error.has_fix_suggestions
        }
        
        # Include runtime context if requested and available
        if include_context and error.runtime_context:
            context = error.runtime_context
            serialized['runtimeContext'] = {
                'exceptionType': context.exception_type,
                'stackTrace': context.stack_trace,
                'localVariables': context.local_variables,
                'globalVariables': context.global_variables,
                'executionPath': context.execution_path,
                'timestamp': context.timestamp,
                'threadId': context.thread_id,
                'processId': context.process_id
            }
        
        # Include fix suggestions if requested and available
        if include_suggestions and error.fix_suggestions:
            serialized['fixSuggestions'] = error.fix_suggestions
        
        # Include additional metadata
        if error.related_symbols:
            serialized['relatedSymbols'] = error.related_symbols
        
        if error.context_lines:
            serialized['contextLines'] = error.context_lines
        
        if error.symbol_info:
            serialized['symbolInfo'] = error.symbol_info
        
        if error.dependency_info:
            serialized['dependencyInfo'] = error.dependency_info
        
        return serialized
    
    def create_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a notification message for sending to clients.
        
        Args:
            method: The notification method name
            params: Optional parameters for the notification
            
        Returns:
            Notification message dictionary
        """
        return {
            'jsonrpc': '2.0',
            'method': method,
            'params': params or {}
        }
    
    def create_error_notification(self, error: ErrorInfo) -> Dict[str, Any]:
        """Create a notification for a new error."""
        return self.create_notification(
            'serena/errorDetected',
            {
                'error': self._serialize_error(error),
                'timestamp': time.time()
            }
        )
    
    def create_error_cleared_notification(self, error_type: str = 'all') -> Dict[str, Any]:
        """Create a notification for cleared errors."""
        return self.create_notification(
            'serena/errorsCleared',
            {
                'type': error_type,
                'timestamp': time.time()
            }
        )
    
    def create_diagnostics_updated_notification(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a notification for updated diagnostics."""
        params = {
            'timestamp': time.time(),
            'errorCount': len(self.bridge.get_all_errors())
        }
        
        if file_path:
            params['filePath'] = file_path
            params['fileErrorCount'] = len(self.bridge.get_file_errors(file_path))
        
        return self.create_notification('serena/diagnosticsUpdated', params)


class SerenaProtocolExtension:
    """
    Extension class for integrating Serena protocol with existing LSP servers.
    
    This class can be used to extend existing LSP server implementations
    with Serena-specific functionality.
    """
    
    def __init__(self, repo_path: str, enable_runtime_collection: bool = True):
        self.bridge = SerenaLSPBridge(repo_path, enable_runtime_collection)
        self.protocol_handler = SerenaProtocolHandler(self.bridge)
        self.notification_callbacks: List[callable] = []
        
        # Setup error handler to send notifications
        self.bridge.add_error_handler(self._on_error_detected)
    
    def _on_error_detected(self, error: ErrorInfo) -> None:
        """Handle new error detection by sending notifications."""
        try:
            notification = self.protocol_handler.create_error_notification(error)
            for callback in self.notification_callbacks:
                callback(notification)
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
    
    def add_notification_callback(self, callback: callable) -> None:
        """Add a callback for sending notifications to LSP clients."""
        self.notification_callbacks.append(callback)
    
    def remove_notification_callback(self, callback: callable) -> None:
        """Remove a notification callback."""
        if callback in self.notification_callbacks:
            self.notification_callbacks.remove(callback)
    
    def handle_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle LSP request with Serena extensions."""
        return self.protocol_handler.handle_message(method, params)
    
    def get_diagnostics(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get diagnostics in LSP format."""
        diagnostics = self.bridge.get_diagnostics_for_lsp(file_path)
        return [asdict(diag) for diag in diagnostics]
    
    def shutdown(self) -> None:
        """Shutdown the protocol extension."""
        self.bridge.shutdown()
        self.notification_callbacks.clear()


# Convenience functions
def create_serena_protocol_extension(repo_path: str, enable_runtime_collection: bool = True) -> SerenaProtocolExtension:
    """Create a Serena protocol extension with default configuration."""
    return SerenaProtocolExtension(repo_path, enable_runtime_collection)


def create_protocol_handler(bridge: SerenaLSPBridge) -> SerenaProtocolHandler:
    """Create a protocol handler for an existing bridge."""
    return SerenaProtocolHandler(bridge)
