#!/usr/bin/env python3
"""
Example usage of the codebase analysis functions.

This demonstrates how to use the summary functions to get insights
about codebases, files, classes, functions, and symbols.
"""

from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)


def demonstrate_codebase_analysis(codebase_path: str):
    """
    Demonstrate all the codebase analysis summary functions.
    
    Args:
        codebase_path: Path to the codebase to analyze
    """
    print(f"🔍 Analyzing codebase: {codebase_path}")
    
    # Initialize the codebase
    codebase = Codebase(codebase_path)
    
    # 1. Get overall codebase summary
    print("\n" + "="*60)
    print("📊 CODEBASE SUMMARY")
    print("="*60)
    codebase_summary = get_codebase_summary(codebase)
    print(codebase_summary)
    
    # 2. Get file summaries (show first 3 files)
    print("\n" + "="*60)
    print("📄 FILE SUMMARIES")
    print("="*60)
    for i, file in enumerate(list(codebase.files)[:3]):
        print(f"\n--- File {i+1} ---")
        file_summary = get_file_summary(file)
        print(file_summary)
    
    # 3. Get class summaries (show first 3 classes)
    print("\n" + "="*60)
    print("🏗️ CLASS SUMMARIES")
    print("="*60)
    for i, cls in enumerate(list(codebase.classes)[:3]):
        print(f"\n--- Class {i+1} ---")
        class_summary = get_class_summary(cls)
        print(class_summary)
    
    # 4. Get function summaries (show first 3 functions)
    print("\n" + "="*60)
    print("⚙️ FUNCTION SUMMARIES")
    print("="*60)
    for i, func in enumerate(list(codebase.functions)[:3]):
        print(f"\n--- Function {i+1} ---")
        function_summary = get_function_summary(func)
        print(function_summary)
    
    # 5. Get symbol summaries (show first 3 symbols)
    print("\n" + "="*60)
    print("🔗 SYMBOL SUMMARIES")
    print("="*60)
    for i, symbol in enumerate(list(codebase.symbols)[:3]):
        print(f"\n--- Symbol {i+1} ---")
        symbol_summary = get_symbol_summary(symbol)
        print(symbol_summary)


def get_specific_summaries(codebase_path: str, target_names: dict):
    """
    Get summaries for specific named entities.
    
    Args:
        codebase_path: Path to the codebase
        target_names: Dict with keys like 'file', 'class', 'function' and their names
    """
    codebase = Codebase(codebase_path)
    
    # Get specific file summary
    if 'file' in target_names:
        file_name = target_names['file']
        try:
            file = codebase.get_file(file_name)
            print(f"\n📄 Summary for file '{file_name}':")
            print(get_file_summary(file))
        except Exception as e:
            print(f"❌ Could not find file '{file_name}': {e}")
    
    # Get specific class summary
    if 'class' in target_names:
        class_name = target_names['class']
        try:
            cls = codebase.get_class(class_name)
            print(f"\n🏗️ Summary for class '{class_name}':")
            print(get_class_summary(cls))
        except Exception as e:
            print(f"❌ Could not find class '{class_name}': {e}")
    
    # Get specific function summary
    if 'function' in target_names:
        function_name = target_names['function']
        try:
            func = codebase.get_function(function_name)
            print(f"\n⚙️ Summary for function '{function_name}':")
            print(get_function_summary(func))
        except Exception as e:
            print(f"❌ Could not find function '{function_name}': {e}")
    
    # Get specific symbol summary
    if 'symbol' in target_names:
        symbol_name = target_names['symbol']
        try:
            symbol = codebase.get_symbol(symbol_name)
            print(f"\n🔗 Summary for symbol '{symbol_name}':")
            print(get_symbol_summary(symbol))
        except Exception as e:
            print(f"❌ Could not find symbol '{symbol_name}': {e}")


def quick_codebase_overview(codebase_path: str):
    """
    Get a quick overview of the codebase structure.
    
    Args:
        codebase_path: Path to the codebase
    """
    codebase = Codebase(codebase_path)
    
    print(f"🚀 Quick Overview of: {codebase_path}")
    print("="*50)
    
    # Overall stats
    print(get_codebase_summary(codebase))
    
    # Top files by symbol count
    files_with_symbols = [(file, len(file.symbols)) for file in codebase.files]
    files_with_symbols.sort(key=lambda x: x[1], reverse=True)
    
    print("\n📈 Top 5 files by symbol count:")
    for i, (file, symbol_count) in enumerate(files_with_symbols[:5]):
        print(f"  {i+1}. {file.name}: {symbol_count} symbols")
    
    # Most used symbols
    symbols_with_usages = [(symbol, len(symbol.symbol_usages)) for symbol in codebase.symbols]
    symbols_with_usages.sort(key=lambda x: x[1], reverse=True)
    
    print("\n🔥 Top 5 most used symbols:")
    for i, (symbol, usage_count) in enumerate(symbols_with_usages[:5]):
        print(f"  {i+1}. {symbol.name} ({type(symbol).__name__}): {usage_count} usages")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python example_usage.py <codebase_path> [mode]")
        print("Modes:")
        print("  full    - Complete analysis (default)")
        print("  quick   - Quick overview")
        print("  specific - Analyze specific entities")
        sys.exit(1)
    
    codebase_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "full"
    
    try:
        if mode == "full":
            demonstrate_codebase_analysis(codebase_path)
        elif mode == "quick":
            quick_codebase_overview(codebase_path)
        elif mode == "specific":
            # Example: analyze specific entities
            targets = {
                'file': 'main.py',  # Adjust these names based on your codebase
                'class': 'MyClass',
                'function': 'main'
            }
            get_specific_summaries(codebase_path, targets)
        else:
            print(f"❌ Unknown mode: {mode}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

