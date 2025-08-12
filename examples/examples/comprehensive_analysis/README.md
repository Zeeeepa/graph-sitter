# Comprehensive Codebase Analysis

This example demonstrates the full capabilities of graph-sitter's comprehensive codebase analysis system. It provides deep insights into code structure, identifies potential issues, and offers actionable recommendations for improving code quality.

## Features

### 🔍 **Dead Code Detection**
- Uses graph traversal from identified entry points
- Identifies unreachable functions, classes, and variables
- Distinguishes between truly dead code and potentially dead code

### 🚪 **Entry Point Identification**
- Automatically identifies main functions and CLI entry points
- Detects web framework routes and decorated functions
- Finds top-level classes and exported symbols

### 🔧 **Unused Parameter Detection**
- Analyzes function scopes to find unused parameters
- Handles special cases like `self`, `cls`, `*args`, `**kwargs`
- Provides function-specific unused parameter lists

### 📦 **Import Analysis**
- **Unused Imports**: Finds imports that are never referenced
- **Circular Imports**: Detects import cycles using graph algorithms
- **Unresolved Imports**: Identifies imports that cannot be resolved

### 📞 **Call Site Analysis**
- Validates function calls against function signatures
- Detects argument count mismatches
- Identifies unresolved function calls

### 🏷️ **Symbol Usage Analysis**
- Comprehensive symbol usage tracking across the codebase
- Dependency mapping and relationship analysis
- Usage statistics and patterns

## Usage

### Basic Usage

```bash
# Analyze FastAPI codebase (default)
python run.py

# Analyze a specific GitHub repository
python run.py fastapi/fastapi
python run.py owner/repository

# Analyze a local repository
python run.py /path/to/local/repo

# Analyze with full GitHub URL
python run.py https://github.com/fastapi/fastapi
```

### Advanced Options

```bash
# Run with individual analysis demonstrations
python run.py --demo

# Save results to JSON file
python run.py --output results.json

# Combine options
python run.py fastapi/fastapi --demo --output fastapi_analysis.json
```

## Example Output

```
🔍 COMPREHENSIVE CODEBASE ANALYSIS REPORT
================================================================================

📊 CODEBASE OVERVIEW:
   Files: 156
   Functions: 1,247
   Classes: 89
   Symbols: 1,456
   Imports: 892
   External Modules: 234

🚪 ENTRY POINTS:
   Main Functions: 3
     - main
     - cli_main
     - run_server
   Web Routes: 45
     - get_items
     - create_item
     - update_item
   Exported Symbols: 67

💀 DEAD CODE ANALYSIS:
   Dead Functions: 12
     - unused_helper
     - deprecated_function
     - old_implementation
   Potentially Dead: 8
     - rarely_used_utility
     - legacy_converter

📦 IMPORT ANALYSIS:
   Total Imports: 892
   Unused Imports: 23
   Circular Import Cycles: 2
   Unresolved Imports: 5

📞 CALL SITE ANALYSIS:
   Total Function Calls: 3,456
   Resolved Calls: 3,234
   Resolution Rate: 93.6%
   Argument Mismatches: 7

💡 RECOMMENDATIONS:
   1. Consider removing 12 dead functions and 3 dead classes
   2. Remove 23 unused imports to clean up dependencies
   3. Resolve 2 circular import cycles to improve architecture
   4. Review 15 functions with unused parameters
```

## Integration with Existing Analysis Functions

The comprehensive analysis builds on the existing graph-sitter analysis functions:

```python
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    comprehensive_analysis,
    print_analysis_report
)

# Load codebase
codebase = Codebase.from_repo('fastapi/fastapi')

# Run comprehensive analysis
results = comprehensive_analysis(codebase)

# Print formatted report
print_analysis_report(results)

# Access individual analysis results
entry_points = results['entry_points']
dead_code = results['dead_code']
import_issues = results['import_analysis']
```

## Individual Analysis Functions

You can also use individual analysis functions for specific needs:

```python
from graph_sitter.codebase.codebase_analysis import (
    identify_entry_points,
    detect_dead_code,
    detect_unused_parameters,
    analyze_imports,
    analyze_call_sites
)

# Individual analyses
entry_points = identify_entry_points(codebase)
dead_code = detect_dead_code(codebase)
unused_params = detect_unused_parameters(codebase)
import_analysis = analyze_imports(codebase)
call_analysis = analyze_call_sites(codebase)
```

## Configuration

The analysis uses comprehensive configuration for optimal results:

```python
from graph_sitter.configs import CodebaseConfig

config = CodebaseConfig(
    method_usages=True,           # Enable method usage tracking
    import_resolution_paths=True, # Enable import resolution
    full_range_index=True,        # Enable full range indexing
    sync_enabled=True            # Enable synchronization
)

codebase = Codebase.from_repo('owner/repo', config=config)
```

## Output Formats

### Console Output
- Formatted, human-readable analysis report
- Color-coded sections and statistics
- Actionable recommendations

### JSON Output
- Machine-readable results for further processing
- Complete analysis data structure
- Integration with other tools and workflows

### Example JSON Structure
```json
{
  "codebase_summary": {
    "total_files": 156,
    "total_functions": 1247,
    "total_classes": 89
  },
  "entry_points": {
    "main_functions": ["main", "cli_main"],
    "web_routes": ["get_items", "create_item"]
  },
  "dead_code": {
    "dead_functions": ["unused_helper", "deprecated_function"],
    "dead_classes": ["OldImplementation"]
  },
  "import_analysis": {
    "unused_imports": [
      {"file": "utils.py", "import": "unused_module"}
    ],
    "circular_imports": [
      {"files": ["module_a.py", "module_b.py"], "cycle_length": 2}
    ]
  },
  "recommendations": [
    "Consider removing 12 dead functions and 3 dead classes",
    "Remove 23 unused imports to clean up dependencies"
  ]
}
```

## Use Cases

### Code Quality Assessment
- Identify technical debt and cleanup opportunities
- Measure code health and maintainability
- Track improvements over time

### Refactoring Planning
- Find safe-to-remove dead code
- Identify architectural issues (circular imports)
- Plan parameter cleanup and function optimization

### Code Review Enhancement
- Automated detection of common issues
- Comprehensive analysis for large codebases
- Integration with CI/CD pipelines

### Architecture Analysis
- Understand entry points and code flow
- Analyze dependency relationships
- Identify architectural patterns and anti-patterns

## Requirements

- Python 3.8+
- graph-sitter framework
- networkx (for circular import detection)
- Access to analyze remote repositories (for GitHub analysis)

## Performance Notes

- Initial analysis may take several minutes for large codebases
- Results are cached for subsequent runs
- Memory usage scales with codebase size
- Optimized graph traversal algorithms for efficiency

## Limitations

- Parameter usage detection is simplified (may have false positives)
- Dynamic code patterns may not be fully captured
- Language-specific patterns may require customization
- Large codebases may require significant memory

## Contributing

To extend the analysis capabilities:

1. Add new analysis functions to `src/graph_sitter/codebase/codebase_analysis.py`
2. Update the `comprehensive_analysis()` function to include new analyses
3. Add corresponding output formatting in `print_analysis_report()`
4. Update this README with new features

## Related Examples

- `delete_dead_code/` - Basic dead code detection
- `api-lsp-error/` - Code metrics and complexity analysis
- `removing_import_loops_in_pytorch/` - Import cycle resolution
- `repo_analytics/` - Repository-wide analytics
