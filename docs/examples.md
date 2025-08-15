# Graph-sitter Examples

This document provides practical examples of using Graph-sitter for various code analysis and transformation tasks.

## Table of Contents

1. [Code Analysis Examples](#code-analysis-examples)
2. [Code Transformation Examples](#code-transformation-examples)
3. [Migration Examples](#migration-examples)
4. [Visualization Examples](#visualization-examples)
5. [Integration Examples](#integration-examples)

## Code Analysis Examples

### Finding Dead Code

This example finds functions that are not used anywhere in the codebase.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Find all functions without usages
dead_functions = []
for function in codebase.functions:
    # Skip test functions
    if not function.usages and not function.name.startswith("test_"):
        dead_functions.append(function)

print(f"Found {len(dead_functions)} unused functions:")
for function in dead_functions:
    print(f"  - {function.name} ({function.filepath})")
```

### Analyzing Function Dependencies

This example analyzes the dependencies of a specific function.

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

### Finding Import Cycles

This example finds cycles in the import graph.

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
```

### Analyzing Type Coverage

This example analyzes the type coverage of a codebase.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Count functions with and without return type annotations
total_functions = len(codebase.functions)
typed_functions = 0
untyped_functions = []

for function in codebase.functions:
    if function.return_type:
        typed_functions += 1
    else:
        untyped_functions.append(function)

# Calculate type coverage
type_coverage = (typed_functions / total_functions) * 100 if total_functions > 0 else 0
print(f"Type coverage: {type_coverage:.2f}%")
print(f"Total functions: {total_functions}")
print(f"Typed functions: {typed_functions}")
print(f"Untyped functions: {len(untyped_functions)}")

# List untyped functions
print("\nUntyped functions:")
for function in untyped_functions[:10]:  # Show first 10
    print(f"  - {function.name} ({function.filepath})")
```

### Finding Complex Functions

This example finds functions with high cyclomatic complexity.

```python
from graph_sitter import Codebase
from graph_sitter.extensions.metrics import calculate_cyclomatic_complexity

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Calculate cyclomatic complexity for all functions
complex_functions = []
for function in codebase.functions:
    complexity = calculate_cyclomatic_complexity(function)
    if complexity > 10:  # Threshold for complex functions
        complex_functions.append((function, complexity))

# Sort by complexity (highest first)
complex_functions.sort(key=lambda x: x[1], reverse=True)

# Print results
print(f"Found {len(complex_functions)} complex functions:")
for function, complexity in complex_functions[:10]:  # Show top 10
    print(f"  - {function.name} ({function.filepath}): {complexity}")
```

## Code Transformation Examples

### Adding Type Annotations

This example adds type annotations to functions based on naming conventions.

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

# Commit changes
codebase.commit("Add return type annotations")
```

### Refactoring Function Parameters

This example refactors functions to use keyword arguments instead of positional arguments.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Find functions with more than 3 parameters without default values
functions_to_refactor = []
for function in codebase.functions:
    # Count parameters without default values
    params_without_defaults = [p for p in function.parameters if not p.default_value]
    if len(params_without_defaults) > 3:
        functions_to_refactor.append(function)

print(f"Found {len(functions_to_refactor)} functions to refactor")

# Refactor functions
for function in functions_to_refactor:
    # Add default values to all parameters except the first one
    for i, param in enumerate(function.parameters):
        if i > 0 and not param.default_value:
            param.set_default_value("None")
            print(f"Added default value to parameter {param.name} in {function.name}")

# Commit changes
codebase.commit("Refactor function parameters to use keyword arguments")
```

### Adding Docstrings

This example adds docstrings to functions that don't have them.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Find functions without docstrings
functions_without_docstrings = []
for function in codebase.functions:
    if not function.docstring and not function.name.startswith("_"):
        functions_without_docstrings.append(function)

print(f"Found {len(functions_without_docstrings)} functions without docstrings")

# Add docstrings
for function in functions_without_docstrings:
    # Generate a basic docstring
    param_docs = "\n".join([f"    {p.name}: TODO" for p in function.parameters])
    return_doc = "    TODO" if function.return_type else ""
    
    docstring = f'"""\n{function.name.replace("_", " ").capitalize()}.\n\nArgs:\n{param_docs}\n'
    if return_doc:
        docstring += f'\nReturns:\n{return_doc}\n'
    docstring += '"""'
    
    function.set_docstring(docstring)
    print(f"Added docstring to {function.name}")

# Commit changes
codebase.commit("Add docstrings to functions")
```

### Extracting Utility Functions

This example extracts common code patterns into utility functions.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Create a new utility file if it doesn't exist
utils_file_path = "src/utils.py"
try:
    utils_file = codebase.get_file(utils_file_path)
except:
    utils_file = codebase.create_file(utils_file_path, "# Utility functions\n\n")
    print(f"Created new utility file: {utils_file_path}")

# Add a utility function
utils_file.add_function(
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
validation_function = utils_file.get_function("validate_input")
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

# Find functions that could use the utility
for function in codebase.functions:
    if "data" in [p.name for p in function.parameters]:
        # Check if the function already validates input
        if "isinstance" in function.source and "dict" in function.source:
            # Add import for the utility function
            function.get_file().add_import("from src.utils import validate_input")
            
            # Replace validation code with utility function call
            new_source = function.source.replace(
                "def " + function.name,
                "def " + function.name + "\n    validate_input(data)"
            )
            function.edit(new_source)
            print(f"Updated {function.name} to use validate_input utility")

# Commit changes
codebase.commit("Extract validation logic to utility function")
```

## Migration Examples

### Python 2 to Python 3 Migration

This example migrates Python 2 code to Python 3.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Find Python 2 print statements
py2_prints = []
for file in codebase.files:
    if file.filepath.endswith(".py"):
        for statement in file.statements:
            if statement.source.strip().startswith("print "):
                py2_prints.append(statement)

print(f"Found {len(py2_prints)} Python 2 print statements")

# Convert to Python 3 print function
for statement in py2_prints:
    # Replace "print x" with "print(x)"
    new_source = statement.source.replace("print ", "print(")
    if not new_source.strip().endswith(")"):
        new_source = new_source.rstrip() + ")"
    statement.edit(new_source)
    print(f"Converted print statement in {statement.filepath}")

# Find Python 2 exception handling
py2_exceptions = []
for function in codebase.functions:
    if "except " in function.source and ", " in function.source.split("except ")[1].split(":")[0]:
        py2_exceptions.append(function)

print(f"Found {len(py2_exceptions)} Python 2 exception handling patterns")

# Convert to Python 3 exception handling
for function in py2_exceptions:
    # Replace "except Exception, e:" with "except Exception as e:"
    new_source = function.source
    for line in function.source.split("\n"):
        if "except " in line and ", " in line.split("except ")[1].split(":")[0]:
            exception_part = line.split("except ")[1].split(":")[0]
            exception_type, exception_var = exception_part.split(", ")
            new_line = line.replace(f"except {exception_type}, {exception_var}", f"except {exception_type} as {exception_var}")
            new_source = new_source.replace(line, new_line)
    function.edit(new_source)
    print(f"Converted exception handling in {function.name}")

# Commit changes
codebase.commit("Migrate Python 2 code to Python 3")
```

### SQLAlchemy 1.x to 2.0 Migration

This example migrates SQLAlchemy 1.x code to 2.0.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Find SQLAlchemy 1.x query patterns
sqlalchemy_1x_patterns = []
for function in codebase.functions:
    if ".query." in function.source:
        sqlalchemy_1x_patterns.append(function)

print(f"Found {len(sqlalchemy_1x_patterns)} SQLAlchemy 1.x query patterns")

# Convert to SQLAlchemy 2.0 patterns
for function in sqlalchemy_1x_patterns:
    # Replace "Model.query.filter_by(...)" with "session.query(Model).filter_by(...)"
    new_source = function.source
    for line in function.source.split("\n"):
        if ".query." in line:
            model_name = line.split(".query.")[0].strip()
            query_part = line.split(".query.")[1]
            new_line = line.replace(f"{model_name}.query.{query_part}", f"session.query({model_name}).{query_part}")
            new_source = new_source.replace(line, new_line)
    function.edit(new_source)
    print(f"Converted SQLAlchemy query in {function.name}")

# Add session parameter to functions that need it
for function in sqlalchemy_1x_patterns:
    if "session" not in [p.name for p in function.parameters]:
        function.add_parameter("session", "Session")
        print(f"Added session parameter to {function.name}")

# Commit changes
codebase.commit("Migrate SQLAlchemy 1.x to 2.0")
```

### Promise to Async/Await Migration

This example migrates Promise-based JavaScript/TypeScript code to async/await.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Find Promise-based functions
promise_functions = []
for function in codebase.functions:
    if ".then(" in function.source and ".catch(" in function.source:
        promise_functions.append(function)

print(f"Found {len(promise_functions)} Promise-based functions")

# Convert to async/await
for function in promise_functions:
    # Make the function async
    new_source = function.source
    if not "async " in new_source.split("function")[0]:
        new_source = new_source.replace("function", "async function")
    
    # Replace Promise chains with await
    lines = new_source.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if ".then(" in line:
            # Find the end of the Promise chain
            promise_chain_start = i
            promise_chain_end = i
            open_braces = line.count("(") - line.count(")")
            while open_braces > 0 and promise_chain_end + 1 < len(lines):
                promise_chain_end += 1
                open_braces += lines[promise_chain_end].count("(") - lines[promise_chain_end].count(")")
            
            # Extract the Promise chain
            promise_chain = "\n".join(lines[promise_chain_start:promise_chain_end+1])
            
            # Convert to await
            if ".catch(" in promise_chain:
                # With error handling
                try_block = promise_chain.split(".then(")[0]
                then_block = promise_chain.split(".then(")[1].split(".catch(")[0]
                catch_block = promise_chain.split(".catch(")[1]
                
                # Extract the function bodies
                then_body = then_block.split("=>")[1].strip()
                catch_body = catch_block.split("=>")[1].strip()
                
                # Create try/catch block
                new_lines.append("try {")
                new_lines.append(f"  const result = await {try_block};")
                new_lines.append(f"  {then_body}")
                new_lines.append("} catch (error) {")
                new_lines.append(f"  {catch_body}")
                new_lines.append("}")
            else:
                # Without error handling
                await_expr = f"await {promise_chain.split('.then(')[0]};"
                then_body = promise_chain.split("=>")[1].strip()
                new_lines.append(f"const result = {await_expr}")
                new_lines.append(then_body)
            
            i = promise_chain_end + 1
        else:
            new_lines.append(line)
            i += 1
    
    # Update the function
    function.edit("\n".join(new_lines))
    print(f"Converted {function.name} to async/await")

# Commit changes
codebase.commit("Migrate Promise-based code to async/await")
```

## Visualization Examples

### Call Graph Visualization

This example visualizes the call graph for a function.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Visualize call graph for a function
function_name = "process_data"
codebase.viz.visualize_call_graph(function_name)

# Export the call graph to a file
codebase.viz.export_call_graph(function_name, "call_graph.html")
```

### Dependency Graph Visualization

This example visualizes the dependency graph for a function.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Visualize dependency graph for a function
function_name = "process_data"
codebase.viz.visualize_dependency_graph(function_name)

# Export the dependency graph to a file
codebase.viz.export_dependency_graph(function_name, "dependency_graph.html")
```

### Import Graph Visualization

This example visualizes the import graph for the codebase.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Visualize import graph
codebase.viz.visualize_import_graph()

# Export the import graph to a file
codebase.viz.export_import_graph("import_graph.html")
```

### Class Hierarchy Visualization

This example visualizes the class hierarchy for the codebase.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Visualize class hierarchy
codebase.viz.visualize_class_hierarchy()

# Export the class hierarchy to a file
codebase.viz.export_class_hierarchy("class_hierarchy.html")
```

## Integration Examples

### Integration with AI Models

This example integrates Graph-sitter with AI models for code generation.

```python
from graph_sitter import Codebase
from graph_sitter.ai import CodegenAI

# Initialize codebase
codebase = Codebase("./path/to/repo")

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

# Generate docstring for a function
function = codebase.get_function("process_data")
docstring = ai.generate_docstring(function)
function.set_docstring(docstring)

# Generate tests for a function
test_code = ai.generate_tests(function)
test_file = codebase.get_file("tests/test_utils.py")
test_file.add_function_from_source(test_code)
```

### Integration with GitHub

This example integrates Graph-sitter with GitHub for PR creation and review.

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Create a branch
branch_name = "feature/add-validation"
codebase.create_branch(branch_name)

# Make changes
file = codebase.get_file("src/main.py")
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

# Commit changes
codebase.commit("Add input validation")

# Create a PR
pr = codebase.create_pr(
    "Add input validation",
    "This PR adds input validation to the process_data function.",
    base_branch="main",
    head_branch=branch_name
)

# Add a comment to the PR
codebase.create_pr_comment(pr.number, "This PR adds input validation to prevent invalid data from being processed.")

# Review a PR
pr_id = 123
patch, commit_sha, modified_symbols, head_ref = codebase.get_modified_symbols_in_pr(pr_id)
print(f"PR {pr_id} modifies {len(modified_symbols)} symbols")
for symbol in modified_symbols:
    print(f"  - {symbol}")

# Add a review comment to a PR
codebase.create_pr_review_comment(
    pr_id,
    "Consider adding a more specific error message here.",
    commit_sha["src/main.py"],
    "src/main.py",
    10
)
```

### Integration with LSP

This example integrates Graph-sitter with Language Server Protocol (LSP) for code analysis.

```python
from graph_sitter import Codebase
from graph_sitter.extensions.lsp import LSPClient

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Initialize LSP client
lsp = LSPClient(codebase)

# Get diagnostics
diagnostics = lsp.get_diagnostics("main.py")
for diag in diagnostics:
    print(f"Line {diag.line}: {diag.message}")

# Get hover information
hover_info = lsp.get_hover("main.py", 10, 15)
print(hover_info)

# Get completions
completions = lsp.get_completions("main.py", 10, 15)
for completion in completions:
    print(f"  - {completion.label}: {completion.detail}")

# Get signature help
signature_help = lsp.get_signature_help("main.py", 10, 15)
print(signature_help)
```

### Integration with Neo4j

This example integrates Graph-sitter with Neo4j for graph database storage and analysis.

```python
from graph_sitter import Codebase
from graph_sitter.extensions.neo4j import Neo4jExporter

# Initialize codebase
codebase = Codebase("./path/to/repo")

# Initialize Neo4j exporter
exporter = Neo4jExporter(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# Export codebase to Neo4j
exporter.export_codebase(codebase)

# Export call graph to Neo4j
exporter.export_call_graph(codebase, "process_data")

# Export dependency graph to Neo4j
exporter.export_dependency_graph(codebase, "process_data")

# Export import graph to Neo4j
exporter.export_import_graph(codebase)

# Export class hierarchy to Neo4j
exporter.export_class_hierarchy(codebase)
```

