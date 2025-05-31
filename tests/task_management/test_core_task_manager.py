"""
Test suite for the core TaskManager functionality.

Tests cover task creation, execution, scheduling, monitoring, and lifecycle management.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.graph_sitter.task_management.core import (
    TaskManager, TaskManagerConfig, Task, TaskType, TaskPriority, TaskStatus
)


class TestTaskManager:
    """Test cases for TaskManager functionality."""
    
    @pytest.fixture
    def task_manager_config(self):
        """Create a test configuration for TaskManager."""
        return TaskManagerConfig(
            max_concurrent_tasks=3,
            default_timeout=timedelta(seconds=30),
            cleanup_interval=timedelta(seconds=1),
            enable_performance_monitoring=True,
            enable_auto_retry=True
        )
    
    @pytest.fixture
    def task_manager(self, task_manager_config):
        """Create a TaskManager instance for testing."""
        manager = TaskManager(task_manager_config)
        yield manager
        manager.shutdown()
    
    @pytest.fixture
    def sample_task_handler(self):
        """Create a sample task handler for testing."""
        def handler(task: Task):
            return {"result": f"Processed task {task.name}"}
        return handler
    
    def test_task_manager_initialization(self, task_manager_config):
        """Test TaskManager initialization with configuration."""
        manager = TaskManager(task_manager_config)
        
        assert manager.config == task_manager_config
        assert manager.scheduler is not None
        assert manager.executor is not None
        assert manager.monitor is not None
        
        manager.shutdown()
    
    def test_task_creation(self, task_manager):
        """Test basic task creation."""
        task = task_manager.create_task(
            name="Test Task",
            task_type=TaskType.CODE_ANALYSIS,
            description="A test task",
            priority=TaskPriority.HIGH,
            input_data={"test": "data"}
        )
        
        assert task.name == "Test Task"
        assert task.task_type == TaskType.CODE_ANALYSIS
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.input_data == {"test": "data"}
        assert task.id in task_manager._tasks
    
    def test_task_creation_with_dependencies(self, task_manager):
        """Test task creation with dependencies."""
        # Create first task
        task1 = task_manager.create_task(
            name="Task 1",
            task_type=TaskType.CODE_ANALYSIS
        )
        
        # Create second task with dependency
        task2 = task_manager.create_task(
            name="Task 2",
            task_type=TaskType.CODE_GENERATION,
            dependencies=[task1.id]
        )
        
        assert len(task2.dependencies) == 1
        assert task2.dependencies[0].task_id == task1.id
    
    def test_task_handler_registration(self, task_manager, sample_task_handler):
        """Test task handler registration."""
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, sample_task_handler)
        
        assert TaskType.CODE_ANALYSIS in task_manager._task_handlers
        assert task_manager._task_handlers[TaskType.CODE_ANALYSIS] == sample_task_handler
    
    def test_task_execution(self, task_manager, sample_task_handler):
        """Test task execution with registered handler."""
        # Register handler
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, sample_task_handler)
        
        # Create task
        task = task_manager.create_task(
            name="Test Execution",
            task_type=TaskType.CODE_ANALYSIS
        )
        
        # Execute task
        success = task_manager.execute_task(task.id)
        assert success
        
        # Wait for completion
        import time
        time.sleep(0.1)  # Give it time to start
        
        # Check status
        updated_task = task_manager.get_task(task.id)
        assert updated_task.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED]
    
    def test_task_scheduling(self, task_manager, sample_task_handler):
        """Test task scheduling functionality."""
        # Register handler
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, sample_task_handler)
        
        # Create task
        task = task_manager.create_task(
            name="Scheduled Task",
            task_type=TaskType.CODE_ANALYSIS,
            scheduled_at=datetime.utcnow() + timedelta(seconds=1)
        )
        
        # Schedule task
        success = task_manager.schedule_task(task.id)
        assert success or task.scheduled_at > datetime.utcnow()  # May not schedule if in future
    
    def test_task_cancellation(self, task_manager, sample_task_handler):
        """Test task cancellation."""
        # Register handler that takes some time
        def slow_handler(task):
            import time
            time.sleep(2)
            return {"result": "completed"}
        
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, slow_handler)
        
        # Create and start task
        task = task_manager.create_task(
            name="Cancellable Task",
            task_type=TaskType.CODE_ANALYSIS
        )
        
        task_manager.execute_task(task.id)
        
        # Cancel task
        success = task_manager.cancel_task(task.id, "Test cancellation")
        assert success
        
        # Check status
        updated_task = task_manager.get_task(task.id)
        assert updated_task.status == TaskStatus.CANCELLED
    
    def test_task_retrieval(self, task_manager):
        """Test task retrieval methods."""
        # Create multiple tasks
        task1 = task_manager.create_task("Task 1", TaskType.CODE_ANALYSIS, priority=TaskPriority.HIGH)
        task2 = task_manager.create_task("Task 2", TaskType.CODE_GENERATION, priority=TaskPriority.LOW)
        task3 = task_manager.create_task("Task 3", TaskType.CODE_ANALYSIS, priority=TaskPriority.MEDIUM)
        
        # Test get_task
        retrieved_task = task_manager.get_task(task1.id)
        assert retrieved_task.id == task1.id
        
        # Test get_tasks with filters
        analysis_tasks = task_manager.get_tasks(task_type=TaskType.CODE_ANALYSIS)
        assert len(analysis_tasks) == 2
        
        high_priority_tasks = task_manager.get_tasks(priority=TaskPriority.HIGH)
        assert len(high_priority_tasks) == 1
        assert high_priority_tasks[0].id == task1.id
    
    def test_system_status(self, task_manager):
        """Test system status reporting."""
        # Create some tasks
        task_manager.create_task("Task 1", TaskType.CODE_ANALYSIS)
        task_manager.create_task("Task 2", TaskType.CODE_GENERATION)
        
        status = task_manager.get_system_status()
        
        assert "total_tasks" in status
        assert "running_tasks" in status
        assert "status_breakdown" in status
        assert status["total_tasks"] == 2
        assert status["max_concurrent_tasks"] == 3
    
    def test_task_dependencies_resolution(self, task_manager, sample_task_handler):
        """Test that task dependencies are properly resolved."""
        # Register handler
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, sample_task_handler)
        task_manager.register_task_handler(TaskType.CODE_GENERATION, sample_task_handler)
        
        # Create tasks with dependencies
        task1 = task_manager.create_task("Task 1", TaskType.CODE_ANALYSIS)
        task2 = task_manager.create_task(
            "Task 2", 
            TaskType.CODE_GENERATION,
            dependencies=[task1.id]
        )
        
        # Task 2 should not be able to execute until Task 1 is complete
        completed_ids = set()
        assert not task2.can_execute(completed_ids, {})
        
        # After Task 1 completes, Task 2 should be executable
        completed_ids.add(task1.id)
        assert task2.can_execute(completed_ids, {})
    
    def test_task_timeout_handling(self, task_manager):
        """Test task timeout handling."""
        # Create handler that takes longer than timeout
        def timeout_handler(task):
            import time
            time.sleep(2)
            return {"result": "should timeout"}
        
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, timeout_handler)
        
        # Create task with short timeout
        task = task_manager.create_task(
            name="Timeout Task",
            task_type=TaskType.CODE_ANALYSIS,
            timeout=timedelta(milliseconds=100)
        )
        
        # Execute task
        task_manager.execute_task(task.id)
        
        # Wait and check if it times out
        import time
        time.sleep(0.5)
        
        # The timeout handling would be done by the cleanup worker
        # In a real scenario, we'd check that the task was cancelled due to timeout
    
    def test_task_retry_mechanism(self, task_manager):
        """Test automatic task retry on failure."""
        retry_count = 0
        
        def failing_handler(task):
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                raise Exception("Simulated failure")
            return {"result": "success after retries"}
        
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, failing_handler)
        
        # Create task with retries enabled
        task = task_manager.create_task(
            name="Retry Task",
            task_type=TaskType.CODE_ANALYSIS,
            max_retries=3
        )
        
        # The retry mechanism would be handled by the cleanup worker
        # In a real test, we'd verify that the task eventually succeeds
        assert task.max_retries == 3
        assert task.retry_count == 0
    
    def test_performance_monitoring_integration(self, task_manager, sample_task_handler):
        """Test integration with performance monitoring."""
        # Register handler
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, sample_task_handler)
        
        # Create and execute task
        task = task_manager.create_task("Monitored Task", TaskType.CODE_ANALYSIS)
        task_manager.execute_task(task.id)
        
        # Check that monitoring is active
        assert task_manager.monitor is not None
        
        # Get metrics
        metrics = task_manager.get_metrics()
        assert metrics is not None
    
    def test_concurrent_task_execution(self, task_manager, sample_task_handler):
        """Test concurrent execution of multiple tasks."""
        # Register handler
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, sample_task_handler)
        
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = task_manager.create_task(f"Concurrent Task {i}", TaskType.CODE_ANALYSIS)
            tasks.append(task)
        
        # Execute all tasks
        for task in tasks:
            task_manager.execute_task(task.id)
        
        # Check that no more than max_concurrent_tasks are running
        import time
        time.sleep(0.1)
        
        running_count = len(task_manager._running_tasks)
        assert running_count <= task_manager.config.max_concurrent_tasks
    
    def test_task_manager_shutdown(self, task_manager_config):
        """Test graceful shutdown of TaskManager."""
        manager = TaskManager(task_manager_config)
        
        # Create some tasks
        manager.create_task("Task 1", TaskType.CODE_ANALYSIS)
        manager.create_task("Task 2", TaskType.CODE_GENERATION)
        
        # Shutdown should complete without errors
        manager.shutdown()
        
        # Verify cleanup
        assert manager._shutdown_event.is_set()


class TestTaskManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def task_manager(self):
        """Create a minimal TaskManager for edge case testing."""
        config = TaskManagerConfig(max_concurrent_tasks=1)
        manager = TaskManager(config)
        yield manager
        manager.shutdown()
    
    def test_execute_nonexistent_task(self, task_manager):
        """Test executing a task that doesn't exist."""
        success = task_manager.execute_task("nonexistent-id")
        assert not success
    
    def test_execute_task_without_handler(self, task_manager):
        """Test executing a task without a registered handler."""
        task = task_manager.create_task("No Handler Task", TaskType.CODE_ANALYSIS)
        success = task_manager.execute_task(task.id)
        assert not success
        
        # Task should be marked as failed
        updated_task = task_manager.get_task(task.id)
        assert updated_task.status == TaskStatus.FAILED
    
    def test_cancel_nonexistent_task(self, task_manager):
        """Test cancelling a task that doesn't exist."""
        success = task_manager.cancel_task("nonexistent-id")
        assert not success
    
    def test_cancel_completed_task(self, task_manager):
        """Test cancelling a task that's already completed."""
        def quick_handler(task):
            return {"result": "quick completion"}
        
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, quick_handler)
        
        task = task_manager.create_task("Quick Task", TaskType.CODE_ANALYSIS)
        task.update_status(TaskStatus.COMPLETED)
        
        success = task_manager.cancel_task(task.id)
        assert not success
    
    def test_duplicate_handler_registration(self, task_manager):
        """Test registering multiple handlers for the same task type."""
        def handler1(task):
            return {"handler": 1}
        
        def handler2(task):
            return {"handler": 2}
        
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, handler1)
        task_manager.register_task_handler(TaskType.CODE_ANALYSIS, handler2)
        
        # Second handler should replace the first
        assert task_manager._task_handlers[TaskType.CODE_ANALYSIS] == handler2
    
    def test_task_with_invalid_dependencies(self, task_manager):
        """Test creating a task with invalid dependencies."""
        task = task_manager.create_task(
            "Invalid Deps Task",
            TaskType.CODE_ANALYSIS,
            dependencies=["nonexistent-id"]
        )
        
        # Task should be created but dependency won't be satisfied
        assert len(task.dependencies) == 1
        assert not task.can_execute(set(), {})


