"""
Advanced CircleCI Integration Usage Examples

This example demonstrates advanced features including:
- Custom failure analysis patterns
- Fix generation and application
- Integration with GitHub and Codegen SDK
- Custom webhook handlers
- Performance monitoring and optimization
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.contexten.extensions.circleci import (
    CircleCIIntegrationAgent,
    CircleCIIntegrationConfig,
    APIConfig,
    WebhookConfig,
    FailureAnalysisConfig,
    AutoFixConfig,
    GitHubIntegrationConfig,
    CodegenIntegrationConfig
)
from src.contexten.extensions.circleci.types import (
    CircleCIEvent, FailureAnalysis, GeneratedFix, FailureType, FixConfidence
)


async def custom_failure_analysis_example():
    """Example with custom failure analysis patterns"""
    print("🔬 Custom Failure Analysis Example")
    print("=" * 50)
    
    config = CircleCIIntegrationConfig(
        api=APIConfig(api_token=os.getenv("CIRCLECI_API_TOKEN", "demo-token")),
        failure_analysis=FailureAnalysisConfig(
            enabled=True,
            log_analysis_depth="deep",
            pattern_matching_enabled=True,
            similarity_search_enabled=True,
            pattern_learning_enabled=True,
            confidence_threshold=0.7
        ),
        debug_mode=True
    )
    
    agent = CircleCIIntegrationAgent(config)
    
    # Custom failure handler
    async def custom_failure_handler(event: CircleCIEvent):
        """Custom handler for failure events"""
        print(f"🚨 Custom handler: Processing failure in {event.project_slug}")
        
        if event.branch == "main":
            print("⚠️ Main branch failure - high priority!")
        
        # Custom analysis logic here
        print(f"📊 Event details:")
        print(f"   - Type: {event.type.value}")
        print(f"   - Status: {event.status.value if event.status else 'unknown'}")
        print(f"   - Branch: {event.branch or 'unknown'}")
        print(f"   - Commit: {event.commit_sha[:8] if event.commit_sha else 'unknown'}")
    
    try:
        await agent.start()
        
        # Register custom handler
        agent.webhook_processor.register_handler(
            handler=custom_failure_handler,
            name="custom-failure-handler",
            priority=200  # High priority
        )
        
        print("✅ Custom failure handler registered")
        
        # Simulate failure analysis
        print("\n🔍 Simulating failure analysis...")
        
        # Create mock failure event
        from src.contexten.extensions.circleci.types import CircleCIEvent, CircleCIEventType, BuildStatus
        
        mock_event = CircleCIEvent(
            id="custom-event-123",
            type=CircleCIEventType.WORKFLOW_COMPLETED,
            timestamp=datetime.now(),
            project_slug="gh/demo-org/demo-repo",
            organization="demo-org",
            workflow_id="workflow-123",
            status=BuildStatus.FAILED,
            branch="main",
            commit_sha="abc123def456"
        )
        
        # Process with custom handler
        await custom_failure_handler(mock_event)
        
        print("\n💡 Custom analysis patterns can include:")
        print("   - Project-specific error patterns")
        print("   - Branch-based priority handling")
        print("   - Custom notification logic")
        print("   - Integration with external monitoring")
        
    finally:
        await agent.stop()


async def fix_generation_example():
    """Example of fix generation and application"""
    print("\n🔧 Fix Generation Example")
    print("=" * 50)
    
    config = CircleCIIntegrationConfig(
        api=APIConfig(api_token=os.getenv("CIRCLECI_API_TOKEN", "demo-token")),
        auto_fix=AutoFixConfig(
            enabled=True,
            fix_confidence_threshold=0.6,
            enable_code_fixes=True,
            enable_config_fixes=True,
            enable_dependency_fixes=True,
            validate_fixes=True,
            require_human_approval=False
        ),
        github=GitHubIntegrationConfig(
            enabled=True,
            github_token=os.getenv("GITHUB_TOKEN"),
            auto_create_prs=True,
            pr_branch_prefix="circleci-autofix"
        ),
        codegen=CodegenIntegrationConfig(
            enabled=True,
            codegen_api_token=os.getenv("CODEGEN_API_TOKEN"),
            codegen_org_id=os.getenv("CODEGEN_ORG_ID")
        ),
        debug_mode=True
    )
    
    agent = CircleCIIntegrationAgent(config)
    
    try:
        await agent.start()
        
        print("🤖 Fix generation capabilities:")
        print("   - AI-powered code fixes using Codegen SDK")
        print("   - Template-based configuration fixes")
        print("   - Dependency resolution and updates")
        print("   - Automatic PR creation and validation")
        
        # Create mock failure analysis
        mock_analysis = FailureAnalysis(
            build_id="build-123",
            project_slug="gh/demo-org/demo-repo",
            analysis_timestamp=datetime.now(),
            failure_type=FailureType.TEST_FAILURE,
            root_cause="Jest test assertion failed: expected true but got false",
            confidence=0.85,
            error_messages=[
                "FAIL src/components/Button.test.js",
                "Expected: true, Received: false"
            ],
            affected_files=["src/components/Button.test.js", "src/components/Button.js"],
            suggested_fixes=[
                "Update test assertion to match expected behavior",
                "Fix Button component implementation",
                "Review test data and mocks"
            ]
        )
        
        print(f"\n📊 Mock Analysis:")
        print(f"   - Failure Type: {mock_analysis.failure_type.value}")
        print(f"   - Confidence: {mock_analysis.confidence:.1%}")
        print(f"   - Affected Files: {len(mock_analysis.affected_files)}")
        print(f"   - Suggested Fixes: {len(mock_analysis.suggested_fixes)}")
        
        # Generate fix
        print("\n🔧 Generating fix...")
        try:
            fix = await agent.generate_fix_for_analysis(mock_analysis)
            
            print(f"✅ Fix generated:")
            print(f"   - Fix ID: {fix.id}")
            print(f"   - Title: {fix.title}")
            print(f"   - Confidence: {fix.overall_confidence.value}")
            print(f"   - Code Fixes: {len(fix.code_fixes)}")
            print(f"   - Config Fixes: {len(fix.config_fixes)}")
            print(f"   - Dependency Fixes: {len(fix.dependency_fixes)}")
            
            if fix.code_fixes:
                print(f"\n📝 Code Fixes:")
                for i, code_fix in enumerate(fix.code_fixes[:2], 1):
                    print(f"   {i}. {code_fix.file_path}: {code_fix.description}")
            
            if fix.config_fixes:
                print(f"\n⚙️ Config Fixes:")
                for i, config_fix in enumerate(fix.config_fixes[:2], 1):
                    print(f"   {i}. {config_fix.file_path}: {config_fix.description}")
            
        except Exception as e:
            print(f"❌ Fix generation failed (expected with demo setup): {e}")
            print("💡 This would work with real API tokens and repository access")
        
    finally:
        await agent.stop()


async def github_integration_example():
    """Example of GitHub integration for PR creation"""
    print("\n🐙 GitHub Integration Example")
    print("=" * 50)
    
    config = CircleCIIntegrationConfig(
        api=APIConfig(api_token=os.getenv("CIRCLECI_API_TOKEN", "demo-token")),
        github=GitHubIntegrationConfig(
            enabled=True,
            github_token=os.getenv("GITHUB_TOKEN"),
            auto_create_prs=True,
            pr_auto_merge=False,
            pr_branch_prefix="circleci-fix",
            pr_title_template="🔧 Fix CircleCI build failure: {failure_type}",
            pr_description_template="""
