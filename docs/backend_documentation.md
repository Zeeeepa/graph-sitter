# Graph-sitter Backend Documentation

## Overview

Graph-sitter is a powerful Python library for analyzing and manipulating codebases. It combines the parsing capabilities of [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) with graph algorithms from [rustworkx](https://github.com/Qiskit/rustworkx) to enable scriptable, multi-language code manipulation at scale.

This documentation provides a comprehensive guide to the backend architecture, components, and usage patterns of Graph-sitter.

## Table of Contents

1. [Architecture](#architecture)
2. [Core Components](#core-components)
3. [Language Support](#language-support)
4. [Key Features](#key-features)
5. [API Reference](#api-reference)
6. [Usage Examples](#usage-examples)
7. [Extension Modules](#extension-modules)
8. [CLI Interface](#cli-interface)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)

## Architecture

Graph-sitter is built around a core architecture that enables code analysis and manipulation across multiple programming languages. The system is designed with the following key architectural components:

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Graph-sitter Core                      │
├─────────────┬─────────────┬────────────────┬───────────────┤
│  Codebase   │    Core     │  Language      │  Extensions   │
│  Management │  Symbols    │  Engines       │               │
└─────────────┴─────────────┴────────────────┴───────────────┘
        │             │             │               │
        ▼             ▼             ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌───────────────┐
│ Python      │ │ TypeScript  │ │ JavaScript │ │ Visualization │
│ Support     │ │ Support     │ │ Support    │ │ & Analysis    │
└─────────────┘ └─────────────┘ └────────────┘ └───────────────┘
        │             │             │               │
        └─────────────┴─────────────┴───────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  CLI & API Layer  │
                    └───────────────────┘
```

### Component Interaction

1. **Parsing Layer**: Uses Tree-sitter to parse source code into abstract syntax trees (ASTs)
2. **Graph Construction**: Builds a graph representation of the codebase with symbols as nodes and relationships as edges
3. **Symbol Management**: Provides APIs to interact with and manipulate code symbols (functions, classes, etc.)
4. **Code Generation**: Enables programmatic code modifications while maintaining correctness

## Core Components

### Codebase

The `Codebase` class is the main entry point for interacting with a codebase. It provides methods to:

- Load and parse a codebase
- Access files, directories, and symbols
- Perform code transformations
- Manage git operations

```python
from graph_sitter import Codebase

# Initialize a codebase from a local directory
codebase = Codebase("./path/to/repo")

# Or from a GitHub repository
codebase = Codebase.from_repo("owner/repository")

# Access files and symbols
for file in codebase.files:
    print(f"File: {file.filepath}")
    
    for function in file.functions:
        print(f"  Function: {function.name}")
```

### Symbol

The `Symbol` class represents a code entity such as a function, class, or variable. It provides methods to:

- Access symbol properties (name, source, etc.)
- Find usages and dependencies
- Modify symbol attributes
- Move symbols between files

```python
# Get a function by name
function = codebase.get_function("process_data")

# View function source
print(function.source)

# Find all usages of the function
for usage in function.usages:
    print(f"Used in: {usage.usage_symbol.filepath}")

# Move the function to another file
function.move_to_file("utils.py")
```

### File

The `File` class represents a source code file. It provides methods to:

- Access file content and metadata
- Find symbols defined in the file
- Add, remove, or modify symbols
- Manage imports

```python
# Get a file by path
file = codebase.get_file("src/main.py")

# View file content
print(file.content)

# Get all functions in the file
for function in file.functions:
    print(function.name)

# Add an import to the file
file.add_import("from utils import helper")
```

### Directory

The `Directory` class represents a directory in the codebase. It provides methods to:

- Access files and subdirectories
- Find symbols defined in the directory
- Perform operations on all files in the directory

```python
# Get a directory by path
directory = codebase.get_directory("src/utils")

# Get all files in the directory
for file in directory.files:
    print(file.filepath)

# Get all functions in the directory
for function in directory.functions:
    print(function.name)
```

## Language Support

Graph-sitter supports multiple programming languages through language-specific modules:

### Python Support

The Python module provides specialized support for Python code:

- Python-specific AST parsing
- Type annotation handling
- Import resolution
- Docstring management

```python
# Python-specific operations
py_file = codebase.get_file("main.py")
py_function = py_file.get_function("process_data")

# Add type annotations
py_function.add_parameter_type_annotation("data", "Dict[str, Any]")
py_function.add_return_type_annotation("List[Result]")

# Add docstring
py_function.set_docstring("""
Process the input data and return results.

Args:
    data: The input data to process

Returns:
    A list of processed results
""")
```

### TypeScript/JavaScript Support

The TypeScript module provides specialized support for TypeScript and JavaScript code:

- TypeScript/JavaScript AST parsing
- Interface and type handling
- JSX/React component support
- Export/import management

```python
# TypeScript-specific operations
ts_file = codebase.get_file("component.tsx")
ts_function = ts_file.get_function("Component")

# Add type annotations
ts_function.add_parameter_type_annotation("props", "ComponentProps")

# Add interface
ts_file.add_interface("ComponentProps", {
    "name": "string",
    "count": "number",
    "items": "Item[]"
})
```

## Key Features

### Code Analysis

Graph-sitter provides powerful code analysis capabilities:

- **Dependency Analysis**: Find all dependencies of a symbol
- **Usage Analysis**: Find all usages of a symbol
- **Call Graph Analysis**: Analyze function call relationships
- **Import Analysis**: Analyze import relationships

```python
# Analyze function dependencies
function = codebase.get_function("process_data")
dependencies = function.dependencies

# Analyze function usages
usages = function.usages

# Get call graph
call_graph = codebase.viz.get_call_graph("process_data")
```

### Code Transformation

Graph-sitter enables programmatic code transformations:

- **Symbol Renaming**: Rename symbols across the codebase
- **Symbol Moving**: Move symbols between files
- **Code Generation**: Generate new code
- **Code Refactoring**: Refactor existing code

```python
# Rename a function
function = codebase.get_function("old_name")
function.rename("new_name")

# Move a function to another file
function.move_to_file("utils.py")

# Add a new function
file = codebase.get_file("main.py")
file.add_function("new_function", ["param1", "param2"], "return param1 + param2")
```

### Visualization

Graph-sitter provides visualization capabilities:

- **Call Graph Visualization**: Visualize function call relationships
- **Dependency Graph Visualization**: Visualize symbol dependencies
- **Import Graph Visualization**: Visualize import relationships

```python
# Visualize call graph
codebase.viz.visualize_call_graph("process_data")

# Visualize dependency graph
codebase.viz.visualize_dependency_graph("process_data")
```

### Git Integration

Graph-sitter integrates with Git:

- **Commit Changes**: Commit changes to the repository
- **Create Branches**: Create new branches
- **Create PRs**: Create pull requests
- **Review PRs**: Review pull requests

```python
# Commit changes
codebase.commit("Refactor process_data function")

# Create a branch
codebase.create_branch("feature/refactor-process-data")

# Create a PR
codebase.create_pr("Refactor process_data function", "This PR refactors the process_data function")
```

## API Reference

### Codebase API

The `Codebase` class is the main entry point for interacting with a codebase.

#### Initialization

```python
# Initialize from a local directory
codebase = Codebase("./path/to/repo")

# Initialize from a GitHub repository
codebase = Codebase.from_repo("owner/repository")

# Initialize from a string
codebase = Codebase.from_string("def hello(): print('Hello, world!')", language="python")

# Initialize from files
codebase = Codebase.from_files({
    "main.py": "def hello(): print('Hello, world!')",
    "utils.py": "def helper(): return 42"
})
```

#### Properties

- `files`: List of all files in the codebase
- `directories`: List of all directories in the codebase
- `functions`: List of all functions in the codebase
- `classes`: List of all classes in the codebase
- `imports`: List of all imports in the codebase
- `global_vars`: List of all global variables in the codebase
- `interfaces`: List of all interfaces in the codebase (TypeScript only)
- `type_aliases`: List of all type aliases in the codebase (TypeScript only)

#### Methods

- `get_file(filepath)`: Get a file by path
- `get_directory(dirpath)`: Get a directory by path
- `get_function(name)`: Get a function by name
- `get_class(name)`: Get a class by name
- `get_import(name)`: Get an import by name
- `get_global_var(name)`: Get a global variable by name
- `get_interface(name)`: Get an interface by name (TypeScript only)
- `get_type_alias(name)`: Get a type alias by name (TypeScript only)
- `commit(message)`: Commit changes to the repository
- `create_branch(name)`: Create a new branch
- `create_pr(title, body)`: Create a pull request

### File API

The `File` class represents a source code file.

#### Properties

- `filepath`: Path to the file
- `content`: Content of the file
- `functions`: List of functions defined in the file
- `classes`: List of classes defined in the file
- `imports`: List of imports in the file
- `global_vars`: List of global variables in the file
- `interfaces`: List of interfaces in the file (TypeScript only)
- `type_aliases`: List of type aliases in the file (TypeScript only)

#### Methods

- `get_function(name)`: Get a function by name
- `get_class(name)`: Get a class by name
- `get_import(name)`: Get an import by name
- `get_global_var(name)`: Get a global variable by name
- `get_interface(name)`: Get an interface by name (TypeScript only)
- `get_type_alias(name)`: Get a type alias by name (TypeScript only)
- `add_function(name, params, body)`: Add a new function
- `add_class(name, bases, body)`: Add a new class
- `add_import(import_string)`: Add a new import
- `add_global_var(name, value)`: Add a new global variable
- `add_interface(name, attributes)`: Add a new interface (TypeScript only)
- `add_type_alias(name, type_string)`: Add a new type alias (TypeScript only)

### Function API

The `Function` class represents a function or method.

#### Properties

- `name`: Name of the function
- `source`: Source code of the function
- `filepath`: Path to the file containing the function
- `parameters`: List of parameters
- `return_type`: Return type annotation (if any)
- `docstring`: Docstring of the function (if any)
- `usages`: List of usages of the function
- `dependencies`: List of dependencies of the function
- `is_async`: Whether the function is async
- `is_exported`: Whether the function is exported (TypeScript only)

#### Methods

- `rename(new_name)`: Rename the function
- `move_to_file(filepath)`: Move the function to another file
- `add_parameter(name, type_annotation=None)`: Add a parameter
- `remove_parameter(name)`: Remove a parameter
- `add_parameter_type_annotation(name, type_annotation)`: Add a type annotation to a parameter
- `add_return_type_annotation(type_annotation)`: Add a return type annotation
- `set_docstring(docstring)`: Set the docstring
- `add_dependency(dependency)`: Add a dependency
- `remove_dependency(dependency)`: Remove a dependency

### Class API

The `Class` class represents a class definition.

#### Properties

- `name`: Name of the class
- `source`: Source code of the class
- `filepath`: Path to the file containing the class
- `methods`: List of methods
- `attributes`: List of attributes
- `parent_class_names`: List of parent class names
- `docstring`: Docstring of the class (if any)
- `usages`: List of usages of the class
- `dependencies`: List of dependencies of the class
- `is_exported`: Whether the class is exported (TypeScript only)

#### Methods

- `rename(new_name)`: Rename the class
- `move_to_file(filepath)`: Move the class to another file
- `add_method(name, params, body)`: Add a method
- `remove_method(name)`: Remove a method
- `add_attribute(name, value)`: Add an attribute
- `remove_attribute(name)`: Remove an attribute
- `add_parent_class(name)`: Add a parent class
- `remove_parent_class(name)`: Remove a parent class
- `set_docstring(docstring)`: Set the docstring

## Usage Examples

### Example 1: Analyzing Function Dependencies

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Get a function
function = codebase.get_function("process_data")

# Analyze dependencies
print(f"Function: {function.name}")
print(f"Dependencies:")
for dep in function.dependencies:
    print(f"  - {dep.name} ({dep.filepath})")

# Analyze usages
print(f"Usages:")
for usage in function.usages:
    print(f"  - Used in {usage.usage_symbol.name} ({usage.usage_symbol.filepath})")
```

### Example 2: Refactoring Code

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Find all functions without type annotations
untyped_functions = []
for function in codebase.functions:
    if not function.return_type and function.filepath.endswith(".py"):
        untyped_functions.append(function)

print(f"Found {len(untyped_functions)} functions without return type annotations")

# Add type annotations
for function in untyped_functions:
    # Infer return type based on function name and body
    if "get_" in function.name or "fetch_" in function.name:
        function.add_return_type_annotation("Any")
        print(f"Added return type annotation to {function.name}")

# Commit changes
codebase.commit("Add return type annotations to getter functions")
```

### Example 3: Creating a New Feature

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Create a new branch
codebase.create_branch("feature/add-validation")

# Get the main file
file = codebase.get_file("src/main.py")

# Add a new validation function
file.add_function(
    "validate_input",
    ["data"],
    """
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")
    
    if "id" not in data:
        raise ValueError("Input must contain an id field")
    
    return True
    """
)

# Add type annotations
validation_function = file.get_function("validate_input")
validation_function.add_parameter_type_annotation("data", "Dict[str, Any]")
validation_function.add_return_type_annotation("bool")

# Add docstring
validation_function.set_docstring("""
Validate the input data.

Args:
    data: The input data to validate

Returns:
    True if the data is valid, otherwise raises ValueError

Raises:
    ValueError: If the data is invalid
""")

# Update the process_data function to use validation
process_function = file.get_function("process_data")
process_function_source = process_function.source
new_process_function_source = process_function_source.replace(
    "def process_data(data):",
    "def process_data(data):\n    validate_input(data)"
)
process_function.edit(new_process_function_source)

# Commit changes
codebase.commit("Add input validation")

# Create a PR
codebase.create_pr(
    "Add input validation",
    "This PR adds input validation to the process_data function."
)
```

## Extension Modules

Graph-sitter provides several extension modules for additional functionality:

### Visualization Extensions

The visualization extensions provide tools for visualizing code relationships:

```python
# Visualize call graph
codebase.viz.visualize_call_graph("process_data")

# Visualize dependency graph
codebase.viz.visualize_dependency_graph("process_data")

# Visualize import graph
codebase.viz.visualize_import_graph()
```

### AI Extensions

The AI extensions provide integration with AI models:

```python
from graph_sitter.ai import CodegenAI

# Initialize AI
ai = CodegenAI(codebase)

# Generate a function
function_code = ai.generate_function(
    "validate_email",
    "Validate an email address",
    ["email"]
)

# Add the function to a file
file = codebase.get_file("utils.py")
file.add_function_from_source(function_code)
```

### LSP Extensions

The LSP (Language Server Protocol) extensions provide integration with language servers:

```python
from graph_sitter.extensions.lsp import LSPClient

# Initialize LSP client
lsp = LSPClient(codebase)

# Get diagnostics
diagnostics = lsp.get_diagnostics("main.py")
for diag in diagnostics:
    print(f"Line {diag.line}: {diag.message}")

# Get hover information
hover_info = lsp.get_hover("main.py", 10, 15)
print(hover_info)
```

### Graph Extensions

The graph extensions provide advanced graph analysis capabilities:

```python
from graph_sitter.extensions.graph import GraphAnalyzer

# Initialize graph analyzer
graph = GraphAnalyzer(codebase)

# Find cycles in the import graph
cycles = graph.find_import_cycles()
for cycle in cycles:
    print("Import cycle:")
    for node in cycle:
        print(f"  - {node}")

# Find strongly connected components
components = graph.find_strongly_connected_components()
for component in components:
    print("Component:")
    for node in component:
        print(f"  - {node}")
```

## CLI Interface

Graph-sitter provides a command-line interface (CLI) for common operations:

### Installation

```bash
pip install graph-sitter
```

### Basic Commands

```bash
# Initialize a new codemod
gs init

# Create a new codemod
gs create my-codemod

# Run a codemod
gs run my-codemod

# Start a notebook
gs notebook

# Get help
gs --help
```

### Advanced Commands

```bash
# Run a codemod on a PR
gs run-on-pr my-codemod --pr 123

# Deploy a codemod
gs deploy my-codemod

# Start the LSP server
gs lsp

# Start the web server
gs serve
```

## Configuration

Graph-sitter can be configured using a `pyproject.toml` file or environment variables:

### pyproject.toml

```toml
[tool.graph-sitter]
debug = false
verify_graph = false
track_graph = false
method_usages = true
sync_enabled = false
full_range_index = false
ignore_process_errors = true
disable_graph = false
disable_file_parse = false
exp_lazy_graph = false
generics = true
import_resolution_paths = []
import_resolution_overrides = {}
py_resolve_syspath = false
allow_external = false
ts_dependency_manager = false
ts_language_engine = false
v8_ts_engine = false
unpacking_assignment_partial_removal = true
conditional_type_resolution = false
use_pink = "OFF"
```

### Environment Variables

```bash
# Debug mode
export CODEBASE_DEBUG=true

# Verify graph
export CODEBASE_VERIFY_GRAPH=true

# Track graph
export CODEBASE_TRACK_GRAPH=true
```

## Troubleshooting

### Common Issues

#### UV Error Related to `[[ packages ]]`

This means you're likely using an outdated version of UV. Try updating to the latest version:

```bash
uv self update
```

#### Error About `No module named 'codegen.sdk.extensions.utils'`

The compiled cython extensions are out of sync. Update them with:

```bash
uv sync --reinstall-package codegen
```

#### RecursionError: Maximum Recursion Depth Exceeded

If you are using Python 3.12, try upgrading to 3.13. If you are already on 3.13, try upping the recursion limit:

```python
import sys
sys.setrecursionlimit(10000)
```

### Getting Help

If you run into additional issues not listed here, please:

- Check the [documentation](https://graph-sitter.com)
- Join the [Slack community](https://community.codegen.com)
- Open an issue on [GitHub](https://github.com/codegen-sh/graph-sitter)

