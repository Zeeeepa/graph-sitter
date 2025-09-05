#!/usr/bin/env python3
"""
Comprehensive Test Suite for LSP Serena Integration

This test suite validates all aspects of the LSP integration including
protocol handling, error retrieval, server management, and real-time diagnostics.
"""

import asyncio
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Import the LSP integration components
from graph_sitter.extensions.serena.lsp_integration import (
    SerenaLSPIntegration,
    create_serena_lsp_integration,
    get_comprehensive_code_errors,
    analyze_file_errors
)

from graph_sitter.extensions.serena.lsp import (
    SerenaLSPClient,
    SerenaServerManager,
    ServerConfig,
    ErrorRetriever,
    ComprehensiveErrorList,
    CodeError,
    ErrorSeverity,
    ErrorCategory,
    ErrorLocation,
    RealTimeDiagnostics,
    DiagnosticFilter,
    DiagnosticStats,
    ConnectionType,
    ProtocolHandler,
    LSPRequest,
    LSPResponse,
    LSPNotification
)


class TestLSPProtocol:
    """Test LSP protocol implementation."""
    
    def test_protocol_handler_creation(self):
        """Test protocol handler creation."""
        handler = ProtocolHandler()
        assert handler is not None
        assert len(handler.get_pending_requests()) == 0
    
    def test_message_creation(self):
        """Test LSP message creation."""
        handler = ProtocolHandler()
        
        # Test request creation
        request = handler.create_request("test/method", {"param": "value"})
        assert request.method == "test/method"
        assert request.params == {"param": "value"}
        assert request.id is not None
        
        # Test response creation
        response = handler.create_response(request.id, result={"success": True})
        assert response.id == request.id
        assert response.result == {"success": True}
        assert response.error is None
        
        # Test notification creation
        notification = handler.create_notification("test/notification", {"data": "test"})
        assert notification.method == "test/notification"
        assert notification.params == {"data": "test"}
    
    def test_message_parsing(self):
        """Test LSP message parsing."""
        handler = ProtocolHandler()
        
        # Test request parsing
        request_json = '{"jsonrpc": "2.0", "id": "1", "method": "test", "params": {"key": "value"}}'
        parsed = handler.parse_message(request_json)
        assert isinstance(parsed, LSPRequest)
        assert parsed.method == "test"
        assert parsed.params == {"key": "value"}
        
        # Test response parsing
        response_json = '{"jsonrpc": "2.0", "id": "1", "result": {"success": true}}'
        parsed = handler.parse_message(response_json)
        assert isinstance(parsed, LSPResponse)
        assert parsed.result == {"success": True}
        
        # Test notification parsing
        notification_json = '{"jsonrpc": "2.0", "method": "test/notify", "params": {"data": "test"}}'
        parsed = handler.parse_message(notification_json)
        assert isinstance(parsed, LSPNotification)
        assert parsed.method == "test/notify"
    
    def test_invalid_message_parsing(self):
        """Test invalid message parsing."""
        handler = ProtocolHandler()
        
        # Test invalid JSON
        with pytest.raises(ValueError):
            handler.parse_message("invalid json")
        
        # Test missing jsonrpc
        with pytest.raises(ValueError):
            handler.parse_message('{"id": "1", "method": "test"}')
        
        # Test invalid jsonrpc version
        with pytest.raises(ValueError):
            handler.parse_message('{"jsonrpc": "1.0", "id": "1", "method": "test"}')


