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

# Print overall stats
print("🔍 Codebase Analysis")
print("=" * 50)
print(f"📚 Total Classes: {len(codebase.classes)}")
print(f"⚡ Total Functions: {len(codebase.functions)}")
print(f"🔄 Total Imports: {len(codebase.imports)}")

# Find class with most inheritance
if codebase.classes:
    deepest_class = max(codebase.classes, key=lambda x: len(x.superclasses))
    print(f"\n🌳 Class with most inheritance: {deepest_class.name}")
    print(f"   📊 Chain Depth: {len(deepest_class.superclasses)}")
    print(f"   ⛓️ Chain: {' -> '.join(s.name for s in deepest_class.superclasses)}")

# Find first 5 recursive functions
recursive = [f for f in codebase.functions
            if any(call.name == f.name for call in f.function_calls)][:5]
if recursive:
    print(f"\n🔄 Recursive functions:")
    for func in recursive:
        print(f"  - {func.name}")


from collections import Counter

# Filter to all test functions and classes
test_functions = [x for x in codebase.functions if x.name.startswith('test_')]
test_classes = [x for x in codebase.classes if x.name.startswith('Test')]

print("🧪 Test Analysis")
print("=" * 50)
print(f"📝 Total Test Functions: {len(test_functions)}")
print(f"🔬 Total Test Classes: {len(test_classes)}")
print(f"📊 Tests per File: {len(test_functions) / len(codebase.files):.1f}")

# Find files with the most tests
print("\n📚 Top Test Files by Class Count")
print("-" * 50)
file_test_counts = Counter([x.file for x in test_classes])
for file, num_tests in file_test_counts.most_common()[:5]:
    print(f"🔍 {num_tests} test classes: {file.filepath}")
    print(f"   📏 File Length: {len(file.source)} lines")
    print(f"   💡 Functions: {len(file.functions)}")


filename = 'tests/test_path.py'
print(f"📦 Splitting Test File: {filename}")
print("=" * 50)

# Grab a file
file = codebase.get_file(filename)
base_name = filename.replace('.py', '')

# Group tests by subpath
test_groups = {}
for test_function in file.functions:
    if test_function.name.startswith('test_'):
        test_subpath = '_'.join(test_function.name.split('_')[:3])
        if test_subpath not in test_groups:
            test_groups[test_subpath] = []
        test_groups[test_subpath].append(test_function)

# Print and process each group
for subpath, tests in test_groups.items():
    print(f"\\n{subpath}/")
    new_filename = f"{base_name}/{subpath}.py"

    # Create file if it doesn't exist
    if not codebase.has_file(new_filename):
        new_file = codebase.create_file(new_filename)
    file = codebase.get_file(new_filename)

    # Move each test in the group
    for test_function in tests:
        print(f"    - {test_function.name}")
        test_function.move_to_file(new_file, strategy="add_back_edge")

# Commit changes to disk
codebase.commit()

# Find dead code
for func in codebase.functions:
    if len(func.usages) == 0:
        print(f'🗑️ Dead code: {func.name}')
        func.remove()

# Analyze import relationships
file = codebase.get_file('api/endpoints.py')
print("\nFiles that import endpoints.py:")
for import_stmt in file.inbound_imports:
    print(f"  {import_stmt.file.path}")

print("\nFiles that endpoints.py imports:")
for import_stmt in file.imports:
    if import_stmt.resolved_symbol:
        print(f"  {import_stmt.resolved_symbol.file.path}")

# Explore class hierarchies
base_class = codebase.get_class('BaseModel')
if base_class:
    print(f"\nClasses that inherit from {base_class.name}:")
    for subclass in base_class.subclasses:
        print(f"  {subclass.name}")
        # We can go deeper in the inheritance tree
        for sub_subclass in subclass.subclasses:
            print(f"    └─ {sub_subclass.name}")

# Get all source files in the codebase
source_files = codebase.files

# Get all files in the codebase (including non-code files)
all_files = codebase.files(extensions="*")

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

# Get all files in the codebase (including README, docs, config files)
files = codebase.files(extensions="*")

