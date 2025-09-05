#!/usr/bin/env python3
"""
Debug symbol information
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter.core.codebase import Codebase

def debug_symbols():
    """Debug what symbols are available in the codebase."""
    
    print("🔍 Debugging symbol information...")
    
    try:
        # Initialize codebase
        print("   📁 Loading codebase...")
        codebase = Codebase(".")
        print(f"   ✅ Loaded {len(codebase.files)} files with {len(codebase.symbols)} symbols")
        
        # Check a specific file
        test_file = "src/graph_sitter/core/codebase.py"
        file = codebase.get_file(test_file, optional=True)
        
        if file:
            print(f"   📄 File: {test_file}")
            print(f"   📊 File has {len(file.symbols)} symbols")
            
            # Show first few symbols
            for i, symbol in enumerate(file.symbols[:10]):
                print(f"      Symbol {i+1}: {symbol.name}")
                print(f"         Type: {type(symbol).__name__}")
                if hasattr(symbol, 'line_number'):
                    print(f"         Line: {symbol.line_number}")
                if hasattr(symbol, 'column_number'):
                    print(f"         Column: {symbol.column_number}")
                if hasattr(symbol, 'start_line'):
                    print(f"         Range: {symbol.start_line}-{getattr(symbol, 'end_line', '?')}")
                print()
        else:
            print(f"   ❌ File not found: {test_file}")
            
        # Show some general symbols
        print("   🔍 First 10 symbols in codebase:")
        for i, symbol in enumerate(codebase.symbols[:10]):
            print(f"      {i+1}. {symbol.name} ({type(symbol).__name__})")
            if hasattr(symbol, 'filepath'):
                print(f"         File: {symbol.filepath}")
            if hasattr(symbol, 'line_number'):
                print(f"         Line: {symbol.line_number}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_symbols()

