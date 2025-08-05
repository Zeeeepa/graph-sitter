# Graph-Sitter LSP Extension with Runtime Error Collection

A comprehensive Language Server Protocol (LSP) extension for Graph-Sitter that provides advanced runtime error collection, context analysis, and intelligent fix suggestions with optional Serena integration.

## Features

### 🔥 Core Capabilities
- **Runtime Error Collection**: Real-time capture of Python runtime errors using exception hooks
- **Comprehensive Context Analysis**: Full stack traces, variable states, and execution paths
- **Intelligent Fix Suggestions**: Context-aware recommendations based on error types and patterns
- **Static Error Management**: Integration with static analysis tools and linters
- **Thread-Safe Operations**: Proper resource management and concurrent access handling

### 🚀 Advanced Features
- **Serena LSP Integration**: Optional integration with Serena's solidlsp for enhanced capabilities
- **Protocol Extensions**: Custom LSP methods for advanced error retrieval and management
- **Performance Monitoring**: Detailed statistics and performance tracking
- **Graceful Fallback**: Works with basic LSP functionality when Serena is unavailable
- **Configurable Collection**: Tunable parameters for performance optimization

### 📊 Error Analysis
- **Multi-Type Error Support**: Static analysis, runtime, linting, security, and performance errors
- **Rich Context Information**: Variable states, execution paths, and dependency analysis
- **Error Classification**: Automatic categorization and severity assessment
- **Fix Suggestion Engine**: Pattern-based intelligent recommendations

## Installation

### Basic Installation

```bash
# Install with LSP support
pip install graph-sitter[lsp]
```

### With Serena Integration

```bash
# Install with Serena support (optional)
pip install graph-sitter[lsp,serena]

# Or install Serena components separately
pip install git+https://github.com/serena-ai/solidlsp.git
# or
uvx install serena-mcp-server
```

### Dependencies

The extension requires:
- `pygls>=2.0.0a2` - Language Server Protocol implementation
- `lsprotocol==2024.0.0b1` - LSP protocol types
- `attrs>=25.1.0` - Attribute classes

Optional Serena dependencies:
- `mcp>=1.0.0` - MCP client library
- `typing-extensions>=4.12.2` - Enhanced type hints
- `dataclasses-json>=0.6.4` - Serialization support

## Quick Start

### Basic Usage

```python
from graph_sitter.extensions.lsp.serena_bridge import create_serena_bridge

# Create LSP bridge with runtime error collection
bridge = create_serena_bridge("/path/to/your/repo", enable_runtime_collection=True)

# Get all errors (static + runtime)
all_errors = bridge.get_all_errors()

# Get error summary
summary = bridge.get_error_summary()
print(f"Total errors: {summary['total_errors']}")
print(f"Runtime errors: {summary['runtime_errors']}")

# Cleanup
bridge.shutdown()
```

### Runtime Error Collection

```python
from graph_sitter.extensions.lsp.runtime_collector import create_runtime_collector

# Create standalone runtime collector
collector = create_runtime_collector("/path/to/repo", auto_start=True)

# Configure collection parameters
collector.configure_collection(
    max_errors=1000,
    collect_variables=True,
    variable_max_length=200
)

# Get collected errors
runtime_errors = collector.get_runtime_errors()

# Get collection statistics
stats = collector.get_collection_stats()
print(f"Average collection time: {stats['average_collection_time']:.3f}s")

# Cleanup
collector.shutdown()
```

### Protocol Extension

```python
from graph_sitter.extensions.lsp.serena_protocol import create_serena_protocol_extension

# Create protocol extension
extension = create_serena_protocol_extension("/path/to/repo")

# Add notification callback
def handle_notification(notification):
    print(f"Received: {notification['method']}")

extension.add_notification_callback(handle_notification)

# Handle LSP requests
response = extension.handle_request('serena/getAllErrors', {})
if not response['error']:
    errors = response['result']['errors']
    print(f"Found {len(errors)} errors")

# Cleanup
extension.shutdown()
```

## API Reference

### SerenaLSPBridge

The main bridge class that coordinates all functionality.

#### Constructor

```python
SerenaLSPBridge(repo_path: str, enable_runtime_collection: bool = True)
```

#### Key Methods

