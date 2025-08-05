# Graph-Sitter Codebase Analysis Tool

This tool provides a comprehensive analysis of your codebase, focusing on error detection, entry points, and inheritance relationships. It uses graph-sitter's own analysis capabilities to analyze itself or any other repository.

## Features

- **Statistical Analysis**: Get counts of files, classes, functions, and global variables
- **Error Detection**: Find actual code issues (not just style problems)
- **Entry Point Analysis**: Identify main entry points and their parameter flows
- **Top-Level File Identification**: Find files that aren't imported by others
- **Interactive HTML Report**: View results in an interactive HTML page with expandable sections
- **GitHub Repository Analysis**: Analyze any GitHub repository by URL

## Usage

```bash
# Analyze local codebase
python scripts/analyze_codebase.py

# Analyze GitHub repository
python scripts/analyze_codebase.py --github-repo https://github.com/Zeeeepa/graph-sitter

# Specify output HTML file
python scripts/analyze_codebase.py --output my_analysis.html
```

## Output

The tool generates two types of output:

1. **Console Output**: A text-based summary of the analysis results
2. **HTML Report**: An interactive HTML page with expandable sections for detailed exploration

### HTML Report Features

- **Expandable Sections**: Click on section headers to expand/collapse details
- **Error Highlighting**: Errors are highlighted with context for easy identification
- **Function Flow Visualization**: See how functions call each other
- **Parameter Analysis**: View parameters used in function calls
- **Inheritance Level Indicators**: See how deeply files are imported by others

## Error Types Detected

The tool detects the following types of actual code issues:

- **Empty Exception Handlers**: Functions with `except: pass` patterns
- **Very Long Functions**: Functions over 100 lines
- **Too Many Parameters**: Functions with more than 7 parameters

Note: Style issues like missing docstrings or unused parameters are intentionally not reported.

## Requirements

- Python 3.6+
- graph-sitter
- jinja2 (automatically installed if missing)

## Example

```bash
# Analyze the graph-sitter repository
python scripts/analyze_codebase.py --github-repo https://github.com/Zeeeepa/graph-sitter

# Open the generated HTML report
open codebase_analysis.html
```

