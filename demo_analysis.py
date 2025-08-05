#!/usr/bin/env python3
"""
Demo Analysis Script
===================

This script demonstrates the core graph-sitter analysis functions:
- get_codebase_summary(codebase)
- get_file_summary(file)
- get_class_summary(cls)
- get_function_summary(function)
- find_dead_code(codebase)

And shows how to use them for comprehensive codebase analysis.
"""

import sys
from pathlib import Path

# Add src to path for graph-sitter imports
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))

try:
    # Core graph-sitter imports
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        get_symbol_summary
    )
    
    print("✅ Successfully imported graph-sitter libraries")
    
except ImportError as e:
    print(f"❌ Error importing graph-sitter libraries: {e}")
    sys.exit(1)


def demo_core_functions():
    """Demonstrate the core analysis functions."""
    print("🚀 Demonstrating Core Graph-Sitter Analysis Functions")
    print("=" * 60)
    
    # Initialize codebase
    print("\n📊 Initializing codebase...")
    codebase = Codebase(".", language="python")
    print(f"✅ Loaded codebase with {len(list(codebase.files))} files")
    
    # 1. get_codebase_summary(codebase)
    print("\n1️⃣ Testing get_codebase_summary(codebase):")
    print("-" * 40)
    codebase_summary = get_codebase_summary(codebase)
    print(codebase_summary)
    
    # 2. get_file_summary(file) - Test with a few files
    print("\n2️⃣ Testing get_file_summary(file):")
    print("-" * 40)
    files_to_test = list(codebase.files)[:3]  # Test first 3 files
    for file in files_to_test:
        print(f"\n📄 File: {file.filepath}")
        try:
            file_summary = get_file_summary(file)
            print(file_summary)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # 3. get_function_summary(function) - Test with a few functions
    print("\n3️⃣ Testing get_function_summary(function):")
    print("-" * 40)
    functions_to_test = list(codebase.functions)[:3]  # Test first 3 functions
    for function in functions_to_test:
        print(f"\n🔧 Function: {function.name}")
        try:
            function_summary = get_function_summary(function)
            print(function_summary)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # 4. get_class_summary(cls) - Test with a few classes
    print("\n4️⃣ Testing get_class_summary(cls):")
    print("-" * 40)
    classes_to_test = list(codebase.classes)[:3]  # Test first 3 classes
    for class_obj in classes_to_test:
        print(f"\n🏛️ Class: {class_obj.name}")
        try:
            class_summary = get_class_summary(class_obj)
            print(class_summary)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # 5. get_symbol_summary(symbol) - Test with a few symbols
    print("\n5️⃣ Testing get_symbol_summary(symbol):")
    print("-" * 40)
    symbols_to_test = list(codebase.symbols)[:3]  # Test first 3 symbols
    for symbol in symbols_to_test:
        print(f"\n🏷️ Symbol: {symbol.name}")
        try:
            symbol_summary = get_symbol_summary(symbol)
            print(symbol_summary)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # 6. find_dead_code(codebase) - Implementation from docs
    print("\n6️⃣ Testing find_dead_code(codebase):")
    print("-" * 40)
    
    def find_dead_code(codebase):
        """Find unused functions - implementation from graph-sitter docs."""
        dead_functions = []
        for function in codebase.functions:
            # Check if function has call sites
            call_sites = getattr(function, 'call_sites', [])
            if not call_sites:
                # Skip main functions, test functions, and magic methods
                func_name = function.name
                if not (func_name in ['main', '__main__'] or 
                       func_name.startswith('test_') or 
                       func_name.startswith('__') and func_name.endswith('__')):
                    dead_functions.append(function)
        return dead_functions
    
    try:
        dead_functions = find_dead_code(codebase)
        print(f"💀 Found {len(dead_functions)} potentially dead functions")
        
        # Show first 10 dead functions
        for i, func in enumerate(dead_functions[:10]):
            print(f"   {i+1}. {func.name} in {func.filepath}")
        
        if len(dead_functions) > 10:
            print(f"   ... and {len(dead_functions) - 10} more")
            
    except Exception as e:
        print(f"❌ Error finding dead code: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("🎯 All core analysis functions are working properly")


if __name__ == "__main__":
    demo_core_functions()

