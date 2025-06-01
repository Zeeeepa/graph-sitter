# Enhanced Codebase AI with Context-Aware Analysis

This document describes the enhanced `codebase_ai` functionality that transforms basic prompt generation into a powerful AI-driven codebase analysis and manipulation system.

## 🚀 Key Features

### Dual AI Backend Support
- **Codegen SDK Integration**: Native support for Codegen org_id/token authentication
- **OpenAI Compatibility**: Maintains existing OpenAI API support
- **Automatic Provider Selection**: Intelligent fallback and preference handling

### Rich Context Awareness
- **Static Analysis Integration**: Leverages GraphSitter's analysis for comprehensive code understanding
- **Automatic Context Gathering**: Call sites, dependencies, usages, and relationships
- **Flexible Context Input**: Support for strings, Editable objects, lists, and dictionaries
- **Context Size Management**: Intelligent truncation and optimization

### Enhanced AI Methods
- **Async `codebase.ai()`**: Primary method with full context awareness
- **Sync `codebase.ai_sync()`**: Convenience method for non-async contexts
- **Rich Response Handling**: Structured responses with metadata and performance metrics

## 📖 Usage Examples

### Basic Setup

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("path/to/your/project")

# Set credentials (choose one)
codebase.set_ai_key("your-openai-api-key")
codebase.set_codegen_credentials("your-org-id", "your-token")
```

### Simple AI Query

```python
# Async usage (recommended)
result = await codebase.ai("What does this codebase do?")
print(result.content)  # The AI response
print(result.provider)  # "codegen" or "openai"
print(result.response_time)  # Response time in seconds

# Sync usage
result = codebase.ai_sync("What does this codebase do?")
print(result.content)
```

### Context-Aware Analysis

```python
# Analyze a function with full context
function = codebase.get_function("process_data")
analysis = await codebase.ai(
    "Analyze this function for potential improvements",
    target=function  # Automatically includes call sites, dependencies, etc.
)

print(f"Analysis: {analysis.content}")
print(f"Context size: {analysis.context_size} characters")
```

### Code Generation with Context

```python
# Generate code with contextual awareness
new_code = await codebase.ai(
    "Create a helper function to validate input data",
    context={
        "style": "defensive programming",
        "return_type": "bool",
        "include_docstring": True
    }
)

print(f"Generated code: {new_code.content}")
```

### Documentation Generation

```python
# Generate docstrings with full context
class_def = codebase.get_class("MyClass")
for method in class_def.methods:
    docstring = await codebase.ai(
        "Generate a docstring describing this method",
        target=method,
        context={"style": "Google docstring format"}
    )
    # Apply the docstring
    method.set_docstring(docstring.content)
```

## 🔧 Implementation Details

### New Components

#### AIClientFactory
Unified client creation and provider management with automatic fallback:

```python
from graph_sitter.ai.client_factory import AIClientFactory

client, provider = AIClientFactory.create_client(
    openai_api_key="your-key",
    codegen_org_id="your-org-id",
    codegen_token="your-token",
    prefer_codegen=True
)
```

#### ContextGatherer
Rich context extraction from GraphSitter analysis:

```python
from graph_sitter.ai.context_gatherer import ContextGatherer

gatherer = ContextGatherer(codebase)
context = gatherer.gather_target_context(target)
formatted = gatherer.format_context_for_prompt(context)
```

#### Enhanced SecretsConfig
Added `codegen_org_id` and `codegen_token` fields:

```python
# Environment variables or .env file
CODEGEN_ORG_ID=your-org-id
CODEGEN_TOKEN=your-token
```

#### AIResponse Class
Structured responses with metadata:

```python
class AIResponse:
    content: str           # The AI response content
    provider: str          # "codegen" or "openai"
    model: str            # Model used
    tokens_used: int      # Tokens consumed
    response_time: float  # Response time in seconds
    context_size: int     # Context size in characters
    metadata: dict        # Additional metadata
```

### Context Gathering

The system automatically gathers:

- **Target Information**: Type, name, signature, location, source preview
- **Static Analysis**: Call sites, dependencies, usages with code context
- **Relationships**: Parent/child relationships, sibling methods/functions
- **Codebase Summary**: High-level project overview
- **User Context**: Custom context in multiple formats

### Async Infrastructure

Full async/await support with sync convenience methods:

```python
# Async (recommended for new code)
result = await codebase.ai("prompt")

