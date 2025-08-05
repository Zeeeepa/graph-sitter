#!/usr/bin/env python3
"""
Graph-Sitter Basic Operations Examples
=====================================

This module demonstrates key Graph-Sitter operations and capabilities
for code analysis and manipulation.
"""

from pathlib import Path
from typing import List, Dict, Any
import json

# Import Graph-Sitter core components
from graph_sitter import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile
from graph_sitter.core.symbol import Symbol


def analyze_codebase_structure(codebase_path: str) -> Dict[str, Any]:
    """
    Analyze the overall structure of a codebase.
    
    Args:
        codebase_path: Path to the codebase to analyze
        
    Returns:
        Dictionary containing structural analysis results
    """
    codebase = Codebase(codebase_path)
    
    analysis = {
        "total_files": len(codebase.files),
        "source_files": len([f for f in codebase.files if isinstance(f, SourceFile)]),
        "total_functions": len(codebase.functions),
        "total_classes": len(codebase.classes),
        "languages": {},
        "file_breakdown": {}
    }
    
    # Analyze by language/extension
    for file in codebase.files:
        ext = Path(file.path).suffix
        if ext not in analysis["languages"]:
            analysis["languages"][ext] = 0
        analysis["languages"][ext] += 1
    
    # Analyze file sizes and complexity
    for file in codebase.source_files:
        analysis["file_breakdown"][file.path] = {
            "lines": len(file.source.splitlines()),
            "functions": len(file.functions),
            "classes": len(file.classes),
            "imports": len(file.imports)
        }
    
    return analysis


def find_unused_functions(codebase: Codebase) -> List[Function]:
    """
    Find functions that are defined but never used.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        List of unused functions
    """
    unused_functions = []
    
    for function in codebase.functions:
        # Check if function has any usages
        if not function.usages:
            # Exclude special methods and entry points
            if not (function.name.startswith("__") or 
                   function.name in ["main", "run", "execute"]):
                unused_functions.append(function)
    
    return unused_functions


def analyze_function_dependencies(function: Function) -> Dict[str, Any]:
    """
    Analyze dependencies and usage patterns for a specific function.
    
    Args:
        function: The function to analyze
        
    Returns:
        Dictionary containing dependency analysis
    """
    return {
        "name": function.name,
        "file": function.file.path,
        "line_number": function.start_line,
        "parameters": [param.name for param in function.parameters],
        "dependencies": [dep.name for dep in function.dependencies],
        "usages": [
            {
                "file": usage.file.path,
                "line": usage.start_line,
                "context": usage.context
            }
            for usage in function.usages
        ],
        "complexity_metrics": {
            "lines_of_code": function.end_line - function.start_line,
            "dependency_count": len(function.dependencies),
            "usage_count": len(function.usages)
        }
    }


def find_complex_functions(codebase: Codebase, max_dependencies: int = 10) -> List[Function]:
    """
    Find functions with high complexity (many dependencies).
    
    Args:
        codebase: The codebase to analyze
        max_dependencies: Threshold for considering a function complex
        
    Returns:
        List of complex functions
    """
    complex_functions = []
    
    for function in codebase.functions:
        if len(function.dependencies) > max_dependencies:
            complex_functions.append(function)
    
    # Sort by dependency count (descending)
    complex_functions.sort(key=lambda f: len(f.dependencies), reverse=True)
    
    return complex_functions


