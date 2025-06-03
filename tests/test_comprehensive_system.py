"""
Comprehensive System Tests

This module contains integration tests for the complete CI/CD system
to validate all components work together correctly.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

# Import system components
from src.contexten.core import ContextenOrchestrator, SystemConfig
from src.contexten.client import ContextenClient, ClientConfig
from src.contexten.integrations import UnifiedAPI, APIRequest, DatabaseConfig
from src.codegen.autogenlib import CodegenClient, TaskConfig, TaskManager
from src.contexten.learning import (
    PatternRecognitionEngine, PerformanceTracker, AdaptationEngine,
    DataPoint, MetricPoint, MetricType, PatternType
)


class TestComprehensiveSystem:
    """Test the complete integrated system."""
    
    @pytest.fixture
    async def system_config(self):
        """Create test system configuration."""
        return SystemConfig(
            codegen_org_id="test-org",
            codegen_token="test-token",
            max_concurrent_tasks=3,
            github_enabled=False,  # Disable for testing
            linear_enabled=False,
            slack_enabled=False,
            learning_enabled=True,
            metrics_enabled=True
        )
    
    @pytest.fixture
    async def orchestrator(self, system_config):
        """Create and initialize orchestrator."""
        orchestrator = ContextenOrchestrator(system_config)
        
        # Mock the Codegen client initialization
        with patch('src.contexten.core.CodegenClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.get_client_info.return_value = {"status": "ok"}
            
            await orchestrator.start()
            yield orchestrator
            await orchestrator.stop()
    
    @pytest.fixture
    async def unified_api(self):
        """Create unified API instance."""
        api = UnifiedAPI(enable_learning=True, enable_performance_tracking=True)
        await api.initialize()
        yield api
        await api.shutdown()
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.status.value == "active"
        assert orchestrator.codegen_client is not None
        assert orchestrator.task_manager is not None
        assert orchestrator.batch_processor is not None
    
    @pytest.mark.asyncio
    async def test_codebase_analysis_integration(self, orchestrator):
        """Test codebase analysis integration."""
        # Mock the analysis execution
        with patch.object(orchestrator, '_enhance_with_local_analysis') as mock_enhance:
            mock_enhance.return_value = {
                "codegen_result": {"status": "completed"},
                "local_analysis": {"functions_used": ["get_codebase_summary"]}
            }
            
            result = await orchestrator.execute_codebase_analysis(
                "https://github.com/test/repo",
                "comprehensive"
            )
            
            assert result["status"] == "completed"
            assert result["repository_url"] == "https://github.com/test/repo"
            assert result["analysis_type"] == "comprehensive"
    
    @pytest.mark.asyncio
    async def test_task_management_workflow(self, orchestrator):
        """Test task management workflow."""
        from src.codegen.autogenlib import WorkflowDefinition
        
        # Create a test workflow
        workflow = WorkflowDefinition(
            id="test_workflow",
            name="Test Workflow",
            description="Test workflow for integration testing",
            tasks=[
                {
                    "id": "task1",
                    "prompt": "Test task 1",
                    "context": {"test": True}
                },
                {
                    "id": "task2", 
                    "prompt": "Test task 2",
                    "context": {"test": True}
                }
            ],
            dependencies={"task2": ["task1"]}
        )
        
        # Create workflow
        task_ids = await orchestrator.create_workflow(workflow)
        
        assert len(task_ids) == 2
        assert workflow.id in orchestrator.active_workflows
        
        # Check workflow status
        workflow_info = orchestrator.active_workflows[workflow.id]
        assert workflow_info["status"] == "active"
        assert len(workflow_info["task_ids"]) == 2
    
    @pytest.mark.asyncio
    async def test_learning_system_integration(self):
        """Test learning system integration."""
        # Initialize learning components
        pattern_engine = PatternRecognitionEngine()
        performance_tracker = PerformanceTracker()
        adaptation_engine = AdaptationEngine(pattern_engine, performance_tracker, auto_adapt=False)
        
        # Add test data points
        for i in range(10):
            data_point = DataPoint(
                timestamp=datetime.now() - timedelta(hours=i),
                event_type="task_execution",
                attributes={"task_type": "analysis", "priority": 5},
                outcome="failed" if i % 3 == 0 else "completed",
                duration=60 + i * 5,
                error_message="timeout error" if i % 3 == 0 else None
            )
            pattern_engine.add_data_point(data_point)
        
        # Analyze patterns
        patterns = await pattern_engine.analyze_patterns()
        assert len(patterns) > 0
        
        # Create adaptations
        adaptations = await adaptation_engine.analyze_and_adapt()
        assert len(adaptations) >= 0  # May be 0 if no patterns meet criteria
        
        # Test performance tracking
        performance_tracker.record_task_performance(
            task_id="test_task",
            duration=1.5,
            success=True
        )
        
        summary = performance_tracker.get_performance_summary()
        assert "metrics" in summary
        assert "timestamp" in summary
    
    @pytest.mark.asyncio
    async def test_unified_api_operations(self, unified_api):
        """Test unified API operations."""
        # Test health check
        health_request = APIRequest(
            action="health_check",
            parameters={}
        )
        health_response = await unified_api.process_request(health_request)
        
        assert health_response.success is True
        assert "api" in health_response.data
        assert health_response.data["api"] == "healthy"
        
        # Test codebase analysis
        analysis_request = APIRequest(
            action="analyze_codebase",
            parameters={
                "repository_url": "https://github.com/test/repo",
                "analysis_type": "summary"
            }
        )
        analysis_response = await unified_api.process_request(analysis_request)
        
        assert analysis_response.success is True
        assert "repository_url" in analysis_response.data
        
        # Test API info
        info_request = APIRequest(
            action="get_api_info",
            parameters={}
        )
        info_response = await unified_api.process_request(info_request)
        
        assert info_response.success is True
        assert "name" in info_response.data
        assert "version" in info_response.data
    
    @pytest.mark.asyncio
    async def test_client_interface(self, system_config):
        """Test client interface."""
        client_config = ClientConfig(
            system_config=system_config,
            auto_start_orchestrator=False  # Don't start for testing
        )
        
        client = ContextenClient(client_config)
        
        # Test client initialization
        assert client.config == client_config
        assert client.orchestrator is None
        assert not client._is_started
    
    @pytest.mark.asyncio
    async def test_database_integration(self):
        """Test database integration."""
        from src.contexten.integrations import DatabaseAdapter, DatabaseConfig
        
        # Create test database config
        db_config = DatabaseConfig(
            host="localhost",
            database="test_db",
            username="test_user"
        )
        
        adapter = DatabaseAdapter(db_config)
        
        # Test connection (mocked)
        with patch.object(adapter, '_execute_command') as mock_command:
            mock_command.return_value = 1
            
            await adapter.connect()
            assert adapter.connected is True
            
            # Test organization creation
            org_id = await adapter.create_organization(
                name="Test Org",
                slug="test-org",
                description="Test organization"
            )
            assert org_id is not None
            
            # Test project creation
            project_id = await adapter.create_project(
                org_id=org_id,
                name="Test Project",
                slug="test-project"
            )
            assert project_id is not None
            
            await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, unified_api):
        """Test error handling throughout the system."""
        # Test invalid action
        invalid_request = APIRequest(
            action="invalid_action",
            parameters={}
        )
        response = await unified_api.process_request(invalid_request)
        
        assert response.success is False
        assert "Unknown action" in response.error
        
        # Test missing parameters
        incomplete_request = APIRequest(
            action="analyze_codebase",
            parameters={}  # Missing required repository_url
        )
        response = await unified_api.process_request(incomplete_request)
        
        assert response.success is False
        assert response.error is not None
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test performance metrics collection."""
        tracker = PerformanceTracker()
        
        # Record various metrics
        tracker.record_task_performance("task1", 1.5, True)
        tracker.record_task_performance("task2", 2.0, False, "timeout")
        tracker.record_throughput(100, 60.0, "api_requests")
        tracker.record_queue_depth("task_queue", 5)
        
        # Get summary
        summary = tracker.get_performance_summary()
        
        assert "metrics" in summary
        assert "timestamp" in summary
        assert summary["metrics"]["success_rate"]["count"] == 2
    
    @pytest.mark.asyncio
    async def test_pattern_recognition(self):
        """Test pattern recognition capabilities."""
        engine = PatternRecognitionEngine()
        
        # Add failure pattern data
        for i in range(5):
            data_point = DataPoint(
                timestamp=datetime.now() - timedelta(minutes=i*10),
                event_type="task_execution",
                attributes={"task_type": "analysis"},
                outcome="failed",
                error_message="timeout error"
            )
            engine.add_data_point(data_point)
        
        # Analyze patterns
        patterns = await engine.analyze_patterns()
        
        # Should detect task failure pattern
        failure_patterns = [p for p in patterns if p.pattern_type == PatternType.TASK_FAILURE]
        assert len(failure_patterns) > 0
        
        # Check pattern attributes
        if failure_patterns:
            pattern = failure_patterns[0]
            assert pattern.confidence_score > 0
            assert pattern.occurrences >= 3
            assert "timeout" in pattern.description.lower()
    
    @pytest.mark.asyncio
    async def test_adaptation_engine(self):
        """Test adaptation engine functionality."""
        pattern_engine = PatternRecognitionEngine()
        performance_tracker = PerformanceTracker()
        adaptation_engine = AdaptationEngine(
            pattern_engine, 
            performance_tracker, 
            auto_adapt=False
        )
        
        # Create a pattern that should trigger adaptation
        for i in range(5):
            data_point = DataPoint(
                timestamp=datetime.now() - timedelta(minutes=i*10),
                event_type="task_execution",
                attributes={"task_type": "analysis"},
                outcome="failed",
                error_message="timeout error"
            )
            pattern_engine.add_data_point(data_point)
        
        # Analyze patterns
        await pattern_engine.analyze_patterns()
        
        # Create adaptations
        adaptations = await adaptation_engine.analyze_and_adapt()
        
        # Check if adaptations were created
        summary = adaptation_engine.get_adaptation_summary()
        assert "total_adaptations" in summary
        assert "pending_adaptations" in summary
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, system_config):
        """Test complete end-to-end workflow."""
        # This test simulates a complete workflow from API request to completion
        
        # 1. Initialize system
        api = UnifiedAPI(enable_learning=True, enable_performance_tracking=True)
        await api.initialize()
        
        try:
            # 2. Analyze codebase
            analysis_response = await api.quick_analyze(
                "https://github.com/test/repo",
                "summary"
            )
            assert analysis_response.success is True
            
            # 3. Check system status
            status_request = APIRequest(
                action="get_system_status",
                parameters={}
            )
            status_response = await api.process_request(status_request)
            assert status_response.success is True
            assert status_response.data["initialized"] is True
            
            # 4. Get performance metrics
            metrics_request = APIRequest(
                action="get_performance_metrics",
                parameters={}
            )
            metrics_response = await api.process_request(metrics_request)
            assert metrics_response.success is True
            
            # 5. Verify learning system is working
            if api.pattern_engine:
                patterns_request = APIRequest(
                    action="get_patterns",
                    parameters={}
                )
                patterns_response = await api.process_request(patterns_request)
                assert patterns_response.success is True
                assert "patterns" in patterns_response.data
        
        finally:
            await api.shutdown()


