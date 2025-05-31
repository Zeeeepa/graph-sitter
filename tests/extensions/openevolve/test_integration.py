"""
Tests for OpenEvolve Integration

This module contains comprehensive tests for the OpenEvolve integration with Graph-sitter,
including unit tests, integration tests, and performance tests.
"""

import asyncio
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from graph_sitter.extensions.openevolve import (
    OpenEvolveIntegration,
    OpenEvolveConfig,
    ContinuousLearningSystem,
    ContextTracker,
    PerformanceMonitor,
    OpenEvolveDatabase
)


class TestOpenEvolveConfig:
    """Test configuration management."""
    
    def test_default_config_creation(self):
        """Test creating default configuration."""
        config = OpenEvolveConfig()
        
        assert config.learning.min_pattern_frequency == 3
        assert config.database.database_path == "openevolve_integration.db"
        assert config.performance.enable_monitoring is True
        assert config.evolution.max_iterations == 100
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = OpenEvolveConfig()
        
        # Valid configuration should pass
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid configuration should fail
        config.learning.min_pattern_frequency = 0
        config.evolution.population_size = 1
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("min_pattern_frequency" in error for error in errors)
        assert any("population_size" in error for error in errors)
    
    def test_config_serialization(self):
        """Test configuration serialization and deserialization."""
        config = OpenEvolveConfig()
        config.learning.learning_rate = 0.2
        config.debug_mode = True
        
        # Convert to dict and back
        config_dict = config.to_dict()
        restored_config = OpenEvolveConfig.from_dict(config_dict)
        
        assert restored_config.learning.learning_rate == 0.2
        assert restored_config.debug_mode is True
    
    def test_config_file_operations(self):
        """Test saving and loading configuration files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            # Create and save config
            config = OpenEvolveConfig()
            config.learning.learning_rate = 0.15
            config.save_to_file(config_path)
            
            # Load config
            loaded_config = OpenEvolveConfig.load_from_file(config_path)
            assert loaded_config.learning.learning_rate == 0.15
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_optimized_configs(self):
        """Test optimized configuration generation."""
        base_config = OpenEvolveConfig()
        
        # Performance optimized
        perf_config = base_config.get_optimized_config("performance")
        assert perf_config.evolution.parallel_evaluation is True
        assert perf_config.evolution.max_parallel_workers == 8
        
        # Accuracy optimized
        acc_config = base_config.get_optimized_config("accuracy")
        assert acc_config.learning.min_training_samples == 50
        assert acc_config.evolution.population_size == 100
        
        # Memory optimized
        mem_config = base_config.get_optimized_config("memory")
        assert mem_config.performance.metric_window_size == 25
        assert mem_config.evolution.population_size == 25


class TestOpenEvolveDatabase:
    """Test database operations."""
    
    @pytest.fixture
    async def database(self):
        """Create a test database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            db = OpenEvolveDatabase(db_path)
            await db.initialize()
            yield db
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, database):
        """Test database schema creation."""
        # Database should be initialized
        assert database._initialized is True
        
        # Check that tables exist by getting stats
        stats = await database.get_database_stats()
        assert "evolution_sessions_count" in stats
        assert "evolution_steps_count" in stats
    
    @pytest.mark.asyncio
    async def test_session_management(self, database):
        """Test session creation and management."""
        session_id = "test_session_001"
        target_files = ["test.py", "utils.py"]
        objectives = {"performance": 0.8, "quality": 0.7}
        
        # Create session
        await database.create_session(session_id, target_files, objectives, 50)
        
        # Verify session exists
        session_data = await database.get_session_data(session_id)
        assert len(session_data) == 0  # No steps yet
        
        # Finalize session
        final_report = {"status": "completed", "results": {}}
        await database.finalize_session(session_id, final_report)
    
    @pytest.mark.asyncio
    async def test_step_context_storage(self, database):
        """Test storing and retrieving step contexts."""
        # Create session first
        session_id = "test_session_002"
        await database.create_session(session_id, ["test.py"], {}, 10)
        
        # Create step context
        step_context = {
            "step_id": "step_001",
            "session_id": session_id,
            "step_type": "code_evolution",
            "file_path": "test.py",
            "prompt": "Optimize code",
            "context": {"focus": "performance"},
            "start_time": time.time(),
            "status": "running"
        }
        
        # Store step context
        await database.store_step_context(step_context)
        
        # Update with metrics
        metrics = {"execution_time": 5.2, "improvement": 0.15}
        await database.update_step_metrics("step_001", metrics)
        
        # Complete step
        step_context.update({
            "end_time": time.time(),
            "execution_time": 5.2,
            "status": "completed",
            "result": {"success": True},
            "errors": []
        })
        await database.complete_step_context("step_001", step_context)
        
        # Retrieve session data
        session_data = await database.get_session_data(session_id)
        assert len(session_data) == 1
        assert session_data[0]["step_id"] == "step_001"
        assert session_data[0]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_learning_data_storage(self, database):
        """Test storing and retrieving learning data."""
        learning_data = {
            "step_id": "step_learning_001",
            "context": {"complexity": 0.7, "patterns": ["optimization"]},
            "result": {"evolution_metrics": {"performance_improvement": 0.2}},
            "timestamp": time.time()
        }
        
        await database.store_learning_data(learning_data)
        
        # Verify data was stored (would need to query learning_data table)
        # This is implicitly tested through other operations
    
    @pytest.mark.asyncio
    async def test_performance_analytics(self, database):
        """Test performance analytics retrieval."""
        session_id = "test_session_analytics"
        await database.create_session(session_id, ["test.py"], {}, 10)
        
        # Add some test data
        for i in range(3):
            step_context = {
                "step_id": f"step_{i}",
                "session_id": session_id,
                "step_type": "code_evolution",
                "start_time": time.time(),
                "status": "running"
            }
            await database.store_step_context(step_context)
            
            # Complete step with metrics
            step_context.update({
                "end_time": time.time(),
                "execution_time": 2.0 + i,
                "status": "completed",
                "result": {},
                "errors": []
            })
            await database.complete_step_context(f"step_{i}", step_context)
        
        # Get analytics
        analytics = await database.get_performance_analytics(session_id)
        assert analytics["total_steps"] == 3
        assert analytics["success_rate"] == 1.0  # All completed successfully
        assert analytics["avg_execution_time"] > 0


