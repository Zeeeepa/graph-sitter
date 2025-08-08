#!/usr/bin/env python3
"""
List all dead code (unused functions and classes) in the graph_sitter package.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
    
    print("🔍 Analyzing graph_sitter package for dead code...")
    
    # Analyze the graph_sitter package itself
    graph_sitter_path = Path(__file__).parent / "src" / "graph_sitter"
    
    # Create a codebase instance
    codebase = Codebase(str(graph_sitter_path), language="python")
    
    unused_functions = []
    unused_classes = []
    
    # Collect unused functions
    for func in codebase.functions:
        if isinstance(func, Function):
            usages = func.symbol_usages
            if len(usages) == 0:
                unused_functions.append(func)
    
    # Collect unused classes  
    for cls in codebase.classes:
        if isinstance(cls, Class):
            usages = cls.symbol_usages
            if len(usages) == 0:
                unused_classes.append(cls)
    
    # Sort by file name for better organization
    unused_functions.sort(key=lambda x: (x.file.name, x.name))
    unused_classes.sort(key=lambda x: (x.file.name, x.name))
    
    print(f"\n" + "="*80)
    print(f"🔴 DEAD CODE ANALYSIS RESULTS")
    print(f"="*80)
    print(f"Found {len(unused_functions)} unused functions and {len(unused_classes)} unused classes")
    
    print(f"\n" + "="*80)
    print(f"🔴 UNUSED FUNCTIONS ({len(unused_functions)} total)")
    print(f"="*80)
    
    current_file = None
    for i, func in enumerate(unused_functions, 1):
        if func.file.name != current_file:
            current_file = func.file.name
            print(f"\n📁 {current_file}:")
        print(f"  {i:3d}. {func.name}")
    
    print(f"\n" + "="*80)
    print(f"🔴 UNUSED CLASSES ({len(unused_classes)} total)")
    print(f"="*80)
    
    current_file = None
    for i, cls in enumerate(unused_classes, 1):
        if cls.file.name != current_file:
            current_file = cls.file.name
            print(f"\n📁 {current_file}:")
        print(f"  {i:3d}. {cls.name}")
    
    # Summary by file
    print(f"\n" + "="*80)
    print(f"📊 DEAD CODE SUMMARY BY FILE")
    print(f"="*80)
    
    file_dead_code = {}
    
    for func in unused_functions:
        file_name = func.file.name
        if file_name not in file_dead_code:
            file_dead_code[file_name] = {'functions': 0, 'classes': 0}
        file_dead_code[file_name]['functions'] += 1
    
    for cls in unused_classes:
        file_name = cls.file.name
        if file_name not in file_dead_code:
            file_dead_code[file_name] = {'functions': 0, 'classes': 0}
        file_dead_code[file_name]['classes'] += 1
    
    # Sort by total dead code count
    sorted_files = sorted(file_dead_code.items(), 
                         key=lambda x: x[1]['functions'] + x[1]['classes'], 
                         reverse=True)
    
    print(f"\nFiles with most dead code:")
    for file_name, counts in sorted_files[:20]:  # Top 20 files
        total = counts['functions'] + counts['classes']
        print(f"  {file_name:<30} | {counts['functions']:2d} functions, {counts['classes']:2d} classes | Total: {total}")
    
    print(f"\n✅ Dead code analysis complete!")
    print(f"💡 Consider removing these unused symbols to clean up the codebase.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure graph_sitter is properly installed")
except Exception as e:
    print(f"❌ Analysis error: {e}")
    import traceback
    traceback.print_exc()

