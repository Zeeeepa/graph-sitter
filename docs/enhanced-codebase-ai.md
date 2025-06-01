# Enhanced Codebase AI with Context and Codegen SDK Integration

The enhanced `codebase.ai()` functionality provides powerful AI-driven code analysis, generation, and refactoring capabilities with rich contextual understanding powered by GraphSitter's static analysis.

## Key Features

- **Dual AI Backend Support**: Works with both OpenAI and Codegen SDK
- **Rich Context Gathering**: Leverages GraphSitter's static analysis for comprehensive code understanding
- **Flexible Usage Patterns**: Supports various AI-powered operations (analysis, generation, documentation, refactoring)
- **Async and Sync APIs**: Choose the appropriate interface for your use case
- **Intelligent Context Management**: Automatically gathers relevant code context and relationships

## Quick Start

### 1. Set Up AI Credentials

Choose your preferred AI provider:

```python
from graph_sitter import Codebase

codebase = Codebase("path/to/your/repo")

# Option 1: OpenAI (traditional)
codebase.set_ai_key("your-openai-api-key")

# Option 2: Codegen SDK (recommended)
codebase.set_codegen_credentials("your-org-id", "your-token")
```

### 2. Basic Usage

```python
# Simple AI query
result = await codebase.ai("What does this codebase do?")

# Synchronous version
result = codebase.ai_sync("What does this codebase do?")
```

## Core Functionality

### The `codebase.ai()` Method

```python
async def ai(
    prompt: str,
    target: Optional[Editable] = None,
    context: Optional[Union[str, Editable, List[Editable], Dict[str, Any]]] = None,
    provider: Optional[str] = None,
    include_context: bool = True,
    **kwargs
) -> str
```

**Parameters:**
- `prompt`: The instruction or question for the AI
- `target`: Optional target element (function, class, file) to focus on
- `context`: Additional context (string, Editable objects, or dict)
- `provider`: Preferred AI provider ("openai" or "codegen_sdk")
- `include_context`: Whether to gather and include static analysis context
- `**kwargs`: Additional parameters for AI generation

## Usage Patterns

### 1. Code Analysis with Context

Analyze specific code elements with full contextual understanding:

```python
# Analyze a function
function = codebase.get_function("process_data")
analysis = await codebase.ai(
    "Analyze this function for potential improvements",
    target=function
)

# The AI automatically receives:
# - Function signature and source code
# - Where the function is called (call sites)
# - What the function depends on
# - How the function is used
# - Related functions in the same class/file
```

### 2. Code Generation with Context

Generate new code with awareness of existing codebase patterns:

```python
new_code = await codebase.ai(
    "Create a helper function to validate input data",
    context={
        "style": "defensive programming",
        "return_type": "bool",
        "include_docstring": True
    }
)
```

### 3. Documentation Generation

Generate comprehensive documentation with full context:

```python
class_def = codebase.get_class("MyClass")
for method in class_def.methods:
    docstring = await codebase.ai(
        "Generate a docstring describing this method",
        target=method,
        context={
            "class": class_def,
            "style": "Google docstring format"
        }
    )
    # Apply the docstring to the method
    method.set_docstring(docstring)
```

### 4. Contextual Refactoring

Refactor code while maintaining compatibility and understanding relationships:

```python
method = codebase.get_class("DataProcessor").get_method("transform")
refactored = await codebase.ai(
    "Refactor this method to be more efficient",
    target=method,
    context={
        "parent_class": method.parent,
        "call_sites": method.call_sites,
        "dependencies": method.dependencies,
        "performance_requirements": "handle 10k+ records"
    }
)
method.edit(refactored)
```

### 5. Code Quality Analysis

Analyze code quality with comprehensive understanding:

```python
# Improve function names based on usage
for function in codebase.functions:
    if await codebase.ai(
        "Does this function name clearly describe its purpose? Answer yes/no",
        target=function
    ).lower() == "no":
        new_name = await codebase.ai(
            "Suggest a better name for this function",
            target=function,
            context={"call_sites": function.call_sites}
        )
        function.rename(new_name)
```

## Advanced Context Gathering

The system automatically gathers rich context when `include_context=True`:

### Static Analysis Context
- **Call Sites**: Where the target is called from
- **Dependencies**: What the target depends on
- **Usages**: How the target is used elsewhere
- **Relationships**: Parent/child relationships, siblings

### Contextual Information
- **Target Info**: Type, name, signature, location
- **Source Preview**: Relevant code snippets
- **Codebase Summary**: High-level project overview

### Custom Context

You can provide additional context in multiple formats:

```python
# String context
await codebase.ai(
    "Optimize this function",
    target=function,
    context="Focus on memory efficiency"
)

# Structured context
await codebase.ai(
    "Refactor this method",
    target=method,
    context={
        "requirements": "Must handle edge cases",
        "style": "functional programming",
        "related_functions": [func1, func2]
    }
)

# Multiple targets
await codebase.ai(
    "Compare these functions",
    context=[function1, function2, function3]
)
```