# Print files that are not source code (documentation, config, etc)
for file in files:
    if not file.filepath.endswith(('.py', '.ts', '.js')):
        print(f"📄 Non-code file: {file.filepath}")

# Get only markdown documentation files
docs = codebase.files(extensions=[".md", ".mdx"])

# Get configuration files
config_files = codebase.files(extensions=[".json", ".yaml", ".toml"])

# Iterate over all symbols (includes functions + classes)
for symbol in codebase.symbols:
    print(symbol.name)

# Iterate over all functions and classes
for symbol in codebase.functions + codebase.classes:
    print(symbol.name)
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

# Get all direct dependencies
deps = my_class.dependencies  # Shorthand for dependencies(UsageType.DIRECT)

# Get dependencies of specific types
direct_deps = my_class.dependencies(UsageType.DIRECT)
chained_deps = my_class.dependencies(UsageType.CHAINED)
indirect_deps = my_class.dependencies(UsageType.INDIRECT)

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

# Check if a symbol is unused
def is_dead_code(symbol):
    return not symbol.usages

# Find all unused functions in a file
dead_functions = [f for f in file.functions if not f.usages]
Finding all imports that a symbol uses:

Copy
# Get all imports a class depends on
class_imports = [dep for dep in my_class.dependencies if isinstance(dep, Import)]

# Get all imports used by a function, including indirect ones
all_function_imports = [
    dep for dep in my_function.dependencies(UsageType.DIRECT | UsageType.INDIRECT)
    if isinstance(dep, Import)
]

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


# Initialize and analyze the codebase
from graph_sitter import Codebase
codebase = Codebase("./")

# Access pre-computed relationships
function = codebase.get_symbol("process_data")
print(f"Dependencies: {function.dependencies}")  # Instant lookup
print(f"Usages: {function.usages}")  # No parsing needed

from graph_sitter import Codebase
from codegen.configs import CodebaseConfig

# Enable lazy graph parsing
codebase = Codebase("<repo_path>", config=CodebaseConfig(exp_lazy_graph=True))

# The codebase object will be created immediately with no parsing done
# These all do not require graph parsing
codebase.files
codebase.directories
codebase.get_file("...")

# These do require graph parsing, and will create the graph only if called
codebase.get_function("...")
codebase.get_class("...")
codebase.imports

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

he generated data can be used to train LLMs in several ways:

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

Codebase Initialization
from graph_sitter import Codebase
codebase = Codebase("./")                    # Local repository
codebase = Codebase.from_repo('org/repo')   # Clone from GitHub
Essential Properties
codebase.functions      # All functions in codebase
codebase.classes        # All classes in codebase
codebase.imports        # All import statements
codebase.files          # All source files
codebase.symbols        # All symbols (functions, classes, variables)
:magnifying_glass: Dead Code Detection & Analysis
Function Usage Analysis
# Primary dead code detection pattern
for function in codebase.functions:
    if not function.usages:           # No usages found
        print(f"Dead code: {function.name}")
        function.remove()             # Safe removal with import updates

# Function analysis properties
function.usages                       # List of all usage locations
function.call_sites                   # All places where function is called
function.dependencies                 # What this function depends on
function.file                        # File containing the function
Method Usage Tracking
# Class method analysis
for method in class_def.methods:
    for usage in method.usages:       # Track method usage across codebase
        print(f"Used in {usage.file.name}")

# Method filtering for analysis
public_methods = class_def.methods(private=False)  # Exclude private methods
regular_methods = class_def.methods(magic=False)   # Exclude magic methods
Continuing with more sections...
:computer: View my work



12:12
:clipboard: Graph-sitter Features & Functions Catalog - Part 2: Import & Class Analysis
:link: Import & Dependency Analysis
Import Operations
# Access and analyze imports
for imp in file.imports:
    print(imp.module)                # Import source
    print(imp.symbol)                # Imported symbol

# Get specific imports
imp = file.get_import('math')
imp = file.get_import('MyComponent')

