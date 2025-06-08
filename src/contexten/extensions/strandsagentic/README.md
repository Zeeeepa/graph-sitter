# StrandsAgentic Extension

StrandsAgentic is a comprehensive agent orchestration extension for Contexten that integrates:
- [strands-agents/tools](https://github.com/strands-agents/tools) - Agent tools and capabilities
- [ControlFlow](https://github.com/zeeeepa/ControlFlow) - Agent orchestration framework
- [Prefect](https://github.com/zeeeepa/prefect) - Workflow monitoring and management

## Architecture

The extension consists of three main components:

1. **StrandsOrchestrator** (`orchestrator.py`)
   - Main orchestration component
   - Integrates ControlFlow with Prefect monitoring
   - Manages task distribution and execution

2. **StrandsAgent** (`agent.py`) 
   - Agent implementation using strands-agents tools
   - Integrates with strands-agents tool system
   - Handles task execution and tool management

3. **StrandsFlow** (`flow.py`)
   - Flow management component
   - Integrates ControlFlow with Prefect monitoring
   - Handles workflow execution and stage management

## Usage Example

```python
from contexten.extensions.strandsagentic import StrandsOrchestrator, StrandsAgent, StrandsFlow

# Configure and create orchestrator
orchestrator = StrandsOrchestrator(
    tools_config={
        "tool_paths": ["path/to/tools"],
        "default_timeout": 30
    },
    agent_config={
        "max_retries": 3,
        "timeout": 300
    },
    prefect_config={
        "monitoring_level": "detailed"
    }
)

# Create agents with specific tools
agent1 = StrandsAgent(
    tools=["tool1", "tool2"],
    context={"capability": "research"}
)

agent2 = StrandsAgent(
    tools=["tool3", "tool4"],
    context={"capability": "execution"}
)

# Create and execute a flow
flow = StrandsFlow(
    name="research_and_execute",
    agents=[agent1, agent2]
)

# Execute workflow
result = flow.execute({
    "stages": [
        {
            "name": "research",
            "tasks": [
                {
                    "action": "research_topic",
                    "required_tools": ["tool1"],
                    "parameters": {"topic": "AI agents"}
                }
            ]
        },
        {
            "name": "execute",
            "tasks": [
                {
                    "action": "implement_findings",
                    "required_tools": ["tool3", "tool4"],
                    "parameters": {"source": "research_results"}
                }
            ]
        }
    ]
})
```

## Features

1. **Integrated Monitoring**
   - Real-time task and workflow monitoring via Prefect
   - Performance metrics and execution tracking
   - Error handling and retry mechanisms

2. **Flexible Agent Configuration**
   - Dynamic tool assignment
   - Contextual execution
   - State management

3. **Workflow Management**
   - Multi-stage workflow execution
   - Parallel task processing
   - Dynamic agent selection

4. **Error Handling**
   - Comprehensive error capture
   - Retry mechanisms
   - Failure isolation

## Configuration

The extension supports various configuration options for each component:

### Orchestrator Configuration
```python
tools_config = {
    "tool_paths": ["path/to/tools"],
    "default_timeout": 30,
    "max_retries": 3
}

agent_config = {
    "max_retries": 3,
    "timeout": 300,
    "error_handling": "strict"
}

prefect_config = {
    "monitoring_level": "detailed",
    "log_level": "INFO",
    "metrics_enabled": True
}
```

### Agent Configuration
```python
agent_config = {
    "tools": ["tool1", "tool2"],
    "context": {
        "capability": "research",
        "priority": "high"
    },
    "timeout": 300
}
```

### Flow Configuration
```python
flow_config = {
    "name": "custom_flow",
    "continue_on_failure": False,
    "max_parallel_tasks": 5,
    "timeout": 3600
}
```

## Error Handling

The extension implements comprehensive error handling:

1. **Task Level**
   - Individual task failures are isolated
   - Retry mechanisms for transient failures
   - Detailed error reporting

2. **Stage Level**
   - Stage failure handling
   - Optional continue-on-failure behavior
   - Stage result aggregation

3. **Workflow Level**
   - Workflow-wide error policies
   - Cleanup on failure
   - Result aggregation and reporting

## Metrics and Monitoring

The extension provides detailed metrics through Prefect:

1. **Execution Metrics**
   - Task duration
   - Success/failure rates
   - Resource utilization

2. **Performance Metrics**
   - Agent utilization
   - Tool usage statistics
   - Workflow throughput

3. **Custom Metrics**
   - User-defined metrics
   - Business-specific KPIs
   - Integration metrics
