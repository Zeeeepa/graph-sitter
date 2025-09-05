#!/usr/bin/env python3
"""
Debug semantic search
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter.core.codebase import Codebase

def debug_semantic_search():
    """Debug semantic search functionality."""
    
    print("🔍 Debugging semantic search...")
    
    try:
        # Initialize codebase
        print("   📁 Loading codebase...")
        codebase = Codebase(".")
        
        # Check symbols
        print(f"   📊 Total symbols: {len(codebase.symbols)}")
        
        # Test search manually
        query = "codebase"
        print(f"   🔍 Searching for '{query}' manually...")
        
        matches = []
        for symbol in codebase.symbols[:100]:  # Check first 100 symbols
            if query.lower() in symbol.name.lower():
                matches.append(symbol)
                print(f"      ✅ Match: {symbol.name} in {symbol.filepath}")
                if len(matches) >= 5:
                    break
        
        if not matches:
            print("   ❌ No matches found in first 100 symbols")
            print("   📝 Sample symbol names:")
            for i, symbol in enumerate(codebase.symbols[:10]):
                print(f"      {i+1}. {symbol.name}")
        
        # Try different queries
        for test_query in ["test", "debug", "symbol", "py"]:
            print(f"   🔍 Testing query '{test_query}'...")
            count = 0
            for symbol in codebase.symbols[:50]:
                if test_query.lower() in symbol.name.lower():
                    count += 1
                    if count == 1:
                        print(f"      ✅ First match: {symbol.name}")
            print(f"      Found {count} matches in first 50 symbols")
            if count > 0:
                break
                    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_semantic_search()

