#!/usr/bin/env python3
"""
Test Symbol Information Retrieval
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena.core import SerenaCore, SerenaCapability

def test_symbol_information_retrieval():
    """Test that symbol information retrieval works with real codebase data."""
    
    print("🧪 Testing Symbol Information Retrieval...")
    
    try:
        # Initialize codebase
        print("   📁 Loading codebase...")
        codebase = Codebase(".")
        print(f"   ✅ Loaded {len(codebase.files)} files with {len(codebase.symbols)} symbols")
        
        # Initialize Serena with intelligence capability
        print("   ⚙️ Initializing Serena...")
        from graph_sitter.extensions.serena.types import SerenaConfig
        config = SerenaConfig(enabled_capabilities=[SerenaCapability.INTELLIGENCE])
        serena = SerenaCore(codebase, config)
        print("   ✅ Serena initialized")
        
        # Test symbol information retrieval on a known file
        test_file = "src/graph_sitter/core/codebase.py"
        test_line = 150  # Around the constructor area
        test_character = 10
        
        print(f"   🔍 Looking for symbol at {test_file}:{test_line}:{test_character}")
        symbol_info = serena.get_symbol_info(test_file, test_line, test_character)
        
        if symbol_info:
            print(f"   ✅ Found symbol: {symbol_info.name}")
            print(f"      Kind: {symbol_info.kind}")
            print(f"      Location: {symbol_info.file_path}:{symbol_info.line}:{symbol_info.character}")
            if symbol_info.documentation:
                print(f"      Documentation: {symbol_info.documentation[:100]}...")
            if symbol_info.type_annotation:
                print(f"      Type: {symbol_info.type_annotation}")
            
            # Validate the symbol info structure
            assert isinstance(symbol_info.name, str)
            assert isinstance(symbol_info.kind, str)
            assert isinstance(symbol_info.file_path, str)
            assert isinstance(symbol_info.line, int)
            assert isinstance(symbol_info.character, int)
            
            print("   ✅ Symbol info structure is valid")
            return True
        else:
            print("   ⚠️ No symbol found at specified position")
            
            # Try to find any symbol in the file
            print("   🔍 Searching for any symbol in the file...")
            for line_offset in range(0, 50, 5):  # Try different lines
                test_line_alt = test_line + line_offset
                symbol_info = serena.get_symbol_info(test_file, test_line_alt, test_character)
                if symbol_info:
                    print(f"   ✅ Found symbol at line {test_line_alt}: {symbol_info.name}")
                    return True
            
            print("   ❌ No symbols found in the test range")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during symbol information test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            if 'serena' in locals():
                serena.shutdown()
        except:
            pass

if __name__ == "__main__":
    success = test_symbol_information_retrieval()
    sys.exit(0 if success else 1)
