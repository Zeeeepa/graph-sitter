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
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


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

        """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

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

print("\n✅ Import cycles resolved!")Break up import cycles


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

"""""""""""""""""""""""""""""""""""""""
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
    """"""""""""""""""""""""""""""""""""""""""""""""""
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
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Organize code into modules


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
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Splitting up large files

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
    """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
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
    """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
