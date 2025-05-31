"""
Examples demonstrating the Enhanced Orchestrator capabilities
"""

import asyncio
import json
from datetime import datetime
from contexten import EnhancedOrchestrator, MemoryManager, EventEvaluator, AutonomousCICD
from contexten.config import ContextenConfig


async def basic_orchestrator_example():
    """Basic example of using the Enhanced Orchestrator"""
    print("=== Basic Orchestrator Example ===")
    
    # Create orchestrator with default configuration
    orchestrator = EnhancedOrchestrator()
    
    try:
        # Start the orchestrator
        await orchestrator.start()
        print("✅ Orchestrator started successfully")
        
        # Create an agent using SDK-Python integration
        agent_config = {
            "name": "example_agent",
            "model_provider": "bedrock",
            "model_id": "us.amazon.nova-pro-v1:0",
            "temperature": 0.3,
            "memory_enabled": True
        }
        
        agent_id = await orchestrator.create_agent(
            agent_config=agent_config,
            tools=["calculator", "memory_operations", "file_operations"],
            memory_context="example_session"
        )
        print(f"✅ Created agent: {agent_id}")
        
        # Execute a task
        task_config = {
            "description": "Calculate the square root of 1764 and store the result",
            "expression": "sqrt(1764)",
            "store_result": True
        }
        
        result = await orchestrator.execute_task(
            task_id="example_task_1",
            task_config=task_config,
            agent_id=agent_id,
            use_memory=True
        )
        print(f"✅ Task completed: {result['status']}")
        print(f"   Result: {json.dumps(result['result'], indent=2)}")
        
        # Get orchestrator health status
        health = orchestrator.get_health_status()
        print(f"✅ System health: {health['orchestrator']}")
        
    finally:
        # Stop the orchestrator
        await orchestrator.stop()
        print("✅ Orchestrator stopped")


async def memory_management_example():
    """Example of advanced memory management"""
    print("\n=== Memory Management Example ===")
    
    # Create memory manager
    memory_manager = MemoryManager(
        backend="persistent",
        retention_days=30,
        optimization_enabled=True
    )
    
    try:
        await memory_manager.start()
        print("✅ Memory manager started")
        
        # Store some context data
        contexts = [
            {
                "context_id": "user_preferences",
                "data": {
                    "theme": "dark",
                    "language": "python",
                    "notifications": True
                },
                "metadata": {"type": "user_settings", "user_id": "user_123"}
            },
            {
                "context_id": "project_config",
                "data": {
                    "name": "Enhanced Orchestrator",
                    "version": "1.0.0",
                    "dependencies": ["asyncio", "pydantic", "sqlalchemy"]
                },
                "metadata": {"type": "project_data", "project_id": "proj_456"}
            },
            {
                "context_id": "task_history",
                "data": {
                    "completed_tasks": 15,
                    "failed_tasks": 2,
                    "average_duration": 45.6
                },
                "metadata": {"type": "analytics", "period": "last_week"}
            }
        ]
        
        # Store contexts
        for context in contexts:
            success = await memory_manager.store_context(**context)
            print(f"✅ Stored context: {context['context_id']} - {success}")
        
        # Retrieve specific context
        user_prefs = await memory_manager.retrieve_context(context_id="user_preferences")
        print(f"✅ Retrieved user preferences: {user_prefs.get('data', {}).get('theme', 'not found')}")
        
        # Semantic search
        search_results = await memory_manager.retrieve_context(
            query="project configuration",
            relevance_threshold=0.5,
            limit=5
        )
        print(f"✅ Search results: {len(search_results.get('results', []))} matches")
        
        # Get memory statistics
        stats = await memory_manager.get_stats()
        print(f"✅ Memory stats: {stats['cache_size']} entries in cache")
        
        # Optimize memory
        optimization_result = await memory_manager.optimize()
        print(f"✅ Memory optimization: {optimization_result}")
        
    finally:
        await memory_manager.stop()
        print("✅ Memory manager stopped")


async def event_evaluation_example():
    """Example of system-level event evaluation"""
    print("\n=== Event Evaluation Example ===")
    
    # Create event evaluator
    event_evaluator = EventEvaluator(
        monitoring_enabled=True,
        classification_threshold=0.8,
        real_time_processing=True
    )
    
    try:
        await event_evaluator.start()
        print("✅ Event evaluator started")
        
        # Generate some test events
        test_events = [
            {
                "type": "task_execution",
                "status": "completed",
                "task_id": "task_001",
                "duration": 2.5,
                "source": "orchestrator"
            },
            {
                "type": "task_execution",
                "status": "failed",
                "task_id": "task_002",
                "error_message": "ImportError: No module named 'missing_lib'",
                "source": "orchestrator"
            },
            {
                "type": "memory_optimization",
                "entries_removed": 150,
                "entries_updated": 25,
                "source": "memory_manager"
            },
            {
                "type": "performance_metric",
                "response_time": 6500,  # > 5 seconds
                "endpoint": "/api/execute",
                "source": "api_server"
            },
            {
                "type": "security_event",
                "severity": "high",
                "alert_type": "unauthorized_access",
                "description": "Multiple failed login attempts",
                "source": "auth_service"
            }
        ]
        
        # Evaluate events
        event_ids = []
        for event_data in test_events:
            event_id = await event_evaluator.evaluate_event(event_data)
            event_ids.append(event_id)
            print(f"✅ Evaluated event: {event_id} ({event_data['type']})")
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Get event statistics
        stats = await event_evaluator.get_stats()
        print(f"✅ Event stats: {stats['total_events']} total, {stats['auto_responses_generated']} auto-responses")
        
        # Get recent events
        recent_events = await event_evaluator.get_events(limit=10)
        print(f"✅ Recent events: {len(recent_events)} events retrieved")
        
        # Get high-priority events
        high_priority_events = await event_evaluator.get_events(
            priority=event_evaluator.EventPriority.HIGH,
            limit=5
        )
        print(f"✅ High-priority events: {len(high_priority_events)} events")
        
    finally:
        await event_evaluator.stop()
        print("✅ Event evaluator stopped")


