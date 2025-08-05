# AutoGenLib Integration with Codegen SDK and Graph-sitter

This module provides a comprehensive integration of AutoGenLib with the Codegen SDK and Graph-sitter codebase analysis, enabling dynamic code generation with rich contextual awareness.

**Note**: This integration has been moved from `contexten.extensions.autogenlib` to `codegen.extensions.autogenlib` to better reflect its primary dependency on the Codegen API.

## Features

- **Dynamic Code Generation**: Import modules and functions that don't exist yet
- **Multiple AI Providers**: Support for Codegen SDK, Claude API, and OpenAI (with fallback)
- **Rich Context Analysis**: Uses Graph-sitter to provide comprehensive codebase context
- **Contexten Integration**: Seamlessly integrates with the broader contexten ecosystem
- **Intelligent Caching**: Optional caching system for generated code
- **CLI Interface**: Command-line tools for management and testing

## Quick Start

### 1. Environment Setup

Set up your AI provider credentials:

```bash
# Codegen SDK (primary)
export CODEGEN_ORG_ID="your-org-id"
export CODEGEN_TOKEN="your-api-token"

# Claude API (fallback)
export CLAUDE_API_KEY="your-claude-key"

# OpenAI (additional fallback)
export OPENAI_API_KEY="your-openai-key"
```

### 2. Basic Usage

```python
from codegen.extensions.autogenlib import init_autogenlib

# Initialize with basic configuration
integration = init_autogenlib(
    description="Utility library for data processing",
    enable_caching=True
)

# Now you can import modules that don't exist yet
from autogenlib.data_processing import clean_data, validate_input
from autogenlib.analysis import calculate_statistics

# Use the generated functions
data = [{"name": "Alice", "score": 95}, {"name": "Bob", "score": 82}]
cleaned = clean_data(data)
stats = calculate_statistics(cleaned)
```

### 3. With Codebase Context

```python
from graph_sitter.core.codebase import Codebase
from codegen.extensions.autogenlib import init_autogenlib

# Load a codebase for context
codebase = Codebase.from_repo("fastapi/fastapi")

# Initialize with codebase context
integration = init_autogenlib(
    description="FastAPI utility extensions",
    codebase=codebase,
    enable_caching=True
)

# Generated code will be informed by FastAPI patterns
from autogenlib.fastapi_utils import create_router, add_middleware
```

### 4. Integration with CodegenApp

```python
from contexten.extensions.events.codegen_app import CodegenApp
from codegen.extensions.autogenlib.integration import setup_autogenlib_for_codegen_app

# Create a CodegenApp instance
app = CodegenApp("My App", repo="owner/repo")
app.parse_repo()

# Set up AutoGenLib integration
setup_autogenlib_for_codegen_app(app)

# Now AutoGenLib has access to the parsed codebase context
from autogenlib.project_utils import create_feature, add_tests
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CODEGEN_ORG_ID` | Codegen SDK organization ID | None |
| `CODEGEN_TOKEN` | Codegen SDK authentication token | None |
| `CLAUDE_API_KEY` | Claude API key | None |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `AUTOGENLIB_DESCRIPTION` | Default library description | "Dynamic code generation library" |
| `AUTOGENLIB_ENABLE_CACHING` | Enable code caching | false |
| `AUTOGENLIB_CACHE_DIR` | Cache directory | ~/.autogenlib_cache |
| `AUTOGENLIB_PROVIDER_ORDER` | Provider preference order | "codegen,claude,openai" |
| `AUTOGENLIB_GENERATION_TIMEOUT` | Generation timeout (seconds) | 30 |
| `AUTOGENLIB_MAX_CONTEXT_FUNCTIONS` | Max context functions | 10 |

### Programmatic Configuration

```python
from codegen.extensions.autogenlib.config import AutoGenLibConfig
from codegen.extensions.autogenlib import init_autogenlib

config = AutoGenLibConfig(
    description="Custom utility library",
    enable_caching=True,
    codegen_org_id="your-org-id",
    codegen_token="your-token",
    claude_api_key="your-claude-key",
    provider_order=["codegen", "claude"],
    max_context_functions=15,
    generation_timeout=45
)

integration = init_autogenlib(
    description=config.description,
    codegen_org_id=config.codegen_org_id,
    codegen_token=config.codegen_token,
    claude_api_key=config.claude_api_key,
    enable_caching=config.enable_caching
)
```

## CLI Usage

The integration includes a comprehensive CLI for management and testing:

### Status and Configuration

```bash
# Check integration status
python -m codegen.extensions.autogenlib.cli status

# Show current configuration
python -m codegen.extensions.autogenlib.cli config

# Show configuration in YAML format
python -m codegen.extensions.autogenlib.cli config --format yaml
```

### Initialization

```bash
# Initialize with basic settings
python -m codegen.extensions.autogenlib.cli init

# Initialize with codebase context
python -m codegen.extensions.autogenlib.cli init --repo "fastapi/fastapi"

# Initialize with custom description and caching
python -m codegen.extensions.autogenlib.cli init \
    --description "FastAPI utilities" \
    --enable-cache
```

### Code Generation

