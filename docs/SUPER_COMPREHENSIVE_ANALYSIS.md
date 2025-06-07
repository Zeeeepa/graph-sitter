# 🚀 Super Comprehensive Single-Mode Analysis

The simplest and most powerful way to analyze any codebase with interactive exploration capabilities.

## Quick Start

```python
from contexten.extensions.graph_sitter.code_analysis import analyze_codebase

# One line to analyze everything
result = analyze_codebase("/path/to/code")

# Explore interactively in your browser
print(f"Explore your code at: {result.interactive_url}")
```

## Features

- **🔍 Complete Analysis**: All Phase 1 & Phase 2 features in one call
- **🌐 Interactive Exploration**: Automatic web interface generation
- **📊 Rich Visualizations**: D3.js-powered interactive reports
- **⚡ Performance Optimized**: Caching and parallel processing
- **🎯 Quality Scoring**: Automatic code quality assessment
- **🔒 Security Analysis**: Built-in security pattern detection
- **📈 Performance Analysis**: Performance issue identification

## API Reference

### Main Function

```python
analyze_codebase(
    path: Union[str, Path],
    auto_open: bool = True,
    port: int = 8000,
    include_interactive: bool = True
) -> CodeAnalysisResult
```

**Parameters:**
- `path`: Path to the codebase to analyze
- `auto_open`: Automatically open browser to interactive analysis
- `port`: Port for web server (will find available port if busy)
- `include_interactive`: Generate interactive web interface

**Returns:** `CodeAnalysisResult` with comprehensive analysis data

### Result Object

```python
@dataclass
class CodeAnalysisResult:
    # Basic information
    path: str
    analysis_time: float
    timestamp: str
    
    # Core metrics
    total_files: int
    total_functions: int
    total_classes: int
    total_lines: int
    
    # Analysis results
    import_loops: int
    dead_code_items: int
    training_data_items: int
    security_issues: int
    performance_issues: int
    quality_score: float  # 0-10 scale
    
    # Interactive exploration
    interactive_url: Optional[str]
    report_path: Optional[str]
    web_server_port: Optional[int]
```

### Methods

```python
# Open interactive analysis in browser
result.open_browser()

# Stop the web server
result.stop_server()

# Print comprehensive summary
print(result)
```

## Usage Examples

### 1. Basic Analysis

```python
from contexten.extensions.graph_sitter.code_analysis import analyze_codebase

# Analyze current directory
result = analyze_codebase(".")
print(result)
```

### 2. Interactive Exploration

```python
# Analyze with automatic browser opening
result = analyze_codebase("/path/to/project", auto_open=True)

# The browser will automatically open to the interactive analysis
# You can also manually open it later:
result.open_browser()
```

### 3. Programmatic Access

```python
result = analyze_codebase("/path/to/project")

# Access metrics programmatically
print(f"Quality Score: {result.quality_score:.1f}/10")
print(f"Files: {result.total_files}")
print(f"Functions: {result.total_functions}")
print(f"Security Issues: {result.security_issues}")

# Check for specific issues
if result.import_loops > 0:
    print(f"⚠️  Found {result.import_loops} import loops")

if result.dead_code_items > 0:
    print(f"🗑️  Found {result.dead_code_items} dead code items")
```

### 4. Quick Analysis Mode

```python
from contexten.extensions.graph_sitter.code_analysis import quick_analyze

# Fast analysis without interactive features
result = quick_analyze("/path/to/project")
print(f"Quick analysis: {result.quality_score:.1f}/10")
```

### 5. Advanced Configuration

```python
from contexten.extensions.graph_sitter.code_analysis import quick_analyze

# Analysis without auto-opening browser
result = analyze_codebase(
    "/path/to/project",
    auto_open=False,
    port=9000,
    include_interactive=True
)

# Manually open when ready
print(f"Analysis ready at: {result.interactive_url}")
result.open_browser()
```

## Interactive Features

The generated interactive web interface includes:

### 📊 **Overview Dashboard**
- File, function, and class counts
- Lines of code metrics
- Quality score visualization
- Analysis time and timestamp

### 🔍 **Issue Analysis**
- Import loop detection and visualization
- Dead code identification
- Security vulnerability patterns
- Performance anti-patterns

### 🌳 **Query Pattern Results**
- Tree-sitter query pattern matches
- Pattern categorization (function, class, security, performance)
- Interactive filtering and search

### ⚡ **Performance Metrics**
- Analysis performance statistics
- Cache hit rates and efficiency
- Memory usage tracking
- Processing speed metrics

### 📈 **Quality Metrics**
- Function complexity analysis
- Maintainability indices
- Design pattern detection
- Code smell identification