async def cicd_pipeline_example():
    """Example of autonomous CI/CD capabilities"""
    print("\n=== CI/CD Pipeline Example ===")
    
    # Create CI/CD system
    cicd_system = AutonomousCICD(
        enabled=True,
        auto_healing=True,
        continuous_optimization=True
    )
    
    try:
        await cicd_system.start()
        print("✅ CI/CD system started")
        
        # List available pipelines
        pipelines = await cicd_system.list_pipelines()
        print(f"✅ Available pipelines: {pipelines}")
        
        # Execute build pipeline
        execution_id = await cicd_system.execute_pipeline(
            pipeline_name="build",
            parameters={
                "branch": "main",
                "environment": "development"
            }
        )
        print(f"✅ Started pipeline execution: {execution_id}")
        
        # Monitor execution
        for i in range(10):  # Check for up to 10 seconds
            status = await cicd_system.get_execution_status(execution_id)
            if status:
                print(f"   Pipeline status: {status['status']}")
                if status['status'] in ['success', 'failed', 'cancelled']:
                    break
            await asyncio.sleep(1)
        
        # Get execution logs
        logs = await cicd_system.get_execution_logs(execution_id)
        print(f"✅ Execution logs: {len(logs)} log entries")
        if logs:
            print(f"   Latest log: {logs[-1]}")
        
        # Get CI/CD system status
        system_status = await cicd_system.get_status()
        print(f"✅ CI/CD status: {system_status['enabled']}, active executions: {system_status['active_executions']}")
        
        # List recent executions
        recent_executions = await cicd_system.list_executions(limit=5)
        print(f"✅ Recent executions: {len(recent_executions)} executions")
        
    finally:
        await cicd_system.stop()
        print("✅ CI/CD system stopped")


async def integration_showcase_example():
    """Showcase integration between SDK-Python and Strands-Agents"""
    print("\n=== Integration Showcase Example ===")
    
    # Create orchestrator with both integrations enabled
    config = ContextenConfig()
    config.sdk_python.enabled = True
    config.strands_agents.enabled = True
    
    orchestrator = EnhancedOrchestrator(config)
    
    try:
        await orchestrator.start()
        print("✅ Orchestrator with integrations started")
        
        # Create an agent with multiple tools
        agent_config = {
            "name": "integration_demo_agent",
            "model_provider": "bedrock",
            "temperature": 0.2,
            "memory_enabled": True,
            "custom_instructions": "You are a helpful assistant that can perform calculations, file operations, and code execution."
        }
        
        tools = [
            "calculator",
            "file_operations", 
            "python_execution",
            "memory_operations",
            "http_client"
        ]
        
        agent_id = await orchestrator.create_agent(
            agent_config=agent_config,
            tools=tools,
            memory_context="integration_demo"
        )
        print(f"✅ Created multi-tool agent: {agent_id}")
        
        # Execute a complex task that uses multiple tools
        complex_task = {
            "description": "Calculate fibonacci sequence up to 10, save to file, and store in memory",
            "type": "multi_step",
            "steps": [
                {
                    "action": "calculate",
                    "expression": "fibonacci(10)"
                },
                {
                    "action": "save_file",
                    "filename": "fibonacci_results.txt"
                },
                {
                    "action": "store_memory",
                    "key": "fibonacci_calculation"
                }
            ]
        }
        
        result = await orchestrator.execute_task(
            task_id="complex_integration_task",
            task_config=complex_task,
            agent_id=agent_id,
            use_memory=True
        )
        
        print(f"✅ Complex task completed: {result['status']}")
        print(f"   Tools used: {result.get('tools_used', [])}")
        
        # Get system optimization results
        optimization = await orchestrator.optimize_system()
        print(f"✅ System optimization completed: {list(optimization.keys())}")
        
        # Get comprehensive health status
        health = orchestrator.get_health_status()
        print("✅ System health status:")
        for component, status in health.items():
            if component != "timestamp":
                print(f"   {component}: {status}")
        
    finally:
        await orchestrator.stop()
        print("✅ Integration showcase completed")


async def run_all_examples():
    """Run all examples in sequence"""
    print("🚀 Starting Enhanced Orchestrator Examples")
    print("=" * 50)
    
    try:
        await basic_orchestrator_example()
        await memory_management_example()
        await event_evaluation_example()
        await cicd_pipeline_example()
        await integration_showcase_example()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())

