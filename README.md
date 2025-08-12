# Comprehensive Codebase Analysis Tool

This tool performs a deep analysis of a codebase using the `graph-sitter` library to identify various issues and provide insights about the codebase structure.

## Features

The analysis identifies:

- **Dead code** - Unused functions, classes, variables
- **Unused parameters** - Parameters defined but never used in functions
- **Wrong call sites** - Incorrect function calls (e.g., wrong number of arguments)
- **Wrong imports** - Unused, circular, or unresolved imports
- **Symbol usages** - How symbols are used throughout the codebase
- **Dependencies** - Relationships between code elements
- **Class attributes and methods** - Properties and methods of classes
- **Function parameters** - Parameters of functions
- **Entry points** - Top-level functions, classes that act as operators

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install graph-sitter networkx rich
```

## Usage

```bash
python graph-sitter_analysis.py <repo_name> [--output-format=<format>] [--language=<lang>]
```

### Arguments

- `repo_name`: GitHub repository in the format 'owner/repo' or local path
- `--output-format`: Output format (text, json, markdown) [default: text]
- `--language`: Force language detection (python, typescript) [default: auto-detect]

### Examples

Analyze a GitHub repository:
```bash
python graph-sitter_analysis.py fastapi/fastapi
```

Analyze a local repository with JSON output:
```bash
python graph-sitter_analysis.py ./my-local-repo --output-format=json
```

Force Python language detection:
```bash
python graph-sitter_analysis.py django/django --language=python
```

## Output

The tool provides a comprehensive analysis report that includes:

- **Summary** - Overview of the codebase (files, classes, functions, issues)
- **Entry Points** - Main functions, API endpoints, CLI commands, etc.
- **Dead Code** - Unused code that can be safely removed
- **Issues** - Problems found in the codebase, categorized by severity:
  - **Critical** - Serious issues that should be fixed immediately
  - **Major** - Important issues that should be addressed
  - **Minor** - Less important issues that could be improved

## Output Formats

- **Text** - Human-readable console output with color highlighting
- **JSON** - Machine-readable JSON format for further processing
- **Markdown** - Markdown format for documentation or GitHub issues

## License

MIT