# Sync (for compatibility)
result = codebase.ai_sync("prompt")

# Legacy (backward compatibility)
result = codebase.ai_legacy("prompt")  # Returns string
```

## 🎛️ Configuration Options

### Context Control

```python
result = await codebase.ai(
    "Analyze this function",
    target=function,
    include_context=True,        # Enable rich context gathering
    max_context_tokens=8000      # Limit context size
)
```

### Provider Preference

```python
# Prefer Codegen SDK
codebase.set_codegen_credentials("org-id", "token")

# Fallback to OpenAI if Codegen unavailable
codebase.set_ai_key("openai-key")
```

### Model Selection

```python
result = await codebase.ai(
    "prompt",
    model="gpt-4o"  # or any supported model
)
```

## 🔄 Migration Guide

### From Legacy AI Method

**Before:**
```python
result = codebase.ai("prompt", target=function)  # Returns string
```

**After:**
```python
# Option 1: Use new async method
result = await codebase.ai("prompt", target=function)
print(result.content)  # Access content

# Option 2: Use sync method
result = codebase.ai_sync("prompt", target=function)
print(result.content)  # Access content

# Option 3: Keep legacy behavior
result = codebase.ai_legacy("prompt", target=function)  # Still returns string
```

### Enhanced Context

**Before:**
```python
result = codebase.ai("analyze function", target=function)
```

**After:**
```python
# Rich context automatically included
result = await codebase.ai("analyze function", target=function)

# Disable rich context if needed
result = await codebase.ai("analyze function", target=function, include_context=False)
```

## 🚨 Error Handling

```python
try:
    result = await codebase.ai("prompt")
    print(f"Success: {result.content}")
except ValueError as e:
    print(f"AI request failed: {e}")
except ImportError as e:
    print(f"Codegen SDK not available: {e}")
```

## 📊 Performance Monitoring

```python
result = await codebase.ai("prompt", target=function)

print(f"Provider: {result.provider}")
print(f"Model: {result.model}")
print(f"Response time: {result.response_time:.2f}s")
print(f"Context size: {result.context_size} chars")
print(f"Tokens used: {result.tokens_used}")
```

## 🔗 Integration Examples

### With Existing Workflows

```python
# Document all functions
for function in codebase.functions:
    if not function.docstring:
        docstring = await codebase.ai(
            "Generate a comprehensive docstring",
            target=function
        )
        function.set_docstring(docstring.content)

# Analyze code quality
for class_def in codebase.classes:
    analysis = await codebase.ai(
        "Analyze this class for design patterns and potential improvements",
        target=class_def
    )
    print(f"Class {class_def.name}: {analysis.content}")
```

### Batch Processing

```python
import asyncio

async def analyze_functions(functions):
    tasks = []
    for func in functions:
        task = codebase.ai(
            "Suggest improvements for this function",
            target=func
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

# Analyze multiple functions concurrently
results = await analyze_functions(codebase.functions[:10])
```

## 🛠️ Troubleshooting

### Common Issues

1. **No credentials provided**
   ```python
   # Solution: Set credentials
   codebase.set_codegen_credentials("org-id", "token")
   # or
   codebase.set_ai_key("openai-key")
   ```

2. **Codegen SDK not available**
   ```bash
   pip install codegen
   ```

3. **Context too large**
   ```python
   # Reduce context size
   result = await codebase.ai("prompt", max_context_tokens=4000)
   ```

4. **Async/sync issues**
   ```python
   # Use ai_sync for non-async contexts
   result = codebase.ai_sync("prompt")
   ```

## 📚 API Reference

### Codebase Methods

- `codebase.ai(prompt, target=None, context=None, model="gpt-4o", include_context=True, max_context_tokens=8000)` → `AIResponse`
- `codebase.ai_sync(...)` → `AIResponse`
- `codebase.ai_legacy(...)` → `str`
- `codebase.set_codegen_credentials(org_id, token)` → `None`
- `codebase.set_ai_key(key)` → `None`

### AIResponse Properties

- `content: str` - The AI response content
- `provider: str` - AI provider used ("codegen" or "openai")
- `model: str` - Model used for generation
- `tokens_used: int` - Number of tokens consumed
- `response_time: float` - Response time in seconds
- `context_size: int` - Size of context in characters
- `metadata: dict` - Additional metadata

This enhanced system provides a powerful foundation for AI-driven codebase analysis and manipulation while maintaining backward compatibility with existing code.

