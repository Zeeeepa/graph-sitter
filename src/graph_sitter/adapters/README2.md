Parsing Codebases
The primary entrypoint to programs leveraging Graph-sitter is the Codebase class.

​
Local Codebases
Construct a Codebase by passing in a path to a local git repository or any subfolder within it. The path must be within a git repository (i.e., somewhere in the parent directory tree must contain a .git folder).


Copy
from graph_sitter import Codebase

# Parse from a git repository root
codebase = Codebase("path/to/repository")

# Parse from a subfolder within a git repository
codebase = Codebase("path/to/repository/src/subfolder")

# Parse from current directory (must be within a git repo)
codebase = Codebase("./")

# Specify programming language (instead of inferring from file extensions)
codebase = Codebase("./", language="typescript")
By default, Graph-sitter will automatically infer the programming language of the codebase and parse all files in the codebase. You can override this by passing the language parameter with a value from the ProgrammingLanguage enum.

The initial parse may take a few minutes for large codebases. This pre-computation enables constant-time operations afterward. Learn more here.

​
Remote Repositories
To fetch and parse a repository directly from GitHub, use the from_repo function.


Copy
from graph_sitter import Codebase
# Fetch and parse a repository (defaults to /tmp/codegen/{repo_name})
codebase = Codebase.from_repo('fastapi/fastapi')

# Customize temp directory, clone depth, specific commit, or programming language
codebase = Codebase.from_repo(
    'fastapi/fastapi',
    tmp_dir='/custom/temp/dir',  # Optional: custom temp directory
    commit='786a8ada7ed0c7f9d8b04d49f24596865e4b7901',  # Optional: specific commit
    shallow=False,  # Optional: full clone instead of shallow
    language="python"  # Optional: override language detection
)
Remote repositories are cloned to the /tmp/codegen/{repo_name} directory by default. The clone is shallow by default for better performance.

​
Configuration Options
You can customize the behavior of your Codebase instance by passing a CodebaseConfig object. This allows you to configure secrets (like API keys) and toggle specific features:


Copy
from graph_sitter import Codebase
from codegen.configs.models.codebase import CodebaseConfig
from codegen.configs.models.secrets import SecretsConfig

codebase = Codebase(
    "path/to/repository",
    config=CodebaseConfig(debug=True),
    secrets=SecretsConfig(openai_api_key="your-openai-key")   # For AI-powered features
)
CodebaseConfig and SecretsConfig allow you to configure
config: Toggle specific features like language engines, dependency management, and graph synchronization
secrets: API keys and other sensitive information needed by the codebase
For a complete list of available feature flags and configuration options, see the source code on GitHub.

​
Advanced Initialization
For more complex scenarios, Graph-sitter supports an advanced initialization mode using ProjectConfig. This allows for fine-grained control over:

Repository configuration
Base path and subdirectory filtering
Multiple project configurations
Here’s an example:


Copy
from graph_sitter import Codebase
from codegen.git.repo_operator.local_repo_operator import LocalRepoOperator
from codegen.git.schemas.repo_config import BaseRepoConfig
from codegen.sdk.codebase.config import ProjectConfig

codebase = Codebase(
    projects = [
        ProjectConfig(
            repo_operator=LocalRepoOperator(
                repo_path="/tmp/codegen-sdk",
                repo_config=BaseRepoConfig(),
                bot_commit=True
            ),
            language="typescript",
            base_path="src/codegen/sdk/typescript",
            subdirectories=["src/codegen/sdk/typescript"]
        )
    ]
)

Reusable Codemods
Graph-sitter enables you to create reusable code transformations using Python functions decorated with @graph_sitter.function. These codemods can be shared, versioned, and run by your team.

​
Creating Codemods
The easiest way to create a new codemod is using the CLI create command:


Copy
gs create rename-function .
This creates a new codemod in your .codegen/codemods directory:


Copy
import graph_sitter
from graph_sitter import Codebase

@graph_sitter.function("rename-function")
def run(codebase: Codebase):
    """Add a description of what this codemod does."""
    # Add your code here
    pass
Codemods are stored in .codegen/codemods/name/name.py and are tracked in Git for easy sharing.

​
AI-Powered Generation with -d
You can use AI to generate an initial implementation by providing a description:


Copy
gs create rename-function . -d "Rename the getUserData function to fetchUserProfile"
This will:

Generate an implementation based on your description
Create a custom system prompt that you can provide to an IDE chat assistant (learn more about working with AI)
Place both files in the codemod directory
​
Running Codemods
Once created, run your codemod using:


Copy
gs run rename-function
The execution flow:

Graph-sitter parses your codebase into a graph representation
Your codemod function is executed against this graph
Changes are tracked and applied to your filesystem
A diff preview shows what changed
​
Codemod Structure
A codemod consists of three main parts:

The @graph_sitter.function decorator that names your codemod
A run function that takes a Codebase parameter
Your transformation logic using the Codebase API

Copy
import graph_sitter
from graph_sitter import Codebase

@graph_sitter.function("update-imports")
def run(codebase: Codebase):
    """Update import statements to use new package names."""
    for file in codebase.files:
        for imp in file.imports:
            if imp.module == "old_package":
                imp.rename("new_package")
    codebase.commit()
​
Arguments
Codemods can accept arguments using Pydantic models:


Copy
from pydantic import BaseModel

class RenameArgs(BaseModel):
    old_name: str
    new_name: str

@graph_sitter.function("rename-function")
def run(codebase: Codebase, arguments: RenameArgs):
    """Rename a function across the codebase."""
    old_func = codebase.get_function(arguments.old_name)
    if old_func:
        old_func.rename(arguments.new_name)
    codebase.commit()
Run it with:


Copy
gs run rename-function --arguments '{"old_name": "getUserData", "new_name": "fetchUserProfile"}'
​
Directory Structure
Your codemods live in a dedicated directory structure:


Copy
.codegen/
└── codemods/
    └── rename_function/
        ├── rename_function.py       # The codemod implementation
        └── rename_function_prompt.md  # 

The .codegen Directory
The .codegen directory contains your project’s Graph-sitter configuration, codemods, and supporting files. It’s automatically created when you run gs init.

​
Directory Structure

Copy
.codegen/
├── .venv/            # Python virtual environment (gitignored)
├── config.toml       # Project configuration
├── codemods/         # Your codemod implementations
├── jupyter/          # Jupyter notebooks for exploration
└── codegen-system-prompt.txt  # AI system prompt
​
Initialization
The directory is created and managed using the gs init command:


Copy
gs init [--repo-name NAME] [--organization-name ORG]
​
Virtual Environment
Graph-sitter maintains its own virtual environment in .codegen/.venv/ to ensure consistent package versions and isolation from your project’s dependencies. This environment is:

Created using uv for fast, reliable package management
Initialized with Python 3.13
Automatically managed by Graph-sitter commands
Used for running codemods and Jupyter notebooks
Gitignored to avoid committing environment-specific files
The environment is created during gs init and used by commands like gs run and gs notebook.

To debug codemods, you will need to set the python virtual environment in your IDE to .codegen/.venv
​
Configuration
The .env file stores your project settings:


Copy
REPOSITORY_OWNER = "your-org"
REPOSITORY_PATH = "/root/git/your-repo"
REPOSITORY_LANGUAGE = "python"  # or other supported language
This configuration is used by Graph-sitter to provide language-specific features and proper repository context.

​
Git Integration
Graph-sitter automatically adds appropriate entries to your .gitignore:


Copy
# Codegen
.codegen/.venv/
.codegen/docs/
.codegen/jupyter/
.codegen/codegen-system-prompt.txt
While most directories are ignored, your codemods in .codegen/codemods/ and config.toml are tracked in Git
The virtual environment and Jupyter notebooks are gitignored to avoid environment-specific issues
​
Working with Codemods
The codemods/ directory is where your transformation functions live. You can create new codemods using:


Copy
gs create my-codemod PATH [--description "what it does"]
This will:

Create a new file in .codegen/codemods/
Generate a system prompt in .codegen/prompts/ (if using --description)
Set up the necessary imports and decorators
Use gs list to see all codemods in your project.

​
Jupyter Integration
The jupyter/ directory contains notebooks for interactive development:


Copy
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase('../../')

# Print stats
print(f"📚 Total Files: {len(codebase.files)}")
print(f"⚡ Total Functions: {len(codebase.functions)}")
A default notebook is created during initialization to help you explore your codebase.

​
Next Steps
After initializing your .codegen directory:

Create your first codemod:

Copy
gs create my-codemod . -d "describe what you want to do"
Run it:

Copy
gs run my-codemod --apply-local

Function Decorator
​
Function Decorator
The function decorator is used to define codegen functions within your application. It allows you to specify a name for the function that will be ran making it easier to run specific codemods

​
Usage
To use the function decorator, simply annotate your function with @graph_sitter.function and provide a name as an argument.

​
Example

Copy
@graph_sitter.function('my-function')
def run(codebase):
    pass
In this example, the function run is decorated with @graph_sitter.function and given the name 'my-function'. This name will be used when the function is ran.

​
Parameters
name (str): The name of the function to be used when ran.
​
Description
The function decorator is part of the codegen SDK CLI and is used to mark functions that are intended to be ran as part of a code generation process. It ensures that the function is properly registered and can be invoked with the specified name.

​
CLI Examples
​
Running a Function
To run a deployed function using the CLI, use the following command:


Copy
gs run my-function
This command runs the function named my-function.

​
See Also
Codebase Visualization: For visualizing codebases in your application.
CLI Init Command: For initializing projects or environments related to the function decorator.
CLI Create Command: For creating new functions or projects using the CLI.
CLI Run Command: For running code or scripts using the CLI.Language Support
Graph-sitter provides first-class support for both Python and TypeScript codebases. The language is automatically inferred when you initialize a codebase.

​
Language Detection
When you create a new Codebase instance, Graph-sitter automatically detects the programming language:


Copy
from graph_sitter import Codebase

# Automatically detects Python or TypeScript
codebase = Codebase("./")

# View language with `codebase.language`
print(codebase.language)  # "python" or "typescript"
Learn more about codebase initialization options in Parsing Codebases.

​
Type System
Graph-sitter uses specialized types for each language. These are defined as type aliases:


Copy
# Python codebases use PyCodebaseType
PyCodebaseType = Codebase[
    PyFile, Directory, PySymbol, PyClass, PyFunction,
    PyImport, PyAssignment, Interface, TypeAlias,
    PyParameter, PyCodeBlock
]

# TypeScript codebases use TSCodebaseType
TSCodebaseType = Codebase[
    TSFile, Directory, TSSymbol, TSClass, TSFunction,
    TSImport, TSAssignment, TSInterface, TSTypeAlias,
    TSParameter, TSCodeBlock
]
Every code element has both a Python and TypeScript implementation that inherits from a common base class. For example:

Function
PyFunction
TSFunction
Class
PyClass
TSClass
Import
PyImport
TSImport
…


Copy
# Base class (core/function.py)
class Function:
    """Abstract representation of a Function."""
    pass

# Python implementation (python/function.py)
class PyFunction(Function):
    """Extends Function for Python codebases."""
    pass

# TypeScript implementation (typescript/function.py)
class TSFunction(Function):
    """Extends Function for TypeScript codebases."""
    pass
This inheritance pattern means that most Graph-sitter programs can work with either Python or TypeScript without modification, since they share the same API structure.


Copy
# Works for both Python and TypeScript
for function in codebase.functions:
    print(f"Function: {function.name}")
    print(f"Parameters: {[p.name for p in function.parameters]}")
    print(f"Return type: {function.return_type}")
​
TypeScript-Specific Features
Some features are only available in TypeScript codebases:

Types and Interfaces: TypeScript’s rich type system (TSTypeAlias, TSInterface)
Exports: Module exports and re-exports (TSExport)
JSX/TSX: React component handling (see React and JSX)
Example of TypeScript-specific features:


Copy
# Only works with TypeScript codebases
if isinstance(codebase, TSCodebaseType):
    # Work with TypeScript interfaces
    for interface in codebase.interfaces:
        print(f"Interface: {interface.name}")
        print(f"Extends: {[i.name for i in interface.parent_interfaces]}")

    # Work with type aliases
    for type_alias in codebase.type_aliases:

Commit and Reset
Graph-sitter requires you to explicitly commit changes by calling codebase.commit().

Keeping everything in memory enables fast, large-scale writes. See the How it Works guide to learn more.

You can manage your codebase’s state with two core APIs:

Codebase.commit() - Commit changes to disk
Codebase.reset() - Reset the codebase and filesystem to its initial state
​
Committing Changes
When you make changes to your codebase through Codegen’s APIs, they aren’t immediately written to disk. You need to explicitly commit them with codebase.commit():


Copy
from graph_sitter import Codebase

codebase = Codebase("./")

# Make some changes
file = codebase.get_file("src/app.py")
file.before("# 🌈 hello, world!")

# Changes aren't on disk yet
codebase.commit()  # Now they are!
This transaction-like behavior helps ensure your changes are atomic and consistent.

​
Resetting State
The codebase.reset() method allows you to revert the codebase to its initial state:


Copy
# Make some changes
codebase.get_file("src/app.py").remove()
codebase.create_file("src/new_file.py", "x = 1")

# Check the changes
assert codebase.get_file("src/app.py", optional=True) is None
assert codebase.get_file("src/new_file.py") is not None

# Reset everything
codebase.reset()

# Changes are reverted
assert codebase.get_file("src/app.py") is not None
assert codebase.get_file("src/new_file.py", optional=True) is None
        print(f"Type alias: {type_alias.name}")

