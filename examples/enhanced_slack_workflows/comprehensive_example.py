"""Comprehensive example of enhanced Slack integration with team communication and workflows."""

import asyncio
import os
from datetime import datetime, timedelta
from contexten.extensions.events.contexten_app import ContextenApp
from contexten.extensions.slack.enhanced_client import NotificationContext
from contexten.extensions.slack.cross_platform_coordinator import PlatformType

# Set up environment variables for the example
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-your-bot-token")
os.environ.setdefault("SLACK_SIGNING_SECRET", "your-signing-secret")
os.environ.setdefault("SLACK_ENABLE_ANALYTICS", "true")
os.environ.setdefault("SLACK_ENABLE_ROUTING", "true")
os.environ.setdefault("SLACK_ENABLE_CROSS_PLATFORM", "true")
os.environ.setdefault("SLACK_ENABLE_WORKFLOWS", "true")


class EnhancedSlackDemo:
    """Demonstration of enhanced Slack integration capabilities."""
    
    def __init__(self):
        # Initialize the ContextenApp with enhanced Slack features
        self.app = ContextenApp("enhanced-slack-demo")
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Set up enhanced event handlers with backward compatibility."""
        
        # Traditional event handler (still works)
        @self.app.slack.event("app_mention")
        async def handle_mention(event):
            """Handle app mentions with enhanced features."""
            print(f"📱 App mentioned by {event.user}: {event.text}")
            
            # Use enhanced client if available
            if self.app.slack.enhanced_client:
                context = NotificationContext(
                    event_type="app_mention_response",
                    priority="normal",
                    target_channels=[event.channel],
                    thread_ts=event.ts,
                    metadata={
                        "original_user": event.user,
                        "original_text": event.text
                    }
                )
                
                await self.app.slack.send_enhanced_notification(
                    event_data={
                        "title": "👋 Hello from Enhanced Slack!",
                        "message": f"Thanks for mentioning me, <@{event.user}>! I now have enhanced capabilities including intelligent notifications, workflow coordination, and team analytics.",
                        "features": [
                            "🎯 Intelligent notification routing",
                            "🔄 Interactive workflow components", 
                            "📊 Team communication analytics",
                            "🔗 Cross-platform integration",
                            "⚡ Real-time performance (<1s notifications)"
                        ]
                    },
                    context=context
                )
            else:
                # Fallback to basic client
                self.app.slack.client.chat_postMessage(
                    channel=event.channel,
                    text=f"Hello <@{event.user}>! (Basic mode)",
                    thread_ts=event.ts
                )
        
        # Enhanced workflow event handler
        @self.app.slack.event("message")
        async def handle_message(event):
            """Handle messages with workflow detection."""
            if "workflow" in event.text.lower() and self.app.slack.enhanced_client:
                await self.demonstrate_workflow_coordination(event)
    
    async def demonstrate_intelligent_notifications(self):
        """Demonstrate intelligent notification routing and filtering."""
        print("\n🎯 Demonstrating Intelligent Notifications...")
        
        # High priority issue notification
        high_priority_context = NotificationContext(
            event_type="issue_assigned",
            priority="urgent",
            source_platform="linear",
            target_channels=["#urgent-alerts"],
            target_users=["tech_lead", "on_call_engineer"],
            metadata={
                "repository": "payment-service",
                "assignee": "developer1",
                "issue_type": "critical_bug"
            }
        )
        
        result = await self.app.slack.send_enhanced_notification(
            event_data={
                "title": "🚨 Critical Payment Service Bug",
                "message": "Payment processing is failing for 15% of transactions",
                "url": "https://linear.app/issue/PAY-123",
                "assignee": "developer1",
                "severity": "critical"
            },
            context=high_priority_context
        )
        
        print(f"✅ High priority notification sent in {result.get('duration_seconds', 0):.3f}s")
        
        # Code review notification with smart routing
        review_context = NotificationContext(
            event_type="pr_review_requested",
            priority="normal",
            source_platform="github",
            metadata={
                "repository": "user-service",
                "author": "developer2",
                "reviewers": ["senior_dev1", "senior_dev2"],
                "pr_size": "medium"
            }
        )
        
        result = await self.app.slack.send_enhanced_notification(
            event_data={
                "title": "👀 Code Review Requested",
                "message": "New authentication feature ready for review",
                "url": "https://github.com/org/user-service/pull/456",
                "author": "developer2",
                "changes": "+127 -45 lines"
            },
            context=review_context
        )
        
        print(f"✅ Code review notification sent in {result.get('duration_seconds', 0):.3f}s")
    
    async def demonstrate_workflow_coordination(self, trigger_event=None):
        """Demonstrate interactive workflow coordination."""
        print("\n🔄 Demonstrating Workflow Coordination...")
        
        # Deployment approval workflow
        deployment_workflow = await self.app.slack.coordinate_workflow(
            workflow_type="approval",
            data={
                "workflow_id": f"deploy_prod_{int(datetime.now().timestamp())}",
                "title": "Production Deployment Approval",
                "description": "Deploy user-service v2.3.0 to production environment",
                "approvers": ["tech_lead", "product_manager", "devops_lead"],
                "deadline": datetime.now() + timedelta(hours=2),
                "notification_channels": ["#deployments", "#leadership"],
                "metadata": {
                    "service": "user-service",
                    "version": "v2.3.0",
                    "environment": "production",
                    "risk_level": "medium"
                },
                "escalation_rules": {
                    "delay_hours": 1,
                    "escalate_to": ["engineering_manager"]
                }
            }
        )
        
        print(f"✅ Deployment workflow created: {deployment_workflow.get('workflow_id')}")
        
        # Code review workflow
        review_workflow = await self.app.slack.coordinate_workflow(
            workflow_type="review",
            data={
                "workflow_id": f"review_{int(datetime.now().timestamp())}",
                "pr_title": "Add OAuth 2.0 authentication",
                "pr_url": "https://github.com/org/auth-service/pull/789",
                "author": "developer3",
                "reviewers": ["senior_dev1", "security_expert"],
                "notification_channels": ["#code-reviews"],
                "metadata": {
                    "complexity": "high",
                    "security_impact": "high",
                    "testing_required": True
                }
            }
        )
        
        print(f"✅ Code review workflow created: {review_workflow.get('workflow_id')}")
        
        # Task assignment workflow
        task_workflow = await self.app.slack.coordinate_workflow(
            workflow_type="task_assignment",
            data={
                "workflow_id": f"task_{int(datetime.now().timestamp())}",
                "task_title": "Implement rate limiting",
                "description": "Add rate limiting to API endpoints to prevent abuse",
                "assignee": "developer4",
                "priority": "high",
                "deadline": datetime.now() + timedelta(days=5),
                "notification_channels": ["#backend-team"],
                "metadata": {
                    "epic": "API Security",
                    "story_points": 8,
                    "dependencies": ["auth-service-update"]
                }
            }
        )
        
        print(f"✅ Task assignment workflow created: {task_workflow.get('workflow_id')}")
    
    async def demonstrate_cross_platform_integration(self):
        """Demonstrate cross-platform event correlation."""
        print("\n🔗 Demonstrating Cross-Platform Integration...")
        
        if not self.app.slack.enhanced_client:
            print("❌ Enhanced client not available for cross-platform demo")
            return
        
        # Simulate Linear issue creation
        linear_event = {
            "type": "Issue",
            "action": "create",
            "data": {
                "id": "AUTH-456",
                "title": "Implement single sign-on",
                "description": "Add SSO support for enterprise customers",
                "assignee": {"id": "developer5", "name": "Alice Developer"},
                "creator": {"id": "product_manager", "name": "Bob PM"},
                "state": {"name": "Todo"},
                "url": "https://linear.app/issue/AUTH-456",
                "project": {"name": "Authentication"}
            }
        }
        
        # Process Linear event
        coordinator = self.app.slack.enhanced_client.notification_router
        if hasattr(coordinator, 'cross_platform_coordinator'):
            result = await coordinator.cross_platform_coordinator.process_platform_event(
                platform=PlatformType.LINEAR,
                event_data=linear_event
            )
            print(f"✅ Linear event processed: {result.get('status')}")
        
        # Simulate GitHub PR creation (correlated with Linear issue)
        github_event = {
            "action": "opened",
            "pull_request": {
                "id": 789,
                "title": "Implement single sign-on (AUTH-456)",
                "body": "This PR implements SSO support as requested in Linear issue AUTH-456",
                "user": {"login": "developer5"},
                "assignee": {"login": "senior_dev2"},
                "state": "open",
                "html_url": "https://github.com/org/auth-service/pull/789"
            },
            "repository": {
                "name": "auth-service",
                "full_name": "org/auth-service"
            }
        }
        
        # Process GitHub event (should correlate with Linear issue)
        if hasattr(coordinator, 'cross_platform_coordinator'):
            result = await coordinator.cross_platform_coordinator.process_platform_event(
                platform=PlatformType.GITHUB,
                event_data=github_event
            )
            print(f"✅ GitHub event processed: {result.get('status')}")
            print(f"📊 Correlations found: {len(result.get('correlations', []))}")
    
    async def demonstrate_team_analytics(self):
        """Demonstrate team communication analytics."""
        print("\n📊 Demonstrating Team Analytics...")
        
        if not self.app.slack.enhanced_client or not self.app.slack.enhanced_client.analytics_engine:
            print("❌ Analytics engine not available")
            return
        
        # Analyze communication patterns
        comm_analysis = await self.app.slack.enhanced_client.analyze_team_communication("week")
        
        print("📈 Weekly Communication Analysis:")
        print(f"  • Total messages: {comm_analysis.get('summary', {}).get('total_messages', 0)}")
        print(f"  • Active participants: {comm_analysis.get('summary', {}).get('active_participants', 0)}")
        print(f"  • Avg response time: {comm_analysis.get('summary', {}).get('avg_response_time_hours', 0):.1f} hours")
        print(f"  • Insights generated: {comm_analysis.get('summary', {}).get('insights_count', 0)}")
        
        # Generate productivity insights
        productivity = await self.app.slack.enhanced_client.analytics_engine.generate_productivity_insights("month")
        
        print("\n🚀 Monthly Productivity Insights:")
        workflow_analysis = productivity.get('workflow_analysis', {})
        print(f"  • Total workflows: {workflow_analysis.get('total_workflows', 0)}")
        
        # Generate team health report
        health_report = await self.app.slack.enhanced_client.analytics_engine.generate_team_health_report()
        
        print("\n💚 Team Health Report:")
        health_metrics = health_report.get('health_metrics', {})
        print(f"  • Overall score: {health_metrics.get('overall_score', 0):.1%}")
        print(f"  • Communication health: {health_metrics.get('communication_health', {}).get('status', 'unknown')}")
        print(f"  • Workflow health: {health_metrics.get('workflow_health', {}).get('status', 'unknown')}")
        
        # Show recommendations
        recommendations = health_report.get('recommendations', [])
        if recommendations:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec}")
    
    async def demonstrate_performance_monitoring(self):
        """Demonstrate performance monitoring capabilities."""
        print("\n⚡ Demonstrating Performance Monitoring...")
        
        # Test notification performance
        start_time = datetime.now()
        
        context = NotificationContext(
            event_type="performance_test",
            priority="normal",
            target_channels=["#general"]
        )
        
        result = await self.app.slack.send_enhanced_notification(
            event_data={
                "title": "Performance Test",
                "message": "Testing notification delivery speed"
            },
            context=context
        )
        
        duration = result.get('duration_seconds', 0)
        print(f"📊 Notification Performance:")
        print(f"  • Delivery time: {duration:.3f}s")
        print(f"  • Target: <1.000s")
        print(f"  • Status: {'✅ PASS' if duration < 1.0 else '❌ FAIL'}")
        
        # Test interactive component performance
        if self.app.slack.enhanced_client:
            start_time = datetime.now()
            
            # Simulate interactive component payload
            interactive_payload = {
                "type": "block_actions",
                "actions": [{"action_id": "test_button", "value": "test"}],
                "user": {"id": "test_user"},
                "channel": {"id": "test_channel"}
            }
            
            result = await self.app.slack.enhanced_client.handle_interactive_component(interactive_payload)
            duration = result.get('duration_seconds', 0)
            
            print(f"\n🖱️ Interactive Component Performance:")
            print(f"  • Response time: {duration:.3f}s")
            print(f"  • Target: <0.500s")
            print(f"  • Status: {'✅ PASS' if duration < 0.5 else '❌ FAIL'}")
    
    async def run_comprehensive_demo(self):
        """Run the complete enhanced Slack integration demonstration."""
        print("🚀 Enhanced Slack Integration Comprehensive Demo")
        print("=" * 50)
        
        # Check if enhanced client is available
        if self.app.slack.enhanced_client:
            print("✅ Enhanced Slack client initialized successfully")
            print(f"📊 Analytics enabled: {self.app.slack.enhanced_client.config.enable_analytics}")
            print(f"🎯 Intelligent routing enabled: {self.app.slack.enhanced_client.config.enable_intelligent_routing}")
            print(f"🔗 Cross-platform enabled: {self.app.slack.enhanced_client.config.enable_cross_platform}")
            print(f"🔄 Interactive workflows enabled: {self.app.slack.enhanced_client.config.enable_interactive_workflows}")
        else:
            print("⚠️ Enhanced Slack client not available - running in basic mode")
        
        try:
            # Run all demonstrations
            await self.demonstrate_intelligent_notifications()
            await self.demonstrate_workflow_coordination()
            await self.demonstrate_cross_platform_integration()
            await self.demonstrate_team_analytics()
            await self.demonstrate_performance_monitoring()
            
            print("\n🎉 Comprehensive demo completed successfully!")
            print("\nKey Features Demonstrated:")
            print("  ✅ Intelligent notification routing with user preferences")
            print("  ✅ Interactive workflow coordination (approval, review, task assignment)")
            print("  ✅ Cross-platform event correlation (Linear ↔ GitHub ↔ Slack)")
            print("  ✅ Team communication analytics and insights")
            print("  ✅ Real-time performance monitoring (<1s notifications, <500ms interactions)")
            print("  ✅ Backward compatibility with existing Slack integration")
            
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main function to run the enhanced Slack demo."""
    demo = EnhancedSlackDemo()
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    # Run the comprehensive demo
    asyncio.run(main())

