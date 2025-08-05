# Enhanced Runtime Error Detection for Graph-Sitter LSP

This document describes the comprehensive runtime error detection and analysis capabilities added to the Graph-Sitter LSP extension through enhanced Serena integration.

## Overview

The enhanced SerenaLSPBridge provides comprehensive error detection that goes beyond traditional static analysis to include:

- **Runtime Error Collection**: Capture errors as they occur during code execution
- **Comprehensive Context Analysis**: Full stack traces, variable states, and execution paths
- **Intelligent Fix Suggestions**: AI-powered suggestions based on error patterns
- **Serena Integration**: Full integration with Serena's advanced LSP capabilities
- **Mixed Error Handling**: Unified interface for both static and runtime errors

## Key Features

### 🔥 Runtime Error Collection

The system automatically captures runtime errors using Python's exception handling mechanisms:

```python
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge

# Initialize with runtime collection enabled
bridge = SerenaLSPBridge("/path/to/repo", enable_runtime_collection=True)

# Get all runtime errors
runtime_errors = bridge.get_runtime_errors()

# Get runtime errors for specific file
file_errors = bridge.get_runtime_errors_for_file("my_file.py")
```

### 📊 Enhanced Error Information

Each error includes comprehensive context:

```python
error_info = ErrorInfo(
    file_path="example.py",
    line=10,
    character=5,
    message="AttributeError: 'NoneType' object has no attribute 'value'",
    severity=DiagnosticSeverity.ERROR,
    error_type=ErrorType.RUNTIME_ERROR,
    runtime_context=RuntimeContext(
        exception_type="AttributeError",
        stack_trace=["traceback frames..."],
        local_variables={"obj": "None", "x": "42"},
        execution_path=["main", "process_data", "get_value"],
        timestamp=1234567890.123
    ),
    fix_suggestions=[
        "Check if the object is None before accessing attributes",
        "Add proper initialization",
        "Use getattr() with default value"
    ]
)
```

### 🧠 Intelligent Error Analysis

The system provides intelligent analysis and suggestions:

- **Exception Type Analysis**: Specific suggestions based on error type
- **Context-Aware Suggestions**: Suggestions based on code context and variable states
- **Pattern Recognition**: Common error patterns and their solutions
- **Code Context**: Enhanced code context around error locations

### 🔍 Comprehensive Diagnostics

Unified interface for all error types:

```python
# Get all diagnostics (static + runtime)
all_diagnostics = bridge.get_diagnostics(include_runtime=True)

# Get only static analysis errors
static_errors = bridge.get_static_errors()

# Get only runtime errors
runtime_errors = bridge.get_runtime_errors()

# Get errors with full context
errors_with_context = bridge.get_all_errors_with_context()
```

## Error Types

The system categorizes errors into several types:

### ErrorType Enum

```python
class ErrorType(IntEnum):
    STATIC_ANALYSIS = 1  # Syntax, import, type errors from static analysis
    RUNTIME_ERROR = 2    # Errors that occur during execution
    LINTING = 3         # Code style and quality issues
    SECURITY = 4        # Security vulnerabilities
    PERFORMANCE = 5     # Performance issues
```

### Runtime Context

Runtime errors include comprehensive context:

```python
@dataclass
class RuntimeContext:
    exception_type: str                    # Type of exception (e.g., "AttributeError")
    stack_trace: List[str]                # Full stack trace
    local_variables: Dict[str, Any]       # Local variables at error time
    global_variables: Dict[str, Any]      # Global variables at error time
    execution_path: List[str]             # Function call path
    timestamp: float                      # When the error occurred
    thread_id: Optional[int]              # Thread ID where error occurred
    process_id: Optional[int]             # Process ID where error occurred
```

## Serena Integration

The enhanced bridge integrates with Serena's comprehensive LSP capabilities:

### Available Serena Components

- **SolidLanguageServer**: Advanced LSP server implementation
- **LanguageServerSymbolRetriever**: Symbol analysis and retrieval
- **Project**: Project-level analysis and management
- **LanguageServerLogger**: Comprehensive logging
- **Symbol Analysis**: Advanced symbol intelligence
- **Code Editor Integration**: Direct editor integration

### Enhanced Analysis Features

When Serena is available, errors are enhanced with:

- **Symbol Information**: Detailed symbol analysis at error locations
- **Dependency Analysis**: Understanding of code dependencies
- **Advanced Context**: Enhanced code context with semantic information
- **Intelligent Suggestions**: AI-powered fix suggestions