```python
# Error retrieval
get_all_errors() -> List[ErrorInfo]
get_runtime_errors() -> List[ErrorInfo]
get_static_errors() -> List[ErrorInfo]
get_file_errors(file_path: str) -> List[ErrorInfo]

# Error management
add_static_error(error_info: ErrorInfo) -> None
clear_runtime_errors() -> None
clear_static_errors() -> None
clear_all_errors() -> None

# Analysis and reporting
get_error_summary() -> Dict[str, Any]
get_performance_stats() -> Dict[str, Any]
get_diagnostics_for_lsp(file_path: Optional[str] = None) -> List[Diagnostic]

# Configuration
configure_runtime_collection(**kwargs) -> None
add_error_handler(handler: Callable[[ErrorInfo], None]) -> None

# Lifecycle
shutdown() -> None
```

### RuntimeErrorCollector

Specialized class for runtime error collection.

#### Constructor

```python
RuntimeErrorCollector(repo_path: str)
```

#### Key Methods

```python
# Collection control
start_collection() -> None
stop_collection() -> None

# Configuration
configure_collection(
    max_errors: Optional[int] = None,
    max_stack_depth: Optional[int] = None,
    collect_variables: Optional[bool] = None,
    variable_max_length: Optional[int] = None
) -> None

# Error retrieval
get_runtime_errors() -> List[ErrorInfo]
get_runtime_errors_for_file(file_path: str) -> List[ErrorInfo]
get_error_summary() -> Dict[str, Any]
get_collection_stats() -> Dict[str, Any]

# Event handling
add_error_handler(handler: Callable[[ErrorInfo], None]) -> None
```

### ErrorInfo

Comprehensive error information class.

#### Properties

```python
# Basic error information
file_path: str
line: int
character: int
message: str
severity: DiagnosticSeverity
error_type: ErrorType

# Enhanced context
runtime_context: Optional[RuntimeContext]
fix_suggestions: List[str]
related_symbols: List[str]
context_lines: List[str]

# Serena-specific
symbol_info: Optional[Dict[str, Any]]
dependency_info: Optional[Dict[str, Any]]
```

#### Methods

```python
# Type checking
is_error() -> bool
is_warning() -> bool
is_runtime_error() -> bool
has_runtime_context() -> bool
has_fix_suggestions() -> bool

# LSP conversion
get_position() -> Position
get_range() -> Range
to_diagnostic() -> Diagnostic

# Analysis
get_context_summary() -> str
```

### Protocol Extension

Custom LSP methods for advanced functionality.

#### Available Methods

- `serena/getAllErrors` - Get all errors with optional filtering
- `serena/getRuntimeErrors` - Get only runtime errors
- `serena/getStaticErrors` - Get only static analysis errors
- `serena/getFileErrors` - Get errors for a specific file
- `serena/getErrorSummary` - Get comprehensive error summary
- `serena/clearErrors` - Clear errors by type
- `serena/refreshDiagnostics` - Force refresh diagnostics
- `serena/configureCollection` - Configure runtime collection
- `serena/getPerformanceStats` - Get performance statistics

#### Notifications

- `serena/errorDetected` - New error detected
- `serena/errorsCleared` - Errors cleared
- `serena/diagnosticsUpdated` - Diagnostics updated

## Configuration

### Runtime Collection Configuration

```python
bridge.configure_runtime_collection(
    max_errors=1000,           # Maximum errors to keep in memory
    max_stack_depth=50,        # Maximum stack trace depth
    collect_variables=True,    # Whether to collect variable states
    variable_max_length=200    # Maximum length for variable values
)
```

### Error Handler Registration

```python
def custom_error_handler(error: ErrorInfo):
    if error.is_error:
        print(f"Critical error: {error.message}")
        # Send to monitoring system, etc.

bridge.add_error_handler(custom_error_handler)
```

## Error Types and Severity

### Error Types

```python
class ErrorType(IntEnum):
    STATIC_ANALYSIS = 1  # Syntax, import, type errors
    RUNTIME_ERROR = 2    # Runtime execution errors
    LINTING = 3         # Code style and quality
    SECURITY = 4        # Security vulnerabilities
    PERFORMANCE = 5     # Performance issues
```

### Severity Levels

```python
class DiagnosticSeverity(IntEnum):
    ERROR = 1        # Critical errors
    WARNING = 2      # Warnings
    INFORMATION = 3  # Informational messages
    HINT = 4         # Hints and suggestions
```

## Advanced Usage

### Context Manager Pattern

