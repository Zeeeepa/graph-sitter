# Codegen Agent API Overlay Extension

A contexten extension that provides overlay functionality for the pip-installed `codegen` package, enhancing it with contexten ecosystem integration while preserving the original API.

## Overview

This extension applies an overlay to the existing `pip install codegen` package, adding contexten-specific functionality without changing the original API. Users can continue to use the standard codegen imports and methods while gaining enhanced features.

## Features

- 🔄 **API Preservation**: Maintains 100% compatibility with original codegen API
- 🎯 **Overlay Architecture**: Enhances existing package without modification
- 🔗 **Contexten Integration**: Seamless integration with contexten ecosystem
- 📊 **Enhanced Monitoring**: Built-in metrics, health checks, and performance tracking
- 📡 **Event System**: Comprehensive event handling and callbacks
- 🛡️ **Error Handling**: Enhanced error reporting and debugging
- ⚡ **Auto-Detection**: Automatically detects and validates codegen package

## Installation & Usage

### Prerequisites

First, ensure you have the codegen package installed:

```bash
pip install codegen
```

### Basic Usage

```python
# Apply the overlay
from contexten.extensions.codegen_agent_api import apply_codegen_overlay
overlay = apply_codegen_overlay()

# Now use codegen normally - API unchanged!
from codegen.agents.agent import Agent

agent = Agent(
    org_id="11",
    token="your_api_token_here",
    base_url="https://codegen-sh-rest-api.modal.run"
)

# The agent now has enhanced contexten integration
task = agent.run(prompt="Which github repos can you currently access?")

# Enhanced functionality available
print(task.status)
task.refresh()

# New: Wait for completion with enhanced monitoring
task.wait_for_completion(timeout=300)

if task.status == "completed":
    print(task.result)
```

### Command Line Application

You can also apply the overlay from the command line:

```bash
python extensions/codegen_agent_api/apply.py
```

This will:
1. Detect the installed codegen package
2. Validate its structure
3. Apply the contexten overlay
4. Provide status information

## Enhanced Features

### Event Handling

Register event handlers to monitor codegen operations:

```python
from contexten.extensions.codegen_agent_api import register_event_handler

def on_agent_created(data):
    print(f"Agent created for org {data['org_id']}")

def on_task_status_changed(data):
    print(f"Task {data['task_id']}: {data['old_status']} -> {data['new_status']}")

def on_task_finished(data):
    print(f"Task {data['task_id']} finished in {data['duration']:.2f}s")

# Register event handlers
register_event_handler("agent_created", on_agent_created)
register_event_handler("task_status_changed", on_task_status_changed)
register_event_handler("task_finished", on_task_finished)

# Now use codegen normally - events will be emitted
agent = Agent(org_id="11", token="your_token")
task = agent.run("Your prompt here")
```

### Available Events

- `agent_created`: When a new agent is created
- `task_starting`: Before a task starts running
- `task_created`: When a new task is created
- `task_status_changed`: When task status changes
- `task_finished`: When a task completes (success/failure)
- `task_timeout`: When a task times out
- `task_error`: When a task encounters an error
- `overlay_applied`: When the overlay is successfully applied

### Enhanced Agent Methods

The overlay adds new methods to agents while preserving all original functionality:

```python
# Original methods work unchanged
agent = Agent(org_id="11", token="your_token")
task = agent.run("Your prompt")
status = agent.get_status()

# New enhanced methods
metrics = agent.get_integration_metrics()
print(f"Agents created: {metrics['agents_created']}")
print(f"Tasks run: {metrics['tasks_run']}")
print(f"Uptime: {metrics['uptime_seconds']:.2f}s")

# Add task callbacks
def on_status_change(old_status, new_status):
    print(f"Status changed: {old_status} -> {new_status}")

agent.add_task_callback(on_status_change)
```

### Enhanced Task Methods

Tasks also gain new functionality:

```python
task = agent.run("Your prompt")

# Original methods work unchanged
task.refresh()
print(task.status)
print(task.result)

# New enhanced methods
task.wait_for_completion(timeout=300, poll_interval=5)

# Add status change callbacks
def on_status_change(old_status, new_status):
    print(f"Task status: {old_status} -> {new_status}")

task.add_status_callback(on_status_change)
```

### Metrics and Monitoring

Get comprehensive metrics about overlay usage:

```python
from contexten.extensions.codegen_agent_api import get_overlay_metrics

metrics = get_overlay_metrics()
print(f"Overlay applied: {metrics['applied']}")
print(f"Package version: {metrics['package_info']['version']}")
print(f"Agents created: {metrics['integration_metrics']['agents_created']}")
print(f"Tasks run: {metrics['integration_metrics']['tasks_run']}")
print(f"Errors: {metrics['integration_metrics']['errors']}")
```

## Architecture

### Overlay Pattern

The extension uses a non-invasive overlay pattern:

1. **Detection**: Automatically detects the installed codegen package
2. **Validation**: Ensures the package has the expected structure
3. **Wrapping**: Wraps the original classes with enhanced versions
4. **Replacement**: Replaces the original classes in the module namespace
5. **Preservation**: All original functionality remains unchanged

### Class Hierarchy