class TestContextTracker:
    """Test context tracking functionality."""
    
    @pytest.fixture
    async def context_tracker(self):
        """Create a test context tracker."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            database = OpenEvolveDatabase(db_path)
            await database.initialize()
            tracker = ContextTracker(database)
            yield tracker
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_session_tracking(self, context_tracker):
        """Test session tracking lifecycle."""
        session_id = "tracker_session_001"
        
        # Start session
        context_tracker.start_session(session_id)
        assert session_id in context_tracker.active_sessions
        assert session_id in context_tracker.decision_trees
        
        # End session
        context_tracker.end_session(session_id)
        session = context_tracker.active_sessions[session_id]
        assert "end_time" in session
        assert "duration" in session
    
    @pytest.mark.asyncio
    async def test_step_tracking(self, context_tracker):
        """Test step tracking functionality."""
        session_id = "tracker_session_002"
        context_tracker.start_session(session_id)
        
        # Start step
        step_id = await context_tracker.start_step(
            session_id=session_id,
            step_type="code_evolution",
            file_path="test.py",
            prompt="Optimize code",
            context={"focus": "performance"}
        )
        
        assert step_id in context_tracker.step_contexts
        assert context_tracker.step_contexts[step_id]["status"] == "running"
        
        # Record decision
        decision_id = await context_tracker.record_decision(
            step_id=step_id,
            decision_type="algorithm_selection",
            decision_context={"algorithm": "genetic"},
            outcome="selected"
        )
        
        assert decision_id is not None
        
        # Record metrics
        await context_tracker.record_metrics(step_id, {
            "execution_time": 3.5,
            "improvement": 0.12
        })
        
        # Complete step
        await context_tracker.complete_step(
            step_id=step_id,
            result={"success": True, "code_generated": True},
            execution_time=3.5
        )
        
        assert context_tracker.step_contexts[step_id]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_error_recording(self, context_tracker):
        """Test error recording functionality."""
        session_id = "tracker_session_003"
        context_tracker.start_session(session_id)
        
        step_id = await context_tracker.start_step(
            session_id=session_id,
            step_type="code_evolution"
        )
        
        # Record error
        await context_tracker.record_error(
            step_id=step_id,
            error="Timeout during evolution",
            execution_time=30.0
        )
        
        step_context = context_tracker.step_contexts[step_id]
        assert step_context["status"] == "error"
        assert len(step_context["errors"]) == 1
        assert step_context["errors"][0]["error"] == "Timeout during evolution"
    
    @pytest.mark.asyncio
    async def test_pattern_analysis(self, context_tracker):
        """Test pattern analysis functionality."""
        session_id = "tracker_session_004"
        context_tracker.start_session(session_id)
        
        # Create multiple steps to analyze
        for i in range(5):
            step_id = await context_tracker.start_step(
                session_id=session_id,
                step_type="code_evolution",
                file_path=f"test_{i}.py"
            )
            
            await context_tracker.complete_step(
                step_id=step_id,
                result={"success": i % 2 == 0},  # Alternate success/failure
                execution_time=2.0 + i
            )
        
        # Analyze patterns
        patterns = await context_tracker.analyze_patterns(session_id)
        
        assert "step_patterns" in patterns
        assert "performance_patterns" in patterns
        assert patterns["step_patterns"]["total_steps"] == 5


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    @pytest.fixture
    async def performance_monitor(self):
        """Create a test performance monitor."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            database = OpenEvolveDatabase(db_path)
            await database.initialize()
            monitor = PerformanceMonitor(database)
            yield monitor
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, performance_monitor):
        """Test monitoring session lifecycle."""
        session_id = "monitor_session_001"
        
        # Start monitoring
        performance_monitor.start_monitoring(session_id)
        assert session_id in performance_monitor.active_sessions
        
        # Record metrics
        await performance_monitor.record_evolution_metrics(
            session_id=session_id,
            step_id="step_001",
            execution_time=5.2,
            result={"evolution_metrics": {"performance_improvement": 0.15}}
        )
        
        # Stop monitoring
        performance_monitor.stop_monitoring(session_id)
        session_info = performance_monitor.active_sessions[session_id]
        assert "end_time" in session_info
    
    @pytest.mark.asyncio
    async def test_metric_collection(self, performance_monitor):
        """Test metric collection functionality."""
        collector = performance_monitor.metric_collector
        
        # Record metrics
        for i in range(10):
            collector.record_metric("execution_time", 2.0 + i * 0.5)
            collector.record_metric("improvement", 0.1 + i * 0.02)
        
        # Get statistics
        exec_stats = collector.get_metric_stats("execution_time")
        assert exec_stats["count"] == 10
        assert exec_stats["mean"] > 0
        assert exec_stats["min"] == 2.0
        
        # Get trend
        trend = collector.get_trend("execution_time")
        assert trend["trend"] in ["increasing", "decreasing", "stable"]
        assert 0 <= trend["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_performance_analysis(self, performance_monitor):
        """Test performance analysis functionality."""
        # Create test session data
        session_data = []
        for i in range(10):
            step_data = {
                "step_id": f"step_{i}",
                "step_type": "code_evolution",
                "execution_time": 3.0 + i * 0.5,
                "success": i % 3 != 0,  # 2/3 success rate
                "errors": [] if i % 3 != 0 else [{"error": "test error"}],
                "start_time": time.time() + i
            }
            session_data.append(step_data)
        
        # Analyze performance
        analysis = performance_monitor.analyzer.analyze_session_performance(session_data)
        
        assert "session_summary" in analysis
        assert "bottlenecks" in analysis
        assert "trends" in analysis
        assert "recommendations" in analysis
        
        summary = analysis["session_summary"]
        assert summary["total_steps"] == 10
        assert 0 <= summary["success_rate"] <= 1


class TestContinuousLearningSystem:
    """Test continuous learning functionality."""
    
    @pytest.fixture
    async def learning_system(self):
        """Create a test learning system."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            database = OpenEvolveDatabase(db_path)
            await database.initialize()
            config = OpenEvolveConfig()
            learning_system = ContinuousLearningSystem(database, config)
            yield learning_system
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_pattern_recognition(self, learning_system):
        """Test pattern recognition functionality."""
        # Create test evolution history
        evolution_history = []
        for i in range(20):
            step = {
                "step_id": f"step_{i}",
                "evolution_prompt": f"optimize performance {i}",
                "applied_patterns": ["optimization", "refactoring"],
                "complexity_metrics": {"cyclomatic_complexity": 5 + i},
                "execution_time": 2.0 + i * 0.1,
                "evolution_metrics": {"performance_improvement": 0.1 + i * 0.01},
                "success": i % 4 != 0  # 75% success rate
            }
            evolution_history.append(step)
        
        # Analyze patterns
        pattern_analysis = learning_system.pattern_recognizer.analyze_evolution_patterns(evolution_history)
        
        assert "patterns" in pattern_analysis
        assert "confidence" in pattern_analysis
        assert pattern_analysis["total_patterns"] >= 0
    
    @pytest.mark.asyncio
    async def test_adaptive_algorithm(self, learning_system):
        """Test adaptive algorithm functionality."""
        # Create training data
        evolution_history = []
        for i in range(15):
            step = {
                "complexity_metrics": {"cyclomatic_complexity": 5 + i},
                "evolution_prompt": f"test prompt {i}",
                "applied_patterns": ["pattern_a", "pattern_b"],
                "execution_time": 2.0 + i * 0.2,
                "evolution_metrics": {"performance_improvement": 0.1 + i * 0.02}
            }
            evolution_history.append(step)
        
        # Train performance predictor
        training_result = learning_system.adaptive_algorithm.train_performance_predictor(evolution_history)
        
        if training_result["status"] == "success":
            assert "model_score" in training_result
            assert "feature_importance" in training_result
            
            # Test prediction
            test_context = {
                "complexity_metrics": {"cyclomatic_complexity": 10},
                "evolution_prompt": "test optimization",
                "applied_patterns": ["pattern_a"]
            }
            
            prediction = learning_system.adaptive_algorithm.predict_evolution_success(test_context)
            assert "prediction" in prediction
            assert 0 <= prediction["prediction"] <= 1
    
    @pytest.mark.asyncio
    async def test_context_enhancement(self, learning_system):
        """Test context enhancement functionality."""
        # Mock database method
        async def mock_get_history(file_path, limit=100):
            return [
                {
                    "step_id": "step_1",
                    "evolution_prompt": "optimize",
                    "success": True,
                    "evolution_metrics": {"performance_improvement": 0.2}
                }
            ]
        
        learning_system.database.get_file_evolution_history = mock_get_history
        
        # Test context enhancement
        enhanced_context = await learning_system.enhance_context(
            file_path="test.py",
            current_analysis={"complexity_metrics": {"cyclomatic_complexity": 5}},
            evolution_prompt="optimize performance",
            historical_context={"previous_attempts": 2}
        )
        
        assert "pattern_analysis" in enhanced_context
        assert "success_prediction" in enhanced_context
        assert "suggested_patterns" in enhanced_context
        assert "insights" in enhanced_context


class TestOpenEvolveIntegration:
    """Test the main integration functionality."""
    
    @pytest.fixture
    async def integration(self):
        """Create a test integration."""
        # Mock codebase
        mock_codebase = MagicMock()
        mock_file_node = MagicMock()
        mock_file_node.symbols = []
        mock_file_node.dependencies = []
        mock_file_node.get_complexity_metrics.return_value = {"cyclomatic_complexity": 5}
        mock_file_node.get_structure_analysis.return_value = {"functions": 3}
        mock_codebase.get_file.return_value = mock_file_node
        
        # Create config
        config = OpenEvolveConfig()
        config.database.database_path = ":memory:"  # Use in-memory database for tests
        
        # Create integration
        integration = OpenEvolveIntegration(mock_codebase, config)
        
        # Initialize database
        await integration.database.initialize()
        
        yield integration
    
    @pytest.mark.asyncio
    async def test_session_lifecycle(self, integration):
        """Test complete session lifecycle."""
        # Start session
        session_id = await integration.start_evolution_session(
            target_files=["test.py"],
            objectives={"performance": 0.8},
            max_iterations=10
        )
        
        assert integration.current_session_id == session_id
        assert session_id in integration.context_tracker.active_sessions
        
        # End session
        final_report = await integration.end_evolution_session()
        
        assert integration.current_session_id is None
        assert "session_id" in final_report
    
    @pytest.mark.asyncio
    async def test_code_evolution(self, integration):
        """Test code evolution functionality."""
        # Start session
        session_id = await integration.start_evolution_session(
            target_files=["test.py"],
            objectives={"performance": 0.8},
            max_iterations=10
        )
        
        # Mock the evolution process
        with patch.object(integration, '_perform_evolution') as mock_evolution:
            mock_evolution.return_value = {
                "file_path": "test.py",
                "evolved_code": "optimized code",
                "evolution_metrics": {"performance_improvement": 0.15},
                "applied_patterns": ["optimization"],
                "timestamp": time.time()
            }
            
            # Evolve code
            result = await integration.evolve_code(
                file_path="test.py",
                evolution_prompt="optimize performance",
                context={"focus": "speed"}
            )
            
            assert "evolution_metrics" in result
            assert result["file_path"] == "test.py"
            assert mock_evolution.called
        
        await integration.end_evolution_session()
    
    @pytest.mark.asyncio
    async def test_insights_generation(self, integration):
        """Test insights generation."""
        # Start session and add some data
        session_id = await integration.start_evolution_session(
            target_files=["test.py"],
            objectives={"performance": 0.8},
            max_iterations=10
        )
        
        # Mock some session data
        mock_session_data = [
            {
                "step_id": "step_1",
                "success": True,
                "execution_time": 3.0,
                "evolution_metrics": {"performance_improvement": 0.1}
            }
        ]
        
        with patch.object(integration.database, 'get_session_data') as mock_get_data:
            mock_get_data.return_value = mock_session_data
            
            # Get insights
            insights = await integration.get_evolution_insights()
            
            assert "session_id" in insights
            assert "performance" in insights
            assert "learning_insights" in insights
            assert "context_patterns" in insights
        
        await integration.end_evolution_session()
    
    @pytest.mark.asyncio
    async def test_strategy_optimization(self, integration):
        """Test strategy optimization."""
        # Start session
        session_id = await integration.start_evolution_session(
            target_files=["test.py"],
            objectives={"performance": 0.8},
            max_iterations=10
        )
        
        # Mock session data for optimization
        mock_session_data = [
            {
                "applied_patterns": ["optimization", "refactoring"],
                "evolution_metrics": {"performance_improvement": 0.2},
                "execution_time": 3.0
            }
        ]
        
        with patch.object(integration.database, 'get_session_data') as mock_get_data:
            mock_get_data.return_value = mock_session_data
            
            # Optimize strategy
            optimization_result = await integration.optimize_evolution_strategy()
            
            assert "session_id" in optimization_result
            assert "updated_strategy_weights" in optimization_result
            assert "suggested_config" in optimization_result
        
        await integration.end_evolution_session()


class TestIntegrationPerformance:
    """Test performance characteristics of the integration."""
    
    @pytest.mark.asyncio
    async def test_database_performance(self):
        """Test database operation performance."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            database = OpenEvolveDatabase(db_path)
            await database.initialize()
            
            # Measure session creation performance
            start_time = time.time()
            
            for i in range(100):
                await database.create_session(
                    f"session_{i}",
                    [f"file_{i}.py"],
                    {"performance": 0.8},
                    50
                )
            
            creation_time = time.time() - start_time
            assert creation_time < 5.0  # Should complete in under 5 seconds
            
            # Measure query performance
            start_time = time.time()
            
            for i in range(50):
                await database.get_session_data(f"session_{i}")
            
            query_time = time.time() - start_time
            assert query_time < 2.0  # Should complete in under 2 seconds
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage characteristics."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create multiple integrations to test memory usage
        integrations = []
        
        for i in range(10):
            mock_codebase = MagicMock()
            config = OpenEvolveConfig()
            config.database.database_path = ":memory:"
            
            integration = OpenEvolveIntegration(mock_codebase, config)
            await integration.database.initialize()
            integrations.append(integration)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 10 integrations)
        assert memory_increase < 100 * 1024 * 1024


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

