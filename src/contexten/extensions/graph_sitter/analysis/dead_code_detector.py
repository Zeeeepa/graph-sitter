#!/usr/bin/env python3
"""
Dead Code Detector

Detects unused functions, variables, imports, and classes using graph_sitter API.
"""

import graph_sitter
from graph_sitter import Codebase


@graph_sitter.function("detect-dead-code")
def detect_dead_code(codebase: Codebase):
    """Detect dead code in the codebase."""
    dead_functions = []
    dead_variables = []
    unused_imports = []
    unused_classes = []
    
    # Find unused functions
    for function in codebase.functions:
        # Skip test files
        if "test" in function.file.filepath:
            continue
            
        # Skip decorated functions (might be used by framework)
        if function.decorators:
            continue
            
        # Check if function has no usages and no call sites
        if not function.usages and not function.call_sites:
            dead_functions.append({
                'name': function.name,
                'file': function.file.filepath,
                'line': function.start_point[0] if function.start_point else 0
            })
    
    # Find unused variables
    for function in codebase.functions:
        for var_assignment in function.code_block.local_var_assignments:
            if not var_assignment.local_usages:
                dead_variables.append({
                    'name': var_assignment.name,
                    'function': function.name,
                    'file': function.file.filepath
                })
    
    # Find unused imports
    for file in codebase.files:
        for imp in file.imports:
            # Check if import is used
            if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                if not imp.imported_symbol.usages:
                    unused_imports.append({
                        'module': imp.module if hasattr(imp, 'module') else str(imp),
                        'file': file.filepath
                    })
    
    # Find unused classes
    for cls in codebase.classes:
        if not cls.usages:
            unused_classes.append({
                'name': cls.name,
                'file': cls.file.filepath,
                'line': cls.start_point[0] if cls.start_point else 0
            })
    
    return {
        'dead_functions': dead_functions,
        'dead_variables': dead_variables,
        'unused_imports': unused_imports,
        'unused_classes': unused_classes,
        'summary': {
            'total_dead_functions': len(dead_functions),
            'total_dead_variables': len(dead_variables),
            'total_unused_imports': len(unused_imports),
            'total_unused_classes': len(unused_classes)
        }
    }


def remove_dead_code(codebase: Codebase):
    """Remove detected dead code from the codebase."""
    removed_count = 0
    
    # Remove unused functions
    for function in codebase.functions:
        if "test" in function.file.filepath:
            continue
        if function.decorators:
            continue
        if not function.usages and not function.call_sites:
            print(f"🗑️ Removing unused function: {function.name}")
            function.remove()
            removed_count += 1
    
    # Remove unused variables
    for function in codebase.functions:
        for var_assignment in function.code_block.local_var_assignments:
            if not var_assignment.local_usages:
                print(f"🧹 Removing unused variable: {var_assignment.name}")
                var_assignment.remove()
                removed_count += 1
    
    return removed_count


if __name__ == "__main__":
    # Example usage
    codebase = Codebase("./")
    result = detect_dead_code(codebase)
    
    print("Dead Code Analysis Results:")
    print(f"Dead functions: {result['summary']['total_dead_functions']}")
    print(f"Dead variables: {result['summary']['total_dead_variables']}")
    print(f"Unused imports: {result['summary']['total_unused_imports']}")
    print(f"Unused classes: {result['summary']['total_unused_classes']}")

