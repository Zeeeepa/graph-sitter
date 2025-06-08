# Flow Orchestration Extension

The Flow Orchestration Extension provides comprehensive workflow management and execution capabilities for the Contexten framework. It integrates multiple orchestration frameworks to provide flexible, scalable, and intelligent flow management.

## Features

### 🚀 **Multi-Framework Support**
- **ControlFlow**: Advanced agent orchestration with complex workflow patterns
- **Prefect**: Professional workflow monitoring and management
- **Strands**: Core agent functionality with MCP (Model Context Protocol) integration

### 🧠 **Intelligent Scheduling**
- Priority-based scheduling with multiple strategies
- Resource-aware scheduling and load balancing
- Dependency management with cycle detection
- Deadline-aware scheduling optimization

### 🔧 **Advanced Execution**
- Automatic retry and recovery mechanisms
- Resource management and throttling
- Detailed execution tracking and metrics
- Error handling with recovery strategies

### 📊 **Comprehensive Monitoring**
- Real-time flow status tracking
- Performance metrics and analytics
- Execution history and audit trails
- Resource usage monitoring

## Architecture

```
Flow Extension
├── FlowManager          # Central orchestration manager
├── FlowOrchestrator     # Unified orchestrator with priority queues
├── FlowExecutor         # Enhanced execution with retry/recovery
├── FlowScheduler        # Intelligent scheduling engine
├── controlflow/         # ControlFlow integration
├── prefect/            # Prefect integration
└── strands/            # Strands agents integration
```

## Quick Start

### Basic Usage

```python
from contexten.extensions.flow import FlowManager, FlowOrchestrator

# Initialize flow manager
flow_manager = FlowManager(
    agents=your_agents,
    enable_prefect=True,
    enable_controlflow=True
)

# Create and execute a simple flow
result = await flow_manager.create_flow(
    name="example_flow",
    workflow_def={
        "stages": [
            {
                "name": "data_processing",
                "tasks": [
                    {
                        "name": "fetch_data",
                        "required_tools": ["http_client"]
                    },
                    {
                        "name": "process_data", 
                        "required_tools": ["data_processor"]
                    }
                ]
            }
        ]
    }
)

# Execute the flow
execution_result = await flow_manager.execute_flow(result["flow_id"])
```

### Advanced Orchestration

```python
from contexten.extensions.flow import (
    FlowOrchestrator, 
    FlowPriority, 
    SchedulingStrategy
)

# Initialize orchestrator with advanced features
orchestrator = FlowOrchestrator(
    agents=your_agents,
    max_concurrent_flows=5,
    enable_monitoring=True
)

await orchestrator.start()

# Submit high-priority flow
result = await orchestrator.submit_flow(
    name="critical_task",
    workflow_def=workflow_definition,
    priority=FlowPriority.HIGH,
    framework="controlflow"
)

# Execute synchronously with timeout
sync_result = await orchestrator.execute_flow_sync(
    name="quick_task",
    workflow_def=simple_workflow,
    timeout=60.0
)
```

### Custom Scheduling

```python
from contexten.extensions.flow import FlowScheduler, SchedulingStrategy

# Initialize scheduler with custom strategy
scheduler = FlowScheduler(
    agents=your_agents,
    strategy=SchedulingStrategy.RESOURCE_AWARE,
    max_concurrent_flows=10,
    enable_load_balancing=True
)

await scheduler.start()

# Schedule flow with dependencies and deadline
result = await scheduler.schedule_flow(
    workflow=your_workflow,
    workflow_def=workflow_definition,
    priority=1,
    deadline=datetime.now() + timedelta(hours=2),
    dependencies=["prerequisite_flow_id"]
)
```

## Workflow Definition Format

Workflows are defined using a structured JSON format:

```json
{
  "id": "unique_workflow_id",
  "name": "My Workflow",
  "description": "Example workflow description",
  "stages": [
    {
      "name": "stage_1",
      "execution_mode": "sequential",
      "continue_on_task_failure": false,
      "tasks": [
        {
          "name": "task_1",
          "type": "data_processing",
          "required_tools": ["http_client", "json_parser"],
          "preferred_agent_type": "DataAgent",
          "complexity": 1,
          "parameters": {
            "url": "https://api.example.com/data",
            "format": "json"
          }
        }
      ]
    }
  ],
  "continue_on_failure": false,
  "monitoring_required": true,
  "complex_orchestration": false,
  "context": {
    "environment": "production",
    "timeout": 300
  }
}
```

## Scheduling Strategies

### FIFO (First In, First Out)
```python
scheduler = FlowScheduler(strategy=SchedulingStrategy.FIFO)
```
Executes flows in the order they were submitted.

### Priority-Based
```python
scheduler = FlowScheduler(strategy=SchedulingStrategy.PRIORITY)
```
Executes flows based on priority levels (lower number = higher priority).

### Resource-Aware
```python
scheduler = FlowScheduler(strategy=SchedulingStrategy.RESOURCE_AWARE)
```
Considers resource availability and agent capacity when scheduling.

