"""
Comprehensive Linear Integration Example

This example demonstrates how to use the enhanced Linear integration
with all its comprehensive features including:
- Intelligent assignment detection
- Automated workflow management
- Codegen SDK integration
- Real-time progress tracking
- Health monitoring
"""

import asyncio
import os
from datetime import datetime
from contexten.extensions.linear import (
    LinearIntegrationAgent,
    get_linear_config,
    create_linear_integration_agent
)
from contexten.extensions.events.contexten_app import ContextenApp


async def basic_usage_example():
    """Basic usage of the comprehensive Linear integration"""
    print("🚀 Basic Linear Integration Example")
    print("=" * 50)
    
    # Method 1: Using the convenience function
    try:
        agent = await create_linear_integration_agent()
        print("✅ Linear integration agent created and initialized")
        
        # Get integration status
        status = await agent.get_integration_status()
        print(f"📊 Integration Status:")
        print(f"   Initialized: {status.initialized}")
        print(f"   Monitoring Active: {status.monitoring_active}")
        print(f"   Active Tasks: {status.active_tasks}")
        
        # Get comprehensive metrics
        metrics = await agent.get_metrics()
        print(f"📈 Metrics:")
        print(f"   Client Requests: {metrics.client_stats.requests_made}")
        print(f"   Events Processed: {metrics.webhook_stats.requests_successful}")
        print(f"   Assignments Detected: {metrics.assignment_stats.requests_made}")
        
        # Cleanup
        await agent.cleanup()
        print("✅ Agent cleanup completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def codegen_app_integration_example():
    """Example of integration with ContextenApp"""
    print("\n🏗️ ContextenApp Integration Example")
    
    # Initialize Linear configuration
    config = get_linear_config()
    
    # Create ContextenApp with Linear integration
    app = ContextenApp(name="linear-integration-example")
    
    # Get the Linear integration agent from the app
    linear_agent = app.linear.integration_agent
    
    print("✅ Linear agent initialized within ContextenApp")
    
    # Get integration status through ContextenApp
    status = await linear_agent.get_status()
    print(f"📊 Integration Status: {status.status}")
    print(f"   Monitoring Active: {status.monitoring_active}")
    print(f"   Last Health Check: {status.last_health_check}")
    
    # Get metrics through ContextenApp
    metrics = await linear_agent.get_metrics()
    print(f"📈 Metrics:")
    print(f"   Total Assignments: {metrics.total_assignments}")
    print(f"   Successful Assignments: {metrics.successful_assignments}")
    print(f"   Failed Assignments: {metrics.failed_assignments}")
    print(f"   Average Response Time: {metrics.average_response_time:.2f}s")
    
    # Cleanup
    if linear_agent.monitoring_active:
        await linear_agent.stop_monitoring()
    
    print("✅ ContextenApp Linear integration cleanup completed")


async def webhook_handling_example():
    """Example of webhook handling"""
    print("\n🔗 Webhook Handling Example")
    print("=" * 50)
    
    try:
        # Create agent
        config = get_linear_config()
        agent = LinearIntegrationAgent(config)
        
        if await agent.initialize():
            print("✅ Agent initialized for webhook handling")
            
            # Simulate webhook payload
            webhook_payload = {
                "type": "Issue",
                "action": "update",
                "data": {
                    "id": "example-issue-id",
                    "title": "Implement new feature",
                    "description": "Please implement a new authentication system",
                    "assignee": {
                        "id": config.bot.bot_user_id or "bot-user-id",
                        "name": "Codegen Bot",
                        "email": config.bot.bot_email or "bot@example.com"
                    },
                    "labels": {
                        "nodes": [
                            {"name": "ai", "color": "#ff0000"},
                            {"name": "automation", "color": "#00ff00"}
                        ]
                    }
                },
                "url": "https://linear.app/example/issue/EX-123",
                "createdAt": datetime.now().isoformat()
            }
            
            # Process event directly (simulating webhook)
            success = await agent.process_event_directly(webhook_payload)
            if success:
                print("✅ Webhook event processed successfully")
                
                # Check if any tasks were created
                active_tasks = agent.workflow_automation.get_active_tasks()
                if active_tasks:
                    print(f"📋 Created {len(active_tasks)} task(s)")
                    for issue_id, task_info in active_tasks.items():
                        print(f"   Task for issue {issue_id}: {task_info['status']}")
                else:
                    print("📋 No tasks created (assignment may not have been detected)")
            else:
                print("❌ Failed to process webhook event")
            
            await agent.cleanup()
        else:
            print("❌ Failed to initialize agent")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def assignment_detection_example():
    """Example of assignment detection and auto-assignment"""
    print("\n🎯 Assignment Detection Example")
    print("=" * 50)
    
    try:
        config = get_linear_config()
        agent = LinearIntegrationAgent(config)
        
        if await agent.initialize():
            print("✅ Agent initialized for assignment detection")
            
            # Get assignment detector stats
            assignment_stats = agent.assignment_detector.get_assignment_stats()
            print(f"📊 Assignment Stats:")
            print(f"   Assignments Detected: {assignment_stats.assignments_detected}")
            print(f"   Auto-assignments Made: {assignment_stats.auto_assignments_made}")
            print(f"   Rate Limit Hits: {assignment_stats.rate_limit_hits}")
            
            # Get rate limit info
            rate_limit_info = agent.assignment_detector.get_rate_limit_info()
            print(f"⏱️ Rate Limit Info:")
            print(f"   Current Hour Assignments: {rate_limit_info['current_hour_assignments']}")
            print(f"   Max Per Hour: {rate_limit_info['max_assignments_per_hour']}")
            print(f"   Remaining: {rate_limit_info['remaining_assignments']}")
            
            # Test auto-assignment detection
            auto_assign_event = {
                "type": "Issue",
                "data": {
                    "id": "auto-assign-test",
                    "title": "Generate automated tests",
                    "description": "Please generate comprehensive unit tests for the authentication module",
                    "assignee": None,  # No assignee yet
                    "labels": {
                        "nodes": [
                            {"name": "ai", "color": "#ff0000"},  # Auto-assign label
                            {"name": "testing", "color": "#0000ff"}
                        ]
                    }
                }
            }
            
            should_auto_assign = await agent.assignment_detector.detect_auto_assignment_candidates(auto_assign_event)
            print(f"🤖 Auto-assignment candidate detected: {should_auto_assign}")
            
            await agent.cleanup()
        else:
            print("❌ Failed to initialize agent")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def workflow_automation_example():
    """Example of workflow automation features"""
    print("\n⚙️ Workflow Automation Example")
    print("=" * 50)
    
    try:
        config = get_linear_config()
        agent = LinearIntegrationAgent(config)
        
        if await agent.initialize():
            print("✅ Agent initialized for workflow automation")
            
            # Get workflow stats
            workflow_stats = agent.workflow_automation.get_workflow_stats()
            print(f"📊 Workflow Stats:")
            print(f"   Tasks Created: {workflow_stats.tasks_created}")
            print(f"   Tasks Completed: {workflow_stats.tasks_completed}")
            print(f"   Tasks Failed: {workflow_stats.tasks_failed}")
            print(f"   Progress Updates Sent: {workflow_stats.progress_updates_sent}")
            
            # Get active tasks
            active_tasks = agent.workflow_automation.get_active_tasks()
            print(f"📋 Active Tasks: {len(active_tasks)}")
            
            if active_tasks:
                for issue_id, task_info in active_tasks.items():
                    print(f"   Issue {issue_id}:")
                    print(f"     Status: {task_info['status']}")
                    print(f"     Progress: {task_info['progress']:.1f}%")
                    print(f"     Current Step: {task_info['current_step']}")
            
            # Simulate creating a task from an issue
            from contexten.extensions.linear.types import LinearIssue, LinearLabel
            
            test_issue = LinearIssue(
                id="test-issue-123",
                title="Implement user authentication",
                description="""
                Requirements:
                - Implement JWT-based authentication
                - Add password hashing with bcrypt
                - Create login and logout endpoints
                - Add middleware for protected routes
                
                Acceptance Criteria:
                - Users can register with email and password
                - Users can login and receive JWT token
                - Protected routes require valid JWT
                - Passwords are securely hashed
                """,
                labels=[
                    LinearLabel(id="1", name="feature", color="#00ff00"),
                    LinearLabel(id="2", name="backend", color="#0000ff")
                ]
            )
            
            # Create task
            task = await agent.workflow_automation.create_task_from_issue(test_issue)
            if task:
                print(f"✅ Created task: {task.id}")
                print(f"   Task Type: {task.metadata.get('task_type', 'unknown')}")
                print(f"   Template: {task.metadata.get('template', 'unknown')}")
                
                # Start the task (this will simulate execution)
                if config.workflow.auto_start_tasks:
                    print("🚀 Starting task execution...")
                    success = await agent.workflow_automation.start_task(task.id)
                    print(f"   Task execution result: {'✅ Success' if success else '❌ Failed'}")
            else:
                print("❌ Failed to create task")
            
            await agent.cleanup()
        else:
            print("❌ Failed to initialize agent")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def monitoring_and_health_example():
    """Example of monitoring and health check features"""
    print("\n🏥 Monitoring and Health Example")
    print("=" * 50)
    
    try:
        config = get_linear_config()
        agent = LinearIntegrationAgent(config)
        
        if await agent.initialize():
            print("✅ Agent initialized for monitoring")
            
            # Start monitoring
            await agent.start_monitoring()
            print("📡 Monitoring started")
            
            # Wait a bit to let monitoring run
            await asyncio.sleep(2)
            
            # Get comprehensive metrics
            metrics = await agent.get_metrics()
            print(f"📊 Comprehensive Metrics:")
            print(f"   Collection Time: {metrics.collected_at}")
            print(f"   Integration Status: {'✅ Running' if metrics.status.initialized else '❌ Failed'}")
            
            # Component health
            components = {
                "Linear Client": metrics.client_stats,
                "Webhook Processor": metrics.webhook_stats,
                "Assignment Detector": metrics.assignment_stats,
                "Workflow Automation": metrics.workflow_stats
            }
            
            print(f"\n🔧 Component Health:")
            for name, stats in components.items():
                uptime = stats.uptime_seconds
                success_rate = (stats.requests_successful / max(stats.requests_made, 1)) * 100
                print(f"   {name}:")
                print(f"     Uptime: {uptime:.1f}s")
                print(f"     Success Rate: {success_rate:.1f}%")
                print(f"     Last Error: {stats.last_error or 'None'}")
            
            # Queue information
            queue_info = agent.webhook_processor.get_queue_info()
            print(f"\n📬 Event Queue:")
            print(f"   Queue Size: {queue_info['queue_size']}/{queue_info['max_queue_size']}")
            print(f"   Failed Events: {queue_info['failed_events']}")
            print(f"   Registered Handlers: {queue_info['registered_handlers']}")
            print(f"   Global Handlers: {queue_info['global_handlers']}")
            
            # Stop monitoring
            await agent.stop_monitoring()
            print("📡 Monitoring stopped")
            
            await agent.cleanup()
        else:
            print("❌ Failed to initialize agent")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def configuration_example():
    """Example of configuration management"""
    print("\n⚙️ Configuration Example")
    print("=" * 50)
    
    try:
        # Load configuration
        config = get_linear_config()
        
        print(f"📋 Configuration Summary:")
        print(f"   Enabled: {config.enabled}")
        print(f"   API Key Configured: {'✅' if config.api.api_key else '❌'}")
        print(f"   Webhook Secret Configured: {'✅' if config.webhook.webhook_secret else '❌'}")
        print(f"   Bot User ID: {config.bot.bot_user_id or 'Not set'}")
        print(f"   Bot Email: {config.bot.bot_email or 'Not set'}")
        
        print(f"\n🎯 Assignment Configuration:")
        print(f"   Auto-assign Labels: {', '.join(config.assignment.auto_assign_labels)}")
        print(f"   Auto-assign Keywords: {', '.join(config.assignment.auto_assign_keywords)}")
        print(f"   Max Assignments/Hour: {config.assignment.max_assignments_per_hour}")
        
        print(f"\n⚙️ Workflow Configuration:")
        print(f"   Auto-start Tasks: {config.workflow.auto_start_tasks}")
        print(f"   Auto-update Status: {config.workflow.auto_update_status}")
        print(f"   Task Timeout: {config.workflow.task_timeout}s")
        
        print(f"\n📊 Monitoring Configuration:")
        print(f"   Monitoring Enabled: {config.monitoring.enabled}")
        print(f"   Monitoring Interval: {config.monitoring.monitoring_interval}s")
        print(f"   Health Check Interval: {config.monitoring.health_check_interval}s")
        
        # Validate configuration
        errors = config.validate()
        if errors:
            print(f"\n❌ Configuration Errors:")
            for error in errors:
                print(f"   - {error}")
        else:
            print(f"\n✅ Configuration is valid")
        
        # Show configuration as dictionary (with secrets masked)
        config_dict = config.to_dict()
        print(f"\n📄 Configuration Dictionary (secrets masked):")
        import json
        print(json.dumps(config_dict, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all examples"""
    print("🎉 Comprehensive Linear Integration Examples")
    print("=" * 60)
    
    # Check if Linear is configured
    config = get_linear_config()
    if not config.enabled:
        print("⚠️ Linear integration is disabled. Set LINEAR_ENABLED=true to enable.")
        print("📝 You can also set other configuration variables for full functionality.")
        print("\nRunning examples with limited functionality...\n")
    elif not config.api.api_key:
        print("⚠️ LINEAR_API_KEY not configured. Some examples may not work fully.")
        print("📝 Set LINEAR_API_KEY to your Linear API key for full functionality.\n")
    
    # Run examples
    examples = [
        configuration_example,
        basic_usage_example,
        codegen_app_integration_example,
        webhook_handling_example,
        assignment_detection_example,
        workflow_automation_example,
        monitoring_and_health_example
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example {example.__name__} failed: {e}")
        
        print()  # Add spacing between examples
    
    print("🎉 All examples completed!")
    print("\n📚 For more information, see:")
    print("   - src/contexten/extensions/linear/README.md")
    print("   - Configuration template: create_config_template()")


if __name__ == "__main__":
    # Set up basic environment if not configured
    if not os.getenv("LINEAR_ENABLED"):
        os.environ["LINEAR_ENABLED"] = "true"
    
    # Run examples
    asyncio.run(main())
