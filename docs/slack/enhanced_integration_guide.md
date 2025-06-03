# Enhanced Slack Integration Guide

## Overview

The Enhanced Slack Integration extends the existing `src/contexten/extensions/events/slack.py` implementation with comprehensive team communication, real-time notifications, and workflow coordination capabilities while maintaining full backward compatibility.

## Features

### 🎯 Core Enhancements

- **Intelligent Notification Routing**: Smart filtering and routing based on user preferences and context
- **Interactive Workflow Components**: Approval workflows, task assignment, and status updates
- **Cross-Platform Integration**: Seamless coordination between Slack, Linear, and GitHub
- **Team Analytics & Insights**: Communication pattern analysis and productivity metrics
- **Advanced Block Kit Support**: Rich interactive messages and modals
- **Real-time Performance**: <1 second notification delivery, <500ms interactive responses

### 🔄 Backward Compatibility

The enhanced integration maintains 100% backward compatibility with existing implementations:

- All existing event handlers continue to work unchanged
- Original decorator patterns (`@app.slack.event`) remain functional
- Basic WebClient functionality is preserved
- No breaking changes to existing APIs

## Architecture

### Component Overview

```
Enhanced Slack Integration
├── EnhancedSlackClient          # Core client with intelligent features
├── NotificationRouter           # Smart routing and filtering
├── BlockKitBuilder             # Rich interactive components
├── AnalyticsEngine             # Team communication insights
├── CrossPlatformCoordinator    # Multi-platform integration
└── Enhanced Event Handler      # Backward-compatible event processing
```

### Integration Points

```python
# Existing integration (unchanged)
from contexten.extensions.events.slack import Slack

# Enhanced features (new)
from contexten.extensions.slack.enhanced_client import EnhancedSlackClient, SlackConfig
from contexten.extensions.slack.notification_router import NotificationRouter
from contexten.extensions.slack.block_kit_builder import BlockKitBuilder
```

## Quick Start

### 1. Environment Configuration

```bash
# Required (existing)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# Optional (enhanced features)
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_ENABLE_ANALYTICS=true
SLACK_ENABLE_ROUTING=true
SLACK_ENABLE_CROSS_PLATFORM=true
SLACK_ENABLE_WORKFLOWS=true
```

### 2. Basic Usage (Existing Pattern)

```python
from contexten.extensions.events.contexten_app import ContextenApp

# Create app (unchanged)
app = ContextenApp("my-app")

# Register event handlers (unchanged)
@app.slack.event("app_mention")
async def handle_mention(event):
    app.slack.client.chat_postMessage(
        channel=event.channel,
        text=f"Hello <@{event.user}>!"
    )
```

### 3. Enhanced Usage (New Features)

```python
from contexten.extensions.slack.enhanced_client import NotificationContext

# Send intelligent notification
context = NotificationContext(
    event_type="issue_assigned",
    priority="high",
    target_channels=["#team-alerts"],
    target_users=["user123"]
)

result = await app.slack.send_enhanced_notification(
    event_data={
        "title": "Critical Issue Assigned",
        "message": "High priority issue needs attention",
        "url": "https://linear.app/issue/123"
    },
    context=context
)

# Coordinate workflow
workflow_result = await app.slack.coordinate_workflow(
    workflow_type="approval",
    data={
        "title": "Deployment Approval",
        "description": "Production deployment requires approval",
        "approvers": ["manager1", "manager2"],
        "deadline": datetime.now() + timedelta(hours=2)
    }
)
```

## Configuration

### SlackConfig Options

```python
from contexten.extensions.slack.enhanced_client import SlackConfig

config = SlackConfig(
    # Required
    bot_token="xoxb-your-token",
    signing_secret="your-secret",
    
    # Optional
    app_token="xapp-your-token",
    
    # Performance settings
    notification_timeout=1.0,      # <1 second requirement
    interactive_timeout=0.5,       # <500ms requirement
    
    # Feature flags
    enable_analytics=True,
    enable_intelligent_routing=True,
    enable_cross_platform=True,
    enable_interactive_workflows=True,
    
    # Notification settings
    max_notifications_per_minute=60,
    enable_notification_aggregation=True,
    aggregation_window_seconds=30,
    
    # Analytics settings
    analytics_retention_days=90,
    enable_team_insights=True,
    enable_productivity_metrics=True
)
```

