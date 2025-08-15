# Getting Started with Graph-sitter

This guide will help you get started with Graph-sitter, a powerful Python library for analyzing and manipulating codebases.

## Installation

Graph-sitter supports Python 3.12 - 3.13 (recommended: Python 3.13+) on macOS and Linux.

### Prerequisites

- Python 3.12 or 3.13
- Git
- macOS or Linux (Windows is supported via WSL)

### Install with pip

```bash
# Install inside existing project
pip install graph-sitter

# Or with uv (recommended)
uv pip install graph-sitter
```

### Install as a global CLI tool

```bash
# Install global CLI
uv tool install graph-sitter --python 3.13
```

## Basic Usage

### Initialize a Codebase

```python
from graph_sitter import Codebase

# Initialize from a local directory
codebase = Codebase("./path/to/repo")

# Or from a GitHub repository
codebase = Codebase.from_repo("owner/repository")
```

### Explore the Codebase

```python
# List all files
for file in codebase.files:
    print(f"File: {file.filepath}")

# List all functions
for function in codebase.functions:
    print(f"Function: {function.name} in {function.filepath}")

# List all classes
for cls in codebase.classes:
    print(f"Class: {cls.name} in {cls.filepath}")
```

### Find Specific Symbols

```python
# Find a function by name
function = codebase.get_function("process_data")
print(f"Function source:\n{function.source}")

# Find a class by name
cls = codebase.get_class("User")
print(f"Class source:\n{cls.source}")

# Find a file by path
file = codebase.get_file("src/main.py")
print(f"File content:\n{file.content}")
```

### Analyze Dependencies and Usages

```python
# Find all dependencies of a function
function = codebase.get_function("process_data")
print(f"Dependencies of {function.name}:")
for dep in function.dependencies:
    print(f"  - {dep.name} ({dep.filepath})")

# Find all usages of a function
print(f"Usages of {function.name}:")
for usage in function.usages:
    print(f"  - Used in {usage.usage_symbol.name} ({usage.usage_symbol.filepath})")
```

### Modify Code

```python
# Rename a function
function = codebase.get_function("old_name")
function.rename("new_name")

# Move a function to another file
function.move_to_file("utils.py")

# Add a parameter to a function
function.add_parameter("new_param", "str")

# Add a return type annotation
function.add_return_type_annotation("List[Dict[str, Any]]")

# Add a docstring
function.set_docstring("""
Process the input data and return results.

Args:
    data: The input data to process
    new_param: A new parameter

Returns:
    A list of processed results
""")
```

### Add New Code

```python
# Add a new function to a file
file = codebase.get_file("src/utils.py")
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

# Add a new class to a file
file.add_class(
    "Result",
    ["BaseModel"],
    """
    id: str
    name: str
    value: float
    
    def __str__(self):
        return f"{self.name}: {self.value}"
    """
)

# Add an import to a file
file.add_import("from typing import Dict, List, Any")
```

### Commit Changes

```python
# Commit all changes
codebase.commit("Add input validation")

# Create a branch
codebase.create_branch("feature/input-validation")

# Create a PR
codebase.create_pr(
    "Add input validation",
    "This PR adds input validation to the process_data function."
)
```

## Using the CLI

Graph-sitter provides a command-line interface (CLI) for common operations.

### Initialize a New Codemod

```bash
# Navigate to your repository
cd path/to/repo

# Initialize a new codemod
gs init
```

### Create a New Codemod

```bash
# Create a new codemod
gs create my-codemod
```

This will create a new codemod in the `.codegen/codemods/my-codemod` directory with the following structure:

```
.codegen/codemods/my-codemod/
├── my-codemod.py
└── README.md
```

### Edit the Codemod

Edit the `my-codemod.py` file to implement your codemod:

