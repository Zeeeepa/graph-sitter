# Codegen Agent API Extension

A comprehensive Codegen integration extension for the Contexten ecosystem that provides overlay functionality to work seamlessly with `pip install codegen` packages while maintaining fallback capabilities.

## Features

- 🔄 **Overlay Functionality**: Automatically detects and uses `pip install codegen` packages with local fallback
- 🤖 **Agent Interface**: Full-featured Agent class for programmatic interaction with Codegen SWE agents
- 🎯 **CodebaseAI Interface**: Direct function call interface similar to codebase.ai
- 🔗 **Contexten Integration**: Seamless integration with the broader contexten ecosystem
- 📡 **Webhook Support**: Comprehensive webhook processing and event handling
- 📊 **Monitoring**: Built-in metrics, health checks, and performance monitoring
- ⚙️ **Configuration**: Flexible configuration management with multiple sources
- 🛡️ **Error Handling**: Robust error handling with detailed exception types

## Quick Start

### Basic Usage

```python
from contexten.extensions.codegen_agent_api import create_codegen_extension

# Create extension instance
extension = create_codegen_extension(
    org_id="your_org_id",
    token="your_api_token"
)

# Create an agent
agent = extension.create_agent()

# Run a task
task = agent.run("Fix the bug in the login function")
task.wait_for_completion()
print(task.result)
```

### Direct Agent Creation

```python
from contexten.extensions.codegen_agent_api import create_agent_with_overlay

# Create agent directly with overlay functionality
agent = create_agent_with_overlay(
    org_id="your_org_id",
    token="your_api_token"
)

# Use the agent
task = agent.run("Improve the performance of this function", context={"file": "app.py"})
```

### CodebaseAI Interface

```python
from contexten.extensions.codegen_agent_api import create_codebase_ai_with_overlay

# Create CodebaseAI instance
codebase_ai = create_codebase_ai_with_overlay(
    org_id="your_org_id", 
    token="your_api_token"
)

# Use direct function calls
result = codebase_ai(
    "Improve this function's implementation",
    target={"source": "def slow_function(): ..."},
    context={"performance": "critical"}
)

# Or use convenience methods
improved_code = codebase_ai.improve_function(function_code)
documentation = codebase_ai.generate_docs(class_code, doc_type="comprehensive")
```

## Overlay Functionality

The extension automatically detects and uses `pip install codegen` packages while providing fallback to local implementations:

### Overlay Strategies

- **`pip_first`** (default): Use pip package if available, fallback to local
- **`local_first`**: Use local implementation first, fallback to pip
- **`pip_only`**: Only use pip package (fails if not available)
- **`local_only`**: Only use local implementation

### Configuration

```python
from contexten.extensions.codegen_agent_api import CodegenAgentAPIConfig

config = CodegenAgentAPIConfig(
    org_id="your_org_id",
    token="your_api_token",
    overlay_priority="pip_first",  # Overlay strategy
    enable_overlay=True,           # Enable overlay functionality
    fallback_to_local=True         # Allow fallback to local implementation
)

extension = CodegenAgentAPI(config)
```

### Environment Variables

```bash
export CODEGEN_ORG_ID="your_org_id"
export CODEGEN_TOKEN="your_api_token"
export CODEGEN_OVERLAY_PRIORITY="pip_first"
export CODEGEN_ENABLE_OVERLAY="true"
export CODEGEN_FALLBACK_TO_LOCAL="true"
```

## Configuration Management

### Multiple Configuration Sources

The extension supports configuration from multiple sources with priority order:

1. Explicit parameters
2. Configuration file
3. Environment variables
4. Default values

```python
from contexten.extensions.codegen_agent_api import get_codegen_config

# From environment variables
config = get_codegen_config()

# From file
config = get_codegen_config(config_file="config.json")

# With explicit overrides
config = get_codegen_config(
    config_file="config.json",
    org_id="override_org_id",
    timeout=60
)
```

### Configuration File

Create a configuration template:

```python
from contexten.extensions.codegen_agent_api import create_config_template

create_config_template("codegen_config.json")
```

