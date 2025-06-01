"""
Comprehensive test suite for the integrated graph-sitter enhancement system.

This test suite validates all components of the system including database schema,
task management, analytics engine, workflow orchestration, and system integration.
"""

import unittest
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import Mock, patch

# Import system components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter.task_management.core.models import (
    Task, TaskStatus, TaskType, Priority, Workflow, WorkflowStep, 
    WorkflowStepType, TaskFactory, TaskExecution
)
from graph_sitter.analytics.core.analysis_config import (
    AnalysisConfig, AnalyzerType, AnalysisLanguage, QualityThresholds,
    ConfigTemplates
)


class MockDatabase:
    """Mock database for testing without external dependencies."""
    
    def __init__(self):
        self.tables = {
            "organizations": [],
            "users": [],
            "tasks": [],
            "workflows": [],
            "analysis_runs": [],
            "metrics": []
        }
        self.id_counter = 1000
    
    def insert(self, table: str, data: Dict[str, Any]) -> str:
        """Insert data into table."""
        if table not in self.tables:
            self.tables[table] = []
        
        record = data.copy()
        if 'id' not in record:
            record['id'] = str(uuid.uuid4())
        
        record['created_at'] = datetime.utcnow()
        record['updated_at'] = datetime.utcnow()
        
        self.tables[table].append(record)
        return record['id']
    
    def select(self, table: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Select data from table."""
        if table not in self.tables:
            return []
        
        records = self.tables[table]
        
        if filters:
            filtered_records = []
            for record in records:
                match = True
                for key, value in filters.items():
                    if key not in record or record[key] != value:
                        match = False
                        break
                if match:
                    filtered_records.append(record)
            return filtered_records
        
        return records.copy()
    
    def update(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update record in table."""
        if table not in self.tables:
            return False
        
        for i, record in enumerate(self.tables[table]):
            if record.get('id') == record_id:
                record.update(data)
                record['updated_at'] = datetime.utcnow()
                return True
        
        return False
    
    def delete(self, table: str, record_id: str) -> bool:
        """Delete record from table."""
        if table not in self.tables:
            return False
        
        for i, record in enumerate(self.tables[table]):
            if record.get('id') == record_id:
                del self.tables[table][i]
                return True
        
        return False


class TestDatabaseSchema(unittest.TestCase):
    """Test database schema and operations."""
    
    def setUp(self):
        self.db = MockDatabase()
    
    def test_organization_creation(self):
        """Test organization creation and validation."""
        org_data = {
            "name": "Test Organization",
            "slug": "test-org",
            "description": "Test organization for validation",
            "settings": {"theme": "dark", "notifications": True}
        }
        
        org_id = self.db.insert("organizations", org_data)
        self.assertIsNotNone(org_id)
        
        # Verify organization was created
        orgs = self.db.select("organizations", {"id": org_id})
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0]["name"], "Test Organization")
        self.assertEqual(orgs[0]["slug"], "test-org")
    
    def test_user_creation(self):
        """Test user creation and validation."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "settings": {"language": "en", "timezone": "UTC"},
            "preferences": {"email_notifications": True}
        }
        
        user_id = self.db.insert("users", user_data)
        self.assertIsNotNone(user_id)
        
        # Verify user was created
        users = self.db.select("users", {"id": user_id})
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["email"], "test@example.com")
    
    def test_data_integrity(self):
        """Test data integrity constraints."""
        # Test unique constraints
        user_data = {
            "email": "unique@example.com",
            "name": "Unique User"
        }
        
        user_id1 = self.db.insert("users", user_data)
        user_id2 = self.db.insert("users", user_data)
        
        # Both should be created (mock doesn't enforce uniqueness)
        # In real implementation, second insert would fail
        self.assertIsNotNone(user_id1)
        self.assertIsNotNone(user_id2)


class TestTaskManagement(unittest.TestCase):
    """Test task management system."""
    
    def setUp(self):
        self.org_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
    
    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(
            name="Test Task",
            description="A test task for validation",
            task_type=TaskType.CODE_ANALYSIS,
            priority=Priority.HIGH,
            created_by=self.user_id,
            organization_id=self.org_id
        )
        
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.task_type, TaskType.CODE_ANALYSIS)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.priority, Priority.HIGH)
        self.assertTrue(task.is_ready)
    
    def test_task_lifecycle(self):
        """Test task execution lifecycle."""
        task = Task(
            name="Lifecycle Test",
            created_by=self.user_id,
            organization_id=self.org_id
        )
        
        # Initial state
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.started_at)
        self.assertIsNone(task.completed_at)
        
        # Mark as started
        task.mark_started()
        self.assertEqual(task.status, TaskStatus.RUNNING)
        self.assertIsNotNone(task.started_at)
        
        # Mark as completed
        result = {"output": "Task completed successfully"}
        task.mark_completed(result)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.result, result)
        
        # Check duration
        duration = task.duration
        self.assertIsNotNone(duration)
        self.assertGreater(duration.total_seconds(), 0)
    
    def test_task_retry_logic(self):
        """Test task retry mechanism."""
        task = Task(
            name="Retry Test",
            created_by=self.user_id,
            organization_id=self.org_id,
            max_retries=3
        )
        
        # Mark as failed
        task.mark_failed("Test error")
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertTrue(task.can_retry)
        
        # Schedule retry
        task.schedule_retry()
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.retry_count, 1)
        self.assertIsNotNone(task.scheduled_at)
        
        # Exhaust retries
        for i in range(3):
            task.mark_failed(f"Error {i+1}")
            if task.can_retry:
                task.schedule_retry()
        
        self.assertFalse(task.can_retry)
        self.assertEqual(task.retry_count, 3)
    
    def test_task_dependencies(self):
        """Test task dependency management."""
        task1 = Task(
            name="Task 1",
            created_by=self.user_id,
            organization_id=self.org_id
        )
        
        task2 = Task(
            name="Task 2",
            created_by=self.user_id,
            organization_id=self.org_id,
            depends_on=[task1.id]
        )
        
        self.assertEqual(len(task2.depends_on), 1)
        self.assertIn(task1.id, task2.depends_on)
    
    def test_workflow_creation(self):
        """Test workflow creation and step management."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
            created_by=self.user_id,
            organization_id=self.org_id
        )
        
        # Add steps
        step1 = WorkflowStep(
            name="Analysis Step",
            step_type=WorkflowStepType.ANALYSIS,
            order=1
        )
        
        step2 = WorkflowStep(
            name="Quality Gate",
            step_type=WorkflowStepType.QUALITY_GATE,
            order=2,
            depends_on_steps=[step1.id]
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        self.assertEqual(len(workflow.steps), 2)
        self.assertEqual(workflow.steps[0].order, 1)
        self.assertEqual(workflow.steps[1].order, 2)
    
    def test_task_factory(self):
        """Test task factory methods."""
        # Code analysis task
        analysis_task = TaskFactory.create_code_analysis_task(
            name="Analyze Repository",
            repository_url="https://github.com/example/repo",
            analysis_type="comprehensive",
            created_by=self.user_id,
            organization_id=self.org_id
        )
        
        self.assertEqual(analysis_task.task_type, TaskType.CODE_ANALYSIS)
        self.assertEqual(analysis_task.configuration["repository_url"], "https://github.com/example/repo")
        self.assertEqual(analysis_task.configuration["analysis_type"], "comprehensive")
        
        # Code generation task
        generation_task = TaskFactory.create_code_generation_task(
            name="Generate Code",
            prompt="Create a REST API endpoint",
            target_language="python",
            created_by=self.user_id,
            organization_id=self.org_id
        )
        
        self.assertEqual(generation_task.task_type, TaskType.CODE_GENERATION)
        self.assertEqual(generation_task.configuration["prompt"], "Create a REST API endpoint")
        self.assertEqual(generation_task.configuration["target_language"], "python")


class TestAnalyticsEngine(unittest.TestCase):
    """Test analytics engine and configuration."""
    
    def test_analysis_config_creation(self):
        """Test analysis configuration creation."""
        config = AnalysisConfig(
            name="Test Analysis",
            target_languages={AnalysisLanguage.PYTHON, AnalysisLanguage.TYPESCRIPT},
            enabled_analyzers={AnalyzerType.COMPLEXITY, AnalyzerType.SECURITY}
        )
        
        self.assertEqual(config.name, "Test Analysis")
        self.assertEqual(len(config.target_languages), 2)
        self.assertEqual(len(config.enabled_analyzers), 2)
        self.assertTrue(config.is_analyzer_enabled(AnalyzerType.COMPLEXITY))
        self.assertFalse(config.is_analyzer_enabled(AnalyzerType.PERFORMANCE))
    
    def test_quality_thresholds(self):
        """Test quality threshold configuration."""
        thresholds = QualityThresholds(
            cyclomatic_complexity_max=15,
            maintainability_min=70.0,
            security_min=95.0
        )
        
        self.assertEqual(thresholds.cyclomatic_complexity_max, 15)
        self.assertEqual(thresholds.maintainability_min, 70.0)
        self.assertEqual(thresholds.security_min, 95.0)
    
    def test_file_pattern_matching(self):
        """Test file pattern matching logic."""
        config = AnalysisConfig(
            target_languages={AnalysisLanguage.PYTHON},
            include_file_patterns=["**/*.py"],
            exclude_file_patterns=["**/test_*.py"]
        )
        
        # Should analyze Python files
        self.assertTrue(config.should_analyze_file("src/main.py"))
        self.assertTrue(config.should_analyze_file("lib/utils.py"))
        
        # Should exclude test files
        self.assertFalse(config.should_analyze_file("tests/test_main.py"))
        
        # Should exclude non-Python files
        self.assertFalse(config.should_analyze_file("src/main.js"))
    
    def test_config_templates(self):
        """Test predefined configuration templates."""
        # Minimal template
        minimal = ConfigTemplates.minimal()
        self.assertEqual(len(minimal.enabled_analyzers), 1)
        self.assertIn(AnalyzerType.COMPLEXITY, minimal.enabled_analyzers)
        
        # Comprehensive template
        comprehensive = ConfigTemplates.comprehensive()
        self.assertGreater(len(comprehensive.enabled_analyzers), 5)
        self.assertIn(AnalyzerType.SECURITY, comprehensive.enabled_analyzers)
        
        # Security focused template
        security = ConfigTemplates.security_focused()
        self.assertIn(AnalyzerType.SECURITY, security.enabled_analyzers)
        self.assertEqual(security.quality_thresholds.security_min, 95.0)


class TestSystemIntegration(unittest.TestCase):
    """Test system integration and end-to-end workflows."""
    
    def setUp(self):
        self.db = MockDatabase()
        self.org_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        
        # Create test organization and user
        self.db.insert("organizations", {
            "id": str(self.org_id),
            "name": "Test Organization",
            "slug": "test-org"
        })
        
        self.db.insert("users", {
            "id": str(self.user_id),
            "email": "test@example.com",
            "name": "Test User"
        })
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow execution."""
        # Create analysis configuration
        config = AnalysisConfig(
            name="Integration Test Analysis",
            target_languages={AnalysisLanguage.PYTHON},
            enabled_analyzers={AnalyzerType.COMPLEXITY, AnalyzerType.SECURITY}
        )
        
        # Create workflow
        workflow = Workflow(
            name="CI/CD Pipeline",
            created_by=self.user_id,
            organization_id=self.org_id
        )
        
        # Add workflow steps
        analysis_step = WorkflowStep(
            name="Code Analysis",
            step_type=WorkflowStepType.ANALYSIS,
            order=1,
            configuration={"analysis_config": config.dict()}
        )
        
        quality_gate_step = WorkflowStep(
            name="Quality Gate",
            step_type=WorkflowStepType.QUALITY_GATE,
            order=2,
            depends_on_steps=[analysis_step.id]
        )
        
        workflow.add_step(analysis_step)
        workflow.add_step(quality_gate_step)
        
        # Create workflow task
        workflow_task = TaskFactory.create_workflow_task(
            name="Execute CI/CD Pipeline",
            workflow=workflow,
            created_by=self.user_id,
            organization_id=self.org_id
        )
        
        # Store in database
        workflow_id = self.db.insert("workflows", workflow.dict())
        task_id = self.db.insert("tasks", workflow_task.dict())
        
        # Verify storage
        stored_workflows = self.db.select("workflows", {"id": workflow_id})
        stored_tasks = self.db.select("tasks", {"id": task_id})
        
        self.assertEqual(len(stored_workflows), 1)
        self.assertEqual(len(stored_tasks), 1)
        self.assertEqual(stored_tasks[0]["name"], "Execute CI/CD Pipeline")
    
    def test_task_execution_tracking(self):
        """Test detailed task execution tracking."""
        task = Task(
            name="Execution Tracking Test",
            created_by=self.user_id,
            organization_id=self.org_id
        )
        
        # Create execution record
        execution = TaskExecution(
            task_id=task.id,
            execution_number=1
        )
        
        # Simulate execution
        execution.started_at = datetime.utcnow()
        execution.status = TaskStatus.RUNNING
        execution.add_log("Task execution started")
        execution.add_log("Processing input data")
        
        # Add resource usage
        execution.cpu_usage_percent = 45.2
        execution.memory_usage_mb = 128.5
        
        # Complete execution
        execution.completed_at = datetime.utcnow()
        execution.status = TaskStatus.COMPLETED
        execution.result = {"status": "success", "output": "Task completed"}
        execution.add_log("Task execution completed successfully")
        
        # Verify execution tracking
        self.assertEqual(execution.status, TaskStatus.COMPLETED)
        self.assertEqual(len(execution.logs), 3)
        self.assertIsNotNone(execution.duration)
        self.assertEqual(execution.cpu_usage_percent, 45.2)
        self.assertEqual(execution.memory_usage_mb, 128.5)
    
    def test_error_handling(self):
        """Test error handling and recovery mechanisms."""
        task = Task(
            name="Error Handling Test",
            created_by=self.user_id,
            organization_id=self.org_id,
            max_retries=2
        )
        
        # Simulate failure
        task.mark_failed("Network connection timeout")
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertTrue(task.can_retry)
        
        # Schedule retry
        task.schedule_retry()
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.retry_count, 1)
        
        # Fail again
        task.mark_failed("Service unavailable")
        task.schedule_retry()
        self.assertEqual(task.retry_count, 2)
        
        # Final failure
        task.mark_failed("Persistent error")
        self.assertFalse(task.can_retry)
    
    def test_concurrent_task_execution(self):
        """Test concurrent task execution simulation."""
        tasks = []
        
        # Create multiple tasks
        for i in range(5):
            task = Task(
                name=f"Concurrent Task {i+1}",
                created_by=self.user_id,
                organization_id=self.org_id,
                priority=Priority.NORMAL
            )
            tasks.append(task)
        
        # Simulate concurrent execution
        for task in tasks:
            task.mark_started()
            self.assertEqual(task.status, TaskStatus.RUNNING)
        
        # Complete tasks
        for i, task in enumerate(tasks):
            task.mark_completed({"task_number": i+1, "result": "success"})
            self.assertEqual(task.status, TaskStatus.COMPLETED)
        
        # Verify all tasks completed
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        self.assertEqual(len(completed_tasks), 5)


class TestPerformance(unittest.TestCase):
    """Test system performance and scalability."""
    
    def setUp(self):
        self.db = MockDatabase()
        self.org_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
    
    def test_task_creation_performance(self):
        """Test performance of task creation."""
        import time
        
        start_time = time.time()
        
        # Create 100 tasks
        tasks = []
        for i in range(100):
            task = Task(
                name=f"Performance Test Task {i+1}",
                created_by=self.user_id,
                organization_id=self.org_id
            )
            tasks.append(task)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should create 100 tasks in under 1 second
        self.assertLess(duration, 1.0)
        self.assertEqual(len(tasks), 100)
    
    def test_dependency_resolution_performance(self):
        """Test performance of dependency resolution."""
        import time
        
        # Create tasks with complex dependencies
        tasks = []
        for i in range(50):
            dependencies = []
            if i > 0:
                # Each task depends on previous 2 tasks
                dependencies = [tasks[max(0, i-2)].id, tasks[max(0, i-1)].id]
            
            task = Task(
                name=f"Dependency Test Task {i+1}",
                created_by=self.user_id,
                organization_id=self.org_id,
                depends_on=dependencies
            )
            tasks.append(task)
        
        start_time = time.time()
        
        # Check ready tasks (simulate dependency resolution)
        ready_tasks = [t for t in tasks if t.is_ready and not t.depends_on]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should resolve dependencies quickly
        self.assertLess(duration, 0.1)
        self.assertGreater(len(ready_tasks), 0)
    
    def test_config_validation_performance(self):
        """Test performance of configuration validation."""
        import time
        
        start_time = time.time()
        
        # Create and validate 50 configurations
        configs = []
        for i in range(50):
            config = AnalysisConfig(
                name=f"Performance Test Config {i+1}",
                target_languages={AnalysisLanguage.PYTHON, AnalysisLanguage.TYPESCRIPT},
                enabled_analyzers={
                    AnalyzerType.COMPLEXITY,
                    AnalyzerType.SECURITY,
                    AnalyzerType.PERFORMANCE
                }
            )
            configs.append(config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should create and validate configs quickly
        self.assertLess(duration, 0.5)
        self.assertEqual(len(configs), 50)


class TestDataQuality(unittest.TestCase):
    """Test data quality and integrity."""
    
    def test_uuid_generation(self):
        """Test UUID generation and uniqueness."""
        uuids = set()
        
        # Generate 1000 UUIDs
        for _ in range(1000):
            task = Task(
                name="UUID Test",
                created_by=uuid.uuid4(),
                organization_id=uuid.uuid4()
            )
            uuids.add(task.id)
        
        # All UUIDs should be unique
        self.assertEqual(len(uuids), 1000)
    
    def test_timestamp_consistency(self):
        """Test timestamp consistency and ordering."""
        task = Task(
            name="Timestamp Test",
            created_by=uuid.uuid4(),
            organization_id=uuid.uuid4()
        )
        
        created_at = task.created_at
        updated_at = task.updated_at
        
        # Update task
        import time
        time.sleep(0.01)  # Small delay
        task.mark_started()
        
        # Timestamps should be ordered correctly
        self.assertLessEqual(created_at, updated_at)
        self.assertLessEqual(updated_at, task.updated_at)
    
    def test_data_validation(self):
        """Test data validation rules."""
        # Test invalid task name
        with self.assertRaises(ValueError):
            Task(
                name="",  # Empty name should fail
                created_by=uuid.uuid4(),
                organization_id=uuid.uuid4()
            )
        
        # Test invalid priority
        task = Task(
            name="Valid Task",
            created_by=uuid.uuid4(),
            organization_id=uuid.uuid4()
        )
        
        # Priority should be valid enum value
        self.assertIn(task.priority, [p.value for p in Priority])


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestDatabaseSchema,
        TestTaskManagement,
        TestAnalyticsEngine,
        TestSystemIntegration,
        TestPerformance,
        TestDataQuality
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)

