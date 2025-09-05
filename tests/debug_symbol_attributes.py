#!/usr/bin/env python3
"""
Debug symbol attributes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter.core.codebase import Codebase

def debug_symbol_attributes():
    """Debug what attributes symbols have."""
    
    print("🔍 Debugging symbol attributes...")
    
    try:
        # Initialize codebase
        print("   📁 Loading codebase...")
        codebase = Codebase(".")
        
        # Check a specific file
        test_file = "src/graph_sitter/core/codebase.py"
        file = codebase.get_file(test_file, optional=True)
        
        if file and file.symbols:
            symbol = file.symbols[0]  # Get first symbol
            print(f"   🔍 Examining symbol: {symbol.name}")
            print(f"   📝 Symbol type: {type(symbol).__name__}")
            print(f"   📋 Symbol attributes:")
            
            for attr in dir(symbol):
                if not attr.startswith('_'):
                    try:
                        value = getattr(symbol, attr)
                        if not callable(value):
                            print(f"      {attr}: {value} ({type(value).__name__})")
                    except:
                        print(f"      {attr}: <error accessing>")
            
            # Check if it has position info
            print(f"   📍 Position info:")
            for pos_attr in ['line_number', 'column_number', 'start_line', 'end_line', 'start_byte', 'end_byte']:
                if hasattr(symbol, pos_attr):
                    print(f"      {pos_attr}: {getattr(symbol, pos_attr)}")
                else:
                    print(f"      {pos_attr}: NOT FOUND")
                    
        # Also check a function symbol
        print("\n   🔍 Looking for function symbols...")
        for symbol in codebase.symbols[:50]:
            if 'Function' in type(symbol).__name__:
                print(f"   🔧 Function symbol: {symbol.name}")
                print(f"      Type: {type(symbol).__name__}")
                if hasattr(symbol, 'filepath'):
                    print(f"      File: {symbol.filepath}")
                for pos_attr in ['line_number', 'column_number', 'start_line', 'end_line']:
                    if hasattr(symbol, pos_attr):
                        print(f"      {pos_attr}: {getattr(symbol, pos_attr)}")
                break
                    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_symbol_attributes()