Example configuration file:

```json
{
  "org_id": "your_org_id",
  "token": "your_api_token",
  "base_url": "https://api.codegen.com",
  "timeout": 30,
  "max_retries": 3,
  "enable_overlay": true,
  "overlay_priority": "pip_first",
  "enable_logging": true,
  "enable_metrics": true
}
```

## Webhook Integration

### Setting Up Webhooks

```python
from contexten.extensions.codegen_agent_api import WebhookProcessor, WebhookEventType

# Create webhook processor
webhook_processor = WebhookProcessor(secret="your_webhook_secret")

# Register handlers
def handle_task_completion(event):
    print(f"Task {event.task_id} completed: {event.data}")

webhook_processor.register_handler(
    WebhookEventType.TASK_COMPLETED,
    handle_task_completion
)

# Process incoming webhook
result = webhook_processor.process_webhook(payload, signature)
```

### Flask Integration

```python
from flask import Flask
from contexten.extensions.codegen_agent_api import WebhookProcessor

app = Flask(__name__)
webhook_processor = WebhookProcessor(secret="your_secret")

# Create webhook endpoint
webhook_processor.create_flask_endpoint(app, "/webhooks/codegen")

if __name__ == "__main__":
    app.run()
```

### Convenience Handlers

```python
from contexten.extensions.codegen_agent_api import (
    create_task_completion_handler,
    create_task_failure_handler,
    create_progress_handler
)

# Create handlers
completion_handler = create_task_completion_handler(
    lambda task_id, result: print(f"Task {task_id} completed: {result}")
)

failure_handler = create_task_failure_handler(
    lambda task_id, error: print(f"Task {task_id} failed: {error}")
)

progress_handler = create_progress_handler(
    lambda task_id, progress: print(f"Task {task_id} progress: {progress['percentage']}%")
)

# Register handlers
webhook_processor.register_handler(WebhookEventType.TASK_COMPLETED, completion_handler)
webhook_processor.register_handler(WebhookEventType.TASK_FAILED, failure_handler)
webhook_processor.register_handler(WebhookEventType.TASK_PROGRESS, progress_handler)
```

## Monitoring and Metrics

### Health Checks

```python
# Perform comprehensive health check
health = extension.health_check()
print(f"Overall status: {health['overall']}")

# Check specific components
for component, status in health['components'].items():
    print(f"{component}: {status['status']}")
```

### Metrics Collection

```python
# Get comprehensive metrics
metrics = extension.get_metrics()

print(f"Extension uptime: {metrics['uptime_seconds']} seconds")
print(f"Overlay strategy: {metrics['overlay_info']['strategy']}")
print(f"Active implementation: {metrics['overlay_info']['active_implementation']}")

# Get overlay-specific metrics
overlay_metrics = extension.overlay_client.get_metrics()
print(f"Pip calls: {overlay_metrics['pip_calls']}")
print(f"Local calls: {overlay_metrics['local_calls']}")
print(f"Fallback count: {overlay_metrics['fallback_count']}")
```

### Testing Implementations

```python
# Test both pip and local implementations
test_results = extension.test_implementations()

for impl, result in test_results.items():
    if result['available']:
        print(f"{impl} implementation: Available")
    else:
        print(f"{impl} implementation: Error - {result['error']}")
```

## Advanced Usage

### Custom Integration Agent

```python
from contexten.extensions.codegen_agent_api import create_integration_agent

# Create integration agent
integration_agent = create_integration_agent(config)

# Register custom event handlers
def handle_agent_created(event):
    print(f"Agent created with strategy: {event['data']['overlay_strategy']}")

integration_agent.register_event_handler("agent_created", handle_agent_created)

# Create agents through integration agent
agent = integration_agent.create_agent()
```

### Global CodebaseAI Instance

```python
from contexten.extensions.codegen_agent_api import (
    initialize_codebase_ai,
    codebase_ai,
    improve_function,
    analyze_codebase
)

# Initialize global instance
initialize_codebase_ai(org_id="your_org_id", token="your_api_token")

# Use global functions anywhere in your code
result = codebase_ai("Explain this code", target=code_snippet)
improved = improve_function(function_code)
analysis = analyze_codebase(codebase_info)
```

