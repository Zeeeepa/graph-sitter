# Enhanced AI Provider System

Graph-sitter now supports multiple AI providers through a robust, unified abstraction layer. This enhanced system allows you to use either OpenAI or the Codegen SDK (or both) seamlessly with advanced features like intelligent fallback, comprehensive error handling, and detailed monitoring.

## 🚀 Key Features

- **🔄 Dual Provider Support**: Use both OpenAI and Codegen SDK seamlessly
- **🧠 Intelligent Selection**: Automatically chooses the best available provider with fallback
- **🛡️ Robust Error Handling**: Exponential backoff, retry mechanisms, and comprehensive error recovery
- **📊 Advanced Monitoring**: Detailed metrics, usage tracking, and performance monitoring
- **⚙️ Explicit Control**: Force specific providers when needed with granular configuration
- **📦 Unified Interface**: Single API for all AI interactions with standardized responses
- **🔙 Backward Compatible**: Existing code works without changes
- **⚡ Enhanced Capabilities**: Access to Codegen's advanced agent features

## 🏗️ Architecture

### Provider Abstraction Layer
```
src/graph_sitter/ai/providers/
├── __init__.py              # Package exports and main interface
├── base.py                  # Abstract AIProvider interface with enhanced features
├── openai_provider.py       # Enhanced OpenAI implementation
├── codegen_provider.py      # Enhanced Codegen SDK implementation
└── factory.py               # Intelligent provider selection and management
```

### Enhanced Codegen SDK Integration
```
src/codegen/
├── __init__.py              # Enhanced SDK package
├── agent.py                 # Enhanced Agent class with robust error handling
├── task.py                  # Enhanced Task management with monitoring
└── exceptions.py            # Comprehensive custom exceptions
```

## ⚙️ Configuration

Set up either or both providers via environment variables:

```bash
# OpenAI (existing)
export OPENAI_API_KEY="your_openai_key"

# Enhanced Codegen SDK (new, preferred)
export CODEGEN_ORG_ID="your_org_id"
export CODEGEN_TOKEN="your_token"

# Optional: Custom base URL
export CODEGEN_BASE_URL="https://api.codegen.com"
```

### Advanced Configuration

```bash
# Timeout settings
export CODEGEN_TIMEOUT=300
export CODEGEN_MAX_RETRIES=3
export OPENAI_TIMEOUT=30
export OPENAI_MAX_RETRIES=3

# Logging
export LOG_LEVEL=INFO
export ENABLE_AI_LOGGING=true
```

## 📖 Usage Examples

### Automatic Provider Selection (Recommended)
```python
from graph_sitter import Codebase

codebase = Codebase(".")
# Automatically uses Codegen SDK if available, falls back to OpenAI
result = codebase.ai("Improve this function", target=my_function)
```

### Explicit Provider Choice
```python
from graph_sitter.ai.client import get_ai_client

# Force specific provider
codegen_client = get_ai_client(provider_name="codegen")
openai_client = get_ai_client(provider_name="openai")

# Generate response
response = codegen_client.generate_response(
    prompt="Analyze this code",
    system_prompt="You are a code analysis expert",
    model="codegen-agent",
    temperature=0.0
)
```

### Enhanced Provider Factory
```python
from graph_sitter.ai.providers import create_ai_provider

# Create with preferences and validation
provider = create_ai_provider(
    prefer_codegen=True,          # Prefer Codegen SDK
    fallback_enabled=True,        # Enable fallback to other providers
    validate_on_creation=True,    # Validate credentials during creation
    timeout=300,                  # Custom timeout
    max_retries=3                 # Custom retry count
)

response = provider.generate_response(
    prompt="Generate a test function",
    system_prompt="You are a test writing expert",
    priority="normal",            # Codegen-specific: task priority
    tags=["test", "generation"],  # Codegen-specific: task tags
    repository="owner/repo",      # Codegen-specific: target repository
    branch="main"                 # Codegen-specific: target branch
)
```

### Provider Status and Monitoring
```python
from graph_sitter.ai.providers import (
    get_provider_status,
    get_provider_comparison,
    detect_available_credentials
)

# Check provider status
status = get_provider_status()
print(f"Available providers: {status}")

# Get detailed comparison
comparison = get_provider_comparison()
print(f"Recommended provider: {comparison['summary']['recommended_provider']}")

# Check credentials
credentials = detect_available_credentials()
print(f"Detected credentials: {credentials}")
```

## 🎯 Enhanced Benefits

### Robustness Features
- **Exponential Backoff**: Intelligent retry mechanisms with exponential backoff
- **Rate Limit Handling**: Automatic rate limit detection and waiting
- **Connection Pooling**: Efficient HTTP connection management
- **Credential Validation**: Automatic credential validation with caching
- **Fallback Mechanisms**: Seamless fallback between providers
- **Comprehensive Logging**: Detailed request/response logging and monitoring

### Effectiveness Improvements
- **Task Management**: Enhanced task creation, monitoring, and artifact handling
- **Progress Tracking**: Real-time progress monitoring with callbacks
- **Usage Analytics**: Detailed usage statistics and cost estimation
- **Performance Metrics**: Response time tracking and performance analysis
- **Webhook Support**: Event-driven notifications for task updates
- **Enhanced Context**: Rich context passing with metadata and tags

### Production-Ready Features
- **Error Recovery**: Comprehensive error handling with specific error types
- **Monitoring Dashboard**: Built-in stats and health monitoring
- **Configuration Management**: Flexible configuration with environment detection
- **Resource Cleanup**: Proper resource management and cleanup
- **Thread Safety**: Safe for concurrent usage
- **Memory Efficiency**: Optimized memory usage with caching strategies