def analyze_class_hierarchy(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze class inheritance patterns and hierarchy.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary containing class hierarchy analysis
    """
    hierarchy = {
        "total_classes": len(codebase.classes),
        "inheritance_chains": {},
        "abstract_classes": [],
        "leaf_classes": [],
        "multiple_inheritance": []
    }
    
    for class_def in codebase.classes:
        class_name = class_def.name
        
        # Analyze parent classes
        if hasattr(class_def, 'parent_classes') and class_def.parent_classes:
            parent_names = [parent.name for parent in class_def.parent_classes]
            hierarchy["inheritance_chains"][class_name] = parent_names
            
            # Check for multiple inheritance
            if len(parent_names) > 1:
                hierarchy["multiple_inheritance"].append(class_name)
        else:
            # No parents - potential root class
            hierarchy["leaf_classes"].append(class_name)
        
        # Check for abstract methods (simplified check)
        abstract_methods = [
            method.name for method in class_def.methods 
            if "abstract" in method.decorators_text.lower()
        ]
        if abstract_methods:
            hierarchy["abstract_classes"].append({
                "name": class_name,
                "abstract_methods": abstract_methods
            })
    
    return hierarchy


def find_import_patterns(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze import patterns and dependencies across the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary containing import analysis
    """
    import_analysis = {
        "external_dependencies": {},
        "internal_imports": {},
        "circular_imports": [],
        "unused_imports": []
    }
    
    for file in codebase.source_files:
        for import_stmt in file.imports:
            module_name = import_stmt.module
            
            # Categorize as external or internal
            if module_name.startswith('.') or any(
                module_name.startswith(pkg) for pkg in ['src', 'lib', 'app']
            ):
                # Internal import
                if module_name not in import_analysis["internal_imports"]:
                    import_analysis["internal_imports"][module_name] = []
                import_analysis["internal_imports"][module_name].append(file.path)
            else:
                # External dependency
                if module_name not in import_analysis["external_dependencies"]:
                    import_analysis["external_dependencies"][module_name] = 0
                import_analysis["external_dependencies"][module_name] += 1
            
            # Check for unused imports (simplified)
            for symbol in import_stmt.symbols:
                if not symbol.usages:
                    import_analysis["unused_imports"].append({
                        "file": file.path,
                        "import": module_name,
                        "symbol": symbol.name
                    })
    
    return import_analysis


def generate_refactoring_suggestions(codebase: Codebase) -> List[Dict[str, Any]]:
    """
    Generate automated refactoring suggestions based on code analysis.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        List of refactoring suggestions
    """
    suggestions = []
    
    # Find unused functions
    unused_functions = find_unused_functions(codebase)
    for func in unused_functions:
        suggestions.append({
            "type": "remove_unused_function",
            "priority": "medium",
            "description": f"Remove unused function '{func.name}' in {func.file.path}",
            "file": func.file.path,
            "line": func.start_line,
            "action": "delete"
        })
    
    # Find complex functions that could be split
    complex_functions = find_complex_functions(codebase, max_dependencies=8)
    for func in complex_functions[:5]:  # Top 5 most complex
        suggestions.append({
            "type": "split_complex_function",
            "priority": "high",
            "description": f"Consider splitting complex function '{func.name}' ({len(func.dependencies)} dependencies)",
            "file": func.file.path,
            "line": func.start_line,
            "action": "refactor"
        })
    
    # Find import optimization opportunities
    import_patterns = find_import_patterns(codebase)
    for unused_import in import_patterns["unused_imports"][:10]:  # Top 10
        suggestions.append({
            "type": "remove_unused_import",
            "priority": "low",
            "description": f"Remove unused import '{unused_import['symbol']}' from {unused_import['import']}",
            "file": unused_import["file"],
            "action": "optimize"
        })
    
    return suggestions


def demonstrate_code_transformation(codebase: Codebase, function_name: str) -> Dict[str, Any]:
    """
    Demonstrate code transformation capabilities.
    
    Args:
        codebase: The codebase to work with
        function_name: Name of function to transform
        
    Returns:
        Dictionary showing transformation results
    """
    function = codebase.get_function(function_name)
    if not function:
        return {"error": f"Function '{function_name}' not found"}
    
    transformation_log = {
        "original_function": {
            "name": function.name,
            "file": function.file.path,
            "line_range": [function.start_line, function.end_line],
            "source": function.source
        },
        "transformations": []
    }
    
    # Example transformation: Add type hints (conceptual)
    if not function.return_type:
        transformation_log["transformations"].append({
            "type": "add_return_type_hint",
            "description": "Add return type annotation",
            "suggested_change": f"def {function.name}(...) -> Any:"
        })
    
    # Example transformation: Add docstring if missing
    if not function.docstring:
        transformation_log["transformations"].append({
            "type": "add_docstring",
            "description": "Add function docstring",
            "suggested_change": f'"""\n    {function.name.replace("_", " ").title()}\n    \n    Returns:\n        Description of return value\n    """'
        })
    
    return transformation_log


def main():
    """
    Demonstrate Graph-Sitter capabilities with the current codebase.
    """
    print("🔍 Graph-Sitter Analysis Demo")
    print("=" * 50)
    
    # Analyze current codebase
    codebase = Codebase(".")
    
    # 1. Basic structure analysis
    print("\n📊 Codebase Structure Analysis:")
    structure = analyze_codebase_structure(".")
    print(f"  Total files: {structure['total_files']}")
    print(f"  Source files: {structure['source_files']}")
    print(f"  Functions: {structure['total_functions']}")
    print(f"  Classes: {structure['total_classes']}")
    print(f"  Languages: {structure['languages']}")
    
    # 2. Find unused functions
    print("\n🗑️  Unused Functions:")
    unused = find_unused_functions(codebase)
    for func in unused[:5]:  # Show first 5
        print(f"  - {func.name} in {func.file.path}")
    
    # 3. Complex functions analysis
    print("\n🧮 Complex Functions (>5 dependencies):")
    complex_funcs = find_complex_functions(codebase, max_dependencies=5)
    for func in complex_funcs[:3]:  # Show top 3
        print(f"  - {func.name}: {len(func.dependencies)} dependencies")
    
    # 4. Import analysis
    print("\n📦 Import Analysis:")
    imports = find_import_patterns(codebase)
    print(f"  External dependencies: {len(imports['external_dependencies'])}")
    print(f"  Internal imports: {len(imports['internal_imports'])}")
    print(f"  Unused imports: {len(imports['unused_imports'])}")
    
    # 5. Refactoring suggestions
    print("\n🔧 Refactoring Suggestions:")
    suggestions = generate_refactoring_suggestions(codebase)
    for suggestion in suggestions[:5]:  # Show first 5
        print(f"  - {suggestion['type']}: {suggestion['description']}")
    
    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()