## Intelligent Notifications

### Notification Context

```python
from contexten.extensions.slack.enhanced_client import NotificationContext

context = NotificationContext(
    event_type="pr_review_requested",
    priority="normal",  # low, normal, high, urgent
    source_platform="github",
    target_channels=["#code-reviews"],
    target_users=["reviewer1", "reviewer2"],
    thread_ts="1234567890.123456",  # Optional thread
    correlation_id="workflow_123",   # Optional correlation
    metadata={
        "repository": "my-repo",
        "author": "developer1",
        "reviewers": ["reviewer1", "reviewer2"]
    }
)
```

### Smart Routing Features

- **User Preferences**: Respect individual notification preferences
- **Working Hours**: Filter notifications based on working hours
- **Rate Limiting**: Prevent notification spam
- **Priority Filtering**: Route urgent notifications appropriately
- **Content Filtering**: Filter based on keywords and event types

### Example: Issue Assignment Notification

```python
# Enhanced notification with smart routing
await app.slack.send_enhanced_notification(
    event_data={
        "title": "Issue Assigned: Fix login bug",
        "message": "High priority bug in authentication system",
        "url": "https://linear.app/issue/AUTH-123",
        "assignee": "developer1",
        "priority": "high"
    },
    context=NotificationContext(
        event_type="issue_assigned",
        priority="high",
        source_platform="linear",
        metadata={
            "repository": "auth-service",
            "assignee": "developer1",
            "project": "Authentication"
        }
    )
)
```

## Interactive Workflows

### Approval Workflows

```python
# Create approval workflow
workflow_result = await app.slack.coordinate_workflow(
    workflow_type="approval",
    data={
        "workflow_id": "deploy_prod_v2.1.0",
        "title": "Production Deployment Approval",
        "description": "Deploy version 2.1.0 to production environment",
        "approvers": ["tech_lead", "product_manager"],
        "deadline": datetime.now() + timedelta(hours=4),
        "notification_channels": ["#deployments"],
        "escalation_rules": {
            "delay_hours": 2,
            "escalate_to": ["engineering_manager"]
        }
    }
)
```

### Code Review Workflows

```python
# Coordinate code review
review_workflow = await app.slack.coordinate_workflow(
    workflow_type="review",
    data={
        "pr_title": "Add user authentication",
        "pr_url": "https://github.com/org/repo/pull/123",
        "author": "developer1",
        "reviewers": ["senior_dev1", "senior_dev2"],
        "notification_channels": ["#code-reviews"]
    }
)
```

### Task Assignment Workflows

```python
# Coordinate task assignment
task_workflow = await app.slack.coordinate_workflow(
    workflow_type="task_assignment",
    data={
        "task_title": "Implement OAuth integration",
        "description": "Add OAuth 2.0 support for third-party login",
        "assignee": "developer2",
        "priority": "high",
        "deadline": datetime.now() + timedelta(days=3)
    }
)
```

## Cross-Platform Integration

### Event Correlation

The system automatically correlates events across platforms:

```python
# Linear issue → GitHub PR → Slack notification
linear_event = {
    "type": "Issue",
    "data": {
        "id": "AUTH-123",
        "title": "Fix login bug",
        "assignee": {"id": "developer1"}
    }
}

# Process Linear event
result = await coordinator.process_platform_event(
    platform=PlatformType.LINEAR,
    event_data=linear_event
)

# Later, when GitHub PR is created...
github_event = {
    "action": "opened",
    "pull_request": {
        "title": "Fix login bug (AUTH-123)",
        "body": "Fixes Linear issue AUTH-123",
        "user": {"login": "developer1"}
    }
}

# System automatically correlates events
result = await coordinator.process_platform_event(
    platform=PlatformType.GITHUB,
    event_data=github_event
)
```

### Workflow Chains

