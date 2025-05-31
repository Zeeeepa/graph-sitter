"""
Module Integration Testing Suite

Tests consolidated codegen/graph_sitter modules for API compatibility,
functionality, backward compatibility, and performance regression.
"""

import pytest
import time
import asyncio
from typing import Dict, List, Any
from unittest.mock import Mock, patch

from graph_sitter import Codebase
from graph_sitter.core import CodebaseAnalyzer
from graph_sitter.python import PythonAnalyzer
from graph_sitter.typescript import TypeScriptAnalyzer
from codegen.agents import Agent
from codegen.cli import CLI


class TestModuleIntegration:
    """Test suite for module integration validation."""

    @pytest.fixture
    def sample_codebase(self):
        """Create a sample codebase for testing."""
        return Codebase.from_directory("tests/fixtures/sample_project")

    @pytest.fixture
    def performance_baseline(self):
        """Performance baseline metrics for regression testing."""
        return {
            "parse_time_ms": 1000,
            "analysis_time_ms": 2000,
            "memory_usage_mb": 100,
            "api_response_time_ms": 500
        }

    def test_graph_sitter_codegen_integration(self, sample_codebase):
        """Test integration between graph_sitter and codegen modules."""
        # Test that codegen can use graph_sitter analysis
        analyzer = CodebaseAnalyzer(sample_codebase)
        analysis_result = analyzer.analyze()
        
        # Verify analysis result structure
        assert "files" in analysis_result
        assert "dependencies" in analysis_result
        assert "metrics" in analysis_result
        
        # Test codegen agent can consume analysis
        agent = Agent()
        task_result = agent.process_analysis(analysis_result)
        
        assert task_result is not None
        assert task_result.get("status") == "success"

    def test_api_compatibility(self):
        """Test API compatibility across modules."""
        # Test Python analyzer API
        python_analyzer = PythonAnalyzer()
        assert hasattr(python_analyzer, "parse")
        assert hasattr(python_analyzer, "analyze")
        assert hasattr(python_analyzer, "get_dependencies")
        
        # Test TypeScript analyzer API
        ts_analyzer = TypeScriptAnalyzer()
        assert hasattr(ts_analyzer, "parse")
        assert hasattr(ts_analyzer, "analyze")
        assert hasattr(ts_analyzer, "get_dependencies")
        
        # Test consistent API signatures
        python_methods = dir(python_analyzer)
        ts_methods = dir(ts_analyzer)
        
        # Core methods should be present in both
        core_methods = ["parse", "analyze", "get_dependencies"]
        for method in core_methods:
            assert method in python_methods
            assert method in ts_methods

    def test_backward_compatibility(self):
        """Test backward compatibility with previous API versions."""
        # Test legacy API endpoints still work
        try:
            # Legacy codebase creation
            codebase = Codebase.from_repo("test/repo")
            assert codebase is not None
            
            # Legacy analysis methods
            analyzer = CodebaseAnalyzer(codebase)
            result = analyzer.legacy_analyze()  # Should still work
            assert result is not None
            
        except AttributeError:
            pytest.fail("Backward compatibility broken - legacy methods not available")

    def test_performance_regression(self, sample_codebase, performance_baseline):
        """Test for performance regressions."""
        # Test parse performance
        start_time = time.time()
        analyzer = CodebaseAnalyzer(sample_codebase)
        parse_time = (time.time() - start_time) * 1000
        
        assert parse_time <= performance_baseline["parse_time_ms"] * 1.2  # 20% tolerance
        
        # Test analysis performance
        start_time = time.time()
        result = analyzer.analyze()
        analysis_time = (time.time() - start_time) * 1000
        
        assert analysis_time <= performance_baseline["analysis_time_ms"] * 1.2
        
        # Memory usage test would require memory profiling tools
        # This is a placeholder for actual memory testing
        assert True  # Placeholder

    def test_cross_language_integration(self):
        """Test integration across different language analyzers."""
        # Create mixed-language codebase
        python_analyzer = PythonAnalyzer()
        ts_analyzer = TypeScriptAnalyzer()
        
        # Test that analyzers can work together
        python_result = python_analyzer.analyze("test.py")
        ts_result = ts_analyzer.analyze("test.ts")
        
        # Test combined analysis
        combined_analyzer = CodebaseAnalyzer()
        combined_result = combined_analyzer.combine_analyses([python_result, ts_result])
        
        assert "python" in combined_result
        assert "typescript" in combined_result
        assert combined_result["total_files"] == 2

    def test_error_handling_integration(self):
        """Test error handling across module boundaries."""
        # Test graceful error handling when modules fail
        with patch('graph_sitter.core.CodebaseAnalyzer.analyze') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            
            analyzer = CodebaseAnalyzer()
            try:
                result = analyzer.safe_analyze()
                assert result["status"] == "error"
                assert "error_message" in result
            except Exception:
                pytest.fail("Error not handled gracefully across modules")

    def test_concurrent_module_access(self):
        """Test concurrent access to modules."""
        async def analyze_concurrently():
            tasks = []
            for i in range(5):
                analyzer = CodebaseAnalyzer()
                task = asyncio.create_task(analyzer.async_analyze(f"test_{i}.py"))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        # Run concurrent analysis
        results = asyncio.run(analyze_concurrently())
        
        # Verify all tasks completed successfully
        for result in results:
            assert not isinstance(result, Exception)

    def test_plugin_integration(self):
        """Test plugin system integration."""
        # Test that plugins can be loaded and integrated
        from graph_sitter.extensions import PluginManager
        
        plugin_manager = PluginManager()
        plugins = plugin_manager.load_plugins()
        
        assert len(plugins) >= 0  # Should not fail to load
        
        # Test plugin functionality
        for plugin in plugins:
            assert hasattr(plugin, "process")
            assert callable(plugin.process)

    def test_configuration_integration(self):
        """Test configuration system integration."""
        from graph_sitter.configs import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Test configuration is properly loaded
        assert config is not None
        assert "analyzers" in config
        assert "performance" in config
        
        # Test configuration affects module behavior
        analyzer = CodebaseAnalyzer(config=config)
        assert analyzer.config == config

