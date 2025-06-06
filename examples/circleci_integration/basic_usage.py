"""
Basic CircleCI Integration Usage Example

This example demonstrates how to set up and use the CircleCI integration
for monitoring builds and automatically fixing failures.
"""

import asyncio
import os
from pathlib import Path

from src.contexten.extensions.circleci import (
    CircleCIIntegrationAgent,
    CircleCIIntegrationConfig,
    APIConfig,
    WebhookConfig
)


async def basic_monitoring_example():
    """Basic build monitoring example"""
    print("🔄 Basic CircleCI Monitoring Example")
    print("=" * 50)
    
    # Create configuration
    config = CircleCIIntegrationConfig(
        api=APIConfig(
            api_token=os.getenv("CIRCLECI_API_TOKEN", "your-token-here")
        ),
        webhook=WebhookConfig(
            webhook_secret=os.getenv("CIRCLECI_WEBHOOK_SECRET", "your-secret-here"),
            validate_signatures=True
        ),
        debug_mode=True  # Enable debug mode for example
    )
    
    # Initialize agent
    agent = CircleCIIntegrationAgent(config)
    
    try:
        # Start monitoring
        print("🚀 Starting CircleCI integration...")
        await agent.start()
        
        # Check health
        health = await agent.health_check()
        print(f"✅ Health Status: {'Healthy' if health['healthy'] else 'Unhealthy'}")
        print(f"📊 Uptime: {health['uptime']:.2f} seconds")
        
        # Get initial metrics
        metrics = agent.get_metrics()
        print(f"📈 Initial Metrics:")
        print(f"   - Builds Monitored: {metrics.builds_monitored}")
        print(f"   - Failures Detected: {metrics.failures_detected}")
        print(f"   - Projects Monitored: {metrics.projects_monitored}")
        
        # Simulate webhook processing
        print("\n🔗 Simulating webhook processing...")
        
        sample_webhook = {
            "type": "workflow-completed",
            "id": "example-event-123",
            "happened_at": "2024-01-01T12:00:00Z",
            "workflow": {
                "id": "workflow-123",
                "name": "test-workflow",
                "project_slug": "gh/your-org/your-repo",
                "status": "failed",
                "pipeline_id": "pipeline-123",
                "pipeline_number": 42
            },
            "project": {
                "slug": "gh/your-org/your-repo",
                "name": "your-repo",
                "organization_name": "your-org"
            }
        }
        
        import json
        headers = {"content-type": "application/json"}
        body = json.dumps(sample_webhook)
        
        result = await agent.process_webhook(headers, body)
        print(f"📨 Webhook Result: {'Success' if result['success'] else 'Failed'}")
        
        if result['success']:
            print(f"   - Event ID: {result['event_id']}")
            print(f"   - Event Type: {result['event_type']}")
            print(f"   - Processing Time: {result['processing_time']:.3f}s")
        else:
            print(f"   - Error: {result['error']}")
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check active tasks
        active_tasks = await agent.get_active_tasks()
        print(f"\n⚙️ Active Tasks: {len(active_tasks)}")
        for task in active_tasks:
            print(f"   - {task['title']} ({task['status']})")
        
        # Get updated metrics
        updated_metrics = agent.get_metrics()
        print(f"\n📊 Updated Metrics:")
        print(f"   - Webhook Events: {updated_metrics.webhook_stats.workflow_events}")
        print(f"   - Analysis Performed: {updated_metrics.analysis_stats.failures_analyzed}")
        
        print("\n✅ Basic monitoring example completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        print("🛑 Stopping integration...")
        await agent.stop()


async def configuration_example():
    """Configuration management example"""
    print("\n🔧 Configuration Management Example")
    print("=" * 50)
    
    # Create configuration from environment
    try:
        config = CircleCIIntegrationConfig.from_env()
        print("✅ Configuration loaded from environment")
    except ValueError as e:
        print(f"❌ Environment configuration failed: {e}")
        print("💡 Using manual configuration instead...")
        
        # Manual configuration
        config = CircleCIIntegrationConfig(
            api=APIConfig(api_token="demo-token"),
            debug_mode=True
        )
    
    # Validate configuration
    issues = config.validate_configuration()
    if issues:
        print(f"⚠️ Configuration Issues:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ Configuration is valid")
    
    # Show configuration summary
    summary = config.summary
    print(f"\n📋 Configuration Summary:")
    print(f"   - API Configured: {summary['api_configured']}")
    print(f"   - GitHub Enabled: {summary['github_enabled']}")
    print(f"   - Auto-fix Enabled: {summary['auto_fix_enabled']}")
    print(f"   - Debug Mode: {summary['debug_mode']}")
    print(f"   - Production Ready: {summary['production_ready']}")
    
    # Save configuration to file
    config_file = Path("example_config.yaml")
    try:
        config.save_to_file(config_file)
        print(f"💾 Configuration saved to {config_file}")
        
        # Load it back
        loaded_config = CircleCIIntegrationConfig.from_file(config_file)
        print("✅ Configuration loaded from file successfully")
        
        # Clean up
        config_file.unlink()
        print("🗑️ Example config file cleaned up")
        
    except Exception as e:
        print(f"❌ File operations failed: {e}")


async def failure_analysis_example():
    """Failure analysis example"""
    print("\n🔍 Failure Analysis Example")
    print("=" * 50)
    
    # Create minimal config for analysis
    config = CircleCIIntegrationConfig(
        api=APIConfig(api_token="demo-token"),
        failure_analysis=FailureAnalysisConfig(
            enabled=True,
            log_analysis_depth="deep",
            pattern_matching_enabled=True
        ),
        debug_mode=True
    )
    
    agent = CircleCIIntegrationAgent(config)
    
    try:
        await agent.start()
        
        print("🔬 Analyzing build failure...")
        
        # Note: This would normally require a real API token and build
        # For demo purposes, we'll show what the analysis would look like
        
        try:
            analysis = await agent.analyze_build_failure("gh/demo-org/demo-repo", 123)
            
            print(f"📊 Analysis Results:")
            print(f"   - Failure Type: {analysis.failure_type.value}")
            print(f"   - Root Cause: {analysis.root_cause}")
            print(f"   - Confidence: {analysis.confidence:.2%}")
            print(f"   - Error Messages: {len(analysis.error_messages)}")
            print(f"   - Failed Tests: {len(analysis.failed_tests)}")
            print(f"   - Affected Files: {len(analysis.affected_files)}")
            print(f"   - Suggested Fixes: {len(analysis.suggested_fixes)}")
            
            if analysis.suggested_fixes:
                print(f"\n💡 Suggested Fixes:")
                for i, fix in enumerate(analysis.suggested_fixes[:3], 1):
                    print(f"   {i}. {fix}")
            
        except Exception as e:
            print(f"❌ Analysis failed (expected with demo token): {e}")
            print("💡 This would work with a real CircleCI API token")
        
    finally:
        await agent.stop()


async def webhook_server_example():
    """Example webhook server setup"""
    print("\n🌐 Webhook Server Example")
    print("=" * 50)
    
    # This example shows how you might integrate with a web framework
    print("📝 Example webhook endpoint setup:")
    
    webhook_code = '''
from aiohttp import web
from src.contexten.extensions.circleci import CircleCIIntegrationAgent

async def circleci_webhook_handler(request):
    """Handle CircleCI webhook"""
    
    # Get headers and body
    headers = dict(request.headers)
    body = await request.text()
    
    # Process with agent
    result = await agent.process_webhook(headers, body)
    
    if result["success"]:
        return web.json_response({
            "status": "ok",
            "event_id": result["event_id"]
        })
    else:
        return web.json_response({
            "status": "error",
            "error": result["error"]
        }, status=400)

# Setup routes
app = web.Application()
app.router.add_post('/webhooks/circleci', circleci_webhook_handler)

# Start server
web.run_app(app, host='0.0.0.0', port=8080)
'''
    
    print(webhook_code)
    print("\n💡 To use this:")
    print("1. Set up your webhook URL: https://your-domain.com/webhooks/circleci")
    print("2. Configure it in your CircleCI project settings")
    print("3. Set the webhook secret in your environment variables")


async def monitoring_dashboard_example():
    """Example monitoring dashboard data"""
    print("\n📊 Monitoring Dashboard Example")
    print("=" * 50)
    
    config = CircleCIIntegrationConfig(
        api=APIConfig(api_token="demo-token"),
        monitoring=MonitoringConfig(
            enabled=True,
            collect_metrics=True,
            health_check_interval=60
        ),
        debug_mode=True
    )
    
    agent = CircleCIIntegrationAgent(config)
    
    try:
        await agent.start()
        
        # Simulate some activity
        await asyncio.sleep(1)
        
        # Get comprehensive status
        health = await agent.health_check()
        metrics = agent.get_metrics()
        status = agent.get_integration_status()
        
        print("🏥 Health Status:")
        print(f"   - Overall: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}")
        print(f"   - API: {'✅' if health['components']['api'] else '❌'}")
        print(f"   - Webhook: {'✅' if health['components']['webhook'] else '❌'}")
        print(f"   - Analysis: {'✅' if health['components']['analysis'] else '❌'}")
        
        print(f"\n📈 Metrics:")
        print(f"   - Uptime: {metrics.uptime_duration}")
        print(f"   - Builds Monitored: {metrics.builds_monitored}")
        print(f"   - Failures Detected: {metrics.failures_detected}")
        print(f"   - Success Rate: {metrics.overall_success_rate:.1f}%")
        
        print(f"\n🔧 Webhook Stats:")
        webhook_stats = metrics.webhook_stats
        print(f"   - Total Requests: {webhook_stats.requests_total}")
        print(f"   - Successful: {webhook_stats.requests_successful}")
        print(f"   - Failed: {webhook_stats.requests_failed}")
        print(f"   - Success Rate: {webhook_stats.success_rate:.1f}%")
        
        print(f"\n🔍 Analysis Stats:")
        analysis_stats = metrics.analysis_stats
        print(f"   - Failures Analyzed: {analysis_stats.failures_analyzed}")
        print(f"   - Patterns Identified: {analysis_stats.patterns_identified}")
        print(f"   - High Confidence: {analysis_stats.high_confidence_analyses}")
        
        print(f"\n⚙️ Active Tasks:")
        active_tasks = await agent.get_active_tasks()
        if active_tasks:
            for task in active_tasks:
                print(f"   - {task['title']} ({task['status']})")
        else:
            print("   - No active tasks")
        
    finally:
        await agent.stop()


async def main():
    """Run all examples"""
    print("🎯 CircleCI Integration Examples")
    print("=" * 60)
    
    examples = [
        basic_monitoring_example,
        configuration_example,
        failure_analysis_example,
        webhook_server_example,
        monitoring_dashboard_example
    ]
    
    for example in examples:
        try:
            await example()
            await asyncio.sleep(1)  # Brief pause between examples
        except KeyboardInterrupt:
            print("\n⏹️ Examples interrupted by user")
            break
        except Exception as e:
            print(f"❌ Example failed: {e}")
            continue
    
    print("\n🎉 All examples completed!")
    print("\n💡 Next Steps:")
    print("1. Set up your CircleCI API token: export CIRCLECI_API_TOKEN='your-token'")
    print("2. Configure webhook secret: export CIRCLECI_WEBHOOK_SECRET='your-secret'")
    print("3. Set up GitHub token for PR creation: export GITHUB_TOKEN='your-token'")
    print("4. Configure Codegen SDK: export CODEGEN_API_TOKEN='your-token'")
    print("5. Deploy webhook endpoint and configure in CircleCI")


if __name__ == "__main__":
    # Import here to avoid issues if modules aren't available
    try:
        from src.contexten.extensions.circleci.config import (
            FailureAnalysisConfig, MonitoringConfig
        )
        
        asyncio.run(main())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure the CircleCI extension is properly installed")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