```
Original codegen.agents.agent.Agent
    ↓ (wrapped by)
EnhancedAgentWrapper
    ↓ (creates)
EnhancedAgent
    ↓ (delegates to original + adds features)

Original codegen.agents.task.AgentTask  
    ↓ (wrapped by)
EnhancedAgentTask
    ↓ (delegates to original + adds features)
```

### Integration Flow

```
User Code:
from codegen.agents.agent import Agent  # Gets EnhancedAgentWrapper
agent = Agent(...)                      # Creates EnhancedAgent
task = agent.run(...)                   # Creates EnhancedAgentTask

Enhanced Features:
- Event emission
- Metrics tracking  
- Callback support
- Enhanced monitoring
- Contexten integration
```

## Error Handling

The overlay includes comprehensive error handling:

```python
from contexten.extensions.codegen_agent_api import CodegenOverlayError

try:
    overlay = apply_codegen_overlay()
except CodegenOverlayError as e:
    print(f"Overlay failed: {e}")
    # Handle missing or invalid codegen package
```

Common error scenarios:
- **Package Not Found**: `pip install codegen` not run
- **Invalid Structure**: Codegen package missing expected modules
- **Version Incompatibility**: Codegen package structure changed

## Advanced Usage

### Manual Overlay Control

```python
from contexten.extensions.codegen_agent_api import CodegenOverlayApplicator

# Create overlay applicator
applicator = CodegenOverlayApplicator()

# Manual detection and validation
applicator.detect_and_validate()

# Get package info
package_info = applicator.package_info
print(f"Codegen version: {package_info['version']}")

# Apply overlay
applicator.apply_overlay()

# Get integration instance
integration = applicator.get_integration()

# Register custom event handlers
integration.register_event_handler("custom_event", my_handler)
```

### Custom Event Handlers

```python
def comprehensive_task_monitor(data):
    """Comprehensive task monitoring handler."""
    event_type = data.get('event_type', 'unknown')
    
    if event_type == 'task_created':
        print(f"📝 New task: {data['task_id']}")
    elif event_type == 'task_status_changed':
        print(f"🔄 Task {data['task_id']}: {data['old_status']} → {data['new_status']}")
    elif event_type == 'task_finished':
        duration = data['duration']
        print(f"✅ Task {data['task_id']} completed in {duration:.2f}s")
    elif event_type == 'task_error':
        print(f"❌ Task error: {data['error']}")

# Register for multiple events
events = ['task_created', 'task_status_changed', 'task_finished', 'task_error']
for event in events:
    register_event_handler(event, comprehensive_task_monitor)
```

### Integration with Contexten Ecosystem

```python
# Example: Integration with other contexten extensions
from contexten.extensions.codegen_agent_api import apply_codegen_overlay

# Apply overlay
overlay = apply_codegen_overlay()
integration = overlay.get_integration()

# Connect to other contexten components
def forward_to_contexten_events(data):
    # Forward codegen events to broader contexten event system
    contexten_event_bus.emit('codegen_event', data)

integration.register_event_handler('*', forward_to_contexten_events)
```

## Troubleshooting

### Common Issues

1. **"Codegen package not found"**
   ```bash
   pip install codegen
   ```

2. **"Package structure invalid"**
   - Ensure you have the latest codegen version
   - Check that `from codegen.agents.agent import Agent` works

3. **"Overlay already applied"**
   - This is normal - overlay can only be applied once per session
   - Restart Python session to reapply

### Debug Information

```python
from contexten.extensions.codegen_agent_api import get_overlay_instance

overlay = get_overlay_instance()
if overlay:
    status = overlay.get_status()
    print("Overlay Status:")
    print(f"  Applied: {status['applied']}")
    print(f"  Package Version: {status['package_info']['version']}")
    print(f"  Package Location: {status['package_info']['location']}")
    print(f"  Metrics: {status['integration_metrics']}")
else:
    print("Overlay not applied")
```

### Logging

Enable debug logging to see overlay operations:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now apply overlay with debug output
from contexten.extensions.codegen_agent_api import apply_codegen_overlay
overlay = apply_codegen_overlay()
```

## API Reference

### Main Functions

- `apply_codegen_overlay()` - Apply the overlay to codegen package
- `get_overlay_instance()` - Get current overlay instance
- `register_event_handler(event_type, handler)` - Register event handler
- `get_overlay_metrics()` - Get overlay metrics and status

### Classes

- `CodegenOverlayApplicator` - Main overlay application class
- `ContextenIntegration` - Contexten ecosystem integration
- `EnhancedAgent` - Enhanced agent wrapper
- `EnhancedAgentTask` - Enhanced task wrapper

### Events

- `agent_created` - New agent created
- `task_starting` - Task about to start
- `task_created` - New task created
- `task_status_changed` - Task status changed
- `task_finished` - Task completed
- `task_timeout` - Task timed out
- `task_error` - Task error occurred
- `overlay_applied` - Overlay successfully applied

## Compatibility

- **Python**: 3.7+
- **Codegen Package**: Latest version from `pip install codegen`
- **Contexten**: 1.0.0+

## Contributing

This extension follows contexten development guidelines:

1. Preserve original API compatibility
2. Use non-invasive overlay patterns
3. Provide comprehensive error handling
4. Include thorough documentation
5. Add comprehensive event coverage

## License

This extension follows the same license as the contexten project.

