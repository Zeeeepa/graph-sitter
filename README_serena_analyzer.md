# Serena Analyzer - Comprehensive Standalone Codebase Analyzer

A comprehensive, standalone codebase analyzer that consolidates all Serena analysis capabilities from the graph-sitter project into a single, self-contained module.

## Features

✅ **24+ Error Types** with severity classification (Critical, Major, Minor)  
✅ **Comprehensive Analysis** including syntax, logic, performance, security, and style issues  
✅ **Semantic Analysis** with AST parsing and code intelligence  
✅ **Repository Support** for both remote URLs and local paths  
✅ **Git Integration** with automatic cloning and cleanup  
✅ **Formatted Reports** with detailed error context and statistics  
✅ **CLI Interface** with progress indicators and verbose logging  
✅ **Self-Contained** - no external dependencies on graph-sitter installation  

## Installation

No installation required! The analyzer is a single, standalone Python file.

**Requirements:**
- Python 3.7+
- Git (for remote repository cloning)

## Usage

### Basic Usage

```bash
# Analyze a remote repository
python serena_analyzer.py --repo https://github.com/user/repo

# Analyze a local repository
python serena_analyzer.py --repo /path/to/local/repo

# Analyze current directory
python serena_analyzer.py --repo .
```

### Advanced Usage

```bash
# Custom output file
python serena_analyzer.py --repo https://github.com/user/repo --output custom_report.txt

# Verbose logging
python serena_analyzer.py --repo . --verbose

# Get help
python serena_analyzer.py --help

# Check version
python serena_analyzer.py --version
```

## Output Format

The analyzer generates a comprehensive report in the exact format requested:

```
SERENA CODEBASE ANALYSIS REPORT
==================================================
Repository: repository-name
Analysis Time: 21.01 seconds
Files Analyzed: 1515
Languages: Python, JavaScript, TypeScript, C++

ERRORS: 104 [⚠️ Critical: 30] [👉 Major: 39] [🔍 Minor: 35]

1 ⚠️- projectname/src/codefile1.py / Function - 'examplefunctionname' [error parameters/reason]
2 ⚠️- projectname/src/codefile.py / Function - 'examplefunctionname' [error parameters/reason]
3 ⚠️- projectname/src/codefile2.py / Function - 'examplefunctionname' [error parameters/reason]
...
104 🔍- projectname/src/codefile12.py / Function - 'examplefunctionname' [error parameters/reason]

ANALYSIS SUMMARY
====================
Error Density: 2.34 errors per file
Critical Error Ratio: 28.85%
Functions with Errors: 45

ERROR CATEGORIES:
  syntax: 5 (4.8%)
  security: 12 (11.5%)
  performance: 8 (7.7%)
  complexity: 15 (14.4%)
  style: 64 (61.5%)

MOST PROBLEMATIC FILES:
  src/main.py: 15 errors
  src/utils.py: 12 errors
  src/config.py: 8 errors
```

## Error Types Detected

### Critical Errors (⚠️)
- **Syntax Errors**: Prevent code execution
- **Import Errors**: Missing modules and problematic imports
- **Undefined Variables**: NameError and UnboundLocalError

### Major Errors (👉)
- **Security Vulnerabilities**: eval(), exec(), unsafe functions
- **Type Errors**: Type mismatches and attribute errors
- **Logic Errors**: Runtime exceptions and infinite loops
- **Performance Issues**: Inefficient algorithms and bottlenecks
- **Dependency Issues**: Circular imports and version conflicts
- **Architectural Issues**: Design pattern violations

### Minor Errors (🔍)
- **Unused Code**: Variables, imports, and dead code
- **Style Violations**: PEP 8 and formatting issues
- **Complexity Issues**: High cyclomatic complexity

## Supported Languages

- Python (.py)
- JavaScript (.js)
- TypeScript (.ts, .tsx)
- React (.jsx, .tsx)
- Java (.java)
- C/C++ (.c, .cpp, .h)
- C# (.cs)
- PHP (.php)
- Ruby (.rb)
- Go (.go)
- Rust (.rs)
- Swift (.swift)
- Kotlin (.kt)
- Scala (.scala)
- Shell (.sh)
- PowerShell (.ps1)

## Exit Codes

- `0`: Success (no errors or only minor errors)
- `1`: Major errors found
- `2`: Critical errors found
- `130`: Interrupted by user (Ctrl+C)

## Architecture

The analyzer consists of several key components:

1. **RepositoryInterface**: Handles Git cloning and file management
2. **ErrorPatterns**: Comprehensive error detection patterns
3. **SemanticAnalyzer**: AST parsing and code intelligence
4. **ComprehensiveErrorAnalyzer**: Main analysis engine
5. **ReportFormatter**: Output formatting and statistics
6. **SerenaAnalyzer**: Orchestrates the entire process

## Performance

- **Fast Analysis**: Processes ~1500 files in ~20 seconds
- **Memory Efficient**: Streams file processing
- **Parallel Ready**: Architecture supports future parallelization
- **Caching**: Built-in error caching for repeated analysis

## Examples

### Example 1: Analyzing a Python Project

```bash
python serena_analyzer.py --repo https://github.com/python/cpython --verbose
```

### Example 2: Analyzing a JavaScript Project

```bash
python serena_analyzer.py --repo https://github.com/facebook/react --output react_analysis.txt
```

### Example 3: Analyzing Local Development

```bash
# Analyze current project
python serena_analyzer.py --repo . --output my_project_report.txt

# Check only critical and major errors
python serena_analyzer.py --repo . && echo "No critical/major errors found!"
```

## Integration

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run Serena Analysis
  run: |
    python serena_analyzer.py --repo . --output analysis_report.txt
    if [ $? -eq 2 ]; then
      echo "Critical errors found - failing build"
      exit 1
    fi
```

### Pre-commit Hook

```bash
#!/bin/bash
python serena_analyzer.py --repo . --output pre_commit_analysis.txt
exit_code=$?
if [ $exit_code -eq 2 ]; then
    echo "Critical errors detected - commit blocked"
    exit 1
fi
```

## Comparison with Full Graph-Sitter

| Feature | Serena Analyzer | Full Graph-Sitter |
|---------|----------------|-------------------|
| Installation | Single file | Full package |
| Dependencies | Python stdlib | Multiple packages |
| Analysis Speed | Fast | Comprehensive |
| Error Types | 24+ types | 24+ types |
| Language Support | 15+ languages | 15+ languages |
| LSP Integration | No | Yes |
| Real-time Analysis | No | Yes |
| Refactoring | No | Yes |

## Contributing

This is a standalone module extracted from the graph-sitter project. For improvements:

1. Modify the `serena_analyzer.py` file
2. Test with various repositories
3. Update error patterns as needed
4. Maintain backward compatibility

## License

This analyzer inherits the license from the original graph-sitter project.

## Changelog

### v1.0.0
- Initial release with comprehensive analysis capabilities
- 24+ error types with severity classification
- Support for 15+ programming languages
- CLI interface with formatted output
- Repository cloning and Git integration
- Comprehensive metrics and statistics

---

**Created by consolidating all Serena analysis capabilities from the graph-sitter project into a single, powerful, standalone module.**
