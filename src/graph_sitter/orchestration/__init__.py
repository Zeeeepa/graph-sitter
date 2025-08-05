"""
Multi-Platform Orchestration & Workflow Management

A comprehensive orchestration system integrating GitHub, Linear, Slack with 
advanced workflow management, event correlation, and automated triggers.

## Quick Start

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

# Start the system
await orchestrator.start()

# Execute a workflow
execution = await orchestrator.execute_workflow(
    workflow_id="pr_review",
    context={"pr_number": 123}
)

# Stop the system
await orchestrator.stop()
```

## Components

- **MultiPlatformOrchestrator**: Main orchestration engine
- **WorkflowManager**: Workflow lifecycle management
- **EventCorrelator**: Cross-platform event correlation
- **AutomatedTriggerSystem**: Trigger management and execution
- **Platform Integrations**: GitHub, Linear, Slack clients

## Features

- Multi-platform workflow orchestration
- Cross-platform event correlation
- Automated workflow triggers
- Advanced scheduling and dependencies
- Real-time coordination and monitoring
- Integration with all system components
"""

from .engine.orchestrator import MultiPlatformOrchestrator, OrchestrationConfig, OrchestrationStatus
from .workflow.manager import WorkflowManager
from .workflow.models import Workflow, WorkflowStep, WorkflowExecution, WorkflowTemplate
from .events.correlator import EventCorrelator
from .events.models import Event, EventCorrelation, CorrelationRule
from .triggers.system import AutomatedTriggerSystem
from .triggers.models import Trigger, TriggerCondition, TriggerAction
from .integrations.github_client import GitHubIntegration
from .integrations.linear_client import LinearIntegration
from .integrations.slack_client import SlackIntegration

__version__ = "1.0.0"

__all__ = [
    # Core orchestration
    "MultiPlatformOrchestrator",
    "OrchestrationConfig", 
    "OrchestrationStatus",
    
    # Workflow management
    "WorkflowManager",
    "Workflow",
    "WorkflowStep",
    "WorkflowExecution",
    "WorkflowTemplate",
    
    # Event correlation
    "EventCorrelator",
    "Event",
    "EventCorrelation",
    "CorrelationRule",
    
    # Trigger system
    "AutomatedTriggerSystem",
    "Trigger",
    "TriggerCondition",
    "TriggerAction",
    
    # Platform integrations
    "GitHubIntegration",
    "LinearIntegration",
    "SlackIntegration",
]

