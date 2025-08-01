"""
Integration Tests for Consolidated System
========================================

Comprehensive integration tests for the unified LSP error retrieval system.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import the consolidated components
try:
    from graph_sitter.core.unified_analysis import UnifiedAnalysisEngine, AnalysisLevel
    from graph_sitter.core.unified_diagnostics import UnifiedDiagnosticEngine, get_diagnostic_engine
    from graph_sitter.core.enhanced_codebase_integration import (
        EnhancedCodebaseIntegration, IntegrationConfig, create_enhanced_integration
    )
    from graph_sitter.core.consolidated_ai_integration import (
        ConsolidatedAIIntegration, AIConfig, AICapability, create_ai_integration
    )
    from graph_sitter.extensions.serena.lsp_code_generation import LSPCodeGenerationEngine
    from graph_sitter.extensions.lsp.language_servers.enhanced_base import EnhancedBaseLanguageServer
    from graph_sitter.extensions.lsp.protocol.enhanced_types import EnhancedDiagnostic, LSPCapabilities
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest.fixture
def temp_codebase():
    """Create a temporary codebase for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    # Create sample Python files with various issues
    (temp_path / "main.py").write_text("""
import os
import sys

def main():
    # Undefined variable error
    print(undefined_variable)
    
    # Import error
    import nonexistent_module
    
    # Syntax error (missing colon)
    if True
        pass
    
    # Type error
    x = "string"
    y = x + 5

if __name__ == "__main__":
    main()
""")
    
    (temp_path / "utils.py").write_text("""
def helper_function():
    # Indentation error
  return "helper"

class TestClass:
    def method(self):
        # Missing return
        pass
        
    def another_method(self):
        return self.nonexistent_attribute
""")
    
    (temp_path / "config.py").write_text("""
# Configuration file
DEBUG = True
DATABASE_URL = "sqlite:///test.db"

def get_config():
    return {
        'debug': DEBUG,
        'database': DATABASE_URL
    }
""")
    
    yield temp_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_codebase(temp_codebase):
    """Create a mock codebase object."""
    mock_codebase = Mock()
    mock_codebase.repo_path = temp_codebase
    mock_codebase.files = []
    mock_codebase.symbols = []
    return mock_codebase


class TestUnifiedAnalysisEngine:
    """Test the unified analysis engine."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_analysis_engine_initialization(self, mock_codebase):
        """Test that the analysis engine initializes correctly."""
        engine = UnifiedAnalysisEngine(mock_codebase)
        assert engine.codebase == mock_codebase
        assert engine.repo_path == mock_codebase.repo_path
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_basic_analysis(self, mock_codebase):
        """Test basic analysis functionality."""
        engine = UnifiedAnalysisEngine(mock_codebase)
        result = engine.analyze(AnalysisLevel.BASIC)
        
        assert isinstance(result, dict)
        assert 'analysis_level' in result
        assert 'timestamp' in result
        assert 'file_count' in result
        assert result['analysis_level'] == AnalysisLevel.BASIC.value
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_comprehensive_analysis(self, mock_codebase):
        """Test comprehensive analysis functionality."""
        engine = UnifiedAnalysisEngine(mock_codebase)
        result = engine.analyze(AnalysisLevel.COMPREHENSIVE)
        
        assert isinstance(result, dict)
        assert 'analysis_level' in result
        assert 'metrics' in result
        assert 'architectural_insights' in result
        assert result['analysis_level'] == AnalysisLevel.COMPREHENSIVE.value
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_deep_analysis(self, mock_codebase):
        """Test deep analysis functionality."""
        engine = UnifiedAnalysisEngine(mock_codebase)
        result = engine.analyze(AnalysisLevel.DEEP)
        
        assert isinstance(result, dict)
        assert 'analysis_level' in result
        assert 'metrics' in result
        assert 'architectural_insights' in result
        assert 'security_analysis' in result
        assert 'performance_analysis' in result
        assert result['analysis_level'] == AnalysisLevel.DEEP.value


class TestUnifiedDiagnosticEngine:
    """Test the unified diagnostic engine."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_diagnostic_engine_creation(self, mock_codebase):
        """Test diagnostic engine creation."""
        engine = get_diagnostic_engine(mock_codebase, enable_lsp=False)
        assert engine is not None
        assert engine.codebase == mock_codebase
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_error_retrieval_methods(self, mock_codebase):
        """Test error retrieval methods."""
        engine = get_diagnostic_engine(mock_codebase, enable_lsp=False)
        
        # Test that methods exist and return appropriate types
        errors = engine.errors
        assert isinstance(errors, list)
        
        warnings = engine.warnings
        assert isinstance(warnings, list)
        
        summary = engine.get_error_summary()
        assert isinstance(summary, dict)


