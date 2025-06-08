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

