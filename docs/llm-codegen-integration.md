# LLM Codegen SDK Integration

This document describes how to integrate Codegen SDK as a selectable and default model for program-wide agentic calls in the LLM system.

## Overview

The enhanced LLM system now supports:
- **Multiple Providers**: OpenAI, Anthropic, XAI, and Codegen SDK
- **Global Configuration**: Program-wide default provider and model settings
- **Agent Function Calls**: Tools for agents to configure LLM providers dynamically
- **Environment Configuration**: Environment variable and config file support
- **Seamless Integration**: Drop-in replacement for existing LLM usage

## Quick Start

### 1. Basic Usage

```python
from contexten.extensions.langchain.llm import LLM

# Method 1: Direct instantiation with Codegen SDK
llm = LLM.with_codegen(
    org_id="your-org-id",
    token="your-token",
    model="codegen-agent"
)

# Method 2: Using global configuration
llm = LLM.from_config()  # Uses configured default provider

# Method 3: Specific provider
llm = LLM(model_provider="codegen", model_name="codegen-agent")
```

### 2. Set Codegen as Default

```python
from contexten.extensions.langchain.llm_config import configure_codegen_default

# Configure Codegen SDK as the default provider program-wide
configure_codegen_default("your-org-id", "your-token", "codegen-agent")

# Now all LLM.from_config() calls will use Codegen SDK
llm = LLM.from_config()
```

## Configuration Methods

### Environment Variables

Set these environment variables to configure the LLM system:

```bash
# Default provider selection
export LLM_DEFAULT_PROVIDER=codegen
export LLM_DEFAULT_MODEL=codegen-agent
export LLM_TEMPERATURE=0.1
export LLM_MAX_TOKENS=4000

# Codegen SDK credentials
export CODEGEN_ORG_ID=your-org-id
export CODEGEN_TOKEN=your-token

# Other provider credentials
export ANTHROPIC_API_KEY=your-anthropic-key
export OPENAI_API_KEY=your-openai-key
export XAI_API_KEY=your-xai-key
```

### Configuration File

Create `llm_config.json` in one of these locations:
- `./llm_config.json` (current directory)
- `~/.contexten/llm_config.json` (user home)
- `/etc/contexten/llm_config.json` (system-wide)

```json
{
  "default_provider": "codegen",
  "default_model": "codegen-agent",
  "temperature": 0.1,
  "max_tokens": 4000,
  "timeout": 300,
  "codegen": {
    "model": "codegen-agent",
    "temperature": 0.1
  },
  "anthropic": {
    "model": "claude-3-5-sonnet-latest",
    "temperature": 0.0
  },
  "openai": {
    "model": "gpt-4",
    "temperature": 0.1
  }
}
```

### Programmatic Configuration

```python
from contexten.extensions.langchain.llm_config import get_llm_config

config = get_llm_config()

# Set Codegen as default
config.set_codegen_as_default("your-org-id", "your-token", "codegen-agent")

# Or configure any provider
config.default_provider = "codegen"
config.default_model = "codegen-agent"
config.temperature = 0.1

# Save configuration to file
config.save_to_file()
```

## Agent Function Call Interface

The system provides function call interfaces that agents can use to configure LLM providers dynamically.

### Universal Configuration Function

```python
from contexten.extensions.langchain.llm_tools import configure_llm_provider

# Set Codegen as default
result = configure_llm_provider(
    action="set_codegen_default",
    org_id="your-org-id",
    token="your-token",
    model="codegen-agent"
)

# Set any provider as default
result = configure_llm_provider(
    action="set_provider",
    provider="anthropic",
    model="claude-3-5-sonnet-latest",
    temperature=0.1
)

# Get current status
status = configure_llm_provider(action="get_status")
```

### LangChain Tools

For integration with LangChain agents:

```python
from contexten.extensions.langchain.llm_tools import get_llm_configuration_tools

# Get tools for agent use
tools = get_llm_configuration_tools()

# Tools available:
# - SetCodegenDefaultTool: Set Codegen SDK as default
# - SetLLMProviderTool: Set any provider as default  
# - GetLLMStatusTool: Get current configuration status
```

### Individual Tool Functions

```python
from contexten.extensions.langchain.llm_tools import (
    set_codegen_as_default_llm,
    set_llm_provider,
    get_llm_status
)

# Set Codegen as default
result = set_codegen_as_default_llm("your-org-id", "your-token")

# Set any provider
result = set_llm_provider("anthropic", model="claude-3-5-sonnet-latest")

# Get status
status = get_llm_status()
```

