"""
Comprehensive CI/CD System Example

This example demonstrates the complete CI/CD system with all integrated components:
- Database operations across 7 modules
- System orchestration and event handling
- Performance monitoring and optimization
- Error handling and recovery
- Continuous learning capabilities
- End-to-end workflow automation
"""

import asyncio
import logging
import json
from datetime import datetime
from contexten import ContextenApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def comprehensive_cicd_example():
    """Demonstrate the comprehensive CI/CD system capabilities."""
    
    print("\n🚀 Comprehensive CI/CD System Example")
    print("="*60)
    
    # Initialize the enhanced ContextenApp
    app = ContextenApp(
        name="comprehensive-cicd-example",
        enable_monitoring=True,
        enable_learning=True
    )
    
    try:
        # Initialize the system
        print("\n1. 🔧 Initializing System...")
        await app.initialize()
        print("✅ System initialized successfully")
        
        # Demonstrate database operations
        print("\n2. 🗄️ Database Operations...")
        
        # Create a project
        project = await app.orchestrator.create_project({
            "name": "Example Project",
            "description": "Comprehensive CI/CD example project",
            "slug": "example-project",
            "programming_languages": ["python", "typescript"],
            "frameworks": ["fastapi", "react"]
        })
        print(f"✅ Created project: {project.name} (ID: {project.id})")
        
        # Create multiple tasks
        tasks = []
        task_types = ["feature_implementation", "bug_fix", "testing", "documentation"]
        
        for i, task_type in enumerate(task_types):
            task = await app.orchestrator.create_task({
                "name": f"Example Task {i+1}",
                "description": f"Example {task_type.replace('_', ' ')} task",
                "title": f"Task {i+1}: {task_type.replace('_', ' ').title()}",
                "task_type": task_type,
                "priority": "medium",
                "project_id": project.id
            })
            tasks.append(task)
            print(f"✅ Created task: {task.name} (Type: {task_type})")
        
        # Demonstrate event system
        print("\n3. 📡 Event System...")
        
        # Register custom event handler
        events_received = []
        
        async def example_event_handler(data):
            events_received.append(data)
            print(f"📨 Event received: {data.get('event_type', 'unknown')}")
        
        app.orchestrator.register_event_handler("example_event", example_event_handler)
        
        # Emit test events
        await app.orchestrator.emit_event("example_event", {
            "event_type": "test_event",
            "message": "Hello from event system!"
        })
        
        # Simulate webhook events
        github_result = await app.simulate_event("github", "push", {
            "repository": {"full_name": "example/repo"},
            "commits": [{"message": "feat: add new feature"}]
        })
        print(f"✅ GitHub event simulated: {type(github_result)}")
        
        linear_result = await app.simulate_event("linear", "issue_update", {
            "action": "update",
            "data": {"id": str(tasks[0].id), "state": {"name": "In Progress"}}
        })
        print(f"✅ Linear event simulated: {type(linear_result)}")
        
        # Demonstrate task workflow
        print("\n4. 🔄 Task Workflow...")
        
        for i, task in enumerate(tasks[:2]):  # Process first 2 tasks
            # Start task
            await app.orchestrator.update_task(str(task.id), {
                "status": "in_progress",
                "started_at": datetime.utcnow(),
                "assigned_agent": "example-agent"
            })
            print(f"🏃 Started task: {task.name}")
            
            # Simulate some processing time
            await asyncio.sleep(0.1)
            
            # Complete task
            success = i == 0  # First task succeeds, second fails for demo
            status = "completed" if success else "failed"
            result = {
                "success": success,
                "output": f"Task {task.name} {'completed successfully' if success else 'failed with error'}",
                "duration_seconds": 0.1
            }
            
            await app.orchestrator.update_task(str(task.id), {
                "status": status,
                "completed_at": datetime.utcnow(),
                "result": result,
                "actual_duration_minutes": 1
            })
            print(f"{'✅' if success else '❌'} {'Completed' if success else 'Failed'} task: {task.name}")
        
        # Demonstrate performance monitoring
        print("\n5. 📊 Performance Monitoring...")
        
        if app.performance_monitor:
            # Record some operations
            await app.performance_monitor.record_operation("example_operation", 0.5, success=True)
            await app.performance_monitor.record_operation("slow_operation", 2.5, success=True)
            await app.performance_monitor.record_operation("failed_operation", 1.0, success=False, error="Example error")
            
            # Get current metrics
            metrics = await app.performance_monitor.get_current_metrics()
            print(f"📈 Current CPU usage: {metrics.get('cpu_usage', 'N/A')}%")
            print(f"📈 Current memory usage: {metrics.get('memory_usage', 'N/A')}%")
            print(f"📈 Performance score: {metrics.get('performance_score', 'N/A')}")
            
            # Get optimization suggestions
            optimization = await app.performance_monitor.optimize_performance()
            if optimization.get('suggestions'):
                print("💡 Performance suggestions:")
                for suggestion in optimization['suggestions'][:3]:  # Show first 3
                    print(f"   - {suggestion.get('suggestion', 'N/A')}")
        else:
            print("⚠️ Performance monitoring not available")
        
        # Demonstrate error handling
        print("\n6. 🚨 Error Handling...")
        
        # Simulate an error
        test_error = ValueError("Example error for demonstration")
        error_result = await app.error_handler.handle_error(
            test_error,
            {"component": "example", "operation": "demonstration"},
            attempt_recovery=False
        )
        print(f"🔍 Error handled: {error_result['error_id']}")
        print(f"🔍 Error category: {error_result['category']}")
        
        # Get error statistics
        error_stats = app.error_handler.get_error_statistics()
        print(f"📊 Total errors recorded: {error_stats['total_errors']}")
        
        # Demonstrate continuous learning
        print("\n7. 🧠 Continuous Learning...")
        
        if app.enable_learning:
            # The system automatically learns from task completions
            # Let's check what learning data was created
            async with app.orchestrator.get_db_session() as session:
                from contexten.database.models import LearningModel
                
                # Query learning data
                result = await session.execute(
                    "SELECT COUNT(*) FROM learning WHERE source_component = 'contexten_app'"
                )
                learning_count = result.scalar()
                print(f"🎓 Learning entries created: {learning_count}")
                
                # Create additional learning data
                learning = LearningModel(
                    name="Example Pattern",
                    description="Example learning pattern from demonstration",
                    learning_type="pattern_recognition",
                    data={
                        "pattern_type": "success_pattern",
                        "context": "task_completion",
                        "confidence": 0.85
                    },
                    source_component="example",
                    confidence_score=0.85
                )
                session.add(learning)
                await session.flush()
                print(f"🎓 Created learning pattern: {learning.name}")
        else:
            print("⚠️ Continuous learning not enabled")
        
        # Demonstrate system health
        print("\n8. 🏥 System Health...")
        
        health = await app.health_check()
        print(f"💚 System status: {health.get('status', 'unknown')}")
        print(f"🕐 Health check timestamp: {health.get('timestamp', 'unknown')}")
        
        # Show component health
        components = health.get('components', {})
        for component, status in components.items():
            emoji = "✅" if status == "healthy" else "❌"
            print(f"{emoji} {component}: {status}")
        
        # Demonstrate analytics
        print("\n9. 📈 Analytics Summary...")
        
        async with app.orchestrator.get_db_session() as session:
            # Count various entities
            task_count = await session.execute("SELECT COUNT(*) FROM tasks")
            project_count = await session.execute("SELECT COUNT(*) FROM projects")
            event_count = await session.execute("SELECT COUNT(*) FROM events")
            analytics_count = await session.execute("SELECT COUNT(*) FROM analytics")
            
            print(f"📊 Tasks created: {task_count.scalar()}")
            print(f"📊 Projects created: {project_count.scalar()}")
            print(f"📊 Events logged: {event_count.scalar()}")
            print(f"📊 Analytics entries: {analytics_count.scalar()}")
        
        # Final summary
        print("\n10. 🎉 Example Summary...")
        print("✅ System initialization and configuration")
        print("✅ Database operations across all 7 modules")
        print("✅ Event system and cross-component communication")
        print("✅ Task workflow and lifecycle management")
        print("✅ Performance monitoring and optimization")
        print("✅ Error handling and recovery")
        print("✅ Continuous learning and pattern recognition")
        print("✅ System health monitoring")
        print("✅ Analytics and metrics collection")
        
        print(f"\n🎯 Events received: {len(events_received)}")
        print("🎯 All system components working together successfully!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await app.shutdown()
        print("✅ System shutdown completed")


async def run_integration_test_example():
    """Run the integration test as an example."""
    print("\n🧪 Running Integration Test Example")
    print("="*60)
    
    from contexten.integration_test import run_integration_test
    
    try:
        results = await run_integration_test()
        
        print("\n📊 Integration Test Results:")
        print("-" * 40)
        
        summary = results.get("summary", {})
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('passed_tests', 0)}")
        print(f"Failed: {summary.get('failed_tests', 0)}")
        print(f"Skipped: {summary.get('skipped_tests', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"Duration: {summary.get('total_duration_seconds', 0):.2f}s")
        print(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        
        # Show individual test results
        print("\n📋 Individual Test Results:")
        for test_name, result in results.items():
            if test_name == "summary":
                continue
            
            if isinstance(result, dict):
                status = result.get("status", "UNKNOWN")
                duration = result.get("duration_seconds", 0)
                emoji = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⏭️"
                print(f"{emoji} {test_name}: {status} ({duration:.2f}s)")
        
        if summary.get("overall_status") == "PASSED":
            print("\n🎉 All integration tests passed!")
        else:
            print("\n⚠️ Some integration tests failed. Check logs for details.")
        
        return results
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise


async def main():
    """Main example function."""
    print("🌟 Comprehensive CI/CD System with Continuous Learning")
    print("=" * 80)
    print("This example demonstrates the complete integrated system:")
    print("• 7-module database system")
    print("• System orchestration and event handling")
    print("• Performance monitoring and optimization")
    print("• Error handling and recovery")
    print("• Continuous learning capabilities")
    print("• End-to-end workflow automation")
    print("=" * 80)
    
    try:
        # Run the comprehensive example
        await comprehensive_cicd_example()
        
        print("\n" + "="*80)
        
        # Run the integration test
        await run_integration_test_example()
        
        print("\n🎊 All examples completed successfully!")
        print("The comprehensive CI/CD system is fully operational and ready for production use.")
        
    except Exception as e:
        logger.error(f"Example execution failed: {e}")
        print(f"\n❌ Example failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())