```python
from graph_sitter.extensions.lsp.runtime_collector import collect_runtime_errors_context_manager

# Temporary runtime error collection
with collect_runtime_errors_context_manager("/path/to/repo") as collector:
    # Your code here - errors will be collected
    result = some_function_that_might_error()
    
    # Check for errors
    errors = collector.get_runtime_errors()
    if errors:
        print(f"Detected {len(errors)} runtime errors")
# Collection automatically stops when exiting context
```

### Custom Error Analysis

```python
def analyze_error_patterns(bridge: SerenaLSPBridge):
    errors = bridge.get_all_errors()
    
    # Group by error patterns
    import_errors = [e for e in errors if "import" in e.message.lower()]
    none_errors = [e for e in errors if "none" in e.message.lower()]
    
    # Analyze runtime context
    context_errors = [e for e in errors if e.has_runtime_context]
    for error in context_errors:
        if error.runtime_context.local_variables:
            print(f"Variables at error: {list(error.runtime_context.local_variables.keys())}")
    
    return {
        'import_errors': len(import_errors),
        'none_errors': len(none_errors),
        'context_errors': len(context_errors)
    }
```

### Integration with Existing LSP Servers

```python
from pygls.server import LanguageServer
from graph_sitter.extensions.lsp.serena_protocol import SerenaProtocolExtension

class MyLanguageServer(LanguageServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serena_extension = None
    
    def initialize(self, params):
        # Initialize Serena extension
        repo_path = params.root_path or os.getcwd()
        self.serena_extension = SerenaProtocolExtension(repo_path)
        
        # Add notification callback
        self.serena_extension.add_notification_callback(
            lambda notification: self.send_notification(
                notification['method'], 
                notification['params']
            )
        )
    
    @lsp_method('serena/getAllErrors')
    def get_all_errors(self, params):
        if self.serena_extension:
            return self.serena_extension.handle_request('serena/getAllErrors', params)
        return {'result': None, 'error': {'message': 'Serena extension not available'}}
```

## Performance Considerations

### Memory Usage

- Runtime error collection is limited by `max_errors` parameter
- Variable collection can be disabled for better performance
- Stack trace depth is configurable via `max_stack_depth`

### CPU Usage

- Error collection uses exception hooks with minimal overhead
- Context analysis is performed asynchronously when possible
- Fix suggestion generation is cached and optimized

### Recommended Settings

```python
# For development environments
bridge.configure_runtime_collection(
    max_errors=1000,
    collect_variables=True,
    variable_max_length=500
)

# For production environments
bridge.configure_runtime_collection(
    max_errors=100,
    collect_variables=False,
    max_stack_depth=20
)
```

## Troubleshooting

### Common Issues

1. **Serena components not available**
   - Install Serena dependencies: `pip install graph-sitter[serena]`
   - Extension will work with basic LSP functionality

2. **Runtime collection not working**
   - Check if collection is enabled: `bridge.runtime_collector.is_active`
   - Verify repository path is correct
   - Check for permission issues

3. **High memory usage**
   - Reduce `max_errors` parameter
   - Disable variable collection: `collect_variables=False`
   - Clear errors periodically: `bridge.clear_runtime_errors()`

4. **Performance issues**
   - Reduce `max_stack_depth`
   - Limit `variable_max_length`
   - Use fewer error handlers

### Debug Mode

```python
import logging
logging.getLogger('graph_sitter.extensions.lsp').setLevel(logging.DEBUG)

# Enable detailed logging
bridge = create_serena_bridge(repo_path, enable_runtime_collection=True)
```

### Health Check

```python
def health_check(bridge: SerenaLSPBridge):
    summary = bridge.get_error_summary()
    stats = bridge.get_performance_stats()
    
    print("=== Health Check ===")
    print(f"Bridge initialized: {summary['bridge_initialized']}")
    print(f"Runtime collection active: {summary['runtime_collection_active']}")
    print(f"Serena available: {summary['serena_available']}")
    print(f"Total errors collected: {stats['total_errors_collected']}")
    print(f"Average collection time: {stats.get('average_collection_time', 'N/A')}")
    
    return summary['bridge_initialized'] and not any([
        stats['total_errors_collected'] > 10000,  # Too many errors
        stats.get('average_collection_time', 0) > 0.1  # Slow collection
    ])
```

## Examples

See the `examples/comprehensive_example.py` file for a complete demonstration of all features.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the same license as Graph-Sitter.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the examples
3. Open an issue on GitHub
4. Check the Graph-Sitter documentation

