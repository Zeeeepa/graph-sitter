# Enhanced AI Provider System with Factory Patterns

Graph-sitter now supports multiple AI providers through a robust, unified abstraction layer with intelligent factory patterns. This enhanced system allows you to use either OpenAI or the Codegen SDK (or both) seamlessly with advanced features like intelligent selection, comprehensive error handling, and detailed monitoring.

## 🚀 Key Features

- **🏭 Factory Patterns**: Intelligent provider creation with automatic selection and fallback
- **🔄 Dual Provider Support**: Use both OpenAI and Codegen SDK seamlessly
- **🧠 Intelligent Selection**: Automatically chooses the best available provider with fallback
- **🛡️ Robust Error Handling**: Exponential backoff, retry mechanisms, and comprehensive error recovery
- **📊 Advanced Monitoring**: Detailed metrics, usage tracking, and performance monitoring
- **⚙️ Explicit Control**: Force specific providers when needed with granular configuration
- **📦 Unified Interface**: Single API for all AI interactions with standardized responses
- **🔙 Backward Compatible**: Existing code works without changes
- **⚡ Enhanced Capabilities**: Access to Codegen's advanced agent features

## 🏗️ Architecture

### Enhanced Provider Factory System
```
src/graph_sitter/ai/providers/
├── __init__.py              # Package exports and factory interface
├── base.py                  # Abstract AIProvider interface with enhanced features
├── openai_provider.py       # Enhanced OpenAI implementation
├── codegen_provider.py      # Enhanced Codegen SDK implementation
└── factory.py               # Intelligent provider factory and selection logic
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

## 🏭 Factory Pattern Usage

### Automatic Provider Selection (Recommended)
```python
from graph_sitter.ai.providers import create_ai_provider

# Automatically selects best available provider
provider = create_ai_provider(prefer_codegen=True)
response = provider.generate_response("Analyze this code")
```

### Explicit Provider Selection
```python
from graph_sitter.ai.providers import create_ai_provider

# Force specific provider with fallback
codegen_provider = create_ai_provider(
    provider_name="codegen",
    fallback_enabled=True,
    validate_on_creation=True
)

# Generate response with Codegen-specific features
response = codegen_provider.generate_response(
    prompt="Analyze this repository",
    priority="normal",
    repository="owner/repo",
    branch="main",
    tags=["analysis", "review"]
)
```

### Task-Specific Provider Selection
```python
from graph_sitter.ai.providers import get_best_provider

# Get best provider for specific task types
code_provider = get_best_provider(task_type="code_generation")
doc_provider = get_best_provider(task_type="documentation")
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
print(f"Recommended: {comparison['summary']['recommended_provider']}")

# Check credentials
credentials = detect_available_credentials()
print(f"Detected credentials: {credentials}")
```

## 📚 Enhanced Client Usage

### Unified Client Interface
```python
from graph_sitter.ai.client import get_ai_client, generate_ai_response

# Get client with automatic provider selection
client = get_ai_client(prefer_codegen=True)

# Or force specific provider
codegen_client = get_ai_client(provider_name="codegen")
openai_client = get_ai_client(provider_name="openai")

# Convenience function for quick responses
response = generate_ai_response(
    prompt="Generate a test function",
    system_prompt="You are a test writing expert",
    model="gpt-4o"
)
```

### Backward Compatibility
```python
from graph_sitter import Codebase

# Existing code automatically uses enhanced provider system
codebase = Codebase(".")
result = codebase.ai("Improve this function", target=my_function)
```

## 🛡️ Enhanced Error Handling

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

## 📊 Monitoring and Statistics

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

1. **No code changes required** - existing code automatically uses the enhanced provider system
2. **Add Codegen credentials** to environment variables
3. **Optional**: Explicitly configure provider preferences

### Backward Compatibility

All existing code continues to work without changes. The enhanced provider system is fully backward compatible with the original OpenAI-only implementation.

## 🧪 Testing and Validation

### Run Enhanced Factory Validation
```bash
python scripts/validate_enhanced_factory.py
```

This tests:
- ✅ Factory pattern imports
- ✅ Provider detection and status
- ✅ Factory creation and selection
- ✅ Enhanced features and monitoring
- ✅ Client integration
- ✅ Backward compatibility
- ✅ Error handling

### Run Example Demo
```bash
python examples/ai_provider_example.py
```

## 🎯 Benefits of Factory Patterns

- **Intelligent Selection**: Automatically chooses the best provider based on availability and preferences
- **Fallback Mechanisms**: Seamless fallback to alternative providers if primary fails
- **Centralized Configuration**: Single point of configuration for all providers
- **Enhanced Monitoring**: Comprehensive statistics and health monitoring
- **Error Recovery**: Robust error handling with specific error types and recovery strategies
- **Task Optimization**: Provider selection optimized for specific task types
- **Production Ready**: Enterprise-grade reliability and resource management

## 🔮 Future Enhancements

The enhanced factory system is designed to be extensible:

- **Additional Providers**: Easy to add new AI providers
- **Custom Providers**: Implement custom provider classes
- **Advanced Routing**: Intelligent request routing based on task type
- **Load Balancing**: Distribute requests across multiple provider instances
- **Caching Layer**: Response caching for improved performance

---

**Ready to use!** This enhanced implementation with factory patterns is production-ready and provides enterprise-grade reliability for AI-powered code analysis and generation.

