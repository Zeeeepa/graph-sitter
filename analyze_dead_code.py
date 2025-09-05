#!/usr/bin/env python3
"""
Dead code analysis script for graph_sitter package using its own analysis capabilities.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.codebase.codebase_analysis import get_codebase_summary, get_symbol_summary
    from graph_sitter.enums import SymbolType
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
    
    print("✅ Successfully imported graph_sitter modules")
    
    # Analyze the graph_sitter package itself
    graph_sitter_path = Path(__file__).parent / "src" / "graph_sitter"
    
    print(f"🔍 Analyzing graph_sitter package at: {graph_sitter_path}")
    
    # Create a codebase instance
    codebase = Codebase(str(graph_sitter_path), language="python")
    
    print("📊 Building codebase analysis...")
    
    # Get overall summary
    summary = get_codebase_summary(codebase)
    print("\n" + "="*60)
    print("GRAPH_SITTER PACKAGE ANALYSIS")
    print("="*60)
    print(summary)
    
    # List all functions and classes
    print("\n" + "="*60)
    print("ALL FUNCTIONS AND CLASSES")
    print("="*60)
    
    all_functions = []
    all_classes = []
    unused_functions = []
    unused_classes = []
    
    # Collect all functions
    for func in codebase.functions:
        if isinstance(func, Function):
            all_functions.append(func)
            usages = func.symbol_usages
            if len(usages) == 0:
                unused_functions.append(func)
    
    # Collect all classes  
    for cls in codebase.classes:
        if isinstance(cls, Class):
            all_classes.append(cls)
            usages = cls.symbol_usages
            if len(usages) == 0:
                unused_classes.append(cls)
    
    # Print all functions
    print(f"\n📋 ALL FUNCTIONS ({len(all_functions)} total):")
    print("-" * 40)
    for i, func in enumerate(all_functions, 1):
        usage_count = len(func.symbol_usages)
        status = "🔴 UNUSED" if usage_count == 0 else f"✅ {usage_count} usages"
        print(f"{i:3d}. {func.name:<30} | {func.file.name:<25} | {status}")
    
    # Print all classes
    print(f"\n📋 ALL CLASSES ({len(all_classes)} total):")
    print("-" * 40)
    for i, cls in enumerate(all_classes, 1):
        usage_count = len(cls.symbol_usages)
        status = "🔴 UNUSED" if usage_count == 0 else f"✅ {usage_count} usages"
        print(f"{i:3d}. {cls.name:<30} | {cls.file.name:<25} | {status}")
    
    # Summary of unused items
    print(f"\n" + "="*60)
    print("DEAD CODE ANALYSIS SUMMARY")
    print("="*60)
    print(f"🔍 Found {len(unused_functions)} potentially unused functions out of {len(all_functions)} total")
    print(f"🔍 Found {len(unused_classes)} potentially unused classes out of {len(all_classes)} total")
    
    if unused_functions:
        print(f"\n🔴 UNUSED FUNCTIONS:")
        for func in unused_functions:
            print(f"  - {func.name} in {func.file.name}")
    
    if unused_classes:
        print(f"\n🔴 UNUSED CLASSES:")
        for cls in unused_classes:
            print(f"  - {cls.name} in {cls.file.name}")
    
    # Show files with most symbols
    print(f"\n📁 Files with most symbols:")
    file_symbol_counts = []
    for file in codebase.files:
        symbol_count = len(file.symbols)
        if symbol_count > 0:
            file_symbol_counts.append((file.name, symbol_count))
    
    file_symbol_counts.sort(key=lambda x: x[1], reverse=True)
    for file_name, count in file_symbol_counts[:10]:
        print(f"  - {file_name}: {count} symbols")
    
    print(f"\n✅ Analysis complete!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure graph_sitter is properly installed")
except Exception as e:
    print(f"❌ Analysis error: {e}")
    import traceback
    traceback.print_exc()
