"""
Comprehensive tests for the Task Management Engine
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.graph_sitter.task_management import (
    Task, TaskStatus, TaskPriority, TaskType,
    TaskExecution, ExecutionStatus,
    Workflow, WorkflowStep, StepType,
    DependencyResolver, TaskScheduler, TaskExecutor, WorkflowOrchestrator,
    TaskAPI, TaskFactory, WorkflowBuilder,
    TaskLogger, TaskMetrics,
    CircularDependencyError
)


class TestTaskModel:
    """Test Task model functionality"""
    
    def test_task_creation(self):
        """Test basic task creation"""
        task = Task(
            name="Test Task",
            description="A test task",
            task_type=TaskType.CODE_ANALYSIS,
            priority=TaskPriority.HIGH,
            created_by="test_user"
        )
        
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert task.retry_count == 0
        assert len(task.depends_on) == 0
    
    def test_task_status_updates(self):
        """Test task status updates"""
        task = Task(name="Test", created_by="test")
        
        # Test status progression
        task.update_status(TaskStatus.RUNNING)
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None
        
        task.update_status(TaskStatus.COMPLETED)
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
    
    def test_task_dependencies(self):
        """Test task dependency management"""
        task1 = Task(name="Task 1", created_by="test")
        task2 = Task(name="Task 2", created_by="test")
        
        # Add dependency
        task2.add_dependency(task1.id)
        assert task1.id in task2.depends_on
        
        # Remove dependency
        task2.remove_dependency(task1.id)
        assert task1.id not in task2.depends_on
    
    def test_task_ready_to_run(self):
        """Test task readiness check"""
        task1 = Task(name="Task 1", created_by="test")
        task2 = Task(name="Task 2", created_by="test", depends_on={task1.id})
        
        # Task 2 not ready (dependency not completed)
        assert not task2.is_ready_to_run(set())
        
        # Task 2 ready (dependency completed)
        assert task2.is_ready_to_run({task1.id})
    
    def test_task_retry_logic(self):
        """Test task retry functionality"""
        task = Task(name="Test", created_by="test", max_retries=3)
        
        # Initially can retry
        task.update_status(TaskStatus.FAILED)
        assert task.can_retry()
        
        # After max retries, cannot retry
        task.retry_count = 3
        assert not task.can_retry()


class TestTaskExecution:
    """Test TaskExecution model functionality"""
    
    def test_execution_lifecycle(self):
        """Test execution lifecycle"""
        execution = TaskExecution(
            task_id=uuid4(),
            execution_number=1,
            executor_id="test_agent",
            executor_type="test"
        )
        
        # Start execution
        execution.start_execution()
        assert execution.status == ExecutionStatus.STARTING
        assert execution.started_at is not None
        
        # Mark running
        execution.mark_running()
        assert execution.status == ExecutionStatus.RUNNING
        
        # Complete execution
        result = {"output": "success"}
        execution.complete_execution(result)
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.result == result
        assert execution.completed_at is not None
    
    def test_execution_failure(self):
        """Test execution failure handling"""
        execution = TaskExecution(
            task_id=uuid4(),
            execution_number=1,
            executor_id="test_agent",
            executor_type="test"
        )
        
        execution.start_execution()
        
        # Fail execution
        error_details = {"error": "Test error"}
        execution.fail_execution(error_details)
        
        assert execution.status == ExecutionStatus.FAILED
        assert execution.error_details == error_details
        assert execution.completed_at is not None


class TestDependencyResolver:
    """Test dependency resolution functionality"""
    
    def test_dependency_validation(self):
        """Test dependency validation"""
        resolver = DependencyResolver()
        
        task1 = Task(name="Task 1", created_by="test")
        task2 = Task(name="Task 2", created_by="test", depends_on={task1.id})
        
        resolver.add_task(task1)
        resolver.add_task(task2)
        
        # Valid dependencies
        errors = resolver.validate_dependencies(task2)
        assert len(errors) == 0
        
        # Invalid dependency (non-existent task)
        task3 = Task(name="Task 3", created_by="test", depends_on={uuid4()})
        errors = resolver.validate_dependencies(task3)
        assert len(errors) > 0
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        resolver = DependencyResolver()
        
        task1 = Task(name="Task 1", created_by="test")
        task2 = Task(name="Task 2", created_by="test", depends_on={task1.id})
        task3 = Task(name="Task 3", created_by="test", depends_on={task2.id})
        
        # Create circular dependency
        task1.depends_on.add(task3.id)
        
        resolver.add_task(task1)
        resolver.add_task(task2)
        resolver.add_task(task3)
        
        # Should detect circular dependency
        errors = resolver.validate_dependencies(task1)
        assert any("circular" in error.lower() for error in errors)
    
    def test_execution_order(self):
        """Test topological execution order"""
        resolver = DependencyResolver()
        
        task1 = Task(name="Task 1", created_by="test")
        task2 = Task(name="Task 2", created_by="test", depends_on={task1.id})
        task3 = Task(name="Task 3", created_by="test", depends_on={task2.id})
        
        resolver.add_task(task1)
        resolver.add_task(task2)
        resolver.add_task(task3)
        
        # Get execution order
        order = resolver.get_execution_order()
        
        # Task 1 should come before Task 2, Task 2 before Task 3
        assert order.index(task1.id) < order.index(task2.id)
        assert order.index(task2.id) < order.index(task3.id)


class TestTaskScheduler:
    """Test task scheduling functionality"""
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization"""
        resolver = DependencyResolver()
        scheduler = TaskScheduler(resolver)
        
        assert scheduler.dependency_resolver == resolver
        assert len(scheduler.task_queue) == 0
    
    def test_task_scheduling(self):
        """Test task scheduling"""
        resolver = DependencyResolver()
        scheduler = TaskScheduler(resolver)
        
        # Add tasks with different priorities
        high_task = Task(name="High", created_by="test", priority=TaskPriority.HIGH)
        normal_task = Task(name="Normal", created_by="test", priority=TaskPriority.NORMAL)
        
        scheduler.add_task(high_task)
        scheduler.add_task(normal_task)
        
        # High priority task should be scheduled first
        next_task = scheduler.get_next_task()
        assert next_task.priority == TaskPriority.HIGH
    
    def test_agent_registration(self):
        """Test agent registration"""
        resolver = DependencyResolver()
        scheduler = TaskScheduler(resolver)
        
        # Register agent
        capabilities = {"code_analysis", "testing"}
        scheduler.register_agent("test_agent", capabilities)
        
        assert "test_agent" in scheduler.agent_capabilities
        assert scheduler.agent_capabilities["test_agent"] == capabilities


