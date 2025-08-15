# Graph-sitter API Reference

This document provides a comprehensive reference for the Graph-sitter API, detailing the classes, methods, and properties available for codebase manipulation.

## Table of Contents

1. [Codebase](#codebase)
2. [File](#file)
3. [Directory](#directory)
4. [Symbol](#symbol)
5. [Function](#function)
6. [Class](#class)
7. [Import](#import)
8. [Assignment](#assignment)
9. [Interface](#interface)
10. [TypeAlias](#typealias)
11. [Parameter](#parameter)
12. [CodeBlock](#codeblock)
13. [Statement](#statement)
14. [Expression](#expression)
15. [Visualization](#visualization)
16. [Git Operations](#git-operations)

## Codebase

The `Codebase` class is the main entry point for interacting with a codebase.

### Constructors

```python
# Initialize from a local directory
Codebase(repo_path: str, language: Optional[str] = None)

# Initialize from a GitHub repository
Codebase.from_repo(repo_name: str, commit: Optional[str] = None, language: Optional[str] = None)

# Initialize from a string
Codebase.from_string(code: str, language: str)

# Initialize from files
Codebase.from_files(files: Dict[str, str], language: Optional[str] = None)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `repo_path` | `Path` | The path to the repository |
| `files` | `List[SourceFile]` | List of all files in the codebase |
| `directories` | `List[Directory]` | List of all directories in the codebase |
| `functions` | `List[Function]` | List of all functions in the codebase |
| `classes` | `List[Class]` | List of all classes in the codebase |
| `imports` | `List[Import]` | List of all imports in the codebase |
| `global_vars` | `List[Assignment]` | List of all global variables in the codebase |
| `interfaces` | `List[Interface]` | List of all interfaces in the codebase (TypeScript only) |
| `type_aliases` | `List[TypeAlias]` | List of all type aliases in the codebase (TypeScript only) |
| `viz` | `VisualizationManager` | Visualization manager for the codebase |
| `console` | `Console` | Console for output |

### Methods

#### File and Directory Access

```python
# Get a file by path
get_file(filepath: str) -> SourceFile

# Get a directory by path
get_directory(dirpath: str) -> Directory

# Get all files matching a pattern
get_files_by_pattern(pattern: str) -> List[SourceFile]

# Get all directories matching a pattern
get_directories_by_pattern(pattern: str) -> List[Directory]
```

#### Symbol Access

```python
# Get a function by name
get_function(name: str) -> Function

# Get a class by name
get_class(name: str) -> Class

# Get an import by name
get_import(name: str) -> Import

# Get a global variable by name
get_global_var(name: str) -> Assignment

# Get an interface by name (TypeScript only)
get_interface(name: str) -> Interface

# Get a type alias by name (TypeScript only)
get_type_alias(name: str) -> TypeAlias
```

#### Git Operations

```python
# Commit changes
commit(message: str) -> str

# Create a branch
create_branch(name: str) -> bool

# Checkout a branch
checkout_branch(name: str) -> bool

# Create a pull request
create_pr(title: str, body: str, base_branch: str = None, head_branch: str = None) -> PullRequest

# Get a pull request
get_pr(pr_id: int) -> PullRequest

# Get modified symbols in a pull request
get_modified_symbols_in_pr(pr_id: int) -> Tuple[str, Dict[str, str], List[str], str]

# Create a comment on a pull request
create_pr_comment(pr_number: int, body: str) -> None

# Create a review comment on a pull request
create_pr_review_comment(pr_number: int, body: str, commit_sha: str, path: str, line: int = None, side: str = "RIGHT", start_line: int = None) -> None
```

#### Codebase Analysis

```python
# Get codebase summary
get_codebase_summary() -> Dict[str, Any]

# Get file summary
get_file_summary(filepath: str) -> Dict[str, Any]

# Get class summary
get_class_summary(class_name: str) -> Dict[str, Any]

# Get function summary
get_function_summary(function_name: str) -> Dict[str, Any]

# Get symbol summary
get_symbol_summary(symbol_name: str) -> Dict[str, Any]
```

## File

The `File` class represents a source code file.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `filepath` | `str` | Path to the file |
| `content` | `str` | Content of the file |
| `functions` | `List[Function]` | List of functions defined in the file |
| `classes` | `List[Class]` | List of classes defined in the file |
| `imports` | `List[Import]` | List of imports in the file |
| `global_vars` | `List[Assignment]` | List of global variables in the file |
| `interfaces` | `List[Interface]` | List of interfaces in the file (TypeScript only) |
| `type_aliases` | `List[TypeAlias]` | List of type aliases in the file (TypeScript only) |
| `statements` | `List[Statement]` | List of statements in the file |
| `language` | `ProgrammingLanguage` | Programming language of the file |

### Methods

#### Symbol Access

```python
# Get a function by name
get_function(name: str) -> Function

# Get a class by name
get_class(name: str) -> Class

# Get an import by name
get_import(name: str) -> Import

# Get a global variable by name
get_global_var(name: str) -> Assignment

# Get an interface by name (TypeScript only)
get_interface(name: str) -> Interface

# Get a type alias by name (TypeScript only)
get_type_alias(name: str) -> TypeAlias
```

#### Symbol Creation

```python
# Add a function
add_function(name: str, params: List[str], body: str) -> Function

# Add a class
add_class(name: str, bases: List[str], body: str) -> Class

# Add an import
add_import(import_string: str) -> Import

# Add a global variable
add_global_var(name: str, value: str) -> Assignment

# Add an interface (TypeScript only)
add_interface(name: str, attributes: Dict[str, str]) -> Interface

# Add a type alias (TypeScript only)
add_type_alias(name: str, type_string: str) -> TypeAlias
```

#### File Operations

```python
# Save the file
save() -> None

# Rename the file
rename(new_filepath: str) -> None

# Delete the file
delete() -> None

# Get the file's directory
get_directory() -> Directory

# Get the file's relative path
get_relative_path(base_path: str) -> str
```

#### Content Operations

```python
# Get the file content
get_content() -> str

# Set the file content
set_content(content: str) -> None

# Get a line from the file
get_line(line_number: int) -> str

# Get a range of lines from the file
get_lines(start_line: int, end_line: int) -> List[str]

# Insert a line at a specific position
insert_line(line_number: int, content: str) -> None

# Replace a line at a specific position
replace_line(line_number: int, content: str) -> None

# Delete a line at a specific position
delete_line(line_number: int) -> None
```

## Directory

The `Directory` class represents a directory in the codebase.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `dirpath` | `str` | Path to the directory |
| `files` | `List[SourceFile]` | List of files in the directory |
| `subdirectories` | `List[Directory]` | List of subdirectories |
| `functions` | `List[Function]` | List of functions defined in the directory |
| `classes` | `List[Class]` | List of classes defined in the directory |
| `imports` | `List[Import]` | List of imports in the directory |
| `global_vars` | `List[Assignment]` | List of global variables in the directory |
| `interfaces` | `List[Interface]` | List of interfaces in the directory (TypeScript only) |
| `type_aliases` | `List[TypeAlias]` | List of type aliases in the directory (TypeScript only) |

### Methods

#### File and Directory Access

```python
# Get a file by name
get_file(filename: str) -> SourceFile

# Get a subdirectory by name
get_subdirectory(dirname: str) -> Directory

# Get all files matching a pattern
get_files_by_pattern(pattern: str) -> List[SourceFile]

# Get all subdirectories matching a pattern
get_subdirectories_by_pattern(pattern: str) -> List[Directory]
```

#### Symbol Access

```python
# Get a function by name
get_function(name: str) -> Function

# Get a class by name
get_class(name: str) -> Class

# Get an import by name
get_import(name: str) -> Import

# Get a global variable by name
get_global_var(name: str) -> Assignment

# Get an interface by name (TypeScript only)
get_interface(name: str) -> Interface

# Get a type alias by name (TypeScript only)
get_type_alias(name: str) -> TypeAlias
```

#### Directory Operations

```python
# Create a file in the directory
create_file(filename: str, content: str) -> SourceFile

# Create a subdirectory
create_subdirectory(dirname: str) -> Directory

# Delete the directory
delete() -> None

# Rename the directory
rename(new_dirpath: str) -> None

# Get the parent directory
get_parent_directory() -> Directory

# Get the directory's relative path
get_relative_path(base_path: str) -> str
```

## Symbol

The `Symbol` class is the base class for all code symbols.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Name of the symbol |
| `source` | `str` | Source code of the symbol |
| `filepath` | `str` | Path to the file containing the symbol |
| `start_line` | `int` | Start line of the symbol in the file |
| `end_line` | `int` | End line of the symbol in the file |
| `usages` | `List[Usage]` | List of usages of the symbol |
| `dependencies` | `List[Symbol]` | List of dependencies of the symbol |
| `is_exported` | `bool` | Whether the symbol is exported (TypeScript only) |

### Methods

#### Symbol Operations

```python
# Rename the symbol
rename(new_name: str) -> None

# Move the symbol to another file
move_to_file(filepath: str) -> None

# Delete the symbol
delete() -> None

# Get the symbol's file
get_file() -> SourceFile

# Get the symbol's directory
get_directory() -> Directory

# Get the symbol's relative path
get_relative_path(base_path: str) -> str
```

#### Usage Analysis

```python
# Get all usages of the symbol
get_usages() -> List[Usage]

# Get all usages of the symbol in a specific file
get_usages_in_file(filepath: str) -> List[Usage]

# Get all usages of the symbol in a specific directory
get_usages_in_directory(dirpath: str) -> List[Usage]

# Get all usages of the symbol by a specific symbol
get_usages_by_symbol(symbol_name: str) -> List[Usage]
```

#### Dependency Analysis

```python
# Get all dependencies of the symbol
get_dependencies() -> List[Symbol]

# Get all dependencies of the symbol in a specific file
get_dependencies_in_file(filepath: str) -> List[Symbol]

# Get all dependencies of the symbol in a specific directory
get_dependencies_in_directory(dirpath: str) -> List[Symbol]

# Get all dependencies of the symbol by a specific symbol type
get_dependencies_by_type(symbol_type: SymbolType) -> List[Symbol]
```

## Function

The `Function` class represents a function or method.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Name of the function |
| `source` | `str` | Source code of the function |
| `filepath` | `str` | Path to the file containing the function |
| `parameters` | `List[Parameter]` | List of parameters |
| `return_type` | `Type` | Return type annotation (if any) |
| `docstring` | `str` | Docstring of the function (if any) |
| `usages` | `List[Usage]` | List of usages of the function |
| `dependencies` | `List[Symbol]` | List of dependencies of the function |
| `is_async` | `bool` | Whether the function is async |
| `is_exported` | `bool` | Whether the function is exported (TypeScript only) |
| `is_method` | `bool` | Whether the function is a method |
| `parent_class` | `Class` | Parent class (if method) |
| `decorators` | `List[Decorator]` | List of decorators |
| `body` | `CodeBlock` | Function body |

### Methods

#### Function Operations

```python
# Rename the function
rename(new_name: str) -> None

# Move the function to another file
move_to_file(filepath: str) -> None

# Delete the function
delete() -> None

# Edit the function
edit(new_source: str) -> None

# Add a parameter
add_parameter(name: str, type_annotation: str = None) -> Parameter

# Remove a parameter
remove_parameter(name: str) -> None

# Add a parameter type annotation
add_parameter_type_annotation(name: str, type_annotation: str) -> None

# Add a return type annotation
add_return_type_annotation(type_annotation: str) -> None

# Set the docstring
set_docstring(docstring: str) -> None

# Add a decorator
add_decorator(decorator: str) -> Decorator

# Remove a decorator
remove_decorator(decorator: str) -> None
```

#### Call Analysis

```python
# Get all calls to the function
get_calls() -> List[FunctionCall]

# Get all calls to the function in a specific file
get_calls_in_file(filepath: str) -> List[FunctionCall]

# Get all calls to the function in a specific directory
get_calls_in_directory(dirpath: str) -> List[FunctionCall]

# Get all calls to the function by a specific function
get_calls_by_function(function_name: str) -> List[FunctionCall]
```

#### Parameter Analysis

```python
# Get a parameter by name
get_parameter(name: str) -> Parameter

# Get a parameter by index
get_parameter_by_index(index: int) -> Parameter

# Get all parameters
get_parameters() -> List[Parameter]

# Get all parameters with type annotations
get_typed_parameters() -> List[Parameter]

# Get all parameters without type annotations
get_untyped_parameters() -> List[Parameter]
```

## Class

The `Class` class represents a class definition.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Name of the class |
| `source` | `str` | Source code of the class |
| `filepath` | `str` | Path to the file containing the class |
| `methods` | `List[Function]` | List of methods |
| `attributes` | `List[Assignment]` | List of attributes |
| `parent_class_names` | `List[str]` | List of parent class names |
| `docstring` | `str` | Docstring of the class (if any) |
| `usages` | `List[Usage]` | List of usages of the class |
| `dependencies` | `List[Symbol]` | List of dependencies of the class |
| `is_exported` | `bool` | Whether the class is exported (TypeScript only) |
| `decorators` | `List[Decorator]` | List of decorators |
| `body` | `CodeBlock` | Class body |

### Methods

#### Class Operations

```python
# Rename the class
rename(new_name: str) -> None

# Move the class to another file
move_to_file(filepath: str) -> None

# Delete the class
delete() -> None

# Edit the class
edit(new_source: str) -> None

# Add a method
add_method(name: str, params: List[str], body: str) -> Function

# Remove a method
remove_method(name: str) -> None

# Add an attribute
add_attribute(name: str, value: str) -> Assignment

# Remove an attribute
remove_attribute(name: str) -> None

# Add a parent class
add_parent_class(name: str) -> None

# Remove a parent class
remove_parent_class(name: str) -> None

# Set the docstring
set_docstring(docstring: str) -> None

# Add a decorator
add_decorator(decorator: str) -> Decorator

# Remove a decorator
remove_decorator(decorator: str) -> None
```

#### Method Analysis

```python
# Get a method by name
get_method(name: str) -> Function

# Get all methods
get_methods() -> List[Function]

# Get all methods with a specific decorator
get_methods_with_decorator(decorator: str) -> List[Function]

# Get all methods with a specific return type
get_methods_with_return_type(return_type: str) -> List[Function]

# Get all methods without a return type
get_methods_without_return_type() -> List[Function]
```

#### Attribute Analysis

```python
# Get an attribute by name
get_attribute(name: str) -> Assignment

# Get all attributes
get_attributes() -> List[Assignment]

# Get all attributes with a specific type annotation
get_attributes_with_type(type_annotation: str) -> List[Assignment]

# Get all attributes without a type annotation
get_attributes_without_type() -> List[Assignment]
```

## Import

The `Import` class represents an import statement.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Name of the import |
| `source` | `str` | Source code of the import |
| `filepath` | `str` | Path to the file containing the import |
| `module_name` | `str` | Name of the imported module |
| `imported_symbol` | `Symbol` | Imported symbol (if any) |
| `alias` | `str` | Alias of the import (if any) |
| `is_dynamic` | `bool` | Whether the import is dynamic |
| `is_default` | `bool` | Whether the import is default |
| `is_namespace` | `bool` | Whether the import is namespace |
| `is_side_effect` | `bool` | Whether the import is side effect |

### Methods

#### Import Operations

```python
# Rename the import
rename(new_name: str) -> None

# Set the import module
set_import_module(module_name: str) -> None

# Set the import symbol alias
set_import_symbol_alias(alias: str) -> None

# Delete the import
delete() -> None

# Resolve the import
resolve() -> Symbol

# Get the import string
get_import_string() -> str
```

## Assignment

The `Assignment` class represents a variable assignment.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Name of the assignment |
| `source` | `str` | Source code of the assignment |
| `filepath` | `str` | Path to the file containing the assignment |
| `value` | `Expression` | Value of the assignment |
| `type_annotation` | `Type` | Type annotation (if any) |
| `usages` | `List[Usage]` | List of usages of the assignment |
| `dependencies` | `List[Symbol]` | List of dependencies of the assignment |
| `is_exported` | `bool` | Whether the assignment is exported (TypeScript only) |
| `is_const` | `bool` | Whether the assignment is constant |
| `is_let` | `bool` | Whether the assignment is let |
| `is_var` | `bool` | Whether the assignment is var |

### Methods

#### Assignment Operations

```python
# Rename the assignment
rename(new_name: str) -> None

# Set the assignment value
set_value(value: str) -> None

# Set the assignment type annotation
set_type_annotation(type_annotation: str) -> None

# Delete the assignment
delete() -> None

# Get the assignment statement
get_statement() -> AssignmentStatement
```

## Interface

The `Interface` class represents an interface definition (TypeScript only).

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Name of the interface |
| `source` | `str` | Source code of the interface |
| `filepath` | `str` | Path to the file containing the interface |
| `attributes` | `List[Attribute]` | List of attributes |
| `parent_interfaces` | `List[str]` | List of parent interface names |
| `usages` | `List[Usage]` | List of usages of the interface |
| `dependencies` | `List[Symbol]` | List of dependencies of the interface |
| `is_exported` | `bool` | Whether the interface is exported |

### Methods

#### Interface Operations

```python
# Rename the interface
rename(new_name: str) -> None

# Move the interface to another file
move_to_file(filepath: str) -> None

# Delete the interface
delete() -> None

# Add an attribute
add_attribute(name: str, type_annotation: str) -> Attribute

# Remove an attribute
remove_attribute(name: str) -> None

# Add a parent interface
add_parent_interface(name: str) -> None

# Remove a parent interface
remove_parent_interface(name: str) -> None
```

#### Attribute Analysis

```python
# Get an attribute by name
get_attribute(name: str) -> Attribute

# Get all attributes
get_attributes() -> List[Attribute]

# Get all attributes with a specific type
get_attributes_with_type(type_annotation: str) -> List[Attribute]
```

## TypeAlias

The `TypeAlias` class represents a type alias definition (TypeScript only).

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Name of the type alias |
| `source` | `str` | Source code of the type alias |
| `filepath` | `str` | Path to the file containing the type alias |
| `type_annotation` | `Type` | Type annotation |
| `usages` | `List[Usage]` | List of usages of the type alias |
| `dependencies` | `List[Symbol]` | List of dependencies of the type alias |
| `is_exported` | `bool` | Whether the type alias is exported |

### Methods

#### TypeAlias Operations

```python
# Rename the type alias
rename(new_name: str) -> None

# Move the type alias to another file
move_to_file(filepath: str) -> None

# Delete the type alias
delete() -> None

# Set the type annotation
set_type_annotation(type_annotation: str) -> None
```

## Parameter

The `Parameter` class represents a function parameter.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Name of the parameter |
| `source` | `str` | Source code of the parameter |
| `filepath` | `str` | Path to the file containing the parameter |
| `type_annotation` | `Type` | Type annotation (if any) |
| `default_value` | `Expression` | Default value (if any) |
| `is_rest` | `bool` | Whether the parameter is rest |
| `is_optional` | `bool` | Whether the parameter is optional |
| `parent_function` | `Function` | Parent function |

### Methods

#### Parameter Operations

```python
# Rename the parameter
rename(new_name: str) -> None

# Set the parameter type annotation
set_type_annotation(type_annotation: str) -> None

# Set the parameter default value
set_default_value(default_value: str) -> None

# Delete the parameter
delete() -> None
```

## CodeBlock

The `CodeBlock` class represents a block of code.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `source` | `str` | Source code of the code block |
| `filepath` | `str` | Path to the file containing the code block |
| `statements` | `List[Statement]` | List of statements in the code block |
| `parent_symbol` | `Symbol` | Parent symbol |

### Methods

#### CodeBlock Operations

```python
# Add a statement
add_statement(statement: str) -> Statement

# Remove a statement
remove_statement(statement: Statement) -> None

# Insert a statement at a specific position
insert_statement(position: int, statement: str) -> Statement

# Replace a statement
replace_statement(old_statement: Statement, new_statement: str) -> Statement

# Get all statements
get_statements() -> List[Statement]

# Get all statements of a specific type
get_statements_by_type(statement_type: StatementType) -> List[Statement]
```

## Statement

The `Statement` class represents a code statement.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `source` | `str` | Source code of the statement |
| `filepath` | `str` | Path to the file containing the statement |
| `start_line` | `int` | Start line of the statement in the file |
| `end_line` | `int` | End line of the statement in the file |
| `parent_block` | `CodeBlock` | Parent code block |
| `statement_type` | `StatementType` | Type of the statement |

### Methods

#### Statement Operations

```python
# Edit the statement
edit(new_source: str) -> None

# Delete the statement
delete() -> None

# Insert a statement before this statement
insert_before(statement: str) -> Statement

# Insert a statement after this statement
insert_after(statement: str) -> Statement

# Replace the statement
replace(new_statement: str) -> Statement
```

## Expression

The `Expression` class represents a code expression.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `source` | `str` | Source code of the expression |
| `filepath` | `str` | Path to the file containing the expression |
| `start_line` | `int` | Start line of the expression in the file |
| `end_line` | `int` | End line of the expression in the file |
| `parent_statement` | `Statement` | Parent statement |
| `expression_type` | `ExpressionType` | Type of the expression |

### Methods

#### Expression Operations

```python
# Edit the expression
edit(new_source: str) -> None

# Delete the expression
delete() -> None

# Replace the expression
replace(new_expression: str) -> Expression
```

## Visualization

The `VisualizationManager` class provides visualization capabilities.

### Methods

#### Call Graph Visualization

```python
# Get the call graph for a function
get_call_graph(function_name: str) -> Graph

# Visualize the call graph for a function
visualize_call_graph(function_name: str) -> None

# Export the call graph for a function
export_call_graph(function_name: str, filepath: str) -> None
```

#### Dependency Graph Visualization

```python
# Get the dependency graph for a symbol
get_dependency_graph(symbol_name: str) -> Graph

# Visualize the dependency graph for a symbol
visualize_dependency_graph(symbol_name: str) -> None

# Export the dependency graph for a symbol
export_dependency_graph(symbol_name: str, filepath: str) -> None
```

#### Import Graph Visualization

```python
# Get the import graph
get_import_graph() -> Graph

# Visualize the import graph
visualize_import_graph() -> None

# Export the import graph
export_import_graph(filepath: str) -> None
```

#### Class Hierarchy Visualization

```python
# Get the class hierarchy
get_class_hierarchy() -> Graph

# Visualize the class hierarchy
visualize_class_hierarchy() -> None

# Export the class hierarchy
export_class_hierarchy(filepath: str) -> None
```

## Git Operations

The `RepoOperator` class provides Git operations.

### Methods

#### Branch Operations

```python
# Create a branch
create_branch(name: str) -> bool

# Checkout a branch
checkout_branch(name: str) -> CheckoutResult

# Delete a branch
delete_branch(name: str) -> bool

# Get all branches
get_branches() -> List[str]

# Get the current branch
get_current_branch() -> str
```

#### Commit Operations

```python
# Commit changes
commit(message: str) -> str

# Get all commits
get_commits() -> List[GitCommit]

# Get a commit by SHA
get_commit(sha: str) -> GitCommit

# Get the diff for a commit
get_commit_diff(sha: str) -> Diff
```

#### Pull Request Operations

```python
# Create a pull request
create_pr(title: str, body: str, base_branch: str = None, head_branch: str = None) -> PullRequest

# Get a pull request
get_pr(pr_id: int) -> PullRequest

# Get all pull requests
get_prs() -> List[PullRequest]

# Get the diff for a pull request
get_pr_diff(pr_id: int) -> str

# Create a comment on a pull request
create_pr_comment(pr_number: int, body: str) -> None

# Create a review comment on a pull request
create_pr_review_comment(pr_number: int, body: str, commit_sha: str, path: str, line: int = None, side: str = "RIGHT", start_line: int = None) -> None
```

#### Remote Operations

```python
# Push changes
push(remote: str = "origin", branch: str = None) -> PushInfoList

# Pull changes
pull(remote: str = "origin", branch: str = None) -> None

# Fetch changes
fetch(remote: str = "origin", branch: str = None) -> None

# Get all remotes
get_remotes() -> List[str]
```