# Filter external imports for dependency analysis
from codegen.sdk import ExternalModule
external_imports = [i for i in codebase.imports if isinstance(i, ExternalModule)]
Import Manipulation
# Modify imports safely
import_stmt.set_module("./new/path")     # Change import source
import_stmt.set_alias("MyAlias")         # Add/update alias
import_stmt.make_type_import()           # Convert to 'import type' (TypeScript)
import_stmt.make_value_import()          # Remove 'type' modifier
:classical_building: Class & Inheritance Analysis
Class Properties
class_def = codebase.get_class("MyClass")
class_def.methods                        # All methods in class
class_def.attributes                     # Class attributes
class_def.constructor                    # __init__ method
class_def.superclasses                   # Parent classes
class_def.subclasses                     # Child classes
Inheritance Analysis
# Check inheritance relationships
resource_classes = [
    cls for cls in codebase.classes
    if cls.is_subclass_of('Resource')
]

# Explore inheritance hierarchies
base_class = codebase.get_class('BaseModel')
if base_class:
    for subclass in base_class.subclasses:
        print(f"Subclass: {subclass.name}")
        for sub_subclass in subclass.subclasses:
            print(f"  └─ {sub_subclass.name}")
:computer: View my work
12:13
:clipboard: Graph-sitter Features & Functions Catalog - Part 3: Function Analysis & Code Transformation
:cog: Function Analysis & Manipulation
Function Properties
function = codebase.get_function("process_data")
function.name                           # Function name
function.parameters                     # Function parameters
function.return_type                    # Return type annotation
function.docstring                      # Function docstring
function.decorators                     # Applied decorators
function.function_calls                 # Functions called within this function
Function Modification
# Rename function and all usages
function.rename('process_resource')     # Updates all references automatically

# Modify function signature
handler = codebase.get_function('event_handler')
handler.get_parameter('e').rename('event')           # Rename parameter
handler.add_parameter('timeout: int = 30')           # Add parameter
handler.add_return_type('Response | None')           # Add return type
:arrows_anticlockwise: Code Transformation & Editing
The Editable API
# Basic editing operations
function.edit("new implementation")      # Replace entire source
function.source                         # Current source code
function.extended_source                 # Includes decorators, comments

# Relationship tracking
function.parent_class                    # Containing class
function.parent_function                 # Containing function
function.file                          # Containing file
Symbol Movement
# Move symbols between files with auto-import updates
cls.move_to_file('enums.py')            # Move class to different file
function.move_to_file(target_file, strategy="add_back_edge")

# Automatically handles:
# - All imports that reference the symbol
# - Maintains dependencies
# - Preserves comments and decorators

Generating Directory READMEs
Here’s how to recursively generate README files for each directory using AI:


Copy
def generate_directory_readme(directory):
    # Skip non-source directories
    if any(skip in directory.name for skip in [
        'node_modules', 'venv', '.git', '__pycache__', 'build', 'dist'
    ]):
        return
        
    # Collect directory contents for context
    files = [f for f in directory.files if f.is_source_file]
    functions = directory.functions
    classes = directory.classes
    
    # Create context for AI
    context = {
        "Directory Name": directory.name,
        "Files": [f"{f.name} ({len(f.source.splitlines())} lines)" for f in files],
        "Functions": [f.name for f in functions],
        "Classes": [c.name for c in classes]
    }
    
    # Generate directory summary using AI
    readme_content = codebase.ai(
        prompt="""Generate a README section that explains this directory's:
        1. Purpose and responsibility
        2. Key components and their roles
        3. How it fits into the larger codebase
        4. Important patterns or conventions
        
        Keep it clear and concise.""",
        target=directory,
        context=context
    )
    
    # Add file listing
    if files:
        readme_content += "\n\n## Files\n"
        for file in files:
            # Get file summary from AI
            file_summary = codebase.ai(
                prompt="Describe this file's purpose in one line:",
                target=file
            )
            readme_content += f"\n### {file.name}\n{file_summary}\n"
            
            # List key components
            if file.classes:
                readme_content += "\nKey classes:\n"
                for cls in file.classes:
                    readme_content += f"- `{cls.name}`\n"
            if file.functions:
                readme_content += "\nKey functions:\n"
                for func in file.functions:
                    readme_content += f"- `{func.name}`\n"
    
    # Create or update README.md
    readme_path = f"{directory.path}/README.md"
    if codebase.has_file(readme_path):
        readme_file = codebase.get_file(readme_path)
        readme_file.edit(readme_content)
    else:
        readme_file = codebase.create_file(readme_path)
        readme_file.edit(readme_content)
    
    # Recursively process subdirectories
    for subdir in directory.subdirectories:
        generate_directory_readme(subdir)

