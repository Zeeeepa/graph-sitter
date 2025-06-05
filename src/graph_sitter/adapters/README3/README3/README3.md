# Moving a function? Graph-sitter handles:
function.move_to_file("new_file.py")
# ✓ Updating all import statements
# ✓ Preserving dependencies
# ✓ Maintaining references
# ✓ Fixing relative imports
# ✓ Resolving naming conflicts

# Renaming a symbol? Graph-sitter manages:
class_def.rename("NewName")
# ✓ Updating all usages
# ✓ Handling string references
# ✓ Preserving docstrings
# ✓ Maintaining inheritance

The Codebase Graph
At the heart of Graph-sitter is a comprehensive graph representation of your code. When you initialize a Codebase, it performs static analysis to construct a rich graph structure connecting code elements:


Copy
# Initialize and analyze the codebase
from graph_sitter import Codebase
codebase = Codebase("./")

# Access pre-computed relationships
function = codebase.get_symbol("process_data")
print(f"Dependencies: {function.dependencies}")  # Instant lookup
print(f"Usages: {function.usages}")  # No parsing needed
​
Building the Graph
Codegen’s graph construction happens in two stages:

AST Parsing: We use Tree-sitter as our foundation for parsing code into Abstract Syntax Trees. Tree-sitter provides fast, reliable parsing across multiple languages.

Multi-file Graph Construction: Custom parsing logic, implemented in rustworkx and Python, analyzes these ASTs to construct a more sophisticated graph structure. This graph captures relationships between symbols, files, imports, and more.

​
Performance Through Pre-computation
Pre-computing a rich index enables Graph-sitter to make certain operations very fast that that are relevant to refactors and code analysis:

Finding all usages of a symbol
Detecting circular dependencies
Analyzing the dependency graphs
Tracing call graphs
Static analysis-based code retrieval for RAG
…etc.
Pre-parsing the codebase enables constant-time lookups rather than requiring re-parsing or real-time analysis.

​
Multi-Language Support
One of Codegen’s core principles is that many programming tasks are fundamentally similar across languages.

Currently, Graph-sitter supports:

Python
TypeScript
React & JSX
Learn about how Graph-sitter handles language specifics in the Language Support guide.

We’ve started with these ecosystems but designed our architecture to be extensible. The graph-based approach provides a consistent interface across languages while handling language-specific details under the hood.

Cyclomatic Complexity
Cyclomatic Complexity measures the number of linearly independent paths through the codebase, making it a valuable indicator of how difficult code will be to test and maintain.

Calculation Method:

Base complexity of 1
+1 for each:
if statement
elif statement
for loop
while loop
+1 for each boolean operator (and, or) in conditions
+1 for each except block in try-catch statements
The calculate_cyclomatic_complexity() function traverses the Codgen codebase object and uses the above rules to find statement objects within each function and calculate the overall cyclomatic complexity of the codebase.


Copy
def calculate_cyclomatic_complexity(function):
    def analyze_statement(statement):
        complexity = 0

        if isinstance(statement, IfBlockStatement):
            complexity += 1
            if hasattr(statement, "elif_statements"):
                complexity += len(statement.elif_statements)

        elif isinstance(statement, (ForLoopStatement, WhileStatement)):
            complexity += 1

        return complexity
​
Halstead Volume
Halstead Volume is a software metric which measures the complexity of a codebase by counting the number of unique operators and operands. It is calculated by multiplying the sum of unique operators and operands by the logarithm base 2 of the sum of unique operators and operands.

Halstead Volume: V = (N1 + N2) * log2(n1 + n2)

This calculation uses codegen’s expression types to make this calculation very efficient - these include BinaryExpression, UnaryExpression and ComparisonExpression. The function extracts operators and operands from the codebase object and calculated in calculate_halstead_volume() function.


Copy
def calculate_halstead_volume(operators, operands):
    n1 = len(set(operators))
    n2 = len(set(operands))

    N1 = len(operators)
    N2 = len(operands)

    N = N1 + N2
    n = n1 + n2

    if n > 0:
        volume = N * math.log2(n)
        return volume, N1, N2, n1, n2
    return 0, N1, N2, n1, n2
​
Depth of Inheritance (DOI)
Depth of Inheritance measures the length of inheritance chain for each class. It is calculated by counting the length of the superclasses list for each class in the codebase. The implementation is handled through a simple calculation using codegen’s class information in the calculate_doi() function.


Copy
def calculate_doi(cls):
    return len(cls.superclasses)
​
Maintainability Index
Maintainability Index is a software metric which measures how maintainable a codebase is. Maintainability is described as ease to support and change the code. This index is calculated as a factored formula consisting of SLOC (Source Lines Of Code), Cyclomatic Complexity and Halstead volume.

Maintainability Index: M = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(SLOC)

This formula is then normalized to a scale of 0-100, where 100 is the maximum maintainability.

The implementation is handled through the calculate_maintainability_index() function. The codegen codebase object is used to efficiently extract the Cyclomatic Complexity and Halstead Volume for each function and class in the codebase, which are then used to calculate the maintainability index.


Copy
def calculate_maintainability_index(
    halstead_volume: float, cyclomatic_complexity: float, loc: int
) -> int:
    """Calculate the normalized maintainability index for a given function."""
    if loc <= 0:
        return 100

    try:
        raw_mi = (
            171
            - 5.2 * math.log(max(1, halstead_volume))
            - 0.23 * cyclomatic_complexity
            - 16.2 * math.log(max(1, loc))
        )
        normalized_mi = max(0, min(100, raw_mi * 100 / 171))
        return int(normalized_mi)
    except (ValueError, TypeError):
        return 0
​
Line Metrics
Line metrics provide insights into the size, complexity, and maintainability of a codebase. These measurements help determine the scale of a project, identify areas that may need refactoring, and track the growth of the codebase over time.

​
Lines of Code
Lines of Code refers to the total number of lines in the source code, including blank lines and comments. This is accomplished with a simple count of all lines in the source file.

​
Logical Lines of Code (LLOC)
LLOC is the amount of lines of code which contain actual functional statements. It excludes comments, blank lines, and other lines which do not contribute to the utility of the codebase. A high LLOC relative to total lines of code suggests dense, potentially complex code that may benefit from breaking into smaller functions or modules with more documentation.

​
Source Lines of Code (SLOC)
SLOC refers to the number of lines containing actual code, excluding blank lines. This includes programming language keywords and comments. While a higher SLOC indicates a larger codebase, it should be evaluated alongside other metrics like cyclomatic complexity and maintainability index to assess if the size is justified by the functionality provided.

​
Comment Density
Comment density is calculated by dividing the lines of code which contain comments by the total lines of code in the codebase. The formula is:


Copy
"comment_density": (total_comments / total_loc * 100)
It measures the proportion of comments in the codebase and is a good indicator of how much code is properly documented. Accordingly, it can show how maintainable and easy to understand the codebase is.

​
General Codebase Statistics
The number of files is determined by traversing codegen’s FileNode objects in the parsed codebase. The number of functions is calculated by counting FunctionDef nodes across all parsed files. The number of classes is obtained by summing ClassDef nodes throughout the codebase.


Copy
num_files = len(codebase.files(extensions="*"))
num_functions = len(codebase.functions)
num_classes = len(codebase.classes)
The commit activity is calculated by using the git history of the repository. The number of commits is counted for each month in the last 12 months.

​
Using the Analysis Tool (Modal Server)
The tool is implemented as a FastAPI application wrapped in a Modal deployment. To analyze a repository:

Send a POST request to /analyze_repo with the repository URL
The tool will:
Clone the repository
Parse the codebase using codegen
Calculate all metrics
Return a comprehensive JSON response with all metrics
This is the only endpoint in the FastAPI server, as it takes care of the entire analysis process. To run the FastAPI server locally, install all dependencies and run the server with modal serve modal_main.py.

The server can be connected to the frontend dashboard. This web component is implemented as a Next.js application with appropriate comments and visualizations for the raw server data. To run the frontend locally, install all dependencies and run the server with npm run dev. This can be connected to the FastAPI server by setting the URL in the request to the /analyze_repo endpoint.

Step 1: Finding Functions and Their Context
First, we will do a “graph expansion” for each function - grab the function’s source, as well as the full source of all usages of the function and all dependencies.

See dependencies and usages to learn more about navigating the code graph
First, let’s import the types we need from Codegen:


Copy
import graph_sitter
from graph_sitter import Codebase
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
Here’s how we get the full context for each function:


Copy
def get_function_context(function) -> dict:
    """Get the implementation, dependencies, and usages of a function."""
    context = {
        "implementation": {"source": function.source, "filepath": function.filepath},
        "dependencies": [],
        "usages": [],
    }

    # Add dependencies
    for dep in function.dependencies:
        # Hop through imports to find the root symbol source
        if isinstance(dep, Import):
            dep = hop_through_imports(dep)

        context["dependencies"].append({"source": dep.source, "filepath": dep.filepath})

    # Add usages
    for usage in function.usages:
        context["usages"].append({
            "source": usage.usage_symbol.source,
            "filepath": usage.usage_symbol.filepath,
        })

    return context
Notice how we use hop_through_imports to resolve dependencies. When working with imports, symbols can be re-exported multiple times. For example, a helper function might be imported and re-exported through several files before being used. We need to follow this chain to find the actual implementation:


Copy
def hop_through_imports(imp: Import) -> Symbol | ExternalModule:
    """Finds the root symbol for an import."""
    if isinstance(imp.imported_symbol, Import):
        return hop_through_imports(imp.imported_symbol)
    return imp.imported_symbol
This creates a structured representation of each function’s context:


Copy
{
  "implementation": {
    "source": "def process_data(input: str) -> dict: ...",
    "filepath": "src/data_processor.py"
  },
  "dependencies": [
    {
      "source": "def validate_input(data: str) -> bool: ...",
      "filepath": "src/validators.py"
    }
  ],
  "usages": [
    {
      "source": "result = process_data(user_input)",
      "filepath": "src/api.py"
    }
  ]
}
​
Step 2: Processing the Codebase
Next, we process all functions in the codebase to generate our training data:


Copy
def run(codebase: Codebase):
    """Generate training data using a node2vec-like approach for code embeddings."""
    # Track all function contexts
    training_data = {
        "functions": [],
        "metadata": {
            "total_functions": len(codebase.functions),
            "total_processed": 0,
            "avg_dependencies": 0,
            "avg_usages": 0,
        },
    }

    # Process each function in the codebase
    for function in codebase.functions:
        # Skip if function is too small
        if len(function.source.split("\n")) < 2:
            continue

        # Get function context
        context = get_function_context(function)

        # Only keep functions with enough context
        if len(context["dependencies"]) + len(context["usages"]) > 0:
            training_data["functions"].append(context)

    # Update metadata
    training_data["metadata"]["total_processed"] = len(training_data["functions"])
    if training_data["functions"]:
        training_data["metadata"]["avg_dependencies"] = sum(
            len(f["dependencies"]) for f in training_data["functions"]
        ) / len(training_data["functions"])
        training_data["metadata"]["avg_usages"] = sum(
            len(f["usages"]) for f in training_data["functions"]
        ) / len(training_data["functions"])

    return training_data
​
Step 3: Running the Generator
Finally, we can run our training data generator on any codebase.

See parsing codebases to learn more

Copy
if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("fastapi/fastapi")

    print("Generating training data...")
    training_data = run(codebase)

    print("Saving training data...")
    with open("training_data.json", "w") as f:
        json.dump(training_data, f, indent=2)
    print("Training data saved to training_data.json")
This will:

Load the target codebase
Process all functions
Save the structured training data to a JSON file
You can use any Git repository as your source codebase by passing the repo URL to Codebase.from_repo(…).

​
Using the Training Data
The generated data can be used to train LLMs in several ways:

Masked Function Prediction: Hide a function’s implementation and predict it from dependencies and usages
Code Embeddings: Generate embeddings that capture semantic relationships between functions
Dependency Prediction: Learn to predict which functions are likely to be dependencies
Usage Pattern Learning: Train models to understand common usage patterns
For example, to create a masked prediction task:


Copy
def create_training_example(function_data):
    """Create a masked prediction example from function data."""
    return {
        "context": {
            "dependencies": function_data["dependencies"],
            "usages": function_data["usages"]
        },
        "target": function_data["implementation"]
    }

# Create training examples
examples = [create_training_example(f) for f in training_data["functions"]]

unc, ExternalModule):
            func_name = func.name
        elif isinstance(func, Function):
            func_name = f"{func.parent_class.name}.{func.name}" if func.is_method else func.name

        # Add node and edge with metadata
        G.add_node(func, name=func_name, 
                  color=COLOR_PALETTE.get(func.__class__.__name__))
        G.add_edge(src_func, func, **generate_edge_meta(call))

        # Recurse for regular functions
        if isinstance(func, Function):
            create_downstream_call_trace(func, depth + 1)
​
Adding Edge Metadata
We can enrich our edges with metadata about the function calls:


Copy
def generate_edge_meta(call: FunctionCall) -> dict:
    """Generate metadata for call graph edges
    
    Args:
        call (FunctionCall): Function call information
        
    Returns:
        dict: Edge metadata including name and location
    """
    return {
        "name": call.name,
        "file_path": call.filepath,
        "start_point": call.start_point,
        "end_point": call.end_point,
        "symbol_name": "FunctionCall"
    }
​
Visualizing the Graph
Finally, we can visualize our call graph starting from a specific function:


Copy
# Get target function to analyze
target_class = codebase.get_class('SharingConfigurationViewSet')
target_method = target_class.get_method('patch')

# Add root node 
G.add_node(target_method, 
           name=f"{target_class.name}.{target_method.name}",
           color=COLOR_PALETTE["StartFunction"])

# Build the call graph
create_downstream_call_trace(target_method)

# Render the visualization
codebase.visualize(G)
​
Take a look

View on codegen.sh

​
Common Use Cases
The call graph visualization is particularly useful for:

Understanding complex codebases
Planning refactoring efforts
Identifying tightly coupled components
Analyzing critical paths
Documenting system architecture
​
Function Dependency Graph
Understanding symbol dependencies is crucial for maintaining and refactoring code. This tutorial will show you how to create visual dependency graphs using Codegen and NetworkX. We will be creating a dependency graph of the get_query_runner function. View the source code here.

​
Basic Setup
We’ll use the same basic setup as the Call Trace Visualization tutorial.

​
Building the Dependency Graph
The core function for building our dependency graph:


Copy
def create_dependencies_visualization(symbol: Symbol, depth: int = 0):
    """Creates visualization of symbol dependencies
    
    Args:
        symbol (Symbol): Starting symbol to analyze
        depth (int): Current recursion depth
    """
    # Prevent excessive recursion
    if depth >= MAX_DEPTH:
        return
    
    # Process each dependency
    for dep in symbol.dependencies:
        dep_symbol = None
        
        # Handle different dependency types
        if isinstance(dep, Symbol):
            # Direct symbol reference
            dep_symbol = dep
        elif isinstance(dep, Import):
            # Import statement - get resolved symbol
            dep_symbol = dep.resolved_symbol if dep.resolved_symbol else None

        if dep_symbol:
            # Add node with appropriate styling
            G.add_node(dep_symbol, 
                      color=COLOR_PALETTE.get(dep_symbol.__class__.__name__, 
                                            "#f694ff"))
            
            # Add dependency relationship
            G.add_edge(symbol, dep_symbol)
            
            # Recurse unless it's a class (avoid complexity)
            if not isinstance(dep_symbol, PyClass):
                create_dependencies_visualization(dep_symbol, depth + 1)
​
Visualizing the Graph
Finally, we can visualize our dependency graph starting from a specific symbol:


Copy
# Get target symbol
target_func = codebase.get_function("get_query_runner")

# Add root node 
G.add_node(target_func, color=COLOR_PALETTE["StartFunction"])

# Generate dependency graph
create_dependencies_visualization(target_func)

# Render visualization
codebase.visualize(G)
​
Take a look

View on codegen.sh

​
Blast Radius visualization
Understanding the impact of code changes is crucial for safe refactoring. A blast radius visualization shows how changes to one function might affect other parts of the codebase by tracing usage relationships. In this tutorial we will create a blast radius visualization of the export_asset function. View the source code here.

​
Basic Setup
We’ll use the same basic setup as the Call Trace Visualization tutorial.

​
Helper Functions
We’ll create some utility functions to help build our visualization:


Copy
# List of HTTP methods to highlight
HTTP_METHODS = ["get", "put", "patch", "post", "head", "delete"]

def generate_edge_meta(usage: Usage) -> dict:
    """Generate metadata for graph edges
    
    Args:
        usage (Usage): Usage relationship information
        
    Returns:
        dict: Edge metadata including name and location
    """
    return {
        "name": usage.match.source,
        "file_path": usage.match.filepath, 
        "start_point": usage.match.start_point,
        "end_point": usage.match.end_point,
        "symbol_name": usage.match.__class__.__name__
    }

def is_http_method(symbol: PySymbol) -> bool:
    """Check if a symbol is an HTTP endpoint method
    
    Args:
        symbol (PySymbol): Symbol to check
        
    Returns:
        bool: True if symbol is an HTTP method
    """
    if isinstance(symbol, PyFunction) and symbol.is_method:
        return symbol.name in HTTP_METHODS
    return False
​
Building the Blast Radius Visualization
The main function for creating our blast radius visualization:


Copy
def create_blast_radius_visualization(symbol: PySymbol, depth: int = 0):
    """Create visualization of symbol usage relationships
    
    Args:
        symbol (PySymbol): Starting symbol to analyze
        depth (int): Current recursion depth
    """
    # Prevent excessive recursion
    if depth >= MAX_DEPTH:
        return
    
    # Process each usage of the symbol
    for usage in symbol.usages:
        usage_symbol = usage.usage_symbol
        
        # Determine node color based on type
        if is_http_method(usage_symbol):
            color = COLOR_PALETTE.get("HTTP_METHOD")
        else:
            color = COLOR_PALETTE.get(usage_symbol.__class__.__name__, "#f694ff")

        # Add node and edge to graph
        G.add_node(usage_symbol, color=color)
        G.add_edge(symbol, usage_symbol, **generate_edge_meta(usage))
        
        # Recursively process usage symbol
        create_blast_radius_visualization(usage_symbol, depth + 1)
​
Visualizing the Graph
Finally, we can create our blast radius visualization:


Copy
# Get target function to analyze
target_func = codebase.get_function('export_asset')

# Add root node
G.add_node(target_func, color=COLOR_PALETTE.get("StartFunction"))

# Build the visualization
create_blast_radius_visualization(target_func)

# Render graph to show impact flow
# Note: a -> b means changes to a will impact b
codebase.visualize(G)

Migrating APIs
API migrations are a common task in large codebases. Whether you’re updating a deprecated function, changing parameter names, or modifying return types, Graph-sitter makes it easy to update all call sites consistently.

​
Common Migration Scenarios
​
Renaming Parameters
When updating parameter names across an API, you need to update both the function definition and all call sites:


Copy
# Find the API function to update
api_function = codebase.get_function("process_data")

# Update the parameter name
old_param = api_function.get_parameter("input")
old_param.rename("data")

# All call sites are automatically updated:
# process_data(input="test") -> process_data(data="test")
See dependencies and usages for more on updating parameter names and types.
​
Adding Required Parameters
When adding a new required parameter to an API:


Copy
# Find all call sites before modifying the function
call_sites = list(api_function.call_sites)

# Add the new parameter
api_function.add_parameter("timeout: int")

# Update all existing call sites to include the new parameter
for call in call_sites:
    call.add_argument("timeout=30")  # Add with a default value
See function calls and callsites for more on handling call sites.
​
Changing Parameter Types
When updating parameter types:


Copy
# Update the parameter type
param = api_function.get_parameter("user_id")
param.type = "UUID"  # Change from string to UUID

# Find all call sites that need type conversion
for call in api_function.call_sites:
    arg = call.get_arg_by_parameter_name("user_id")
    if arg:
        # Convert string to UUID
        arg.edit(f"UUID({arg.value})")
See working with type annotations for more on changing parameter types.
​
Deprecating Functions
When deprecating an old API in favor of a new one:


Copy
old_api = codebase.get_function("old_process_data")
new_api = codebase.get_function("new_process_data")

# Add deprecation warning
old_api.add_decorator('@deprecated("Use new_process_data instead")')

# Update all call sites to use the new API
for call in old_api.call_sites:
    # Map old arguments to new parameter names
    args = [
        f"data={call.get_arg_by_parameter_name('input').value}",
        f"timeout={call.get_arg_by_parameter_name('wait').value}"
    ]
    
    # Replace the old call with the new API
    call.replace(f"new_process_data({', '.join(args)})")
​
Bulk Updates to Method Chains
When updating chained method calls, like database queries or builder patterns:


Copy
# Find all query chains ending with .execute()
for execute_call in codebase.function_calls:
    if execute_call.name != "execute":
        continue
        
    # Get the full chain
    chain = execute_call.call_chain
    
    # Example: Add .timeout() before .execute()
    if "timeout" not in {call.name for call in chain}:
        execute_call.insert_before("timeout(30)")
​
Handling Breaking Changes
When making breaking changes to an API, it’s important to:

Identify all affected call sites
Make changes consistently
Update related documentation
Consider backward compatibility
Here’s a comprehensive example:


Copy
def migrate_api_v1_to_v2(codebase):
    old_api = codebase.get_function("create_user_v1")
    
    # Document all existing call patterns
    call_patterns = {}
    for call in old_api.call_sites:
        args = [arg.source for arg in call.args]
        pattern = ", ".join(args)
        call_patterns[pattern] = call_patterns.get(pattern, 0) + 1
    
    print("Found call patterns:")
    for pattern, count in call_patterns.items():
        print(f"  {pattern}: {count} occurrences")
    
    # Create new API version
    new_api = old_api.copy()
    new_api.rename("create_user_v2")
    
    # Update parameter types
    new_api.get_parameter("email").type = "EmailStr"
    new_api.get_parameter("role").type = "UserRole"
    
    # Add new required parameters
    new_api.add_parameter("tenant_id: UUID")
    
    # Update all call sites
    for call in old_api.call_sites:
        # Get current arguments
        email_arg = call.get_arg_by_parameter_name("email")
        role_arg = call.get_arg_by_parameter_name("role")
        
        # Build new argument list with type conversions
        new_args = [
            f"email=EmailStr({email_arg.value})",
            f"role=UserRole({role_arg.value})",
            "tenant_id=get_current_tenant_id()"
        ]
        
        # Replace old call with new version
        call.replace(f"create_user_v2({', '.join(new_args)})")
    
    # Add deprecation notice to old version
    old_api.add_decorator('@deprecated("Use create_user_v2 instead")')

# Run the migration
migrate_api_v1_to_v2(codebase)
​
Best Practices
Analyze First: Before making changes, analyze all call sites to understand usage patterns


Copy
# Document current usage
for call in api.call_sites:
    print(f"Called from: {call.parent_function.name}")
    print(f"With args: {[arg.source for arg in call.args]}")
Make Atomic Changes: Update one aspect at a time


Copy
# First update parameter names
param.rename("new_name")

# Then update types
param.type = "new_type"

# Finally update call sites
for call in api.call_sites:
    # ... update calls
Maintain Backwards Compatibility:


Copy
# Add new parameter with default
api.add_parameter("new_param: str = None")

# Later make it required
api.get_parameter("new_param").remove_default()
Document Changes:


Copy
# Add clear deprecation messages
old_api.add_decorator('''@deprecated(
    "Use new_api() instead. Migration guide: docs/migrations/v2.md"
)''')


Organizing Your Codebase
Codegen SDK provides a powerful set of tools for deterministically moving code safely and efficiently. This guide will walk you through the basics of moving code with Codegen SDK.