## Usage Examples

### Basic Runtime Error Collection

```python
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge

# Initialize bridge
bridge = SerenaLSPBridge("/path/to/repo", enable_runtime_collection=True)

# Your code that might have runtime errors
try:
    result = risky_operation()
except Exception:
    pass  # Error is automatically collected

# Get collected errors
runtime_errors = bridge.get_runtime_errors()
for error in runtime_errors:
    print(f"Error: {error.message}")
    print(f"File: {error.file_path}:{error.line}")
    if error.runtime_context:
        print(f"Exception: {error.runtime_context.exception_type}")
        print(f"Variables: {error.runtime_context.local_variables}")
    print(f"Suggestions: {error.fix_suggestions}")
```

### File-Specific Error Analysis

```python
# Get all diagnostics for a specific file
file_diagnostics = bridge.get_file_diagnostics("my_module.py", include_runtime=True)

# Separate by error type
runtime_errors = [d for d in file_diagnostics if d.is_runtime_error]
static_errors = [d for d in file_diagnostics if d.is_static_error]

print(f"Runtime errors: {len(runtime_errors)}")
print(f"Static errors: {len(static_errors)}")
```

### Comprehensive Error Context

```python
# Get errors with full context
errors_with_context = bridge.get_all_errors_with_context()

for error_context in errors_with_context:
    basic_info = error_context['basic_info']
    print(f"Error in {basic_info['file_path']} at line {basic_info['line']}")
    
    if 'runtime' in error_context:
        runtime_info = error_context['runtime']
        print(f"Exception: {runtime_info['exception_type']}")
        print(f"Stack trace: {len(runtime_info['stack_trace'])} frames")
        print(f"Local variables: {runtime_info['local_variables']}")
    
    if 'fix_suggestions' in error_context:
        print(f"Suggestions: {error_context['fix_suggestions']}")
```

### Error Summary and Statistics

```python
# Get runtime error summary
summary = bridge.get_runtime_error_summary()
print(f"Total runtime errors: {summary['total_errors']}")
print(f"Errors by type: {summary['errors_by_type']}")
print(f"Errors by file: {summary['errors_by_file']}")

# Get comprehensive status
status = bridge.get_status()
print(f"Diagnostic counts: {status['diagnostic_counts']}")
print(f"Serena status: {status['serena_status']}")
print(f"Runtime status: {status['runtime_status']}")
```

## Configuration

### Runtime Collection Settings

```python
# Configure runtime error collector
collector = RuntimeErrorCollector("/path/to/repo")
collector.max_errors = 500              # Maximum errors to keep
collector.max_stack_depth = 30          # Maximum stack trace depth
collector.collect_variables = True      # Collect variable states
collector.variable_max_length = 100     # Maximum variable string length
```

### Bridge Configuration

```python
# Initialize with custom settings
bridge = SerenaLSPBridge(
    repo_path="/path/to/repo",
    enable_runtime_collection=True
)

# Access runtime collector for configuration
if bridge.runtime_collector:
    bridge.runtime_collector.max_errors = 1000
    bridge.runtime_collector.collect_variables = True
```

## Error Management

### Clearing Errors

```python
# Clear all runtime errors
bridge.clear_runtime_errors()

# Clear specific file errors (manual filtering)
all_errors = bridge.get_runtime_errors()
filtered_errors = [e for e in all_errors if e.file_path != "unwanted_file.py"]
bridge.clear_runtime_errors()
# Re-add filtered errors if needed
```

### Error Handlers

```python
def my_error_handler(error_info):
    print(f"New runtime error: {error_info.message}")
    # Custom processing...

# Add error handler
if bridge.runtime_collector:
    bridge.runtime_collector.add_error_handler(my_error_handler)
```

## Performance Considerations

### Memory Management

- Runtime errors are limited by `max_errors` setting (default: 1000)
- Variable collection can be disabled for better performance
- Stack trace depth is limited by `max_stack_depth` setting

### Thread Safety

- All operations are thread-safe using RLock
- Runtime error collection works across multiple threads
- Thread ID is captured for each error

### Impact on Execution

- Minimal performance impact during normal execution
- Error collection only activates when exceptions occur
- Variable collection adds slight overhead but provides valuable context

## Integration with Existing Systems

### LSP Protocol Compatibility

The enhanced bridge maintains full compatibility with LSP protocol:

- Standard diagnostic messages
- Position and range information
- Severity levels (Error, Warning, Information, Hint)
- Source attribution