### Load-Balanced
```python
scheduler = FlowScheduler(strategy=SchedulingStrategy.LOAD_BALANCED)
```
Distributes flows to balance load across available agents.

### Deadline-Aware
```python
scheduler = FlowScheduler(strategy=SchedulingStrategy.DEADLINE_AWARE)
```
Prioritizes flows based on deadlines and urgency.

## Error Handling and Recovery

The flow system includes comprehensive error handling:

### Automatic Retry
```python
executor = FlowExecutor(
    max_retries=3,
    retry_delay=1.0,  # Exponential backoff
    enable_recovery=True
)
```

### Recovery Strategies
- **Timeout Recovery**: Increases timeout for subsequent attempts
- **Agent Failure Recovery**: Rotates agents or reinitializes tools
- **Resource Recovery**: Performs garbage collection and resource cleanup
- **Network Recovery**: Implements longer delays for network issues

### Custom Recovery
```python
async def custom_recovery_strategy(context):
    # Custom recovery logic
    context.log("info", "Applying custom recovery")
    await asyncio.sleep(2.0)

executor.recovery_strategies["custom_error"] = custom_recovery_strategy
```

## Monitoring and Metrics

### Flow Status Tracking
```python
# Get flow status
status = await flow_manager.get_flow_status("flow_id")

# List all flows
flows = await flow_manager.list_flows(status_filter="running", limit=20)
```

### Orchestrator Metrics
```python
# Get orchestrator status
status = await orchestrator.get_orchestrator_status()
print(f"Active flows: {status['resource_usage']['active_flows']}")
print(f"Success rate: {status['resource_usage']['total_completed']}")
```

### Scheduler Analytics
```python
# Get scheduler status
status = scheduler.get_scheduler_status()
print(f"Queue size: {status['pending_flows']}")
print(f"System load: {status['system_load']:.1f}%")
```

## Integration with Contexten

The flow extension integrates seamlessly with the Contexten ecosystem:

### ContextenApp Integration
```python
from contexten import ContextenApp

app = ContextenApp(name="my-app")

# Flow manager is automatically available
flow_result = await app.flow_manager.create_flow(
    name="automated_task",
    workflow_def=workflow_definition
)
```

### Dashboard Integration
The flow system provides APIs for dashboard integration:
- Real-time flow status updates
- Performance metrics and analytics
- Flow creation and management interfaces
- Resource usage monitoring

### Event Integration
Flows can be triggered by various events:
- GitHub webhook events
- Linear issue updates
- Slack commands
- Scheduled triggers

## Best Practices

### 1. Workflow Design
- Keep stages focused and cohesive
- Use appropriate execution modes (sequential vs parallel)
- Define clear dependencies between flows
- Set realistic deadlines and priorities

### 2. Resource Management
- Monitor system load and adjust concurrency limits
- Use resource-aware scheduling for heavy workloads
- Implement proper cleanup in custom agents
- Consider agent capacity when designing workflows

### 3. Error Handling
- Enable automatic retry for transient failures
- Implement custom recovery strategies for specific error types
- Use appropriate timeout values
- Log detailed error information for debugging

### 4. Performance Optimization
- Use load balancing for distributed workloads
- Monitor execution metrics and optimize bottlenecks
- Cache frequently used resources
- Implement efficient agent selection algorithms

## Framework-Specific Features

### ControlFlow Integration
- Advanced orchestration patterns
- Complex workflow dependencies
- Agent coordination and communication
- Distributed execution capabilities

### Prefect Integration
- Professional workflow monitoring
- Detailed execution logs and metrics
- Flow versioning and deployment
- Integration with Prefect Cloud/Server

### Strands Integration
- MCP (Model Context Protocol) support
- Tool registry and management
- Event-driven execution
- Context-aware agent behavior

## Troubleshooting

### Common Issues

**Flow not executing:**
- Check agent availability and capacity
- Verify workflow definition format
- Ensure dependencies are satisfied
- Check system resource usage

**High failure rate:**
- Review error logs and recovery strategies
- Adjust retry settings and timeouts
- Verify agent tool compatibility
- Check network connectivity

**Poor performance:**
- Monitor system load and adjust concurrency
- Optimize workflow design and task granularity
- Use appropriate scheduling strategy
- Consider agent distribution and load balancing

### Debug Mode
```python
import logging
logging.getLogger('contexten.extensions.flow').setLevel(logging.DEBUG)
```

### Health Checks
```python
# Check orchestrator health
status = await orchestrator.get_orchestrator_status()
if status['status'] != 'running':
    await orchestrator.start()

# Check scheduler health  
scheduler_status = scheduler.get_scheduler_status()
if not scheduler_status['running']:
    await scheduler.start()
```

## Contributing

To contribute to the flow extension:

1. Follow the existing code patterns and architecture
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure compatibility with all supported frameworks
5. Test integration with the broader Contexten ecosystem

## License

This extension is part of the Contexten framework and follows the same licensing terms.