Common use cases include:


Splitting up large files


Copy
print(f"🔍 Processing file: {filepath}")
file = codebase.get_file(filepath)

# Get the directory path for creating new files
dir_path = file.directory.path if file.directory else ""

# Iterate through all functions in the file
for function in file.functions:
    # Create new filename based on function name
    new_filepath = f"{dir_path}/{function.name}.py"
    print(f"📝 Creating new file: {new_filepath}")

    # Create the new file
    new_file = codebase.create_file(new_filepath)

    # Move the function to the new file, including dependencies
    print(f"➡️ Moving function: {function.name}")
    function.move_to_file(new_file, include_dependencies=True)

Organize code into modules


Copy
# Dictionary to track modules and their functions
module_map = {
    "utils": lambda f: f.name.startswith("util_") or f.name.startswith("helper_"),
    "api": lambda f: f.name.startswith("api_") or f.name.startswith("endpoint_"),
    "data": lambda f: f.name.startswith("data_") or f.name.startswith("db_"),
    "core": lambda f: True  # Default module for other functions
}

print("🔍 Starting code organization...")

# Create module directories if they don't exist
for module in module_map.keys():
    if not codebase.has_directory(module):
        print(f"📁 Creating module directory: {module}")
        codebase.create_directory(module, exist_ok=True)

# Process each file in the codebase
for file in codebase.files:
    print(f"\n📄 Processing file: {file.filepath}")

    # Skip if file is already in a module directory
    if any(file.filepath.startswith(module) for module in module_map.keys()):
        continue

    # Process each function in the file
    for function in file.functions:
        # Determine which module this function belongs to
        target_module = next(
            (module for module, condition in module_map.items()
             if condition(function)),
            "core"
        )

        # Create the new file path
        new_filepath = f"{target_module}/{function.name}.py"

        print(f"  ➡️ Moving {function.name} to {target_module} module")

        # Create new file and move function
        if not codebase.has_file(new_filepath):
            new_file = codebase.create_file(new_filepath)
            function.move_to_file(new_file, include_dependencies=True)

print("\n✅ Code organization complete!")

Break up import cycles


Copy
# Create a graph to detect cycles
import networkx as nx

# Build dependency graph
G = nx.DiGraph()

# Add edges for imports between files
for file in codebase.files:
    for imp in file.imports:
        if imp.from_file:
            G.add_edge(file.filepath, imp.from_file.filepath)

# Find cycles in the graph
cycles = list(nx.simple_cycles(G))

if not cycles:
    print("✅ No import cycles found!")
    exit()

print(f"🔍 Found {len(cycles)} import cycles")

# Process each cycle
for cycle in cycles:
    print(f"\n⭕ Processing cycle: {' -> '.join(cycle)}")

    # Get the first two files in the cycle
    file1 = codebase.get_file(cycle[0])
    file2 = codebase.get_file(cycle[1])

    # Find functions in file1 that are used by file2
    for function in file1.functions:
        if any(usage.file == file2 for usage in function.usages):
            # Create new file for the shared function
            new_filepath = f"shared/{function.name}.py"
            print(f"  ➡️ Moving {function.name} to {new_filepath}")

            if not codebase.has_directory("shared"):
                codebase.create_directory("shared")

            new_file = codebase.create_file(new_filepath)
            function.move_to_file(new_file, include_dependencies=True)

print("\n✅ Import cycles resolved!")
Most operations in Graph-sitter will automatically handle updaging dependencies and imports. See Moving Symbols to learn more.

​
Basic Symbol Movement
To move a symbol from one file to another, you can use the move_to_file method.


python

typescript

Copy
# Get the symbol
symbol_to_move = source_file.get_symbol("my_function")
# Pick a destination file
dst_file = codebase.get_file("path/to/dst/location.py")
# Move the symbol, move all of its dependencies with it (remove from old file), and add an import of symbol into old file
symbol_to_move.move_to_file(dst_file, include_dependencies=True, strategy="add_back_edge")
This will move my_function to path/to/dst/location.py, safely updating all references to it in the process.

​
Updating Imports
After moving a symbol, you may need to update imports throughout your codebase. GraphSitter offers two strategies for this:

Update All Imports: This strategy updates all imports across the codebase to reflect the new location of the symbol.

python

typescript

Copy
symbol_to_move = codebase.get_symbol("symbol_to_move")
dst_file = codebase.create_file("new_file.py")
symbol_to_move.move_to_file(dst_file, strategy="update_all_imports")
Updating all imports can result in very large PRs
Add Back Edge: This strategy adds an import in the original file that re-imports (and exports) the moved symbol, maintaining backwards compatibility. This will result in fewer total modifications, as existing imports will not need to be updated.

python

typescript

Copy
symbol_to_move = codebase.get_symbol("symbol_to_move")
dst_file = codebase.create_file("new_file.py")
symbol_to_move.move_to_file(dst_file, strategy="add_back_edge")
​
Handling Dependencies
By default, Graph-sitter will move all of a symbols dependencies along with it. This ensures that your codebase remains consistent and functional.


python

typescript

Copy
my_symbol = codebase.get_symbol("my_symbol")
dst_file = codebase.create_file("new_file.py")
my_symbol.move_to_file(dst_file, include_dependencies=True)
If you set include_dependencies=False, only the symbol itself will be moved, and any dependencies will remain in the original file.

​
Moving Multiple Symbols
If you need to move multiple symbols, you can do so in a loop:


Copy
source_file = codebase.get_file("path/to/source_file.py")
dest_file = codebase.get_file("path/to/destination_file.py")
# Create a list of symbols to move
symbols_to_move = [source_file.get_function("my_function"), source_file.get_class("MyClass")]
# Move each symbol to the destination file
for symbol in symbols_to_move:
    symbol.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")
​
Best Practices
Commit After Major Changes: If you’re making multiple significant changes, use codebase.commit() between them to ensure the codebase graph is up-to-date.

Re-fetch References: After a commit, re-fetch any file or symbol references you’re working with, as they may have become stale.

Handle Errors: Be prepared to handle cases where symbols or files might not exist, or where moves might fail due to naming conflicts.

By following these guidelines, you can effectively move symbols around your codebase while maintaining its integrity and functionality.

Finding Promise Chains
Graph-sitter offers multiple ways to locate Promise chains in your codebase:

In files
In functions
Part of a function call chain
​
Promise Chains in a File
Find all Promise chains in a file:


Copy
ts_file = codebase.get_file("api_client.ts")
promise_chains = ts_file.promise_chains

print(f"Found {len(promise_chains)} Promise chains")
​
Promise Chains in a Function
Find Promise chains within a specific function:


Copy
ts_func = codebase.get_function("getUserData")
chains = ts_func.promise_chains

for chain in chains:
    print(f"Found chain starting with: {chain.name}")
​
Promise Chain starting from a Function Call
Find Promise chains starting from a specific function call:


Copy
# Assuming the function call is part of a promise chain
fetch_call = codebase.get_function("fetchUserData").function_calls[2]
chain = fetch_call.promise_chain
​
Converting Promise Chains
​
In-Place Conversion
Convert Promise chains directly in your codebase:


Copy
# Find and convert all Promise chains in a file
for chain in typescript_file.promise_chains:
    chain.convert_to_async_await()
​
Handle Business Logic Without In-Place Edit
Generate the transformed code without inplace edit by returning the new code as a string. This is useful when you want to add additional business logic to the overall conversion.


Copy
async_await_code = chain.convert_to_async_await(inplace_edit=False)
print("Converted code:", async_await_code)

promise_statement = chain.parent_statement
new_code = promise_statement.edit(
    f"""
    {async_await_code}

    // handle additional business logic here
    """
)
​
Supported Promise Chain Patterns
Basic promise.then() statements of any length
Catch promise.then().catch() statements of any length
Finally promise.then().catch().finally() statements of any length
Desctructure promise.then((var1, var2)) statements -> let [var1, var2] = await statement;
Implicit returns -> return promise.then(() => console.log("hello"))
Top level variable assignments -> let assigned_var = promise.then()
Top level variable assignments -> let assigned_var = promise.then()
Ambiguous/conditional return blocks
A list of all the covered cases can be found in the example notebook.

​
Examples
​
1. Basic Promise Chains

Copy
// Before
function getValue(): Promise<number> {
    return Promise.resolve(10)
        .then(value => value * 2);
}
Applying the conversion…


Copy
promise_chain = codebase.get_function("getValue").promise_chains[0]
promise_chain.convert_to_async_await()
codebase.commit()

Copy
// After
async function getValue(): Promise<number> {
    let value = await Promise.resolve(10);
    return value * 2;
}
​
2. Error Handling with Catch/Finally

Copy
// Before
function processData(): Promise<void> {
    return fetchData()
        .then(data => processData(data))
        .catch(error => {
            console.error("Error:", error);
            throw error;
        })
        .finally(() => {
            cleanup();
        });
}
Applying the conversion…


Copy
promise_chain = codebase.get_function("processData").promise_chains[0]
promise_chain.convert_to_async_await()
codebase.commit()

Copy
// After
async function processData(): Promise<void> {
    try {
        let data = await fetchData();
        return processData(data);
    } catch (error) {
        console.error("Error:", error);
        throw error;
    } finally {
        cleanup();
    }
}
​
3. Promise.all with Destructuring

Copy
// Before
function getAllUserInfo(userId: number) {
    return Promise.all([
        fetchUserData(userId),
        fetchUserPosts(userId)
    ]).then(([user, posts]) => {
        return { user, posts };
    });
}
Applying the conversion…


Copy
promise_chain = codebase.get_function("getAllUserInfo").promise_chains[0]
promise_chain.convert_to_async_await()
codebase.commit()

Copy
// After
async function getAllUserInfo(userId: number) {
    const [user, posts] = await Promise.all([
        fetchUserData(userId),
        fetchUserPosts(userId)
    ]);
    return { user, posts };
}
​
4. Handling Ambiguous Returns Using Anonymous functions
For then blocks that have more than one return statement, Graph-sitter will add an anonymous function to handle the ambiguous return to guarantee a deterministic conversion.


Copy
// Before
function create(opts: any): Promise<any> {
	let qResponse = request(opts);
	qResponse = qResponse.then(function success(response) {
		if (response.statusCode < 200 || response.statusCode >= 300) {
			throw new Error(JSON.stringify(response));
		}
		if (typeof response.body === "string") {
			return JSON.parse(response.body);
		}
		return response.body;
	});

	return qResponse;
}
Applying the conversion…


Copy
promise_chain = codebase.get_function("create").promise_chains[0]
promise_chain.convert_to_async_await()
codebase.commit()

Copy
// After
async function create(opts): Promise<any> {
	let qResponse = request(opts);
	let response = await qResponse;
	qResponse = (async (response) => {
		if (response.statusCode < 200 || response.statusCode >= 300) {
			throw new Error(JSON.stringify(response));
		}
		if (typeof response.body === "string") {
			return JSON.parse(response.body);
		}
		return response.body;
	})(response);

	return qResponse;
}
​
Handling Top-Level Assignment Variables
When converting Promise chains that involve top-level assignment variables, you can specify the variable name of your choice or pick the default which is the original variable assignment name.


Copy
# Convert with custom variable names for clarity
chain.convert_to_async_await(
    assignment_variable_name="operationResult",
)
​
Next Steps
Converting Promise chains to async/await improves code readability and maintainability. Codegen’s tools make this migration process automated and reliable, handling complex cases while preserving business logic. Here are some next steps to ensure a successful migration:

Ensure to run npx prettier --write . after the migration to fix indentation + linting
Incremental Migration: Convert one module at a time
Handle Additional Business Logic: Use .promise_statement.edit() to modify the entire chain and handle external business logic
If the specific conversion case is not covered, open an issue on the Codegen repository or try to right your own transformation logic using the codegen-sdk

Improving Code Modularity
Codegen SDK provides powerful tools for analyzing and improving code modularity. This guide will help you identify and fix common modularity issues like circular dependencies, tight coupling, and poorly organized imports.