# Generate READMEs for the entire codebase
generate_directory_readme(codebase.root_directory)
This will create a hierarchy of README.md files that explain each directory’s purpose and contents. For example:


Copy
# src/
Core implementation directory containing the main business logic and data models.
This directory is responsible for the core functionality of the application.

## Key Patterns
- Business logic is separated from API endpoints
- Models follow the Active Record pattern
- Services implement the Repository pattern

## Files

### models.py
Defines the core data models and their relationships.

Key classes:
- `User`
- `Product`
- `Order`

### services.py
Implements business logic and data access services.

Key classes:
- `UserService`
- `ProductService`
Key functions:
- `initialize_db`
- `migrate_data`
​
Customizing the Generation
You can customize the README generation by modifying the prompts and adding more context:


Copy
def get_directory_patterns(directory):
    """Analyze common patterns in a directory"""
    patterns = []
    
    # Check for common file patterns
    if any('test_' in f.name for f in directory.files):
        patterns.append("Contains unit tests")
    if any('interface' in f.name.lower() for f in directory.files):
        patterns.append("Uses interface-based design")
    if any(c.is_dataclass for c in directory.classes):
        patterns.append("Uses dataclasses for data models")
        
    return patterns

def generate_enhanced_readme(directory):
    # Get additional context
    patterns = get_directory_patterns(directory)
    dependencies = [imp.module for imp in directory.imports]
    
    # Enhanced context for AI
    context = {
        "Common Patterns": patterns,
        "Dependencies": dependencies,
        "Parent Directory": directory.parent.name if directory.parent else None,
        "Child Directories": [d.name for d in directory.subdirectories],
        "Style": "technical but approachable"
    }
    
    # Generate README with enhanced context
    # ... rest of the generation logic
​
Best Practices
Keep Summaries Focused: Direct the AI to generate concise, purpose-focused summaries.

Include Key Information:

Directory purpose
Important patterns
Key files and their roles
How components work together



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
### Primary Library Interface

```python
from graph_sitter import Codebase
from codegen.configs import CodebaseConfig

# Initialize codebase with automatic parsing
codebase = Codebase("./")
codebase = Codebase.from_repo('fastapi/fastapi')  # Clone + parse remote repo

# Access pre-computed graph elements
codebase.functions    # All functions in codebase
codebase.classes      # All classes
codebase.imports      # All import statements
codebase.files        # All files
```

### Graph Navigation & Analysis

```python
# Function analysis
for function in codebase.functions:
    function.usages           # All usage sites
    function.call_sites       # All call locations
    function.dependencies     # Function dependencies
    function.function_calls   # Functions this function calls

# Class hierarchy analysis
for cls in codebase.classes:
    cls.superclasses         # Parent classes
    cls.subclasses          # Child classes
    cls.is_subclass_of('BaseClass')  # Inheritance checking

# Import relationship analysis
for file in codebase.files:
    file.imports            # Outbound imports
    file.inbound_imports    # Files that import this file
```

### Code Transformation Operations

```python
# Safe code removal with automatic import updates
function.remove()           # Removes function and updates references
cls.remove()               # Removes class and updates imports

# Code movement with dependency handling
function.move_to_file(target_file, strategy="add_back_edge")
cls.move_to_file('enums.py')

# Function signature modification
handler = codebase.get_function('event_handler')
handler.get_parameter('e').rename('event')
handler.add_parameter('timeout: int = 30')
handler.add_return_type('Response | None')

# Symbol renaming with reference updates
old_function.rename('new_name')  # Updates all references automatically
```