Git Operations
Many workflows require Git operations. Graph-sitter provides a high-level API for common Git operations through the Codebase class, including:

Codebase.git_commit(…)
Codebase.checkout(…)
​
Committing Changes to Git
You can commit changes to Git using the Codebase.git_commit(…):


Copy
# Make some changes and call `commit()` to sync them to disk
codebase.functions[0].rename('foo')
codebase.commit()

# Commit all staged changes to git with a message
commit = codebase.git_commit("feat: update function signatures")

# You can also verify the commit (runs pre-commit hooks)
commit = codebase.git_commit("feat: update signatures", verify=True)

# The method returns the commit object if changes were committed, None otherwise
if commit:
    print(f"Created commit: {commit.hexsha}")
git_commit will only commit changes that have been synced to the filesystem by calling Codebase.commit(). See Commit and Reset for more details.

​
Checking Current Git State
Graph-sitter provides properties to check the current Git state:


Copy
# Get the default branch (e.g. 'main' or 'master')
default = codebase.default_branch
print(f"Default branch: {default}")

# Get the current commit
current = codebase.current_commit
if current:
    print(f"Current commit: {current.hexsha}")
​
Checking Out Branches and Commits
The Codebase.checkout(…) method allows you to switch between branches and commits.

This will automatically re-parse the codebase to reflect the new state.


Copy
# Checkout a branch
result = codebase.checkout(branch="feature/new-api")

# Create a new branch if it doesn't exist
result = codebase.checkout(branch="feature/new-api", create_if_missing=True)

# Checkout a specific commit
result = codebase.checkout(commit="abc123")

# Checkout and pull from remote
result = codebase.checkout(branch="main", remote=True)

Files and Directories
Graph-sitter provides three primary abstractions for working with your codebase’s file structure:

File - Represents a file in the codebase (e.g. README.md, package.json, etc.)
SourceFile - Represents a source code file (e.g. Python, TypeScript, React, etc.)
Directory - Represents a directory in the codebase
SourceFile is a subclass of File that provides additional functionality for source code files.

​
Accessing Files and Directories
You typically access files from the codebase object with two APIs:

codebase.get_file(…) - Get a file by its path
codebase.files - Enables iteration over all files in the codebase

Copy
# Get a file from the codebase
file = codebase.get_file("path/to/file.py")

# Iterate over all files in the codebase
for file in codebase.files:
    pass

# Check if a file exists
exists = codebase.has_file("path/to/file.py")
These APIs are similar for Directory, which provides similar methods for accessing files and subdirectories.


Copy
# Get a directory
dir = codebase.get_directory("path/to/dir")

# Iterate over all files in the directory
for file in dir.files:
    pass

# Get the directory containing a file:
dir = file.directory

# Check if a directory exists
exists = codebase.has_directory("path/to/dir")
​
Differences between SourceFile and File
File - a general purpose class that represents any file in the codebase including non-code files like README.md, .env, .json, image files, etc.
SourceFile - a subclass of File that provides additional functionality for source code files written in languages supported by the codegen-sdk (Python, TypeScript, JavaScript, React).
The majority of intended use cases involve using exclusively SourceFile objects as these contain code that can be parsed and manipulated by the codegen-sdk. However, there may be cases where it will be necessary to work with non-code files. In these cases, the File class can be used.

By default, the codebase.files property will only return SourceFile objects. To include non-code files the extensions='*' argument must be used.


Copy
# Get all source files in the codebase
source_files = codebase.files

# Get all files in the codebase (including non-code files)
all_files = codebase.files(extensions="*")
When getting a file with codebase.get_file, files ending in .py, .js, .ts, .jsx, .tsx are returned as SourceFile objects while other files are returned as File objects.

Furthermore, you can use the isinstance function to check if a file is a SourceFile:


Copy
py_file = codebase.get_file("path/to/file.py")
if isinstance(py_file, SourceFile):
    print(f"File {py_file.filepath} is a source file")

# prints: `File path/to/file.py is a source file`

mdx_file = codebase.get_file("path/to/file.mdx")
if not isinstance(mdx_file, SourceFile):
    print(f"File {mdx_file.filepath} is a non-code file")

# prints: `File path/to/file.mdx is a non-code file`
Currently, the codebase object can only parse source code files of one language at a time. This means that if you want to work with both Python and TypeScript files, you will need to create two separate codebase objects.

​
Accessing Code
SourceFiles and Directories provide several APIs for accessing and iterating over their code.

See, for example:

.functions (SourceFile / Directory) - All Functions in the file/directory
.classes (SourceFile / Directory) - All Classes in the file/directory
.imports (SourceFile / Directory) - All Imports in the file/directory
.get_function(...) (SourceFile / Directory) - Get a specific function by name
.get_class(...) (SourceFile / Directory) - Get a specific class by name
.get_global_var(...) (SourceFile / Directory) - Get a specific global variable by name

Copy
# Get all functions in a file
for function in file.functions:
    print(f"Found function: {function.name}")
    print(f"Parameters: {[p.name for p in function.parameters]}")
    print(f"Return type: {function.return_type}")

# Get all classes
for cls in file.classes:
    print(f"Found class: {cls.name}")
    print(f"Methods: {[m.name for m in cls.methods]}")
    print(f"Attributes: {[a.name for a in cls.attributes]}")

# Get imports (can also do `file.import_statements`)
for imp in file.imports:
    print(f"Import from: {imp.module}")
    print(f"Imported symbol: {[s.name for s in imp.imported_symbol]}")

# Get specific symbols
main_function = file.get_function("main")
user_class = file.get_class("User")
config = file.get_global_var("CONFIG")

# Access code blocks
if main_function:
    for statement in main_function.code_block.statements:
        print(f"Statement type: {statement.statement_type}")

# Get local variables in a function
if main_function:
    local_vars = main_function.code_block.get_local_var_assignments()
    for var in local_vars:
        print(f"Local var: {var.name} = {var.value}")
​
Working with Non-Code Files (README, JSON, etc.)
By default, Graph-sitter focuses on source code files (Python, TypeScript, etc). However, you can access all files in your codebase, including documentation, configuration, and other non-code files like README.md, package.json, or .env:


Copy
# Get all files in the codebase (including README, docs, config files)
files = codebase.files(extensions="*")

# Print files that are not source code (documentation, config, etc)
for file in files:
    if not file.filepath.endswith(('.py', '.ts', '.js')):
        print(f"📄 Non-code file: {file.filepath}")
You can also filter for specific file types:


Copy
# Get only markdown documentation files
docs = codebase.files(extensions=[".md", ".mdx"])

# Get configuration files
config_files = codebase.files(extensions=[".json", ".yaml", ".toml"])
These APIs are similar for Directory, which provides similar methods for accessing files and subdirectories.

​
Raw Content and Metadata

Copy
# Grab raw file string content
content = file.content # For text files
print('Length:', len(content))
print('# of functions:', len(file.functions))

# Access file metadata
name = file.name # Base name without extension
extension = file.extension # File extension with dot
filepath = file.filepath # Full relative path
dir = file.directory # Parent directory

# Access directory metadata
name = dir.name # Base name without extension
path = dir.path # Full relative path from repository root
parent = dir.parent # Parent directory
​
Editing Files Directly
Files themselves are Editable objects, just like Functions and Classes.

Learn more about the Editable API.

This means they expose many useful operations, including:

File.search - Search for all functions named “main”
File.edit - Edit the file
File.replace - Replace all instances of a string with another string
File.insert_before - Insert text before a specific string
File.insert_after - Insert text after a specific string
File.remove - Remove a specific string

Copy
# Get a file
file = codebase.get_file("path/to/file.py")

# Replace all instances of a string
file.replace("name", "new_name")
file.replace("name", "new_name", include_comments=False) # Don't edit comments

# Replace entire text of the file
file.edit('hello, world!')

# Get + delete all instances of a string
for editable in file.search("foo"):
    editable.remove()

# Insert text at the top of the file
file.insert_before("def main():\npass")
# ... or at the bottom
file.insert_after("def end():\npass")

# Delete the file
file.remove()
You can frequently do bulk modifictions via the .edit(…) method or .replace(…) method.

Most useful operations will have bespoke APIs that handle edge cases, update references, etc.

​
Moving and Renaming Files
Files can be manipulated through methods like File.update_filepath(), File.rename(), and File.remove():


Copy
# Move/rename a file
file.update_filepath("/path/to/foo.py")  # Move to new location
file.rename("bar")  # Rename preserving extension, e.g. `bar.py`

# Remove a file (potentially destructive)
file.remove()

# Move all tests to a tests directory
for file in codebase.files:
    if 'test_' in file.name:
        # This will handle updating imports and other references
        file.update_filepath('tests/' + file.filepath.replace("test_", ""))
Removing files is a potentially breaking operation. Only remove files if they have no external usages.

​
Directories
Directories expose a similar API to the File class, with the addition of the subdirectories property.


Copy
# Get a directory
dir = codebase.get_directory("path/to/dir")

# Iterate over all directories in the codebase
for directory in codebase.directories:
    print(f"Found directory: {directory.path}")

# Check directory existence
exists = codebase.has_directory("path/to/dir")

# Access metadata
name = dir.name  # Directory name
path = dir.path  # Full path
parent = dir.parent  # Parent directory

# Get specific items
file = dir.get_file("file.py")
subdir = dir.get_subdirectory("subdir")

# Get all ancestor subdirectories
subdirs = dir.subdirectories

# Get the parent directory
parent_dir = dir.parent

# Find all child directories
for subdir in dir.subdirectories:
    if dir.parent == subdir:
        print(f"Found child subdirectory: {subdir.path}")

# Move to new location
dir.update_filepath("new/path")

# Rename directory in place
dir.rename("new_name")

# Remove a directory and all contents (potentially destructive)
dir.remove()

The Editable API
Every code element in Graph-sitter is an Editable - meaning it can be manipulated while maintaining correctness.

All higher-level code manipulation APIs are built on top of the atomic Editable API.

​
Core Concepts
Every Editable provides:

Information about the source code:
source - the text content of the Editable
extended_source - includes relevant content like decorators, comments, etc.
Information about the file that contains the Editable:
file - the SourceFile that contains this Editable
Relationship tracking
parent_class - the Class that contains this Editable
parent_function - the Function that contains this Editable
parent_statement - the Statement that contains this Editable
Safe modification operations
​
Basic Editing
There are several fundamental ways to modify code with Editables:


Copy
# 1. edit() - Replace entire source with new content
function = codebase.get_function("process_data")
function.edit("""
def process_data(input_data: dict) -> dict:
    return transform(input_data)
""")

# 2. Replace - Substitute text while preserving context
class_def = codebase.get_class("UserModel")
class_def.replace("user_id", "account_id")  # Updates all occurrences

# 3. Remove - Safely delete code with proper cleanup
unused_import = file.get_import("from utils import deprecated_func")
unused_import.remove()  # Handles formatting, commas, etc

# 4. Insert - Add code before or after an element
function.insert_before("# Process user input")  # Adds comment before function
function.insert_after("""
def validate_data(data: dict) -> bool:
    return all(required in data for required in REQUIRED_FIELDS)
""")  # Adds new function after
​
Finding and Searching
Editables provide powerful search capabilities:


Copy
# Find string literals
results = function.find_string_literals(["error", "warning"])
results = function.find_string_literals(["error"], fuzzy_match=True)

# Search with regex
matches = function.search(r"data\['[^']*'\]")  # Find dict access
matches = function.search("TODO:", include_comments=True)

# Find specific patterns
variables = function.get_variable_usages("config")
function_calls = function.function_calls  # All function calls within this node
​
Smart Formatting
Graph-sitter handles formatting details automatically:


Copy
# Adding to import statements
import_stmt = file.get_import("from mylib import func1")
import_stmt.add_symbol("func2")  # Handles comma placement
import_stmt.add_symbol("func3")  # Maintains proper formatting

# Multi-line formatting is preserved
from mylib import (
    func1,
    func2,    # New imports maintain
    func3     # existing style
)
​
Safe Removals
Removing code elements is safe and clean:


Copy
# Remove a function and its decorators
function.remove()  # Removes associated comments and formatting

# Remove imports cleanly
import_stmt.remove()  # Handles commas and whitespace
​
Working with References
Editables track their relationships to other code elements:


Copy
# Find and update all references
function = codebase.get_function("old_name")
function.rename("new_name")  # Updates all usages

# Navigate relationships
print(function.parent_function)  # Containing function
print(function.parent_class)    # Containing class
print(function.parent_statement)  # Containing statement
​
Understanding Context
Editables provide rich information about their location and context in the code:

​
Parent Relationships

Copy
# Get containing elements
function = codebase.get_function("process_data")
print(function.parent_class)     # Class containing this function
print(function.parent_function)  # Function containing this function (for nested functions)
print(function.parent_statement) # Statement containing this function

# Check if top-level
is_top_level = function.parent_class is None and function.parent_function is None
​
Statement Containment
The is_wrapped_in method lets you check if an Editable is contained within specific types of statements:


Copy
# Check containment in statement types
is_in_try = function.is_wrapped_in("try")
is_in_if = function.is_wrapped_in("if")
is_in_while = function.is_wrapped_in("while")

# Get the first parent statements of a certain type
if_block = function.parent_of_type(IfStatement)

# Common patterns
if function.is_wrapped_in(IfStatement):
    print("This is in an IfBlock")

if variable.is_wrapped_in(WithStatement):
    print("Variable used in WithStatement")
​
Common Use Cases

