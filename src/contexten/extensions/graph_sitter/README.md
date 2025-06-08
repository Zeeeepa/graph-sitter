# Graph_Sitter Extension for Contexten

Comprehensive codebase analysis using the actual [graph_sitter](https://graph-sitter.com) API. This extension provides real issue detection, complexity analysis, security scanning, and actionable insights for code improvement.

## Features

### 🔍 **Comprehensive Analysis**
- **Dead Code Detection**: Find unused functions, variables, imports, and classes
- **Complexity Analysis**: Cyclomatic complexity, Halstead metrics, maintainability index
- **Dependency Analysis**: Import relationships, circular dependencies, coupling metrics
- **Security Analysis**: SQL injection, hardcoded secrets, unsafe eval usage, command injection
- **Call Graph Analysis**: Function call relationships, hotspots, recursive functions

### ✅ **Real Issue Detection**
Unlike simple static analysis tools, this extension uses graph_sitter's semantic understanding to detect:
- Actually unused code (not just unreferenced)
- Real security vulnerabilities in context
- Performance bottlenecks based on call patterns
- Architectural issues like circular dependencies

### 🛠️ **Actionable Results**
- Specific file locations and line numbers
- Severity levels (critical, high, medium, low)
- Concrete recommendations for fixes
- Automated dead code removal

## Installation

```bash
# Install graph_sitter
pip install graph-sitter

# The extension is already included in contexten
```

## Usage

### Python API

```python
from graph_sitter import Codebase
from contexten.extensions.graph_sitter import comprehensive_analysis

# Run comprehensive analysis
codebase = Codebase("./my_project")
results = comprehensive_analysis(codebase)

# Print summary
from contexten.extensions.graph_sitter import print_analysis_summary
print_analysis_summary(results)

# Save detailed report
from contexten.extensions.graph_sitter import save_analysis_report
save_analysis_report(results, "analysis_report.json")
```

### Individual Analyzers

```python
from graph_sitter import Codebase
from contexten.extensions.graph_sitter import (
    detect_dead_code,
    analyze_complexity, 
    analyze_security,
    analyze_dependencies,
    analyze_call_graph
)

codebase = Codebase("./my_project")

# Dead code analysis
dead_code = detect_dead_code(codebase)
print(f"Found {dead_code['summary']['total_dead_functions']} unused functions")

# Security analysis
security = analyze_security(codebase)
print(f"Found {security['summary']['critical_issues']} critical security issues")

# Complexity analysis
complexity = analyze_complexity(codebase)
print(f"Average maintainability: {complexity['summary']['avg_maintainability']:.1f}")
```

### Command Line Interface

```bash
# Run comprehensive analysis
python -m contexten.extensions.graph_sitter.cli ./my_project

# Run specific analysis
python -m contexten.extensions.graph_sitter.cli ./my_project --analysis security

# Save detailed report
python -m contexten.extensions.graph_sitter.cli ./my_project --output report.json

# Automatically remove dead code (use with caution)
python -m contexten.extensions.graph_sitter.cli ./my_project --fix-dead-code
```

## Analysis Types

### 1. Dead Code Detection

Finds truly unused code elements:

```python
from contexten.extensions.graph_sitter import detect_dead_code, remove_dead_code

# Detect dead code
results = detect_dead_code(codebase)

# Automatically remove (use with caution)
removed_count = remove_dead_code(codebase)
codebase.commit()  # Save changes
```

**Detects:**
- Functions with no call sites
- Variables with no usages
- Imports that are never used
- Classes that are never instantiated

### 2. Complexity Analysis

Analyzes code complexity using multiple metrics:

```python
from contexten.extensions.graph_sitter import analyze_complexity, find_complex_functions

results = analyze_complexity(codebase)
complex_funcs = find_complex_functions(codebase, complexity_threshold=10)
```

**Metrics:**
- Cyclomatic complexity
- Halstead volume and metrics
- Maintainability index (0-100)
- Lines of code per function

### 3. Security Analysis

Detects real security vulnerabilities:

```python
from contexten.extensions.graph_sitter import analyze_security

results = analyze_security(codebase)
```

**Detects:**
- SQL injection vulnerabilities
- Hardcoded passwords/API keys
- Unsafe eval/exec usage
- Insecure random number generation
- Command injection risks
- Path traversal vulnerabilities

### 4. Dependency Analysis

Analyzes import relationships and dependencies:

```python
from contexten.extensions.graph_sitter import analyze_dependencies, detect_circular_dependencies

deps = analyze_dependencies(codebase)
circular = detect_circular_dependencies(codebase)
```

**Analyzes:**
- Import relationships
- Circular dependencies
- Module coupling
- External vs internal dependencies
- Unused imports

### 5. Call Graph Analysis

Analyzes function call relationships:

```python
from contexten.extensions.graph_sitter import analyze_call_graph, find_hotspot_functions

calls = analyze_call_graph(codebase)
hotspots = find_hotspot_functions(codebase)
```

**Provides:**
- Most called functions
- Functions making most calls
- Recursive function detection
- Call frequency analysis
- Function hotspots

## Example Output

```
📊 COMPREHENSIVE CODEBASE ANALYSIS REPORT
============================================================
📅 Analysis Date: 2024-01-15T10:30:00
⏱️  Duration: 2.34 seconds
📁 Files: 45
⚡ Functions: 234
🏗️  Classes: 12

📈 QUALITY SCORES
Overall Code Quality: 78/100
Maintainability: 82/100
Security: 65/100

🚨 ISSUES FOUND
Total Issues: 23
Critical Issues: 2
High Priority: 8

💡 TOP RECOMMENDATIONS
1. 🔴 Fix 2 critical security issues
   Address critical security vulnerabilities immediately
2. 🟠 Refactor 5 complex functions
   Break down complex functions to improve readability
3. 🟠 Resolve 3 circular dependencies
   Break circular dependencies to improve code architecture
```

## Integration with Frontend

The analysis results are designed for frontend consumption:

```python
# Get dashboard data
dashboard_data = {
    'summary': results['summary'],
    'issues_by_category': {
        'security': len(results['security']['sql_injection_risks']),
        'complexity': results['complexity']['summary']['high_complexity_functions'],
        'dead_code': results['dead_code']['summary']['total_dead_functions']
    },
    'recommendations': results['recommendations'][:10],
    'trends': {
        'quality_score': results['summary']['code_quality_score'],
        'issue_count': results['summary']['total_issues']
    }
}
```

## Real-World Examples

### Finding Security Issues

```python
# Find SQL injection vulnerabilities
security_results = analyze_security(codebase)
for risk in security_results['sql_injection_risks']:
    print(f"SQL injection risk in {risk['function']} at {risk['file']}:{risk['line']}")
    print(f"Recommendation: {risk['recommendation']}")
```

### Identifying Performance Bottlenecks

```python
# Find complex functions that might be slow
complexity_results = analyze_complexity(codebase)
for func in complexity_results['functions']:
    if func['cyclomatic_complexity'] > 15:
        print(f"Complex function: {func['name']} (complexity: {func['cyclomatic_complexity']})")
```

### Cleaning Up Dead Code

```python
# Safe dead code removal
dead_code = detect_dead_code(codebase)
print(f"Found {len(dead_code['dead_functions'])} unused functions")

# Review before removing
for func in dead_code['dead_functions']:
    print(f"Unused: {func['name']} in {func['file']}")

# Remove if confirmed
if input("Remove dead code? (y/N): ").lower() == 'y':
    removed = remove_dead_code(codebase)
    codebase.commit()
    print(f"Removed {removed} dead code elements")
```

## Best Practices

1. **Run Regular Analysis**: Include analysis in CI/CD pipelines
2. **Address Critical Issues First**: Focus on security and high-complexity issues
3. **Review Before Auto-fixing**: Always review dead code before removal
4. **Track Trends**: Save reports to track code quality over time
5. **Use Specific Analyzers**: Run targeted analysis for specific concerns

## API Reference

### Main Functions

- `comprehensive_analysis(codebase)` - Run all analyzers
- `print_analysis_summary(results)` - Print formatted summary
- `save_analysis_report(results, filename)` - Save JSON report

### Individual Analyzers

- `detect_dead_code(codebase)` - Find unused code
- `analyze_complexity(codebase)` - Complexity metrics
- `analyze_security(codebase)` - Security vulnerabilities
- `analyze_dependencies(codebase)` - Import analysis
- `analyze_call_graph(codebase)` - Call relationships

### Utility Functions

- `remove_dead_code(codebase)` - Remove unused code
- `find_complex_functions(codebase, threshold)` - Find complex functions
- `find_hotspot_functions(codebase)` - Find frequently called functions
- `detect_circular_dependencies(codebase)` - Find circular imports

## Contributing

This extension uses the official graph_sitter API patterns. When adding new analyzers:

1. Use `@graph_sitter.function("analyzer-name")` decorator
2. Work with `codebase.functions`, `codebase.classes`, `codebase.files`
3. Use actual properties like `function.usages`, `function.call_sites`
4. Follow the existing result format patterns
5. Add comprehensive error handling

## License

This extension is part of the Contexten project and follows the same license terms.


## Advanced Configuration

The extension now supports all advanced graph-sitter configuration flags from [graph-sitter.com/introduction/advanced-settings](https://graph-sitter.com/introduction/advanced-settings).

### Configuration Modes

#### Performance Mode
Optimized for large codebases with fast analysis:
```python
from contexten.extensions.graph_sitter import enhanced_comprehensive_analysis

# Performance-optimized analysis
results = enhanced_comprehensive_analysis("./large_project", optimization_mode="performance")
```

**Features:**
- `exp_lazy_graph=True` - Lazy graph construction for faster initialization
- `method_usages=False` - Disabled for speed boost
- `generics=False` - Simplified type analysis
- `full_range_index=False` - Reduced memory usage

#### Debug Mode
Comprehensive debugging with verbose logging:
```python
# Debug mode with full verification
results = enhanced_comprehensive_analysis("./project", optimization_mode="debug")
```

**Features:**
- `debug=True` - Verbose logging for debugging
- `verify_graph=True` - Graph state verification
- `track_graph=True` - Original graph tracking
- `full_range_index=True` - Complete range-to-node mapping

#### TypeScript Mode
Optimized for TypeScript/JavaScript projects:
```python
# TypeScript-specific optimizations
results = enhanced_comprehensive_analysis("./ts_project", optimization_mode="typescript")
```

**Features:**
- `ts_dependency_manager=True` - TypeScript dependency resolution
- `ts_language_engine=True` - TypeScript compiler integration
- `generics=True` - Generic type resolution
- `method_usages=True` - Complete call graph analysis

### Configuration Manager

Get intelligent configuration recommendations:

```python
from contexten.extensions.graph_sitter import ConfigurationManager

manager = ConfigurationManager()

# Get recommendations based on codebase characteristics
recommendations = manager.get_config_recommendations("./my_project")
print(f"Recommended config: {recommendations['recommended_config']['config_name']}")
print(f"Reason: {recommendations['recommended_config']['reasoning']}")

# Compare multiple configurations
comparison = manager.compare_configurations("./my_project", 
                                          ["performance", "comprehensive", "debug"])
print(f"Fastest config: {comparison['performance_comparison']['fastest_config']}")
```

### Advanced Configuration Flags

All flags from the official documentation are supported:

#### Performance Flags
- `exp_lazy_graph` - Lazy graph construction for large codebases
- `method_usages` - Enable/disable method usage resolution
- `generics` - Enable/disable generic type resolution
- `sync_enabled` - Graph sync during codebase.commit()

#### Debugging Flags
- `debug` - Verbose logging and additional assertions
- `verify_graph` - Graph state verification after reset
- `track_graph` - Keep copy of original graph for debugging
- `full_range_index` - Complete tree-sitter range-to-node mapping

#### Import Resolution Flags
- `py_resolve_syspath` - Resolve imports from sys.path
- `allow_external` - Resolve external imports and modules
- `import_resolution_paths` - Alternative import resolution paths
- `import_resolution_overrides` - Import path overrides

#### TypeScript Flags
- `ts_dependency_manager` - TypeScript dependency installer
- `ts_language_engine` - TypeScript compiler integration
- `v8_ts_engine` - V8-based TypeScript compiler

#### Experimental Flags
- `unpacking_assignment_partial_removal` - Smart unpacking assignment removal
- `ignore_process_errors` - Control external process error handling
- `disable_graph` - AST-only mode without graph construction

### Custom Configuration

Create custom configurations for specific needs:

```python
from contexten.extensions.graph_sitter import AdvancedCodebaseConfig
from graph_sitter import Codebase

# Create custom configuration
config = AdvancedCodebaseConfig()
config.method_usages = True
config.generics = True
config.full_range_index = True
config.debug = True

# Use with codebase
codebase = Codebase("./project", config=config.create_config())
```

### Command Line Advanced Features

```bash
# Enhanced analysis with performance mode
python -m contexten.extensions.graph_sitter.cli ./project --enhanced --mode performance

# Get configuration recommendations
python -m contexten.extensions.graph_sitter.cli ./project --config-recommend

# Compare multiple configurations
python -m contexten.extensions.graph_sitter.cli ./project --config-compare performance comprehensive debug

# Debug mode analysis
python -m contexten.extensions.graph_sitter.cli ./project --enhanced --mode debug
```

### Configuration Examples

#### Large Codebase (1000+ files)
```python
# Optimized for performance
config = create_performance_config()
# - Uses lazy graph construction
# - Disables expensive features
# - Minimizes memory usage
```

#### Complex TypeScript Project
```python
# Full TypeScript support
config = create_typescript_analysis_config()
# - TypeScript language engine
# - Generic type resolution
# - Dependency management
```

#### Debugging Problematic Repository
```python
# Maximum debugging information
config = create_debug_config()
# - Verbose logging
# - Graph verification
# - Complete range indexing
```

### Performance Impact

Configuration choice significantly affects performance:

| Configuration | Initialization Time | Memory Usage | Features Available |
|---------------|-------------------|--------------|-------------------|
| Performance   | Fast (0.1-0.5s)  | Low          | Basic analysis    |
| Comprehensive | Medium (0.5-2s)  | Medium       | Full analysis     |
| Debug         | Slow (2-10s)     | High         | All + debugging   |
| TypeScript    | Medium (1-3s)    | Medium       | TS-specific       |

### Best Practices

1. **Start with recommendations**: Use `ConfigurationManager` to get optimal settings
2. **Performance first**: Use performance mode for CI/CD pipelines
3. **Debug when needed**: Enable debug mode only for troubleshooting
4. **Language-specific**: Use TypeScript mode for TS/JS projects
5. **Monitor impact**: Compare configurations to understand trade-offs

