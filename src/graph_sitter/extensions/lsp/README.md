# Enhanced Serena LSP Bridge for Graph-Sitter

This enhanced LSP bridge provides comprehensive error detection and analysis capabilities for graph-sitter, combining static analysis with optional runtime error collection and Serena LSP integration.

## Features

### Core Capabilities
- **Static Analysis Integration**: Traditional LSP diagnostics from language servers
- **Runtime Error Collection**: Real-time capture of runtime exceptions with full context
- **Serena LSP Integration**: Optional integration with Serena's solidlsp components
- **Enhanced Error Context**: Comprehensive error information with fix suggestions
- **Thread-Safe Operations**: Safe for use in multi-threaded environments

### Error Types Supported
- **Static Analysis Errors**: Syntax, import, type errors from static analysis
- **Runtime Errors**: Exceptions that occur during code execution
- **Linting Issues**: Code style and quality problems
- **Security Vulnerabilities**: Security-related issues (when available)
- **Performance Issues**: Performance-related problems (when available)

### Runtime Error Context
When runtime error collection is enabled, each error includes:
- **Exception Details**: Type, message, and stack trace
- **Variable State**: Local and global variables at time of error
- **Execution Path**: Function call chain leading to the error
- **Fix Suggestions**: Intelligent suggestions based on error type
- **Timing Information**: Timestamp, thread ID, process ID

## Installation

### Basic Installation
The LSP extension is included with graph-sitter. For basic functionality:

```bash
pip install graph-sitter[lsp]
```

### Enhanced Serena Integration
For full Serena LSP integration, install additional components:

```bash
# Option 1: Install via git (recommended)
pip install git+https://github.com/serena-ai/solidlsp.git

# Option 2: Install via uvx
uvx install serena-mcp-server

# Option 3: Install with enhanced dependencies
pip install graph-sitter[lsp,serena]
```

## Usage

### Basic Usage

```python
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge

# Initialize with basic functionality
lsp_bridge = SerenaLSPBridge("/path/to/your/repo")

# Get static analysis errors
static_errors = lsp_bridge.get_static_errors()
for error in static_errors:
    print(f"{error.severity.name}: {error.message} at {error.file_path}:{error.line}")
```

### Runtime Error Collection

```python
# Initialize with runtime error collection enabled
lsp_bridge = SerenaLSPBridge(
    repo_path="/path/to/your/repo",
    enable_runtime_collection=True
)

# Your code that might have runtime errors
try:
    # Some code that might fail
    result = risky_operation()
except Exception:
    pass  # Error will be automatically collected

# Get runtime errors with full context
runtime_errors = lsp_bridge.get_runtime_errors()
for error in runtime_errors:
    print(f"Runtime Error: {error.message}")
    if error.runtime_context:
        print(f"  Exception Type: {error.runtime_context.exception_type}")
        print(f"  Local Variables: {error.runtime_context.local_variables}")
        print(f"  Fix Suggestions: {error.fix_suggestions}")

# Always shutdown when done
lsp_bridge.shutdown()
```

### Comprehensive Error Analysis

```python
# Get all errors with full context
all_errors = lsp_bridge.get_all_errors_with_context()
for error_context in all_errors:
    basic_info = error_context['basic_info']
    print(f"Error in {basic_info['file_path']}:{basic_info['line']}")
    print(f"Message: {basic_info['message']}")
    
    # Runtime context (if available)
    if 'runtime' in error_context:
        runtime = error_context['runtime']
        print(f"Exception: {runtime['exception_type']}")
        print(f"Execution Path: {' -> '.join(runtime['execution_path'])}")
    
    # Fix suggestions
    for suggestion in error_context['fix_suggestions']:
        print(f"  Suggestion: {suggestion}")
```

### File-Specific Diagnostics

```python
# Get diagnostics for a specific file
file_path = "/path/to/your/file.py"
file_errors = lsp_bridge.get_file_diagnostics(file_path, include_runtime=True)

print(f"Found {len(file_errors)} issues in {file_path}")
for error in file_errors:
    if error.is_runtime_error:
        print(f"  Runtime Error: {error.message}")
    else:
        print(f"  Static Error: {error.message}")
```

## API Reference

### SerenaLSPBridge

#### Constructor
```python
SerenaLSPBridge(repo_path: str, enable_runtime_collection: bool = False)
```

#### Core Methods

##### Error Retrieval
- `get_diagnostics(include_runtime: bool = True) -> List[ErrorInfo]`
  - Get all diagnostics (static + runtime)
- `get_static_errors() -> List[ErrorInfo]`
  - Get only static analysis errors
- `get_runtime_errors() -> List[ErrorInfo]`
  - Get only runtime errors
- `get_file_diagnostics(file_path: str, include_runtime: bool = True) -> List[ErrorInfo]`
  - Get diagnostics for a specific file

