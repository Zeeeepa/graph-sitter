# Enhanced Graph-Sitter Codebase Analysis Tool

This directory contains an enhanced tool for analyzing the Graph-Sitter codebase using its own analysis capabilities.

## Overview

The `analyze_codebase.py` script provides a comprehensive analysis of the Graph-Sitter codebase, focusing on:

- **Statistical Information**: Total files, code files, documentation files, classes, functions, and global variables
- **Error Detection**: Detailed analysis of functions with potential issues, including context and specific error information
- **Entry Point Analysis**: Identification of main entry points with parameter flow and inheritance level analysis
- **Top-Level Files**: Files that aren't imported by other files, representing potential starting points for understanding the codebase
- **Operator Analysis**: Extraction of operators and operands from functions to understand code complexity

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

### Error Analysis
- Detailed list of functions with potential issues
- Error context showing the problematic code
- Error categorization (empty exception handlers, unused parameters, etc.)

### Main Entry Points
- Files that likely serve as entry points to the application
- Function parameter flow analysis
- Inheritance level analysis showing how deeply integrated each entry point is

### Top-Level Files
- Files that aren't imported by other files
- Function listings with parameter information
- Operator and operand analysis

## How It Works

The script leverages Graph-Sitter's own codebase analysis tools to analyze itself:

1. It loads the codebase using the `Codebase` class
2. Analyzes the structure using functions from `codebase_analysis.py`
3. Performs error detection using heuristics and pattern matching
4. Analyzes parameter flow and inheritance relationships
5. Identifies top-level files and entry points
6. Formats and prints the results in a readable format

## Integration

This enhanced analysis tool can be integrated into your development workflow to:

- Identify and fix potential code issues before they cause problems
- Understand the codebase structure and entry points
- Track code quality metrics over time
- Onboard new developers by providing a clear map of the codebase

## Example Output

```
================================================================================
GRAPH-SITTER CODEBASE ANALYSIS
================================================================================

## CODEBASE SUMMARY
--------------------------------------
Total files: 245
  - Code files: 230     - Documentation files: 15
--------------------------------------
Total classes: 87
--------------------------------------
Total functions: 1253 / Functions with errors: 12
--------------------------------------
error 1,
src/graph_sitter/core/function.py[parse_parameters]= Error specifics [Empty exception handler] try:
    # Parse parameter
    pass
except:
    pass
...
error 2,
src/graph_sitter/codebase/codebase_context.py[build_graph]= Error specifics [Very long function (142 lines)] Function spans from line 243 to 385
--------------------------------------
Total global variables: 342
Programming Languages:
  - PYTHON: 230 files
--------------------------------------

## MAIN ENTRY POINTS
(Top Level Inheritance Codefile Name List + Their Flow Function lists with parameters used in these flows and codefile locations)- this should create callable tree flows.
  - src/graph_sitter/cli/cli.py
    Main functions: cli [Parameters callable in/ callable out] [Inheritance 1/4] - [1.src/graph_sitter/cli/cli.py/method='cli'{} - features, scope, analyze]
  - src/graph_sitter/cli/main.py
    Main function: main[Parameters callable in/ callable out] [Inheritance 1/4] - [1.src/graph_sitter/cli/main.py/method='main'{} - parse_args, setup_logging, run_command]

[ To list ALL top level [Highest inheritance level where noone imports them] = And list all project's codefiles like this. even if there are 50 such codefiles.
  - src/graph_sitter/cli/commands/analyze/main.py
    Main function: analyze[Parameters callable in/ callable out]
  - src/graph_sitter/cli/commands/features/main.py
    Main function: features[Parameters callable in/ callable out]
================================================================================
```

