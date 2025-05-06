# Graph-Sitter Codebase Analysis Tool

This directory contains a tool for analyzing the Graph-Sitter codebase using its own analysis capabilities.

## Overview

The `analyze_codebase.py` script provides a comprehensive analysis of the Graph-Sitter codebase, including:

- Total number of files, code files, and documentation files
- Class hierarchy and inheritance depth
- Function statistics and error detection
- Main entry points and core functionality
- Symbol usage and dependencies

## Usage

```bash
# Analyze the local codebase
python scripts/analyze_codebase.py

# Analyze a specific GitHub repository
python scripts/analyze_codebase.py --github-repo https://github.com/Zeeeepa/graph-sitter
```

## Output

The script outputs a detailed analysis report that includes:

### Codebase Summary
- Total number of files (code and documentation)
- Total number of classes, functions, and global variables
- Programming languages used in the codebase

### Main Entry Points
- Files that likely serve as entry points to the application
- Main functions and CLI interfaces

### Class Hierarchy
- Classes with the deepest inheritance chains
- Classes with the most methods

### Function Statistics
- Functions with the most parameters
- Functions with the most dependencies
- Total number of functions and those with potential issues

### Potential Issues
- List of functions with potential code quality issues
- File paths and error descriptions

## How It Works

The script leverages Graph-Sitter's own codebase analysis tools to analyze itself:

1. It loads the codebase using `Codebase` class
2. Analyzes the structure using functions from `codebase_analysis.py`
3. Calculates additional metrics like depth of inheritance
4. Identifies potential code quality issues using heuristics
5. Formats and prints the results in a readable format

## Integration

This tool can be integrated into your development workflow to:

- Monitor code quality over time
- Identify complex areas of the codebase
- Find potential entry points for new developers
- Detect potential issues before they cause problems

## Example

```
================================================================================
GRAPH-SITTER CODEBASE ANALYSIS
================================================================================

## CODEBASE SUMMARY
Total files: 245
  - Code files: 230
  - Documentation files: 15
Total classes: 87
Total functions: 1253
Total global variables: 342

Programming Languages:
  - PYTHON: 230 files

## MAIN ENTRY POINTS
  - src/graph_sitter/cli/cli.py
  - src/graph_sitter/cli/main.py
    Main function: main

## CLASS HIERARCHY
Classes with deepest inheritance:
  - CodebaseContext: 3 levels
  - Codebase: 2 levels
  - Function: 2 levels

Classes with most methods:
  - Codebase: 45 methods
  - CodebaseContext: 32 methods
  - Function: 28 methods

## FUNCTION STATISTICS
Functions with most parameters:
  - create_pr: 8 parameters
  - analyze_code: 7 parameters
  - process_file: 6 parameters

Functions with most dependencies:
  - build_graph: 15 dependencies
  - process_symbols: 12 dependencies
  - analyze_imports: 10 dependencies

## POTENTIAL ISSUES
Found 12 potential issues:
  - src/graph_sitter/core/function.py: parse_parameters - Empty exception handler
  - src/graph_sitter/codebase/codebase_context.py: build_graph - Very long function (142 lines)
================================================================================
```

