# Serena LSP Integration for Graph-Sitter

This module provides comprehensive Language Server Protocol (LSP) integration with Serena for advanced error analysis, code intelligence, and repository analysis capabilities.

## Features

### 🔍 **Comprehensive Error Analysis**
- **Multi-severity error detection**: ERROR, WARNING, INFO, HINT
- **Error categorization**: SYNTAX, TYPE, LOGIC, PERFORMANCE, SECURITY, STYLE, COMPATIBILITY, DEPENDENCY
- **Real-time error monitoring** with runtime error collection
- **Context-aware error reporting** with fix suggestions

### 🌐 **GitHub Repository Analysis**
- **Repository cloning and analysis** from GitHub URLs
- **Branch-specific analysis** with configurable clone depth
- **Concurrent multi-repository analysis**
- **Caching and performance optimization**

### ⚡ **Advanced LSP Capabilities**
- **Protocol-compliant LSP communication** with Serena servers
- **Async/await support** for non-blocking operations
- **Request/response correlation** and error handling
- **Custom Serena protocol extensions**

### 📊 **Intelligence and Analytics**
- **Symbol intelligence** with dependency tracking
- **Code context analysis** with impact assessment
- **Performance monitoring** and metrics collection
- **Comprehensive reporting** and statistics

## Quick Start

### Basic Error Analysis

```python
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge

# Initialize LSP bridge for a codebase
bridge = SerenaLSPBridge("/path/to/codebase", enable_runtime_collection=True)

# Get all diagnostics
diagnostics = bridge.get_diagnostics(include_runtime=True)

# Filter by severity
errors = [d for d in diagnostics if d.is_error]
warnings = [d for d in diagnostics if d.is_warning]

# Get file-specific diagnostics
file_errors = bridge.get_file_diagnostics("src/main.py")

print(f"Found {len(errors)} errors and {len(warnings)} warnings")
```

### GitHub Repository Analysis

```python
from graph_sitter.extensions.lsp.serena_analysis import analyze_github_repository

# Analyze a GitHub repository
result = await analyze_github_repository(
    repo_url="https://github.com/owner/repo",
    branch="main",
    severity_filter=["error", "warning"]
)

# Get errors by severity
errors_by_severity = result['errors_by_severity']
print(f"Critical errors: {len(errors_by_severity['critical'])}")
print(f"Warnings: {len(errors_by_severity['warning'])}")

# Get summary statistics
summary = result['summary_by_severity']
for severity, stats in summary.items():
    print(f"{severity}: {stats['count']} errors in {stats['files_affected']} files")
```

### Real-time Error Monitoring

```python
from graph_sitter.extensions.lsp.serena_analysis import GitHubRepositoryAnalyzer

analyzer = GitHubRepositoryAnalyzer()

# Monitor repository for real-time errors
async for errors in analyzer.get_real_time_errors(
    repo_url="https://github.com/owner/repo",
    poll_interval=5.0
):
    print(f"Current errors: {len(errors)}")
    for error in errors[:5]:  # Show first 5
        print(f"  {error.display_text}")
```

## API Reference

### SerenaLSPBridge

The main class for LSP integration with comprehensive error analysis.

```python
class SerenaLSPBridge:
    def __init__(self, repo_path: str, enable_runtime_collection: bool = True)
    
    # Error retrieval
    def get_diagnostics(self, include_runtime: bool = True) -> List[ErrorInfo]
    def get_file_diagnostics(self, file_path: str, include_runtime: bool = True) -> List[ErrorInfo]
    def get_runtime_errors(self) -> List[ErrorInfo]
    def get_static_errors(self) -> List[ErrorInfo]
    
    # Analysis and context
    def get_all_errors_with_context(self) -> List[Dict[str, Any]]
    def get_runtime_error_summary(self) -> Dict[str, Any]
    def get_status(self) -> Dict[str, Any]
    
    # Management
    def refresh_diagnostics(self) -> None
    def clear_runtime_errors(self) -> None
    def shutdown(self) -> None
```

### GitHubRepositoryAnalyzer

Comprehensive GitHub repository analysis with caching and performance monitoring.