```python
# Create workflow chain across platforms
correlation_id = await coordinator.create_workflow_chain(
    workflow_type="issue_to_deployment",
    initial_event=linear_event,
    workflow_steps=[
        "issue_created",
        "pr_opened", 
        "pr_reviewed",
        "pr_merged",
        "deployment_started",
        "deployment_completed"
    ]
)

# Update workflow steps as events occur
await coordinator.update_workflow_step(
    correlation_id=correlation_id,
    step="pr_opened",
    event=github_pr_event
)
```

## Team Analytics

### Communication Analysis

```python
# Analyze team communication patterns
analysis = await app.slack.enhanced_client.analyze_team_communication("week")

print(f"Total messages: {analysis['team_metrics']['total_messages']}")
print(f"Active participants: {analysis['team_metrics']['unique_participants']}")
print(f"Average response time: {analysis['team_metrics']['avg_response_time_minutes']} minutes")

# Review insights
for insight in analysis['insights']:
    print(f"Insight: {insight['title']} - {insight['severity']}")
    for recommendation in insight['recommendations']:
        print(f"  - {recommendation}")
```

### Productivity Insights

```python
# Generate productivity insights
insights = await app.slack.enhanced_client.analytics_engine.generate_productivity_insights("month")

print(f"Workflow completion rate: {insights['workflow_analysis']['completion_rate']:.1%}")
print(f"Average workflow duration: {insights['workflow_analysis']['avg_duration_hours']:.1f} hours")

# Review bottlenecks
for bottleneck in insights['bottlenecks']:
    print(f"Bottleneck: {bottleneck['bottleneck_step']} - {bottleneck['delay_hours']:.1f} hours")
```

### Team Health Report

```python
# Generate comprehensive team health report
health_report = await app.slack.enhanced_client.analytics_engine.generate_team_health_report()

print(f"Overall health score: {health_report['health_metrics']['overall_score']:.1%}")
print(f"Communication health: {health_report['health_metrics']['communication_health']['status']}")
print(f"Workflow health: {health_report['health_metrics']['workflow_health']['status']}")

# Review recommendations
for recommendation in health_report['recommendations']:
    print(f"Recommendation: {recommendation}")
```

## Block Kit Components

### Rich Notifications

```python
from contexten.extensions.slack.block_kit_builder import BlockKitBuilder

builder = BlockKitBuilder()

# Build issue notification blocks
blocks = await builder.build_notification_blocks(
    event_data={
        "title": "Critical Bug Report",
        "url": "https://linear.app/issue/BUG-456",
        "assignee": "developer1",
        "priority": "urgent"
    },
    context=NotificationContext(
        event_type="issue_assigned",
        priority="urgent"
    )
)

# Send with rich blocks
await app.slack.client.chat_postMessage(
    channel="#urgent-bugs",
    blocks=blocks
)
```

### Interactive Modals

```python
# Build approval modal
approval_blocks = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Deployment Approval Required*"}
    },
    {
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": "*Environment:*\nProduction"},
            {"type": "mrkdwn", "text": "*Version:*\nv2.1.0"}
        ]
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Approve"},
                "style": "primary",
                "action_id": "approve_deployment"
            },
            {
                "type": "button", 
                "text": {"type": "plain_text", "text": "Reject"},
                "style": "danger",
                "action_id": "reject_deployment"
            }
        ]
    }
]

modal_view = builder.build_modal_view(
    title="Deployment Approval",
    blocks=approval_blocks,
    callback_id="deployment_approval_modal"
)
```

## Performance Optimization

### Notification Performance

- **Target**: <1 second notification delivery
- **Techniques**: 
  - Async processing
  - Intelligent routing
  - Notification aggregation
  - Caching user preferences

### Interactive Response Performance

- **Target**: <500ms interactive component responses
- **Techniques**:
  - Optimized event handling
  - Efficient state management
  - Minimal API calls
  - Smart caching

### Monitoring

```python
# Performance monitoring is built-in
result = await app.slack.send_enhanced_notification(event_data, context)

print(f"Notification delivery time: {result['duration_seconds']:.3f}s")
if result['duration_seconds'] > 1.0:
    print("⚠️ Performance target exceeded!")
```

## Error Handling

### Graceful Degradation

