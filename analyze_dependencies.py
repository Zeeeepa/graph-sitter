#!/usr/bin/env python3
"""
Step 3: Build Dependency Graph
Analyze imports and create dependency visualization.
"""

import json
import ast
from pathlib import Path
from collections import defaultdict

def extract_imports(filepath):
    """Extract all imports from a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "is_local": is_local_import(alias.name)
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ""
                for alias in node.names:
                    imports.append({
                        "type": "from_import",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "is_local": is_local_import(module)
                    })
        
        return imports
    except Exception as e:
        print(f"Error extracting imports from {filepath}: {e}")
        return []

def is_local_import(module_name):
    """Check if an import is from the local codebase."""
    local_prefixes = [
        "graph_sitter",
        "autogenlib",
        "lsp_diagnostics",
        "analysis",
        "graph_sitter_analysis",
        "graph_sitter_backend",
        "analysisbig"
    ]
    return any(module_name.startswith(prefix) for prefix in local_prefixes)

def build_dependency_graph():
    """Build a dependency graph showing which files import from which."""
    
    print("=" * 80)
    print("STEP 3: Building Dependency Graph")
    print("=" * 80)
    
    # Files to analyze
    target_files = [
        "src/graph_sitter_analysis.py",
        "src/graph_sitter_backend.py",
        "src/lsp_diagnostics.py",
        "src/autogenlib_adapter.py",
        "src/analysisbig.py",
        "src/analysis.py"
    ]
    
    # Tool files
    tool_dir = Path("src/graph_sitter/extensions/tools")
    target_tools = [
        "reveal_symbol_fn.py",
        "reveal_symbol.py",
        "mdx_docs_generation.py",
        "list_directory.py",
        "generate_docs_json.py",
        "document_functions.py",
        "current_code_codebase.py",
        "codegen_sdk_codebase.py"
    ]
    
    # Build dependency map
    dependency_map = {}
    
    print("\n📊 Analyzing Dependencies in Analysis Files:")
    print("-" * 80)
    
    for filepath in target_files:
        path = Path(filepath)
        if path.exists():
            imports = extract_imports(path)
            local_imports = [imp for imp in imports if imp['is_local']]
            
            dependency_map[filepath] = {
                "total_imports": len(imports),
                "local_imports": len(local_imports),
                "local_dependencies": local_imports
            }
            
            print(f"\n📁 {filepath}")
            print(f"  Total imports: {len(imports)}")
            print(f"  Local imports: {len(local_imports)}")
            
            # Group by module
            modules = defaultdict(list)
            for imp in local_imports:
                module = imp.get('module', 'unknown')
                modules[module].append(imp.get('name', module))
            
            if modules:
                print(f"  Local dependencies:")
                for module, names in sorted(modules.items())[:10]:
                    if names and names[0]:
                        print(f"    - {module}: {', '.join(names[:5])}")
                    else:
                        print(f"    - {module}")
    
    print("\n\n📊 Analyzing Dependencies in Tool Files:")
    print("-" * 80)
    
    for tool in target_tools:
        filepath = tool_dir / tool
        if filepath.exists():
            imports = extract_imports(filepath)
            local_imports = [imp for imp in imports if imp['is_local']]
            
            dependency_map[str(filepath)] = {
                "total_imports": len(imports),
                "local_imports": len(local_imports),
                "local_dependencies": local_imports
            }
            
            print(f"\n📁 {tool}")
            print(f"  Total imports: {len(imports)}")
            print(f"  Local imports: {len(local_imports)}")
    
    # Identify cross-dependencies
    print("\n\n🔗 Cross-Dependencies Between Analysis Files:")
    print("-" * 80)
    
    for file1 in target_files:
        if file1 in dependency_map:
            deps = dependency_map[file1]['local_dependencies']
            for dep in deps:
                module = dep.get('module', '')
                # Check if this refers to another analysis file
                for file2 in target_files:
                    file2_name = Path(file2).stem
                    if file2_name in module:
                        print(f"  {Path(file1).name} → {Path(file2).name}")
    
    # Save results
    output_file = "analysis_step3_dependencies.json"
    with open(output_file, 'w') as f:
        json.dump(dependency_map, f, indent=2)
    
    print(f"\n\n✅ Dependency analysis saved to: {output_file}")
    
    return dependency_map

if __name__ == "__main__":
    build_dependency_graph()