```python
class GitHubRepositoryAnalyzer:
    def __init__(self, work_dir: Optional[str] = None, enable_runtime_collection: bool = True)
    
    # Repository analysis
    async def analyze_repository_by_url(
        self, repo_url: str, branch: str = "main", 
        clone_depth: Optional[int] = 1, use_cache: bool = True,
        severity_filter: Optional[List[ErrorSeverity]] = None
    ) -> AnalysisResult
    
    # File-specific analysis
    async def get_file_errors(self, repo_url: str, file_path: str, branch: str = "main") -> List[CodeError]
    
    # Real-time monitoring
    async def get_real_time_errors(
        self, repo_url: str, branch: str = "main", poll_interval: float = 5.0
    ) -> AsyncGenerator[List[CodeError], None]
    
    # Analytics and management
    def get_analysis_summary(self) -> Dict[str, Any]
    def clear_cache(self, repo_url: Optional[str] = None) -> None
    async def shutdown(self) -> None
```

### Error Classes

#### ErrorInfo
Core error information with runtime context support.

```python
@dataclass
class ErrorInfo:
    file_path: str
    line: int
    character: int
    message: str
    severity: DiagnosticSeverity
    error_type: ErrorType = ErrorType.STATIC_ANALYSIS
    source: Optional[str] = None
    code: Optional[Union[str, int]] = None
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    runtime_context: Optional[RuntimeContext] = None
    related_errors: List['ErrorInfo'] = field(default_factory=list)
    fix_suggestions: List[str] = field(default_factory=list)
    symbol_info: Optional[Dict[str, Any]] = None
    code_context: Optional[str] = None
    dependency_chain: List[str] = field(default_factory=list)
```

#### CodeError
Enhanced error representation with comprehensive context.

```python
@dataclass
class CodeError:
    id: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    location: ErrorLocation
    code: Optional[str] = None
    source: str = "serena"
    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    related_errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
```

## Configuration

### Environment Variables

```bash
# Enable debug logging
export GRAPH_SITTER_LOG_LEVEL=DEBUG

# Configure LSP server timeout
export SERENA_LSP_TIMEOUT=30

# Set working directory for repository cloning
export SERENA_WORK_DIR=/tmp/serena_analysis
```

### Optional Dependencies

Install Serena LSP support:

```bash
pip install graph-sitter[serena]
```

This installs the optional Serena dependencies for full LSP integration.

## Examples

### Example 1: Analyze Repository Errors by Severity

```python
import asyncio
from graph_sitter.extensions.lsp.serena_analysis import analyze_github_repository

async def main():
    result = await analyze_github_repository(
        repo_url="https://github.com/python/cpython",
        branch="main",
        severity_filter=["error", "warning"]
    )
    
    # Print summary
    analysis = result['analysis']
    print(f"Repository: {result['repository']['name']}")
    print(f"Total errors: {analysis['total_errors']}")
    print(f"Critical errors: {analysis['critical_errors']}")
    print(f"Warnings: {analysis['warnings']}")
    print(f"Files analyzed: {analysis['files_analyzed']}")
    print(f"Analysis time: {analysis['analysis_duration']:.2f}s")
    
    # Show top error categories
    summary = result['summary_by_severity']
    for severity, stats in summary.items():
        if stats['count'] > 0:
            print(f"\n{severity.upper()} ({stats['count']} errors):")
            for category, count in stats['categories'].items():
                if count > 0:
                    print(f"  {category}: {count}")

asyncio.run(main())
```

### Example 2: Real-time Error Monitoring

```python
import asyncio
from graph_sitter.extensions.lsp.serena_analysis import GitHubRepositoryAnalyzer

async def monitor_repository():
    analyzer = GitHubRepositoryAnalyzer()
    
    try:
        print("Starting real-time monitoring...")
        
        async for errors in analyzer.get_real_time_errors(
            repo_url="https://github.com/owner/repo",
            branch="develop",
            poll_interval=10.0
        ):
            # Filter critical errors
            critical_errors = [e for e in errors if e.severity == ErrorSeverity.ERROR]
            
            if critical_errors:
                print(f"🚨 {len(critical_errors)} critical errors detected:")
                for error in critical_errors[:3]:
                    print(f"  {error.location.file_name}:{error.location.line} - {error.message}")
            else:
                print(f"✅ No critical errors ({len(errors)} total diagnostics)")
    
    finally:
        await analyzer.shutdown()

asyncio.run(monitor_repository())
```