```bash
# Generate code for a module
python -m codegen.extensions.autogenlib.cli generate autogenlib.utils.helpers

# Generate with custom description
python -m codegen.extensions.autogenlib.cli generate autogenlib.data.processor \
    --description "Data processing utilities for CSV and JSON"

# Generate and save to file
python -m codegen.extensions.autogenlib.cli generate autogenlib.auth.tokens \
    --output tokens.py
```

### Testing and Development

```bash
# Test code generation interactively
python -m codegen.extensions.autogenlib.cli test autogenlib.test.module --interactive

# Test with automatic description
python -m codegen.extensions.autogenlib.cli test autogenlib.math.statistics
```

### Cache Management

```bash
# List cached modules
python -m codegen.extensions.autogenlib.cli list-cache

# Clear cache
python -m codegen.extensions.autogenlib.cli clear-cache
```

## Architecture

### Core Components

1. **AutoGenLibIntegration**: Main orchestration class
2. **CodeGenerator**: Manages multiple AI providers with fallback
3. **GraphSitterContextProvider**: Extracts rich context from codebases
4. **AutoGenLibFinder**: Custom import system integration
5. **CodeCache**: Intelligent caching system

### Provider System

The integration supports multiple AI providers with automatic fallback:

1. **Codegen SDK**: Primary provider using Codegen's agent system
2. **Claude API**: High-quality fallback using Anthropic's Claude
3. **OpenAI**: Additional fallback for compatibility

### Context Enhancement

Graph-sitter integration provides:

- **Function Analysis**: Related functions, dependencies, usage patterns
- **Codebase Statistics**: Overall project metrics and patterns
- **Caller Analysis**: Understanding of how generated code will be used
- **Similar Modules**: Examples from existing codebase

## Advanced Usage

### Custom Providers

```python
from codegen.extensions.autogenlib.generator import CodeGenerationProvider

class CustomProvider(CodeGenerationProvider):
    def generate_code(self, description, fullname, **kwargs):
        # Your custom generation logic
        return generated_code
    
    def is_available(self):
        return True  # Check if provider is ready
    
    @property
    def name(self):
        return "CustomProvider"

# Add to integration
integration.add_provider(CustomProvider())
```

### Context Customization

```python
from codegen.extensions.autogenlib.context import GraphSitterContextProvider

class CustomContextProvider(GraphSitterContextProvider):
    def get_context(self, fullname, caller_info=None):
        context = super().get_context(fullname, caller_info)
        # Add your custom context
        context["custom_data"] = self.get_custom_data(fullname)
        return context

# Use custom context provider
integration.context_provider = CustomContextProvider(codebase)
```

### Integration with Existing Systems

```python
# Integration with FastAPI
from fastapi import FastAPI
from codegen.extensions.autogenlib.integration import get_contexten_autogenlib

app = FastAPI()

@app.on_event("startup")
async def setup_autogenlib():
    integration = get_contexten_autogenlib()
    if integration and integration.is_available():
        print("AutoGenLib ready for dynamic imports")

# Integration with async workflows
import asyncio

async def generate_async(module_name):
    integration = get_contexten_autogenlib()
    if integration:
        # Run generation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        code = await loop.run_in_executor(
            None, 
            integration.autogenlib.generate_module,
            module_name
        )
        return code
```

## Error Handling and Debugging

### Logging

```python
import logging
from graph_sitter.shared.logging.get_logger import get_logger

# Enable debug logging
logger = get_logger("codegen.extensions.autogenlib")
logger.setLevel(logging.DEBUG)

# Check provider status
integration = get_contexten_autogenlib()
if integration:
    status = integration.get_status()
    print(f"Available providers: {status['available_providers']}")
```

### Common Issues

1. **No providers available**: Check API keys and credentials
2. **Generation timeout**: Increase `generation_timeout` in config
3. **Context too large**: Reduce `max_context_*` settings
4. **Import errors**: Ensure module names follow `autogenlib.*` pattern

### Debugging Generation

```python
# Enable detailed logging
import os
os.environ["AUTOGENLIB_DEBUG"] = "true"

# Test generation with detailed output
from codegen.extensions.autogenlib.cli import test
test("autogenlib.debug.test", interactive=True)
```

## Performance Considerations

### Caching Strategy

- Enable caching for production use
- Cache is persistent across Python sessions
- Cache keys are based on module names
- Clear cache when changing descriptions or context

### Context Optimization

- Limit context size for faster generation
- Use specific repository sections for focused context
- Consider caching codebase analysis results

### Provider Selection

- Codegen SDK: Best for code-specific tasks
- Claude: Excellent for complex logic and documentation
- OpenAI: Good general-purpose fallback

## Examples

See `examples.py` for comprehensive usage examples including:

- Basic dynamic imports
- Codebase-aware generation
- Integration with CodegenApp
- Error handling patterns
- Advanced configuration

## Contributing

When extending this integration:

1. Follow the existing provider pattern for new AI services
2. Add comprehensive logging for debugging
3. Include configuration options for new features
4. Update CLI commands for new functionality
5. Add examples for new usage patterns

## License

This integration follows the same license as the parent contexten project.