Copy
# Move nested functions to module level
for func in file.functions:
    if func.parent_function:  # This is a nested function
        func.parent_function.insert_before(func.source) # Move to module level
        func.remove() # Remove the nested function

# Find variables defined in unsafe blocks
for var in function.code_block.get_local_var_assignments():
    if var.is_wrapped_in(TryStatement):
        print(f"Warning: {var.name} defined in try block")


Accessing Symbols
The Codebase class provides getters and iterators for functions, classes and symbols:


Copy
# Core symbol types
symbol = codebase.get_symbol("process_data") # will return a Function, Class, etc.
function = codebase.get_function("process_data")
class_def = codebase.get_class("DataProcessor")

# Iterate over all symbols (includes functions + classes)
for symbol in codebase.symbols:
    print(symbol.name)

# Iterate over all functions and classes
for symbol in codebase.functions + codebase.classes:
    print(symbol.name)
​
Shared APIs
All symbols share common APIs for manipulation:

The Editable API
Metadata
symbol.name
symbol.source
symbol.docstring
Edit operations
symbol.set_docstring
symbol.move_to_file (see Moving Symbols)
Graph relations (See Usages and Dependencies)
symbol.usages
symbol.dependencies
​
Name operations

Copy
# Name operations
print(symbol.name)
symbol.rename("new_name")

# Source code
print(symbol.source)  # Get source code
symbol.edit("new source code")  # Modify source

# Documentation
print(symbol.docstring)  # Get docstring
symbol.set_docstring("New documentation")

# Move symbol to new file
symbol.move_to_file(new_file)

# Add before/after other symbols
symbol.insert_before("# deprecated")
symbol.insert_after("# end deprecated")
​
Function Statement Manipulation
Functions provide special APIs for adding statements to their body:

Function.prepend_statements - add statements to the start of the function body
Function.add_statements - add statements to the end of the function body

Copy
# Add statements at the start of a function
function.prepend_statements("print('Starting function')")
method.prepend_statements("self.validate_input()")

# Add statements at the end of a function
function.add_statements("print('Done')")
method.add_statements("return self.result")
The statement manipulation APIs (prepend_statements and add_statements) are only available on Function objects. For other symbols, use the general Editable APIs like insert_before and insert_after.

​
Common Patterns
Most Graph-sitter programs focus on finding and manipulating symbols:


Copy
# Find and modify functions
for function in codebase.functions:
    if function.name.startswith("old_"):
        # Rename function
        function.rename(function.name.replace("old_", "new_"))
        # Update docstring
        function.set_docstring("Updated version of function")

# Update class methods
for method in class_def.methods:
    # Add logging
    method.prepend_statements("logger.info('Called {}'".format(method.name))


The Class API
The Class API extends the Symbol API to support methods, attributes, and inheritance hierarchies.

​
Methods and Method Usages
Classes provide access to their methods and method usages through an intuitive API:


Copy
# Access methods
for method in class_def.methods:
    print(f"Method: {method.name}")
    # Find all usages of this method
    for usage in method.usages:
        print(f"Used in {usage.file.name}")

# Get specific methods
init_method = class_def.constructor  # Get __init__ method
process_method = class_def.get_method("process_data")

# Filter methods
public_methods = class_def.methods(private=False)  # Exclude private methods
regular_methods = class_def.methods(magic=False)   # Exclude magic methods
Methods are typed as Function objects.

​
Class Attributes
Attributes can be accessed and modified easily:


Copy
# Access all attributes
for attr in class_def.attributes:
    print(f"Attribute: {attr.name}")

# Add new attributes
class_def.add_attribute_from_source("count: int = 0")

# Get specific attribute
name_attr = class_def.get_attribute("name")

# Add attribute from another class
other_class = codebase.get_class("OtherClass")
class_def.add_attribute(
    other_class.get_attribute("config"),
    include_dependencies=True  # Also adds required imports
)
​
Manipulating Attributes
Attributes expose their own API for modification and analysis:


Copy
# Modify attribute values and types
attr = class_def.get_attribute("count")
attr.set_value("42")  # Change value
attr.assignment.set_type_annotation("float")  # Change type
attr.assignment.type.remove()  # Remove type annotation

# Find attribute usages
for usage in attr.usages:
    print(f"Used in {usage.file.name}")

# Find local usages (within the class)
for usage in attr.local_usages:
    print(f"Used in method: {usage.parent_function.name}")

# Rename attributes (updates all references)
attr.rename("new_name")  # Also updates self.count -> self.new_name

# Remove attributes
attr.remove()  # Removes the attribute definition

# Check attribute properties
if attr.is_private:  # Starts with underscore
    print("Private attribute")
if attr.is_optional:  # Optional[Type] or Type | None
    print("Optional attribute")

# Access underlying value
if attr.value:  # The expression assigned to the attribute
    print(f"Default value: {attr.value.source}")
Attribute operations automatically handle all references, including self.attribute usages in methods and string references.

​
Working with Inheritance
You can navigate inheritance hierarchies with APIs including:

Class.superclasses
Class.subclasses
Class.is_subclass_of

Copy
class_def = codebase.get_class("Cube")

# View ancestors
all_ancestors = class_def.superclasses # All classes inherited
immediate_parents = class_def.superclasses(max_depth=1)  # Direct parents only

# Inheritance-aware method lookup
method = class_def.get_method("process")  # Searches up inheritance chain
if method.parent_class != class_def:
    print(f"Method inherited from {method.parent_class.name}")

# Handle external dependencies
if class_def.is_subclass_of("Enum"):  # Works with stdlib/external classes
    print("This is an enum class")
Likewise, you can modify inheritance by accessing:

Class.parent_class_names
Class.get_parent_class(cls_name)
Which return lists of Name objects.


Copy
# Modify inheritance
parent_names = class_def.parent_class_names
if parent_names[0] == 'BaseClass':
    parent_names[0].edit("NewBaseClass")  # Change parent class

# Get specific parent class
parent_class = class_def.get_parent_class("BaseClass")
if parent_class:
    parent_class.edit("NewBaseClass")  # Change parent class
When working with inheritance, use max_depth to control how far up the inheritance chain to look. max_depth=0 means current class only, max_depth=None means traverse entire hierarchy.

Graph-sitter handles both internal and external parent classes (like stdlib classes). The superclasses property follows the language’s MRO rules for method resolution.

​
Method Resolution Order (MRO)
Graph-sitter follows the target language’s method resolution order (MRO) for inheritance:


Copy
# Access superclasses
for parent in class_def.superclasses:
    print(f"Parent: {parent.name}")

# Check inheritance
if class_def.is_subclass_of("BaseClass"):
    print("This is a subclass of BaseClass")

# Get all subclasses
for child in class_def.subclasses:
    print(f"Child class: {child.name}")

# Access inherited methods/attributes
all_methods = class_def.methods(max_depth=None)  # Include inherited methods
all_attrs = class_def.attributes(max_depth=None)  # Include inherited attributes

The Import API
The Import API provides tools for working with imports and managing dependencies between files.

​
Accessing Imports
You can access these through File.imports and File.import_statements:


Copy
# Direct access to imports via file
for imp in file.imports:
    ...

# Grab by name of symbol being imported
imp = file.get_import('math')

# Grab and filter from a codebase
from codegen.sdk import ExternalModule

external_imports = [i for i in codebase.imports if isinstance(i, ExternalModule)]
​
Common Operations
The Import API provides several methods for modifying imports:


Copy
# Get a specific import
import_stmt = file.get_import("MyComponent")

# Change import source
import_stmt.set_module("./new/path")

# Add/update alias
import_stmt.set_alias("MyAlias")  # import X as MyAlias

# TypeScript-specific operations
import_stmt.make_type_import()  # Convert to 'import type'
import_stmt.make_value_import() # Remove 'type' modifier

# Update multiple properties
import_stmt.update(
    module="./new/path",
    alias="NewAlias",
    is_type=True
)
​
Import Resolution
Imports can be traced to their original symbols:


Copy
# Follow import chain to source
import_stmt = file.get_import("MyComponent")
original = import_stmt.resolved_symbol

if original:
    print(f"Defined in: {original.file.filepath}")
    print(f"Original name: {original.name}")

# Get file relationships
print(f"From file: {import_stmt.from_file.filepath}")
print(f"To file: {import_stmt.to_file.filepath}")
With Python one can specify the PYTHONPATH environment variable which is then considered when resolving packages.

​
Working with External Modules
You can determine if an import references an ExternalModule by checking the type of Import.imported_symbol, like so:


Copy
# Check if import is from external package
for imp in file.imports:
    if isinstance(imp.imported_symbol, ExternalModule):
        print(f"External import: {imp.name} from {imp.module}")
    else:
        print(f"Local import: {imp.name}")
Learn more about external modules here
​
Bulk Operations
Here are patterns for working with multiple imports:


Copy
# Update imports from a specific module
old_path = "./old/path"
new_path = "./new/path"

for imp in file.imports:
    if imp.module == old_path:
        imp.set_module(new_path)

# Remove unused imports (excluding external)
for imp in file.imports:
    if not imp.usages and not isinstance(imp.resolved_symbol, ExternalModule):
        print(f"Removing: {imp.name}")
        imp.remove()

# Consolidate duplicate imports
from collections import defaultdict

module_imports = defaultdict(list)
for imp in file.imports:
    module_imports[imp.module].append(imp)

for module, imports in module_imports.items():
    if len(imports) > 1:
        # Create combined import
        symbols = [imp.name for imp in imports]
        file.add_import(
            f"import {{ {', '.join(symbols)} }} from '{module}'"
        )
        # Remove old imports
        for imp in imports:
            imp.remove()
Always check if imports resolve to external modules before modification to avoid breaking third-party package imports.

​
Import Statements vs Imports
Graph-sitter provides two levels of abstraction for working with imports:

ImportStatement - Represents a complete import statement
Import - Represents individual imported symbols

Python

Typescript

Copy
# One ImportStatement containing multiple Import objects
from math import sin, cos as cosine
# Creates:
# - Import for 'sin'
# - Import for 'cos' with alias 'cosine'
You can access these through File.imports and File.import_statements:


Copy
# Direct access to imports
for imp in file.imports:
    ...

# Access to imports via statements
for stmt in file.import_statements:
    for imp in stmt.imports:

The Export API
The Export API provides tools for managing exports and module boundaries in TypeScript codebases.

Exports are a TS-only language feature
​
Export Statements vs Exports
Similar to imports, Graph-sitter provides two levels of abstraction for working with exports:

ExportStatement - Represents a complete export statement
Export - Represents individual exported symbols

Copy
// One ExportStatement containing multiple Export objects
export { foo, bar as default, type User };
// Creates:
// - Export for 'foo'
// - Export for 'bar' as default
// - Export for 'User' as a type

// Direct exports create one ExportStatement per export
export const value = 42;
export function process() {}
You can access these through your file’s collections:


Copy
# Access all exports in the codebase
for export in codebase.exports:
    ...

# Access all export statements
for stmt in file.export_statements:
    for exp in stmt.exports:
        ...
ExportStatement inherits from Statement, providing operations like remove() and insert_before(). This is particularly useful when you want to manipulate the entire export declaration.

​
Common Operations
Here are common operations for working with exports:


Copy
# Add exports from source code
file.add_export_from_source("export { MyComponent };")
file.add_export_from_source("export type { MyType } from './types';")

# Export existing symbols
component = file.get_function("MyComponent")
file.add_export(component)  # export { MyComponent }
file.add_export(component, alias="default")  # export { MyComponent as default }

# Convert to type export
export = file.get_export("MyType")
export.make_type_export()

# Remove exports
export = file.get_export("MyComponent")
export.remove()  # Removes export but keeps the symbol

# Remove multiple exports
for export in file.exports:
    if not export.is_type_export():
        export.remove()

# Update export properties
export.update(
    name="NewName",
    is_type=True,
    is_default=False
)

# Export from another file
other_file = codebase.get_file("./components.ts")
component = other_file.get_class("Button")
file.add_export(component, from_file=other_file)  # export { Button } from './components';

# Analyze symbols being exported
for export in file.exports:
    if isinstance(export.exported_symbol, ExternalModule):
        print('Exporting ExternalModule')
    else:
        ...
When adding exports, you can:

Add from source code with add_export_from_source()
Export existing symbols with add_export()
Re-export from other files by specifying from_file
The export will automatically handle adding any required imports.

​
Export Types
Graph-sitter supports several types of exports:


Copy
// Direct exports
export const value = 42;                     // Value export
export function myFunction() {}              // Function export
export class MyClass {}                      // Class export
export type MyType = string;                 // Type export
export interface MyInterface {}              // Interface export
export enum MyEnum {}                        // Enum export

// Re-exports
export { foo, bar } from './other-file';     // Named re-exports
export type { Type } from './other-file';    // Type re-exports
export * from './other-file';                // Wildcard re-exports
export * as utils from './other-file';       // Namespace re-exports

// Aliased exports
export { foo as foop };                      // Basic alias
export { foo as default };                   // Default export alias
export { bar as baz } from './other-file';   // Re-export with alias
​
Identifying Export Types
The Export API provides methods to identify and filter exports:

.is_type_export()
.is_default_export()
.is_wildcard_export()

Copy
# Check export types
for exp in file.exports:
    if exp.is_type_export():
        print(f"Type export: {exp.name}")
    elif exp.is_default_export():
        print(f"Default export: {exp.name}")
    elif exp.is_wildcard_export():
        print(f"Wildcard export from: {exp.from_file.filepath}")
​
Export Resolution
You can trace exports to their original symbols:


