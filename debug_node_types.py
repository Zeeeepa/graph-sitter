#!/usr/bin/env python3
"""
Debug script to understand the actual node and edge types in the graph
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph_sitter import Codebase

def debug_node_types():
    print("🔍 DEBUGGING NODE AND EDGE TYPES")
    print("=" * 60)
    
    # Initialize codebase
    print("1. Initializing codebase...")
    codebase_path = Path.cwd()
    codebase = Codebase(str(codebase_path), language="python")
    print(f"   ✅ Codebase initialized")
    
    # Get nodes and analyze their types
    print("\n2. Analyzing node types...")
    nodes = codebase.ctx.get_nodes()
    print(f"   📊 Total nodes: {len(nodes)}")
    
    # Sample nodes and their attributes
    print("\n   🔍 Sample node analysis:")
    for i, node in enumerate(nodes[:10]):
        print(f"   Node {i+1}:")
        print(f"      Type: {type(node)}")
        print(f"      Node type: {getattr(node, 'node_type', 'N/A')}")
        print(f"      ID: {getattr(node, 'id', 'N/A')}")
        print(f"      Name: {getattr(node, 'name', 'N/A')}")
        print(f"      File path: {getattr(node, 'file_path', 'N/A')}")
        print(f"      All attributes: {[attr for attr in dir(node) if not attr.startswith('_')]}")
        print()
    
    # Check if there are different ways to identify file nodes
    print("\n3. Looking for file nodes...")
    file_candidates = []
    
    for node in nodes[:100]:  # Check first 100 nodes
        # Check various ways a node might be identified as a file
        if hasattr(node, 'file_path'):
            file_candidates.append(node)
        elif hasattr(node, 'path'):
            file_candidates.append(node)
        elif str(type(node)).lower().find('file') != -1:
            file_candidates.append(node)
    
    print(f"   📁 Potential file nodes found: {len(file_candidates)}")
    
    if file_candidates:
        print("   📁 Sample file node:")
        file_node = file_candidates[0]
        print(f"      Type: {type(file_node)}")
        print(f"      Node type: {getattr(file_node, 'node_type', 'N/A')}")
        print(f"      File path: {getattr(file_node, 'file_path', 'N/A')}")
        print(f"      Path: {getattr(file_node, 'path', 'N/A')}")
    
    # Analyze edges
    print("\n4. Analyzing edge types...")
    edges = codebase.ctx.edges
    print(f"   🔗 Total edges: {len(edges)}")
    
    print("\n   🔍 Sample edge analysis:")
    for i, edge in enumerate(edges[:5]):
        print(f"   Edge {i+1}:")
        print(f"      Type: {type(edge)}")
        print(f"      Edge type: {getattr(edge, 'type', 'N/A')}")
        print(f"      Source: {getattr(edge, 'source', 'N/A')}")
        print(f"      Target: {getattr(edge, 'target', 'N/A')}")
        print(f"      All attributes: {[attr for attr in dir(edge) if not attr.startswith('_')]}")
        print()
    
    # Check for import edges specifically
    print("\n5. Looking for import edges...")
    import_candidates = []
    
    for edge in edges[:100]:  # Check first 100 edges
        edge_type = getattr(edge, 'type', None)
        if edge_type and ('import' in str(edge_type).lower() or str(edge_type) == 'imports'):
            import_candidates.append(edge)
    
    print(f"   📦 Potential import edges found: {len(import_candidates)}")
    
    if import_candidates:
        print("   📦 Sample import edge:")
        import_edge = import_candidates[0]
        print(f"      Type: {type(import_edge)}")
        print(f"      Edge type: {getattr(import_edge, 'type', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG COMPLETE")

if __name__ == "__main__":
    debug_node_types()