### Context Manager Usage

```python
# Use extension as context manager
with create_codegen_extension(org_id="your_org_id", token="your_api_token") as extension:
    agent = extension.create_agent()
    task = agent.run("Analyze this codebase")
    task.wait_for_completion()
    print(task.result)
# Extension automatically shuts down
```

## Error Handling

The extension provides comprehensive error handling with specific exception types:

```python
from contexten.extensions.codegen_agent_api import (
    CodegenError,
    AuthenticationError,
    OverlayError,
    PipPackageNotFoundError,
    ConfigurationError
)

try:
    agent = create_agent_with_overlay(org_id="invalid", token="invalid")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except OverlayError as e:
    print(f"Overlay error: {e}")
    print(f"Overlay info: {e.details.get('overlay_info', {})}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    print(f"Config key: {e.config_key}")
except CodegenError as e:
    print(f"General Codegen error: {e}")
    print(f"Error code: {e.error_code}")
    print(f"Details: {e.details}")
```

## API Reference

### Main Classes

- **`CodegenAgentAPI`**: Main extension class
- **`Agent`**: Enhanced agent for API interaction
- **`Task`**: Task representation with monitoring
- **`CodebaseAI`**: Direct function call interface
- **`OverlayClient`**: Handles pip/local overlay functionality
- **`WebhookProcessor`**: Processes incoming webhooks
- **`CodegenIntegrationAgent`**: Contexten ecosystem integration

### Configuration

- **`CodegenAgentAPIConfig`**: Configuration dataclass
- **`get_codegen_config()`**: Get configuration from multiple sources
- **`create_config_template()`**: Create configuration file template
- **`detect_pip_codegen()`**: Detect pip-installed codegen package

### Factory Functions

- **`create_codegen_extension()`**: Create main extension instance
- **`create_agent_with_overlay()`**: Create agent with overlay functionality
- **`create_codebase_ai_with_overlay()`**: Create CodebaseAI with overlay functionality

### Types and Enums

- **`TaskStatus`**: Task status enumeration
- **`TaskPriority`**: Task priority levels
- **`OverlayStrategy`**: Overlay strategy options
- **`WebhookEventType`**: Webhook event types

## Integration with Contexten

This extension follows the established contexten extension patterns:

- Standard directory structure and naming conventions
- Consistent configuration management
- Integration with contexten event system
- Comprehensive error handling and logging
- Metrics and monitoring capabilities

### Extension Metadata

```python
from contexten.extensions.codegen_agent_api import get_extension_info

info = get_extension_info()
print(f"Extension: {info['name']} v{info['version']}")
print(f"Overlay support: {info['overlay_support']}")
print(f"Pip package: {info['pip_package']}")
```

## Troubleshooting

### Common Issues

1. **Pip package not found**: Ensure `pip install codegen` is run in the same environment
2. **Authentication errors**: Verify org_id and token are correct
3. **Overlay failures**: Check overlay strategy and fallback settings
4. **Webhook signature failures**: Verify webhook secret matches

### Debug Information

```python
# Get overlay status
from contexten.extensions.codegen_agent_api import get_overlay_status

status = get_overlay_status()
print(f"Pip available: {status['pip_available']}")
if status['pip_info']:
    print(f"Pip version: {status['pip_info']['version']}")

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

```python
# Comprehensive health check
health = extension.health_check()

if health['overall'] != 'healthy':
    print("Extension health issues detected:")
    for component, info in health['components'].items():
        if info.get('status') != 'healthy':
            print(f"  {component}: {info.get('status')} - {info.get('error', 'No details')}")
```

## Contributing

This extension is part of the contexten ecosystem. For contributions:

1. Follow contexten extension development guidelines
2. Ensure compatibility with both pip and local implementations
3. Add comprehensive tests for overlay functionality
4. Update documentation for new features

## License

This extension follows the same license as the contexten project.