Copy
for exp in file.exports:
    if exp.is_reexport():
        # Get original and current symbols
        current = exp.exported_symbol
        original = exp.resolved_symbol
        
        print(f"Re-exporting {original.name} from {exp.from_file.filepath}")
        print(f"Through: {' -> '.join(e.file.filepath for e in exp.export_chain)}")
​
Managing Re-exports
You can manage re-exports with the TSExport.is_reexport() API:


Copy
# Create public API
index_file = codebase.get_file("index.ts")

# Re-export from internal files
for internal_file in codebase.files:
    if internal_file.name != "index":
        for symbol in internal_file.symbols:
            if symbol.is_public:
                index_file.add_export(
                    symbol,
                    from_file=internal_file
                )

# Convert default to named exports
for exp in file.exports:
    if exp.is_default_export():
        exp.make_named_export()

# Consolidate re-exports
from collections import defaultdict

file_exports = defaultdict(list)
for exp in file.exports:
    if exp.is_reexport():
        file_exports[exp.from_file].append(exp)

for from_file, exports in file_exports.items():
    if len(exports) > 1:
        # Create consolidated re-export
        names = [exp.name for exp in exports]
        file.add_export_from_source(
            f"export {{ {', '.join(names)} }} from '{from_file.filepath}'"
        )
        # Remove individual exports
        for exp in exports:
            exp.remove()

Core Behaviors
HasName: For elements with Names (Functions, Classes, Assignments, etc.)
HasValue: For elements with Values (Arguments, Assignments, etc.)
HasBlock: For elements containing CodeBlocks (Files, Functions, Classes)
Editable: For elements that can be safely modified (learn more)
These “behaviors” are implemented as inherited classes.
​
Working with Names
The HasName behavior provides APIs for working with named elements:


Copy
# Access the name
print(function.name)  # Base name without namespace
print(function.full_name)  # Full qualified name with namespace

# Modify the name
function.set_name("new_name")  # Changes just the name
function.rename("new_name")    # Changes name and updates all usages

# Get the underlying name node
name_node = function.get_name()
​
Working with Values
The HasValue behavior provides APIs for elements that have values:


Copy
# Access the value
value = variable.value  # Gets the value Expression node
print(value.source)     # Gets the string content

# Modify the value
variable.set_value("new_value")

# Common patterns
if variable.value is not None:
    print(f"{variable.name} = {variable.value.source}")
​
Working with Code Blocks
The HasBlock behavior provides APIs for elements containing code:


Copy
# Access the code block
block = function.code_block
print(len(block.statements))  # Number of statements
printS(block.source)
Learn more about CodeBlocks and Statements here

​
Working with Attributes
The get_attribute method provides APIs for attribute access:


Copy
# Common patterns
class_attr = class_def.get_attribute("attribute_name")
if class_attr:
    print(f"Class variable value: {class_attr.value.source}")
Learn more about working with Attributes here.

​
Behavior Combinations
Many code elements inherit multiple behaviors. For example, a function typically has:


Copy
# Functions combine multiple behaviors
function = codebase.get_function("process_data")

# HasName behavior
print(function.name)
function.rename("process_input")

# HasBlock behavior
print(len(function.code_block.statements))
function.add_decorator("@timer")

# Editable behavior
function.edit("def process_input():\n    pass")
        ...

Statements and Code Blocks
Graph-sitter uses two classes to represent code structure at the highest level:

Statement: Represents a single line or block of code

Can be assignments, imports, loops, conditionals, etc.
Contains source code, dependencies, and type information
May contain nested code blocks (like in functions or loops)
CodeBlock: A container for multiple Statements

Found in files, functions, classes, and control flow blocks
Provides APIs for analyzing and manipulating statements
Handles scope, variables, and dependencies
Graph-sitter provides rich APIs for working with code statements and blocks, allowing you to analyze and manipulate code structure at a granular level.

​
Working with Statements
​
Basic Usage
Every file, function, and class in Graph-sitter has a CodeBlock that contains its statements:


Copy
# Access statements in a file
file = codebase.get_file("main.py")
for statement in file.code_block.statements:
    print(f"Statement type: {statement.statement_type}")

# Access statements in a function
function = file.get_function("process_data")
for statement in function.code_block.statements:
    print(f"Statement: {statement.source}")
​
Filtering Statements
Filter through statements using Python’s builtin isinstance function.


Copy
# Filter statements by type
for stmt in file.code_block.statements:
    if isinstance(stmt, ImportStatement):
        print(stmt)
​
Adding Statements
Functions and Files support .prepend_statement(…) and .add_statement(…) to add statements to the symbol.

See Adding Statements for details.

​
Working with Nested Structures
Frequently you will want to check if a statement is nested within another structure, for example if a statement is inside an if block or a try/catch statement.

Graph-sitter supports this functionality with the Editable.is_wrapped_in(…) method.


Copy
func = codebase.get_function("process_data")
for usage in func.local_variable_usages:
    if usage.is_wrapped_in(IfStatement):
        print(f"Usage of {usage.name} is inside an if block")
Similarly, all Editable objects support the .parent_statement, which can be used to navigate the statement hierarchy.


Copy
func = codebase.get_function("process_data")
for usage in func.local_variable_usages:
    if isinstance(usage.parent_statement, IfStatement):
        print(f"Usage of {usage.name} is directly beneath an IfStatement")
​
Wrapping and Unwrapping Statements
CodeBlocks support wrapping and unwrapping with the following APIs:

.wrap(…) - allows you to wrap a statement in a new structure.
.unwrap(…) - allows you to remove the wrapping structure while preserving the code block’s contents.

Copy
# Wrap code blocks with new structures
function.code_block.wrap("with open('test.txt', 'w') as f:")
# Result:
#   with open('test.txt', 'w') as f:
#       original_code_here...

# Wrap code in a function
file.code_block.wrap("def process_data(a, b):")
# Result:
#   def process_data(a, b):
#       original_code_here...

# Unwrap code from its container
if_block.code_block.unwrap()  # Removes the if statement but keeps its body
while_loop.code_block.unwrap()  # Removes the while loop but keeps its body
Both wrap and unwrap are potentially unsafe changes and will modify business logic.

The unwrap() method preserves the indentation of the code block’s contents while removing the wrapping structure. This is useful for refactoring nested code structures.

​
Statement Types
Graph-sitter supports various statement types, each with specific APIs:

​
Import Statements / Export Statements
See imports and exports for more details.


Copy
# Access import statements
for import_stmt in file.import_statements:
    print(f"Module: {import_stmt.module}")
    for imported in import_stmt.imports:
        print(f"  Imported: {imported.name}")

# Remove specific imports
import_stmt = file.import_statements[0]
import_stmt.imports[0].remove()  # Remove first import

# Remove entire import statement
import_stmt.remove()
​
If/Else Statements
If/Else statements provide rich APIs for analyzing and manipulating conditional logic:


Copy
# Access if/else blocks
if_block = file.code_block.statements[0]
print(f"Condition: {if_block.condition.source}")

# Check block types
if if_block.is_if_statement:
    print("Main if block")
elif if_block.is_elif_statement:
    print("Elif block")
elif if_block.is_else_statement:
    print("Else block")

# Access alternative blocks
for elif_block in if_block.elif_statements:
    print(f"Elif condition: {elif_block.condition.source}")

if else_block := if_block.else_statement:
    print("Has else block")

# Access nested code blocks
for block in if_block.nested_code_blocks:
    print(f"Block statements: {len(block.statements)}")
If blocks also support condition reduction, which can simplify conditional logic:


Copy
# Reduce if condition to True
if_block.reduce_condition(True)
# Before:
#   if condition:
#       print("a")
#   else:
#       print("b")
# After:
#   print("a")

# Reduce elif condition to False
elif_block.reduce_condition(False)
# Before:
#   if a:
#       print("a")
#   elif condition:
#       print("b")
#   else:
#       print("c")
# After:
#   if a:
#       print("a")
#   else:
#       print("c")
When reducing conditions, Graph-sitter automatically handles the restructuring of elif/else chains and preserves the correct control flow.

​
Switch/Match Statements

Copy
# TypeScript switch statements
switch_stmt = file.code_block.statements[0]
for case_stmt in switch_stmt.cases:
    print(f"Case condition: {case_stmt.condition}")
    print(f"Is default: {case_stmt.default}")

    # Access statements in each case
    for statement in case_stmt.code_block.statements:
        print(f"Statement: {statement.source}")

# Python match statements
match_stmt = file.code_block.statements[0]
for case in match_stmt.cases:
    print(f"Pattern: {case.pattern}")
    for statement in case.code_block.statements:
        print(f"Statement: {statement.source}")
​
While Statements

Copy
while_stmt = file.code_block.statements[0]
print(f"Condition: {while_stmt.condition}")

# Access loop body
for statement in while_stmt.code_block.statements:
    print(f"Body statement: {statement.source}")

# Get function calls within the loop
for call in while_stmt.function_calls:
    print(f"Function call: {call.source}")
​
Assignment Statements

Copy
# Access assignments in a code block
for statement in code_block.statements:
    if statement.statement_type == StatementType.ASSIGNMENT:
        for assignment in statement.assignments:
            print(f"Variable: {assignment.name}")
            print(f"Value: {assignment.value}")
​
Working with Code Blocks
Code blocks provide several ways to analyze and manipulate their content:

​
Statement Access

Copy
code_block = function.code_block

# Get all statements
all_statements = code_block.statements

# Get statements by type
if_blocks = code_block.if_blocks
while_loops = code_block.while_loops
try_blocks = code_block.try_blocks

# Get local variables
local_vars = code_block.get_local_var_assignments()
​
Statement Dependencies

Copy
# Get dependencies between statements
function = file.get_function("process")
for statement in function.code_block.statements:
    deps = statement.dependencies
    print(f"Statement {statement.source} depends on: {[d.name for d in deps]}")
​
Parent-Child Relationships

Copy
# Access parent statements
function = file.get_function("main")
parent_stmt = function.parent_statement

# Access nested symbols
class_def = file.get_class("MyClass")
for method in class_def.methods:
    parent = method.parent_statement
    print(f"Method {method.name} is defined in {parent.source}")
​
Common Operations
​
Finding Statements

Copy
# Find specific statements
assignments = [s for s in code_block.statements
              if s.statement_type == StatementType.ASSIGNMENT]

# Find statements by content
matching = [s for s in code_block.statements
           if "specific_function()" in s.source]
​
Analyzing Flow Control

Copy
# Analyze control flow
for statement in code_block.statements:
    if statement.statement_type == StatementType.IF_BLOCK:
        print("Condition:", statement.condition)
        print("Then:", statement.consequence_block.statements)
        if statement.alternative_block:
            print("Else:", statement.alternative_block.statements)
​
Working with Functions

Copy
# Analyze function calls in statements
for statement in code_block.statements:
    for call in statement.function_calls:
        print(f"Calls function: {call.name}")
        print(f"With arguments: {[arg.source for arg in call.arguments]}")

Dependencies and Usages
Graph-sitter pre-computes dependencies and usages for all symbols in the codebase, enabling constant-time queries for these relationships.

​
Overview
Graph-sitter provides two main ways to track relationships between symbols:

.dependencies / - What symbols does this symbol depend on?
.usages / .usages(…) - Where is this symbol used?
Dependencies and usages are inverses of each other. For example, given the following input code:


Copy
# Input code
from module import BaseClass

class MyClass(BaseClass):
    pass
The following assertions will hold in the Codegen API:


Copy
base = codebase.get_symbol("BaseClass")
my_class = codebase.get_symbol("MyClass")

# MyClass depends on BaseClass
assert base in my_class.dependencies

# BaseClass is used by MyClass
assert my_class in base.usages
If A depends on B, then B is used by A. This relationship is tracked in both directions, allowing you to navigate the codebase from either perspective.

used by

depends on

BaseClass

MyClass

MyClass.dependencies answers the question: “which symbols in the codebase does MyClass depend on?”

BaseClass.usages answers the question: “which symbols in the codebase use BaseClass?”

​
Usage Types
Both APIs use the UsageType enum to specify different kinds of relationships:


Copy
class UsageType(IntFlag):
    DIRECT = auto()    # Direct usage within the same file
    CHAINED = auto()   # Usage through attribute access (module.symbol)
    INDIRECT = auto()  # Usage through a non-aliased import
    ALIASED = auto()   # Usage through an aliased import
​
DIRECT Usage
A direct usage occurs when a symbol is used in the same file where it’s defined, without going through any imports or attribute access.


Copy
# Define MyClass
class MyClass:
    def __init__(self):
        pass

# Direct usage of MyClass in same file
class Child(MyClass):
    pass
​
CHAINED Usage
A chained usage occurs when a symbol is accessed through module or object attribute access, using dot notation.


Copy
import module

# Chained usage of ClassB through module
obj = module.ClassB()
# Chained usage of method through obj
result = obj.method()
​
INDIRECT Usage
An indirect usage happens when a symbol is used through a non-aliased import statement.


Copy
from module import BaseClass

# Indirect usage of BaseClass through import
class MyClass(BaseClass):
  pass
​
ALIASED Usage
An aliased usage occurs when a symbol is used through an import with an alias.


Copy
from module import BaseClass as AliasedBase

# Aliased usage of BaseClass
class MyClass(AliasedBase):
  pass
​
Dependencies API
The dependencies API lets you find what symbols a given symbol depends on.

​
Basic Usage

Copy
# Get all direct dependencies
deps = my_class.dependencies  # Shorthand for dependencies(UsageType.DIRECT)

