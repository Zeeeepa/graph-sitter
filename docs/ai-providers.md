# AI Provider System

Graph-sitter now supports multiple AI providers through a unified abstraction layer. This allows you to use either OpenAI or the Codegen SDK (or both) seamlessly.

## Supported Providers

### 1. Codegen SDK (Recommended)
The Codegen SDK provides access to powerful AI agents that can perform complex development tasks.

**Configuration:**
```bash
export CODEGEN_ORG_ID="your_organization_id"
export CODEGEN_TOKEN="your_api_token"
```

Get your credentials from:
- API Token: https://codegen.sh/token
- Organization ID: https://codegen.sh/developer

### 2. OpenAI
Traditional OpenAI API integration for chat completions.

**Configuration:**
```bash
export OPENAI_API_KEY="your_openai_api_key"
```

## Usage

### Automatic Provider Selection
The system automatically selects the best available provider:

```python
from graph_sitter import Codebase

# Automatically uses Codegen SDK if available, falls back to OpenAI
codebase = Codebase(".")
result = codebase.ai("Improve this function", target=my_function)
```

### Explicit Provider Selection
You can explicitly choose which provider to use:

```python
from graph_sitter.ai.client import get_ai_client

# Force OpenAI
openai_client = get_ai_client(provider_name="openai")

# Force Codegen SDK
codegen_client = get_ai_client(provider_name="codegen")
```

### Provider Factory
For advanced use cases, use the provider factory directly:

```python
from graph_sitter.ai.providers import create_ai_provider

# Create with preferences
provider = create_ai_provider(
    provider_name="codegen",  # Explicit provider
    prefer_codegen=True,      # Preference when auto-selecting
    model="gpt-4o"           # Model preference
)

response = provider.generate_response(
    prompt="Write a test for this function",
    system_prompt="You are a helpful coding assistant",
    model="gpt-4o",
    temperature=0.0
)
```

## Environment Configuration

Create a `.env` file in your project root:

```bash
# AI Provider Configuration
# You can use either OpenAI or Codegen SDK (or both)

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Codegen SDK Configuration (Preferred)
CODEGEN_ORG_ID=your_organization_id_here
CODEGEN_TOKEN=your_api_token_here

# The system will automatically prefer Codegen SDK if both are configured
```

## Provider Capabilities

### Codegen SDK Features
- **Task Management**: Create and monitor long-running development tasks
- **Agent Orchestration**: Access to specialized coding agents
- **Advanced Reasoning**: Multi-step problem solving
- **Code Generation**: Sophisticated code creation and refactoring
- **Integration Support**: Built-in GitHub, Linear, and other integrations

### OpenAI Features
- **Chat Completions**: Direct access to OpenAI models
- **Tool Calling**: Function calling capabilities
- **Streaming**: Real-time response streaming
- **Fine-tuning**: Custom model support

## Migration Guide

### From OpenAI-only to Multi-provider

1. **Install dependencies** (already included):
   ```bash
   pip install requests>=2.31.0
   ```

2. **Add Codegen credentials** to your environment:
   ```bash
   export CODEGEN_ORG_ID="your_org_id"
   export CODEGEN_TOKEN="your_token"
   ```

3. **No code changes required** - existing code will automatically use the new provider system with Codegen SDK preferred.

### Backward Compatibility

All existing code continues to work without changes. The new provider system is fully backward compatible with the original OpenAI-only implementation.

## Error Handling

The provider system includes comprehensive error handling:

```python
try:
    result = codebase.ai("Generate code")
except Exception as e:
    print(f"AI request failed: {e}")
    # Automatic fallback to alternative provider if available
```

## Advanced Configuration

### Custom Provider Implementation

You can implement custom providers by extending the `AIProvider` base class:

```python
from graph_sitter.ai.providers.base import AIProvider, AIResponse

class CustomProvider(AIProvider):
    provider_name = "custom"
    
    def generate_response(self, prompt, **kwargs):
        # Your custom implementation
        return AIResponse(
            content="Generated response",
            provider_name="custom",
            model="custom-model"
        )
```

### Provider Selection Logic

The system uses the following priority order:
1. Explicitly specified provider (`provider_name` parameter)
2. Codegen SDK (if credentials available and `prefer_codegen=True`)
3. OpenAI (if credentials available)
4. Raises error if no providers available

## Troubleshooting

### Common Issues

1. **No providers available**: Ensure at least one set of credentials is configured
2. **Codegen SDK errors**: Check your organization ID and token validity
3. **OpenAI rate limits**: Consider switching to Codegen SDK for better rate limits
4. **Model compatibility**: Some models may only be available on specific providers

### Debug Mode

Enable debug logging to see provider selection:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Will show which provider is selected and why
result = codebase.ai("Debug this code")
```

## Examples

See the `examples/` directory for complete examples of using both providers in various scenarios.