class TestTaskExecutor:
    """Test task execution functionality"""
    
    def test_executor_initialization(self):
        """Test executor initialization"""
        executor = TaskExecutor(max_concurrent_tasks=5)
        
        assert executor.max_concurrent_tasks == 5
        assert len(executor.running_executions) == 0
    
    def test_agent_registration(self):
        """Test agent registration with executor"""
        executor = TaskExecutor()
        
        def dummy_executor(task, context):
            return {"result": "success"}
        
        # Register agent
        executor.register_agent(
            "test_agent",
            "test_type",
            dummy_executor,
            {"code_analysis"}
        )
        
        assert "test_agent" in executor.agents
        assert executor.agents["test_agent"]["type"] == "test_type"


class TestWorkflowOrchestrator:
    """Test workflow orchestration functionality"""
    
    def test_workflow_creation(self):
        """Test workflow creation"""
        workflow = Workflow(
            name="Test Workflow",
            created_by="test_user",
            steps=[]
        )
        
        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.PENDING
        assert len(workflow.steps) == 0
    
    def test_workflow_step_creation(self):
        """Test workflow step creation"""
        step = WorkflowStep(
            id="test_step",
            name="Test Step",
            step_type=StepType.TASK,
            task_template={"name": "Test Task"}
        )
        
        assert step.id == "test_step"
        assert step.step_type == StepType.TASK
        assert step.status == TaskStatus.PENDING