# Get dependencies of specific types
direct_deps = my_class.dependencies(UsageType.DIRECT)
chained_deps = my_class.dependencies(UsageType.CHAINED)
indirect_deps = my_class.dependencies(UsageType.INDIRECT)
​
Combining Usage Types
You can combine usage types using the bitwise OR operator:


Copy
# Get both direct and indirect dependencies
deps = my_class.dependencies(UsageType.DIRECT | UsageType.INDIRECT)

# Get all types of dependencies
deps = my_class.dependencies(
    UsageType.DIRECT | UsageType.CHAINED |
    UsageType.INDIRECT | UsageType.ALIASED
)
​
Common Patterns
Finding dead code (symbols with no usages):

Copy
# Check if a symbol is unused
def is_dead_code(symbol):
    return not symbol.usages

# Find all unused functions in a file
dead_functions = [f for f in file.functions if not f.usages]
See Deleting Dead Code to learn more about finding unused code.

Finding all imports that a symbol uses:

Copy
# Get all imports a class depends on
class_imports = [dep for dep in my_class.dependencies if isinstance(dep, Import)]

# Get all imports used by a function, including indirect ones
all_function_imports = [
    dep for dep in my_function.dependencies(UsageType.DIRECT | UsageType.INDIRECT)
    if isinstance(dep, Import)
]
​
Traversing the Dependency Graph
Sometimes you need to analyze not just direct dependencies, but the entire dependency graph up to a certain depth. The dependencies method allows you to traverse the dependency graph and collect all dependencies up to a specified depth level.

​
Basic Usage

Copy
# Get only direct dependencies
deps = symbol.dependencies(max_depth=1)

# Get deep dependencies (up to 5 levels)
deps = symbol.dependencies(max_depth=5)
The method returns a dictionary mapping each symbol to its list of direct dependencies. This makes it easy to analyze the dependency structure:


Copy
# Print the dependency tree
for sym, direct_deps in deps.items():
    print(f"{sym.name} depends on: {[d.name for d in direct_deps]}")
​
Example: Analyzing Class Inheritance
Here’s an example of using dependencies to analyze a class inheritance chain:


Copy
class A:
    def method_a(self): pass

class B(A):
    def method_b(self): 
        self.method_a()

class C(B):
    def method_c(self):
        self.method_b()

# Get the full inheritance chain
symbol = codebase.get_class("C")
deps = symbol.dependencies(
    max_depth=3
)

# Will show:
# C depends on: [B]
# B depends on: [A]
# A depends on: []
​
Handling Cyclic Dependencies
The method properly handles cyclic dependencies in the codebase:


Copy
class A:
    def method_a(self):
        return B()

class B:
    def method_b(self):
        return A()

# Get dependencies including cycles
symbol = codebase.get_class("A")
deps = symbol.dependencies()

# Will show:
# A depends on: [B]
# B depends on: [A]

Function Calls and Call Sites
Graph-sitter provides comprehensive APIs for working with function calls through several key classes:

FunctionCall - Represents a function invocation
Argument - Represents arguments passed to a function
Parameter - Represents parameters in a function definition
See Migrating APIs for relevant tutorials and applications.

​
Navigating Function Calls
Graph-sitter provides two main ways to navigate function calls:

From a function to its call sites using call_sites
From a function to the calls it makes (within it’s CodeBlock) using function_calls
Here’s how to analyze function usage patterns:


Copy
# Find the most called function
most_called = max(codebase.functions, key=lambda f: len(f.call_sites))
print(f"\nMost called function: {most_called.name}")
print(f"Called {len(most_called.call_sites)} times from:")
for call in most_called.call_sites:
    print(f"  - {call.parent_function.name} at line {call.start_point[0]}")

# Find function that makes the most calls
most_calls = max(codebase.functions, key=lambda f: len(f.function_calls))
print(f"\nFunction making most calls: {most_calls.name}")
print(f"Makes {len(most_calls.function_calls)} calls to:")
for call in most_calls.function_calls:
    print(f"  - {call.name}")

# Find functions with no callers (potential dead code)
unused = [f for f in codebase.functions if len(f.call_sites) == 0]
print(f"\nUnused functions:")
for func in unused:
    print(f"  - {func.name} in {func.filepath}")

# Find recursive functions
recursive = [f for f in codebase.functions
            if any(call.name == f.name for call in f.function_calls)]
print(f"\nRecursive functions:")
for func in recursive:
    print(f"  - {func.name}")
This navigation allows you to:

Find heavily used functions
Analyze call patterns
Map dependencies between functions
​
Arguments and Parameters
The Argument class represents values passed to a function, while Parameter represents the receiving variables in the function definition:

Consider the following code:


Copy
# Source code:
def process_data(input_data: str, debug: bool = False):
    pass

process_data("test", debug=True)
You can access and modify the arguments and parameters of the function call with APIs detailed below.

​
Finding Arguments
The primary APIs for finding arguments are:

FunctionCall.args
FunctionCall.get_arg_by_parameter_name(…)
FunctionCall.get_arg_by_index(…)

Copy
# Get the function call
call = file.function_calls[0]

# Working with arguments
for arg in call.args:
    print(f"Arg {arg.index}: {arg.value}")  # Access argument value
    print(f"Is named: {arg.is_named}")      # Check if it's a kwarg
    print(f"Name: {arg.name}")              # For kwargs, e.g. "debug"

    # Get corresponding parameter
    if param := arg.parameter:
        print(f"Parameter type: {param.type}")
        print(f"Is optional: {param.is_optional}")
        print(f"Has default: {param.default}")

# Finding specific arguments
debug_arg = call.get_arg_by_parameter_name("debug")
first_arg = call.get_arg_by_index(0)
​
Modifying Arguments
There are two ways to modify function call arguments:

Using FunctionCall.set_kwarg(…) to add or modify keyword arguments:

Copy
# Modifying keyword arguments
call.set_kwarg("debug", "False")  # Modifies existing kwarg
call.set_kwarg("new_param", "value", create_on_missing=True)  # Adds new kwarg
call.set_kwarg("input_data", "'new_value'", override_existing=True)  # Converts positional to kwarg
Using FuncionCall.args.append(…) to add new arguments:
FunctionCall.args is a Collection of Argument objects, so it supports .append(…), .insert(…) and other collection methods.


Copy
# Adding new arguments
call.args.append('cloud="aws"')  # Add a new keyword argument
call.args.append('"value"')      # Add a new positional argument

# Real-world example: Adding arguments to a decorator
@app.function(image=runner_image)
def my_func():
    pass

# Add cloud and region if not present
if "cloud=" not in decorator.call.source:
    decorator.call.args.append('cloud="aws"')
if "region=" not in decorator.call.source:
    decorator.call.args.append('region="us-east-1"')
The set_kwarg method provides intelligent argument manipulation:

If the argument exists and is positional, it converts it to a keyword argument
If the argument exists and is already a keyword, it updates its value (if override_existing=True)
If the argument doesn’t exist, it creates it (if create_on_missing=True)
When creating new arguments, it intelligently places them based on parameter order
Arguments and parameters support safe edit operations like so:


Copy
# Modifying arguments
debug_arg.edit("False")              # Change argument value
first_arg.add_keyword("input_data")  # Convert to named argument

# modifying parameters
param = codebase.get_function('process_data').get_parameter('debug')
param.rename('_debug') # updates all call-sites
param.set_type_annotation('bool')
​
Finding Function Definitions
Every FunctionCall can navigate to its definition through function_definition and function_definitions:


Copy
function_call = codebase.files[0].function_calls[0]
function_definition = function_call.function_definition
print(f"Definition found in: {function_definition.filepath}")
​
Finding Parent (Containing) Functions
FunctionCalls can access the function that invokes it via parent_function.

For example, given the following code:


Copy
# Source code:
def outer():
    def inner():
        helper()
    inner()
You can find the parent function of the helper call:


Copy
# Manipulation code:
# Find the helper() call
helper_call = file.get_function("outer").function_calls[1]

# Get containing function
parent = helper_call.parent_function
print(f"Call is inside: {parent.name}")  # 'inner'

# Get the full call hierarchy
outer = parent.parent_function
print(f"Which is inside: {outer.name}")  # 'outer'
​
Method Chaining
Graph-sitter enables working with chained method calls through predecessor and related properties:

For example, for the following database query:


Copy
# Source code:
query.select(Table)
    .where(id=1)
    .order_by("name")
    .limit(10)
You can access the chain of calls:


Copy
# Manipulation code:
# Get the `limit` call in the chain
limit_call = next(f for f in file.function.function_calls if f.name == "limit", None)

# Navigate backwards through the chain
order_by = limit_call.predecessor
where = order_by.predecessor
select = where.predecessor

# Get the full chain at once
chain = limit_call.call_chain  # [select, where, order_by, limit]

# Access the root object
base = limit_call.base  # Returns the 'query' object

# Check call relationships
print(f"After {order_by.name}: {limit_call.name}")
print(f"Before {where.name}: {select.name}")

Variable Assignments
Codegen’s enables manipulation of variable assignments via the following classes:

AssignmentStatement - A statement containing one or more assignments
Assignment - A single assignment within an AssignmentStatement
​
Simple Value Changes
Consider the following source code:


Copy
const userId = 123;
const [userName, userAge] = ["Eve", 25];
In Codegen, you can access assignments with the get_local_var_assignment method.

You can then manipulate the assignment with the set_value method.


Copy
id_assignment = file.code_block.get_local_var_assignment("userId")
id_assignment.set_value("456")

name_assignment = file.code_block.get_local_var_assignment("name")
name_assignment.rename("userName")
Assignments inherit both HasName and HasValue behaviors. See Inheritable Behaviors for more details.

​
Type Annotations
Similarly, you can set type annotations with the set_type_annotation method.

For example, consider the following source code:


Copy
let status;
const data = fetchData();
You can manipulate the assignments as follows:


Copy
status_assignment = file.code_block.get_local_var_assignment("status")
status_assignment.set_type_annotation("Status")
status_assignment.set_value("Status.ACTIVE")

data_assignment = file.code_block.get_local_var_assignment("data")
data_assignment.set_type_annotation("ResponseData<T>")

# Result:
let status: Status = Status.ACTIVE;
const data: ResponseData<T> = fetchData();
​
Tracking Usages and Dependencies
Like other symbols, Assignments support usages and dependencies.


Copy
assignment = file.code_block.get_local_var_assignment("userId")

# Get all usages of the assignment
usages = assignment.usages

# Get all dependencies of the assignment
dependencies = assignment.dependencies

Local Variables
This document explains how to work with local variables in Codegen.

​
Overview
Through the CodeBlock class, Graph-sitter exposes APIs for analyzing and manipulating local variables within code blocks.

local_var_assignments: find all Assignments in this scope
get_local_var_assignment(…): get specific Assignments by name
rename_local_variable(…): rename variables safely across the current scope
​
Basic Usage
Every code block (function body, loop body, etc.) provides access to its local variables:


Copy
# Get all local variables in a function
function = codebase.get_function("process_data")
local_vars = function.code_block.local_var_assignments
for var in local_vars:
    print(var.name)

# Find a specific variable
config_var = function.code_block.get_local_var_assignment("config")
config_var.rename("settings")  # Updates all references safely

# Rename a variable used in this scope (but not necessarily declared here)
function.rename_local_variable("foo", "bar")
​
Fuzzy Matching
Graph-sitter supports fuzzy matching when searching for local variables. This allows you to find variables whose names contain a substring, rather than requiring exact matches:


Copy
# Get all local variables containing "config"
function = codebase.get_function("process_data")

# Exact match - only finds variables named exactly "config"
exact_matches = function.code_block.get_local_var_assignments("config")
# Returns: config = {...}

# Fuzzy match - finds any variable containing "config"
fuzzy_matches = function.code_block.get_local_var_assignments("config", fuzzy_match=True)
# Returns: config = {...}, app_config = {...}, config_settings = {...}

# Fuzzy matching also works for variable usages
usages = function.code_block.get_variable_usages("config", fuzzy_match=True)

# And for renaming variables
function.code_block.rename_variable_usages("config", "settings", fuzzy_match=True)
# Renames: config -> settings, app_config -> app_settings, config_settings -> settings_settin

Comments and Docstrings
Graph-sitter enables reading, modifying, and manipulating comments and docstrings while preserving proper formatting.

This guide describes proper usage of the following classes:

Comment - Represents a single comment.
CommentGroup - Represents a group of comments.
​
Accessing with Comments
Comments can be accessed through any symbol or directly from code blocks. Each comment is represented by a Comment object that provides access to both the raw source and parsed text:


Copy
# Find all comments in a file
file = codebase.get_file("my_file.py")
for comment in file.code_block.comments:
    print(comment.text)

# Access comments associated with a symbol
symbol = file.get_symbol("my_function")
if symbol.comment:
    print(symbol.comment.text)  # Comment text without delimiters
    print(symbol.comment.source)  # Full comment including delimiters

# Access inline comments
if symbol.inline_comment:
    print(symbol.inline_comment.text)

# Accessing all comments in a function
for comment in symbol.code_block.comments:
    print(comment.text)
​
Editing Comments
Comments can be modified using the edit_text() method, which handles formatting and delimiters automatically:


Copy
# Edit a regular comment
symbol.comment.edit_text("Updated comment text")

# Edit an inline comment
symbol.set_inline_comment("New inline comment")
​
Comment Groups
Multiple consecutive comments are automatically grouped into a CommentGroup, which can be edited as a single unit:


Copy
# Original comments:
# First line
# Second line
# Third line

comment_group = symbol.comment
print(comment_group.text)  # "First line\nSecond line\nThird line"

