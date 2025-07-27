#!/usr/bin/env python3
"""
Performance Optimization Demo for Serena Analysis

This demo showcases the performance enhancements added to Serena analysis,
including intelligent caching, parallel processing, and memory optimization.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def demo_caching_system():
    """Demonstrate intelligent caching capabilities."""
    print("🚀 Testing Intelligent Caching System")
    print("=" * 50)
    
    try:
        from graph_sitter.extensions.serena.performance import (
            get_cache, configure_cache, cached_analysis, batch_cached_analysis
        )
        
        # Configure cache for demo
        configure_cache(max_entries=100, default_ttl=300.0, max_memory_mb=10.0)
        cache = get_cache()
        
        print("✅ Cache system initialized")
        print(f"📊 Initial cache stats: {cache.get_stats()}")
        
        # Demo cached analysis decorator
        @cached_analysis("demo_analysis")
        def expensive_analysis(file_path: str, complexity: int = 1):
            """Simulate expensive analysis operation."""
            time.sleep(0.1 * complexity)  # Simulate work
            return {
                'file_path': file_path,
                'analysis_result': f"Analysis complete for {Path(file_path).name}",
                'complexity_score': complexity * 10,
                'timestamp': time.time()
            }
        
        # Test caching with multiple calls
        test_files = [
            "src/example1.py",
            "src/example2.py", 
            "src/example3.py"
        ]
        
        print("\n🔄 Running analysis (first time - no cache):")
        start_time = time.time()
        
        for file_path in test_files:
            result = expensive_analysis(file_path, complexity=2)
            print(f"  - {Path(file_path).name}: {result['complexity_score']}")
        
        first_run_time = time.time() - start_time
        print(f"⏱️  First run time: {first_run_time:.2f}s")
        
        print("\n🔄 Running analysis (second time - cached):")
        start_time = time.time()
        
        for file_path in test_files:
            result = expensive_analysis(file_path, complexity=2)
            print(f"  - {Path(file_path).name}: {result['complexity_score']}")
        
        second_run_time = time.time() - start_time
        print(f"⏱️  Second run time: {second_run_time:.2f}s")
        
        speedup = first_run_time / second_run_time if second_run_time > 0 else float('inf')
        print(f"🚀 Speedup: {speedup:.1f}x")
        
        # Show cache statistics
        final_stats = cache.get_stats()
        print(f"\n📊 Final cache stats:")
        print(f"  - Entries: {final_stats['entries']}")
        print(f"  - Hit rate: {final_stats['hit_rate']:.1%}")
        print(f"  - Memory usage: {final_stats['memory_usage_mb']:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Caching demo failed: {e}")
        return False


def demo_parallel_processing():
    """Demonstrate parallel processing capabilities."""
    print("\n⚡ Testing Parallel Processing System")
    print("=" * 50)
    
    try:
        from graph_sitter.extensions.serena.performance import (
            ParallelAnalyzer, parallel_analysis, batch_analyze_files
        )
        
        def cpu_intensive_analysis(file_path: str, iterations: int = 1000):
            """Simulate CPU-intensive analysis."""
            result = 0
            for i in range(iterations):
                result += i * hash(file_path) % 1000
            
            return {
                'file_path': file_path,
                'result': result,
                'iterations': iterations
            }
        
        # Test files
        test_files = [f"src/test_file_{i}.py" for i in range(20)]
        
        print(f"📁 Analyzing {len(test_files)} files...")
        
        # Sequential analysis
        print("\n🐌 Sequential analysis:")
        start_time = time.time()
        
        sequential_results = []
        for file_path in test_files:
            result = cpu_intensive_analysis(file_path, iterations=500)
            sequential_results.append(result)
        
        sequential_time = time.time() - start_time
        print(f"⏱️  Sequential time: {sequential_time:.2f}s")
        
        # Parallel analysis
        print("\n🚀 Parallel analysis:")
        start_time = time.time()
        
        parallel_results = parallel_analysis(
            operation="cpu_intensive",
            analysis_func=cpu_intensive_analysis,
            file_paths=test_files,
            parameters={'iterations': 500},
            max_workers=4
        )
        
        parallel_time = time.time() - start_time
        print(f"⏱️  Parallel time: {parallel_time:.2f}s")
        
        # Calculate speedup
        speedup = sequential_time / parallel_time if parallel_time > 0 else float('inf')
        print(f"🚀 Speedup: {speedup:.1f}x")
        
        # Verify results
        successful_results = [r for r in parallel_results if r.error is None]
        print(f"✅ Successful analyses: {len(successful_results)}/{len(test_files)}")
        
        # Test batch analysis with multiple operations
        print("\n🔄 Testing batch analysis with multiple operations:")
        
        def simple_analysis(file_path: str):
            return {'file_path': file_path, 'lines': hash(file_path) % 100}
        
        def complexity_analysis(file_path: str):
            return {'file_path': file_path, 'complexity': hash(file_path) % 20}
        
        batch_results = batch_analyze_files(
            analysis_functions={
                'simple': simple_analysis,
                'complexity': complexity_analysis
            },
            file_paths=test_files[:5],  # Smaller set for demo
            max_workers=2
        )
        
        print(f"📊 Batch analysis results:")
        for operation, results in batch_results.items():
            successful = [r for r in results if r.error is None]
            print(f"  - {operation}: {len(successful)} successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Parallel processing demo failed: {e}")
        return False


def demo_memory_optimization():
    """Demonstrate memory optimization capabilities."""
    print("\n🧠 Testing Memory Optimization System")
    print("=" * 50)
    
    try:
        from graph_sitter.extensions.serena.performance import (
            get_memory_optimizer, get_memory_stats, memory_efficient_analysis,
            optimize_memory_usage, MemoryOptimizer
        )
        
        # Get initial memory stats
        initial_stats = get_memory_stats()
        print(f"📊 Initial memory usage:")
        print(f"  - Process memory: {initial_stats.process_memory_mb:.1f} MB")
        print(f"  - System memory: {initial_stats.memory_percent:.1f}% used")
        
        # Create memory optimizer
        optimizer = get_memory_optimizer()
        print(f"✅ Memory optimizer initialized")
        
        # Simulate memory-intensive operations
        print(f"\n🔄 Running memory-intensive operations:")
        
        large_data = []
        
        with memory_efficient_analysis(enable_gc=True, gc_frequency=50) as context:
            for i in range(100):
                # Simulate creating large data structures
                class DataObject:
                    def __init__(self, id_val, content, metadata):
                        self.id = id_val
                        self.content = content
                        self.metadata = metadata
                
                data = DataObject(i, 'x' * 1000, list(range(100)))
                large_data.append(data)
                
                # Register object for tracking (use class instance instead of dict)
                optimizer.register_object(data)
                
                # Checkpoint every 25 operations
                if i % 25 == 0:
                    context.checkpoint()
                    stats = context.get_stats()
                    print(f"  - Step {i}: {stats.process_memory_mb:.1f} MB")
        
        # Check tracked objects
        tracked_count = optimizer.get_tracked_objects_count()
        print(f"📈 Tracked objects: {tracked_count}")
        
        # Optimize memory usage
        print(f"\n🧹 Optimizing memory usage:")
        optimization_result = optimize_memory_usage()
        
        print(f"📊 Optimization results:")
        print(f"  - Memory freed: {optimization_result['memory_freed_mb']:.1f} MB")
        print(f"  - Objects collected: {optimization_result['objects_collected']}")
        
        # Final memory stats
        final_stats = get_memory_stats()
        memory_delta = final_stats.process_memory_mb - initial_stats.process_memory_mb
        print(f"\n📊 Final memory usage:")
        print(f"  - Process memory: {final_stats.process_memory_mb:.1f} MB")
        print(f"  - Memory change: {memory_delta:+.1f} MB")
        
        # Test streaming analyzer
        print(f"\n🌊 Testing streaming analysis:")
        
        from graph_sitter.extensions.serena.performance.memory import StreamingAnalyzer
        
        def chunk_analyzer(chunk: str, chunk_num: int, file_path: str, **kwargs):
            return {
                'chunk_num': chunk_num,
                'chunk_size': len(chunk),
                'word_count': len(chunk.split()),
                'file_path': file_path
            }
        
        # Create a temporary file for streaming demo
        temp_file = Path("temp_demo_file.txt")
        with open(temp_file, 'w') as f:
            f.write("This is a demo file for streaming analysis. " * 1000)
        
        try:
            streaming_analyzer = StreamingAnalyzer(chunk_size=1024)
            chunk_results = list(streaming_analyzer.analyze_file_streaming(
                temp_file, chunk_analyzer
            ))
            
            total_words = sum(r.get('word_count', 0) for r in chunk_results)
            print(f"  - Processed {len(chunk_results)} chunks")
            print(f"  - Total words: {total_words}")
            
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Memory optimization demo failed: {e}")
        return False


async def demo_async_analysis():
    """Demonstrate async analysis capabilities."""
    print("\n🔄 Testing Async Analysis System")
    print("=" * 50)
    
    try:
        from graph_sitter.extensions.serena.performance.parallel import AsyncAnalyzer
        
        async def async_analysis_func(file_path: str, delay: float = 0.1):
            """Simulate async I/O intensive analysis."""
            await asyncio.sleep(delay)  # Simulate I/O wait
            return {
                'file_path': file_path,
                'analysis_type': 'async_io',
                'delay': delay,
                'timestamp': time.time()
            }
        
        # Test files
        test_files = [f"src/async_test_{i}.py" for i in range(10)]
        
        # Create async analyzer
        analyzer = AsyncAnalyzer(max_concurrent=5)
        
        print(f"📁 Analyzing {len(test_files)} files asynchronously...")
        
        start_time = time.time()
        results = await analyzer.analyze_files(
            operation="async_io_test",
            file_paths=test_files,
            analysis_func=async_analysis_func,
            delay=0.1
        )
        
        async_time = time.time() - start_time
        
        successful_results = [r for r in results if r.error is None]
        print(f"✅ Completed {len(successful_results)} analyses in {async_time:.2f}s")
        print(f"📊 Average time per file: {async_time / len(test_files):.3f}s")
        
        # Show analyzer stats
        stats = analyzer.get_stats()
        print(f"📈 Async analyzer stats:")
        print(f"  - Max concurrent: {stats['max_concurrent']}")
        print(f"  - Success rate: {stats['success_rate']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Async analysis demo failed: {e}")
        return False


async def main():
    """Run the comprehensive performance optimization demo."""
    print("🚀 Serena Performance Optimization Demo")
    print("=" * 60)
    print("Testing performance enhancements...\n")
    
    results = []
    
    # Test each performance component
    results.append(("Intelligent Caching", demo_caching_system()))
    results.append(("Parallel Processing", demo_parallel_processing()))
    results.append(("Memory Optimization", demo_memory_optimization()))
    results.append(("Async Analysis", await demo_async_analysis()))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Performance Optimization Test Results")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for feature, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{feature:<25} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All performance optimization tests passed!")
        print("\n🚀 Performance enhancements ready for production:")
        print("   • Intelligent caching with file-based invalidation")
        print("   • Parallel processing with thread/process pools")
        print("   • Memory optimization with automatic GC")
        print("   • Async analysis for I/O intensive operations")
        print("   • Streaming analysis for large files")
        print("   • Batch processing with memory management")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Some performance features may not be available.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