## Quality Scoring

The quality score (0-10) is calculated based on:

- **Import Loops**: Circular dependencies reduce score
- **Dead Code**: Unused code reduces score
- **Security Issues**: Security vulnerabilities reduce score
- **Performance Issues**: Performance anti-patterns reduce score
- **Complexity**: High function complexity reduces score
- **Best Practices**: Following best practices increases score

## Advanced Features

### All Phase 1 Features Enabled
- Import loop detection with graph analysis
- Dead code detection using usage analysis
- Training data generation for LLMs
- Enhanced function and class metrics
- Graph structure analysis

### All Phase 2 Features Enabled
- Tree-sitter query patterns for advanced syntax analysis
- Interactive HTML reports with D3.js integration
- Performance optimizations with caching and parallel processing
- Advanced CodebaseConfig usage with all flags

### Automatic Optimizations
- Language-specific optimizations (Python, TypeScript, JavaScript)
- Size-based optimizations (small, medium, large codebases)
- Performance optimization levels (minimal, balanced, aggressive)
- Intelligent caching and parallel processing

## Dependencies

### Required
- Python 3.7+
- Standard library modules (http.server, threading, etc.)

### Optional (for enhanced features)
- `graph-sitter`: Advanced syntax analysis
- `networkx`: Graph analysis capabilities
- `tree-sitter`: Query pattern matching
- `jinja2`: Template rendering for reports
- `redis`: Distributed caching
- `psutil`: Resource monitoring

### Graceful Degradation
The system works even without optional dependencies:
- Basic analysis without graph-sitter
- Simple reports without jinja2
- Memory caching without redis
- Single-threaded processing without advanced libraries

## Command Line Usage

```bash
# Direct module execution
python -m contexten.extensions.graph_sitter.code_analysis /path/to/code

# Using the comprehensive CLI
python -m graph_sitter.adapters.analysis.cli /path/to/code --comprehensive --html-report
```

## Integration Examples

### CI/CD Integration

```python
import sys
from contexten.extensions.graph_sitter.code_analysis import analyze_codebase

def check_code_quality(path, min_quality=7.0):
    """Check code quality in CI/CD pipeline."""
    result = analyze_codebase(path, auto_open=False, include_interactive=False)
    
    print(f"Code Quality: {result.quality_score:.1f}/10")
    
    if result.quality_score < min_quality:
        print(f"❌ Quality below threshold ({min_quality})")
        sys.exit(1)
    
    print("✅ Quality check passed")
    return result

# Usage in CI
check_code_quality(".", min_quality=7.0)
```

### Development Workflow

```python
from contexten.extensions.graph_sitter.code_analysis import analyze_codebase

def analyze_changes(project_path):
    """Analyze code changes during development."""
    result = analyze_codebase(project_path)
    
    # Print summary
    print(f"📊 Analysis Summary:")
    print(f"   Quality: {result.quality_score:.1f}/10")
    print(f"   Files: {result.total_files}")
    print(f"   Issues: {result.security_issues + result.performance_issues}")
    
    # Open interactive analysis for detailed exploration
    if result.interactive_url:
        print(f"🌐 Detailed analysis: {result.interactive_url}")
        result.open_browser()
    
    return result
```

## Troubleshooting

### Common Issues

1. **No interactive URL generated**
   - Check if `include_interactive=True`
   - Ensure web server dependencies are available
   - Check for port conflicts

2. **Analysis returns empty results**
   - Verify the path exists and contains code files
   - Check file permissions
   - Ensure supported file types are present

3. **Browser doesn't open automatically**
   - Set `auto_open=True` explicitly
   - Check if `webbrowser` module is available
   - Manually open the URL from `result.interactive_url`

### Performance Tips

1. **For large codebases**:
   ```python
   # Use performance optimizations
   result = analyze_codebase(
       path,
       include_interactive=False  # Skip HTML generation for speed
   )
   ```

2. **For repeated analysis**:
   - Caching is enabled by default
   - Subsequent runs will be much faster
   - Clear cache if needed: delete `.cache/graph_sitter/`

3. **For CI/CD environments**:
   ```python
   # Minimal analysis for CI
   from graph_sitter.adapters.code_analysis import quick_analyze
   result = quick_analyze(path)
   ```

## Contributing

The super comprehensive analysis system is built on top of the enhanced analysis framework. To contribute:

1. Core analysis features: `src/graph_sitter/adapters/analysis/`
2. Single-mode interface: `src/graph_sitter/adapters/code_analysis.py`
3. Examples: `examples/simple_analysis_example.py`

## License

Same as the main graph-sitter project.