##### Runtime Error Management
- `get_runtime_errors_for_file(file_path: str) -> List[ErrorInfo]`
  - Get runtime errors for a specific file
- `clear_runtime_errors() -> None`
  - Clear all collected runtime errors
- `get_runtime_error_summary() -> Dict[str, Any]`
  - Get summary statistics about runtime errors

##### Context and Analysis
- `get_all_errors_with_context() -> List[Dict[str, Any]]`
  - Get all errors with comprehensive context information
- `get_status() -> Dict[str, Any]`
  - Get comprehensive status information
- `shutdown() -> None`
  - Shutdown and clean up all resources

### ErrorInfo

Enhanced error information class with the following properties:

#### Basic Properties
- `file_path: str` - Path to the file containing the error
- `line: int` - Line number (0-based)
- `character: int` - Character position
- `message: str` - Error message
- `severity: DiagnosticSeverity` - Error severity level

#### Enhanced Properties
- `error_type: Optional[ErrorType]` - Type of error (static, runtime, etc.)
- `runtime_context: Optional[RuntimeContext]` - Runtime execution context
- `fix_suggestions: List[str]` - Intelligent fix suggestions
- `symbol_info: Optional[Dict[str, Any]]` - Symbol information
- `code_context: Optional[str]` - Code context around the error

#### Methods
- `is_error() -> bool` - Check if this is an error (not warning/hint)
- `is_runtime_error() -> bool` - Check if this is a runtime error
- `is_static_error() -> bool` - Check if this is a static analysis error
- `get_full_context() -> Dict[str, Any]` - Get comprehensive context

### RuntimeContext

Runtime execution context for errors:

- `exception_type: str` - Type of exception
- `stack_trace: List[str]` - Full stack trace
- `local_variables: Dict[str, Any]` - Local variables at error time
- `global_variables: Dict[str, Any]` - Global variables at error time
- `execution_path: List[str]` - Function call chain
- `timestamp: float` - When the error occurred
- `thread_id: Optional[int]` - Thread identifier
- `process_id: Optional[int]` - Process identifier

## Configuration

### Runtime Error Collection Settings

The runtime error collector can be configured:

```python
# Access the runtime collector directly
if lsp_bridge.runtime_collector:
    collector = lsp_bridge.runtime_collector
    
    # Configure collection limits
    collector.max_errors = 500  # Maximum errors to keep
    collector.max_stack_depth = 30  # Maximum stack trace depth
    collector.collect_variables = True  # Whether to collect variable state
    collector.variable_max_length = 100  # Maximum variable string length
```

### Serena Integration

When Serena components are available, additional capabilities are enabled:

- **Symbol Retrieval**: Enhanced symbol information
- **Project Analysis**: Project-wide analysis capabilities
- **Advanced LSP Features**: Additional language server features

## Error Handling and Graceful Degradation

The enhanced LSP bridge is designed to gracefully handle missing dependencies:

- **No Serena Components**: Falls back to basic LSP functionality
- **No Runtime Collection**: Only static analysis is available
- **Partial Serena Installation**: Uses available components only

## Examples

See the `examples/` directory for comprehensive usage examples:

- `runtime_error_example.py` - Complete demonstration of runtime error collection
- Additional examples for specific use cases

## Thread Safety

All operations are thread-safe and can be used in multi-threaded environments:

- Internal locking prevents race conditions
- Runtime error collection works across threads
- Safe shutdown from any thread

## Performance Considerations

- **Memory Usage**: Runtime error collection has configurable limits
- **Variable Collection**: Can be disabled for better performance
- **Stack Trace Depth**: Configurable to balance detail vs. performance
- **Error Caching**: Efficient caching of diagnostic information

## Troubleshooting

### Common Issues

1. **Runtime Collection Not Working**
   - Ensure `enable_runtime_collection=True`
   - Check that `RuntimeErrorCollector` is available
   - Verify errors are being generated in repo files

2. **Serena Integration Issues**
   - Install Serena components: `pip install git+https://github.com/serena-ai/solidlsp.git`
   - Check status with `lsp_bridge.get_status()`
   - Review logs for initialization errors

3. **Performance Issues**
   - Reduce `max_errors` limit
   - Disable variable collection: `collect_variables = False`
   - Reduce stack trace depth: `max_stack_depth = 10`

### Debug Information

```python
# Get comprehensive status
status = lsp_bridge.get_status()
print("LSP Bridge Status:")
print(f"  Initialized: {status['initialized']}")
print(f"  Runtime Collection: {status['runtime_collection']}")
print(f"  Serena Components: {status['serena_components']}")
print(f"  Capabilities: {status['capabilities']}")
```

## Contributing

When contributing to the enhanced LSP bridge:

1. Maintain backward compatibility
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Follow the graceful degradation pattern for optional dependencies

## License

This enhanced LSP bridge follows the same license as the main graph-sitter project.