### File Operations

```python
# File creation and manipulation
new_file = codebase.create_file('new_module.py')
file = codebase.get_file('path/to/file.py')
file.insert_after("new_code = 'value'")

# Commit changes to disk
codebase.commit()
```

### CLI Tools

```bash
# Project initialization
gs init                    # Creates .codegen/ directory structure
gs notebook --demo        # Launch Jupyter with demo notebook

# Codemod creation and execution
gs create organize-imports -d "Sort and organize imports according to PEP8"
gs run organize-imports    # Execute codemod
gs reset                   # Reset filesystem changes
```

### Advanced Configuration

```python
# Extensive configuration options via CodebaseConfig
config = CodebaseConfig(
    debug=True,                    # Verbose logging
    verify_graph=True,             # Graph state assertions
    method_usages=True,            # Enable method usage resolution
    sync_enabled=True,             # Graph sync during commit
    generics=True,                 # Generic type resolution
    ts_language_engine=True,       # TypeScript compiler integration
    import_resolution_overrides={  # Custom import path mapping
        "old_module": "new_module"
    }
)
codebase = Codebase("./", config=config)
```

---

## Codebase Analysis Capabilities

### Dead Code Detection ✅ **Primary Capability**

**Functions Available:**
- `function.usages` - Check if function has any usage sites
- `function.remove()` - Safe removal with automatic import cleanup
- `cls.usages` - Check class usage across codebase

**Code Examples:**
```python
# Dead function detection and removal
for function in codebase.functions:
    if not function.usages:  # No usages found
        print(f'🗑️ Dead code: {function.name}')
        function.remove()    # Safe removal with import updates

# Dead class detection
for cls in codebase.classes:
    if len(cls.usages) == 0:
        cls.remove()

# Commit changes
codebase.commit()
```

### Parameter Issues ⚠️ **Partial Support**

**Functions Available:**
- `handler.get_parameter(name)` - Access function parameters
- `parameter.rename(new_name)` - Rename parameters with call-site updates
- `handler.add_parameter(signature)` - Add new parameters
- `fcall.get_arg_by_parameter_name(name)` - Access call-site arguments

**Code Examples:**
```python
# Parameter analysis and modification
handler = codebase.get_function('event_handler')
param = handler.get_parameter('e')
param.rename('event')  # Updates all call-sites automatically

# Add parameters with defaults
handler.add_parameter('timeout: int = 30')

# Analyze call-site arguments
for fcall in handler.call_sites:
    arg = fcall.get_arg_by_parameter_name('env')
    if isinstance(arg.value, Collection):
        # Modify argument values
        data_key = arg.value.get('data')
        data_key.value.edit(f'{data_key.value} or None')
```

**Limitations:** No explicit parameter validation or type checking mentioned in documentation.

### Call-out Problems ⚠️ **Partial Support**

**Functions Available:**
- `function.call_sites` - Find all locations where function is called
- `function.function_calls` - Functions called by this function
- `function.usages` - All usage sites including calls

**Code Examples:**
```python
# Analyze function call patterns
for func in codebase.functions:
    print(f"Function {func.name} is called at {len(func.call_sites)} locations")
    for call_site in func.call_sites:
        print(f"  - Called in {call_site.file.filepath}")

# Find recursive functions
recursive = [f for f in codebase.functions 
            if any(call.name == f.name for call in f.function_calls)]

# Analyze call graph relationships
function = codebase.get_symbol("process_data")
print(f"Dependencies: {function.dependencies}")
print(f"Usages: {function.usages}")
```

**Limitations:** No explicit call-site validation or incorrect usage detection mentioned.

### Import Issues ✅ **Strong Support**

**Functions Available:**
- `file.imports` - Outbound imports from file
- `file.inbound_imports` - Files that import this file
- `import_stmt.resolved_symbol` - Check if import resolves correctly
- Automatic import updates during code movement