class TestTaskFactory:
    """Test task factory functionality"""
    
    def test_code_analysis_task_creation(self):
        """Test code analysis task creation"""
        task = TaskFactory.create_code_analysis_task(
            name="Analyze Repo",
            repository_url="https://github.com/test/repo",
            analysis_type="complexity",
            created_by="test_user"
        )
        
        assert task.name == "Analyze Repo"
        assert task.task_type == TaskType.CODE_ANALYSIS
        assert task.metadata["repository_url"] == "https://github.com/test/repo"
        assert task.metadata["analysis_type"] == "complexity"
    
    def test_batch_task_creation(self):
        """Test batch task creation"""
        task_configs = [
            {"name": "Task 1", "task_type": "code_analysis"},
            {"name": "Task 2", "task_type": "testing"},
            {"name": "Task 3", "task_type": "deployment"}
        ]
        
        tasks = TaskFactory.create_batch_tasks(task_configs, "test_user")
        
        assert len(tasks) == 3
        assert all("batch" in task.tags for task in tasks)
        assert all(task.metadata["batch_size"] == 3 for task in tasks)
    
    def test_pipeline_task_creation(self):
        """Test pipeline task creation"""
        pipeline_config = {
            "stages": [
                {
                    "name": "Build",
                    "tasks": [{"name": "Compile", "task_type": "code_generation"}]
                },
                {
                    "name": "Test", 
                    "tasks": [{"name": "Unit Tests", "task_type": "testing"}]
                }
            ]
        }
        
        tasks = TaskFactory.create_pipeline_tasks(pipeline_config, "test_user")
        
        assert len(tasks) == 2
        # Second task should depend on first
        assert tasks[0].id in tasks[1].depends_on


class TestWorkflowBuilder:
    """Test workflow builder functionality"""
    
    def test_workflow_builder_basic(self):
        """Test basic workflow building"""
        builder = WorkflowBuilder("Test Workflow", "test_user")
        
        workflow = (builder
                   .description("A test workflow")
                   .max_parallel_tasks(5)
                   .add_task_step("step1", {"name": "Task 1"})
                   .add_task_step("step2", {"name": "Task 2"}, depends_on={"step1"})
                   .build())
        
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.max_parallel_tasks == 5
        assert len(workflow.steps) == 2
        assert "step1" in workflow.steps[1].depends_on
    
    def test_ci_cd_workflow_creation(self):
        """Test CI/CD workflow creation"""
        workflow = WorkflowBuilder.create_ci_cd_workflow(
            "CI/CD Pipeline",
            "test_user",
            "https://github.com/test/repo"
        )
        
        assert workflow.name == "CI/CD Pipeline"
        assert len(workflow.steps) > 0
        # Should have build, test, and deploy steps
        step_names = [step.name for step in workflow.steps]
        assert any("build" in name.lower() for name in step_names)


class TestTaskMetrics:
    """Test task metrics functionality"""
    
    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = TaskMetrics()
        
        assert metrics.concurrent_tasks == 0
        assert metrics.total_tasks_processed == 0
        assert len(metrics.task_durations) == 0
    
    def test_task_metrics_recording(self):
        """Test task metrics recording"""
        metrics = TaskMetrics()
        task_id = uuid4()
        
        # Record task start
        metrics.record_task_started(task_id, "test_agent")
        assert metrics.concurrent_tasks == 1
        
        # Record task completion
        metrics.record_task_completed(task_id, 5.0)
        assert metrics.concurrent_tasks == 0
        assert metrics.total_tasks_processed == 1
        assert len(metrics.task_durations) == 1
    
    def test_agent_metrics(self):
        """Test agent metrics"""
        metrics = TaskMetrics()
        
        # Record agent success
        metrics.record_agent_success("test_agent", 3.0)
        assert metrics.agent_success_counts["test_agent"] == 1
        assert metrics.agent_avg_durations["test_agent"] == 3.0
        
        # Record another success
        metrics.record_agent_success("test_agent", 5.0)
        assert metrics.agent_success_counts["test_agent"] == 2
        assert metrics.agent_avg_durations["test_agent"] == 4.0  # Average of 3.0 and 5.0