Common use cases include:

Breaking up circular dependencies
Organizing imports and exports
Identifying highly coupled modules
Extracting shared code into common modules
Analyzing module boundaries
​
Analyzing Import Relationships
First, let’s see how to analyze import relationships in your codebase:


Copy
import networkx as nx
from collections import defaultdict

# Create a graph of file dependencies
def create_dependency_graph():
    G = nx.DiGraph()
    
    for file in codebase.files:
        # Add node for this file
        G.add_node(file.filepath)
        
        # Add edges for each import
        for imp in file.imports:
            if imp.from_file:  # Skip external imports
                G.add_edge(file.filepath, imp.from_file.filepath)
    
    return G

# Create and analyze the graph
graph = create_dependency_graph()

# Find circular dependencies
cycles = list(nx.simple_cycles(graph))
if cycles:
    print("🔄 Found circular dependencies:")
    for cycle in cycles:
        print(f"  • {' -> '.join(cycle)}")

# Calculate modularity metrics
print("\n📊 Modularity Metrics:")
print(f"  • Number of files: {len(graph.nodes)}")
print(f"  • Number of imports: {len(graph.edges)}")
print(f"  • Average imports per file: {len(graph.edges)/len(graph.nodes):.1f}")
​
Breaking Circular Dependencies
When you find circular dependencies, here’s how to break them:


Copy
def break_circular_dependency(cycle):
    # Get the first two files in the cycle
    file1 = codebase.get_file(cycle[0])
    file2 = codebase.get_file(cycle[1])
    
    # Create a shared module for common code
    shared_dir = "shared"
    if not codebase.has_directory(shared_dir):
        codebase.create_directory(shared_dir)
    
    # Find symbols used by both files
    shared_symbols = []
    for symbol in file1.symbols:
        if any(usage.file == file2 for usage in symbol.usages):
            shared_symbols.append(symbol)
    
    # Move shared symbols to a new file
    if shared_symbols:
        shared_file = codebase.create_file(f"{shared_dir}/shared_types.py")
        for symbol in shared_symbols:
            symbol.move_to_file(shared_file, strategy="update_all_imports")

# Break each cycle found
for cycle in cycles:
    break_circular_dependency(cycle)
​
Organizing Imports
Clean up and organize imports across your codebase:


Copy
def organize_file_imports(file):
    # Group imports by type
    std_lib_imports = []
    third_party_imports = []
    local_imports = []
    
    for imp in file.imports:
        if imp.is_standard_library:
            std_lib_imports.append(imp)
        elif imp.is_third_party:
            third_party_imports.append(imp)
        else:
            local_imports.append(imp)
    
    # Sort each group
    for group in [std_lib_imports, third_party_imports, local_imports]:
        group.sort(key=lambda x: x.module_name)
    
    # Remove all existing imports
    for imp in file.imports:
        imp.remove()
    
    # Add imports back in organized groups
    if std_lib_imports:
        for imp in std_lib_imports:
            file.add_import(imp.source)
        file.insert_after_imports("")  # Add newline
        
    if third_party_imports:
        for imp in third_party_imports:
            file.add_import(imp.source)
        file.insert_after_imports("")  # Add newline
        
    if local_imports:
        for imp in local_imports:
            file.add_import(imp.source)

# Organize imports in all files
for file in codebase.files:
    organize_file_imports(file)
​
Identifying Highly Coupled Modules
Find modules that might need to be split up:


Copy
from collections import defaultdict

def analyze_module_coupling():
    coupling_scores = defaultdict(int)
    
    for file in codebase.files:
        # Count unique files imported from
        imported_files = {imp.from_file for imp in file.imports if imp.from_file}
        coupling_scores[file.filepath] = len(imported_files)
        
        # Count files that import this file
        importing_files = {usage.file for symbol in file.symbols 
                         for usage in symbol.usages if usage.file != file}
        coupling_scores[file.filepath] += len(importing_files)
    
    # Sort by coupling score
    sorted_files = sorted(coupling_scores.items(), 
                         key=lambda x: x[1], 
                         reverse=True)
    
    print("\n🔍 Module Coupling Analysis:")
    print("\nMost coupled files:")
    for filepath, score in sorted_files[:5]:
        print(f"  • {filepath}: {score} connections")

analyze_module_coupling()
​
Extracting Shared Code
When you find highly coupled modules, extract shared code:


Copy
def extract_shared_code(file, min_usages=3):
    # Find symbols used by multiple files
    for symbol in file.symbols:
        # Get unique files using this symbol
        using_files = {usage.file for usage in symbol.usages 
                      if usage.file != file}
        
        if len(using_files) >= min_usages:
            # Create appropriate shared module
            module_name = determine_shared_module(symbol)
            if not codebase.has_file(f"shared/{module_name}.py"):
                shared_file = codebase.create_file(f"shared/{module_name}.py")
            else:
                shared_file = codebase.get_file(f"shared/{module_name}.py")
            
            # Move symbol to shared module
            symbol.move_to_file(shared_file, strategy="update_all_imports")

def determine_shared_module(symbol):
    # Logic to determine appropriate shared module name
    if symbol.is_type:
        return "types"
    elif symbol.is_constant:
        return "constants"
    elif symbol.is_utility:
        return "utils"
    else:
        return "common"

Managing Feature Flags
Graph-sitter has been used in production for multi-million line codebases to automatically delete “dead” (rolled-out) feature flags. This guide will walk you through analyzing feature flag usage and safely removing rolled out flags.

Every codebase does feature flags differently. This guide shows common techniques and syntax but likely requires adaptation to codebase-specific circumstances.

​
Analyzing Feature Flag Usage
Before removing a feature flag, it’s important to analyze its usage across the codebase. Graph-sitter provides tools to help identify where and how feature flags are used.

​
For Python Codebases
For Python codebases using a FeatureFlags class pattern like so:


Copy
class FeatureFlags:
    FEATURE_1 = False
    FEATURE_2 = True
You can use Class.get_attribute(…) and Attribute.usages to analyze the coverage of your flags, like so:


Copy
feature_flag_usage = {}
feature_flag_class = codebase.get_class('FeatureFlag')

if feature_flag_class:
    # Initialize usage count for all attributes
    for attr in feature_flag_class.attributes:
        feature_flag_usage[attr.name] = 0
    
    # Get all usages of the FeatureFlag class
    for usage in feature_flag_class.usages:
        usage_source = usage.usage_symbol.source if hasattr(usage, 'usage_symbol') else str(usage)
        for flag_name in feature_flag_usage.keys():
            if f"FeatureFlag.{flag_name}" in usage_source:
                feature_flag_usage[flag_name] += 1

    sorted_flags = sorted(feature_flag_usage.items(), key=lambda x: x[1], reverse=True)

    print("Feature Flag Usage Table:")
    print("-------------------------")
    print(f"{'Feature Flag':<30} | {'Usage Count':<12}")
    print("-" * 45)
    for flag, count in sorted_flags:
        print(f"{flag:<30} | {count:<12}")

    print(f"\nTotal feature flags: {len(sorted_flags)}")
else:
    print("❗ FeatureFlag enum not found in the codebase")
This will output a table showing all feature flags and their usage counts, helping identify which flags are candidates for removal.

Learn more about Attributes and tracking usages here

​
Removing Rolled Out Flags
Once you’ve identified a flag that’s ready to be removed, Graph-sitter can help safely delete it and its associated code paths.

This primarily leverages Codegen’s API for reduction conditions

​
Python Example
For Python codebases, here’s how to remove a feature flag and its usages:


Copy
flag_name = "FEATURE_TO_REMOVE"

# Get the feature flag variable
feature_flag_file = codebase.get_file("app/utils/feature_flags.py")
flag_class = feature_flag_file.get_class("FeatureFlag")

# Check if the flag exists
flag_var = flag_class.get_attribute(flag_name)
if not flag_var:
    print(f'No such flag: {flag_name}')
    return

# Remove all usages of the feature flag
for usage in flag_var.usages:
    if isinstance(usage.parent, IfBlockStatement):
        # For if statements, reduce the condition to True
        usage.parent.reduce_condition(True)
    elif isinstance(usage.parent, WithStatement):
        # For with statements, keep the code block
        usage.parent.code_block.unwrap()
    else:
        # For other cases, remove the usage
        usage.remove()

# Remove the flag definition
flag_var.remove()

# Commit changes
codebase.commit()
​
React/TypeScript Example
For React applications using a hooks-based feature flag system:


Copy
feature_flag_name = "NEW_UI_ENABLED"
target_value = True  # The value to reduce the flag to

print(f'Removing feature flag: {feature_flag_name}')

# 1. Remove from configuration
config_file = codebase.get_file("src/featureFlags/config.ts")
feature_flag_config = config_file.get_symbol("FEATURE_FLAG_CONFIG").value
if feature_flag_name in feature_flag_config.keys():
    feature_flag_config.pop(feature_flag_name)
    print('✅ Removed from feature flag config')

# 2. Find and reduce all hook usages
hook = codebase.get_function("useFeatureFlag")
for usage in hook.usages:
    fcall = usage.match
    if isinstance(fcall, FunctionCall):
        # Check if this usage is for our target flag
        first_arg = fcall.args[0].value
        if isinstance(first_arg, String) and first_arg.content == feature_flag_name:
            print(f'Reducing in: {fcall.parent_symbol.name}')
            # This automatically handles:
            # - Ternary expressions: flag ? <New /> : <Old />
            # - If statements: if (flag) { ... }
            # - Conditional rendering: {flag && <Component />}
            fcall.reduce_condition(target_value)

# 3. Commit changes
codebase.commit()
This will:

Remove the feature flag from the configuration
Find all usages of the useFeatureFlag hook for this flag
Automatically reduce any conditional logic using the flag
Handle common React patterns like ternaries and conditional rendering

Deleting Dead Code
Dead code refers to code that is not being used or referenced anywhere in your codebase.

However, it’s important to note that some code might appear unused but should not be deleted, including:

Test files and test functions
Functions with decorators (which may be called indirectly)
Public API endpoints
Event handlers or callback functions
Code used through reflection or dynamic imports
This guide will show you how to safely identify and remove genuinely unused code while preserving important functionality.

​
Overview
To simply identify code without any external usages, you can check for the absence of Symbol.usages.

See Dependencies and Usages for more information on how to use these properties.

Copy
# Iterate through all functions in the codebase
for function in codebase.functions:
    # Remove functions with no usages
    if not function.usages:
        function.remove()

# Commit
codebase.commit()
This will remove all code that is not explicitly referenced elsewhere, including tests, endpoints, etc. This is almost certainly not what you want. We recommend further filtering.

​
Filtering for Special Cases
To filter out special cases that are not explicitly referenced yet are, nonetheless, worth keeping around, you can use the following pattern:


Copy
for function in codebase.functions:

    # Skip test files
    if "test" in function.file.filepath:
        continue

    # Skip decorated functions
    if function.decorators:
        continue

    # Skip public routes, e.g. next.js endpoints
    # (Typescript only)
    if 'routes' in function.file.filepath and function.is_jsx:
        continue

    # ... etc.

    # Check if the function has no usages and no call sites
    if not function.usages and not function.call_sites:
        # Print a message indicating the removal of the function
        print(f"Removing unused function: {function.name}")
        # Remove the function from the file
        function.remove()

# Commit
codebase.commit()
​
Cleaning Up Unused Variables
To remove unused variables, you can check for their usages within their scope:

typescript

Copy
for func in codebase.functions:
    # Iterate through local variable assignments in the function
    for var_assignments in func.code_block.local_var_assignments:
        # Check if the local variable assignment has no usages
        if not var_assignments.local_usages:
            # Remove the local variable assignment
            var_assignments.remove()

# Commit
codebase.commit()
​
Cleaning Up After Removal
After removing dead code, you may need to clean up any remaining artifacts:


Copy
for file in codebase.files:
    # Check if the file is empty
    if not file.content.strip():
        # Print a message indicating the removal of the empty file
        print(f"Removing empty file: {file.filepath}")
        # Remove the empty file
        file.remove()