class TestErrorRetrieval:
    """Test error retrieval system."""
    
    def test_code_error_creation(self):
        """Test CodeError creation."""
        location = ErrorLocation(
            file_path="/test/file.py",
            line=10,
            column=5
        )
        
        error = CodeError(
            id="test_error",
            message="Test error message",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            location=location
        )
        
        assert error.id == "test_error"
        assert error.message == "Test error message"
        assert error.severity == ErrorSeverity.ERROR
        assert error.category == ErrorCategory.SYNTAX
        assert error.location.file_path == "/test/file.py"
        assert error.is_critical is True
    
    def test_code_error_from_lsp_diagnostic(self):
        """Test CodeError creation from LSP diagnostic."""
        diagnostic = {
            "range": {
                "start": {"line": 9, "character": 4},
                "end": {"line": 9, "character": 10}
            },
            "severity": 1,
            "message": "Syntax error",
            "source": "python"
        }
        
        error = CodeError.from_lsp_diagnostic(diagnostic, "/test/file.py")
        
        assert error.location.line == 10  # LSP is 0-based, we use 1-based
        assert error.location.column == 5
        assert error.severity == ErrorSeverity.ERROR
        assert error.message == "Syntax error"
    
    def test_comprehensive_error_list(self):
        """Test ComprehensiveErrorList functionality."""
        error_list = ComprehensiveErrorList()
        
        # Create test errors
        error1 = CodeError(
            id="error1",
            message="Error 1",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            location=ErrorLocation("/test/file1.py", 10, 5)
        )
        
        error2 = CodeError(
            id="error2", 
            message="Error 2",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.STYLE,
            location=ErrorLocation("/test/file2.py", 20, 10)
        )
        
        # Add errors
        error_list.add_error(error1)
        error_list.add_error(error2)
        
        # Test counts
        assert error_list.total_count == 2
        assert error_list.critical_count == 1
        assert error_list.warning_count == 1
        assert len(error_list.files_analyzed) == 2
        
        # Test filtering
        critical_errors = error_list.get_critical_errors()
        assert len(critical_errors) == 1
        assert critical_errors[0].id == "error1"
        
        syntax_errors = error_list.get_errors_by_category(ErrorCategory.SYNTAX)
        assert len(syntax_errors) == 1
        assert syntax_errors[0].id == "error1"
    
    @pytest.mark.asyncio
    async def test_error_retriever(self):
        """Test ErrorRetriever functionality."""
        protocol = ProtocolHandler()
        retriever = ErrorRetriever(protocol)
        
        # Test with mock protocol
        with patch.object(retriever, '_send_request_and_wait') as mock_send:
            mock_send.return_value = {
                'diagnostics': {
                    'file:///test/file.py': [
                        {
                            'range': {'start': {'line': 0, 'character': 0}},
                            'severity': 1,
                            'message': 'Test error',
                            'source': 'test'
                        }
                    ]
                }
            }
            
            result = await retriever.get_comprehensive_errors()
            
            assert isinstance(result, ComprehensiveErrorList)
            assert result.total_count == 1
            assert result.errors[0].message == 'Test error'