## Provider-Specific Features

### Codegen SDK

**Benefits:**
- Specialized for software engineering tasks
- Integrated with Codegen's code understanding
- Advanced code generation capabilities
- Better handling of large codebases

**Configuration:**
```python
# Direct instantiation
llm = LLM.with_codegen("org-id", "token", "codegen-agent")

# Via configuration
from contexten.extensions.langchain.llm_config import configure_codegen_default
configure_codegen_default("org-id", "token", "codegen-agent")
```

**Environment Variables:**
```bash
export CODEGEN_ORG_ID=your-org-id
export CODEGEN_TOKEN=your-token
```

### OpenAI

**Configuration:**
```python
llm = LLM(model_provider="openai", model_name="gpt-4")
```

**Environment Variables:**
```bash
export OPENAI_API_KEY=your-api-key
```

### Anthropic

**Configuration:**
```python
llm = LLM(model_provider="anthropic", model_name="claude-3-5-sonnet-latest")
```

**Environment Variables:**
```bash
export ANTHROPIC_API_KEY=your-api-key
```

### XAI

**Configuration:**
```python
llm = LLM(model_provider="xai", model_name="grok-beta")
```

**Environment Variables:**
```bash
export XAI_API_KEY=your-api-key
export XAI_API_BASE=https://api.x.ai/v1/  # Optional
```

## Advanced Usage

### Provider Selection Logic

The system automatically selects providers in this order:

1. **Explicit provider**: If specified in constructor or method call
2. **Configured default**: From global configuration
3. **Auto-selection**: Based on available credentials
   - Preference order: Codegen → Anthropic → OpenAI → XAI

```python
from contexten.extensions.langchain.llm_config import get_llm_config

config = get_llm_config()

# Check available providers
available = config.get_available_providers()
print(f"Available: {available}")

# Auto-select best provider
provider = config.auto_select_provider()
print(f"Auto-selected: {provider}")
```

### Custom Configuration

```python
from contexten.extensions.langchain.llm_config import LLMConfig, set_llm_config

# Create custom configuration
custom_config = LLMConfig(
    default_provider="codegen",
    default_model="codegen-agent",
    temperature=0.2,
    max_tokens=8000,
    codegen_org_id="your-org-id",
    codegen_token="your-token"
)

# Set as global configuration
set_llm_config(custom_config)

# Now all LLM.from_config() calls use this configuration
llm = LLM.from_config()
```

### Error Handling

```python
from contexten.extensions.langchain.llm import LLM
from contexten.extensions.langchain.llm_config import get_llm_config

try:
    llm = LLM.from_config()
except ValueError as e:
    if "No LLM providers are available" in str(e):
        print("Please configure at least one LLM provider")
        # Show available configuration options
        config = get_llm_config()
        print(f"Available providers: {config.get_available_providers()}")
    else:
        print(f"Configuration error: {e}")
```

## Integration Examples

### Agent with LLM Configuration Tools

```python
from langchain.agents import create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate
from contexten.extensions.langchain.llm_tools import get_llm_configuration_tools
from contexten.extensions.langchain.llm import LLM

# Create LLM instance
llm = LLM.from_config()

# Get LLM configuration tools
llm_tools = get_llm_configuration_tools()

# Create agent with LLM configuration capabilities
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI assistant that can configure LLM providers."),
    ("user", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

agent = create_openai_functions_agent(llm, llm_tools, prompt)

# Now the agent can configure LLM providers via function calls
```

### Dynamic Provider Switching

```python
from contexten.extensions.langchain.llm import LLM
from contexten.extensions.langchain.llm_config import get_llm_config

def get_best_llm_for_task(task_type: str) -> LLM:
    """Select the best LLM provider for a specific task"""
    
    config = get_llm_config()
    available = config.get_available_providers()
    
    if task_type == "code_generation" and "codegen" in available:
        return LLM(model_provider="codegen")
    elif task_type == "analysis" and "anthropic" in available:
        return LLM(model_provider="anthropic")
    elif task_type == "general" and "openai" in available:
        return LLM(model_provider="openai")
    else:
        # Fall back to configured default
        return LLM.from_config()

# Usage
code_llm = get_best_llm_for_task("code_generation")
analysis_llm = get_best_llm_for_task("analysis")
```

### Batch Configuration