# commit is NECESSARY to remove the files from the codebase
codebase.commit()

# Remove redundant newlines
for file in codebase.files:
    # Replace three or more consecutive newlines with two newlines
    file.edit(re.sub(r"\n{3,}", "\n\n", file.content))

Increasing Type Coverage
This guide demonstrates how to analyze and manipulate type annotations with Codegen SDK.

Common use cases include:

Adding a type to a union or generic type
Checking if a generic type has a given subtype
Resolving a type annotation
Adding type hints can improve developer experience and significantly speed up programs like the Typescript compiler and mypy.

See Type Annotations for a general overview of the type maninpulation
​
APIs for monitoring types
Graph-sitter programs typically access type annotations through the following APIs:

Parameter.type
Function.return_type
Assignment.type
Each of these has an associated setter.

​
Finding the extent of your type coverage
To get an indication of your progress on type coverage, analyze the percentage of typed elements across your codebase


Copy
# Initialize counters for parameters
total_parameters = 0
typed_parameters = 0

# Initialize counters for return types
total_functions = 0
typed_returns = 0

# Initialize counters for class attributes
total_attributes = 0
typed_attributes = 0

# Count parameter and return type coverage
for function in codebase.functions:
    # Count parameters
    total_parameters += len(function.parameters)
    typed_parameters += sum(1 for param in function.parameters if param.is_typed)

    # Count return types
    total_functions += 1
    if function.return_type and function.return_type.is_typed:
        typed_returns += 1

# Count class attribute coverage
for cls in codebase.classes:
    for attr in cls.attributes:
        total_attributes += 1
        if attr.is_typed:
            typed_attributes += 1

# Calculate percentages
param_percentage = (typed_parameters / total_parameters * 100) if total_parameters > 0 else 0
return_percentage = (typed_returns / total_functions * 100) if total_functions > 0 else 0
attr_percentage = (typed_attributes / total_attributes * 100) if total_attributes > 0 else 0

# Print results
print("\nType Coverage Analysis")
print("---------------------")
print(f"Parameters: {param_percentage:.1f}% ({typed_parameters}/{total_parameters} typed)")
print(f"Return types: {return_percentage:.1f}% ({typed_returns}/{total_functions} typed)")
print(f"Class attributes: {attr_percentage:.1f}% ({typed_attributes}/{total_attributes} typed)")
This analysis gives you a breakdown of type coverage across three key areas:

Function parameters - Arguments passed to functions
Return types - Function return type annotations
Class attributes - Type hints on class variables
Focus first on adding types to the most frequently used functions and classes, as these will have the biggest impact on type checking and IDE support.

​
Adding simple return type annotations
To add a return type, use function.set_return_type. The script below will add a -> None return type to all functions that contain no return statements:


For Python

For Typescript

Copy
for file in codebase.files:
    # Check if 'app' is in the file's filepath
    if "app" in file.filepath:
        # Iterate through all functions in the file
        for function in file.functions:
            # Check if the function has no return statements
            if len(function.return_statements) == 0:
                # Set the return type to None
                function.set_return_type("None")
​
Coming Soon: Advanced Type Inference

Common Export Management Tasks
​
Collecting and Processing Exports
When reorganizing exports, the first step is identifying which exports need to be processed:


Copy
processed_imports = set()

for file in codebase.files:
    # Only process files under /src/shared
    if '/src/shared' not in file.filepath:
        continue

    # Gather all reexports that are not external exports
    all_reexports = []
    for export_stmt in file.export_statements:
        for export in export_stmt.exports:
            if export.is_reexport() and not export.is_external_export:
                all_reexports.append(export)

    # Skip if there are none
    if not all_reexports:
        continue
​
Moving Exports to Public Files
When centralizing exports in public-facing files:


Copy
# Replace "src/" with "src/shared/"
resolved_public_file = export.resolved_symbol.filepath.replace("src/", "src/shared/")

# Get relative path from the "public" file back to the original file
relative_path = codebase.get_relative_path(
    from_file=resolved_public_file,
    to_file=export.resolved_symbol.filepath
)

# Ensure the "public" file exists
if not codebase.has_file(resolved_public_file):
    target_file = codebase.create_file(resolved_public_file, sync=True)
else:
    target_file = codebase.get_file(resolved_public_file)

# If target file already has a wildcard export for this relative path, skip
if target_file.has_export_statement_for_path(relative_path, "WILDCARD"):
    has_wildcard = True
    continue
​
Managing Different Export Types
Graph-sitter can handle all types of exports automatically:


Wildcard Exports


Type Exports


Named Exports

​
Updating Import References
After moving exports, you need to update all import references:


Copy
# Now update all import usages that refer to this export
for usage in export.symbol_usages():
    if isinstance(usage, TSImport) and usage not in processed_imports:
        processed_imports.add(usage)

        # Translate the resolved_public_file to the usage file's TS config import path
        new_path = usage.file.ts_config.translate_import_path(resolved_public_file)

        if has_wildcard and export.name != export.resolved_symbol.name:
            name = f"{export.resolved_symbol.name} as {export.name}"
        else:
            name = usage.name

        if usage.is_type_import():
            new_import = f'import type {{ {name} }} from "{new_path}"'
        else:
            new_import = f'import {{ {name} }} from "{new_path}"'

        usage.file.insert_before(new_import)
        usage.remove()

# Remove the old export from the original file
export.remove()

# If the file ends up with no exports, remove it entirely
if not file.export_statements and len(file.symbols) == 0:
    file.remove()
​
Best Practices
Check for Wildcards First: Always check for existing wildcard exports before adding new ones:

Copy
if target_file.has_export_statement_for_path(relative_path, "WILDCARD"):
    has_wildcard = True
    continue
Handle Path Translations: Use TypeScript config for path translations:

Copy
new_path = usage.file.ts_config.translate_import_path(resolved_public_file)
Clean Up Empty Files: Remove files that no longer contain exports or symbols:

Copy
if not file.export_statements and len(file.symbols) == 0:
    file.remove()
​
Next Steps
After reorganizing your exports:

Run your test suite to verify everything still works
Review the generated import statements
Check for any empty files that should be removed
Verify that all export types (wildcard, type, named) are working as expected
Remember that managing exports is an iterative process. You may need to run the codemod multiple times as your codebase evolves.

​
Related tutorials
Moving symbols
Exports
Dependencies and usages
​
Complete Codemod
Here’s the complete codemod that you can copy and use directly:


Copy
processed_imports = set()

for file in codebase.files:
    # Only process files under /src/shared
    if '/src/shared' not in file.filepath:
        continue

    # Gather all reexports that are not external exports
    all_reexports = []
    for export_stmt in file.export_statements:
        for export in export_stmt.exports:
            if export.is_reexport() and not export.is_external_export:
                all_reexports.append(export)

    # Skip if there are none
    if not all_reexports:
        continue

    for export in all_reexports:
        has_wildcard = False

        # Replace "src/" with "src/shared/"
        resolved_public_file = export.resolved_symbol.filepath.replace("src/", "src/shared/")

        # Get relative path from the "public" file back to the original file
        relative_path = codebase.get_relative_path(
            from_file=resolved_public_file,
            to_file=export.resolved_symbol.filepath
        )

        # Ensure the "public" file exists
        if not codebase.has_file(resolved_public_file):
            target_file = codebase.create_file(resolved_public_file, sync=True)
        else:
            target_file = codebase.get_file(resolved_public_file)

        # If target file already has a wildcard export for this relative path, skip
        if target_file.has_export_statement_for_path(relative_path, "WILDCARD"):
            has_wildcard = True
            continue

        # Compare "public" path to the local file's export.filepath
        if codebase._remove_extension(resolved_public_file) != codebase._remove_extension(export.filepath):

            # A) Wildcard export, e.g. `export * from "..."`
            if export.is_wildcard_export():
                target_file.insert_before(f'export * from "{relative_path}"')

            # B) Type export, e.g. `export type { Foo, Bar } from "..."`
            elif export.is_type_export():
                # Does this file already have a type export statement for the path?
                statement = file.get_export_statement_for_path(relative_path, "TYPE")
                if statement:
                    # Insert into existing statement
                    if export.is_aliased():
                        statement.insert(0, f"{export.resolved_symbol.name} as {export.name}")
                    else:
                        statement.insert(0, f"{export.name}")
                else:
                    # Insert a new type export statement
                    if export.is_aliased():
                        target_file.insert_before(
                            f'export type {{ {export.resolved_symbol.name} as {export.name} }} '
                            f'from "{relative_path}"'
                        )
                    else:
                        target_file.insert_before(
                            f'export type {{ {export.name} }} from "{relative_path}"'
                        )

            # C) Normal export, e.g. `export { Foo, Bar } from "..."`
            else:
                statement = file.get_export_statement_for_path(relative_path, "EXPORT")
                if statement:
                    # Insert into existing statement
                    if export.is_aliased():
                        statement.insert(0, f"{export.resolved_symbol.name} as {export.name}")
                    else:
                        statement.insert(0, f"{export.name}")
                else:
                    # Insert a brand-new normal export statement
                    if export.is_aliased():
                        target_file.insert_before(
                            f'export {{ {export.resolved_symbol.name} as {export.name} }} '
                            f'from "{relative_path}"'
                        )
                    else:
                        target_file.insert_before(
                            f'export {{ {export.name} }} from "{relative_path}"'
                        )

        # Now update all import usages that refer to this export
        for usage in export.symbol_usages():
            if isinstance(usage, TSImport) and usage not in processed_imports:
                processed_imports.add(usage)

                # Translate the resolved_public_file to the usage file's TS config import path
                new_path = usage.file.ts_config.translate_import_path(resolved_public_file)

                if has_wildcard and export.name != export.resolved_symbol.name:
                    name = f"{export.resolved_symbol.name} as {export.name}"
                else:
                    name = usage.name

                if usage.is_type_import():
                    new_import = f'import type {{ {name} }} from "{new_path}"'
                else:
                    new_import = f'import {{ {name} }} from "{new_path}"'

                usage.file.insert_before(new_import)
                usage.remove()

        # Remove the old export from the original file
        export.remove()

    # If the file ends up with no exports, remove it entirely
    if not file.export_statements and len(file.symbols) == 0:
        file.remove()
Converting Default Exports
Convert default exports to named exports in your TypeScript codebase

Graph-sitter provides tools to help you migrate away from default exports to named exports in your TypeScript codebase. This tutorial builds on the concepts covered in exports to show you how to automate this conversion process.

​
Overview
Default exports can make code harder to maintain and refactor. Converting them to named exports provides several benefits:

Better IDE support for imports and refactoring
More explicit and consistent import statements
Easier to track symbol usage across the codebase
​
Converting Default Exports
Here’s how to convert default exports to named exports:


Copy
for file in codebase.files:
    target_file = file.filepath
    if not target_file:
        print(f"⚠️ Target file not found: {filepath}")
        continue

    # Get corresponding non-shared file
    non_shared_path = target_file.filepath.replace('/shared/', '/')
    if not codebase.has_file(non_shared_path):
        print(f"⚠️ No matching non-shared file for: {filepath}")
        continue

    non_shared_file = codebase.get_file(non_shared_path)
    print(f"📄 Processing {target_file.filepath}")

    # Process individual exports
    for export in target_file.exports:
        # Handle default exports
        if export.is_reexport() and export.is_default_export():
            print(f"  🔄 Converting default export '{export.name}'")
            default_export = next((e for e in non_shared_file.default_exports), None)
            if default_export:
                default_export.make_non_default()

    print(f"✨ Fixed exports in {target_file.filepath}")
​
Understanding the Process
Let’s break down how this works:


Finding Default Exports


Converting to Named Exports


File Path Handling

​
Best Practices
Check for Missing Files: Always verify files exist before processing:

Copy
if not target_file:
    print(f"⚠️ Target file not found: {filepath}")
    continue
Log Progress: Add logging to track the conversion process:

