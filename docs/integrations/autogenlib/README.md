# AutogenLib Integration for Graph-Sitter

This document describes the integration of [autogenlib](https://github.com/Zeeeepa/autogenlib) with graph-sitter to provide enhanced generative features for missing implementations.

## Overview

The AutogenLib integration extends graph-sitter's code analysis capabilities with dynamic code generation powered by OpenAI's API. This integration provides:

- **Automatic code completion** for missing implementations
- **Intelligent code suggestions** based on context
- **Pattern-based code generation** using successful patterns
- **Template-driven development** assistance
- **Context-aware refactoring** suggestions

## Features

### Enhanced Context Provision

The integration leverages graph-sitter's deep code analysis to provide rich context to autogenlib:

- **AST Analysis**: Full abstract syntax tree analysis of existing code
- **Symbol Information**: Type information, function signatures, and symbol relationships
- **Dependency Analysis**: Understanding of module dependencies and imports
- **Pattern Recognition**: Identification of common coding patterns and conventions
- **Caller Code Analysis**: Analysis of how generated code will be used

### Dynamic Code Generation

- **On-demand Generation**: Generate code when importing non-existent modules/functions
- **Context-Aware**: Generated code follows existing patterns and conventions
- **Incremental Enhancement**: Add new functionality to existing modules seamlessly
- **Template Support**: Predefined templates for common code structures

### Caching and Performance

- **Intelligent Caching**: Cache generated code with context-aware invalidation
- **Pattern Storage**: Store successful generation patterns for reuse
- **Performance Metrics**: Track generation success rates and performance

### Database Integration

- **Generation History**: Store complete history of code generations
- **Pattern Analytics**: Analyze successful patterns for improvement
- **Cache Management**: Efficient caching with expiration and hit tracking
- **Metrics Collection**: Comprehensive analytics and reporting

## Installation

The integration is included with graph-sitter when autogenlib is available:

```bash
pip install graph-sitter[autogenlib]
```

Or install autogenlib separately:

```bash
pip install autogenlib>=0.1.3
```

## Configuration

### Basic Configuration

Create a configuration file or use environment variables:

```json
{
  "enabled": true,
  "openai_api_key": "your-openai-api-key",
  "openai_model": "gpt-4",
  "enable_caching": true,
  "use_graph_sitter_context": true,
  "max_context_size": 10000,
  "allowed_namespaces": ["autogenlib.generated"]
}
```

### Environment Variables

```bash
export GRAPH_SITTER_AUTOGENLIB_ENABLED=true
export GRAPH_SITTER_AUTOGENLIB_OPENAI_API_KEY=your-key
export GRAPH_SITTER_AUTOGENLIB_OPENAI_MODEL=gpt-4
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | false | Enable autogenlib integration |
| `openai_api_key` | str | None | OpenAI API key |
| `openai_model` | str | "gpt-4" | OpenAI model to use |
| `openai_api_base_url` | str | None | Custom OpenAI API base URL |
| `enable_caching` | bool | true | Enable code caching |
| `use_graph_sitter_context` | bool | true | Use graph-sitter for context |
| `max_context_size` | int | 10000 | Maximum context size in characters |
| `temperature` | float | 0.1 | Generation temperature |
| `allowed_namespaces` | list | ["autogenlib.generated"] | Allowed generation namespaces |

## Usage

### CLI Commands

#### Initialize Configuration

```bash
gs autogenlib config init --interactive
```

#### Generate Code

```bash
gs autogenlib generate \
  --module-name "myproject.utils.helpers" \
  --function-name "format_data" \
  --description "Format data for API response" \
  --output "src/myproject/utils/helpers.py"
```

#### View Statistics

```bash
gs autogenlib stats overview
gs autogenlib stats history --limit 20
gs autogenlib stats cache
```

### Programmatic Usage

```python
from graph_sitter.integrations.autogenlib import (
    AutogenLibIntegration,
    AutogenLibConfig
)

# Configure integration
config = AutogenLibConfig(
    enabled=True,
    openai_api_key="your-key",
    use_graph_sitter_context=True
)

# Initialize integration
integration = AutogenLibIntegration(config)

# Generate missing implementation
result = integration.generate_missing_implementation(
    module_name="myproject.utils.helpers",
    function_name="format_data",
    description="Format data for API response with validation"
)

if result.success:
    print("Generated code:")
    print(result.code)
else:
    print(f"Generation failed: {result.error}")
```

### Template-Based Generation

```python
# Generate a data model class
result = integration.generate_template_code(
    template_type="data_model",
    parameters={
        "class_name": "UserProfile",
        "fields": ["name", "email", "age"],
        "validation": True
    }
)

# Generate API client
result = integration.generate_template_code(
    template_type="api_client",
    parameters={
        "base_url": "https://api.example.com",
        "endpoints": ["users", "posts", "comments"],
        "auth_type": "bearer"
    }
)
```

### Code Completion

```python
# Get code completion suggestions
suggestions = integration.suggest_code_completion(
    context="def process_data(data):\n    # ",
    cursor_position=25,
    max_suggestions=5
)

for suggestion in suggestions:
    print(f"{suggestion['type']}: {suggestion['description']}")
    print(f"Code: {suggestion['text']}")
```

### Refactoring Suggestions

```python
# Get refactoring suggestions
suggestions = integration.generate_refactoring_suggestions(
    code=existing_code,
    target_pattern="clean_code"
)

for suggestion in suggestions:
    print(f"{suggestion['type']}: {suggestion['description']}")
    print(f"Confidence: {suggestion['confidence']}")
```

## Database Schema

The integration creates several database tables for storing generation data:

### Tables

- **generation_history**: Complete history of all generations
- **generation_patterns**: Successful patterns for reuse
- **generation_cache**: Cached generated code
- **generation_metrics**: Analytics and performance metrics

### Views

- **generation_stats**: Daily generation statistics
- **popular_patterns**: Most successful patterns
- **cache_performance**: Cache hit rates and performance

## Best Practices

### Security

1. **Namespace Restrictions**: Limit generation to specific namespaces
2. **API Key Management**: Use environment variables for API keys
3. **Code Review**: Always review generated code before production use
4. **Rate Limiting**: Be mindful of OpenAI API rate limits

### Performance

1. **Context Size**: Optimize context size for better performance
2. **Caching**: Enable caching for frequently generated code
3. **Pattern Reuse**: Leverage successful patterns for consistency
4. **Batch Operations**: Use batch operations for multiple generations

### Quality

1. **Descriptive Prompts**: Provide clear, detailed descriptions
2. **Context Provision**: Include relevant existing code context
3. **Pattern Analysis**: Review and refine successful patterns
4. **Testing**: Generate comprehensive tests for generated code

## Troubleshooting

### Common Issues

#### Integration Not Enabled

```bash
# Check configuration
gs autogenlib config show

# Validate configuration
gs autogenlib config validate

# Test configuration
gs autogenlib config test
```

#### Generation Failures

1. Check OpenAI API key and quota
2. Verify network connectivity
3. Review context size limits
4. Check allowed namespaces

#### Performance Issues

1. Reduce context size
2. Enable caching
3. Use pattern-based generation
4. Optimize database queries

### Debugging

Enable verbose logging:

```python
import logging
logging.getLogger('graph_sitter.integrations.autogenlib').setLevel(logging.DEBUG)
```

View generation history:

```bash
gs autogenlib stats history --verbose
```

## Examples

### Example 1: Utility Function Generation

```python
# Generate a utility function for data validation
result = integration.generate_missing_implementation(
    module_name="myproject.utils.validation",
    function_name="validate_email",
    description="Validate email address format with regex"
)
```

### Example 2: API Client Generation

```python
# Generate an API client class
result = integration.generate_template_code(
    template_type="api_client",
    parameters={
        "service_name": "UserService",
        "base_url": "https://api.users.com",
        "endpoints": {
            "get_user": "GET /users/{id}",
            "create_user": "POST /users",
            "update_user": "PUT /users/{id}",
            "delete_user": "DELETE /users/{id}"
        },
        "authentication": "bearer_token"
    }
)
```

### Example 3: Test Generation

```python
# Generate tests for existing code
result = integration.generate_template_code(
    template_type="test",
    parameters={
        "test_file": "test_user_service.py",
        "target_module": "myproject.services.user_service",
        "test_framework": "pytest",
        "coverage_target": 90
    }
)
```

## Contributing

To contribute to the AutogenLib integration:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

This integration is part of graph-sitter and follows the same license terms.

