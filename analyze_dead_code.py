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
    
    # Find potentially unused symbols
    print("\n" + "="*60)
    print("DEAD CODE ANALYSIS")
    print("="*60)
    
    unused_functions = []
    unused_classes = []
    
    # Check functions
    for func in codebase.functions:
        if isinstance(func, Function):
            usages = func.symbol_usages
            if len(usages) == 0:
                unused_functions.append(func)
    
    # Check classes  
    for cls in codebase.classes:
        if isinstance(cls, Class):
            usages = cls.symbol_usages
            if len(usages) == 0:
                unused_classes.append(cls)
    
    print(f"\n🔍 Found {len(unused_functions)} potentially unused functions:")
    for func in unused_functions[:10]:  # Show first 10
        print(f"  - {func.name} in {func.file.name}")
    
    if len(unused_functions) > 10:
        print(f"  ... and {len(unused_functions) - 10} more")
    
    print(f"\n🔍 Found {len(unused_classes)} potentially unused classes:")
    for cls in unused_classes[:10]:  # Show first 10
        print(f"  - {cls.name} in {cls.file.name}")
    
    if len(unused_classes) > 10:
        print(f"  ... and {len(unused_classes) - 10} more")
    
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
