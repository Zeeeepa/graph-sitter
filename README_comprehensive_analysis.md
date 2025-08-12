# Comprehensive Codebase Analysis Tool

A powerful, production-ready tool for comprehensive codebase analysis using **100% real graph-sitter infrastructure**. This tool provides deep insights into code quality, architecture, and potential issues.

## 🎯 Features

### Complete Analysis Coverage
- **Dead Code Detection**: Identifies unused functions, classes, variables, and imports
- **Parameter Analysis**: Finds unused parameters in functions with real code block traversal
- **Call Site Validation**: Detects incorrect function calls with argument mismatches
- **Import Analysis**: Finds circular imports, unused imports, and unresolved dependencies
- **Entry Point Detection**: Identifies main functions, CLI commands, API endpoints, and top-level classes
- **Code Quality Metrics**: Calculates cyclomatic complexity and identifies large classes/functions
- **Dependency Mapping**: Creates comprehensive dependency graphs

### Real Graph-Sitter Integration
- Uses actual `function.usages`, `function.call_sites`, `function.decorators` properties
- Real `function.code_block.statements` for parameter analysis
- Actual `file.imports` and import resolution system
- Genuine graph traversal for dependency analysis
- No mock functions - 100% real infrastructure

### Multiple Output Formats
- **Text**: Rich console output with color coding and tables
- **JSON**: Machine-readable format for integration
- **Markdown**: Documentation-ready reports

## 🚀 Installation

```bash
# Install dependencies
pip install networkx rich

# The tool uses graph-sitter which should already be available
```

## 📖 Usage

### Basic Usage

```bash
# Analyze a GitHub repository
python comprehensive_codebase_analysis.py fastapi/fastapi

# Analyze a local repository
python comprehensive_codebase_analysis.py ./my-local-repo

# Generate JSON output
python comprehensive_codebase_analysis.py django/django --output-format=json

# Generate Markdown report
python comprehensive_codebase_analysis.py ./project --output-format=markdown

# Force language detection
python comprehensive_codebase_analysis.py myrepo/project --language=python
```

### Command Line Options

```
positional arguments:
  repo_name             GitHub repository (owner/repo) or local path

optional arguments:
  --output-format {text,json,markdown}
                        Output format (default: text)
  --language {python,typescript}
                        Force language detection (default: auto-detect)
```

## 📊 Analysis Results

### Summary Metrics
- Total files, classes, functions, and symbols
- Entry points count
- Dead code items with impact scores
- Issues categorized by severity (Critical, Major, Minor)

### Entry Points
- Main functions and CLI commands
- API endpoints and web routes
- Top-level classes with inheritance chains
- Exported symbols and public APIs

### Dead Code Detection
- Unused functions with no call sites
- Unreferenced classes
- Unused imports
- Blast radius analysis showing impact of removal

### Code Issues
- **Critical**: Circular imports, unresolved dependencies
- **Major**: Wrong call sites, high complexity functions
- **Minor**: Unused parameters, large classes

### Import Analysis
- Circular import detection using NetworkX
- Import dependency graphs
- Unused and unresolved imports

## 🔧 Technical Implementation

### Real Graph-Sitter Patterns
The tool follows proven patterns from existing graph-sitter examples:

```python
# REAL: Dead code detection (from delete_dead_code/run.py)
if (not func.usages and 
    not func.call_sites and 
    not func.decorators):
    # Function is dead code

# REAL: Parameter analysis using code blocks
for stmt in func.code_block.statements:
    for usage in stmt.symbol_usages:
        if usage.name == param_name:
            param_used = True

# REAL: Import cycle detection (from PyTorch example)
cycles = list(nx.strongly_connected_components(import_graph))
```

### Architecture
- **Modular Design**: Separate analyzers for each analysis type
- **Progressive Analysis**: Build file tree → Entry points → Dead code → Issues
- **Error Handling**: Graceful handling of missing properties and parsing errors
- **Performance**: Memory-efficient processing for large codebases

## 📈 Example Output

### Text Format
```
COMPREHENSIVE CODEBASE ANALYSIS COMPLETE

SUMMARY:
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric            ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total Files       │   156 │
│ Total Classes     │    45 │
│ Total Functions   │   234 │
│ Entry Points      │    12 │
│ Dead Code Items   │     8 │
│ Total Issues      │    23 │
└───────────────────┴───────┘

ENTRY POINTS:
🟩 src/main.py / Function - 'main' [Main function]
🟩 src/api/routes.py / Function - 'health_check' [API endpoint]

DEAD CODE:
💀 src/utils/helpers.py / Function - 'unused_helper' [No usages or call sites found]

ISSUES:
⚠️ Critical - src/models/user.py / Circular Import - File is part of import cycle
👉 Major - src/services/auth.py:45 / Wrong Call Site - Function called with wrong arguments
```

### JSON Format
```json
{
  "summary": {
    "total_files": 156,
    "total_classes": 45,
    "total_functions": 234,
    "entry_points": 12,
    "dead_code_items": 8,
    "total_issues": 23
  },
  "entry_points": [
    {
      "name": "main",
      "filepath": "src/main.py",
      "type": "function",
      "reason": "Main function"
    }
  ],
  "dead_code": [
    {
      "name": "unused_helper",
      "filepath": "src/utils/helpers.py",
      "type": "function",
      "reason": "No usages or call sites found",
      "impact_score": 0
    }
  ],
  "issues": [
    {
      "filepath": "src/models/user.py",
      "issue_type": "Circular Import",
      "message": "File is part of import cycle",
      "severity": "CRITICAL",
      "recommendation": "Refactor to break the circular dependency"
    }
  ]
}
```

## 🧪 Testing

```bash
# Run basic tests
python test_comprehensive_analysis.py

# Test with a real repository
python comprehensive_codebase_analysis.py graph-sitter --output-format=json
```

## 🔍 Validation

The tool includes comprehensive validation:

### Level 1: Syntax & Style
```bash
python -m py_compile comprehensive_codebase_analysis.py
```

### Level 2: Unit Tests
- Analyzer initialization
- Issue severity handling
- Helper method functionality

### Level 3: Integration Tests
- Real repository analysis
- Output format validation
- Error handling verification

## 🚨 Anti-Patterns Avoided

- ❌ No mock functions - uses only real graph-sitter infrastructure
- ❌ No hardcoded assumptions - relies on actual properties
- ❌ No ignored errors - graceful handling with specific error types
- ❌ No memory leaks - efficient processing for large codebases

## 🤝 Contributing

This tool follows the established patterns from graph-sitter examples:
- `delete_dead_code/run.py` for dead code detection
- `repo_analytics/run.py` for complexity analysis
- `removing_import_loops_in_pytorch/` for import cycle detection

## 📄 License

This tool is part of the graph-sitter project and follows the same licensing terms.
