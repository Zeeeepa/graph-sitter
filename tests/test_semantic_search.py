#!/usr/bin/env python3
"""
Test Semantic Search Implementation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena.core import SerenaCore, SerenaCapability
from graph_sitter.extensions.serena.types import SerenaConfig

def test_semantic_search():
    """Test that semantic search works with real codebase data."""
    
    print("🧪 Testing Semantic Search...")
    
    try:
        # Initialize codebase
        print("   📁 Loading codebase...")
        codebase = Codebase(".")
        print(f"   ✅ Loaded {len(codebase.files)} files with {len(codebase.symbols)} symbols")
        
        # Initialize Serena with intelligence and search capabilities
        print("   ⚙️ Initializing Serena...")
        config = SerenaConfig(enabled_capabilities=[SerenaCapability.INTELLIGENCE, SerenaCapability.SEARCH])
        serena = SerenaCore(codebase, config)
        print("   ✅ Serena initialized")
        
        # Test semantic search for common terms
        test_queries = ["codebase", "function", "class", "symbol", "file"]
        
        for query in test_queries:
            print(f"   🔍 Searching for '{query}'...")
            results = serena.semantic_search(query, max_results=5)
            
            if results:
                print(f"      ✅ Found {len(results)} results:")
                for i, result in enumerate(results[:3]):  # Show first 3
                    print(f"         {i+1}. {result['symbol_name']} ({result['symbol_type']})")
                    print(f"            File: {result['file']}:{result['line']}")
                    print(f"            Score: {result['score']:.2f}")
                    if result.get('context'):
                        snippet = result['context'][:50] + "..." if len(result['context']) > 50 else result['context']
                        print(f"            Context: {snippet}")
                
                # Validate result structure
                result = results[0]
                assert isinstance(result['symbol_name'], str)
                assert isinstance(result['file'], str)
                assert isinstance(result['line'], int)
                assert isinstance(result['symbol_type'], str)
                assert isinstance(result['score'], (int, float))
                
                print(f"      ✅ Search results structure is valid")
                break
        else:
            print("   ❌ No search results found for any query")
            return False
        
        # Test empty query
        print("   🔍 Testing empty query...")
        empty_results = serena.semantic_search("", max_results=5)
        print(f"      ✅ Empty query returned {len(empty_results)} results")
        
        # Test non-existent query
        print("   🔍 Testing non-existent query...")
        no_results = serena.semantic_search("xyznonexistent123", max_results=5)
        print(f"      ✅ Non-existent query returned {len(no_results)} results")
        
        print("🎉 All semantic search tests passed!")
        return True
            
    except Exception as e:
        print(f"   ❌ Error during semantic search test: {e}")
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
    success = test_semantic_search()
    sys.exit(0 if success else 1)
