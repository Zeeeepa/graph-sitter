#!/usr/bin/env python3
"""
Debug script to investigate why the comprehensive analysis is producing empty results
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph_sitter import Codebase
from graph_sitter.extensions.serena.advanced_api import SerenaAdvancedAPI

async def debug_analysis():
    print("🔍 DEBUGGING COMPREHENSIVE ANALYSIS")
    print("=" * 60)
    
    # Initialize codebase
    print("1. Initializing codebase...")
    codebase_path = Path.cwd()
    codebase = Codebase(str(codebase_path), language="python")
    print(f"   ✅ Codebase initialized at: {codebase_path}")
    
    # Check basic codebase properties
    print("\n2. Checking basic codebase properties...")
    try:
        nodes = codebase.ctx.get_nodes()
        print(f"   📊 Total nodes in graph: {len(nodes)}")
        
        # Check node types
        node_types = {}
        for node in nodes[:100]:  # Sample first 100 nodes
            node_type = getattr(node, 'node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("   🏗️ Node types (sample):")
        for node_type, count in node_types.items():
            print(f"      {node_type}: {count}")
            
    except Exception as e:
        print(f"   ❌ Error accessing nodes: {e}")
    
    # Check edges
    print("\n3. Checking graph edges...")
    try:
        edges = codebase.ctx.edges
        print(f"   🔗 Total edges in graph: {len(edges)}")
        
        # Sample some edges
        edge_types = {}
        for edge in edges[:100]:  # Sample first 100 edges
            edge_type = getattr(edge, 'type', 'unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        print("   🔗 Edge types (sample):")
        for edge_type, count in edge_types.items():
            print(f"      {edge_type}: {count}")
            
    except Exception as e:
        print(f"   ❌ Error accessing edges: {e}")
    
    # Initialize Serena API
    print("\n4. Initializing Serena API...")
    try:
        api = SerenaAdvancedAPI(codebase)
        print("   ✅ Serena API initialized")
    except Exception as e:
        print(f"   ❌ Error initializing Serena API: {e}")
        return
    
    # Test knowledge graph building
    print("\n5. Testing knowledge graph building...")
    try:
        knowledge_graph = await api.build_knowledge_graph()
        print(f"   📊 Knowledge graph type: {type(knowledge_graph)}")
        
        if isinstance(knowledge_graph, dict):
            print(f"   📊 Knowledge graph keys: {list(knowledge_graph.keys())}")
            
            # Check nodes
            nodes = knowledge_graph.get('nodes', {})
            print(f"   📊 Knowledge graph nodes: {len(nodes)}")
            
            # Sample some nodes
            if nodes:
                sample_keys = list(nodes.keys())[:5]
                print("   📊 Sample node keys:")
                for key in sample_keys:
                    print(f"      {key}")
                    
            # Check edges
            edges = knowledge_graph.get('edges', {})
            print(f"   📊 Knowledge graph edges: {len(edges)}")
            
        else:
            print(f"   ⚠️ Unexpected knowledge graph format: {knowledge_graph}")
            
    except Exception as e:
        print(f"   ❌ Error building knowledge graph: {e}")
        import traceback
        traceback.print_exc()
    
    # Test dependency analysis
    print("\n6. Testing dependency analysis...")
    try:
        # Get file nodes
        file_nodes = [node for node in codebase.ctx.get_nodes() 
                     if hasattr(node, 'node_type') and node.node_type == 'file']
        print(f"   📁 File nodes found: {len(file_nodes)}")
        
        if file_nodes:
            # Test with first file
            test_file = file_nodes[0]
            print(f"   🧪 Testing with file: {test_file.file_path}")
            
            # Try to get successors
            try:
                successors = codebase.ctx.successors(test_file.id, edge_type='imports')
                print(f"   🔗 Successors found: {len(successors)}")
                
                for i, successor in enumerate(successors[:3]):
                    print(f"      {i+1}. {getattr(successor, 'name', 'unknown')} ({type(successor)})")
                    
            except Exception as e:
                print(f"   ❌ Error getting successors: {e}")
                
    except Exception as e:
        print(f"   ❌ Error in dependency analysis: {e}")
    
    # Test error analysis
    print("\n7. Testing error analysis...")
    try:
        diagnostics = codebase.diagnostics
        print(f"   🐛 Diagnostics found: {len(diagnostics)}")
        
        error_count = len([d for d in diagnostics if d.is_error])
        print(f"   🐛 Errors found: {error_count}")
        
    except Exception as e:
        print(f"   ❌ Error in error analysis: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG ANALYSIS COMPLETE")

if __name__ == "__main__":
    asyncio.run(debug_analysis())