```python
# Enhanced features gracefully fall back to basic functionality
if app.slack.enhanced_client:
    # Use enhanced features
    result = await app.slack.send_enhanced_notification(event_data, context)
else:
    # Fall back to basic notification
    app.slack.client.chat_postMessage(
        channel=context.target_channels[0],
        text=event_data["message"]
    )
```

### Error Recovery

```python
try:
    result = await app.slack.coordinate_workflow(workflow_type, data)
except Exception as e:
    logger.exception(f"Workflow coordination failed: {e}")
    # Send basic notification as fallback
    app.slack.client.chat_postMessage(
        channel="#alerts",
        text=f"⚠️ Workflow coordination failed: {e}"
    )
```

## Migration Guide

### From Basic to Enhanced

1. **No Code Changes Required**: Existing code continues to work
2. **Optional Environment Variables**: Add enhanced feature flags
3. **Gradual Adoption**: Enable features incrementally
4. **Feature Flags**: Control rollout with environment variables

### Example Migration

```python
# Before (still works)
@app.slack.event("app_mention")
async def handle_mention(event):
    app.slack.client.chat_postMessage(
        channel=event.channel,
        text="Hello!"
    )

# After (enhanced, optional)
@app.slack.event("app_mention")
async def handle_mention(event):
    if app.slack.enhanced_client:
        # Use enhanced notification
        context = NotificationContext(
            event_type="app_mention",
            target_channels=[event.channel],
            thread_ts=event.ts
        )
        await app.slack.send_enhanced_notification(
            {"message": "Hello with enhanced features!"}, 
            context
        )
    else:
        # Fall back to basic
        app.slack.client.chat_postMessage(
            channel=event.channel,
            text="Hello!"
        )
```

## Best Practices

### 1. Use Intelligent Routing

```python
# Good: Use context for smart routing
context = NotificationContext(
    event_type="pr_review_requested",
    priority="normal",
    metadata={"repository": "critical-service"}
)

# Avoid: Manual channel specification
# target_channels=["#general"]  # Too broad
```

### 2. Leverage Analytics

```python
# Good: Regular health monitoring
health_report = await app.slack.enhanced_client.analytics_engine.generate_team_health_report()
if health_report['health_metrics']['overall_score'] < 0.7:
    # Take action to improve team health
    pass
```

### 3. Design for Performance

```python
# Good: Batch notifications
notifications = []
for event in events:
    notifications.append(create_notification(event))

# Send in batch
results = await asyncio.gather(*[
    app.slack.send_enhanced_notification(notif['data'], notif['context'])
    for notif in notifications
])
```

### 4. Handle Errors Gracefully

```python
# Good: Graceful degradation
try:
    result = await app.slack.coordinate_workflow(workflow_type, data)
except Exception as e:
    logger.exception(f"Enhanced workflow failed: {e}")
    # Fall back to basic notification
    await send_basic_notification(data)
```

## Troubleshooting

### Common Issues

1. **Enhanced Client Not Initialized**
   ```
   WARNING: Enhanced Slack client not initialized - missing required environment variables
   ```
   **Solution**: Ensure `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are set

2. **Performance Targets Not Met**
   ```
   WARNING: Notification delivery took 1.234s, exceeding 1.000s target
   ```
   **Solution**: Check network latency, enable notification aggregation

3. **Interactive Components Not Working**
   ```
   WARNING: Interactive component received but enhanced client not available
   ```
   **Solution**: Set `SLACK_ENABLE_WORKFLOWS=true` and ensure app token is configured

### Debug Mode

```python
import logging
logging.getLogger("contexten.extensions.slack").setLevel(logging.DEBUG)

# Enhanced debug information will be logged
```

## API Reference

See the individual component documentation:

- [Enhanced Client API](./enhanced_client_api.md)
- [Notification Router API](./notification_router_api.md)
- [Block Kit Builder API](./block_kit_builder_api.md)
- [Analytics Engine API](./analytics_engine_api.md)
- [Cross-Platform Coordinator API](./cross_platform_coordinator_api.md)

## Examples

See the [examples directory](../../examples/enhanced_slack_workflows/) for complete working examples:

- Basic enhanced notifications
- Interactive approval workflows
- Cross-platform event correlation
- Team analytics dashboards
- Custom Block Kit components