## CircleCI Build Fix

**Failure Type**: {failure_type}
**Root Cause**: {root_cause}
**Confidence**: {confidence}

### Changes Made
{changes_description}

### Validation
{validation_results}

---
*This PR was automatically generated by the CircleCI integration.*
""",
            request_reviews=True,
            default_reviewers=["team-lead", "senior-dev"],
            add_labels=True,
            default_labels=["circleci", "automated-fix", "ci-fix"]
        ),
        debug_mode=True
    )
    
    print("🔧 GitHub Integration Configuration:")
    print(f"   - Auto Create PRs: {config.github.auto_create_prs}")
    print(f"   - Auto Merge: {config.github.pr_auto_merge}")
    print(f"   - Branch Prefix: {config.github.pr_branch_prefix}")
    print(f"   - Request Reviews: {config.github.request_reviews}")
    print(f"   - Default Labels: {', '.join(config.github.default_labels)}")
    
    if config.github.github_token:
        print("✅ GitHub token configured")
    else:
        print("⚠️ GitHub token not configured (set GITHUB_TOKEN environment variable)")
    
    print("\n📝 Example PR Creation Flow:")
    print("1. CircleCI build fails")
    print("2. Failure analysis identifies root cause")
    print("3. Fix is generated using AI/templates")
    print("4. New branch is created with fix")
    print("5. PR is created with detailed description")
    print("6. Reviewers are assigned and labels added")
    print("7. Validation tests are run")
    print("8. PR is ready for review/merge")


async def performance_monitoring_example():
    """Example of performance monitoring and optimization"""
    print("\n📊 Performance Monitoring Example")
    print("=" * 50)
    
    config = CircleCIIntegrationConfig(
        api=APIConfig(
            api_token=os.getenv("CIRCLECI_API_TOKEN", "demo-token"),
            rate_limit_requests_per_minute=300,
            max_retries=3,
            request_timeout=30
        ),
        webhook=WebhookConfig(
            max_queue_size=1000,
            processing_timeout=60,
            max_event_retries=3
        ),
        monitoring=MonitoringConfig(
            enabled=True,
            collect_metrics=True,
            health_check_interval=60,
            alert_on_failures=True,
            alert_threshold_failure_rate=0.1,
            alert_threshold_response_time=10.0
        ),
        debug_mode=True
    )
    
    agent = CircleCIIntegrationAgent(config)
    
    try:
        await agent.start()
        
        # Simulate load
        print("🔄 Simulating load for performance monitoring...")
        
        start_time = datetime.now()
        
        # Process multiple webhooks
        for i in range(10):
            webhook_payload = {
                "type": "ping",
                "id": f"perf-test-{i}",
                "happened_at": datetime.now().isoformat()
            }
            
            headers = {"content-type": "application/json"}
            body = json.dumps(webhook_payload)
            
            result = await agent.process_webhook(headers, body)
            if not result["success"]:
                print(f"❌ Webhook {i} failed: {result['error']}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Get performance metrics
        metrics = agent.get_metrics()
        health = await agent.health_check()
        
        print(f"\n📈 Performance Results:")
        print(f"   - Total Processing Time: {processing_time:.2f}s")
        print(f"   - Average per Webhook: {processing_time/10:.3f}s")
        print(f"   - Webhooks Processed: {metrics.webhook_stats.requests_total}")
        print(f"   - Success Rate: {metrics.webhook_stats.success_rate:.1f}%")
        print(f"   - Average Response Time: {metrics.webhook_stats.average_response_time:.3f}s")
        
        print(f"\n🏥 Health Metrics:")
        print(f"   - Overall Health: {'✅' if health['healthy'] else '❌'}")
        print(f"   - Uptime: {health['uptime']:.2f}s")
        print(f"   - Memory Usage: {health.get('memory_usage', 'N/A')}")
        
        # Queue information
        queue_info = agent.webhook_processor.get_queue_info()
        print(f"\n📦 Queue Status:")
        print(f"   - Current Size: {queue_info['queue_size']}")
        print(f"   - Max Size: {queue_info['max_queue_size']}")
        print(f"   - Utilization: {queue_info['queue_size']/queue_info['max_queue_size']*100:.1f}%")
        
        print(f"\n💡 Performance Optimization Tips:")
        print("   - Increase rate limits for high-volume projects")
        print("   - Adjust queue sizes based on load patterns")
        print("   - Monitor response times and set appropriate timeouts")
        print("   - Use health checks to detect performance degradation")
        print("   - Scale horizontally for very high loads")
        
    finally:
        await agent.stop()


async def custom_webhook_handlers_example():
    """Example of custom webhook handlers and routing"""
    print("\n🔗 Custom Webhook Handlers Example")
    print("=" * 50)
    
    config = CircleCIIntegrationConfig(
        api=APIConfig(api_token=os.getenv("CIRCLECI_API_TOKEN", "demo-token")),
        debug_mode=True
    )
    
    agent = CircleCIIntegrationAgent(config)
    
    # Custom handlers for different scenarios
    async def main_branch_handler(event: CircleCIEvent):
        """Handler for main branch events"""
        if event.branch == "main":
            print(f"🚨 CRITICAL: Main branch failure in {event.project_slug}")
            # Send urgent notifications
            # Escalate to on-call team
            # Create high-priority ticket
    
    async def test_failure_handler(event: CircleCIEvent):
        """Handler specifically for test failures"""
        if event.is_failure_event:
            print(f"🧪 Test failure detected in {event.project_slug}")
            # Analyze test patterns
            # Check for flaky tests
            # Update test metrics
    
    async def performance_handler(event: CircleCIEvent):
        """Handler for performance monitoring"""
        print(f"📊 Performance event: {event.type.value} in {event.project_slug}")
        # Track build times
        # Monitor resource usage
        # Detect performance regressions
    
    async def notification_handler(event: CircleCIEvent):
        """Handler for notifications"""
        if event.is_failure_event:
            print(f"📢 Sending notifications for failure in {event.project_slug}")
            # Send Slack notifications
            # Update dashboard
            # Log to monitoring system
    
    try:
        await agent.start()
        
        # Register custom handlers with different priorities
        handlers = [
            (main_branch_handler, "main-branch-handler", 1000),  # Highest priority
            (test_failure_handler, "test-failure-handler", 800),
            (performance_handler, "performance-handler", 600),
            (notification_handler, "notification-handler", 400)   # Lowest priority
        ]
        
        for handler, name, priority in handlers:
            agent.webhook_processor.register_handler(
                handler=handler,
                name=name,
                priority=priority
            )
            print(f"✅ Registered {name} (priority: {priority})")
        
        # Show handler information
        registered_handlers = agent.webhook_processor.get_handlers()
        print(f"\n📋 Registered Handlers ({len(registered_handlers)}):")
        for handler_info in registered_handlers:
            print(f"   - {handler_info['name']} (priority: {handler_info['priority']})")
        
        # Simulate different types of events
        test_events = [
            {
                "type": "workflow-completed",
                "id": "main-branch-failure",
                "happened_at": datetime.now().isoformat(),
                "workflow": {
                    "id": "workflow-123",
                    "project_slug": "gh/demo-org/critical-app",
                    "status": "failed"
                },
                "project": {"organization_name": "demo-org"},
                "pipeline": {"vcs": {"branch": "main"}}
            },
            {
                "type": "job-completed",
                "id": "test-failure",
                "happened_at": datetime.now().isoformat(),
                "job": {
                    "id": "job-123",
                    "project_slug": "gh/demo-org/test-app",
                    "status": "failed",
                    "web_url": "https://circleci.com/test"
                },
                "project": {"organization_name": "demo-org"},
                "pipeline": {"vcs": {"branch": "feature/new-feature"}}
            }
        ]
        
        print(f"\n🔄 Processing test events...")
        for i, event_data in enumerate(test_events, 1):
            headers = {"content-type": "application/json"}
            body = json.dumps(event_data)
            
            result = await agent.process_webhook(headers, body)
            print(f"   Event {i}: {'✅' if result['success'] else '❌'}")
        
        # Wait for processing
        await asyncio.sleep(1)
        
        print(f"\n💡 Custom Handler Benefits:")
        print("   - Specialized logic for different failure types")
        print("   - Priority-based processing")
        print("   - Flexible notification routing")
        print("   - Custom metrics and monitoring")
        print("   - Integration with external systems")
        
    finally:
        await agent.stop()


async def enterprise_deployment_example():
    """Example enterprise deployment configuration"""
    print("\n🏢 Enterprise Deployment Example")
    print("=" * 50)
    
    # Enterprise-grade configuration
    config = CircleCIIntegrationConfig(
        api=APIConfig(
            api_token=os.getenv("CIRCLECI_API_TOKEN", "demo-token"),
            rate_limit_requests_per_minute=1000,  # Higher limits
            max_retries=5,
            request_timeout=60
        ),
        webhook=WebhookConfig(
            webhook_secret=os.getenv("CIRCLECI_WEBHOOK_SECRET"),
            validate_signatures=True,
            validate_timestamps=True,
            max_queue_size=5000,  # Large queue
            processing_timeout=300,  # 5 minutes
            max_event_retries=5
        ),
        failure_analysis=FailureAnalysisConfig(
            enabled=True,
            log_analysis_depth="deep",
            max_log_lines=50000,  # More detailed analysis
            pattern_learning_enabled=True,
            cache_duration=timedelta(hours=48),  # Longer cache
            max_cache_size=10000
        ),
        auto_fix=AutoFixConfig(
            enabled=True,
            fix_confidence_threshold=0.8,  # Higher confidence required
            max_fixes_per_failure=5,
            validate_fixes=True,
            require_human_approval=True,  # Enterprise safety
            max_fix_attempts_per_day=50
        ),
        workflow=WorkflowConfig(
            enabled=True,
            max_concurrent_tasks=20,  # Higher concurrency
            task_timeout=7200,  # 2 hours
            progress_update_interval=30
        ),
        github=GitHubIntegrationConfig(
            enabled=True,
            github_token=os.getenv("GITHUB_TOKEN"),
            auto_create_prs=True,
            pr_auto_merge=False,  # Manual review required
            request_reviews=True,
            default_reviewers=["security-team", "platform-team"]
        ),
        security=SecurityConfig(
            use_environment_variables=True,
            credential_rotation_enabled=True,
            credential_rotation_interval=timedelta(days=30),
            audit_logging_enabled=True,
            audit_log_retention_days=365,  # 1 year retention
            enable_rate_limiting=True,
            max_requests_per_minute=500
        ),
        monitoring=MonitoringConfig(
            enabled=True,
            collect_metrics=True,
            metrics_retention_days=90,
            health_check_interval=30,  # More frequent checks
            alert_on_failures=True,
            alert_threshold_failure_rate=0.05,  # 5% threshold
            alert_threshold_response_time=5.0
        ),
        # Production settings
        debug_mode=False,
        dry_run_mode=False,
        monitor_all_projects=False,  # Explicit project list
        monitored_projects=[
            "gh/company/critical-service-1",
            "gh/company/critical-service-2",
            "gh/company/platform-core"
        ]
    )
    
    print("🔧 Enterprise Configuration:")
    print(f"   - Rate Limit: {config.api.rate_limit_requests_per_minute}/min")
    print(f"   - Queue Size: {config.webhook.max_queue_size}")
    print(f"   - Max Concurrent Tasks: {config.workflow.max_concurrent_tasks}")
    print(f"   - Security Features: {'✅' if config.security.audit_logging_enabled else '❌'}")
    print(f"   - Human Approval Required: {'✅' if config.auto_fix.require_human_approval else '❌'}")
    print(f"   - Monitored Projects: {len(config.monitored_projects)}")
    
    # Validate enterprise configuration
    issues = config.validate_configuration()
    if issues:
        print(f"\n⚠️ Configuration Issues:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"\n✅ Enterprise configuration is valid")
    
    print(f"\n🏭 Enterprise Deployment Checklist:")
    checklist = [
        ("API Token Configured", bool(os.getenv("CIRCLECI_API_TOKEN"))),
        ("Webhook Secret Set", bool(os.getenv("CIRCLECI_WEBHOOK_SECRET"))),
        ("GitHub Token Set", bool(os.getenv("GITHUB_TOKEN"))),
        ("Security Enabled", config.security.audit_logging_enabled),
        ("Monitoring Enabled", config.monitoring.enabled),
        ("Human Approval Required", config.auto_fix.require_human_approval),
        ("Production Mode", not config.debug_mode),
        ("Rate Limiting Enabled", config.security.enable_rate_limiting)
    ]
    
    for item, status in checklist:
        print(f"   {'✅' if status else '❌'} {item}")
    
    print(f"\n🚀 Deployment Recommendations:")
    print("   - Deploy behind load balancer for high availability")
    print("   - Use container orchestration (Kubernetes/Docker)")
    print("   - Set up monitoring and alerting")
    print("   - Configure log aggregation")
    print("   - Implement backup and disaster recovery")
    print("   - Regular security audits and updates")
    print("   - Performance testing and capacity planning")


async def main():
    """Run all advanced examples"""
    print("🚀 Advanced CircleCI Integration Examples")
    print("=" * 60)
    
    examples = [
        custom_failure_analysis_example,
        fix_generation_example,
        github_integration_example,
        performance_monitoring_example,
        custom_webhook_handlers_example,
        enterprise_deployment_example
    ]
    
    for example in examples:
        try:
            await example()
            await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Examples interrupted by user")
            break
        except Exception as e:
            print(f"❌ Example failed: {e}")
            continue
    
    print("\n🎉 All advanced examples completed!")
    print("\n🔗 Additional Resources:")
    print("   - CircleCI API Documentation: https://circleci.com/docs/api/")
    print("   - GitHub API Documentation: https://docs.github.com/en/rest")
    print("   - Codegen SDK Documentation: https://docs.codegen.com/")
    print("   - Webhook Security Best Practices")
    print("   - Enterprise Deployment Guide")


if __name__ == "__main__":
    try:
        # Import additional modules
        from src.contexten.extensions.circleci.config import (
            MonitoringConfig, SecurityConfig
        )
        
        asyncio.run(main())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

