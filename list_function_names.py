#!/usr/bin/env python3
"""
List all actual function names (both used and unused) in the graph_sitter package.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.function import Function
    
    print("🔍 Extracting all function names from graph_sitter package...")
    
    # Analyze the graph_sitter package itself
    graph_sitter_path = Path(__file__).parent / "src" / "graph_sitter"
    
    # Create a codebase instance
    codebase = Codebase(str(graph_sitter_path), language="python")
    
    all_functions = []
    used_functions = []
    unused_functions = []
    
    # Collect all functions
    for func in codebase.functions:
        if isinstance(func, Function):
            all_functions.append(func)
            usages = func.symbol_usages
            if len(usages) == 0:
                unused_functions.append(func)
            else:
                used_functions.append(func)
    
    # Sort alphabetically
    all_functions.sort(key=lambda x: x.name.lower())
    used_functions.sort(key=lambda x: x.name.lower())
    unused_functions.sort(key=lambda x: x.name.lower())
    
    print(f"\n" + "="*80)
    print(f"📋 ALL FUNCTION NAMES ({len(all_functions)} total)")
    print(f"="*80)
    
    for i, func in enumerate(all_functions, 1):
        usage_count = len(func.symbol_usages)
        status = "🔴 UNUSED" if usage_count == 0 else f"✅ {usage_count} usages"
        print(f"{i:3d}. {func.name}")
    
    print(f"\n" + "="*80)
    print(f"✅ USED FUNCTION NAMES ({len(used_functions)} total)")
    print(f"="*80)
    
    for i, func in enumerate(used_functions, 1):
        print(f"{i:3d}. {func.name}")
    
    print(f"\n" + "="*80)
    print(f"🔴 UNUSED FUNCTION NAMES ({len(unused_functions)} total)")
    print(f"="*80)
    
    for i, func in enumerate(unused_functions, 1):
        print(f"{i:3d}. {func.name}")
    
    print(f"\n" + "="*80)
    print(f"📊 SUMMARY")
    print(f"="*80)
    print(f"Total functions: {len(all_functions)}")
    print(f"Used functions: {len(used_functions)} ({len(used_functions)/len(all_functions)*100:.1f}%)")
    print(f"Unused functions: {len(unused_functions)} ({len(unused_functions)/len(all_functions)*100:.1f}%)")
    
    print(f"\n✅ Function name extraction complete!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure graph_sitter is properly installed")
except Exception as e:
    print(f"❌ Analysis error: {e}")
    import traceback
    traceback.print_exc()