## 🔧 Advanced Usage

### Custom Error Handling
```python
from graph_sitter.ai.providers import (
    create_ai_provider,
    ProviderUnavailableError,
    ProviderRateLimitError,
    ProviderTimeoutError
)

try:
    provider = create_ai_provider(provider_name="codegen")
    response = provider.generate_response("Analyze this code")
except ProviderRateLimitError as e:
    print(f"Rate limited, retry after: {e.retry_after}")
except ProviderTimeoutError as e:
    print(f"Request timed out after: {e.timeout_duration}")
except ProviderUnavailableError as e:
    print(f"Provider unavailable: {e}")
```

### Task Monitoring with Callbacks
```python
from codegen import Agent

agent = Agent(org_id="your_org", token="your_token")

def progress_callback(progress_info):
    print(f"Task progress: {progress_info}")

def status_callback(old_status, new_status):
    print(f"Status changed: {old_status} -> {new_status}")

task = agent.run("Analyze this repository")
task.add_status_callback(status_callback)

task.wait_for_completion(
    timeout=300,
    poll_interval=10,
    progress_callback=progress_callback
)
```

### Provider Statistics and Monitoring
```python
# Get comprehensive provider stats
provider = create_ai_provider(provider_name="codegen")

# Basic stats
stats = provider.get_stats()
print(f"Requests: {stats['request_count']}, Errors: {stats['error_count']}")

# Enhanced stats (if available)
if hasattr(provider, 'get_enhanced_stats'):
    enhanced_stats = provider.get_enhanced_stats()
    print(f"Success rate: {enhanced_stats['success_rate']:.2%}")
    print(f"Task count: {enhanced_stats['task_count']}")
```

## 🔄 Migration Guide

### From OpenAI-only to Enhanced Multi-provider

1. **Install enhanced dependencies** (already included):
   ```bash
   pip install requests>=2.31.0
   ```

2. **Add Codegen credentials** to your environment:
   ```bash
   export CODEGEN_ORG_ID="your_org_id"
   export CODEGEN_TOKEN="your_token"
   ```

3. **No code changes required** - existing code automatically uses the enhanced provider system with Codegen SDK preferred.

### Backward Compatibility

All existing code continues to work without changes. The enhanced provider system is fully backward compatible with the original OpenAI-only implementation.

```python
# This still works exactly as before
from graph_sitter import Codebase

codebase = Codebase(".")
result = codebase.ai("Generate code")  # Now uses enhanced provider system
```

## 🛠️ Troubleshooting

### Common Issues

1. **No providers available**
   - Ensure at least one set of credentials is configured
   - Check environment variables are set correctly
   - Verify network connectivity

2. **Codegen SDK errors**
   - Check your organization ID and token validity at https://codegen.sh/developer
   - Verify your organization has sufficient credits
   - Check API endpoint accessibility

3. **OpenAI rate limits**
   - Consider switching to Codegen SDK for better rate limits
   - Implement custom retry logic if needed
   - Monitor usage with provider statistics

4. **Model compatibility**
   - Some models may only be available on specific providers
   - Check available models with `provider.get_available_models()`
   - Use provider-specific model names

### Debug Mode

Enable debug logging to see provider selection and request details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will show detailed provider selection and request information
result = codebase.ai("Debug this code")
```

### Health Checks

```python
from graph_sitter.ai.providers import get_provider_status

# Check all provider health
status = get_provider_status()
for provider_name, provider_status in status.items():
    if provider_status['is_available']:
        print(f"✅ {provider_name}: Available")
    else:
        print(f"❌ {provider_name}: {provider_status.get('error', 'Not available')}")
```

## 📊 Performance Optimization

### Caching and Connection Pooling
- Credential validation is cached for 5 minutes
- HTTP connections are pooled for efficiency
- Provider instances can be reused across requests

### Rate Limit Management
- Automatic rate limit detection and handling
- Exponential backoff with configurable parameters
- Rate limit status tracking and reporting

### Memory Management
- Efficient artifact and log caching
- Automatic cleanup of completed tasks
- Optimized memory usage for long-running processes

## 🔮 Future Enhancements

The enhanced provider system is designed to be extensible:

- **Additional Providers**: Easy to add new AI providers
- **Custom Providers**: Implement custom provider classes
- **Advanced Routing**: Intelligent request routing based on task type
- **Load Balancing**: Distribute requests across multiple provider instances
- **Caching Layer**: Response caching for improved performance

## 📚 API Reference

### Core Classes

- `AIProvider`: Abstract base class for all providers
- `AIResponse`: Standardized response format
- `CodegenProvider`: Enhanced Codegen SDK implementation
- `OpenAIProvider`: Enhanced OpenAI implementation

### Factory Functions

- `create_ai_provider()`: Main provider creation function
- `get_provider_status()`: Get status of all providers
- `detect_available_credentials()`: Check available credentials
- `get_provider_comparison()`: Compare provider capabilities

### Exception Classes

- `ProviderUnavailableError`: Provider not available or misconfigured
- `ProviderAuthenticationError`: Authentication failed
- `ProviderRateLimitError`: Rate limit exceeded
- `ProviderTimeoutError`: Request timed out

## 🎉 Ready to Use

This enhanced implementation is production-ready and provides a solid foundation for leveraging both OpenAI and Codegen SDK capabilities in graph-sitter projects with enterprise-grade robustness and monitoring.

