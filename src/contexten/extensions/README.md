# Contexten Extensions

This directory contains all extensions for the Contexten system, providing comprehensive integration with various services and tools for project management, workflow orchestration, and development automation.

## Available Extensions

### Core Integrations

#### 🐙 GitHub Extension (`github/`)
- **Purpose**: Repository management, PR handling, issue tracking
- **Features**:
  - Repository discovery and management
  - Pull request creation and monitoring
  - Issue tracking and management
  - Webhook processing for real-time updates
  - Code analysis integration
- **Configuration**: Requires GitHub API token
- **Dependencies**: None

#### 📋 Linear Extension (`linear/`)
- **Purpose**: Project and issue management
- **Features**:
  - Team and project management
  - Issue creation and tracking
  - Workflow automation
  - Progress monitoring
  - GraphQL API integration
- **Configuration**: Requires Linear API key
- **Dependencies**: None

#### 🤖 Codegen Extension (`codegen/`)
- **Purpose**: AI-powered code generation and planning
- **Features**:
  - Automated project planning
  - Task execution and monitoring
  - Code analysis and generation
  - Quality assessment
  - Progress tracking
- **Configuration**: Requires Codegen org ID and token
- **Dependencies**: None

### Workflow Orchestration

#### ⚡ Flow Orchestrator (`flows/`)
- **Purpose**: Multi-system workflow orchestration
- **Features**:
  - **Prefect Integration**: Data workflow management
  - **ControlFlow Integration**: Agent-based workflows
  - **Strands Integration**: Tool-based workflows
  - **MCP Integration**: Model Context Protocol flows
  - Multi-layered execution
  - Real-time monitoring
  - Flow lifecycle management
- **Configuration**: Optional API keys for each system
- **Dependencies**: GitHub, Linear, Codegen

### User Interface

#### 🎛️ Dashboard Extension (`dashboard/`)
- **Purpose**: Web-based management interface
- **Features**:
  - Project selection and pinning
  - Requirements management
  - Flow control and monitoring
  - Real-time updates via WebSocket
  - Settings management
  - Multi-service integration
- **Configuration**: Host, port, frontend path
- **Dependencies**: All other extensions

### Communication

#### 💬 Slack Extension (`slack/`)
- **Purpose**: Team communication and notifications
- **Features**:
  - Real-time notifications
  - Command interface
  - Status updates
  - Integration with workflows
- **Configuration**: Slack bot token and secrets
- **Dependencies**: None

### CI/CD Integration

#### 🔄 CircleCI Extension (`circleci/`)
- **Purpose**: Continuous integration and deployment
- **Features**:
  - Build monitoring
  - Failure analysis
  - Workflow automation
  - Quality gates
- **Configuration**: CircleCI API token
- **Dependencies**: GitHub

## Extension Architecture

### Base Classes

All extensions inherit from one of these base classes:

```python
# Basic extension with lifecycle management
class Extension(ABC):
    async def initialize(self) -> None
    async def start(self) -> None
    async def stop(self) -> None
    async def health_check(self) -> Dict[str, Any]

# Extension with event handling capabilities
class EventHandlerExtension(Extension):
    def register_event_handler(self, event_type: str, handler: callable)
    async def handle_event(self, event_type: str, event_data: Any)

# Extension with service registration capabilities
class ServiceExtension(Extension):
    def register_service(self, service_type: Type[Any], implementation: Any)
    def get_service(self, service_type: Type[Any]) -> Any
```

### Extension Lifecycle

1. **Registration**: Extensions are registered with the ExtensionRegistry
2. **Initialization**: `initialize()` method is called to set up the extension
3. **Startup**: `start()` method is called to begin operations
4. **Runtime**: Extension handles events and provides services
5. **Shutdown**: `stop()` method is called for cleanup

### Event System

Extensions communicate through a centralized event bus:

```python
# Publishing events
await self.app.event_bus.publish(Event(
    type="project.pinned",
    source="dashboard",
    data={"project_id": "123", "repository": "owner/repo"}
))

# Subscribing to events
self.register_event_handler("project.pinned", self._handle_project_pin)
```

## Configuration

### Environment Variables

Extensions can be configured using environment variables:

```bash
# GitHub
export GITHUB_TOKEN="your_github_token"
export GITHUB_WEBHOOK_SECRET="your_webhook_secret"

# Linear
export LINEAR_API_KEY="your_linear_api_key"

# Codegen
export CODEGEN_ORG_ID="your_org_id"
export CODEGEN_TOKEN="your_token"

# Dashboard
export DASHBOARD_HOST="0.0.0.0"
export DASHBOARD_PORT="8000"
```

### Configuration File

Create a configuration file based on the example:

```python
from contexten.config.example_config import get_config

config = get_config("production")
app = ContextenApp(config)
```

## Usage Examples

### Starting the Full System

```python
from contexten import ContextenApp
from contexten.config.example_config import get_config

# Load configuration
config = get_config("development")

# Create and start application
app = ContextenApp(config)
await app.start()

# Application is now running with all configured extensions
```

### Dashboard-Only Mode

```python
config = {
    "dashboard": {
        "host": "0.0.0.0",
        "port": 8000,
        "frontend_path": "./frontend/build"
    }
}

app = ContextenApp(config)
await app.start()
```

### Accessing Extensions

```python
# Get extension instance
github_ext = app.get_extension("github")
if github_ext:
    repos = await github_ext.get_repositories()

# Check extension availability
if app.has_extension("linear"):
    linear_ext = app.get_extension("linear")
    teams = await linear_ext.get_teams()
```

## Development

### Creating a New Extension

1. Create extension directory: `src/contexten/extensions/my_extension/`
2. Implement extension class:

```python
from ...core.extension import Extension, ExtensionMetadata

class MyExtension(Extension):
    @property
    def metadata(self) -> ExtensionMetadata:
        return ExtensionMetadata(
            name="my_extension",
            version="1.0.0",
            description="My custom extension",
            author="Your Name",
            dependencies=[],
            required=False
        )

    async def initialize(self) -> None:
        # Setup extension
        pass

    async def start(self) -> None:
        # Start extension services
        pass

    async def stop(self) -> None:
        # Cleanup
        pass
```

3. Register extension in `__init__.py`
4. Add to auto-registration in `contexten_app.py`

### Testing Extensions

```python
import pytest
from contexten import ContextenApp

@pytest.mark.asyncio
async def test_my_extension():
    config = {"my_extension": {"api_key": "test"}}
    app = ContextenApp(config)
    
    await app.start()
    
    # Test extension functionality
    ext = app.get_extension("my_extension")
    assert ext is not None
    
    health = await ext.health_check()
    assert health["status"] == "healthy"
    
    await app.stop()
```

## API Reference

### Extension Registry

- `register_extension(extension_type, config)`: Register an extension
- `get_extension(name)`: Get extension instance
- `initialize_extensions()`: Initialize all extensions
- `start_extensions()`: Start all extensions
- `stop_extensions()`: Stop all extensions

### Event Bus

- `publish(event)`: Publish an event
- `subscribe(event_type, handler)`: Subscribe to events
- `unsubscribe(event_type, handler)`: Unsubscribe from events

### Service Container

- `register(service_type, implementation)`: Register a service
- `get(service_type)`: Get service instance

## Troubleshooting

### Common Issues

1. **Extension not loading**: Check configuration and dependencies
2. **API authentication errors**: Verify API keys and tokens
3. **Port conflicts**: Ensure dashboard port is available
4. **WebSocket connection issues**: Check CORS and firewall settings

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("contexten").setLevel(logging.DEBUG)
```

Check extension health:

```python
health = await app.health_check()
print(health["components"]["extensions"])
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your extension
4. Add tests
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