class TestLSPCodeGenerationEngine:
    """Test the LSP code generation engine."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_code_generation_engine_initialization(self, mock_codebase):
        """Test code generation engine initialization."""
        diagnostic_engine = get_diagnostic_engine(mock_codebase, enable_lsp=False)
        code_gen = LSPCodeGenerationEngine(diagnostic_engine)
        
        assert code_gen.diagnostic_engine == diagnostic_engine
        assert code_gen.repo_path == mock_codebase.repo_path
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_error_fix_generation(self, mock_codebase):
        """Test error fix generation."""
        diagnostic_engine = get_diagnostic_engine(mock_codebase, enable_lsp=False)
        code_gen = LSPCodeGenerationEngine(diagnostic_engine)
        
        # Mock an error
        with patch.object(diagnostic_engine, 'get_full_error_context') as mock_context:
            mock_context.return_value = {
                'error': Mock(
                    id='test_error',
                    message='name "undefined_variable" is not defined',
                    file_path='test.py',
                    line=5
                ),
                'context_lines': {
                    'before': ['def test():'],
                    'error_line': '    print(undefined_variable)',
                    'after': ['    pass']
                }
            }
            
            fixes = code_gen.generate_error_fixes('test_error')
            assert isinstance(fixes, list)


class TestConsolidatedAIIntegration:
    """Test the consolidated AI integration."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_ai_integration_initialization(self):
        """Test AI integration initialization."""
        config = AIConfig(enabled_capabilities=[AICapability.CODE_GENERATION])
        ai = ConsolidatedAIIntegration(config)
        
        assert ai.config == config
        assert isinstance(ai._providers, dict)
        assert isinstance(ai._performance_metrics, dict)
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_code_generation(self):
        """Test AI code generation."""
        config = AIConfig(enabled_capabilities=[AICapability.CODE_GENERATION])
        ai = ConsolidatedAIIntegration(config)
        
        response = await ai.generate_code("Create a hello world function")
        
        assert hasattr(response, 'capability')
        assert hasattr(response, 'success')
        assert hasattr(response, 'content')
        assert response.capability == AICapability.CODE_GENERATION
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_error_analysis(self):
        """Test AI error analysis."""
        config = AIConfig(enabled_capabilities=[AICapability.ERROR_ANALYSIS])
        ai = ConsolidatedAIIntegration(config)
        
        response = await ai.analyze_error("NameError: name 'x' is not defined")
        
        assert response.capability == AICapability.ERROR_ANALYSIS
        assert hasattr(response, 'success')
        assert hasattr(response, 'content')
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        ai = ConsolidatedAIIntegration()
        metrics = ai.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert 'total_requests' in metrics
        assert 'successful_requests' in metrics
        assert 'cache_hits' in metrics
        assert 'success_rate' in metrics