**Code Examples:**
```python
# Analyze import relationships
file = codebase.get_file('api/endpoints.py')
print("Files that import endpoints.py:")
for import_stmt in file.inbound_imports:
    print(f"  {import_stmt.file.path}")

print("Files that endpoints.py imports:")
for import_stmt in file.imports:
    if import_stmt.resolved_symbol:
        print(f"  {import_stmt.resolved_symbol.file.path}")
    else:
        print(f"  ⚠️ Unresolved import: {import_stmt}")

# Automatic import management during transformations
cls.move_to_file('new_location.py')  # Automatically updates all imports
```

**Advanced Import Configuration:**
```python
config = CodebaseConfig(
    import_resolution_paths=["custom/path"],
    import_resolution_overrides={"old_module": "new_module"},
    py_resolve_syspath=True,  # Resolve from sys.path
    allow_external=True       # Resolve external imports
)
```

### Type Safety ⚠️ **Limited Support**

**Functions Available:**
- `generics=True` config flag for generic type resolution
- `ts_language_engine=True` for TypeScript compiler integration
- `handler.add_return_type()` - Add return type annotations

**Code Examples:**
```python
# Generic type resolution (when enabled)
config = CodebaseConfig(generics=True)
codebase = Codebase("./", config=config)

# TypeScript type analysis (when enabled)
config = CodebaseConfig(ts_language_engine=True)
# Enables commands like inferred_return_type (not detailed in docs)

# Add type annotations
handler = codebase.get_function('process_data')
handler.add_return_type('Response | None')
```

**Limitations:** Limited type safety analysis capabilities documented. TypeScript integration mentioned but not detailed.

### Code Quality ⚠️ **Basic Support**

**Functions Available:**
- Inheritance hierarchy analysis
- Code organization and file splitting
- Pattern detection through graph traversal

**Code Examples:**
```python
# Analyze inheritance patterns
if codebase.classes:
    deepest_class = max(codebase.classes, key=lambda x: len(x.superclasses))
    print(f"Class with most inheritance: {deepest_class.name}")
    print(f"Chain Depth: {len(deepest_class.superclasses)}")

# Organize code by patterns
for cls in codebase.classes:
    if cls.is_subclass_of('Enum'):
        cls.move_to_file('enums.py')  # Organize enums

# Test file analysis and organization
test_functions = [x for x in codebase.functions if x.name.startswith('test_')]
test_classes = [x for x in codebase.classes if x.name.startswith('Test')]
```

**Limitations:** No explicit code quality metrics, linting, or pattern enforcement mentioned.

---

## Code Examples by Category

### 1. Initialization and Setup

```python
# Basic initialization
from graph_sitter import Codebase
codebase = Codebase("./")

# Remote repository cloning
codebase = Codebase.from_repo('fastapi/fastapi')

# Advanced configuration
from codegen.configs import CodebaseConfig
config = CodebaseConfig(
    debug=True,
    method_usages=True,
    sync_enabled=True
)
codebase = Codebase("./", config=config)
```

### 2. Analysis Workflows

```python
# Comprehensive codebase statistics
print("🔍 Codebase Analysis")
print("=" * 50)
print(f"📚 Total Classes: {len(codebase.classes)}")
print(f"⚡ Total Functions: {len(codebase.functions)}")
print(f"🔄 Total Imports: {len(codebase.imports)}")

# Test analysis workflow
from collections import Counter
test_functions = [x for x in codebase.functions if x.name.startswith('test_')]
test_classes = [x for x in codebase.classes if x.name.startswith('Test')]

file_test_counts = Counter([x.file for x in test_classes])
for file, num_tests in file_test_counts.most_common()[:5]:
    print(f"🔍 {num_tests} test classes: {file.filepath}")
```

### 3. Error Detection Patterns

```python
# Dead code detection
for func in codebase.functions:
    if len(func.usages) == 0:
        print(f'🗑️ Dead code: {func.name}')
        func.remove()

# Recursive function detection
recursive = [f for f in codebase.functions 
            if any(call.name == f.name for call in f.function_calls)]
if recursive:
    print("🔄 Recursive functions:")
    for func in recursive:
        print(f"  - {func.name}")

# Import resolution checking
for import_stmt in file.imports:
    if not import_stmt.resolved_symbol:
        print(f"⚠️ Unresolved import: {import_stmt}")
```