class TestTaskLogger:
    """Test task logging functionality"""
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        logger = TaskLogger()
        
        assert logger.logger is not None
        assert logger.logger.name == "task_management"
    
    def test_structured_logging(self):
        """Test structured logging"""
        logger = TaskLogger()
        task_id = uuid4()
        
        # Test different log types
        logger.log_task_created(task_id, "Test Task", "test_user")
        logger.log_task_started(task_id, "test_agent", uuid4())
        logger.log_task_completed(task_id, uuid4(), 5.0)
        
        # Should not raise exceptions


@pytest.mark.asyncio
class TestTaskAPI:
    """Test Task API functionality"""
    
    async def test_api_initialization(self):
        """Test API initialization"""
        api = TaskAPI()
        
        assert api.dependency_resolver is not None
        assert api.task_scheduler is not None
        assert api.task_executor is not None
        assert api.workflow_orchestrator is not None
    
    async def test_task_crud_operations(self):
        """Test task CRUD operations"""
        api = TaskAPI()
        
        # Create task
        task = Task(name="Test Task", created_by="test_user")
        task_response = await api.create_task(task)
        
        assert task_response.name == "Test Task"
        assert task_response.status == TaskStatus.PENDING
        
        # Get task
        retrieved_task = await api.get_task(task_response.id)
        assert retrieved_task is not None
        assert retrieved_task.id == task_response.id
        
        # Update task
        from src.graph_sitter.task_management.api.task_api import UpdateTaskRequest
        update_request = UpdateTaskRequest(name="Updated Task")
        updated_task = await api.update_task(task_response.id, update_request)
        assert updated_task.name == "Updated Task"
        
        # Delete task
        success = await api.delete_task(task_response.id)
        assert success
        
        # Cleanup
        await api.shutdown()
    
    async def test_task_listing(self):
        """Test task listing with filters"""
        api = TaskAPI()
        
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = Task(
                name=f"Task {i}",
                created_by="test_user",
                priority=TaskPriority.HIGH if i % 2 == 0 else TaskPriority.NORMAL
            )
            task_response = await api.create_task(task)
            tasks.append(task_response)
        
        # List all tasks
        all_tasks = await api.list_tasks(limit=10)
        assert len(all_tasks) == 5
        
        # List high priority tasks
        high_priority_tasks = await api.list_tasks(priority=TaskPriority.HIGH)
        assert len(high_priority_tasks) == 3  # Tasks 0, 2, 4
        
        # Cleanup
        await api.shutdown()
    
    async def test_health_check(self):
        """Test health check endpoint"""
        api = TaskAPI()
        
        health = await api.health_check()
        
        assert health["status"] == "healthy"
        assert "components" in health
        assert "metrics" in health
        
        # Cleanup
        await api.shutdown()


class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_task_execution(self):
        """Test complete task execution flow"""
        api = TaskAPI()
        
        # Create a simple task
        task = TaskFactory.create_code_analysis_task(
            name="Integration Test Task",
            repository_url="https://github.com/test/repo",
            analysis_type="complexity",
            created_by="test_user"
        )
        
        # Add to system
        task_response = await api.create_task(task)
        assert task_response.status == TaskStatus.PENDING
        
        # Get system metrics
        metrics = await api.get_system_metrics()
        assert "total_tasks_processed" in metrics
        
        # Get queue statistics
        stats = await api.get_queue_statistics()
        assert stats["pending_tasks"] >= 1
        
        # Cleanup
        await api.shutdown()
    
    @pytest.mark.asyncio
    async def test_workflow_execution_flow(self):
        """Test complete workflow execution flow"""
        api = TaskAPI()
        
        # Create a simple workflow
        workflow = WorkflowBuilder("Integration Test Workflow", "test_user").build()
        
        # The workflow would be executed here in a real scenario
        # For testing, we just verify the workflow structure
        assert workflow.name == "Integration Test Workflow"
        assert workflow.created_by == "test_user"
        
        # Cleanup
        await api.shutdown()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