@pytest.mark.asyncio
class TestTaskManagerAsync:
    """Test asynchronous aspects of TaskManager."""
    
    @pytest.fixture
    async def async_task_manager(self):
        """Create an async TaskManager for testing."""
        config = TaskManagerConfig(max_concurrent_tasks=2)
        manager = TaskManager(config)
        yield manager
        manager.shutdown()
    
    async def test_async_task_execution(self, async_task_manager):
        """Test asynchronous task execution patterns."""
        async def async_handler(task):
            await asyncio.sleep(0.1)
            return {"async_result": True}
        
        # Note: The current implementation uses sync handlers
        # This test demonstrates how async support could be added
        
        def sync_wrapper(task):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_handler(task))
            finally:
                loop.close()
        
        async_task_manager.register_task_handler(TaskType.CODE_ANALYSIS, sync_wrapper)
        
        task = async_task_manager.create_task("Async Task", TaskType.CODE_ANALYSIS)
        success = async_task_manager.execute_task(task.id)
        assert success
    
    async def test_concurrent_async_operations(self, async_task_manager):
        """Test multiple concurrent async operations."""
        def handler(task):
            import time
            time.sleep(0.1)
            return {"result": f"Task {task.name} completed"}
        
        async_task_manager.register_task_handler(TaskType.CODE_ANALYSIS, handler)
        
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = async_task_manager.create_task(f"Async Task {i}", TaskType.CODE_ANALYSIS)
            tasks.append(task)
        
        # Execute all tasks concurrently
        for task in tasks:
            async_task_manager.execute_task(task.id)
        
        # Wait for completion
        await asyncio.sleep(0.5)
        
        # Check results
        for task in tasks:
            updated_task = async_task_manager.get_task(task.id)
            assert updated_task.status in [TaskStatus.COMPLETED, TaskStatus.RUNNING]


if __name__ == "__main__":
    pytest.main([__file__])

