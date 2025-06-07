# Codegen Package Overlay System

This overlay system enhances an existing `pip install codegen` package with contexten integration while preserving the original API.

## Overview

The overlay system modifies the installed codegen package to add enhanced functionality without changing the user experience. Users continue to use the exact same import statement:

```python
from codegen.agents.agent import Agent
```

## Features

- 🔄 **API Preservation**: 100% compatibility with original codegen API
- 🎯 **Package Enhancement**: Adds functionality to existing installation
- 🔗 **Contexten Integration**: Full ecosystem integration with events and metrics
- 📊 **Enhanced Monitoring**: Built-in metrics, health checks, and performance tracking
- 📡 **Event System**: Comprehensive event handling and callbacks
- 🛡️ **Safe Application**: Creates backups and validates before modification

## Installation & Usage

### Prerequisites

First, ensure you have the codegen package installed:

```bash
pip install codegen
```

### Apply the Overlay

```bash
python extensions/codegen/apply_overlay.py
```

This will:
1. Detect the installed codegen package
2. Validate its structure and permissions
3. Create contexten extension modules
4. Enhance the Agent class with new functionality
5. Preserve all original functionality

### Usage After Overlay

```python
# Use codegen exactly as before - API unchanged!
from codegen.agents.agent import Agent

agent = Agent(
    org_id="11",
    token="your_api_token_here",
    base_url="https://codegen-sh-rest-api.modal.run"
)

# Original functionality works unchanged
task = agent.run(prompt="Which github repos can you currently access?")
print(task.status)
task.refresh()

if task.status == "completed":
    print(task.result)

# New enhanced functionality available
metrics = agent.get_contexten_metrics()
print(f"Tasks run: {metrics['counters']['tasks_run']}")

# Add callbacks for monitoring
def on_task_event(data):
    print(f"Task event: {data}")

agent.add_callback(on_task_event)

# Enhanced run method with automatic monitoring
task = agent.run_enhanced("Your prompt here")
```

## What the Overlay Does

### 1. Creates Contexten Modules

The overlay adds these modules to the codegen package:

```
codegen/
├── contexten/
│   ├── __init__.py
│   ├── integration.py    # Main integration logic
│   ├── events.py         # Event system
│   ├── metrics.py        # Metrics collection
│   └── monitoring.py     # Health monitoring
```

### 2. Enhances Agent Class

The original `codegen/agents/agent.py` is enhanced with:

- **Contexten Integration**: Automatic event emission and metrics
- **Enhanced Methods**: New methods for monitoring and callbacks
- **Backward Compatibility**: All original methods preserved
- **Safe Enhancement**: Original file backed up as `.original`

### 3. Adds New Functionality

#### Event System
```python
from codegen.contexten.integration import register_event_handler

def on_agent_created(data):
    print(f"Agent created: {data}")

def on_task_finished(data):
    print(f"Task finished: {data}")

register_event_handler("agent_created", on_agent_created)
register_event_handler("task_finished", on_task_finished)
```

#### Metrics Collection
```python
from codegen.contexten.metrics import get_metrics

metrics = get_metrics()
print(f"Uptime: {metrics['uptime_seconds']}")
print(f"Counters: {metrics['counters']}")
```

#### Health Monitoring
```python
from codegen.contexten.monitoring import run_health_checks

health = run_health_checks()
print(f"Overall status: {health['overall_status']}")
```

## Enhanced Agent Methods

After applying the overlay, the Agent class gains new methods:

### `get_contexten_metrics()`
```python
agent = Agent(org_id="11", token="your_token")
metrics = agent.get_contexten_metrics()
print(metrics)
# Output: {'uptime_seconds': 123.45, 'counters': {'agents_created': 1, 'tasks_run': 0}, ...}
```

### `add_callback(callback)`
```python
def my_callback(event_data):
    print(f"Agent event: {event_data}")

agent.add_callback(my_callback)
```

