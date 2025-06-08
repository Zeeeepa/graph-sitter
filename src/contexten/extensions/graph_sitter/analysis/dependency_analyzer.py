#!/usr/bin/env python3
"""
Dependency Analyzer

Analyzes dependencies, imports, and relationships between code elements.
Uses graph_sitter API for dependency tracking and circular dependency detection.
"""

import graph_sitter
from graph_sitter import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol
from collections import defaultdict, deque
import networkx as nx


def hop_through_imports(imp: Import) -> Symbol | ExternalModule:
    """Finds the root symbol for an import."""
    if isinstance(imp.imported_symbol, Import):
        return hop_through_imports(imp.imported_symbol)
    return imp.imported_symbol


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


@graph_sitter.function("analyze-dependencies")
def analyze_dependencies(codebase: Codebase):
    """Analyze dependencies and imports in the codebase."""
    results = {
        'import_analysis': {},
        'circular_dependencies': [],
        'external_dependencies': [],
        'unused_imports': [],
        'dependency_graph': {},
        'summary': {
            'total_imports': 0,
            'external_imports': 0,
            'internal_imports': 0,
            'circular_count': 0
        }
    }
    
    # Create dependency graph
    dependency_graph = create_dependency_graph(codebase)
    
    # Find circular dependencies
    cycles = list(nx.simple_cycles(dependency_graph))
    results['circular_dependencies'] = cycles
    results['summary']['circular_count'] = len(cycles)
    
    # Analyze imports
    total_imports = 0
    external_imports = 0
    internal_imports = 0
    
    for file in codebase.files:
        file_imports = {
            'filepath': file.filepath,
            'imports': [],
            'external_imports': [],
            'unused_imports': []
        }
        
        for imp in file.imports:
            total_imports += 1
            
            import_info = {
                'module': imp.module if hasattr(imp, 'module') else str(imp),
                'is_external': False,
                'is_used': True
            }
            
            # Check if it's an external import
            resolved = imp.resolved_symbol if hasattr(imp, 'resolved_symbol') else None
            if isinstance(resolved, ExternalModule):
                import_info['is_external'] = True
                external_imports += 1
                results['external_dependencies'].append({
                    'module': import_info['module'],
                    'file': file.filepath
                })
            else:
                internal_imports += 1
            
            # Check if import is used
            if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                if not imp.imported_symbol.usages:
                    import_info['is_used'] = False
                    results['unused_imports'].append({
                        'module': import_info['module'],
                        'file': file.filepath
                    })
            
            file_imports['imports'].append(import_info)
        
        results['import_analysis'][file.filepath] = file_imports
    
    # Update summary
    results['summary']['total_imports'] = total_imports
    results['summary']['external_imports'] = external_imports
    results['summary']['internal_imports'] = internal_imports
    
    return results


def create_dependency_graph(codebase: Codebase):
    """Create a graph of file dependencies."""
    G = nx.DiGraph()
    
    for file in codebase.files:
        # Add node for this file
        G.add_node(file.filepath)
        
        # Add edges for each import
        for imp in file.imports:
            if hasattr(imp, 'from_file') and imp.from_file:  # Skip external imports
                G.add_edge(file.filepath, imp.from_file.filepath)
    
    return G


def analyze_module_coupling(codebase: Codebase):
    """Analyze coupling between modules."""
    coupling_scores = defaultdict(int)
    
    for file in codebase.files:
        # Count unique files imported from
        imported_files = set()
        for imp in file.imports:
            if hasattr(imp, 'from_file') and imp.from_file:
                imported_files.add(imp.from_file.filepath)
        coupling_scores[file.filepath] += len(imported_files)
        
        # Count files that import this file
        importing_files = set()
        for symbol in file.symbols if hasattr(file, 'symbols') else []:
            for usage in symbol.usages:
                if hasattr(usage, 'file') and usage.file != file:
                    importing_files.add(usage.file.filepath)
        coupling_scores[file.filepath] += len(importing_files)
    
    # Sort by coupling score
    sorted_files = sorted(coupling_scores.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'coupling_scores': dict(coupling_scores),
        'most_coupled': sorted_files[:10],
        'average_coupling': sum(coupling_scores.values()) / len(coupling_scores) if coupling_scores else 0
    }