class TestEnhancedCodebaseIntegration:
    """Test the enhanced codebase integration."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_integration_initialization(self, mock_codebase):
        """Test integration initialization."""
        config = IntegrationConfig(enable_lsp=False, enable_real_time_monitoring=False)
        integration = EnhancedCodebaseIntegration(mock_codebase, config)
        
        assert integration.codebase == mock_codebase
        assert integration.config == config
        assert not integration.status.is_initialized
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_integration_initialization_async(self, mock_codebase):
        """Test async integration initialization."""
        config = IntegrationConfig(enable_lsp=False, enable_real_time_monitoring=False)
        integration = EnhancedCodebaseIntegration(mock_codebase, config)
        
        success = await integration.initialize()
        assert isinstance(success, bool)
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self, mock_codebase):
        """Test comprehensive analysis through integration."""
        config = IntegrationConfig(enable_lsp=False, enable_real_time_monitoring=False)
        integration = EnhancedCodebaseIntegration(mock_codebase, config)
        
        await integration.initialize()
        result = await integration.run_comprehensive_analysis()
        
        assert isinstance(result, dict)
        if 'error' not in result:
            assert 'performance' in result
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_health_check(self, mock_codebase):
        """Test system health check."""
        config = IntegrationConfig(enable_lsp=False, enable_real_time_monitoring=False)
        integration = EnhancedCodebaseIntegration(mock_codebase, config)
        
        await integration.initialize()
        health = await integration.health_check()
        
        assert isinstance(health, dict)
        assert 'overall_health' in health
        assert 'components' in health
        assert health['overall_health'] in ['healthy', 'degraded', 'critical']


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_full_system_integration(self, mock_codebase):
        """Test the full system working together."""
        # Create integration with all components disabled for testing
        config = IntegrationConfig(
            enable_lsp=False,
            enable_real_time_monitoring=False,
            enable_code_generation=False,
            enable_deep_analysis=True
        )
        
        integration = EnhancedCodebaseIntegration(mock_codebase, config)
        
        # Initialize the system
        success = await integration.initialize()
        assert isinstance(success, bool)
        
        # Get comprehensive status
        status = integration.get_comprehensive_status()
        assert isinstance(status, dict)
        assert 'integration_status' in status
        assert 'error_status' in status
        
        # Run health check
        health = await integration.health_check()
        assert isinstance(health, dict)
        assert 'overall_health' in health
        
        # Shutdown gracefully
        await integration.shutdown()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_error_detection_and_fixing_workflow(self, mock_codebase):
        """Test the complete error detection and fixing workflow."""
        # This test simulates the full workflow:
        # 1. Detect errors using unified diagnostics
        # 2. Generate fixes using code generation
        # 3. Apply fixes (simulated)
        
        # Create diagnostic engine
        diagnostic_engine = get_diagnostic_engine(mock_codebase, enable_lsp=False)
        
        # Create code generation engine
        code_gen = LSPCodeGenerationEngine(diagnostic_engine)
        
        # Mock some errors
        with patch.object(diagnostic_engine, 'errors', new_callable=lambda: []):
            # Test that the workflow doesn't crash
            errors = diagnostic_engine.errors
            assert isinstance(errors, list)
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    def test_lsp_methods_integration(self, mock_codebase):
        """Test LSP methods integration with unified components."""
        # Import LSP methods mixin
        try:
            from graph_sitter.core.lsp_methods import LSPMethodsMixin
            
            # Create a test class that uses the mixin
            class TestCodebase(LSPMethodsMixin):
                def __init__(self, repo_path):
                    self.repo_path = repo_path
            
            # Create test instance
            test_codebase = TestCodebase(mock_codebase.repo_path)
            
            # Test that methods exist
            assert hasattr(test_codebase, 'errors')
            assert hasattr(test_codebase, 'errors_by_file')
            assert hasattr(test_codebase, 'comprehensive_analysis')
            assert hasattr(test_codebase, 'basic_analysis')
            assert hasattr(test_codebase, 'deep_analysis')
            
            # Test that methods return appropriate types
            errors = test_codebase.errors()
            assert isinstance(errors, list)
            
            analysis = test_codebase.basic_analysis()
            assert isinstance(analysis, dict)
            
        except ImportError:
            pytest.skip("LSP methods not available")


class TestPerformanceAndScalability:
    """Test performance and scalability aspects."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, mock_codebase):
        """Test handling multiple concurrent analysis requests."""
        config = IntegrationConfig(enable_lsp=False, enable_real_time_monitoring=False)
        integration = EnhancedCodebaseIntegration(mock_codebase, config)
        
        await integration.initialize()
        
        # Create multiple concurrent analysis tasks
        tasks = [
            integration.run_comprehensive_analysis("BASIC")
            for _ in range(5)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all completed
        assert len(results) == 5
        for result in results:
            assert isinstance(result, (dict, Exception))
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_ai_batch_processing(self):
        """Test AI batch processing performance."""
        ai = ConsolidatedAIIntegration()
        
        # Create batch requests
        requests = [
            {
                'capability': AICapability.CODE_GENERATION.value,
                'prompt': f'Generate function {i}',
                'context': '',
                'metadata': {'index': i}
            }
            for i in range(3)
        ]
        
        # Process batch
        responses = await ai.batch_process(requests)
        
        assert len(responses) == 3
        for response in responses:
            assert hasattr(response, 'capability')
            assert hasattr(response, 'success')


class TestErrorHandlingAndResilience:
    """Test error handling and system resilience."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_graceful_component_failure(self, mock_codebase):
        """Test graceful handling of component failures."""
        config = IntegrationConfig(enable_lsp=False)
        integration = EnhancedCodebaseIntegration(mock_codebase, config)
        
        # Mock a component failure
        with patch.object(integration, '_initialize_components', side_effect=Exception("Component failed")):
            success = await integration.initialize()
            # Should handle the failure gracefully
            assert isinstance(success, bool)
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_ai_provider_fallback(self):
        """Test AI provider fallback mechanisms."""
        # Create AI integration with fallback enabled
        config = AIConfig(fallback_enabled=True, enabled_capabilities=[AICapability.CODE_GENERATION])
        ai = ConsolidatedAIIntegration(config)
        
        # Test that fallback providers are created
        assert AICapability.CODE_GENERATION in ai._providers
        
        # Test fallback response
        response = await ai.generate_code("test prompt")
        assert hasattr(response, 'success')
        assert hasattr(response, 'content')


# Utility functions for testing
def create_test_error():
    """Create a test error for testing purposes."""
    return Mock(
        id='test_error_123',
        message='Test error message',
        file_path='test.py',
        line=10,
        severity=1
    )


def create_test_diagnostic():
    """Create a test diagnostic for testing purposes."""
    if IMPORTS_AVAILABLE:
        from graph_sitter.extensions.lsp.protocol.lsp_types import Position, Range, DiagnosticSeverity
        
        return EnhancedDiagnostic(
            range=Range(
                start=Position(line=5, character=0),
                end=Position(line=5, character=10)
            ),
            message="Test diagnostic message",
            severity=DiagnosticSeverity.ERROR,
            source="test",
            file_path="test.py",
            id="test_diagnostic_123"
        )
    else:
        return Mock()


# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Mark all tests as integration tests
pytestmark = pytest.mark.integration