# Edit the entire group at once
comment_group.edit_text("New first line\nNew second line")
​
Working with Docstrings
Docstrings are special comments that document functions, classes, and modules. Graph-sitter provides similar APIs for working with docstrings:


Copy
function = file.get_symbol("my_function")
if function.docstring:
    print(function.docstring.text)  # Docstring content
    print(function.docstring.source)  # Full docstring with delimiters
​
Adding Docstrings
You can add docstrings to any symbol that supports them:


Copy
# Add a single-line docstring
function.set_docstring("A brief description")

# Add a multi-line docstring
function.set_docstring("""
    A longer description that
    spans multiple lines.

    Args:
        param1: Description of first parameter
""")
​
Language-Specific Formatting
Graph-sitter automatically handles language-specific docstring formatting:


Copy
# Python: Uses triple quotes
def my_function():
    """Docstring is formatted with triple quotes."""
    pass

Copy
// TypeScript: Uses JSDoc style
function myFunction() {
  /** Docstring is formatted as JSDoc */
}
​
Editing Docstrings
Like comments, docstrings can be modified while preserving formatting:


Copy
# Edit a docstring
function.docstring.edit_text("Updated documentation")

# Edit a multi-line docstring
function.docstring.edit_text("""
    Updated multi-line documentation
    that preserves indentation and formatting.
""")
​
Comment Operations
Graph-sitter provides utilities for working with comments at scale. For example, you can update or remove specific types of comments across your codebase:


Copy
# Example: Remove eslint disable comments for a specific rule
for file in codebase.files:
    for comment in file.code_block.comments:
        if "eslint-disable" in comment.source:
            # Check if comment disables specific rule
            if "@typescript-eslint/no-explicit-any" in comment.text:
                comment.remove()
When editing multi-line comments or docstrings, Graph-sitter automatically handles indentation and maintains the existing comment style.

​
Special APIs and AI Integration
​
Google Style Docstrings
Graph-sitter supports Google-style docstrings and can handle their specific formatting, using the CommentGroup.to_google_docstring(…) method.


Copy
# Edit while preserving Google style
symbol_a = file.get_symbol("SymbolA")
func_b = symbol_a.get_method("funcB")
func_b.docstring.to_google_docstring(func_b)
​
Using AI for Documentation
Graph-sitter integrates with LLMs to help generate and improve documentation. You can use the Codebase.ai(…) method to:

Generate comprehensive docstrings
Update existing documentation
Convert between documentation styles
Add parameter descriptions

Copy
# Generate a docstring using AI
function = codebase.get_function("my_function")

new_docstring = codebase.ai(
    "Generate a comprehensive docstring in Google style",
    target=function
    context={
        # provide additional context to the LLM
        'usages': function.usages,
        'dependencies': function.dependencies
    }
)
function.set_docstring(new_docstring)
Learn more about AI documentation capabilities in our Documentation Guide and LLM Integration Guide.

​
Documentation Coverage
You can analyze and improve documentation coverage across your codebase:


Copy
# Count documented vs undocumented functions
total = 0
documented = 0
for function in codebase.functions:
    total += 1
    if function.docstring:
        documented += 1

coverage = (documented / total * 100) if total > 0 else 0
print(f"Documentation coverage: {coverage:.1f}%")

External Modules
Graph-sitter provides a way to handle imports from external packages and modules through the ExternalModule class.


Copy
# Python examples
import datetime
from requests import get