def find_unused_imports(codebase: Codebase):
    """Find imports that are not used in the code."""
    unused_imports = []
    
    for file in codebase.files:
        for imp in file.imports:
            # Check if import is used
            if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                if not imp.imported_symbol.usages:
                    unused_imports.append({
                        'module': imp.module if hasattr(imp, 'module') else str(imp),
                        'file': file.filepath,
                        'line': imp.start_point[0] if hasattr(imp, 'start_point') and imp.start_point else 0
                    })
    
    return unused_imports


def organize_imports(file):
    """Organize imports in a file by type (standard library, third-party, local)."""
    # Group imports by type
    std_lib_imports = []
    third_party_imports = []
    local_imports = []
    
    for imp in file.imports:
        resolved = imp.resolved_symbol if hasattr(imp, 'resolved_symbol') else None
        
        if isinstance(resolved, ExternalModule):
            # Simple heuristic to distinguish stdlib from third-party
            module_name = imp.module if hasattr(imp, 'module') else str(imp)
            if module_name in ['os', 'sys', 'json', 'math', 'datetime', 're', 'collections']:
                std_lib_imports.append(imp)
            else:
                third_party_imports.append(imp)
        else:
            local_imports.append(imp)
    
    return {
        'standard_library': std_lib_imports,
        'third_party': third_party_imports,
        'local': local_imports
    }


@graph_sitter.function("detect-circular-dependencies")
def detect_circular_dependencies(codebase: Codebase):
    """Detect circular dependencies in the codebase."""
    # Create dependency graph
    graph = create_dependency_graph(codebase)
    
    # Find circular dependencies
    cycles = list(nx.simple_cycles(graph))
    
    results = {
        'cycles': cycles,
        'cycle_count': len(cycles),
        'affected_files': set(),
        'suggestions': []
    }
    
    # Collect all affected files
    for cycle in cycles:
        results['affected_files'].update(cycle)
    
    results['affected_files'] = list(results['affected_files'])
    
    # Generate suggestions for breaking cycles
    for cycle in cycles:
        if len(cycle) == 2:
            results['suggestions'].append({
                'type': 'extract_shared_module',
                'description': f"Extract shared code from {cycle[0]} and {cycle[1]} into a common module",
                'files': cycle
            })
        else:
            results['suggestions'].append({
                'type': 'dependency_inversion',
                'description': f"Consider dependency inversion for cycle: {' -> '.join(cycle)}",
                'files': cycle
            })
    
    return results


def analyze_function_dependencies(codebase: Codebase):
    """Analyze dependencies at the function level."""
    function_deps = {}
    
    for function in codebase.functions:
        context = get_function_context(function)
        
        function_deps[function.name] = {
            'file': function.filepath,
            'dependencies': len(context['dependencies']),
            'usages': len(context['usages']),
            'dependency_files': list(set(dep['filepath'] for dep in context['dependencies'])),
            'usage_files': list(set(usage['filepath'] for usage in context['usages']))
        }
    
    return function_deps


if __name__ == "__main__":
    # Example usage
    codebase = Codebase("./")
    
    print("🔍 Analyzing dependencies...")
    results = analyze_dependencies(codebase)
    
    print(f"\n📊 Dependency Analysis Results:")
    print(f"Total imports: {results['summary']['total_imports']}")
    print(f"External imports: {results['summary']['external_imports']}")
    print(f"Internal imports: {results['summary']['internal_imports']}")
    print(f"Circular dependencies: {results['summary']['circular_count']}")
    
    if results['circular_dependencies']:
        print(f"\n🔄 Circular dependencies found:")
        for cycle in results['circular_dependencies']:
            print(f"  • {' -> '.join(cycle)}")
    
    if results['unused_imports']:
        print(f"\n🧹 Unused imports ({len(results['unused_imports'])}):")
        for unused in results['unused_imports'][:5]:
            print(f"  • {unused['module']} in {unused['file']}")
    
    # Analyze coupling
    print(f"\n🔗 Analyzing module coupling...")
    coupling = analyze_module_coupling(codebase)
    print(f"Average coupling: {coupling['average_coupling']:.1f}")
    
    if coupling['most_coupled']:
        print(f"Most coupled files:")
        for filepath, score in coupling['most_coupled'][:3]:
            print(f"  • {filepath}: {score} connections")