## AI Provider Configuration

### Automatic Provider Selection

The system automatically selects the best available provider:

1. If you specify a `provider` parameter, it uses that (if available)
2. Otherwise, it prefers Codegen SDK if configured
3. Falls back to OpenAI if available
4. Raises an error if no providers are configured

### Provider-Specific Features

**Codegen SDK Benefits:**
- Integrated with Codegen's specialized code understanding
- Optimized for software engineering tasks
- Better handling of large codebases
- Advanced code generation capabilities

**OpenAI Benefits:**
- Familiar API and behavior
- Broad general knowledge
- Fast response times
- Well-established reliability

### Checking Available Providers

```python
from graph_sitter.ai.ai_client_factory import AIClientFactory

available = AIClientFactory.get_available_providers(codebase.ctx.secrets)
print(f"Available providers: {available}")
```

## Configuration and Limits

### Session Options

Control AI usage with session options:

```python
# Set custom AI request limits
codebase.set_session_options(max_ai_requests=200)

# Context size limits
result = await codebase.ai(
    "Analyze this code",
    target=large_function,
    max_context_size=10000  # Limit context to 10k characters
)
```

### Context Management

Fine-tune what context is gathered:

```python
from graph_sitter.ai.context_gatherer import ContextGatherer

gatherer = ContextGatherer(codebase)
context = gatherer.gather_context(
    target=function,
    include_call_sites=True,
    include_dependencies=True,
    include_usages=False,  # Skip usage analysis
    include_related_symbols=True,
    max_context_size=8000
)
```

## Best Practices

### 1. Provide Relevant Context

```python
# Good: Specific, relevant context
summary = await codebase.ai(
    "Generate a summary of this method's purpose",
    target=method,
    context={
        "class": method.parent,
        "usages": list(method.usages),
        "dependencies": method.dependencies,
        "style": "concise"
    }
)

# Less optimal: Missing context
summary = await codebase.ai(
    "Generate a summary",
    target=method  # AI only sees the method's code
)
```

### 2. Use Appropriate Granularity

```python
# For detailed analysis, focus on specific elements
function_analysis = await codebase.ai(
    "Analyze this function for bugs",
    target=specific_function
)

# For high-level insights, provide broader context
architecture_review = await codebase.ai(
    "Review the overall architecture",
    context={"classes": codebase.classes[:10]}
)
```

### 3. Gather Comprehensive Context

```python
def get_method_context(method):
    return {
        "class": method.parent,
        "call_sites": list(method.call_sites),
        "dependencies": list(method.dependencies),
        "related_methods": [m for m in method.parent.methods 
                          if m.name != method.name]
    }

# Use gathered context in AI call
new_impl = await codebase.ai(
    "Refactor this method to be more efficient",
    target=method,
    context=get_method_context(method)
)
```

### 4. Review Generated Code

```python
# Generate and review before applying
new_code = await codebase.ai(
    "Optimize this function",
    target=function
)
print("Review generated code:")
print(new_code)
if input("Apply changes? (y/n): ").lower() == 'y':
    function.edit(new_code)
```

## Error Handling

```python
try:
    result = await codebase.ai("Analyze this code", target=function)
except ValueError as e:
    if "No AI provider credentials" in str(e):
        print("Please set AI credentials first")
    else:
        print(f"AI request failed: {e}")
except MaxAIRequestsError as e:
    print(f"Exceeded AI request limit: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Migration from Legacy AI Method

If you're upgrading from the old `codebase.ai()` method:

### Old Usage
```python
# Legacy method (deprecated)
result = codebase.ai(
    "Analyze this function",
    target=function,
    model="gpt-4"
)
```

### New Usage
```python
# Enhanced method
result = await codebase.ai(
    "Analyze this function",
    target=function,
    provider="openai",  # or "codegen_sdk"
    model="gpt-4"  # passed as kwargs
)

# Or synchronous
result = codebase.ai_sync(
    "Analyze this function",
    target=function
)
```

## Examples and Use Cases

See [`examples/enhanced_codebase_ai_demo.py`](../examples/enhanced_codebase_ai_demo.py) for comprehensive examples demonstrating:

- Code analysis with rich context
- Code generation with contextual awareness
- Documentation generation
- Contextual refactoring
- Code quality analysis
- Provider selection and configuration

## Troubleshooting

### Common Issues

1. **"No AI provider credentials available"**
   - Set either OpenAI or Codegen SDK credentials
   - Verify credentials are correct

2. **"Cannot use ai_sync() from within an async context"**
   - Use `await codebase.ai()` instead of `codebase.ai_sync()`

3. **Context too large**
   - Reduce `max_context_size` parameter
   - Disable some context gathering options

4. **Slow responses**
   - Consider using Codegen SDK for better performance
   - Reduce context size
   - Use more specific targets

### Performance Tips

- Use `include_context=False` for simple queries that don't need context
- Specify `max_context_size` to control response time vs. context richness
- Cache results for repeated similar queries
- Use specific targets rather than broad context when possible

