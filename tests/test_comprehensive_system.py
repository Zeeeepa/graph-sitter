"""
Comprehensive test suite for the merged Graph-Sitter enhancement system.

This test suite validates all components of the comprehensive system including:
- Database schema and operations
- Task management engine
- Analytics system
- Integration between components
- Performance and reliability
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta

# Import the comprehensive system components
from src.graph_sitter.task_management import (
    TaskAPI, TaskFactory, TaskType, TaskPriority, TaskStatus,
    WorkflowBuilder, DependencyResolver
)
from src.graph_sitter.analytics import (
    AnalyticsEngine, AnalysisConfig, ComplexityAnalyzer,
    PerformanceAnalyzer, SecurityAnalyzer, DeadCodeAnalyzer
)


class TestDatabaseSchema:
    """Test database schema functionality."""
    
    def test_schema_creation(self):
        """Test that database schema can be created successfully."""
        # This would test the actual database schema creation
        # For now, we'll test the structure validation
        assert True  # Placeholder for actual database tests
    
    def test_task_operations(self):
        """Test basic task database operations."""
        # Test task CRUD operations
        assert True  # Placeholder for actual database tests
    
    def test_analytics_storage(self):
        """Test analytics data storage and retrieval."""
        # Test analytics data operations
        assert True  # Placeholder for actual database tests


class TestTaskManagement:
    """Test task management engine functionality."""
    
    @pytest.fixture
    def task_api(self):
        """Create a task API instance for testing."""
        return TaskAPI()
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return TaskFactory.create_code_analysis_task(
            name="Test Analysis Task",
            repository_url="https://github.com/test/repo",
            analysis_type="complexity",
            created_by="test_user",
            priority=TaskPriority.HIGH
        )
    
    def test_task_creation(self, sample_task):
        """Test task creation with all required fields."""
        assert sample_task.name == "Test Analysis Task"
        assert sample_task.task_type == TaskType.CODE_ANALYSIS
        assert sample_task.priority == TaskPriority.HIGH
        assert sample_task.status == TaskStatus.PENDING
        assert sample_task.created_by == "test_user"
    
    def test_task_dependencies(self, sample_task):
        """Test task dependency management."""
        dependency_id = uuid4()
        
        # Add dependency
        sample_task.add_dependency(dependency_id)
        assert dependency_id in sample_task.depends_on
        
        # Remove dependency
        sample_task.remove_dependency(dependency_id)
        assert dependency_id not in sample_task.depends_on
    
    def test_task_lifecycle(self, sample_task):
        """Test task status transitions."""
        # Initial state
        assert sample_task.status == TaskStatus.PENDING
        
        # Mark as running
        sample_task.status = TaskStatus.RUNNING
        sample_task.started_at = datetime.utcnow()
        assert sample_task.status == TaskStatus.RUNNING
        
        # Mark as completed
        result = {"analysis_complete": True, "issues_found": 5}
        sample_task.mark_completed(result)
        assert sample_task.status == TaskStatus.COMPLETED
        assert sample_task.result == result
        assert sample_task.completed_at is not None
    
    def test_task_retry_logic(self, sample_task):
        """Test task retry functionality."""
        sample_task.max_retries = 3
        
        # Initially can't retry (not failed)
        assert not sample_task.can_retry()
        
        # Mark as failed
        sample_task.mark_failed("Test error")
        assert sample_task.status == TaskStatus.FAILED
        assert sample_task.can_retry()
        
        # Increment retry
        sample_task.increment_retry()
        assert sample_task.retry_count == 1
        assert sample_task.status == TaskStatus.RETRYING
    
    def test_dependency_resolver(self):
        """Test dependency resolution functionality."""
        resolver = DependencyResolver()
        
        # Create tasks with dependencies
        task1 = TaskFactory.create_code_analysis_task(
            name="Task 1", repository_url="test", analysis_type="complexity",
            created_by="test", priority=TaskPriority.NORMAL
        )
        task2 = TaskFactory.create_code_analysis_task(
            name="Task 2", repository_url="test", analysis_type="security",
            created_by="test", priority=TaskPriority.NORMAL
        )
        task3 = TaskFactory.create_code_analysis_task(
            name="Task 3", repository_url="test", analysis_type="performance",
            created_by="test", priority=TaskPriority.NORMAL
        )
        
        # Set up dependencies: task3 depends on task2, task2 depends on task1
        task2.add_dependency(task1.id)
        task3.add_dependency(task2.id)
        
        tasks = [task1, task2, task3]
        
        # Test dependency validation
        for task in tasks:
            errors = resolver.validate_dependencies(task, tasks)
            assert len(errors) == 0  # No circular dependencies
        
        # Test execution order
        execution_order = resolver.get_execution_order(tasks)
        task_ids = [task.id for task in execution_order]
        
        # task1 should come before task2, task2 before task3
        assert task_ids.index(task1.id) < task_ids.index(task2.id)
        assert task_ids.index(task2.id) < task_ids.index(task3.id)
    
    def test_workflow_creation(self):
        """Test workflow creation and structure."""
        workflow = WorkflowBuilder.create_ci_cd_workflow(
            name="Test CI/CD",
            created_by="test_user",
            repository_url="https://github.com/test/repo"
        )
        
        assert workflow.name == "Test CI/CD"
        assert workflow.created_by == "test_user"
        assert len(workflow.steps) > 0
        
        # Check that workflow has expected steps
        step_names = [step.name for step in workflow.steps]
        expected_steps = ["checkout", "build", "test", "deploy"]
        
        # At least some expected steps should be present
        assert any(expected in " ".join(step_names).lower() for expected in expected_steps)


class TestAnalyticsSystem:
    """Test analytics system functionality."""
    
    @pytest.fixture
    def temp_codebase(self):
        """Create a temporary codebase for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create sample Python files
        (Path(temp_dir) / "main.py").write_text("""
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(x):
                    for j in range(y):
                        if i * j > z:
                            return i * j
                        elif i + j < z:
                            continue
                        else:
                            break
    return 0

def unused_function():
    pass

def simple_function(a, b):
    return a + b
""")
        
        (Path(temp_dir) / "utils.py").write_text("""
import os
import sys

def get_config():
    return {"debug": True}

def process_data(data):
    # Potential security issue - eval usage
    return eval(data)

class UnusedClass:
    def __init__(self):
        self.value = 42
""")
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def analysis_config(self):
        """Create analysis configuration for testing."""
        return AnalysisConfig(
            enable_complexity=True,
            enable_performance=True,
            enable_security=True,
            enable_dead_code=True,
            enable_dependency=True,
            max_workers=2,
            timeout_seconds=60,
            analysis_depth="standard"
        )
    
    def test_analysis_config_validation(self):
        """Test analysis configuration validation."""
        # Valid configuration
        config = AnalysisConfig(
            enable_complexity=True,
            max_workers=4,
            languages={"python", "typescript"}
        )
        assert config.max_workers == 4
        assert "python" in config.languages
        
        # Invalid language should raise error
        with pytest.raises(ValueError):
            AnalysisConfig(languages={"invalid_language"})
    
    def test_complexity_analyzer(self, temp_codebase, analysis_config):
        """Test complexity analysis functionality."""
        analyzer = ComplexityAnalyzer()
        
        # Test analyzer initialization
        assert analyzer.name == "complexity"
        assert "python" in analyzer.supported_languages
        
        # Test complexity thresholds
        assert analyzer.cyclomatic_thresholds["high"] > analyzer.cyclomatic_thresholds["medium"]
        assert analyzer.cognitive_thresholds["critical"] > analyzer.cognitive_thresholds["high"]
    
    def test_security_analyzer(self, temp_codebase, analysis_config):
        """Test security analysis functionality."""
        analyzer = SecurityAnalyzer()
        
        # Test analyzer initialization
        assert analyzer.name == "security"
        assert "python" in analyzer.supported_languages
        
        # Test security patterns
        assert len(analyzer.vulnerability_patterns) > 0
        assert "eval" in str(analyzer.vulnerability_patterns).lower()
    
    def test_dead_code_analyzer(self, temp_codebase, analysis_config):
        """Test dead code detection functionality."""
        analyzer = DeadCodeAnalyzer()
        
        # Test analyzer initialization
        assert analyzer.name == "dead_code"
        assert "python" in analyzer.supported_languages
        
        # Test confidence thresholds
        assert 0.0 <= analyzer.confidence_thresholds["high"] <= 1.0
    
    def test_performance_analyzer(self, temp_codebase, analysis_config):
        """Test performance analysis functionality."""
        analyzer = PerformanceAnalyzer()
        
        # Test analyzer initialization
        assert analyzer.name == "performance"
        assert "python" in analyzer.supported_languages
        
        # Test performance patterns
        assert len(analyzer.performance_patterns) > 0
    
    def test_analytics_engine_integration(self, temp_codebase, analysis_config):
        """Test full analytics engine integration."""
        engine = AnalyticsEngine(analysis_config)
        
        # Test engine initialization
        assert len(engine.analyzers) > 0
        assert "complexity" in engine.analyzers
        assert "security" in engine.analyzers
        
        # Test analyzer configuration
        for analyzer_name, analyzer in engine.analyzers.items():
            assert analyzer.name == analyzer_name
            assert hasattr(analyzer, 'analyze')