Copy
print(f"📄 Processing {target_file.filepath}")
print(f"  🔄 Converting default export '{export.name}'")
Handle Missing Exports: Check that default exports exist before converting:

Copy
default_export = next((e for e in non_shared_file.default_exports), None)
if default_export:
    default_export.make_non_default()
​
Next Steps
After converting default exports:

Run your test suite to verify everything still works
Update any import statements that were using default imports
Review the changes to ensure all exports were converted correctly
Consider adding ESLint rules to prevent new default exports
Remember to test thoroughly after converting default exports, as this change affects how other files import the converted modules.

​
Related tutorials
Managing typescript exports
Exports
Dependencies and usages
​
Complete Codemod
Here’s the complete codemod that you can copy and use directly:


Copy
for file in codebase.files:
    target_file = file.filepath
    if not target_file:
        print(f"⚠️ Target file not found: {filepath}")
        continue

    # Get corresponding non-shared file
    non_shared_path = target_file.filepath.replace('/shared/', '/')
    if not codebase.has_file(non_shared_path):
        print(f"⚠️ No matching non-shared file for: {filepath}")
        continue

    non_shared_file = codebase.get_file(non_shared_path)
    print(f"📄 Processing {target_file.filepath}")

    # Process individual exports
    for export in target_file.exports:
        # Handle default exports
        if export.is_reexport() and export.is_default_export():
            print(f"  🔄 Converting default export '{export.name}'")
            default_export = next((e for e in non_shared_file.default_exports), None)
            if default_export:
                default_export.make_non_default()

    print(f"✨ Fixed exports in {target_file.filepath}")
Was this page helpful?


Yes

No


Creating Documentation
This guide demonstrates how to determine docs coverage and create documentation for your codebase.

This primarily leverages two APIs:

codebase.ai(…) for generating docstrings
function.set_docstring(…) for modifying them
​
Determining Documentation Coverage
In order to determine the extent of your documentation coverage, you can iterate through all symbols of interest and count the number of docstrings:

To see your current documentation coverage, you can iterate through all symbols of interest and count the number of docstrings:

python

Copy
# Initialize counters
total_functions = 0
functions_with_docs = 0
total_classes = 0
classes_with_docs = 0

# Check functions
for function in codebase.functions:
    total_functions += 1
    if function.docstring:
        functions_with_docs += 1

# Check classes
for cls in codebase.classes:
    total_classes += 1
    if cls.docstring:
        classes_with_docs += 1

# Calculate percentages
func_coverage = (functions_with_docs / total_functions * 100) if total_functions > 0 else 0
class_coverage = (classes_with_docs / total_classes * 100) if total_classes > 0 else 0

# Print results with emojis
print("\n📊 Documentation Coverage Report:")
print(f"\n📝 Functions:")
print(f"  • Total: {total_functions}")
print(f"  • Documented: {functions_with_docs}")
print(f"  • Coverage: {func_coverage:.1f}%")

print(f"\n📚 Classes:")
print(f"  • Total: {total_classes}")
print(f"  • Documented: {classes_with_docs}")
print(f"  • Coverage: {class_coverage:.1f}%")

print(f"\n🎯 Overall Coverage: {((functions_with_docs + classes_with_docs) / (total_functions + total_classes) * 100):.1f}%")
Which provides the following output:


Copy
📊 Documentation Coverage Report:
📝 Functions:
  • Total: 1384
  • Documented: 331
  • Coverage: 23.9%
📚 Classes:
  • Total: 453
  • Documented: 91
  • Coverage: 20.1%
🎯 Overall Coverage: 23.0%
​
Identifying Areas of Low Documentation Coverage
To identify areas of low documentation coverage, you can iterate through all directories and count the number of functions with docstrings.

Learn more about Directories here.
python

Copy
# Track directory stats
dir_stats = {}

# Analyze each directory
for directory in codebase.directories:
    # Skip test, sql and alembic directories
    if any(x in directory.path.lower() for x in ['test', 'sql', 'alembic']):
        continue
        
    # Get undecorated functions
    funcs = [f for f in directory.functions if not f.is_decorated]
    total = len(funcs)
    
    # Only analyze dirs with >10 functions
    if total > 10:
        documented = sum(1 for f in funcs if f.docstring)
        coverage = (documented / total * 100)
        dir_stats[directory.path] = {
            'total': total,
            'documented': documented,
            'coverage': coverage
        }

# Find lowest coverage directory
if dir_stats:
    lowest_dir = min(dir_stats.items(), key=lambda x: x[1]['coverage'])
    path, stats = lowest_dir
    
    print(f"📉 Lowest coverage directory: '{path}'")
    print(f"  • Total functions: {stats['total']}")
    print(f"  • Documented: {stats['documented']}")
    print(f"  • Coverage: {stats['coverage']:.1f}%")
    
    # Print all directory stats for comparison
    print("\n📊 All directory coverage rates:")
    for path, stats in sorted(dir_stats.items(), key=lambda x: x[1]['coverage']):
        print(f"  '{path}': {stats['coverage']:.1f}% ({stats['documented']}/{stats['total']} functions)")
Which provides the following output:


Copy
📉 Lowest coverage directory: 'codegen-backend/app/utils/github_utils/branch'
  • Total functions: 12
  • Documented: 0
  • Coverage: 0.0%
📊 All directory coverage rates:
  'codegen-backend/app/utils/github_utils/branch': 0.0% (0/12 functions)
  'codegen-backend/app/utils/slack': 14.3% (2/14 functions)
  'codegen-backend/app/modal_app/github': 18.2% (2/11 functions)
  'codegen-backend/app/modal_app/slack': 18.2% (2/11 functions)
  'codegen-backend/app/utils/github_utils/webhook': 21.4% (6/28 functions)
  'codegen-backend/app/modal_app/cron': 23.1% (3/13 functions)
  'codegen-backend/app/utils/github_utils': 23.5% (39/166 functions)
  'codegen-backend/app/codemod': 25.0% (7/28 functions)
​
Leveraging AI for Generating Documentation
For non-trivial codebases, it can be challenging to achieve full documentation coverage.

The most efficient way to edit informative docstrings is to use codebase.ai to generate docstrings, then use the set_docstring method to update the docstring.

Learn more about using AI in our guides.
python

Copy
# Import datetime for timestamp
from datetime import datetime

# Get current timestamp
timestamp = datetime.now().strftime("%B %d, %Y")

print("📚 Generating and Updating Function Documentation")

# Process all functions in the codebase
for function in codebase.functions:
    current_docstring = function.docstring()

    if current_docstring:
        # Update existing docstring to be more descriptive
        new_docstring = codebase.ai(
            f"Update the docstring for {function.name} to be more descriptive and comprehensive.",
            target=function
        )
        new_docstring += f"\n\nUpdated on: {timestamp}"
    else:
        # Generate new docstring for function
        new_docstring = codebase.ai(
            f"Generate a comprehensive docstring for {function.name} including parameters, return type, and description.",
            target=function
        )
        new_docstring += f"\n\nCreated on: {timestamp}"

    # Set the new or updated docstring
    function.set_docstring(new_docstring)
​
Adding Explicit Parameter Names and Types
Alternatively, you can also rely on deterministic string formatting to edit docstrings.

To add “Google-style” parameter names and types to a function docstring, you can use the following code snippet:

python

Copy
# Iterate through all functions in the codebase
for function in codebase.functions:
    # Skip if function already has a docstring
    if function.docstring:
        continue

    # Build parameter documentation
    param_docs = []
    for param in function.parameters:
        param_type = param.type.source if param.is_typed else "Any"
        param_docs.append(f"    {param.name} ({param_type}): Description of {param.name}")

    # Get return type if present
    return_type = function.return_type.source if function.return_type else "None"

    # Create Google-style docstring
    docstring = f'''"""
    Description of {function.name}.

    Args:
{chr(10).join(param_docs)}

    Returns:
        {return_type}: Description of return value
    """'''

    # Set the new docstring
    function.set_docstring(docstring)

React Modernization
Modernize your React codebase with Codegen

Codegen SDK provides powerful APIs for modernizing React codebases. This guide will walk you through common React modernization patterns.

Common use cases include:

Upgrading to modern APIs, including React 18+
Automatically memoizing components
Converting to modern hooks
Standardizing prop types
Organizing components into individual files
and much more.

​
Converting Class Components to Functions
Here’s how to convert React class components to functional components:


Copy
# Find all React class components
for class_def in codebase.classes:
    # Skip if not a React component
    if not class_def.is_jsx or "Component" not in [base.name for base in class_def.bases]:
        continue

    print(f"Converting {class_def.name} to functional component")

    # Extract state from constructor
    constructor = class_def.get_method("constructor")
    state_properties = []
    if constructor:
        for statement in constructor.code_block.statements:
            if "this.state" in statement.source:
                # Extract state properties
                state_properties = [prop.strip() for prop in
                    statement.source.split("{")[1].split("}")[0].split(",")]

    # Create useState hooks for each state property
    state_hooks = []
    for prop in state_properties:
        hook_name = f"[{prop}, set{prop[0].upper()}{prop[1:]}]"
        state_hooks.append(f"const {hook_name} = useState(null);")

    # Convert lifecycle methods to effects
    effects = []
    if class_def.get_method("componentDidMount"):
        effects.append("""
    useEffect(() => {
        // TODO: Move componentDidMount logic here
    }, []);
    """)

    if class_def.get_method("componentDidUpdate"):
        effects.append("""
    useEffect(() => {
        // TODO: Move componentDidUpdate logic here
    });
    """)

    # Get the render method
    render_method = class_def.get_method("render")

    # Create the functional component
    func_component = f"""
const {class_def.name} = ({class_def.get_method("render").parameters[0].name}) => {{
    {chr(10).join(state_hooks)}
    {chr(10).join(effects)}

    {render_method.code_block.source}
}}
"""

    # Replace the class with the functional component
    class_def.edit(func_component)

    # Add required imports
    file = class_def.file
    if not any("useState" in imp.source for imp in file.imports):
        file.add_import("import { useState, useEffect } from 'react';")
​
Migrating to Modern Hooks
Convert legacy patterns to modern React hooks:


Copy
# Find components using legacy patterns
for function in codebase.functions:
    if not function.is_jsx:
        continue

    # Look for common legacy patterns
    for call in function.function_calls:
        # Convert withRouter to useNavigate
        if call.name == "withRouter":
            # Add useNavigate import
            function.file.add_import(
                "import { useNavigate } from 'react-router-dom';"
            )
            # Add navigate hook
            function.insert_before_first_return("const navigate = useNavigate();")
            # Replace history.push calls
            for history_call in function.function_calls:
                if "history.push" in history_call.source:
                    history_call.edit(
                        history_call.source.replace("history.push", "navigate")
                    )

        # Convert lifecycle methods in hooks
        elif call.name == "componentDidMount":
            call.parent.edit("""
useEffect(() => {
    // Your componentDidMount logic here
}, []);
""")
​
Standardizing Props
​
Inferring Props from Usage
Add proper prop types and TypeScript interfaces based on how props are used:


Copy
# Add TypeScript interfaces for props
for function in codebase.functions:
    if not function.is_jsx:
        continue

    # Get props parameter
    props_param = function.parameters[0] if function.parameters else None
    if not props_param:
        continue

    # Collect used props
    used_props = set()
    for prop_access in function.function_calls:
        if f"{props_param.name}." in prop_access.source:
            prop_name = prop_access.source.split(".")[1]
            used_props.add(prop_name)

    # Create interface
    if used_props:
        interface_def = f"""
interface {function.name}Props {{
    {chr(10).join(f'    {prop}: any;' for prop in used_props)}
}}
"""
        function.insert_before(interface_def)
        # Update function signature
        function.edit(function.source.replace(
            f"({props_param.name})",
            f"({props_param.name}: {function.name}Props)"
        ))
​
Extracting Inline Props
Convert inline prop type definitions to separate type declarations:


Copy
# Iterate over all files in the codebase
for file in codebase.files:
    # Iterate over all functions in the file
    for function in file.functions:
        # Check if the function is a React functional component
        if function.is_jsx:  # Assuming is_jsx indicates a function component
            # Check if the function has inline props definition
            if len(function.parameters) == 1 and isinstance(function.parameters[0].type, Dict):
                # Extract the inline prop type
                inline_props: TSObjectType = function.parameters[0].type.source
                # Create a new type definition for the props
                props_type_name = f"{function.name}Props"
                props_type_definition = f"type {props_type_name} = {inline_props};"

                # Set the new type for the parameter
                function.parameters[0].set_type_annotation(props_type_name)
                # Add the new type definition to the file
                function.insert_before('\n' + props_type_definition + '\n')
This will convert components from:


Copy
function UserCard({ name, age }: { name: string; age: number }) {
  return (
    <div>
      {name} ({age})
    </div>
  );
}
To:


Copy
type UserCardProps = { name: string; age: number };

function UserCard({ name, age }: UserCardProps) {
  return (
    <div>
      {name} ({age})
    </div>
  );
}
Extracting prop types makes them reusable and easier to maintain. It also improves code readability by separating type definitions from component logic.

​
Updating Fragment Syntax
Modernize React Fragment syntax:


Copy
for function in codebase.functions:
    if not function.is_jsx:
        continue

    # Replace React.Fragment with <>
    for element in function.jsx_elements:
        if element.name == "React.Fragment":
            element.edit(element.source.replace(
                "<React.Fragment>",
                "<>"
            ).replace(
                "</React.Fragment>",
                "</>"
            ))
​
Organizing Components into Individual Files
A common modernization task is splitting files with multiple components into a more maintainable structure where each component has its own file. This is especially useful when modernizing legacy React codebases that might have grown organically.


Copy
# Initialize a dictionary to store files and their corresponding JSX components
files_with_jsx_components = {}

# Iterate through all files in the codebase
for file in codebase.files:
    # Check if the file is in the components directory
    if 'components' not in file.filepath:
        continue

    # Count the number of JSX components in the file
    jsx_count = sum(1 for function in file.functions if function.is_jsx)

    # Only proceed if there are multiple JSX components
    if jsx_count > 1:
        # Identify non-default exported components
        non_default_components = [
            func for func in file.functions
            if func.is_jsx and not func.is_exported
        ]
        default_components = [
            func for func in file.functions
            if func.is_jsx and func.is_exported and func.export.is_default_export()
        ]

        # Log the file path and its components
        print(f"📁 {file.filepath}:")
        for component in default_components:
            print(f"  🟢 {component.name} (default)")
        for component in non_default_components:
            print(f"  🔵 {component.name}")

            # Create a new directory path based on the original file's directory
            new_dir_path = "/".join(file.filepath.split("/")[:-1]) + "/" + file.name.split(".")[0]
            codebase.create_directory(new_dir_path, exist_ok=True)

            # Create a new file path for the component
            new_file_path = f"{new_dir_path}/{component.name}.tsx"
            new_file = codebase.create_file(new_file_path)

            # Log the movement of the component
            print(f"    🫸 Moved to: {new_file_path}")

            # Move the component to the new file
            component.move_to_file(new_file, strategy="add_back_edge")
This script will:

Find files containing multiple React components
Create a new directory structure based on the original file
Move each non-default exported component to its own file
Preserve imports and dependencies automatically
Keep default exports in their original location
For example, given this structure:


Copy
components/
  Forms.tsx  # Contains Button, Input, Form (default)
It will create:


Copy
components/
  Forms.tsx  # Contains Form (default)
  forms/
    Button.tsx
    Input.tsx

Migrating from unittest to pytest
Learn how to migrate unittest test suites to pytest using Codegen

Migrating from unittest to pytest involves converting test classes and assertions to pytest’s more modern and concise style. This guide will walk you through using Graph-sitter to automate this migration.

You can find the complete example code in our examples repository.

​
Overview
The migration process involves four main steps:

Converting test class inheritance and setup/teardown methods
Updating assertions to pytest style
Converting test discovery patterns
Modernizing fixture usage
Let’s walk through each step using Codegen.

​
Step 1: Convert Test Classes and Setup Methods
The first step is to convert unittest’s class-based tests to pytest’s function-based style. This includes:

Removing unittest.TestCase inheritance
Converting setUp and tearDown methods to fixtures
Updating class-level setup methods

Copy
# From:
class TestUsers(unittest.TestCase):
    def setUp(self):
        self.db = setup_test_db()

    def tearDown(self):
        self.db.cleanup()

    def test_create_user(self):
        user = self.db.create_user("test")
        self.assertEqual(user.name, "test")

# To:
import pytest

@pytest.fixture
def db():
    db = setup_test_db()
    yield db
    db.cleanup()

def test_create_user(db):
    user = db.create_user("test")
    assert user.name == "test"
​
Step 2: Update Assertions
Next, we’ll convert unittest’s assertion methods to pytest’s plain assert statements:


Copy
# From:
def test_user_validation(self):
    self.assertTrue(is_valid_email("user@example.com"))
    self.assertFalse(is_valid_email("invalid"))
    self.assertEqual(get_user_count(), 0)
    self.assertIn("admin", get_roles())
    self.assertRaises(ValueError, parse_user_id, "invalid")

# To:
def test_user_validation():
    assert is_valid_email("user@example.com")
    assert not is_valid_email("invalid")
    assert get_user_count() == 0
    assert "admin" in get_roles()
    with pytest.raises(ValueError):
        parse_user_id("invalid")
​
Step 3: Update Test Discovery
pytest uses a different test discovery pattern than unittest. We’ll update the test file names and patterns:


Copy
# From:
if __name__ == '__main__':
    unittest.main()

# To:
# Remove the unittest.main() block entirely
# Rename test files to test_*.py or *_test.py
​
Step 4: Modernize Fixture Usage
Finally, we’ll update how test dependencies are managed using pytest’s powerful fixture system:


Copy
# From:
class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_conn = create_test_db()

    def setUp(self):
        self.transaction = self.db_conn.begin()

    def tearDown(self):
        self.transaction.rollback()

# To:
@pytest.fixture(scope="session")
def db_conn():
    return create_test_db()

@pytest.fixture
def transaction(db_conn):
    transaction = db_conn.begin()
    yield transaction
    transaction.rollback()
​
Common Patterns
Here are some common patterns you’ll encounter when migrating to pytest:

Parameterized Tests

Copy
# From:
def test_validation(self):
    test_cases = [("valid@email.com", True), ("invalid", False)]
    for email, expected in test_cases:
        with self.subTest(email=email):
            self.assertEqual(is_valid_email(email), expected)

# To:
@pytest.mark.parametrize("email,expected", [
    ("valid@email.com", True),
    ("invalid", False)
])
def test_validation(email, expected):
    assert is_valid_email(email) == expected
Exception Testing

Copy
# From:
def test_exceptions(self):
    self.assertRaises(ValueError, process_data, None)
    with self.assertRaises(TypeError):
        process_data(123)

# To:
def test_exceptions():
    with pytest.raises(ValueError):
        process_data(None)
    with pytest.raises(TypeError):
        process_data(123)
Temporary Resources

Copy
# From:
def setUp(self):
    self.temp_dir = tempfile.mkdtemp()

def tearDown(self):
    shutil.rmtree(self.temp_dir)

# To:
@pytest.fixture
def temp_dir():
    dir = tempfile.mkdtemp()
    yield dir
    shutil.rmtree(dir)
​
Tips and Notes
pytest fixtures are more flexible than unittest’s setup/teardown methods:

They can be shared across test files
They support different scopes (function, class, module, session)
They can be parameterized
pytest’s assertion introspection provides better error messages by default:


Copy
# pytest shows a detailed comparison
assert result == expected
You can gradually migrate to pytest:

pytest can run unittest-style tests
Convert one test file at a time
Start with assertion style updates before moving to fixtures
Consider using pytest’s built-in fixtures:

tmp_path for temporary directories
capsys for capturing stdout/stderr
monkeypatch for modifying objects
caplog for capturing log messages
Was this page helpful?


Overview
The steps to identify and fix import loops are as follows:

Detect import loops
Visualize them
Identify problematic cycles with mixed static/dynamic imports
Fix these cycles using Codegen
​
Step 1: Detect Import Loops
Create a graph
Loop through imports in the codebase and add edges between the import files
Find strongly connected components using Networkx (the import loops)

Copy
G = nx.MultiDiGraph()

# Add all edges to the graph
for imp in codebase.imports:
    if imp.from_file and imp.to_file:
        edge_color = "red" if imp.is_dynamic else "black"
        edge_label = "dynamic" if imp.is_dynamic else "static"

        # Store the import statement and its metadata
        G.add_edge(
            imp.to_file.filepath,
            imp.from_file.filepath,
            color=edge_color,
            label=edge_label,
            is_dynamic=imp.is_dynamic,
            import_statement=imp,  # Store the whole import object
            key=id(imp.import_statement),
        )
# Find strongly connected components
cycles = [scc for scc in nx.strongly_connected_components(G) if len(scc) > 1]

print(f"🔄 Found {len(cycles)} import cycles:")
for i, cycle in enumerate(cycles, 1):
    print(f"\nCycle #{i}:")
    print(f"Size: {len(cycle)} files")

    # Create subgraph for this cycle to count edges
    cycle_subgraph = G.subgraph(cycle)

    # Count total edges
    total_edges = cycle_subgraph.number_of_edges()
    print(f"Total number of imports in cycle: {total_edges}")

    # Count dynamic and static imports separately
    dynamic_imports = sum(1 for u, v, data in cycle_subgraph.edges(data=True) if data.get("color") == "red")
    static_imports = sum(1 for u, v, data in cycle_subgraph.edges(data=True) if data.get("color") == "black")

    print(f"Number of dynamic imports: {dynamic_imports}")
    print(f"Number of static imports: {static_imports}")
​
Understanding Import Cycles
Not all import cycles are problematic! Here’s an example of a cycle that one may think would cause an error but it does not because due to using dynamic imports.


Copy
# top level import in in APoT_tensor.py
from quantizer.py import objectA

Copy
# dynamic import in quantizer.py
def some_func():
    # dynamic import (evaluated when some_func() is called)
    from APoT_tensor.py import objectB

A dynamic import is an import defined inside of a function, method or any executable body of code which delays the import execution until that function, method or body of code is called.

You can use Import.is_dynamic to check if the import is dynamic allowing you to investigate imports that are handled more intentionally.

​
Step 2: Visualize Import Loops
Create a new subgraph to visualize one cycle
color and label the edges based on their type (dynamic/static)
visualize the cycle graph using codebase.visualize(graph)
Learn more about codebase visualization here

Copy
cycle = cycles[0]

def create_single_loop_graph(cycle):
    cycle_graph = nx.MultiDiGraph()  # Changed to MultiDiGraph to support multiple edges
    cycle = list(cycle)
    for i in range(len(cycle)):
        for j in range(len(cycle)):
            # Get all edges between these nodes from original graph
            edge_data_dict = G.get_edge_data(cycle[i], cycle[j])
            if edge_data_dict:
                # For each edge between these nodes
                for edge_key, edge_data in edge_data_dict.items():
                    # Add edge with all its attributes to cycle graph
                    cycle_graph.add_edge(cycle[i], cycle[j], **edge_data)
    return cycle_graph


cycle_graph = create_single_loop_graph(cycle)
codebase.visualize(cycle_graph)

Import loops in pytorch/torchgen/model.py

​
Step 3: Identify problematic cycles with mixed static & dynamic imports
The import loops that we are really concerned about are those that have mixed static/dynamic imports.

Here’s an example of a problematic cycle that we want to fix:


Copy
# In flex_decoding.py
from .flex_attention import (
    compute_forward_block_mn,
    compute_forward_inner,
    # ... more static imports
)

# Also in flex_decoding.py
def create_flex_decoding_kernel(*args, **kwargs):
    from .flex_attention import set_head_dim_values  # dynamic import
