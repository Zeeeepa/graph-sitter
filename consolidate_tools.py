#!/usr/bin/env python3
"""
Automated Tool Consolidation Script
Consolidates 8 tool files into graph_sitter_tools_adapter.py
"""

import re
from pathlib import Path

# Tool files to consolidate
TOOL_FILES = [
    "src/graph_sitter/extensions/tools/reveal_symbol_fn.py",
    "src/graph_sitter/extensions/tools/reveal_symbol.py",
    "src/graph_sitter/extensions/tools/mdx_docs_generation.py",
    "src/graph_sitter/extensions/tools/list_directory.py",
    "src/graph_sitter/extensions/tools/generate_docs_json.py",
    "src/graph_sitter/extensions/tools/document_functions.py",
    "src/graph_sitter/extensions/tools/current_code_codebase.py",
    "src/graph_sitter/extensions/tools/codegen_sdk_codebase.py"
]

def extract_functions_and_classes(filepath):
    """Extract all functions and classes from a Python file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Extract imports
        import_pattern = r'^(from .+ import .+|import .+)$'
        imports = re.findall(import_pattern, content, re.MULTILINE)
        
        # Extract classes (with full body)
        class_pattern = r'(class \w+.*?:\n(?:    .*\n)*)'
        classes = re.findall(class_pattern, content, re.MULTILINE)
        
        # Extract top-level functions (with full body)
        func_pattern = r'^(def \w+\(.*?\).*?:\n(?:(?:    .*\n)|(?:\n))*?)(?=\n(?:def |class |\Z))'
        functions = re.findall(func_pattern, content, re.MULTILINE | re.DOTALL)
        
        return {
            'imports': imports,
            'classes': classes,
            'functions': functions,
            'full_content': content
        }
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def main():
    print("=" * 80)
    print("CONSOLIDATING TOOL FILES")
    print("=" * 80)
    
    all_imports = set()
    all_classes = []
    all_functions = []
    
    for tool_file in TOOL_FILES:
        print(f"\nProcessing: {tool_file}")
        data = extract_functions_and_classes(tool_file)
        
        if data:
            all_imports.update(data['imports'])
            all_classes.extend(data['classes'])
            all_functions.extend(data['functions'])
            print(f"  Found: {len(data['classes'])} classes, {len(data['functions'])} functions")
    
    # Generate consolidated file
    output = []
    output.append('"""Graph-Sitter Tools - Consolidated from 8 tool files"""')
    output.append('')
    output.append('# Consolidated imports')
    for imp in sorted(all_imports):
        # Fix imports to work with new location
        fixed_imp = imp.replace('from .', 'from graph_sitter.extensions.tools.')
        output.append(fixed_imp)
    
    output.append('')
    output.append('# ========== CONSOLIDATED CLASSES ==========')
    for cls in all_classes:
        output.append('')
        output.append(cls)
    
    output.append('')
    output.append('# ========== CONSOLIDATED FUNCTIONS ==========')
    for func in all_functions:
        output.append('')
        output.append(func)
    
    # Save to temporary file for review
    temp_output = 'tools_consolidated_temp.py'
    with open(temp_output, 'w') as f:
        f.write('\n'.join(output))
    
    print(f"\n✅ Consolidated content saved to: {temp_output}")
    print(f"Total imports: {len(all_imports)}")
    print(f"Total classes: {len(all_classes)}")
    print(f"Total functions: {len(all_functions)}")

if __name__ == "__main__":
    main()