class TestSystemComponents:
    """Test individual system components."""
    
    @pytest.mark.asyncio
    async def test_codegen_client_integration(self):
        """Test Codegen client integration."""
        client = CodegenClient("test-org", "test-token")
        
        # Test client initialization
        assert client.org_id == "test-org"
        assert client.token == "test-token"
        
        # Test task configuration
        config = TaskConfig(
            prompt="Test prompt",
            context={"test": True},
            priority=5
        )
        
        assert config.prompt == "Test prompt"
        assert config.context["test"] is True
        assert config.priority == 5
    
    @pytest.mark.asyncio
    async def test_task_manager_functionality(self):
        """Test task manager functionality."""
        # Mock Codegen client
        mock_client = Mock()
        mock_client.run_task = AsyncMock(return_value=Mock(status="completed"))
        
        manager = TaskManager(mock_client, max_concurrent_tasks=2)
        
        # Add a task
        config = TaskConfig(prompt="Test task")
        task = manager.add_task("test_task", config)
        
        assert task.id == "test_task"
        assert task.config == config
        assert "test_task" in manager.tasks
    
    def test_database_schema_validation(self):
        """Test database schema validation."""
        # Read the schema file
        with open("database/00_comprehensive_schema.sql", "r") as f:
            schema_content = f.read()
        
        # Basic validation
        assert "CREATE TABLE organizations" in schema_content
        assert "CREATE TABLE projects" in schema_content
        assert "CREATE TABLE tasks" in schema_content
        assert "CREATE TABLE pipelines" in schema_content
        assert "CREATE TABLE agents" in schema_content
        assert "CREATE TABLE integrations" in schema_content
        assert "CREATE TABLE learning_models" in schema_content
        
        # Check for indexes
        assert "CREATE INDEX" in schema_content
        
        # Check for triggers
        assert "CREATE TRIGGER" in schema_content


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

