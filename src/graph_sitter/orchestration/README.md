# Multi-Platform Orchestration & Workflow Management

A comprehensive orchestration system for integrating GitHub, Linear, Slack, and other platforms with advanced workflow management capabilities.

## 🎯 Overview

This system provides:

- **Multi-platform orchestration engine** - Coordinate workflows across GitHub, Linear, Slack
- **Advanced workflow management** - Define, execute, and monitor complex workflows
- **Cross-platform event correlation** - Identify relationships between events across platforms
- **Automated trigger system** - Execute workflows based on events and conditions
- **Real-time monitoring** - Track system health and performance

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Multi-Platform Orchestrator                  │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Workflow Manager│ Event Correlator│ Automated Trigger System│
├─────────────────┼─────────────────┼─────────────────────────┤
│ • Execution     │ • Cross-platform│ • Event-based triggers  │
│ • Scheduling    │   correlation   │ • Condition evaluation  │
│ • Dependencies  │ • Pattern       │ • Action execution      │
│ • Monitoring    │   analysis      │ • Rate limiting         │
└─────────────────┴─────────────────┴─────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐         ┌─────▼─────┐         ┌─────▼─────┐
   │ GitHub  │         │  Linear   │         │  Slack    │
   │Integration│       │Integration│         │Integration│
   └─────────┘         └───────────┘         └───────────┘
```

## 🚀 Quick Start

### Installation

```python
from graph_sitter.orchestration import MultiPlatformOrchestrator, OrchestrationConfig

# Create configuration
config = OrchestrationConfig(
    github_enabled=True,
    linear_enabled=True,
    slack_enabled=True
)

# Initialize orchestrator
orchestrator = MultiPlatformOrchestrator(config)
```

### Basic Usage

```python
import asyncio

async def main():
    # Start the orchestrator
    await orchestrator.start()
    
    # Execute a workflow
    execution = await orchestrator.execute_workflow(
        workflow_id="pr_review",
        context={"pr_number": 123, "repository": "owner/repo"}
    )
    
    # Check status
    status = await orchestrator.get_workflow_status(execution.id)
    print(f"Workflow status: {status['status']}")
    
    # Stop the orchestrator
    await orchestrator.stop()

asyncio.run(main())
```

### CLI Usage

```bash
# Start the orchestration system
python -m graph_sitter.orchestration.cli start

# Create a workflow
python -m graph_sitter.orchestration.cli workflow create \
    --name "PR Review" \
    --description "Automated PR review workflow"

# List workflows
python -m graph_sitter.orchestration.cli workflow list

# Execute a workflow
python -m graph_sitter.orchestration.cli workflow execute pr_review \
    --context '{"pr_number": 123}'

# Check system status
python -m graph_sitter.orchestration.cli status overview
```

## 📋 Workflow Management

### Creating Workflows

```python
from graph_sitter.orchestration.workflow import Workflow, WorkflowStep

# Create a workflow
workflow = Workflow(
    id="github_pr_review",
    name="GitHub PR Review",
    description="Automated code review workflow"
)

# Add steps
fetch_pr = WorkflowStep(
    id="fetch_pr",
    name="Fetch PR Details",
    action="github.get_pr",
    parameters={
        "owner": "${repository.owner}",
        "repo": "${repository.name}",
        "pr_number": "${pr_number}"
    }
)

analyze_code = WorkflowStep(
    id="analyze_code",
    name="Analyze Code",
    action="codegen.analyze_pr",
    dependencies=["fetch_pr"],
    parameters={
        "pr_data": "${fetch_pr.result}"
    }
)

workflow.add_step(fetch_pr)
workflow.add_step(analyze_code)

# Register workflow
orchestrator.workflow_manager.register_workflow(workflow)
```

### Workflow Features

- **Dependencies** - Define step execution order
- **Conditional execution** - Skip steps based on conditions
- **Retries** - Automatic retry on failure
- **Timeouts** - Prevent hanging steps
- **Variable substitution** - Use results from previous steps
- **Parallel execution** - Run independent steps concurrently

## 🎯 Trigger System

### Creating Triggers

```python
from graph_sitter.orchestration.triggers import Trigger, TriggerCondition, TriggerAction

# Create a trigger
trigger = Trigger(
    id="pr_opened_trigger",
    name="PR Opened Trigger",
    description="Trigger review when PR is opened",
    trigger_type=TriggerType.EVENT,
    event_types=["github.pr.opened"],
    platforms=["github"]
)

# Add conditions
trigger.add_condition(
    TriggerCondition(
        field="event.data.draft",
        operator=ConditionOperator.EQUALS,
        value=False
    )
)

# Add actions
trigger.add_action(
    TriggerAction(
        action_type="workflow",
        parameters={
            "workflow_id": "github_pr_review",
            "pr_number": "${event.data.number}"
        }
    )
)