### Example 3: Multi-Repository Analysis

```python
import asyncio
from graph_sitter.extensions.lsp.serena_analysis import analyze_multiple_repositories

async def analyze_multiple():
    repos = [
        "https://github.com/owner/repo1",
        "https://github.com/owner/repo2",
        "https://github.com/owner/repo3"
    ]
    
    results = await analyze_multiple_repositories(
        repo_urls=repos,
        branch="main",
        max_concurrent=2
    )
    
    for repo_url, result in results.items():
        if 'error' in result:
            print(f"❌ {repo_url}: {result['error']}")
        else:
            analysis = result['analysis']
            print(f"✅ {repo_url}: {analysis['total_errors']} errors in {analysis['analysis_duration']:.1f}s")

asyncio.run(analyze_multiple())
```

### Example 4: Custom Error Filtering and Analysis

```python
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge, ErrorType, DiagnosticSeverity

# Initialize bridge
bridge = SerenaLSPBridge("/path/to/codebase")

# Get all diagnostics
all_diagnostics = bridge.get_diagnostics(include_runtime=True)

# Custom filtering
syntax_errors = [
    d for d in all_diagnostics 
    if d.error_type == ErrorType.STATIC_ANALYSIS and "syntax" in d.message.lower()
]

runtime_errors = [
    d for d in all_diagnostics 
    if d.error_type == ErrorType.RUNTIME_ERROR
]

security_issues = [
    d for d in all_diagnostics 
    if d.error_type == ErrorType.SECURITY
]

print(f"Syntax errors: {len(syntax_errors)}")
print(f"Runtime errors: {len(runtime_errors)}")
print(f"Security issues: {len(security_issues)}")

# Get comprehensive error context
errors_with_context = bridge.get_all_errors_with_context()
for error_context in errors_with_context[:3]:  # Show first 3
    basic_info = error_context['basic_info']
    print(f"\nError: {basic_info['message']}")
    print(f"File: {basic_info['file_path']}:{basic_info['line']}")
    
    if 'runtime' in error_context:
        runtime = error_context['runtime']
        print(f"Exception: {runtime['exception_type']}")
        print(f"Stack frames: {len(runtime['stack_trace'])}")
    
    if 'fix_suggestions' in error_context:
        suggestions = error_context['fix_suggestions']
        if suggestions:
            print("Suggestions:")
            for suggestion in suggestions[:2]:
                print(f"  - {suggestion}")

bridge.shutdown()
```

## Testing

Run the integration tests:

```bash
python -m graph_sitter.extensions.lsp.test_serena_integration
```

This will test:
- Basic LSP bridge functionality
- GitHub repository analysis
- Error categorization
- Performance monitoring

## Performance Considerations

### Caching
- Repository analysis results are cached by URL and branch
- LSP diagnostics are cached per file
- Use `clear_cache()` to manage memory usage

### Concurrency
- Use `max_concurrent` parameter for multi-repository analysis
- Real-time monitoring uses async generators for efficiency
- LSP communication is fully asynchronous

### Memory Management
- Runtime error collection has configurable limits
- Automatic cleanup of completed requests
- Proper resource disposal in `shutdown()` methods

## Troubleshooting

### Common Issues

1. **LSP Server Not Found**
   ```
   Solution: Install serena with `pip install graph-sitter[serena]`
   ```

2. **Repository Clone Failures**
   ```
   Solution: Check network connectivity and repository permissions
   ```

3. **High Memory Usage**
   ```
   Solution: Use `clear_cache()` periodically and limit `clone_depth`
   ```

4. **Slow Analysis**
   ```
   Solution: Use shallow clones (`clone_depth=1`) and enable caching
   ```

### Debug Logging

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use graph-sitter's logger
from graph_sitter.shared.logging.get_logger import get_logger
logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)
```

## Contributing

1. **Adding New Error Types**: Extend `ErrorType` and `ErrorCategory` enums
2. **Custom Protocol Extensions**: Add methods to `SerenaProtocolExtensions`
3. **Performance Improvements**: Focus on caching and async operations
4. **Testing**: Add tests to `test_serena_integration.py`

## License

This module is part of the graph-sitter project and follows the same Apache 2.0 license.

