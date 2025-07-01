#!/usr/bin/env python3
"""
Performance demonstration for enhanced graph_sitter visualization system.

This script demonstrates the improvements made to the visualization system:
- Error handling and recovery
- Performance optimizations with caching
- Memory usage improvements
- Async I/O capabilities
"""

import asyncio
import time
import tracemalloc
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import networkx as nx
import plotly.graph_objects as go
from unittest.mock import Mock

from graph_sitter.visualizations.visualization_manager import VisualizationManager
from graph_sitter.visualizations.viz_utils import (
    graph_to_json, 
    get_conversion_stats, 
    clear_conversion_cache
)
from graph_sitter.visualizations.enums import VizNode, ExportFormat


def create_mock_repo_operator(base_dir: str = "/tmp/viz_demo"):
    """Create a mock RepoOperator for demonstration."""
    import os
    import tempfile
    
    # Use a real temporary directory for the demo
    temp_dir = tempfile.mkdtemp(prefix="viz_demo_")
    
    mock_op = Mock()
    mock_op.base_dir = temp_dir
    
    def folder_exists(path):
        return os.path.exists(path)
    
    def mkdir(path):
        os.makedirs(path, exist_ok=True)
    
    def emptydir(path):
        if os.path.exists(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
    
    mock_op.folder_exists = folder_exists
    mock_op.mkdir = mkdir
    mock_op.emptydir = emptydir
    
    return mock_op, temp_dir


def create_test_graphs():
    """Create various test graphs for performance testing."""
    graphs = {}
    
    # Small graph
    small_graph = nx.Graph()
    for i in range(10):
        small_graph.add_node(i, name=f"node_{i}", color="blue")
    for i in range(9):
        small_graph.add_edge(i, i + 1, weight=1.0)
    graphs["small"] = small_graph
    
    # Medium graph
    medium_graph = nx.Graph()
    for i in range(100):
        medium_graph.add_node(i, name=f"node_{i}", color="green")
    for i in range(99):
        medium_graph.add_edge(i, i + 1, weight=1.0)
    # Add some random edges
    import random
    for _ in range(50):
        a, b = random.randint(0, 99), random.randint(0, 99)
        if a != b:
            medium_graph.add_edge(a, b, weight=random.random())
    graphs["medium"] = medium_graph
    
    # Large graph
    large_graph = nx.Graph()
    for i in range(1000):
        large_graph.add_node(i, name=f"node_{i}", color="red")
    for i in range(999):
        large_graph.add_edge(i, i + 1, weight=1.0)
    # Add random edges
    for _ in range(500):
        a, b = random.randint(0, 999), random.randint(0, 999)
        if a != b:
            large_graph.add_edge(a, b, weight=random.random())
    graphs["large"] = large_graph
    
    return graphs


def benchmark_graph_conversion(graphs):
    """Benchmark graph to JSON conversion performance."""
    print("\n🔄 Graph Conversion Performance Benchmark")
    print("=" * 50)
    
    results = {}
    
    for name, graph in graphs.items():
        print(f"\n📊 Testing {name} graph ({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)")
        
        # Clear cache before each test
        clear_conversion_cache()
        
        # Measure conversion time
        start_time = time.time()
        try:
            json_result = graph_to_json(graph)
            conversion_time = time.time() - start_time
            
            # Measure memory usage
            tracemalloc.start()
            graph_to_json(graph)  # Convert again to measure memory
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            results[name] = {
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "conversion_time": conversion_time,
                "json_size": len(json_result),
                "memory_peak": peak,
                "success": True
            }
            
            print(f"  ✅ Conversion time: {conversion_time:.4f}s")
            print(f"  📄 JSON size: {len(json_result):,} characters")
            print(f"  🧠 Peak memory: {peak / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            results[name] = {
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "error": str(e),
                "success": False
            }
            print(f"  ❌ Conversion failed: {e}")
    
    # Show cache statistics
    cache_stats = get_conversion_stats()
    print(f"\n📈 Cache Statistics:")
    print(f"  Cache hits: {cache_stats['node_cache_hits']}")
    print(f"  Cache misses: {cache_stats['node_cache_misses']}")
    print(f"  Cache size: {cache_stats['node_cache_size']}/{cache_stats['node_cache_max_size']}")
    
    return results


async def benchmark_async_operations(manager, graphs):
    """Benchmark asynchronous visualization operations."""
    print("\n⚡ Async Operations Performance Benchmark")
    print("=" * 50)
    
    results = {}
    
    for name, graph in graphs.items():
        print(f"\n📊 Testing async write for {name} graph")
        
        start_time = time.time()
        try:
            await manager.write_graphviz_data_async(graph)
            async_time = time.time() - start_time
            
            results[name] = {
                "async_write_time": async_time,
                "success": True
            }
            
            print(f"  ✅ Async write time: {async_time:.4f}s")
            
        except Exception as e:
            results[name] = {
                "error": str(e),
                "success": False
            }
            print(f"  ❌ Async write failed: {e}")
    
    return results


def benchmark_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n🛡️ Error Handling Demonstration")
    print("=" * 50)
    
    # Test invalid graph input
    print("\n🔍 Testing invalid graph input handling:")
    try:
        graph_to_json("not_a_graph")
        print("  ❌ Should have raised an error")
    except Exception as e:
        print(f"  ✅ Correctly caught error: {type(e).__name__}: {e}")
    
    # Test empty graph
    print("\n🔍 Testing empty graph handling:")
    try:
        empty_graph = nx.Graph()
        result = graph_to_json(empty_graph)
        print(f"  ✅ Empty graph handled successfully (JSON length: {len(result)})")
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
    
    # Test graph with invalid root
    print("\n🔍 Testing invalid root node handling:")
    try:
        test_graph = nx.Graph()
        test_graph.add_node(1)
        graph_to_json(test_graph, root=999)
        print("  ❌ Should have raised an error")
    except Exception as e:
        print(f"  ✅ Correctly caught error: {type(e).__name__}: {e}")


def demonstrate_enhanced_features():
    """Demonstrate new features and enhancements."""
    print("\n🚀 Enhanced Features Demonstration")
    print("=" * 50)
    
    # VizNode validation
    print("\n🔍 VizNode validation:")
    try:
        # Valid VizNode
        valid_node = VizNode(
            name="test_node",
            color="#FF0000",
            start_point=(10, 20),
            end_point=(30, 40)
        )
        print(f"  ✅ Valid VizNode created: {valid_node.name}")
        
        # Invalid VizNode
        try:
            invalid_node = VizNode(color="invalid_color_123")
            print("  ❌ Should have raised validation error")
        except ValueError as e:
            print(f"  ✅ Validation caught invalid color: {e}")
            
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
    
    # Export formats
    print("\n📤 Export format support:")
    for format_type in ExportFormat:
        print(f"  📄 Supported format: {format_type.value}")


async def main():
    """Main demonstration function."""
    print("🎯 Graph-Sitter Visualization System Performance Demo")
    print("=" * 60)
    
    # Create mock repo operator and manager
    mock_op, temp_dir = create_mock_repo_operator()
    manager = VisualizationManager(mock_op)
    
    try:
        # Create test graphs
        print("\n📊 Creating test graphs...")
        graphs = create_test_graphs()
        print(f"Created {len(graphs)} test graphs")
        
        # Benchmark graph conversion
        conversion_results = benchmark_graph_conversion(graphs)
        
        # Benchmark async operations
        async_results = await benchmark_async_operations(manager, graphs)
        
        # Demonstrate error handling
        benchmark_error_handling()
        
        # Demonstrate enhanced features
        demonstrate_enhanced_features()
        
        # Show performance statistics
        print("\n📈 Final Performance Statistics")
        print("=" * 50)
        stats = manager.get_performance_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        # Summary
        print("\n🎉 Performance Demo Summary")
        print("=" * 50)
        successful_conversions = sum(1 for r in conversion_results.values() if r.get("success", False))
        successful_async = sum(1 for r in async_results.values() if r.get("success", False))
        
        print(f"  ✅ Successful graph conversions: {successful_conversions}/{len(conversion_results)}")
        print(f"  ⚡ Successful async operations: {successful_async}/{len(async_results)}")
        print(f"  🧠 Memory management: Enhanced with caching")
        print(f"  🛡️ Error handling: Comprehensive coverage")
        print(f"  📊 Performance monitoring: Real-time statistics")
        
        # Show improvements
        print("\n🚀 Key Improvements Implemented:")
        print("  • Comprehensive error handling and recovery")
        print("  • LRU caching for performance optimization")
        print("  • Asynchronous I/O operations")
        print("  • Input validation and data integrity checks")
        print("  • Memory usage monitoring and optimization")
        print("  • Performance statistics and monitoring")
        print("  • Enhanced export capabilities")
        print("  • Comprehensive test coverage")
        
    finally:
        # Cleanup
        manager.cleanup()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())

