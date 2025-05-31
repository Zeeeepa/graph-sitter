"""
Performance Optimization Demo

Comprehensive demonstration of the performance optimization and scalability enhancements.
"""

import asyncio
import time
from typing import List

# Import the performance optimization modules
from graph_sitter.performance import (
    CacheManager, CacheStrategy,
    MemoryManager, MemoryStrategy,
    PerformanceMonitor, MetricsCollector,
    OptimizationEngine, OptimizationStrategy,
    AdvancedProfiler, ProfilerConfig,
    ScalabilityManager, LoadBalancingStrategy,
    get_performance_integration
)

from graph_sitter.performance.integration import (
    optimize_file_ops,
    optimize_parsing,
    optimize_types,
    optimize_imports,
    optimize_graph,
    optimize_database
)


def demo_basic_optimization():
    """Demonstrate basic performance optimization"""
    print("🚀 Basic Performance Optimization Demo")
    print("=" * 50)
    
    # Get optimization engine
    engine = OptimizationEngine()
    
    # Example function to optimize
    @engine.optimize(OptimizationStrategy.CPU_OPTIMIZED, cache_key="fibonacci")
    def fibonacci(n: int) -> int:
        """Fibonacci calculation with optimization"""
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)
    
    # Test performance
    start_time = time.time()
    result = fibonacci(35)
    end_time = time.time()
    
    print(f"Fibonacci(35) = {result}")
    print(f"Execution time: {end_time - start_time:.4f} seconds")
    
    # Get metrics
    metrics = engine.get_global_metrics()
    print(f"Optimization metrics: {metrics}")
    print()


def demo_advanced_caching():
    """Demonstrate advanced caching strategies"""
    print("💾 Advanced Caching Demo")
    print("=" * 50)
    
    # Create cache manager
    cache_manager = CacheManager()
    
    # Create different cache types
    lru_cache = cache_manager.create_cache("lru_demo", CacheStrategy.LRU, max_size=100)
    lfu_cache = cache_manager.create_cache("lfu_demo", CacheStrategy.LFU, max_size=100)
    
    # Example cached function
    @cache_manager.cached(cache_name="lru_demo", ttl=60)
    def expensive_computation(x: int, y: int) -> int:
        """Simulate expensive computation"""
        time.sleep(0.1)  # Simulate work
        return x * y + x ** 2
    
    # Test caching performance
    print("First call (cache miss):")
    start_time = time.time()
    result1 = expensive_computation(10, 20)
    end_time = time.time()
    print(f"Result: {result1}, Time: {end_time - start_time:.4f}s")
    
    print("Second call (cache hit):")
    start_time = time.time()
    result2 = expensive_computation(10, 20)
    end_time = time.time()
    print(f"Result: {result2}, Time: {end_time - start_time:.4f}s")
    
    # Show cache statistics
    stats = cache_manager.get_all_stats()
    print(f"Cache statistics: {stats}")
    print()


def demo_memory_optimization():
    """Demonstrate memory optimization"""
    print("🧠 Memory Optimization Demo")
    print("=" * 50)
    
    # Create memory manager
    memory_manager = MemoryManager()
    
    # Example memory-optimized function
    @memory_manager.optimize_memory(MemoryStrategy.AGGRESSIVE)
    def memory_intensive_task(size: int) -> List[int]:
        """Simulate memory-intensive task"""
        data = list(range(size))
        # Simulate processing
        result = [x * 2 for x in data if x % 2 == 0]
        return result
    
    # Test memory optimization
    print("Running memory-intensive task...")
    start_stats = memory_manager.get_global_stats()
    
    result = memory_intensive_task(100000)
    
    end_stats = memory_manager.get_global_stats()
    
    print(f"Processed {len(result)} items")
    print(f"Memory stats before: {start_stats['system_memory'].used_memory / 1024 / 1024:.2f} MB")
    print(f"Memory stats after: {end_stats['system_memory'].used_memory / 1024 / 1024:.2f} MB")
    print()


def demo_performance_monitoring():
    """Demonstrate performance monitoring"""
    print("📊 Performance Monitoring Demo")
    print("=" * 50)
    
    # Create performance monitor
    monitor = PerformanceMonitor()
    
    # Example monitored function
    @monitor.monitor_function("demo_function", track_errors=True, track_duration=True)
    def monitored_function(iterations: int) -> int:
        """Function with performance monitoring"""
        total = 0
        for i in range(iterations):
            total += i ** 2
            if i % 10000 == 0:
                time.sleep(0.001)  # Simulate some work
        return total
    
    # Run monitored function
    print("Running monitored function...")
    result = monitored_function(50000)
    print(f"Result: {result}")
    
    # Get performance summary
    summary = monitor.get_performance_summary()
    print("Performance Summary:")
    for metric_name, metric_data in summary['metrics'].items():
        if metric_data['current_value'] is not None:
            print(f"  {metric_name}: {metric_data['current_value']}")
    print()


def demo_scalability():
    """Demonstrate scalability features"""
    print("⚡ Scalability Demo")
    print("=" * 50)
    
    # Create scalability manager
    scalability_manager = ScalabilityManager()
    
    # Example distributed function
    @scalability_manager.distributed_execution()
    def parallel_task(data: List[int]) -> int:
        """Task that can be distributed"""
        return sum(x ** 2 for x in data)
    
    # Test distributed execution
    print("Running distributed tasks...")
    
    # Create test data
    data_chunks = [
        list(range(i * 1000, (i + 1) * 1000))
        for i in range(5)
    ]
    
    start_time = time.time()
    results = []
    for chunk in data_chunks:
        result = parallel_task(chunk)
        results.append(result)
    end_time = time.time()
    
    print(f"Processed {len(data_chunks)} chunks")
    print(f"Total result: {sum(results)}")
    print(f"Execution time: {end_time - start_time:.4f} seconds")
    
    # Get scalability stats
    stats = scalability_manager.get_global_stats()
    print(f"Scalability stats: {stats['default']['worker_pool']}")
    print()