# TypeScript/JavaScript examples
import React from 'react'
import { useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import axios from 'axios'
​
What are External Modules?
When writing code, you often import from packages that aren’t part of your project - like datetime and requests in Python, or react and axios in TypeScript. In Codegen, these are represented as ExternalModule instances.


Copy
for imp in codebase.imports:
    if isinstance(imp.symbol, ExternalModule):
        print(f"Importing from external package: {imp.resolved_symbol.source}")
External modules are read-only - you can analyze them but can’t modify their implementation. This makes sense since they live in your project’s dependencies!

​
Working with External Modules
The most common use case is handling external modules differently from your project’s code:

​
Identifying Function Calls as External Modules
For FunctionCall instances, you can check if the function definition is an ExternalModule via the FunctionCall.function_definition property:


Copy
for fcall in file.function_calls:
    definition = fcall.function_definition
    if isinstance(definition, ExternalModule):
        # Skip external functions
        print(f'External function: {definition.name}')
    else:
        # Process local functions...
        print(f'Local function: {definition.name}')
​
Import Resolution
Similarly, when working with imports, you can determine if they resolve to external modules by checking the Import.resolved_symbol property:


Copy
for imp in file.imports:
    resolved = imp.resolved_symbol
    if isinstance(resolved, ExternalModule):
        print(f"Import from external package: from {imp.module} import {imp.name}")
Use isinstance(symbol, ExternalModule) to reliably identify external modules. This works better than checking names or paths since it handles all edge cases.

​
Properties and Methods
External modules provide several useful properties:


Copy
# Get the module name
module_name = external_module.name  # e.g. "datetime" or "useState"

# Check if it's from node_modules (TypeScript/JavaScript)
if external_module.filepath == "":
    print("This is an external package from node_modules")
​
Common Patterns
Here are some typical ways you might work with external modules:

​
Skip External Processing:
When modifying function calls or imports, skip external modules since they can’t be changed:


Copy
# Example from a codemod that adds type hints
def add_type_hints(function):
    if isinstance(function.definition, ExternalModule):
        return  # Can't add type hints to external modules like React.FC
    # Add type hints to local functions...
​
Analyze Dependencies
Track which external packages your code uses:


Copy
# Find all external package dependencies
external_deps = set()
for imp in codebase.imports:
    if isinstance(imp.resolved_symbol, ExternalModule):
        external_deps.add(imp.resolved_symbol.source)
        # Will find things like 'react', 'lodash', 'datetime', etc.

Working with Type Annotations
This guide covers the core APIs and patterns for working with type annotations in Codegen.

​
Type Resolution
Graph-sitter builds a complete dependency graph of your codebase, connecting functions, classes, imports, and their relationships. This enables powerful type resolution capabilities:


Copy
from graph_sitter import Codebase

# Initialize codebase with dependency graph
codebase = Codebase("./")

# Get a function with a type annotation
function = codebase.get_file("path/to/file.py").get_function("my_func")

# Resolve its return type to actual symbols
return_type = function.return_type
resolved_symbols = return_type.resolved_types  # Returns the actual Symbol objects

# For generic types, you can resolve parameters
if hasattr(return_type, "parameters"):
    for param in return_type.parameters:
        resolved_param = param.resolved_types  # Get the actual type parameter symbols

# For assignments, resolve their type
assignment = codebase.get_file("path/to/file.py").get_assignment("my_var")
resolved_type = assignment.type.resolved_types
Type resolution follows imports and handles complex cases like type aliases, forward references, and generic type parameters.

​
Core Interfaces
Type annotations in Graph-sitter are built on two key interfaces:

Typeable - The base interface for any node that can have a type annotation (parameters, variables, functions, etc). Provides .type and .is_typed.
Type - The base class for all type annotations. Provides type resolution and dependency tracking.
Any node that inherits from Typeable will have a .type property that returns a Type object, which can be used to inspect and modify type annotations.

Learn more about inheritable behaviors like Typeable here
​
Core Type APIs
Type annotations can be accessed and modified through several key APIs:

​
Function Types
The main APIs for function types are Function.return_type and Function.set_return_type:


Copy
# Get return type
return_type = function.return_type  # -> TypeAnnotation
print(return_type.source)  # "List[str]"
print(return_type.is_typed)  # True/False

# Set return type
function.set_return_type("List[str]")
function.set_return_type(None)  # Removes type annotation
​
Parameter Types
Parameters use Parameter.type and Parameter.set_type_annotation:


Copy
for param in function.parameters:
    # Get parameter type
    param_type = param.type  # -> TypeAnnotation
    print(param_type.source)  # "int"
    print(param_type.is_typed)  # True/False

    # Set parameter type
    param.set_type("int")
    param.set_type(None)  # Removes type annotation
​
Variable Types
Variables and attributes use Assignment.type and Assignment.set_type_annotation. This applies to:

Global variables
Local variables
Class attributes (via Class.attributes)

Copy
# For global/local assignments
assignment = file.get_assignment("my_var")
var_type = assignment.type  # -> TypeAnnotation
print(var_type.source)  # "str"

# Set variable type
assignment.set_type("str")
assignment.set_type(None)  # Removes type annotation

# For class attributes
class_def = file.get_class("MyClass")
for attr in class_def.attributes:
    # Each attribute has an assignment property
    attr_type = attr.assignment.type  # -> TypeAnnotation
    print(f"{attr.name}: {attr_type.source}")  # e.g. "x: int"
    
    # Set attribute type
    attr.assignment.set_type("int")

# You can also access attributes directly by index
first_attr = class_def.attributes[0]
first_attr.assignment.set_type("str")
​
Working with Complex Types
​
Union Types
Union types (UnionType) can be manipulated as collections:


Copy
# Get union type
union_type = function.return_type  # -> A | B 
print(union_type.symbols)  # ["A", "B"]

# Add/remove options
union_type.append("float")
union_type.remove("None")

# Check contents
if "str" in union_type.options:
    print("String is a possible type")
Learn more about working with collections here
​
Generic Types
Generic types (GenericType) expose their parameters as collection of Parameters:


Copy
# Get generic type
generic_type = function.return_type  # -> GenericType
print(generic_type.base)  # "List"
print(generic_type.parameters)  # ["str"]

# Modify parameters
generic_type.parameters.append("int")
generic_type.parameters[0] = "float"

# Create new generic
function.set_return_type("List[str]")
Learn more about working with collections here
​
Type Resolution
Type resolution uses Type.resolved_value to get the actual symbols that a type refers to:


Copy
# Get the actual symbols for a type
type_annotation = function.return_type  # -> Type
resolved_types = type_annotation.resolved_value  # Returns an Expression, likely a Symbol or collection of Symbols

# For generic types, resolve each parameter
if hasattr(type_annotation, "parameters"):
    for param in type_annotation.parameters:
        param_types = param.resolved_value # Get symbols for each parameter

# For union types, resolve each option
if hasattr(type_annotation, "options"):
    for option in type_annotation.options:
        option_types = option.resolved_value # Get symbols for each union option

Moving Symbols
Graph-sitter provides fast, configurable and safe APIs for moving symbols (functions, classes, variables) between files while automatically handling imports and dependencies.

The key API is Symbol.move_to_file(…).

​
Basic Symbol Movement
Simply call Symbol.move_to_file(…) to move a symbol to a new file.


Copy
# Manipulation code:
file1 = codebase.get_file("file1.py")
file2 = codebase.get_file("file2.py")

helper_func = file1.get_symbol("helper")

# Ensure the destination file exists
if not file2.exists():
    file2 = codebase.create_file('file2.py')

# Move the symbol
helper_func.move_to_file(file2)
By default, this will move any dependencies, including imports, to the new file.

​
Moving Strategies
The Symbol.move_to_file(…) method accepts a strategy parameter, which can be used to control how imports are updated.

Your options are:

"update_all_imports": Updates all import statements across the codebase (default)
"add_back_edge": Adds import and re-export in the original file
"add_back_edge" is useful when moving a symbol that is depended on by other symbols in the original file, and will result in smaller diffs.

"add_back_edge" will result in circular dependencies if the symbol has non-import dependencies in it’s original file.

​
Moving Symbols in Bulk
Make sure to call Codebase.commit(…) after moving symbols in bulk for performant symbol movement.


Copy
# Move all functions with a specific prefix
for file in codebase.files:
    for function in file.functions:
        if function.name.startswith("pylsp_"):
            function.move_to_file(
                shared_file,
                include_dependencies=True,
                strategy="update_all_imports"
            )

# Commit the changes once, at the end
codebase.commit()

Collections
Graph-sitter enables traversing and manipulating collections through the List and Dict classes.

These APIs work consistently across Python and TypeScript while preserving formatting and structure.

​
Core Concepts
The List and Dict classes provide a consistent interface for working with ordered sequences of elements. Key features include:

Standard sequence operations (indexing, length, iteration)
Automatic formatting preservation
Safe modification operations
Language-agnostic behavior
Comment and whitespace preservation
Collections handle:

Proper indentation
Delimiters (commas, newlines)
Multi-line formatting
Leading/trailing whitespace
Nested structures
​
List Operations
Lists in both Python and TypeScript can be manipulated using the same APIs:


Copy
# Basic operations
items_list = file.get_symbol("items").value  # Get list value
first = items_list[0]        # Access elements
length = len(items_list)     # Get length
items_list[0] = "new"       # Modify element
items_list.append("d")      # Add to end
items_list.insert(1, "x")   # Insert at position
del items_list[1]           # Remove element

# Iteration
for item in items_list:
    print(item.source)

# Bulk operations
items_list.clear()          # Remove all elements
​
Single vs Multi-line Lists
Collections automatically preserve formatting:


Copy
# Source code:
items = [a, b, c]
config = [
    "debug",
    "verbose",
    "trace",
]

# Manipulation code:
items_list = file.get_symbol("items").value
items_list.append("d")    # Adds new element

config_list = file.get_symbol("config").value
config_list.append("info")  # Adds with formatting

# Result:
items = [a, b, c, d]
config = [
    "debug",
    "verbose",
    "trace",
    "info",
]
​
Dictionary Operations
Dictionaries provide a similar consistent interface:


Copy
# Basic operations
settings = file.get_symbol("settings").value  # Get dict value
value = settings["key"]     # Get value
settings["key"] = "value"   # Set value
del settings["key"]         # Remove key
has_key = "key" in settings # Check existence

# Iteration
for key in settings:
    print(f"{key}: {settings[key]}")

# Bulk operations
settings.clear()           # Remove all entries

Traversing the Call Graph
Graph-sitter provides powerful capabilities for analyzing and visualizing function call relationships in your codebase. This guide will show you how to traverse the call graph and create visual representations of function call paths.

​
Understanding Call Graph Traversal
At the heart of call graph traversal is the .function_calls property, which returns information about all function calls made within a function:


Copy
def example_function():
    result = helper_function()
    process_data()
    return result

# Get all calls made by example_function
successors = example_function.function_calls
for successor in successors:
    print(f"Call: {successor.source}")  # The actual function call
    print(f"Called: {successor.function_definition.name}")  # The function being called
​
Building a Call Graph
Here’s how to build a directed graph of function calls using NetworkX:


Copy
import networkx as nx
from codegen.sdk.core.interfaces.callable import FunctionCallDefinition
from codegen.sdk.core.function import Function
from codegen.sdk.core.external_module import ExternalModule

def create_call_graph(start_func, end_func, max_depth=5):
    G = nx.DiGraph()

    def traverse_calls(parent_func, current_depth):
        if current_depth > max_depth:
            return

        # Determine source node
        if isinstance(parent_func, Function):
            src_call = src_func = parent_func
        else:
            src_func = parent_func.function_definition
            src_call = parent_func

        # Skip external modules
        if isinstance(src_func, ExternalModule):
            return

        # Traverse all function calls
        for call in src_func.function_calls:
            func = call.function_definition

            # Skip recursive calls
            if func.name == src_func.name:
                continue

            # Add nodes and edges
            G.add_node(call)
            G.add_edge(src_call, call)

            # Check if we reached the target
            if func == end_func:
                G.add_edge(call, end_func)
                return

            # Continue traversal
            traverse_calls(call, current_depth + 1)

    # Initialize graph
    G.add_node(start_func, color="blue")  # Start node
    G.add_node(end_func, color="red")     # End node

    # Start traversal
    traverse_calls(start_func, 1)
    return G

# Usage example
start = codebase.get_function("create_skill")
end = codebase.get_function("auto_define_skill_description")
graph = create_call_graph(start, end)
​
Filtering and Visualization
You can filter the graph to show only relevant paths and visualize the results:


Copy
# Find all paths between start and end
all_paths = nx.all_simple_paths(graph, source=start, target=end)

# Create subgraph of only the nodes in these paths
nodes_in_paths = set()
for path in all_paths:
    nodes_in_paths.update(path)
filtered_graph = graph.subgraph(nodes_in_paths)

# Visualize the graph
codebase.visualize(filtered_graph)
​
Advanced Usage
​
Example: Finding Dead Code
You can use call graph analysis to find unused functions:


Copy
def find_dead_code(codebase):
    dead_functions = []
    for function in codebase.functions:
        if not any(function.function_calls):
            # No other functions call this one
            dead_functions.append(function)
    return dead_functions
​
Example: Analyzing Call Chains
Find the longest call chain in your codebase:


Copy
def get_max_call_chain(function):
    G = nx.DiGraph()

    def build_graph(func, depth=0):
        if depth > 10:  # Prevent infinite recursion
            return
        for call in func.function_calls:
            called_func = call.function_definition
            G.add_edge(func, called_func)
            build_graph(called_func, depth + 1)

    build_graph(function)
    return nx.dag_longest_path(G)

React and JSX
GraphSitter exposes several React and JSX-specific APIs for working with modern React codebases.

Key APIs include:

Function.is_jsx - Check if a function contains JSX elements
Class.jsx_elements - Get all JSX elements in a class
Function.jsx_elements - Get all JSX elements in a function
JSXElement - Manipulate JSX elements
JSXProp - Manipulate JSX props
See React Modernization for tutorials and applications of the concepts described here

​
Detecting React Components with is_jsx
Graph-sitter exposes a is_jsx property on both classes and functions, which can be used to check if a symbol is a React component.


Copy
# Check if a function is a React component
function = file.get_function("MyComponent")
is_component = function.is_jsx  # True for React components

# Check if a class is a React component
class_def = file.get_class("MyClassComponent")
is_component = class_def.is_jsx  # True for React class components
​
Working with JSX Elements
Given a React component, you can access its JSX elements using the jsx_elements property.

You can manipulate these elements by using the JSXElement and JSXProp APIs.


Copy
# Get all JSX elements in a component
for element in component.jsx_elements:
    # Access element name
    if element.name == "Button":
        # Wrap element in a div
        element.wrap("<div className='wrapper'>", "</div>")

    # Get specific prop
    specific_prop = element.get_prop("className")

    # Iterate over all props
    for prop in element.props:
        if prop.name == "className":
            # Set prop value
            prop.set_value('"my-classname"')

    # Modify element
    element.set_name("NewComponent")
    element.add_prop("newProp", "{value}")

    # Get child JSX elements
    child_elements = element.jsx_elements

    # Wrap element in a JSX expression (preserves whitespace)
    element.wrap("<div className='wrapper'>", "</div>")
​
Common React Operations
See React Modernization for more
​
Refactoring Components into Separate Files
Split React components into individual files:


Copy
# Find (named) React components
react_components = [
    func for func in codebase.functions
    if func.is_jsx and func.name is not None
]

# Filter out those that are not the default export
non_default_components = [
    comp for comp in react_components
    if not comp.export or not comp.export.is_default_export()
]

# Move these non-default components to new files
for component in react_components:
    if component != default_component:
        # Create new file
        new_file_path = '/'.join(component.filepath.split('/')[:-1]) + f"{component.name}.tsx"
        new_file = codebase.create_file(new_file_path)

        # Move component and update imports
        component.move_to_file(new_file, strategy="add_back_edge")
See Moving Symbols for more details on moving symbols between files.

​
Updating Component Names and Props
Replace components throughout the codebase with prop updates:


Copy
# Find target component
new_component = codebase.get_symbol("NewComponent")

for function in codebase.functions:
    if function.is_jsx:
        # Update JSX elements
        for element in function.jsx_elements:
            if element.name == "OldComponent":
                # Update name
                element.set_name("NewComponent")

                # Edit props
                needs_clsx = not file.has_import("clsx")
                for prop in element.props:
                    if prop.name == "className":
                        prop.set_value('clsx("new-classname")')
                        needs_clsx = True
                    elif prop.name == "onClick":
                        prop.set_name('handleClick')

                # Add import if needed
                if needs_clsx:
                    file.add_import_from_import_source("import clsx from 'clsx'")

                # Add import if needed
                if not file.has_import("NewComponent"):
                    file.add_import(new_component)


Codebase Visualization
Graph-sitter provides the ability to create interactive graph visualizations via the codebase.visualize(…) method.

These visualizations have a number of applications, including:

Understanding codebase structure
Monitoring critical code paths
Analyzing dependencies
Understanding inheritance hierarchies
This guide provides a basic overview of graph creation and customization. Like the one below which displays the call_graph for the modal/client.py module.


Graph-sitter visualizations are powered by NetworkX and rendered using d3.

​
Basic Usage
The Codebase.visualize method operates on a NetworkX DiGraph.


Copy
import networkx as nx

# Basic visualization
G = nx.grid_2d_graph(5, 5)
# Or start with an empty graph
# G = nx.DiGraph()
codebase.visualize(G)
It is up to the developer to add nodes and edges to the graph.

​
Adding Nodes and Edges
When adding nodes to your graph, you can either add the symbol directly or just its name:


Copy
import networkx as nx
G = nx.DiGraph()
function = codebase.get_function("my_function")

# Add the function object directly - enables source code preview
graph.add_node(function)  # Will show function's source code on click

# Add just the name - no extra features
graph.add_node(function.name)  # Will only show the name
Adding symbols to the graph directly (as opposed to adding by name) enables automatic type information, code preview on hover, and more.

​
Common Visualization Types
​
Call Graphs
Visualize how functions call each other and trace execution paths:


Copy
def create_call_graph(entry_point: Function):
    graph = nx.DiGraph()

    def add_calls(func):
        for call in func.call_sites:
            called_func = call.resolved_symbol
            if called_func:
                # Add function objects for rich previews
                graph.add_node(func)
                graph.add_node(called_func)
                graph.add_edge(func, called_func)
                add_calls(called_func)

    add_calls(entry_point)
    return graph

# Visualize API endpoint call graph
endpoint = codebase.get_function("handle_request")
call_graph = create_call_graph(endpoint)
codebase.visualize(call_graph, root=endpoint)
Learn more about traversing the call graph here.

​
React Component Trees
Visualize the hierarchy of React components:


Copy
def create_component_tree(root_component: Class):
    graph = nx.DiGraph()

    def add_children(component):
        for usage in component.usages:
            if isinstance(usage.parent, Class) and "Component" in usage.parent.bases:
                graph.add_edge(component.name, usage.parent.name)
                add_children(usage.parent)

    add_children(root_component)
    return graph

# Visualize component hierarchy
app = codebase.get_class("App")
component_tree = create_component_tree(app)
codebase.visualize(component_tree, root=app)
​
Inheritance Graphs
Visualize class inheritance relationships:


Copy
import networkx as nx

G = nx.DiGraph()
base = codebase.get_class("BaseModel")

def add_subclasses(cls):
    for subclass in cls.subclasses:
        G.add_edge(cls, subclass)
        add_subclasses(subclass)

add_subclasses(base)

codebase.visualize(G, root=base)
​
Module Dependencies
Visualize dependencies between modules:


Copy
def create_module_graph(start_file: File):
    G = nx.DiGraph()

    def add_imports(file):
        for imp in file.imports:
            if imp.resolved_symbol and imp.resolved_symbol.file:
                graph.add_edge(file, imp.resolved_symbol.file)
                add_imports(imp.resolved_symbol.file)

    add_imports(start_file)
    return graph

# Visualize module dependencies
main = codebase.get_file("main.py")
module_graph = create_module_graph(main)
codebase.visualize(module_graph, root=main)
​
Function Modularity
Visualize function groupings by modularity:


Copy
def create_modularity_graph(functions: list[Function]):
    graph = nx.Graph()

    # Group functions by shared dependencies
    for func in functions:
        for dep in func.dependencies:
            if isinstance(dep, Function):
                weight = len(set(func.dependencies) & set(dep.dependencies))
                if weight > 0:
                    graph.add_edge(func.name, dep.name, weight=weight)

    return graph

# Visualize function modularity
funcs = codebase.functions
modularity_graph = create_modularity_graph(funcs)
codebase.visualize(modularity_graph)
​
Customizing Visualizations
You can customize your visualizations using NetworkX’s attributes while still preserving the smart node features:


Copy
def create_custom_graph(codebase):
    graph = nx.DiGraph()

    # Add nodes with custom attributes while preserving source preview
    for func in codebase.functions:
        graph.add_node(func,
            color='red' if func.is_public else 'blue',
            shape='box' if func.is_async else 'oval'
        )

    # Add edges between actual function objects
    for func in codebase.functions:
        for call in func.call_sites:
            if call.resolved_symbol:
                graph.add_edge(func, call.resolved_symbol,
                    style='dashed' if call.is_conditional else 'solid',
                    weight=call.count
                )

    return graph
​
Best Practices
Use Symbol Objects for Rich Features


Copy
# Better: Add symbol objects for rich previews
# This will include source code previews, syntax highlighting, type information, etc.
for func in api_funcs:
    graph.add_node(func)

# Basic: Just names, no extra features
for func in api_funcs:
    graph.add_node(func.name)
Focus on Relevant Subgraphs


Copy
# Better: Visualize specific subsystem
api_funcs = [f for f in codebase.functions if "api" in f.filepath]
api_graph = create_call_graph(api_funcs)
codebase.visualize(api_graph)

# Avoid: Visualizing entire codebase
full_graph = create_call_graph(codebase.functions)  # Too complex
Use Meaningful Layouts


Copy
# Group related nodes together
graph.add_node(controller_class, cluster="api")
graph.add_node(service_class, cluster="db")
Add Visual Hints


Copy
# Color code by type while preserving rich previews
for node in codebase.functions:
    if "Controller" in node.name:
        graph.add_node(node, color="red")
    elif "Service" in node.name:
        graph.add_node(node, color="blue")
​
Limitations
Large graphs may become difficult to read
Complex relationships might need multiple views
Some graph layouts may take time to compute
Preview features only work when adding symbol objects directly

lagging Symbols
Learn how to use symbol flags for debugging, tracking changes, and marking code for review

​
Flagging Symbols
Symbol flags are a powerful feature in Graph-sitter that allow you to mark and track specific code elements during development, debugging, or code review processes. Flags can be used to visually highlight code in the editor and can also integrate with various messaging systems.

​
Basic Usage
The simplest way to flag a symbol is to call the flag() method on any symbol:


Copy
# Flag a function
function.flag(message="This function needs optimization")

# Flag a class
my_class.flag(message="Consider breaking this into smaller classes")

# Flag a variable
variable.flag(message="Type hints needed here")
When you flag a symbol, two things happen:

A visual flag emoji (🚩) is added as an inline comment
A CodeFlag object is created to track the flag in the system
​
Language-Specific Behavior
The flag system adapts automatically to the programming language being used:


Copy
# Python
# Results in: def my_function():  # 🚩 Review needed
python_function.flag(message="Review needed")

# TypeScript
# Results in: function myFunction() {  // 🚩 Review needed
typescript_function.flag(message="Review needed")
​
Example: Code Analysis
Here’s an example of using flags during code analysis:


Copy
def analyze_codebase(codebase):
    for function in codebase.functions:            
        # Check documentation
        if not function.docstring:
            function.flag(
                message="Missing docstring",
            )
            
        # Check error handling
        if function.is_async and not function.has_try_catch:
            function.flag(
                message="Async function missing error handling",
            )
This feature is particularly useful when building, and iterating on the symbols that you are trying to modify.

Calling Out to LLMs
Graph-sitter natively integrates with LLMs via the codebase.ai(…) method, which lets you use large language models (LLMs) to help generate, modify, and analyze code.

​
Configuration
Before using AI capabilities, you need to provide an OpenAI API key via codebase.set_ai_key(…):


Copy
# Set your OpenAI API key
codebase.set_ai_key("your-openai-api-key")
​
Calling Codebase.ai(…)
The Codebase.ai(…) method takes three key arguments:


Copy
result = codebase.ai(
    prompt="Your instruction to the AI",
    target=symbol_to_modify,  # Optional: The code being operated on
    context=additional_info   # Optional: Extra context from static analysis
)
prompt: Clear instruction for what you want the AI to do
target: The symbol (function, class, etc.) being operated on - its source code will be provided to the AI
context: Additional information you want to provide to the AI, which you can gather using GraphSitter’s analysis tools
Graph-sitter does not automatically provide any context to the LLM by default. It does not “understand” your codebase, only the context you provide.

The context parameter can include:

A single symbol (its source code will be provided)
A list of related symbols
A dictionary mapping descriptions to symbols/values
Nested combinations of the above
​
How Context Works
The AI doesn’t automatically know about your codebase. Instead, you can provide relevant context by:

Using GraphSitter’s static analysis to gather information:

Copy
function = codebase.get_function("process_data")
context = {
    "call_sites": function.call_sites,      # Where the function is called
    "dependencies": function.dependencies,   # What the function depends on
    "parent": function.parent,              # Class/module containing the function
    "docstring": function.docstring,        # Existing documentation
}
Passing this information to the AI:

Copy
result = codebase.ai(
    "Improve this function's implementation",
    target=function,
    context=context  # AI will see the gathered information
)
​
Common Use Cases
​
Code Generation
Generate new code or refactor existing code:


Copy
# Break up a large function
function = codebase.get_function("large_function")
new_code = codebase.ai(
    "Break this function into smaller, more focused functions",
    target=function
)
function.edit(new_code)

# Generate a test
my_function = codebase.get_function("my_function")
test_code = codebase.ai(
    f"Write a test for the function {my_function.name}",
    target=my_function
)
my_function.insert_after(test_code)
​
Documentation
Generate and format documentation:


Copy
# Generate docstrings for a class
class_def = codebase.get_class("MyClass")
for method in class_def.methods:
    docstring = codebase.ai(
        "Generate a docstring describing this method",
        target=method,
        context={
            "class": class_def,
            "style": "Google docstring format"
        }
    )
    method.set_docstring(docstring)
​
Code Analysis and Improvement
Use AI to analyze and improve code:


Copy
# Improve function names
for function in codebase.functions:
    if codebase.ai(
        "Does this function name clearly describe its purpose? Answer yes/no",
        target=function
    ).lower() == "no":
        new_name = codebase.ai(
            "Suggest a better name for this function",
            target=function,
            context={"call_sites": function.call_sites}
        )
        function.rename(new_name)
​
Contextual Modifications
Make changes with full context awareness:


Copy
# Refactor a class method
method = codebase.get_class("MyClass").get_method("target_method")
new_impl = codebase.ai(
    "Refactor this method to be more efficient",
    target=method,
    context={
        "parent_class": method.parent,
        "call_sites": method.call_sites,
        "dependencies": method.dependencies
    }
)
method.edit(new_impl)
​
Best Practices
Provide Relevant Context


Copy
# Good: Providing specific, relevant context
summary = codebase.ai(
    "Generate a summary of this method's purpose",
    target=method,
    context={
        "class": method.parent,              # Class containing the method
        "usages": list(method.usages),       # How the method is used
        "dependencies": method.dependencies,  # What the method depends on
        "style": "concise"
    }
)

# Bad: Missing context that could help the AI
summary = codebase.ai(
    "Generate a summary",
    target=method  # AI only sees the method's code
)
Gather Comprehensive Context


Copy
# Gather relevant information before AI call
def get_method_context(method):
    return {
        "class": method.parent,
        "call_sites": list(method.call_sites),
        "dependencies": list(method.dependencies),
        "related_methods": [m for m in method.parent.methods
                          if m.name != method.name]
    }

# Use gathered context in AI call
new_impl = codebase.ai(
    "Refactor this method to be more efficient",
    target=method,
    context=get_method_context(method)
)
Handle AI Limits


Copy
# Set custom AI request limits for large operations
codebase.set_session_options(max_ai_requests=200)
Review Generated Code


Copy
# Generate and review before applying
new_code = codebase.ai(
    "Optimize this function",
    target=function
)
print("Review generated code:")
print(new_code)
if input("Apply changes? (y/n): ").lower() == 'y':
    function.edit(new_code)
​
Limitations and Safety
The AI doesn’t automatically know about your codebase - you must provide relevant context
AI-generated code should always be reviewed
Default limit of 150 AI requests per codemod execution
Use set_session_options(…) to adjust limits:

Copy
codebase.set_session_options(max_ai_requests=200)

Semantic Code Search
Graph-sitter provides semantic code search capabilities using embeddings. This allows you to search codebases using natural language queries and find semantically related code, even when the exact terms aren’t present.

This is under active development. Interested in an application? Reach out to the team!
​
Basic Usage
Here’s how to create and use a semantic code search index:


Copy
# Parse a codebase
codebase = Codebase.from_repo('fastapi/fastapi', language='python')

# Create index
index = FileIndex(codebase)
index.create() # computes per-file embeddings

# Save index to .pkl
index.save('index.pkl')

# Load index into memory
index.load('index.pkl')

# Update index after changes
codebase.files[0].edit('# 🌈 Replacing File Content 🌈')
codebase.commit()
index.update() # re-computes 1 embedding
​
Searching Code
Once you have an index, you can perform semantic searches:


Copy
# Search with natural language
results = index.similarity_search(
    "How does FastAPI handle dependency injection?",
    k=5  # number of results
)

# Print results
for file, score in results:
    print(f"\nScore: {score:.3f} | File: {file.filepath}")
    print(f"Preview: {file.content[:200]}...")
The FileIndex returns tuples of (File, score)
The search uses cosine similarity between embeddings to find the most semantically related files, regardless of exact keyword matches.

​
Available Indices
Graph-sitter provides two types of semantic indices:

​
FileIndex
The FileIndex operates at the file level:

Indexes entire files, splitting large files into chunks
Best for finding relevant files or modules
Simpler and faster to create/update

Copy
from graph_sitter.extensions.index.file_index import FileIndex

index = FileIndex(codebase)
index.create()
​
SymbolIndex (Experimental)
The SymbolIndex operates at the symbol level:

Indexes individual functions, classes, and methods
Better for finding specific code elements
More granular search results

Copy
from graph_sitter.extensions.index.symbol_index import SymbolIndex

index = SymbolIndex(codebase)
index.create()
​
How It Works
The semantic indices:

Process code at either file or symbol level
Split large content into chunks that fit within token limits
Use OpenAI’s text-embedding-3-small model to create embeddings
Store embeddings efficiently for similarity search
Support incremental updates when code changes
When searching:

Your query is converted to an embedding
Cosine similarity is computed with all stored embeddings
The most similar items are returned with their scores
Creating embeddings requires an OpenAI API key with access to the embeddings endpoint.

​
Example Searches
Here are some example semantic searches:


Copy
# Find authentication-related code
results = index.similarity_search(
    "How is user authentication implemented?",
    k=3
)

# Find error handling patterns
results = index.similarity_search(
    "Show me examples of error handling and custom exceptions",
    k=3
)

# Find configuration management
results = index.similarity_search(
    "Where is the application configuration and settings handled?",
    k=3
)

Reducing Conditions
Graph-sitter provides powerful APIs for reducing conditional logic to constant values. This is particularly useful for removing feature flags, cleaning up dead code paths, and simplifying conditional logic.

​
Overview
The reduce_condition() method is available on various conditional constructs:

If/else statements
Ternary expressions
Binary expressions
Function calls
When you reduce a condition to True or False, Graph-sitter automatically:

Evaluates which code path(s) to keep
Removes unnecessary branches
Preserves proper indentation and formatting
​
Motivating Example
For example, consider the following code:


Copy
flag = get_feature_flag('MY_FEATURE')
if flag:
    print('MY_FEATURE: ON')
else:
    print('MY_FEATURE: OFF')
.reduce_condition allows you to deterministically reduce this code to the following:


Copy
print('MY_FEATURE: ON')
This is useful when a feature flag is fully “rolled out”.

​
Implementations
​
IfBlockStatements
You can reduce if/else statements to either their “true” or “false” branch.

For example, in the code snippet above:


Copy
# Grab if statement
if_block = file.code_block.statements[1]

# Reduce to True branch
if_block.reduce_condition(True)
This will remove the else branch and keep the print statement, like so:


Copy
flag = get_feature_flag('MY_FEATURE')
print('MY_FEATURE: ON')
​
Handling Elif Chains
Graph-sitter intelligently handles elif chains when reducing conditions:


Copy
# Original code
if condition_a:
    print("A")
elif condition_b:
    print("B")
else:
    print("C")

# Reduce first condition to False
if_block.reduce_condition(False)
# Result:
if condition_b:
    print("B")
else:
    print("C")

# Reduce elif condition to True
elif_block.reduce_condition(True)
# Result:
print("B")
​
Ternary Expressions
Ternary expressions (conditional expressions) can also be reduced:


Copy
# Original code
result = 'valueA' if condition else 'valueB'

# Reduce to True
ternary_expr.reduce_condition(True)
# Result:
result = 'valueA'

# Reduce to False
ternary_expr.reduce_condition(False)
# Result:
result = 'valueB'
​
Nested Ternaries
Graph-sitter handles nested ternary expressions correctly:


Copy
# Original code
result = 'A' if a else 'B' if b else 'C'

# Reduce outer condition to False
outer_ternary.reduce_condition(False)
# Result:
result = 'B' if b else 'C'

# Then reduce inner condition to True
inner_ternary.reduce_condition(True)
# Result:
result = 'B'
​
Binary Operations
Binary operations (and/or) can be reduced to simplify logic:


Copy
# Original code
result = (x or y) and b

# Reduce x to True
x_assign.reduce_condition(True)
# Result:
result = b

# Reduce y to False
y_assign.reduce_condition(False)
# Result:
result = x and b
​
Function Calls
Function calls can also be reduced, which is particularly useful when dealing with hooks or utility functions that return booleans:


Copy
// Original code
const isEnabled = useFeatureFlag("my_feature");
return isEnabled ? <NewFeature /> : <OldFeature />;

// After reducing useFeatureFlag to True
return <NewFeature />;
​
Feature Flag Hooks
A common use case is reducing feature flag hooks to constants. Consider the following code:


Copy
// Original code
function MyComponent() {
  const showNewUI = useFeatureFlag("new_ui_enabled");

  if (showNewUI) {
    return <NewUI />;
  }
  return <OldUI />;
}
We can reduce the useFeatureFlag hook to a constant value like so, with FunctionCall.reduce_condition:


Copy
hook = codebase.get_function("useFeatureFlag")
for usage in hook.usages():
    if isinstance(usage.match, FunctionCall):
        fcall = usage.match
        if fcall.args[0].value.content == 'new_ui_enabled':
            # This will automatically reduce any conditions using the flag
            fcall.reduce_condition(True)
This produces the following code:


Copy
function MyComponent() {
  return <NewUI />;
}
​
Comprehensive Example
Here’s a complete example of removing a feature flag from both configuration and usage:


Copy
feature_flag_name = "new_ui_enabled"
target_value = True

# 1. Remove from config
config_file = codebase.get_file("src/featureFlags/config.ts")
feature_flag_config = config_file.get_symbol("FEATURE_FLAG_CONFIG").value
feature_flag_config.pop(feature_flag_name)

# 2. Find and reduce all usages
hook = codebase.get_function("useFeatureFlag")
for usage in hook.usages():
    fcall = usage.match
    if isinstance(fcall, FunctionCall):
        # Check if this usage is for our target flag
        first_arg = fcall.args[0].value
        if isinstance(first_arg, String) and first_arg.content == feature_flag_name:
            print(f'Reducing in: {fcall.parent_symbol.name}')
            # This will automatically reduce:
            # - Ternary expressions using the flag
            # - If statements checking the flag
            # - Binary operations with the flag
            fcall.reduce_condition(target_value)

# Commit changes to disk
codebase.commit()
This example:

Removes the feature flag from configuration
Finds all usages of the feature flag hook
Reduces each usage to a constant value
Automatically handles all conditional constructs using the flag
When reducing a function call, Graph-sitter automatically handles all dependent conditions. This includes: - If/else statements - Ternary expressions - Binary operations

​
TypeScript and JSX Support
Condition reduction works with TypeScript and JSX, including conditional rendering:


Copy
// Original JSX
const MyComponent: React.FC = () => {
  let isVisible = true;
  return (
    <div>
      {isVisible && <span>Visible</span>}
      {!isVisible && <span>Hidden</span>}
    </div>
  );
};

// After reducing isVisible to True
const MyComponent: React.FC = () => {
  return (
    <div>
      <span>Visible</span>
    </div>
  );
};
System prompt (if using AI)
