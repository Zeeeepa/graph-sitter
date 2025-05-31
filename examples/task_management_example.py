"""
Example usage of the Task Management Engine

This example demonstrates how to use the core task management engine
for various scenarios including task creation, workflow orchestration,
and monitoring.
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from src.graph_sitter.task_management import (
    Task, TaskPriority, TaskType, TaskStatus,
    TaskAPI, TaskFactory, WorkflowBuilder,
    WorkflowCondition, ConditionOperator
)


async def basic_task_example():
    """Basic task creation and execution example"""
    print("=== Basic Task Example ===")
    
    # Initialize the task management API
    api = TaskAPI()
    
    # Create a simple task
    task = TaskFactory.create_code_analysis_task(
        name="Analyze FastAPI Repository",
        repository_url="https://github.com/tiangolo/fastapi",
        analysis_type="complexity",
        created_by="example_user",
        priority=TaskPriority.HIGH
    )
    
    # Add task to the system
    task_response = await api.create_task(task)
    print(f"Created task: {task_response.id} - {task_response.name}")
    
    # Get task status
    status = await api.get_task(task_response.id)
    print(f"Task status: {status.status}")
    
    # List all tasks
    tasks = await api.list_tasks(limit=10)
    print(f"Total tasks in system: {len(tasks)}")
    
    return api


async def dependency_example():
    """Example with task dependencies"""
    print("\n=== Task Dependencies Example ===")
    
    api = TaskAPI()
    
    # Create a pipeline of dependent tasks
    pipeline_config = {
        "stages": [
            {
                "name": "Setup",
                "tasks": [
                    {
                        "name": "Clone Repository",
                        "task_type": "custom",
                        "metadata": {"action": "clone", "repo": "example/repo"}
                    }
                ]
            },
            {
                "name": "Analysis",
                "tasks": [
                    {
                        "name": "Code Analysis",
                        "task_type": "code_analysis",
                        "metadata": {"analysis_type": "complexity"}
                    },
                    {
                        "name": "Security Scan",
                        "task_type": "code_analysis", 
                        "metadata": {"analysis_type": "security"}
                    }
                ]
            },
            {
                "name": "Report",
                "tasks": [
                    {
                        "name": "Generate Report",
                        "task_type": "custom",
                        "metadata": {"action": "report"}
                    }
                ]
            }
        ]
    }
    
    # Create pipeline tasks
    pipeline_tasks = TaskFactory.create_pipeline_tasks(pipeline_config, "example_user")
    
    # Add all tasks to the system
    for task in pipeline_tasks:
        await api.create_task(task)
        print(f"Created pipeline task: {task.name}")
    
    # Get execution plan
    task_ids = {task.id for task in pipeline_tasks}
    execution_plan = await api.get_execution_plan(task_ids)
    print(f"Execution plan phases: {len(execution_plan['phases'])}")
    
    return api


async def workflow_example():
    """Example with complex workflow orchestration"""
    print("\n=== Workflow Orchestration Example ===")
    
    api = TaskAPI()
    
    # Create a CI/CD workflow
    workflow = WorkflowBuilder.create_ci_cd_workflow(
        name="FastAPI CI/CD Pipeline",
        created_by="example_user",
        repository_url="https://github.com/tiangolo/fastapi"
    )
    
    print(f"Created workflow: {workflow.name} with {len(workflow.steps)} steps")
    
    # Execute workflow
    result = await api.execute_workflow(workflow)
    print(f"Workflow status: {result.status}")
    
    # Monitor workflow progress
    status = await api.get_workflow_status(workflow.id)
    if status:
        print(f"Workflow progress: {status['progress_percentage']:.1f}%")
    
    return api


async def monitoring_example():
    """Example of monitoring and metrics"""
    print("\n=== Monitoring and Metrics Example ===")
    
    api = TaskAPI()
    
    # Create some sample tasks for monitoring
    tasks = [
        TaskFactory.create_code_analysis_task(
            name=f"Analysis Task {i}",
            repository_url=f"https://github.com/example/repo{i}",
            analysis_type="complexity",
            created_by="example_user",
            priority=TaskPriority.NORMAL
        )
        for i in range(5)
    ]
    
    # Add tasks to system
    for task in tasks:
        await api.create_task(task)
    
    # Get system metrics
    metrics = await api.get_system_metrics()
    print(f"System metrics:")
    print(f"  - Total tasks processed: {metrics['total_tasks_processed']}")
    print(f"  - Concurrent tasks: {metrics['concurrent_tasks']}")
    print(f"  - Tasks per minute: {metrics['tasks_per_minute']}")
    print(f"  - Average duration: {metrics['average_duration_seconds']:.2f}s")
    
    # Get queue statistics
    queue_stats = await api.get_queue_statistics()
    print(f"Queue statistics:")
    print(f"  - Pending tasks: {queue_stats['pending_tasks']}")
    print(f"  - Running tasks: {queue_stats['running_tasks']}")
    print(f"  - Completed tasks: {queue_stats['completed_tasks']}")
    
    # Get performance report
    report = await api.get_performance_report()
    print(f"Performance report generated at: {report['report_timestamp']}")
    
    return api


async def agent_management_example():
    """Example of agent registration and management"""
    print("\n=== Agent Management Example ===")
    
    api = TaskAPI()
    
    # Register different types of agents
    agents = [
        {
            "agent_id": "codegen_agent_1",
            "agent_type": "codegen",
            "capabilities": {"code_analysis", "code_generation", "code_review"}
        },
        {
            "agent_id": "claude_agent_1", 
            "agent_type": "claude",
            "capabilities": {"code_review", "testing", "custom"}
        },
        {
            "agent_id": "task_manager_1",
            "agent_type": "task_manager",
            "capabilities": {"monitoring", "deployment", "custom"}
        }
    ]
    
    # Register agents
    for agent in agents:
        await api.register_agent(
            agent["agent_id"],
            agent["agent_type"],
            agent["capabilities"]
        )
        print(f"Registered agent: {agent['agent_id']} ({agent['agent_type']})")
    
    # Get agent statistics
    agent_stats = await api.get_agent_statistics()
    print(f"Agent statistics:")
    for agent_id, stats in agent_stats.items():
        print(f"  - {agent_id}: {stats['success_rate_percent']:.1f}% success rate")
    
    return api


async def error_handling_example():
    """Example of error handling and recovery"""
    print("\n=== Error Handling and Recovery Example ===")
    
    api = TaskAPI()
    
    # Create a task that might fail
    task = Task(
        name="Potentially Failing Task",
        description="A task that demonstrates error handling",
        task_type=TaskType.CUSTOM,
        priority=TaskPriority.NORMAL,
        created_by="example_user",
        max_retries=3,
        timeout_seconds=30,
        metadata={"simulate_failure": True}
    )
    
    # Add task to system
    task_response = await api.create_task(task)
    print(f"Created task with retry capability: {task_response.name}")
    print(f"Max retries: {task_response.max_retries}")
    
    # Simulate task failure and retry
    print("Task would be executed and potentially retried on failure...")
    
    return api


async def performance_optimization_example():
    """Example of performance optimization features"""
    print("\n=== Performance Optimization Example ===")
    
    api = TaskAPI()
    
    # Create batch of tasks with different priorities
    high_priority_tasks = TaskFactory.create_batch_tasks([
        {
            "name": f"Critical Task {i}",
            "task_type": "code_analysis",
            "priority": TaskPriority.CRITICAL,
            "metadata": {"urgency": "high"}
        }
        for i in range(3)
    ], "example_user", "critical_batch")
    
    normal_priority_tasks = TaskFactory.create_batch_tasks([
        {
            "name": f"Normal Task {i}",
            "task_type": "code_generation", 
            "priority": TaskPriority.NORMAL,
            "metadata": {"urgency": "normal"}
        }
        for i in range(10)
    ], "example_user", "normal_batch")
    
    # Add all tasks
    all_tasks = high_priority_tasks + normal_priority_tasks
    for task in all_tasks:
        await api.create_task(task)
    
    print(f"Created {len(all_tasks)} tasks with different priorities")
    
    # Get dependency graph
    dep_graph = await api.get_dependency_graph()
    print(f"Dependency graph has {len(dep_graph['nodes'])} nodes and {len(dep_graph['edges'])} edges")
    
    return api


async def main():
    """Run all examples"""
    print("Task Management Engine Examples")
    print("=" * 50)
    
    try:
        # Run examples
        api1 = await basic_task_example()
        api2 = await dependency_example()
        api3 = await workflow_example()
        api4 = await monitoring_example()
        api5 = await agent_management_example()
        api6 = await error_handling_example()
        api7 = await performance_optimization_example()
        
        # Health check
        print("\n=== System Health Check ===")
        health = await api1.health_check()
        print(f"System status: {health['status']}")
        print(f"All components: {list(health['components'].keys())}")
        
        # Cleanup
        await api1.shutdown()
        print("\nTask Management Engine examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