def demo_profiling():
    """Demonstrate advanced profiling"""
    print("🔍 Advanced Profiling Demo")
    print("=" * 50)
    
    # Create profiler
    config = ProfilerConfig(
        enable_cpu_profiling=True,
        enable_memory_profiling=True,
        enable_function_profiling=True
    )
    profiler = AdvancedProfiler(config)
    
    # Example profiled function
    @profiler.profile_function("demo_profiled_function")
    def profiled_function(n: int) -> int:
        """Function with detailed profiling"""
        result = 0
        for i in range(n):
            result += i ** 2
            if i % 1000 == 0:
                # Simulate some memory allocation
                temp_data = [j for j in range(100)]
                result += sum(temp_data)
        return result
    
    # Run with profiling
    print("Running profiled function...")
    with profiler.profile_context():
        result = profiled_function(10000)
        print(f"Result: {result}")
    
    # Get profiling summary
    summary = profiler.get_profiling_summary()
    print("Profiling Summary:")
    print(f"  Function count: {summary.get('function_count', 0)}")
    if 'top_functions' in summary:
        print("  Top functions by execution time:")
        for func_data in summary['top_functions'][:3]:
            print(f"    {func_data['function_name']}: {func_data['total_time']:.4f}s")
    print()


def demo_integration_decorators():
    """Demonstrate integration decorators"""
    print("🔧 Integration Decorators Demo")
    print("=" * 50)
    
    # Example functions with different optimizations
    @optimize_file_ops
    def file_operation_example(filename: str) -> str:
        """Simulated file operation"""
        time.sleep(0.01)  # Simulate file I/O
        return f"Processed file: {filename}"
    
    @optimize_parsing
    def parsing_operation_example(code: str) -> dict:
        """Simulated parsing operation"""
        time.sleep(0.02)  # Simulate parsing work
        return {"tokens": len(code.split()), "lines": len(code.split('\n'))}
    
    @optimize_types
    def type_resolution_example(symbol: str) -> str:
        """Simulated type resolution"""
        time.sleep(0.005)  # Simulate type analysis
        return f"Type of {symbol}: ComplexType"
    
    @optimize_imports
    def import_analysis_example(module: str) -> list:
        """Simulated import analysis"""
        time.sleep(0.01)  # Simulate import resolution
        return [f"import_{i}" for i in range(5)]
    
    # Test optimized functions
    print("Testing optimized functions...")
    
    file_result = file_operation_example("example.py")
    print(f"File operation: {file_result}")
    
    parse_result = parsing_operation_example("def hello(): pass")
    print(f"Parsing result: {parse_result}")
    
    type_result = type_resolution_example("my_variable")
    print(f"Type resolution: {type_result}")
    
    import_result = import_analysis_example("my_module")
    print(f"Import analysis: {import_result}")
    print()


def demo_comprehensive_report():
    """Generate comprehensive performance report"""
    print("📈 Comprehensive Performance Report")
    print("=" * 50)
    
    # Get performance integration
    integration = get_performance_integration()
    
    # Generate optimization report
    report = integration.get_optimization_report()
    
    print("Optimization Report Summary:")
    print(f"  Optimized function categories: {len(report['optimized_functions'])}")
    
    for category, functions in report['optimized_functions'].items():
        print(f"    {category}: {len(functions)} functions")
    
    print(f"  Cache statistics available: {len(report['cache_stats'])}")
    print(f"  Memory optimization active: {report['memory_stats']['system_memory'].memory_percent:.1f}% used")
    print(f"  Performance monitoring: {report['performance_summary']['collection_config']['enabled']}")
    print()


async def demo_async_optimization():
    """Demonstrate async optimization"""
    print("🔄 Async Optimization Demo")
    print("=" * 50)
    
    # Get optimization engine
    engine = OptimizationEngine()
    
    # Example async function
    @engine.optimize(OptimizationStrategy.LATENCY_OPTIMIZED)
    async def async_task(delay: float, data: int) -> int:
        """Async task with optimization"""
        await asyncio.sleep(delay)
        return data ** 2
    
    # Run async tasks
    print("Running async optimized tasks...")
    start_time = time.time()
    
    tasks = [async_task(0.1, i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    print(f"Results: {results}")
    print(f"Total time: {end_time - start_time:.4f} seconds")
    print()


def main():
    """Run all performance optimization demos"""
    print("🎯 Graph-Sitter Performance Optimization Demo")
    print("=" * 60)
    print()
    
    # Run all demos
    demo_basic_optimization()
    demo_advanced_caching()
    demo_memory_optimization()
    demo_performance_monitoring()
    demo_scalability()
    demo_profiling()
    demo_integration_decorators()
    demo_comprehensive_report()
    
    # Run async demo
    print("Running async optimization demo...")
    asyncio.run(demo_async_optimization())
    
    print("✅ All performance optimization demos completed!")
    print()
    print("🚀 Performance optimization system is now active and monitoring your application.")
    print("📊 Check the logs and metrics for detailed performance insights.")


if __name__ == "__main__":
    main()