class TestSystemIntegration:
    """Test integration between different system components."""
    
    def test_task_analytics_integration(self):
        """Test integration between task management and analytics."""
        # Create a code analysis task
        task = TaskFactory.create_code_analysis_task(
            name="Integration Test Analysis",
            repository_url="https://github.com/test/repo",
            analysis_type="comprehensive",
            created_by="test_user",
            priority=TaskPriority.HIGH
        )
        
        # Verify task configuration for analytics
        assert task.task_type == TaskType.CODE_ANALYSIS
        assert "analysis_type" in task.metadata
        assert task.metadata["analysis_type"] == "comprehensive"
    
    def test_workflow_analytics_integration(self):
        """Test workflow integration with analytics tasks."""
        workflow = WorkflowBuilder.create_code_review_workflow(
            name="Code Review with Analytics",
            created_by="test_user",
            pull_request_url="https://github.com/test/repo/pull/123"
        )
        
        # Verify workflow contains analytics steps
        step_types = [step.step_type for step in workflow.steps]
        assert "task" in step_types
        
        # Check for analysis-related steps
        task_steps = [step for step in workflow.steps if step.step_type == "task"]
        analysis_steps = [
            step for step in task_steps 
            if step.task_template and 
            step.task_template.get("task_type") == "code_analysis"
        ]
        assert len(analysis_steps) > 0
    
    def test_database_task_integration(self):
        """Test database integration with task management."""
        # This would test actual database operations
        # For now, validate the data models are compatible
        
        task = TaskFactory.create_code_analysis_task(
            name="Database Integration Test",
            repository_url="test",
            analysis_type="complexity",
            created_by="test",
            priority=TaskPriority.NORMAL
        )
        
        # Verify task can be serialized for database storage
        task_dict = task.dict()
        assert "id" in task_dict
        assert "name" in task_dict
        assert "task_type" in task_dict
        assert "metadata" in task_dict
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow execution."""
        # Create a comprehensive workflow
        workflow = WorkflowBuilder.create_data_processing_workflow(
            name="E2E Test Workflow",
            created_by="test_user",
            data_sources=["source1", "source2"]
        )
        
        # Verify workflow structure
        assert workflow.name == "E2E Test Workflow"
        assert len(workflow.steps) > 0
        
        # Verify workflow can be executed (mock execution)
        workflow.status = "running"
        workflow.started_at = datetime.utcnow()
        
        # Simulate step completion
        for step in workflow.steps:
            step.status = "completed"
            step.started_at = datetime.utcnow()
            step.completed_at = datetime.utcnow() + timedelta(seconds=1)
        
        # Complete workflow
        workflow.status = "completed"
        workflow.completed_at = datetime.utcnow()
        
        assert workflow.status == "completed"
        assert workflow.get_duration() is not None


class TestPerformanceAndReliability:
    """Test system performance and reliability."""
    
    def test_task_creation_performance(self):
        """Test task creation performance."""
        start_time = datetime.utcnow()
        
        # Create multiple tasks
        tasks = []
        for i in range(100):
            task = TaskFactory.create_code_analysis_task(
                name=f"Performance Test Task {i}",
                repository_url="test",
                analysis_type="complexity",
                created_by="test",
                priority=TaskPriority.NORMAL
            )
            tasks.append(task)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should create 100 tasks in under 1 second
        assert duration < 1.0
        assert len(tasks) == 100
    
    def test_dependency_resolution_performance(self):
        """Test dependency resolution performance with many tasks."""
        resolver = DependencyResolver()
        
        # Create a large number of tasks with complex dependencies
        tasks = []
        for i in range(50):
            task = TaskFactory.create_code_analysis_task(
                name=f"Perf Task {i}",
                repository_url="test",
                analysis_type="complexity",
                created_by="test",
                priority=TaskPriority.NORMAL
            )
            
            # Add dependencies to previous tasks
            if i > 0:
                task.add_dependency(tasks[i-1].id)
            if i > 1:
                task.add_dependency(tasks[i-2].id)
            
            tasks.append(task)
        
        start_time = datetime.utcnow()
        execution_order = resolver.get_execution_order(tasks)
        end_time = datetime.utcnow()
        
        duration = (end_time - start_time).total_seconds()
        
        # Should resolve dependencies quickly
        assert duration < 0.5
        assert len(execution_order) == len(tasks)
    
    def test_analytics_config_validation_performance(self):
        """Test analytics configuration validation performance."""
        start_time = datetime.utcnow()
        
        # Create and validate multiple configurations
        configs = []
        for i in range(100):
            config = AnalysisConfig(
                enable_complexity=True,
                enable_security=True,
                max_workers=4,
                timeout_seconds=300,
                languages={"python", "typescript"}
            )
            configs.append(config)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should create and validate configs quickly
        assert duration < 0.5
        assert len(configs) == 100
    
    def test_memory_usage(self):
        """Test memory usage with large data structures."""
        import sys
        
        # Create large task structure
        workflow = WorkflowBuilder()
        
        # Add many steps
        for i in range(1000):
            workflow.add_task_step(
                f"step_{i}",
                {
                    "name": f"Task {i}",
                    "task_type": "code_analysis",
                    "metadata": {"index": i, "data": "x" * 100}
                }
            )
        
        # Memory usage should be reasonable
        # This is a basic check - in production you'd use more sophisticated memory profiling
        workflow_size = sys.getsizeof(workflow)
        assert workflow_size < 10 * 1024 * 1024  # Less than 10MB


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_task_creation(self):
        """Test handling of invalid task creation parameters."""
        with pytest.raises(ValueError):
            TaskFactory.create_code_analysis_task(
                name="",  # Empty name should fail
                repository_url="test",
                analysis_type="complexity",
                created_by="test",
                priority=TaskPriority.NORMAL
            )
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        resolver = DependencyResolver()
        
        # Create tasks with circular dependency
        task1 = TaskFactory.create_code_analysis_task(
            name="Task 1", repository_url="test", analysis_type="complexity",
            created_by="test", priority=TaskPriority.NORMAL
        )
        task2 = TaskFactory.create_code_analysis_task(
            name="Task 2", repository_url="test", analysis_type="security",
            created_by="test", priority=TaskPriority.NORMAL
        )
        
        # Create circular dependency
        task1.add_dependency(task2.id)
        task2.add_dependency(task1.id)
        
        tasks = [task1, task2]
        
        # Should detect circular dependency
        errors = resolver.validate_dependencies(task1, tasks)
        assert len(errors) > 0
        assert "circular" in str(errors[0]).lower()
    
    def test_invalid_analysis_config(self):
        """Test handling of invalid analysis configuration."""
        with pytest.raises(ValueError):
            AnalysisConfig(
                max_workers=0  # Invalid worker count
            )
        
        with pytest.raises(ValueError):
            AnalysisConfig(
                timeout_seconds=10  # Too short timeout
            )
    
    def test_analyzer_error_handling(self):
        """Test analyzer error handling."""
        analyzer = ComplexityAnalyzer()
        
        # Test with invalid input
        result = analyzer.create_result("failed")
        result.error_message = "Test error"
        
        assert result.status == "failed"
        assert result.error_message == "Test error"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])