### `run_enhanced(prompt, **kwargs)`
```python
# Enhanced run with automatic monitoring and event emission
task = agent.run_enhanced("Your prompt here")
```

## Event Types

The overlay emits these events automatically:

- `agent_created`: When a new agent is created
- `task_starting`: Before a task starts running
- `task_created`: When a new task is created
- `task_status_changed`: When task status changes
- `task_finished`: When a task completes
- `task_error`: When a task encounters an error
- `overlay_applied`: When the overlay is successfully applied

## File Structure After Overlay

```
codegen/                           # Original package
├── agents/
│   ├── agent.py                   # Enhanced with contexten integration
│   ├── agent.py.original          # Backup of original file
│   └── task.py                    # Unchanged
├── contexten/                     # New contexten modules
│   ├── __init__.py
│   ├── integration.py
│   ├── events.py
│   ├── metrics.py
│   └── monitoring.py
└── __init__.py                    # Unchanged
```

## Safety Features

### Backup Creation
- Original `agent.py` backed up as `agent.py.original`
- Overlay can be reversed by restoring backup

### Validation
- Checks package structure before modification
- Validates write permissions
- Ensures expected classes and methods exist

### Error Handling
- Comprehensive error reporting
- Safe failure modes
- Detailed logging

## Troubleshooting

### Common Issues

1. **"Package not writable"**
   - Run in a virtual environment
   - Use `sudo` (not recommended)
   - Install codegen in user directory: `pip install --user codegen`

2. **"Codegen package not found"**
   ```bash
   pip install codegen
   ```

3. **"Package structure invalid"**
   - Ensure you have the latest codegen version
   - Check that `from codegen.agents.agent import Agent` works

### Debug Information

```python
# Check if overlay was applied
try:
    from codegen.contexten.integration import get_metrics
    print("Overlay applied successfully")
    print(get_metrics())
except ImportError:
    print("Overlay not applied")
```

### Reverting the Overlay

To revert the overlay:

1. Find the codegen package location:
   ```python
   import codegen
   print(codegen.__file__)
   ```

2. Restore the original agent file:
   ```bash
   cd /path/to/codegen/agents/
   cp agent.py.original agent.py
   ```

3. Remove contexten directory:
   ```bash
   rm -rf /path/to/codegen/contexten/
   ```

## Advanced Usage

### Custom Event Handlers

```python
from codegen.contexten.integration import register_event_handler

def comprehensive_monitor(data):
    event_type = data.get('event_type', 'unknown')
    timestamp = data.get('timestamp', 0)
    
    if event_type == 'task_created':
        print(f"📝 Task created at {timestamp}")
    elif event_type == 'task_finished':
        duration = data.get('duration', 0)
        print(f"✅ Task completed in {duration:.2f}s")

register_event_handler("task_created", comprehensive_monitor)
register_event_handler("task_finished", comprehensive_monitor)
```

### Custom Metrics

```python
from codegen.contexten.metrics import increment, set_gauge

# Custom counters
increment("custom_operations")
increment("api_calls", 5)

# Custom gauges
set_gauge("current_load", 0.75)
set_gauge("active_connections", 42)
```

### Health Checks

```python
from codegen.contexten.monitoring import add_health_check

def check_api_connectivity():
    # Your health check logic
    return {"status": "ok", "response_time": 0.123}

add_health_check("api_connectivity", check_api_connectivity)
```

## Compatibility

- **Python**: 3.7+
- **Codegen Package**: Latest version from `pip install codegen`
- **Operating Systems**: Linux, macOS, Windows
- **Permissions**: Write access to Python site-packages

## Contributing

When contributing to this overlay system:

1. Preserve 100% API compatibility
2. Create comprehensive backups
3. Validate before modification
4. Include thorough error handling
5. Add comprehensive logging
6. Test with multiple codegen versions

## License

This overlay system follows the same license as the contexten project.