```python
import graph_sitter
from graph_sitter import Codebase

@graph_sitter.function("my-codemod")
def run(codebase: Codebase):
    """
    My codemod description.
    """
    # Your code here
    print("Running my codemod...")
    
    # Find all functions without return type annotations
    untyped_functions = []
    for function in codebase.functions:
        if not function.return_type and function.filepath.endswith(".py"):
            untyped_functions.append(function)
    
    print(f"Found {len(untyped_functions)} functions without return type annotations")
    
    # Add return type annotations
    for function in untyped_functions:
        # Infer return type based on function name and body
        if "get_" in function.name or "fetch_" in function.name:
            function.add_return_type_annotation("Any")
            print(f"Added return type annotation to {function.name}")
    
    # Commit changes
    codebase.commit("Add return type annotations to getter functions")
```

### Run the Codemod

```bash
# Run the codemod
gs run my-codemod
```

### Start a Notebook

```bash
# Start a Jupyter notebook with graph-sitter
gs notebook
```

This will create an isolated venv with graph-sitter and open a Jupyter notebook.

## Common Patterns

### Finding Dead Code

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Find all functions without usages
dead_functions = []
for function in codebase.functions:
    if not function.usages and not function.name.startswith("test_"):
        dead_functions.append(function)

print(f"Found {len(dead_functions)} unused functions:")
for function in dead_functions:
    print(f"  - {function.name} ({function.filepath})")
```

### Adding Type Annotations

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Find all functions without return type annotations
untyped_functions = []
for function in codebase.functions:
    if not function.return_type and function.filepath.endswith(".py"):
        untyped_functions.append(function)

print(f"Found {len(untyped_functions)} functions without return type annotations")

# Add return type annotations
for function in untyped_functions:
    # Infer return type based on function name and body
    if "get_" in function.name or "fetch_" in function.name:
        function.add_return_type_annotation("Any")
        print(f"Added return type annotation to {function.name}")
    elif "is_" in function.name or "has_" in function.name:
        function.add_return_type_annotation("bool")
        print(f"Added return type annotation to {function.name}")
    elif "create_" in function.name or "build_" in function.name:
        function.add_return_type_annotation("Any")  # Could be more specific
        print(f"Added return type annotation to {function.name}")
```

### Fixing Import Loops

```python
from graph_sitter import Codebase
from graph_sitter.extensions.graph import GraphAnalyzer

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Initialize graph analyzer
graph = GraphAnalyzer(codebase)

# Find cycles in the import graph
cycles = graph.find_import_cycles()
print(f"Found {len(cycles)} import cycles")

for i, cycle in enumerate(cycles):
    print(f"Cycle {i+1}:")
    for node in cycle:
        print(f"  - {node}")

# Fix the first cycle as an example
if cycles:
    cycle = cycles[0]
    # Find the file with the most incoming dependencies
    file_to_fix = max(cycle, key=lambda f: len(codebase.get_file(f).usages))
    print(f"Fixing file: {file_to_fix}")
    
    # Get the file
    file = codebase.get_file(file_to_fix)
    
    # Find imports that are part of the cycle
    cycle_imports = []
    for imp in file.imports:
        if imp.module_name in cycle:
            cycle_imports.append(imp)
    
    # Move the imports to a new file
    if cycle_imports:
        # Create a new file for types
        types_file = file_to_fix.replace(".py", "_types.py")
        codebase.create_file(types_file, "# Type definitions\n\n")
        
        # Move the imports to the new file
        for imp in cycle_imports:
            imp.move_to_file(types_file)
        
        print(f"Moved {len(cycle_imports)} imports to {types_file}")
```

### Visualizing Code Relationships

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Visualize call graph for a function
codebase.viz.visualize_call_graph("process_data")

# Visualize dependency graph for a function
codebase.viz.visualize_dependency_graph("process_data")

# Visualize import graph
codebase.viz.visualize_import_graph()

# Visualize class hierarchy
codebase.viz.visualize_class_hierarchy()
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

## Next Steps

Now that you're familiar with the basics of Graph-sitter, you can:

- Explore the [API Reference](./api_reference.md) for more details on available classes and methods
- Check out the [Backend Documentation](./backend_documentation.md) for a deeper understanding of the architecture
- Try the [examples](../examples) for more complex use cases
- Join the [Slack community](https://community.codegen.com) to connect with other users and get help

