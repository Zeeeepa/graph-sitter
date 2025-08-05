"""
Basic Usage Examples for the Advanced Task Management System

This module demonstrates how to use the task management system for common scenarios
including task creation, workflow orchestration, and integration with external systems.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict

from ..core import TaskManager, TaskManagerConfig, Task, TaskType, TaskPriority
from ..workflow import WorkflowOrchestrator, Workflow, WorkflowStep, StepType
from ..integration import CodegenIntegration, IntegrationConfig
from ..performance import PerformanceMonitor
from ..evaluation import EvaluationSystem


async def basic_task_management_example():
    """Demonstrate basic task management capabilities."""
    print("=== Basic Task Management Example ===")
    
    # Initialize task manager with configuration
    config = TaskManagerConfig(
        max_concurrent_tasks=5,
        default_timeout=timedelta(minutes=30),
        enable_performance_monitoring=True,
        enable_auto_retry=True
    )
    
    task_manager = TaskManager(config)
    
    # Register a simple task handler
    def simple_code_analysis_handler(task: Task) -> Dict[str, Any]:
        """Simple handler for code analysis tasks."""
        print(f"Analyzing code for task: {task.name}")
        
        # Simulate analysis work
        import time
        time.sleep(2)
        
        return {
            "analysis_result": "Code analysis completed",
            "files_analyzed": task.input_data.get("files", []),
            "issues_found": 3,
            "suggestions": ["Add type hints", "Improve error handling", "Add unit tests"]
        }
    
    # Register the handler
    task_manager.register_task_handler(TaskType.CODE_ANALYSIS, simple_code_analysis_handler)
    
    # Create and execute a simple task
    task = task_manager.create_task(
        name="Analyze Python Module",
        task_type=TaskType.CODE_ANALYSIS,
        description="Analyze a Python module for code quality issues",
        priority=TaskPriority.HIGH,
        input_data={
            "files": ["src/main.py", "src/utils.py"],
            "analysis_type": "quality"
        }
    )
    
    print(f"Created task: {task.id}")
    
    # Wait for task completion
    while task.status.value not in ["completed", "failed", "cancelled"]:
        await asyncio.sleep(1)
        task = task_manager.get_task(task.id)
    
    print(f"Task completed with status: {task.status.value}")
    if task.status.value == "completed":
        print(f"Result: {task.output_data}")
    
    # Get system metrics
    metrics = task_manager.get_metrics()
    if metrics:
        print(f"System metrics: {metrics.total_tasks_completed} tasks completed")
    
    # Cleanup
    task_manager.shutdown()


async def workflow_orchestration_example():
    """Demonstrate workflow orchestration capabilities."""
    print("\n=== Workflow Orchestration Example ===")
    
    # Create a workflow for a complete feature implementation
    workflow = Workflow(
        name="Feature Implementation Workflow",
        description="Complete workflow for implementing a new feature"
    )
    
    # Step 1: Code analysis
    analysis_step = WorkflowStep(
        name="Analyze Existing Code",
        step_type=StepType.TASK,
        task_type=TaskType.CODE_ANALYSIS,
        task_config={
            "analysis_type": "feature_impact",
            "target_feature": "user_authentication"
        }
    )
    workflow.add_step(analysis_step)
    workflow.entry_points.append(analysis_step.id)
    
    # Step 2: Generate implementation
    implementation_step = WorkflowStep(
        name="Generate Implementation",
        step_type=StepType.TASK,
        task_type=TaskType.CODE_GENERATION,
        task_config={
            "feature_type": "authentication",
            "framework": "FastAPI"
        },
        depends_on=[analysis_step.id]
    )
    workflow.add_step(implementation_step)
    
    # Step 3: Generate tests
    test_step = WorkflowStep(
        name="Generate Tests",
        step_type=StepType.TASK,
        task_type=TaskType.CODE_GENERATION,
        task_config={
            "test_type": "unit_tests",
            "coverage_target": 90
        },
        depends_on=[implementation_step.id]
    )
    workflow.add_step(test_step)
    
    # Step 4: Performance optimization
    optimization_step = WorkflowStep(
        name="Optimize Performance",
        step_type=StepType.TASK,
        task_type=TaskType.PERFORMANCE_OPTIMIZATION,
        task_config={
            "optimization_targets": ["response_time", "memory_usage"]
        },
        depends_on=[implementation_step.id, test_step.id]
    )
    workflow.add_step(optimization_step)
    
    # Validate workflow
    errors = workflow.validate_workflow()
    if errors:
        print(f"Workflow validation errors: {errors}")
        return
    
    print(f"Created workflow: {workflow.name}")
    print(f"Total steps: {len(workflow.steps)}")
    
    # Initialize workflow orchestrator
    orchestrator = WorkflowOrchestrator()
    
    # Execute workflow (simplified - would normally integrate with task manager)
    workflow.update_status(workflow.WorkflowStatus.RUNNING)
    
    print("Workflow execution started")
    print(f"Ready steps: {[step.name for step in workflow.get_ready_steps()]}")
    
    # Get execution summary
    summary = workflow.get_execution_summary()
    print(f"Execution summary: {summary}")


async def integration_example():
    """Demonstrate integration with external systems."""
    print("\n=== Integration Example ===")
    
    # Configure Codegen integration
    codegen_config = IntegrationConfig(
        name="codegen",
        enabled=True,
        connection_timeout=30,
        retry_attempts=3
    )
    
    # Note: This would require actual Codegen credentials
    # codegen_integration = CodegenIntegration(
    #     config=codegen_config,
    #     org_id="your_org_id",
    #     token="your_api_token"
    # )
    
    print("Integration configuration created")
    print("In a real implementation, this would:")
    print("1. Connect to Codegen SDK")
    print("2. Register task handlers for code operations")
    print("3. Execute tasks using AI agents")
    print("4. Monitor integration health and performance")


async def performance_monitoring_example():
    """Demonstrate performance monitoring capabilities."""
    print("\n=== Performance Monitoring Example ===")
    
    # Initialize performance monitor
    monitor = PerformanceMonitor()
    
    # Create a sample task for monitoring
    task = Task(
        name="Sample Monitoring Task",
        task_type=TaskType.CODE_ANALYSIS,
        priority=TaskPriority.MEDIUM
    )
    
    # Simulate task lifecycle with monitoring
    monitor.task_created(task)
    print("Task created and monitoring started")
    
    # Simulate task execution
    task.update_status(task.TaskStatus.RUNNING)
    monitor.task_started(task)
    print("Task execution started")
    
    # Simulate some work
    await asyncio.sleep(1)
    
    # Complete task
    task.update_status(task.TaskStatus.COMPLETED)
    monitor.task_completed(task)
    print("Task completed")
    
    # Get metrics
    metrics = monitor.get_metrics()
    if metrics:
        print(f"Monitoring metrics:")
        print(f"  Total tasks: {metrics.total_tasks_created}")
        print(f"  Completed tasks: {metrics.total_tasks_completed}")
        print(f"  Average execution time: {metrics.average_execution_time:.2f}s")
    
    # Cleanup
    monitor.shutdown()


async def evaluation_example():
    """Demonstrate evaluation and analytics capabilities."""
    print("\n=== Evaluation Example ===")
    
    # Initialize evaluation system
    evaluation_system = EvaluationSystem()
    
    # Create sample tasks for evaluation
    tasks = [
        Task(
            name=f"Sample Task {i}",
            task_type=TaskType.CODE_GENERATION,
            priority=TaskPriority.MEDIUM
        )
        for i in range(3)
    ]
    
    # Simulate task completion with different outcomes
    for i, task in enumerate(tasks):
        task.update_status(task.TaskStatus.COMPLETED)
        task.output_data = {
            "lines_of_code": 100 + i * 50,
            "test_coverage": 80 + i * 5,
            "performance_score": 85 + i * 3
        }
    
    print(f"Created {len(tasks)} sample tasks for evaluation")
    print("In a real implementation, this would:")
    print("1. Evaluate task effectiveness and quality")
    print("2. Generate analytics reports")
    print("3. Provide optimization recommendations")
    print("4. Track trends and performance over time")


async def comprehensive_example():
    """Comprehensive example combining all features."""
    print("\n=== Comprehensive Example ===")
    
    print("This example would demonstrate:")
    print("1. Complete task management lifecycle")
    print("2. Complex workflow orchestration")
    print("3. Integration with multiple external systems")
    print("4. Real-time performance monitoring")
    print("5. Comprehensive evaluation and analytics")
    print("6. Database persistence and querying")
    print("7. API access and web interface")
    print("8. CLI management tools")
    
    print("\nThe system provides:")
    print("✓ Advanced task scheduling and execution")
    print("✓ Sophisticated workflow orchestration")
    print("✓ Seamless external system integration")
    print("✓ Comprehensive performance monitoring")
    print("✓ Intelligent evaluation and optimization")
    print("✓ Production-ready scalability")


async def main():
    """Run all examples."""
    print("Advanced Task Management System - Examples")
    print("=" * 50)
    
    try:
        await basic_task_management_example()
        await workflow_orchestration_example()
        await integration_example()
        await performance_monitoring_example()
        await evaluation_example()
        await comprehensive_example()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