# Register trigger
orchestrator.trigger_system.register_trigger(trigger)
```

### Trigger Types

- **Event triggers** - Respond to platform events
- **Schedule triggers** - Execute on cron schedules
- **Condition triggers** - Execute when conditions are met
- **Manual triggers** - Execute on demand

## 🔗 Event Correlation

The system automatically correlates events across platforms:

```python
# Events are automatically correlated based on:
# - Time proximity
# - Shared attributes (user, repository, issue ID)
# - Custom correlation rules

# Example: GitHub PR and Linear issue correlation
github_event = {
    "type": "pull_request.opened",
    "repository": "owner/repo",
    "user": "developer",
    "pr_number": 123
}

linear_event = {
    "type": "issue.updated", 
    "user": "developer",
    "issue_id": "DEV-456"
}

# System identifies correlation and can trigger workflows
```

## 🔌 Platform Integrations

### GitHub Integration

```python
# GitHub operations
await github.get_pr("owner", "repo", 123)
await github.create_review("owner", "repo", 123, "LGTM!")
await github.add_comment("owner", "repo", 123, "Automated review complete")
```

### Linear Integration

```python
# Linear operations
await linear.create_issue("Bug fix needed", "Description", team_id="team_123")
await linear.update_issue("issue_id", state_id="completed")
await linear.add_comment("issue_id", "Fixed in PR #123")
```

### Slack Integration

```python
# Slack operations
await slack.send_message("#dev", "PR review completed!")
await slack.add_reaction("channel", "timestamp", "✅")
```

## 📊 Monitoring & Metrics

### System Metrics

```python
# Get orchestration metrics
metrics = await orchestrator.get_orchestration_metrics()

print(f"Active workflows: {metrics['active_workflows']}")
print(f"Total correlations: {metrics['event_correlator']['total_correlations']}")
print(f"Trigger success rate: {metrics['trigger_system']['success_rate']}")
```

### Health Checks

```python
# Check system health
for platform, integration in orchestrator.integrations.items():
    health = await integration.health_check()
    print(f"{platform}: {'✅' if health['healthy'] else '❌'}")
```

## 🛠️ Configuration

### Environment Variables

```bash
# GitHub
GITHUB_API_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Linear
LINEAR_API_TOKEN=lin_api_xxxxxxxxxxxx
LINEAR_TEAM_ID=team_xxxxxxxxxxxx

# Slack
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
SLACK_APP_TOKEN=xapp-xxxxxxxxxxxx
SLACK_SIGNING_SECRET=xxxxxxxxxxxx
```

### Configuration File

```json
{
  "github_enabled": true,
  "linear_enabled": true,
  "slack_enabled": true,
  "max_concurrent_workflows": 10,
  "event_correlation_window": 300,
  "auto_retry_failed_workflows": true,
  "max_retry_attempts": 3
}
```

## 📝 Examples

See `examples/sample_workflows.py` for complete workflow examples:

- **PR Review Workflow** - Comprehensive code review automation
- **Issue Sync Workflow** - GitHub to Linear issue synchronization  
- **Deployment Workflow** - Multi-platform deployment notifications

## 🔧 Advanced Features

### Custom Actions

```python
# Register custom actions
async def custom_analysis(code_data, analysis_type):
    # Your custom logic here
    return analysis_result

orchestrator.workflow_manager.executor.register_action(
    "custom.analysis", 
    custom_analysis
)
```

### Event Handlers

```python
# Register event handlers
async def handle_pr_event(event, correlations):
    print(f"PR event: {event['type']}")
    print(f"Correlations: {len(correlations)}")

orchestrator.register_event_handler("github", handle_pr_event)
```

### Correlation Rules

```python
from graph_sitter.orchestration.events import CorrelationRule

# Custom correlation rule
rule = CorrelationRule(
    id="custom_correlation",
    name="Custom Event Correlation",
    event_types=[EventType.GITHUB_PR_OPENED, EventType.LINEAR_ISSUE_CREATED],
    time_window=timedelta(hours=1),
    required_attributes=["user_id"],
    base_confidence=0.8
)

orchestrator.event_correlator.add_correlation_rule(rule)
```

## 🧪 Testing

```python
# Simulate events for testing
await orchestrator.handle_platform_event("github", {
    "event_type": "pull_request.opened",
    "data": {
        "number": 123,
        "title": "Test PR",
        "repository": {"owner": "test", "name": "repo"}
    }
})
```

## 📚 API Reference

### Core Classes

- `MultiPlatformOrchestrator` - Main orchestration engine
- `WorkflowManager` - Workflow lifecycle management
- `EventCorrelator` - Cross-platform event correlation
- `AutomatedTriggerSystem` - Trigger management and execution

### Workflow Classes

- `Workflow` - Workflow definition
- `WorkflowStep` - Individual workflow step
- `WorkflowExecution` - Runtime execution instance

### Trigger Classes

- `Trigger` - Trigger definition
- `TriggerCondition` - Condition for trigger evaluation
- `TriggerAction` - Action to execute when triggered

### Integration Classes

- `GitHubIntegration` - GitHub API integration
- `LinearIntegration` - Linear API integration  
- `SlackIntegration` - Slack API integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