### 4. Transformation Examples

```python
# Large test file splitting
filename = 'tests/test_path.py'
file = codebase.get_file(filename)
base_name = filename.replace('.py', '')

# Group tests by subpath
test_groups = {}
for test_function in file.functions:
    if test_function.name.startswith('test_'):
        test_subpath = '_'.join(test_function.name.split('_')[:3])
        if test_subpath not in test_groups:
            test_groups[test_subpath] = []
        test_groups[test_subpath].append(test_function)

# Move tests to separate files
for subpath, tests in test_groups.items():
    new_filename = f"{base_name}/{subpath}.py"
    if not codebase.has_file(new_filename):
        new_file = codebase.create_file(new_filename)

    target_file = codebase.get_file(new_filename)
    for test_function in tests:
        test_function.move_to_file(target_file, strategy="add_back_edge")

codebase.commit()
```
https://github.com/Zeeeepa/graph-sitter/blob/codegen-bot/enhanced-codebase-ai-context-aware-analysis/src/graph_sitter/codebase/codebase_analysis.py
The codebase analysis view should present all analysis codebase context. (not all at once - but react expandable when clicking on  elements their corresponding sub-ccontexts would appear).  - Main goal -> To View Code Problems, Wrong Function implementations, Wrongly set parameters, wrong function call parameters, to be able to view issues, to view their blast impact in regards to higher level module or whole codebase, to view function flows and sequences of selected functions, 
implement to dashboard project codebase analysis view - codebase_analysis.py  and codebase_ai.py  
from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol
from graph_sitter.enums import EdgeType, SymbolType


def get_codebase_summary(codebase: Codebase) -> str:
    node_summary = f"""Contains {len(codebase.ctx.get_nodes())} nodes
- {len(list(codebase.files))} files
- {len(list(codebase.imports))} imports
- {len(list(codebase.external_modules))} external_modules
- {len(list(codebase.symbols))} symbols
\t- {len(list(codebase.classes))} classes
\t- {len(list(codebase.functions))} functions
\t- {len(list(codebase.global_vars))} global_vars
\t- {len(list(codebase.interfaces))} interfaces
"""
    edge_summary = f"""Contains {len(codebase.ctx.edges)} edges
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.SYMBOL_USAGE])} symbol -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION])} import -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.EXPORT])} export -> exported symbol
    """

    return f"{node_summary}\n{edge_summary}"


def get_file_summary(file: SourceFile) -> str:
    return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global variables
\t- {len(file.interfaces)} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
"""


def get_class_summary(cls: Class) -> str:
    return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

{get_symbol_summary(cls)}
    """


def get_function_summary(func: Function) -> str:
    return f"""==== [ `{func.name}` (Function) Dependency Summary ] ====
- {len(func.return_statements)} return statements
- {len(func.parameters)} parameters
- {len(func.function_calls)} function calls
- {len(func.call_sites)} call sites
- {len(func.decorators)} decorators
- {len(func.dependencies)} dependencies

{get_symbol_summary(func)}
        """


def get_symbol_summary(symbol: Symbol) -> str:
    usages = symbol.symbol_usages
    imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]

    return f"""==== [ `{symbol.name}` ({type(symbol).__name__}) Usage Summary ] ====
- {len(usages)} usages
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t- {len(imported_symbols)} imports
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t\t- {len([x for x in imported_symbols if isinstance(x, ExternalModule)])} external modules
\t\t- {len([x for x in imported_symbols if isinstance(x, SourceFile)])} files
    """



To View all codebase statistics and issues, not used dead code -> and to be able to use codebase_ai.py in a similar manner =->  (Where after analysis -> it would automatically be sent error code +codebase's contextual code  with get_function_context - Asking to resolve the issue (Automatic relevant error code context retrieval + prompt sending via python code execution 

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

Step 3: Running the Generator
Finally, we can run our training data generator on any codebase.

See 
parsing codebases
 to learn more
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

You can use any Git repository as your source codebase by passing the repo URL to 
Codebase.from_repo(…).

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
