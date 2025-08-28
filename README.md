# Serena Adapter

A Python adapter for the [Serena](https://github.com/oraios/serena) code analysis tool, providing a simple interface to collect diagnostics and issues from codebases.

## Features

- **Diagnostic Collection**: Collect diagnostics (errors, warnings, etc.) from files and projects
- **Symbol Information**: Retrieve symbol information and document structure
- **Code Navigation**: Get references and definitions for symbols
- **Analysis Utilities**: Summarize and group diagnostics by file and severity
- **Command-line Interface**: Run analysis from the command line

## Installation

The adapter requires Python 3.11 and Serena to be installed:

```bash
# Create a Python 3.11 virtual environment
python3.11 -m venv venv-serena

# Activate the virtual environment
source venv-serena/bin/activate  # On Linux/macOS
venv-serena\Scripts\activate     # On Windows

# Install Serena
pip install git+https://github.com/oraios/serena.git
```

## Usage

### As a Library

```python
from serena_adapter import SerenaAdapter, DiagnosticLevel

# Initialize the adapter with a project path
with SerenaAdapter("/path/to/project") as adapter:
    # Get diagnostics for a specific file
    issues = adapter.get_file_diagnostics("path/to/file.py")
    
    # Get diagnostics for the entire project
    all_issues = adapter.get_project_diagnostics()
    
    # Filter diagnostics by severity
    error_issues = adapter.get_project_diagnostics(filter_level=DiagnosticLevel.ERROR)
    
    # Get a summary of diagnostics by severity
    summary = adapter.get_diagnostics_summary(all_issues)
    
    # Group diagnostics by file
    issues_by_file = adapter.group_diagnostics_by_file(all_issues)
    
    # Analyze the entire codebase
    results = adapter.analyze_codebase()
    
    # Get symbol information for a file
    symbols = adapter.get_file_symbols("path/to/file.py")
    
    # Get document overview
    overview = adapter.get_document_overview("path/to/file.py")
    
    # Get references to a symbol
    references = adapter.get_references("path/to/file.py", line=10, character=15)
    
    # Get definition of a symbol
    definition = adapter.get_definition("path/to/file.py", line=10, character=15)
    
    # Get containing symbol at a position
    symbol = adapter.get_containing_symbol("path/to/file.py", line=10, character=15)
```

### Command-line Interface

```bash
# Analyze a project
./serena_adapter.py /path/to/project

# Analyze a project and save results to a file
./serena_adapter.py /path/to/project --output results.json

# Filter diagnostics by severity
./serena_adapter.py /path/to/project --severity error

# Analyze a subdirectory
./serena_adapter.py /path/to/project --path src/module

# Enable verbose output
./serena_adapter.py /path/to/project --verbose
```

## API Reference

### `SerenaAdapter`

The main adapter class for interacting with Serena.

#### Methods

- `get_file_diagnostics(file_path)`: Get diagnostics for a specific file
- `get_project_diagnostics(relative_path="", filter_level=None)`: Get diagnostics for the entire project or a subdirectory
- `get_diagnostics_summary(issues)`: Get a summary of diagnostics by severity level
- `group_diagnostics_by_file(issues)`: Group diagnostics by file
- `get_file_symbols(file_path)`: Get symbols for a specific file
- `get_document_overview(file_path)`: Get an overview of a document
- `analyze_codebase(relative_path="", filter_level=None)`: Analyze the entire codebase or a subdirectory
- `get_references(file_path, line, character)`: Get references to a symbol at a specific position
- `get_definition(file_path, line, character)`: Get the definition of a symbol at a specific position
- `get_containing_symbol(file_path, line, character)`: Get the symbol containing a specific position

### `DiagnosticLevel`

Enum representing diagnostic severity levels.

- `ERROR`: Error-level diagnostics
- `WARNING`: Warning-level diagnostics
- `INFORMATION`: Information-level diagnostics
- `HINT`: Hint-level diagnostics

### `SerenaIssue`

Class representing a diagnostic issue found by Serena.

#### Attributes

- `file_path`: Path to the file containing the issue
- `line`: Line number of the issue (0-based)
- `column`: Column number of the issue (0-based)
- `message`: Message describing the issue
- `level`: Severity level of the issue (DiagnosticLevel)
- `code`: Optional code associated with the issue
- `source`: Optional source of the issue

## License

This project is licensed under the MIT License - see the LICENSE file for details.