class TestServerManager:
    """Test server management functionality."""
    
    def test_server_config_creation(self):
        """Test ServerConfig creation."""
        config = ServerConfig(
            name="test_server",
            command=["test-lsp-server"],
            connection_type=ConnectionType.STDIO
        )
        
        assert config.name == "test_server"
        assert config.command == ["test-lsp-server"]
        assert config.connection_type == ConnectionType.STDIO
        assert config.auto_start is True
    
    def test_server_config_serialization(self):
        """Test ServerConfig serialization."""
        config = ServerConfig(
            name="test_server",
            command=["test-lsp-server"],
            host="localhost",
            port=8080
        )
        
        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict['name'] == "test_server"
        assert config_dict['command'] == ["test-lsp-server"]
        assert config_dict['host'] == "localhost"
        assert config_dict['port'] == 8080
        
        # Test from_dict
        restored_config = ServerConfig.from_dict(config_dict)
        assert restored_config.name == config.name
        assert restored_config.command == config.command
        assert restored_config.host == config.host
        assert restored_config.port == config.port
    
    @pytest.mark.asyncio
    async def test_server_manager_basic_operations(self):
        """Test basic server manager operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SerenaServerManager(temp_dir)
            
            # Test server registration
            config = ServerConfig(
                name="test_server",
                command=["echo", "test"],
                auto_start=False
            )
            
            success = manager.register_server(config)
            assert success is True
            
            # Test server retrieval
            server_info = manager.get_server_info("test_server")
            assert server_info is not None
            assert server_info.config.name == "test_server"
            
            # Test server discovery
            discovered = manager.discover_servers(["/usr/bin", "/bin"])
            assert isinstance(discovered, list)
            
            # Cleanup
            await manager.cleanup()


class TestRealTimeDiagnostics:
    """Test real-time diagnostics system."""
    
    def test_diagnostic_filter(self):
        """Test diagnostic filtering."""
        filter_config = DiagnosticFilter(
            severities={ErrorSeverity.ERROR},
            categories={ErrorCategory.SYNTAX}
        )
        
        # Create test errors
        error1 = CodeError(
            id="error1",
            message="Syntax error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            location=ErrorLocation("/test/file.py", 10, 5)
        )
        
        error2 = CodeError(
            id="error2",
            message="Style warning",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.STYLE,
            location=ErrorLocation("/test/file.py", 20, 10)
        )
        
        # Test filtering
        assert filter_config.matches(error1) is True
        assert filter_config.matches(error2) is False
    
    def test_diagnostic_stats(self):
        """Test diagnostic statistics."""
        stats = DiagnosticStats()
        
        # Create test errors
        errors = [
            CodeError(
                id="error1",
                message="Error 1",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.SYNTAX,
                location=ErrorLocation("/test/file1.py", 10, 5)
            ),
            CodeError(
                id="error2",
                message="Warning 1",
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.STYLE,
                location=ErrorLocation("/test/file2.py", 20, 10)
            )
        ]
        
        # Update stats
        stats.update_from_errors(errors)
        
        assert stats.total_errors == 2
        assert stats.critical_errors == 1
        assert stats.warnings == 1
        assert stats.files_with_errors == 2
        assert stats.categories['syntax'] == 1
        assert stats.categories['style'] == 1
    
    @pytest.mark.asyncio
    async def test_real_time_diagnostics(self):
        """Test real-time diagnostics system."""
        diagnostics = RealTimeDiagnostics()
        
        # Test event handling
        events_received = []
        
        def error_handler(error):
            events_received.append(('error', error))
        
        def stats_handler(stats):
            events_received.append(('stats', stats))
        
        diagnostics.add_error_handler(error_handler)
        diagnostics.add_stats_handler(stats_handler)
        
        # Create test error
        error = CodeError(
            id="test_error",
            message="Test error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.LOGIC,
            location=ErrorLocation("/test/file.py", 10, 5)
        )
        
        # Process error
        await diagnostics.processor.process_errors([error])
        
        # Allow processing to complete
        await asyncio.sleep(0.1)
        
        # Check results
        current_errors = diagnostics.get_current_errors()
        assert len(current_errors) == 1
        assert current_errors[0].id == "test_error"
        
        current_stats = diagnostics.get_current_stats()
        assert current_stats.total_errors == 1
        
        # Cleanup
        await diagnostics.cleanup()


class TestLSPIntegration:
    """Test main LSP integration functionality."""
    
    @pytest.mark.asyncio
    async def test_integration_creation(self):
        """Test LSP integration creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            integration = SerenaLSPIntegration(
                config_dir=temp_dir,
                auto_discover_servers=False,
                enable_real_time_diagnostics=True
            )
            
            assert integration is not None
            assert integration.real_time_diagnostics is not None
            assert integration._initialized is False
            
            # Test initialization (will fail without real servers, but should handle gracefully)
            success = await integration.initialize()
            
            # Should handle missing servers gracefully
            assert isinstance(success, bool)
            
            # Cleanup
            await integration.shutdown()
    
    @pytest.mark.asyncio
    async def test_integration_with_mock_server(self):
        """Test integration with mock server."""
        with tempfile.TemporaryDirectory() as temp_dir:
            integration = SerenaLSPIntegration(
                config_dir=temp_dir,
                auto_discover_servers=False,
                enable_real_time_diagnostics=True
            )
            
            # Register mock server
            mock_config = ServerConfig(
                name="mock_server",
                command=["echo", "mock"],
                auto_start=False
            )
            
            integration.server_manager.register_server(mock_config)
            
            # Test server registration
            servers = integration.server_manager.get_all_servers()
            assert "mock_server" in servers
            
            # Cleanup
            await integration.shutdown()
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience functions."""
        # These should handle missing servers gracefully
        
        # Test with non-existent path (should return empty results)
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello world')")
            
            # These functions create their own integration instances
            # They should handle missing LSP servers gracefully
            try:
                result = await get_comprehensive_code_errors(str(temp_dir))
                assert isinstance(result, ComprehensiveErrorList)
            except RuntimeError:
                # Expected if no LSP servers available
                pass
            
            try:
                errors = await analyze_file_errors(str(test_file))
                assert isinstance(errors, list)
            except RuntimeError:
                # Expected if no LSP servers available
                pass


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""
    
    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self):
        """Test various error handling scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            integration = SerenaLSPIntegration(
                config_dir=temp_dir,
                auto_discover_servers=False,
                enable_real_time_diagnostics=False
            )
            
            # Test operations on uninitialized integration
            with pytest.raises(RuntimeError):
                await integration.get_comprehensive_errors()
            
            with pytest.raises(RuntimeError):
                await integration.analyze_file("/test/file.py")
            
            with pytest.raises(RuntimeError):
                await integration.analyze_codebase("/test/path")
            
            # Test initialization
            await integration.initialize()
            
            # Test operations with no active servers (should return empty results)
            result = await integration.get_comprehensive_errors()
            assert isinstance(result, ComprehensiveErrorList)
            assert result.total_count == 0
            
            errors = await integration.analyze_file("/test/file.py")
            assert isinstance(errors, list)
            assert len(errors) == 0
            
            codebase_result = await integration.analyze_codebase("/test/path")
            assert isinstance(codebase_result, ComprehensiveErrorList)
            assert codebase_result.total_count == 0
            
            # Cleanup
            await integration.shutdown()
    
    @pytest.mark.asyncio
    async def test_event_system(self):
        """Test event system functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            integration = SerenaLSPIntegration(
                config_dir=temp_dir,
                auto_discover_servers=False,
                enable_real_time_diagnostics=True
            )
            
            # Setup event listeners
            error_events = []
            stats_events = []
            connection_events = []
            
            def error_listener(errors):
                error_events.append(errors)
            
            def stats_listener(stats):
                stats_events.append(stats)
            
            def connection_listener(server_name, connected):
                connection_events.append((server_name, connected))
            
            integration.add_error_listener(error_listener)
            integration.add_stats_listener(stats_listener)
            integration.add_connection_listener(connection_listener)
            
            # Initialize
            await integration.initialize()
            
            # Test that listeners are properly registered
            assert len(integration._error_listeners) == 1
            assert len(integration._stats_listeners) == 1
            assert len(integration._connection_listeners) == 1
            
            # Cleanup
            await integration.shutdown()
    
    def test_module_imports(self):
        """Test that all modules can be imported correctly."""
        # Test main integration import
        from graph_sitter.extensions.serena.lsp_integration import SerenaLSPIntegration
        assert SerenaLSPIntegration is not None
        
        # Test LSP components import
        from graph_sitter.extensions.serena.lsp import SerenaLSPClient
        assert SerenaLSPClient is not None
        
        # Test convenience functions import
        from graph_sitter.extensions.serena.lsp_integration import (
            create_serena_lsp_integration,
            get_comprehensive_code_errors,
            analyze_file_errors
        )
        assert create_serena_lsp_integration is not None
        assert get_comprehensive_code_errors is not None
        assert analyze_file_errors is not None
    
    def test_serena_extension_integration(self):
        """Test integration with main Serena extension."""
        # Test that LSP components are available through main extension
        from graph_sitter.extensions.serena import LSP_AVAILABLE
        
        if LSP_AVAILABLE:
            from graph_sitter.extensions.serena import (
                SerenaLSPIntegration,
                SerenaLSPClient,
                ComprehensiveErrorList,
                CodeError
            )
            
            assert SerenaLSPIntegration is not None
            assert SerenaLSPClient is not None
            assert ComprehensiveErrorList is not None
            assert CodeError is not None


# Performance and stress tests
class TestPerformance:
    """Test performance characteristics."""
    
    def test_large_error_list_performance(self):
        """Test performance with large error lists."""
        error_list = ComprehensiveErrorList()
        
        # Create many errors
        start_time = time.time()
        
        for i in range(1000):
            error = CodeError(
                id=f"error_{i}",
                message=f"Error {i}",
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.STYLE,
                location=ErrorLocation(f"/test/file_{i % 10}.py", i % 100 + 1, 5)
            )
            error_list.add_error(error)
        
        creation_time = time.time() - start_time
        
        # Test filtering performance
        start_time = time.time()
        critical_errors = error_list.get_critical_errors()
        filter_time = time.time() - start_time
        
        # Test summary generation performance
        start_time = time.time()
        summary = error_list.get_summary()
        summary_time = time.time() - start_time
        
        # Verify results
        assert error_list.total_count == 1000
        assert len(critical_errors) == 0  # All were warnings
        assert summary['total_errors'] == 1000
        
        # Performance should be reasonable
        assert creation_time < 1.0  # Should create 1000 errors in under 1 second
        assert filter_time < 0.1    # Should filter in under 100ms
        assert summary_time < 0.1   # Should generate summary in under 100ms
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            integration = SerenaLSPIntegration(
                config_dir=temp_dir,
                auto_discover_servers=False,
                enable_real_time_diagnostics=True
            )
            
            await integration.initialize()
            
            # Test concurrent error retrievals
            tasks = []
            for i in range(10):
                task = asyncio.create_task(
                    integration.get_comprehensive_errors(use_cache=False)
                )
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            # All should complete without errors
            for result in results:
                assert isinstance(result, ComprehensiveErrorList)
            
            # Should complete in reasonable time
            assert duration < 5.0  # Should complete in under 5 seconds
            
            await integration.shutdown()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