### Graph-Sitter Integration

Seamless integration with Graph-Sitter's transaction system:

- Automatic diagnostic updates on file changes
- Transaction-aware error management
- Codebase-wide error analysis

### IDE Integration

Works with any LSP-compatible editor:

- VS Code
- Neovim with LSP
- Emacs with LSP
- Sublime Text with LSP
- Any editor supporting Language Server Protocol

## Troubleshooting

### Common Issues

1. **Runtime collection not working**
   - Ensure `enable_runtime_collection=True`
   - Check that the collector is started: `collector._active`
   - Verify exception hooks are installed

2. **Missing Serena features**
   - Check `SERENA_AVAILABLE` flag
   - Ensure Serena modules are properly installed
   - Review initialization logs

3. **Performance issues**
   - Reduce `max_errors` setting
   - Disable variable collection: `collect_variables=False`
   - Reduce stack trace depth: `max_stack_depth=20`

### Debug Information

```python
# Get comprehensive status for debugging
status = bridge.get_status()
print("Debug Information:")
print(f"  Initialized: {status['initialized']}")
print(f"  Runtime collection: {status['runtime_collection_enabled']}")
print(f"  Serena available: {status['serena_status']['serena_available']}")
print(f"  Language servers: {status['language_servers']}")
print(f"  Cache sizes: {status['cache_sizes']}")
```

## API Reference

### SerenaLSPBridge Methods

#### Error Retrieval
- `get_diagnostics(include_runtime=True)` - Get all diagnostics
- `get_runtime_errors()` - Get only runtime errors
- `get_static_errors()` - Get only static analysis errors
- `get_file_diagnostics(file_path, include_runtime=True)` - Get file-specific diagnostics
- `get_runtime_errors_for_file(file_path)` - Get runtime errors for specific file
- `get_all_errors_with_context()` - Get errors with full context

#### Error Management
- `clear_runtime_errors()` - Clear all runtime errors
- `get_runtime_error_summary()` - Get runtime error statistics
- `get_status()` - Get comprehensive status information

#### Lifecycle
- `shutdown()` - Shutdown all components and clean up resources

### RuntimeErrorCollector Methods

#### Collection Control
- `start_collection()` - Start collecting runtime errors
- `stop_collection()` - Stop collecting runtime errors

#### Error Access
- `get_runtime_errors()` - Get all collected errors
- `get_runtime_errors_for_file(file_path)` - Get errors for specific file
- `get_error_summary()` - Get error statistics

#### Configuration
- `add_error_handler(handler)` - Add custom error handler
- `remove_error_handler(handler)` - Remove error handler
- `clear_runtime_errors()` - Clear all collected errors

### ErrorInfo Properties

#### Basic Properties
- `file_path` - File where error occurred
- `line` - Line number (0-based)
- `character` - Character position
- `message` - Error message
- `severity` - Error severity level
- `error_type` - Type of error (static/runtime/etc.)

#### Runtime Properties
- `runtime_context` - Runtime context information
- `fix_suggestions` - List of fix suggestions
- `symbol_info` - Symbol information (when Serena available)
- `code_context` - Code context around error

#### Helper Methods
- `is_error` - Check if severity is ERROR
- `is_warning` - Check if severity is WARNING
- `is_runtime_error` - Check if this is a runtime error
- `is_static_error` - Check if this is a static analysis error
- `get_full_context()` - Get comprehensive context dictionary

## Examples and Demos

See the following files for complete examples:

- `examples/enhanced_runtime_error_demo.py` - Comprehensive demonstration
- `tests/unit/extensions/lsp/test_enhanced_serena_bridge.py` - Unit tests
- `src/graph_sitter/extensions/lsp/serena_bridge.py` - Implementation

## Future Enhancements

Planned improvements include:

- **Machine Learning Integration**: Pattern recognition for common error types
- **Performance Profiling**: Integration with performance monitoring
- **Security Analysis**: Enhanced security vulnerability detection
- **Code Quality Metrics**: Integration with code quality analysis
- **Real-time Collaboration**: Multi-developer error sharing
- **IDE-Specific Features**: Enhanced integration with specific editors

## Contributing

To contribute to the enhanced runtime error detection:

1. Review the existing implementation in `serena_bridge.py`
2. Add tests in `test_enhanced_serena_bridge.py`
3. Update documentation as needed
4. Ensure compatibility with existing LSP protocol
5. Test with various error scenarios

## License

This enhancement is part of the Graph-Sitter project and follows the same licensing terms.

