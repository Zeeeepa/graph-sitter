# Autogenlib - Codegen SDK Integration Module

Autogenlib is a comprehensive integration layer between graph-sitter's codebase analysis capabilities and the Codegen SDK for AI-powered software engineering.

## Features

- **Codegen SDK Client**: Wrapper around the Codegen SDK with authentication, configuration, and error handling
- **Context Enhancement**: Automatic prompt enhancement using existing codebase analysis functions
- **Performance Optimization**: Caching layers and performance monitoring to meet <2s response time targets
- **Asynchronous Processing**: Queue management and async task execution for long-running operations
- **Orchestrator Integration**: Clean interfaces for contexten orchestrator integration
- **Usage Tracking**: Cost management and usage monitoring with configurable alerts
- **Error Handling**: Comprehensive retry logic with exponential backoff

## Quick Start

### Basic Usage

```python
from src.codegen.autogenlib import SimpleInterface, AutogenConfig

# Configure the client
config = AutogenConfig(
    org_id="your_org_id",
    token="your_api_token",
    enable_context_enhancement=True,
)

# Create interface
interface = SimpleInterface(config)

# Run a task
response = interface.run_task(
    prompt="Create a Python function that calculates fibonacci numbers",
    codebase_path="./src",  # Optional: for context enhancement
)

print(f"Result: {response.result}")
```

### Async Usage

```python
import asyncio
from src.codegen.autogenlib import OrchestratorInterface, AutogenConfig

async def main():
    config = AutogenConfig(
        org_id="your_org_id",
        token="your_api_token",
        enable_async_processing=True,
        max_concurrent_tasks=5,
    )
    
    interface = OrchestratorInterface(config)
    
    # Submit task
    response = await interface.submit_task(
        prompt="Implement a REST API endpoint for user management",
        codebase_path="./src",
    )
    
    # Monitor progress
    while True:
        status = await interface.get_task_status(response.task_id)
        if status.status in ["completed", "failed"]:
            break
        await asyncio.sleep(1)
    
    print(f"Final result: {status.result}")
    
    await interface.shutdown()

asyncio.run(main())
```

### Integration with Existing CodegenApp

```python
from src.codegen.autogenlib import create_autogenlib_integration

# Create integration
integration = create_autogenlib_integration()

# Handle agent request (compatible with existing CodegenApp)
result = await integration.handle_agent_request(
    prompt="Fix the bug in the authentication module",
    context={"codebase": {"path": "./src"}}
)

print(f"Success: {result['success']}")
print(f"Task ID: {result['task_id']}")
```

## Configuration

Autogenlib uses environment variables for configuration:

```bash
# Required
export AUTOGENLIB_ORG_ID="your_org_id"
export AUTOGENLIB_TOKEN="your_api_token"

# Optional
export AUTOGENLIB_API_BASE_URL="https://api.codegen.com"
export AUTOGENLIB_CACHE_ENABLED="true"
export AUTOGENLIB_CACHE_TTL="3600"
export AUTOGENLIB_MAX_RESPONSE_TIME="2.0"
export AUTOGENLIB_MAX_RETRIES="3"
export AUTOGENLIB_ENABLE_CONTEXT_ENHANCEMENT="true"
export AUTOGENLIB_MAX_CONTEXT_LENGTH="8000"
export AUTOGENLIB_ENABLE_ASYNC_PROCESSING="true"
export AUTOGENLIB_MAX_CONCURRENT_TASKS="5"
export AUTOGENLIB_USAGE_ALERT_THRESHOLD="100.0"
```

Or create a configuration object:

```python
from src.codegen.autogenlib import AutogenConfig

config = AutogenConfig(
    org_id="your_org_id",
    token="your_api_token",
    cache_enabled=True,
    cache_ttl=3600,
    max_response_time=2.0,
    max_retries=3,
    enable_context_enhancement=True,
    max_context_length=8000,
    enable_async_processing=True,
    max_concurrent_tasks=5,
    usage_alert_threshold=100.0,
)
```

## Context Enhancement

Autogenlib automatically enhances prompts with relevant codebase context using graph-sitter's analysis functions:

- **Codebase Summary**: Overall statistics and structure
- **File Summaries**: Dependencies and usage for relevant files
- **Class Summaries**: Class relationships and methods
- **Function Summaries**: Function dependencies and call sites
- **Symbol Summaries**: Symbol usage across the codebase

The context enhancement is intelligent and respects the `max_context_length` setting to avoid overwhelming the AI model.

## Caching

Multiple caching backends are supported:

- **Memory Cache**: Fast in-memory caching with LRU eviction
- **File Cache**: Persistent file-based caching
- **Redis Cache**: Distributed caching (planned)

Caching is applied to:
- Codebase analysis results
- Enhanced prompts
- Task results (for identical requests)

## Error Handling and Retries

Autogenlib includes comprehensive error handling:

- **Retry Logic**: Exponential backoff for transient failures
- **Smart Retry**: Avoids retrying authentication and validation errors
- **Usage Limits**: Prevents runaway costs with configurable thresholds
- **Graceful Degradation**: Falls back to original prompts if context enhancement fails

## Monitoring and Health Checks

```python
# Health check
health = await interface.health_check()
print(f"Status: {health['status']}")

# Usage statistics
stats = await interface.get_usage_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['success_rate']}%")
print(f"Estimated cost: ${stats['estimated_cost']:.2f}")
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Contexten Orchestrator                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                OrchestratorInterface                        │
├─────────────────────┬───────────────────────────────────────┤
│                     │                                       │
│  ┌─────────────────▼──────────────┐  ┌──────────────────────┐ │
│  │      AutogenClient             │  │   ContextEnhancer    │ │
│  │  ┌─────────────────────────┐   │  │  ┌─────────────────┐ │ │
│  │  │    Codegen SDK          │   │  │  │ Codebase        │ │ │
│  │  │    (Agent)              │   │  │  │ Analysis        │ │ │
│  │  └─────────────────────────┘   │  │  └─────────────────┘ │ │
│  └─────────────────┬──────────────┘  └──────────────────────┘ │
│                    │                                          │
│  ┌─────────────────▼──────────────┐  ┌──────────────────────┐ │
│  │    AsyncTaskProcessor          │  │    CacheManager      │ │
│  └────────────────────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Testing

Run the test suite:

```bash
# Unit tests
python -m pytest tests/unit/codegen/autogenlib/

# Integration tests
python -m pytest tests/integration/codegen/

# All tests
python -m pytest tests/
```

## Examples

See `examples/autogenlib_usage.py` for comprehensive usage examples including:

- Basic synchronous usage
- Asynchronous task processing
- Context enhancement
- Error handling
- Integration patterns

## Performance Targets

- **Response Time**: <2s for typical requests (configurable)
- **Concurrency**: Configurable concurrent task processing
- **Caching**: Intelligent caching to reduce API calls
- **Memory Usage**: Efficient memory management with LRU eviction

## Contributing

1. Follow the existing code patterns and structure
2. Add comprehensive tests for new functionality
3. Update documentation for any API changes
4. Ensure all tests pass and coverage remains >90%

## License

This module is part of the graph-sitter project and follows the same license terms.

