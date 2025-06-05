# Graph-sitter Analysis Module

Comprehensive code analysis module following the patterns from [graph-sitter.com/tutorials/at-a-glance](https://graph-sitter.com/tutorials/at-a-glance) with enhanced issue detection and comprehensive reporting.

## Features

### 🔍 Comprehensive Analysis
- **Dead Code Detection**: Identifies unused functions, classes, and variables
- **Code Quality Issues**: Detects various code quality problems with severity levels
- **Metrics Calculation**: Cyclomatic complexity, maintainability index, technical debt ratio
- **Dependency Analysis**: Import graph analysis and circular dependency detection
- **Function & Class Metrics**: Detailed metrics for all functions and classes

### 📊 Analysis Results
The analysis provides detailed information including:
- Total files, functions, classes, and lines of code
- Dead code items with location and confidence levels
- Code issues categorized by severity (critical, major, minor, info)
- Function metrics (complexity, parameters, nesting depth)
- Class metrics (methods, attributes, inheritance depth)
- Dependency graph and circular dependencies
- Quality metrics (maintainability index, technical debt ratio)

## Usage

### Basic Usage with Codebase Class

```python
from graph_sitter import Codebase

# Analyze local repository
codebase = Codebase("path/to/git/repo")
result = codebase.Analysis()

# Analyze remote repository  
codebase = Codebase.from_repo("fastapi/fastapi")
result = codebase.Analysis()

# Print formatted results
from graph_sitter.adapters.analysis import format_analysis_results
print(format_analysis_results(result))
```

### Direct Usage

```python
from graph_sitter.adapters.analysis import analyze_codebase, format_analysis_results

# Analyze a repository
result = analyze_codebase("path/to/repo")

# Print results
print(format_analysis_results(result))

# Access specific data
print(f"Total functions: {result.total_functions}")
print(f"Dead code items: {len(result.dead_code_items)}")
print(f"Issues found: {len(result.issues)}")
```

### Command Line Usage

```bash
# Analyze current directory
python -m graph_sitter.adapters.analysis.analysis .

# Analyze specific repository with JSON output
python -m graph_sitter.adapters.analysis.analysis /path/to/repo --format json --output results.json
```

## Analysis Results Structure

### Summary Information
```
Analysis Results:
  • Total Files: 100
  • Total Functions: 250
  • Total Classes: 45
  • Total Lines: 15000
  • Maintainability Index: 85.2/100
  • Technical Debt Ratio: 0.15
  • Test Coverage Estimate: 75.0%
```

### Dead Code Detection
```
Dead Code Items: 5
  • Function: unused_helper_function
    Location: src/utils/helpers.py:45-60
    Reason: Function is defined but never called
    Confidence: 80.0%
```

### Issue Detection
Issues are categorized by severity:
- **Critical**: Syntax errors, import errors
- **Major**: Complex functions, potential bugs
- **Minor**: Style issues, long lines
- **Info**: TODO comments, documentation issues

### Function Metrics
For each function, the analysis provides:
- Cyclomatic complexity
- Lines of code
- Number of parameters
- Return statements count
- Nesting depth
- Cognitive complexity

### Class Metrics
For each class, the analysis provides:
- Number of methods
- Number of attributes
- Inheritance depth
- Coupling metrics
- Cohesion metrics

## Advanced Features

### Dead Code Detection
The analyzer identifies:
- Unused functions (with confidence levels)
- Unused imports
- Unused variables
- Unreachable code

### Dependency Analysis
- Import graph construction
- Circular dependency detection
- Module coupling analysis
- Dependency path analysis

### Quality Metrics
- **Maintainability Index**: Based on complexity and lines of code
- **Technical Debt Ratio**: Based on issue severity and frequency
- **Test Coverage Estimate**: Heuristic based on test file presence

## Configuration

The analyzer can be configured for different analysis depths:

```python
from graph_sitter.adapters.analysis import CodeAnalyzer

analyzer = CodeAnalyzer("path/to/repo")
# Analyzer automatically discovers Python files and performs comprehensive analysis
result = analyzer.analyze()
```

## Integration with Graph-sitter

This module integrates seamlessly with the graph-sitter ecosystem:
- Uses AST parsing for accurate code analysis
- Follows graph-sitter patterns and conventions
- Provides tree-sitter compatible analysis results
- Supports multiple programming languages (Python focus)

## Output Formats

### Text Format (Default)
Human-readable formatted output with emojis and clear structure.

### JSON Format
Machine-readable JSON output for integration with other tools:

```json
{
  "summary": {
    "total_files": 100,
    "total_functions": 250,
    "total_classes": 45,
    "maintainability_index": 85.2
  },
  "dead_code_items": [...],
  "issues": [...],
  "function_metrics": [...],
  "class_metrics": [...]
}
```

## Examples

### Example 1: Basic Analysis
```python
from graph_sitter import Codebase

codebase = Codebase(".")
result = codebase.Analysis()
print(f"Found {len(result.issues)} issues in {result.total_files} files")
```

### Example 2: Dead Code Report
```python
from graph_sitter.adapters.analysis import analyze_codebase

result = analyze_codebase("my_project")
for item in result.dead_code_items:
    print(f"Dead {item.type}: {item.name} in {item.file_path}")
```

### Example 3: Quality Metrics
```python
result = analyze_codebase("my_project")
print(f"Maintainability Index: {result.maintainability_index:.1f}")
print(f"Technical Debt Ratio: {result.technical_debt_ratio:.2f}")
```

## Requirements

- Python 3.7+
- AST module (built-in)
- pathlib (built-in)
- Optional: tree-sitter for enhanced parsing

## Contributing

This module follows the graph-sitter contribution guidelines and patterns established in the main repository.

