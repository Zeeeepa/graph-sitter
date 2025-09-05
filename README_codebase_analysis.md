# Comprehensive Codebase Analysis Tool

A unified analysis tool that combines all graph_sitter capabilities to provide comprehensive codebase insights including dead code detection, function interconnections, error categorization, and much more.

## Features

🔍 **Comprehensive Analysis**
- Dead code detection with blast radius analysis
- Function interconnection mapping and call graphs
- Error categorization by severity (Critical, Major, Minor)
- Entry point identification
- Type coverage analysis
- Halstead complexity metrics

🌳 **Visual Tree Structure**
- Repository tree with issue counts and severity indicators
- Entry point highlighting
- File and directory issue aggregation

📊 **Multiple Output Formats**
- Console output with emoji indicators and tree structure
- JSON reports for programmatic access
- Detailed function context analysis

🚀 **Flexible Input Support**
- Local repository paths
- Remote repository URLs (GitHub, GitLab, etc.)
- Built-in demo mode

## Installation

Make sure you're in the graph_sitter repository root and have graph_sitter installed:

```bash
pip install -e .
```

## Usage

### Basic Usage

```bash
# Analyze a local repository
python codebase_analysis.py /path/to/your/repo

# Analyze a remote repository
python codebase_analysis.py https://github.com/user/repo.git

# Run demo on graph_sitter itself
python codebase_analysis.py --demo
```

### Advanced Options

```bash
# Generate JSON report
python codebase_analysis.py /path/to/repo --format json --output report.json

# Enable verbose logging
python codebase_analysis.py /path/to/repo --verbose

# Save console output to file
python codebase_analysis.py /path/to/repo --output analysis.txt
```

### Command Line Options

- `repo_path`: Path to local repository or URL to remote repository
- `--demo`: Run demo analysis on the graph_sitter codebase itself
- `--format {console,json}`: Output format (default: console)
- `--output FILE`: Output file path
- `--verbose`: Enable verbose logging
- `--lazy-graph`: Enable lazy graph parsing for better performance (default: True)

## Output Format

### Console Output

The console output provides a comprehensive analysis with the following sections:

```
🚀 COMPREHENSIVE CODEBASE ANALYSIS
============================================================

📊 ANALYSIS SUMMARY:
------------------------------
📁 Total Files: 156
🔧 Total Functions: 1,234
🏛️  Total Classes: 89
🚨 Total Issues: 45
⚠️  Critical Issues: 5
👉 Major Issues: 20
🔍 Minor Issues: 20
💀 Dead Code Items: 12
🎯 Entry Points: 3

🌳 REPOSITORY STRUCTURE:
------------------------------
├── 📁 src/
│   ├── 📁 graph_sitter/ [⚠️ Critical: 2] [👉 Major: 8] [🔍 Minor: 5]
│   │   ├── 📁 core/ [🟩 Entrypoint: 1] [⚠️ Critical: 1]
│   │   │   └── 🐍 codebase.py [🟩 Entrypoint]
│   │   └── 📁 python/ [👉 Major: 4] [🔍 Minor: 3]
│   └── 📁 tests/
└── 🐍 README.md

🚨 ISSUES BY SEVERITY:
-------------------------
CRITICAL (5 issues):
1 ⚠️- src/graph_sitter/core/function.py / Function - 'parse_parameters' [Syntax error: invalid syntax]
...

🌟 MOST IMPORTANT FUNCTIONS:
-----------------------------------
📞 Makes Most Calls: process_codebase
   📊 Call Count: 45
   🎯 Calls: parse_file, analyze_symbols, build_graph...

📈 Most Called: get_symbol
   📊 Usage Count: 123

📝 TYPE COVERAGE ANALYSIS:
------------------------------
Parameters: 67.3% (234/348 typed)
Return types: 45.2% (156/345 typed)
Class attributes: 23.1% (45/195 typed)

📊 HALSTEAD METRICS:
--------------------
📝 Operators (n1): 89
📝 Operands (n2): 456
📊 Total Operators (N1): 2,345
📊 Total Operands (N2): 5,678
📚 Vocabulary: 545
📏 Length: 8,023
📦 Volume: 72,456.78
⚡ Difficulty: 12.34
💪 Effort: 894,567.89

🎯 ENTRY POINTS:
---------------
📁 src/graph_sitter/cli/main.py
   🟩 Function: main (2 params)
📁 src/graph_sitter/core/codebase.py
   🟩 Function: from_repo (1 params)
```

### JSON Output

The JSON output provides structured data suitable for programmatic access:

```json
{
  "summary": {
    "total_files": 156,
    "total_functions": 1234,
    "total_classes": 89,
    "total_issues": 45,
    "critical_issues": 5,
    "major_issues": 20,
    "minor_issues": 20,
    "dead_code_items": 12,
    "entry_points": 3
  },
  "most_important_functions": {
    "most_calls": {
      "name": "process_codebase",
      "call_count": 45,
      "calls": ["parse_file", "analyze_symbols", "build_graph"]
    },
    "most_called": {
      "name": "get_symbol",
      "usage_count": 123
    }
  },
  "function_contexts": {
    "process_codebase": {
      "name": "process_codebase",
      "filepath": "src/graph_sitter/core/codebase.py",
      "parameters": ["repo_path", "config"],
      "dependencies": ["Parser", "SymbolResolver"],
      "function_calls": ["parse_file", "analyze_symbols"],
      "called_by": ["main", "cli_handler"],
      "issues": [],
      "is_entry_point": true,
      "is_dead_code": false,
      "max_call_chain": ["process_codebase", "parse_file", "analyze_symbols"],
      "complexity_score": 8.5
    }
  },
  "issues_by_severity": {
    "critical": [
      {
        "severity": "critical",
        "message": "Syntax error: invalid syntax",
        "filepath": "src/graph_sitter/core/function.py",
        "line_number": 45,
        "function_name": "parse_parameters",
        "class_name": null,
        "issue_type": "syntax_error"
      }
    ]
  },
  "dead_code_analysis": {
    "total_dead_functions": 8,
    "total_dead_classes": 4,
    "dead_code_items": [
      {
        "name": "unused_helper",
        "type": "function",
        "filepath": "src/graph_sitter/utils.py",
        "reason": "No usages found",
        "blast_radius": ["helper_dependency", "another_dep"],
        "line_number": 123
      }
    ]
  },
  "halstead_metrics": {
    "n1": 89,
    "n2": 456,
    "N1": 2345,
    "N2": 5678,
    "vocabulary": 545,
    "length": 8023,
    "volume": 72456.78,
    "difficulty": 12.34,
    "effort": 894567.89
  },
  "type_coverage": {
    "parameter_coverage": 67.3,
    "return_type_coverage": 45.2,
    "attribute_coverage": 23.1,
    "total_parameters": 348,
    "typed_parameters": 234,
    "total_functions": 345,
    "typed_returns": 156,
    "total_attributes": 195,
    "typed_attributes": 45
  },
  "repository_tree": {
    "src": {
      "type": "directory",
      "children": {
        "graph_sitter": {
          "type": "directory",
          "issues": {"critical": 2, "major": 8, "minor": 5},
          "children": {
            "core": {
              "type": "directory",
              "issues": {"critical": 1, "major": 0, "minor": 0},
              "children": {
                "codebase.py": {
                  "type": "file",
                  "filepath": "src/graph_sitter/core/codebase.py",
                  "issues": {"critical": 0, "major": 0, "minor": 0},
                  "functions": 15,
                  "classes": 1
                }
              }
            }
          }
        }
      }
    }
  },
  "entry_points": [
    {
      "filepath": "src/graph_sitter/cli/main.py",
      "filename": "main.py",
      "main_functions": [
        {"name": "main", "parameters": 2}
      ],
      "is_executable": true
    }
  ]
}
```

## Analysis Types

### 1. Dead Code Detection
- Identifies unused functions and classes
- Calculates blast radius (what would be affected if removed)
- Categorizes by severity (functions = minor, classes = major)

### 2. Function Interconnections
- Maps function call relationships
- Identifies most called and most calling functions
- Builds call chains and dependency graphs

### 3. Error Analysis
- Syntax error detection
- Import resolution issues
- Categorizes by severity:
  - **Critical**: Syntax errors, parse failures
  - **Major**: Unresolved imports, unused classes
  - **Minor**: Unused functions, style issues

### 4. Entry Point Detection
- Identifies main entry points (main.py, app.py, cli.py, etc.)
- Detects `__name__ == "__main__"` patterns
- Finds main/run/start/cli functions

### 5. Type Coverage Analysis
- Parameter type annotation coverage
- Return type annotation coverage
- Class attribute type annotation coverage

### 6. Halstead Complexity Metrics
- Operator and operand analysis
- Vocabulary, length, volume calculations
- Difficulty and effort metrics

## Integration with graph_sitter

This tool leverages the full power of the graph_sitter library:

- **Codebase**: Main interface for repository analysis
- **Function/Class/Symbol**: Core entities with dependency tracking
- **Import Resolution**: Tracks import relationships and resolution
- **Usage Analysis**: Identifies where symbols are used
- **Dependency Analysis**: Maps symbol dependencies

## Performance Considerations

- Uses lazy graph parsing by default for better performance
- Limits tree depth in console output to prevent excessive output
- Handles large codebases with progress tracking
- Includes timeout handling for long-running analyses

## Error Handling

- Graceful handling of syntax errors and parse failures
- Continues analysis even if individual files fail
- Comprehensive logging with different verbosity levels
- Automatic cleanup of temporary directories for remote repos

## Examples

### Analyzing a Python Project

```bash
python codebase_analysis.py /path/to/python/project
```

### Analyzing a Remote Repository

```bash
python codebase_analysis.py https://github.com/python/cpython.git --format json --output cpython_analysis.json
```

### Running the Demo

```bash
python codebase_analysis.py --demo
```

This will analyze the graph_sitter codebase itself and demonstrate all the analysis capabilities.

## Contributing

This tool is part of the graph_sitter project. To contribute:

1. Make sure you understand the graph_sitter architecture
2. Add new analysis types by extending the `CodebaseAnalyzer` class
3. Update the output formatters to handle new analysis results
4. Add tests for new functionality

## License

This tool is part of the graph_sitter project and follows the same license terms.