```python
from contexten.extensions.langchain.llm_tools import configure_llm_provider

def setup_development_environment():
    """Configure LLM providers for development environment"""
    
    # Set Codegen as default for code tasks
    result1 = configure_llm_provider(
        action="set_codegen_default",
        org_id=os.getenv("CODEGEN_ORG_ID"),
        token=os.getenv("CODEGEN_TOKEN"),
        model="codegen-agent"
    )
    
    print("Development environment configured:")
    print(result1)
    
    # Verify configuration
    status = configure_llm_provider(action="get_status")
    print(status)

# Run setup
setup_development_environment()
```

## Migration Guide

### From Existing LLM Usage

**Before:**
```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Separate instances for different providers
openai_llm = ChatOpenAI(model="gpt-4")
anthropic_llm = ChatAnthropic(model="claude-3-5-sonnet-latest")
```

**After:**
```python
from contexten.extensions.langchain.llm import LLM

# Unified interface for all providers
openai_llm = LLM(model_provider="openai", model_name="gpt-4")
anthropic_llm = LLM(model_provider="anthropic", model_name="claude-3-5-sonnet-latest")
codegen_llm = LLM.with_codegen("org-id", "token", "codegen-agent")

# Or use global configuration
llm = LLM.from_config()  # Uses configured default
```

### Adding Codegen Support to Existing Agents

1. **Update LLM creation:**
   ```python
   # Before
   llm = ChatOpenAI(model="gpt-4")
   
   # After
   llm = LLM.from_config()  # Uses global configuration
   ```

2. **Add configuration tools:**
   ```python
   from contexten.extensions.langchain.llm_tools import get_llm_configuration_tools
   
   # Add to existing tools
   existing_tools = [tool1, tool2, tool3]
   llm_config_tools = get_llm_configuration_tools()
   all_tools = existing_tools + llm_config_tools
   ```

3. **Set Codegen as default:**
   ```python
   from contexten.extensions.langchain.llm_config import configure_codegen_default
   
   # One-time setup
   configure_codegen_default("your-org-id", "your-token")
   ```

## Troubleshooting

### Common Issues

1. **"No LLM providers are available"**
   - Check that at least one provider has valid credentials
   - Use `get_llm_status()` to see which providers are configured

2. **"CODEGEN_ORG_ID not found"**
   - Set environment variable or pass credentials directly
   - Use `LLM.with_codegen(org_id, token)` for direct configuration

3. **"Unknown model provider: codegen"**
   - Ensure Codegen SDK is installed: `pip install codegen`
   - Check that the import path is correct

4. **Configuration not persisting**
   - Save configuration to file: `config.save_to_file()`
   - Check file permissions for config directory

### Debug Information

```python
from contexten.extensions.langchain.llm_config import get_llm_config
from contexten.extensions.langchain.llm_tools import get_llm_status

# Get detailed status
status = get_llm_status()
print(status)

# Check configuration
config = get_llm_config()
print(f"Default provider: {config.default_provider}")
print(f"Available providers: {config.get_available_providers()}")
print(f"Codegen configured: {bool(config.codegen_org_id and config.codegen_token)}")
```

## Best Practices

1. **Use Global Configuration**: Set up global configuration once and use `LLM.from_config()` throughout your application

2. **Environment Variables**: Use environment variables for credentials and basic configuration

3. **Provider Selection**: Use Codegen SDK for code-related tasks, Anthropic for analysis, OpenAI for general tasks

4. **Error Handling**: Always handle provider availability errors gracefully

5. **Configuration Management**: Save configuration to files for persistence across sessions

6. **Security**: Never hardcode credentials; use environment variables or secure configuration files

## Examples

See [`examples/llm_codegen_integration_demo.py`](../examples/llm_codegen_integration_demo.py) for comprehensive examples demonstrating:

- Basic LLM usage with different providers
- Configuration system usage
- Agent function call interfaces
- LangChain tool integration
- Environment and file configuration
- Actual LLM calls and responses

## API Reference

### Classes

- **`LLM`**: Unified chat model supporting all providers
- **`LLMConfig`**: Configuration management class
- **`ChatCodegen`**: LangChain wrapper for Codegen SDK

### Functions

- **`configure_codegen_default()`**: Set Codegen as default provider
- **`get_llm_config()`**: Get global configuration
- **`create_llm_with_config()`**: Create LLM with global config
- **`configure_llm_provider()`**: Universal configuration function
- **`get_llm_configuration_tools()`**: Get LangChain tools

### Tools

- **`SetCodegenDefaultTool`**: LangChain tool to set Codegen as default
- **`SetLLMProviderTool`**: LangChain tool to set any provider
- **`GetLLMStatusTool`**: LangChain tool to get configuration status