It’s clear that there is both a top level and a dynamic import that imports from the same module. Thus, this can cause issues if not handled carefully.


Let’s find these problematic cycles:


Copy
def find_problematic_import_loops(G, sccs):
    """Find cycles where files have both static and dynamic imports between them."""
    problematic_cycles = []

    for i, scc in enumerate(sccs):
        if i == 2:  # skipping the second import loop as it's incredibly long (it's also invalid)
            continue
        mixed_import_files = {}  # (from_file, to_file) -> {dynamic: count, static: count}

        # Check all file pairs in the cycle
        for from_file in scc:
            for to_file in scc:
                if G.has_edge(from_file, to_file):
                    # Get all edges between these files
                    edges = G.get_edge_data(from_file, to_file)

                    # Count imports by type
                    dynamic_count = sum(1 for e in edges.values() if e["color"] == "red")
                    static_count = sum(1 for e in edges.values() if e["color"] == "black")

                    # If we have both types between same files, this is problematic
                    if dynamic_count > 0 and static_count > 0:
                        mixed_import_files[(from_file, to_file)] = {"dynamic": dynamic_count, "static": static_count, "edges": edges}

        if mixed_import_files:
            problematic_cycles.append({"files": scc, "mixed_imports": mixed_import_files, "index": i})

    # Print findings
    print(f"Found {len(problematic_cycles)} cycles with mixed imports:")
    for i, cycle in enumerate(problematic_cycles):
        print(f"\n⚠️  Problematic Cycle #{i + 1}:")
        print(f"\n⚠️  Index #{cycle['index']}:")
        print(f"Size: {len(cycle['files'])} files")

        for (from_file, to_file), data in cycle["mixed_imports"].items():
            print("\n📁 Mixed imports detected:")
            print(f"  From: {from_file}")
            print(f"  To:   {to_file}")
            print(f"  Dynamic imports: {data['dynamic']}")
            print(f"  Static imports: {data['static']}")

    return problematic_cycles

problematic_cycles = find_problematic_import_loops(G, cycles)
​
Step 4: Fix the loop by moving the shared symbols to a separate utils.py file
One common fix to this problem to break this cycle is to move all the shared symbols to a separate utils.py file. We can do this using the method symbol.move_to_file:

Learn more about moving symbols here

Copy
# Create new utils file
utils_file = codebase.create_file("torch/_inductor/kernel/flex_utils.py")

# Get the two files involved in the import cycle
decoding_file = codebase.get_file("torch/_inductor/kernel/flex_decoding.py")
attention_file = codebase.get_file("torch/_inductor/kernel/flex_attention.py")
attention_file_path = "torch/_inductor/kernel/flex_attention.py"
decoding_file_path = "torch/_inductor/kernel/flex_decoding.py"

# Track symbols to move
symbols_to_move = set()

# Find imports from flex_attention in flex_decoding
for imp in decoding_file.imports:
    if imp.from_file and imp.from_file.filepath == attention_file_path:
        # Get the actual symbol from flex_attention
        if imp.imported_symbol:
            symbols_to_move.add(imp.imported_symbol)

# Move identified symbols to utils file
for symbol in symbols_to_move:
    symbol.move_to_file(utils_file)

print(f"🔄 Moved {len(symbols_to_move)} symbols to flex_utils.py")
for symbol in symbols_to_move:
    print(symbol.name)

# Commit changes
codebase.commit()
​
Conclusions & Next Steps
Import loops can be tricky to identify and fix, but Graph-sitter provides powerful tools to help manage them:

Use codebase.imports to analyze import relationships across your project
Visualize import cycles to better understand dependencies
Distinguish between static and dynamic imports using Import.is_dynamic
Move shared symbols to break cycles using symbol.move_to_file
Here are some next steps you can take:

Analyze Your Codebase: Run similar analysis on your own codebase to identify potential import cycles
Create Import Guidelines: Establish best practices for your team around when to use static vs dynamic imports
Automate Fixes: Create scripts to automatically detect and fix problematic import patterns
Monitor Changes: Set up CI checks to prevent new problematic import cycles from being introduced

Building a Model Context Protocol server with Codegen
Learn how to build a Model Context Protocol (MCP) server that enables AI models to understand and manipulate code using Codegen’s powerful tools.

This guide will walk you through creating an MCP server that can provide semantic code search

View the full code in our examples repository
​
Setup:
Install the MCP python library


Copy
uv pip install mcp
​
Step 1: Setting Up Your MCP Server
First, let’s create a basic MCP server using Codegen’s MCP tools:

server.py


Copy
from graph_sitter import Codebase
from mcp.server.fastmcp import FastMCP
from typing import Annotated
# Initialize the codebase
codebase = Codebase.from_repo(".")

# create the MCP server using FastMCP
mcp = FastMCP(name="demo-mcp", instructions="Use this server for semantic search of codebases")


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting demo mpc server...")
    mcp.run(transport="stdio")
​
Step 2: Create the search tool
Let’s implement the semantic search tool.

server.py


Copy
from graph_sitter.extensions.tools.semantic_search import semantic_search

....

@mcp.tool('codebase_semantic_search', "search codebase with the provided query")
def search(query: Annotated[str, "search query to run against codebase"]):
  codebase = Codebase("provide location to codebase", language="provide codebase Language")
  # use the semantic search tool from graph_sitter.extensions.tools OR write your own
  results = semantic_search(codebase=codebase, query=query)
  return results

....
​
Run Your MCP Server
You can run and inspect your MCP server with:


Copy
mcp dev server.py

Neo4j Graph
Graph-sitter can export codebase graphs to Neo4j for visualization and analysis.

​
Installation
In order to use Neo4j you will need to install it and run it locally using Docker.

​
Neo4j
First, install Neo4j using the official installation guide.

​
Docker
To run Neo4j locally using Docker, follow the instructions here.

​
Launch Neo4j Locally

Copy
docker run \
    -p 7474:7474 -p 7687:7687 \
    -v $PWD/data:/data -v $PWD/plugins:/plugins \
    --name neo4j-apoc \
    -e NEO4J_apoc_export_file_enabled=true \
    -e NEO4J_apoc_import_file_enabled=true \
    -e NEO4J_apoc_import_file_use__neo4j__config=true \
    -e NEO4J_PLUGINS=\[\"apoc\"\] \
    neo4j:latest
​
Usage

Copy
from graph_sitter import Codebase
from graph_sitter.extensions.graph.main import visualize_codebase

# parse codebase
codebase = Codebase("path/to/codebase")

# export to Neo4j
visualize_codebase(codebase, "bolt://localhost:7687", "neo4j", "password")
​
Visualization
Once exported, you can open the Neo4j browser at http://localhost:7474, sign in with the username neo4j and the password password, and use the following Cypher queries to visualize the codebase:

​
Class Hierarchy

Copy
Match (s: Class )-[r: INHERITS_FROM*]-> (e:Class) RETURN s, e LIMIT 10

AI Impact Analysis
This tutorial shows how to use Codegen’s attribution extension to analyze the impact of AI on your codebase. You’ll learn how to identify which parts of your code were written by AI tools like GitHub Copilot, Devin, or other AI assistants.

Note: the code is flexible - you can track CI pipeline bots, or any other contributor you want.

​
Overview
The attribution extension analyzes git history to:

Identify which symbols (functions, classes, etc.) were authored or modified by AI tools
Calculate the percentage of AI contributions in your codebase
Find high-impact AI-written code (code that many other parts depend on)
Track the evolution of AI contributions over time
​
Installation
The attribution extension is included with Codegen. No additional installation is required.

​
Basic Usage
​
Running the Analysis
You can run the AI impact analysis using the graph_sitter.cli:


Copy
codegen analyze-ai-impact
Or from Python code:


Copy
from graph_sitter import Codebase
from graph_sitter.extensions.attribution.cli import run

# Initialize codebase from current directory
codebase = Codebase.from_repo("your-org/your-repo", language="python")

# Run the analysis
run(codebase)
​
Understanding the Results
The analysis will print a summary of AI contributions to your console and save detailed results to a JSON file. The summary includes:

List of all contributors (human and AI)
Percentage of commits made by AI
Number of files and symbols touched by AI
High-impact AI-written code (code with many dependents)
Top files by AI contribution percentage
​
Advanced Usage
​
Accessing Attribution Information
After running the analysis, each symbol in your codebase will have attribution information attached to it:


Copy
from graph_sitter import Codebase
from graph_sitter.extensions.attribution.main import add_attribution_to_symbols

# Initialize codebase
codebase = Codebase.from_repo("your-org/your-repo", language="python")

# Add attribution information to symbols
ai_authors = ['github-actions[bot]', 'dependabot[bot]', 'copilot[bot]']
add_attribution_to_symbols(codebase, ai_authors)

# Access attribution information on symbols
for symbol in codebase.symbols:
    if hasattr(symbol, 'is_ai_authored') and symbol.is_ai_authored:
        print(f"AI-authored symbol: {symbol.name} in {symbol.filepath}")
        print(f"Last editor: {symbol.last_editor}")
        print(f"All editors: {symbol.editor_history}")
​
Customizing AI Author Detection
By default, the analysis looks for common AI bot names in commit authors. You can customize this by providing your own list of AI authors:


Copy
from graph_sitter import Codebase
from graph_sitter.extensions.attribution.main import analyze_ai_impact

# Initialize codebase
codebase = Codebase.from_repo("your-org/your-repo", language="python")

# Define custom AI authors
ai_authors = [
    'github-actions[bot]',
    'dependabot[bot]',
    'copilot[bot]',
    'devin[bot]',
    'your-custom-ai-email@example.com'
]

# Run analysis with custom AI authors
results = analyze_ai_impact(codebase, ai_authors)
​
Example: Contributor Analysis
Here’s a complete example that analyzes contributors to your codebase and their impact:


Copy
import os
from collections import Counter

from graph_sitter import Codebase
from graph_sitter.extensions.attribution.main import add_attribution_to_symbols
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.sdk.codebase.config import ProjectConfig
from codegen.shared.enums.programming_language import ProgrammingLanguage

def analyze_contributors(codebase):
    """Analyze contributors to the codebase and their impact."""
    print("\n🔍 Contributor Analysis:")
    
    # Define which authors are considered AI
    ai_authors = ['devin[bot]', 'codegen[bot]', 'github-actions[bot]', 'dependabot[bot]']
    
    # Add attribution information to all symbols
    print("Adding attribution information to symbols...")
    add_attribution_to_symbols(codebase, ai_authors)
    
    # Collect statistics about contributors
    contributor_stats = Counter()
    ai_contributor_stats = Counter()
    
    print("Analyzing symbol attributions...")
    for symbol in codebase.symbols:
        if hasattr(symbol, 'last_editor') and symbol.last_editor:
            contributor_stats[symbol.last_editor] += 1
            
            # Track if this is an AI contributor
            if any(ai in symbol.last_editor for ai in ai_authors):
                ai_contributor_stats[symbol.last_editor] += 1
    
    # Print top contributors overall
    print("\n👥 Top Contributors by Symbols Authored:")
    for contributor, count in contributor_stats.most_common(10):
        is_ai = any(ai in contributor for ai in ai_authors)
        ai_indicator = "🤖" if is_ai else "👤"
        print(f"  {ai_indicator} {contributor}: {count} symbols")
    
    # Print top AI contributors if any
    if ai_contributor_stats:
        print("\n🤖 Top AI Contributors:")
        for contributor, count in ai_contributor_stats.most_common(5):
            print(f"  • {contributor}: {count} symbols")

# Initialize codebase from current directory
if os.path.exists(".git"):
    repo_path = os.getcwd()
    repo_config = RepoConfig.from_repo_path(repo_path)
    repo_operator = RepoOperator(repo_config=repo_config)
    
    project = ProjectConfig.from_repo_operator(
        repo_operator=repo_operator,
        programming_language=ProgrammingLanguage.PYTHON
    )
    codebase = Codebase(projects=[project])
    
    # Run the contributor analysis
    analyze_contributors(codebase)



