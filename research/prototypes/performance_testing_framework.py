#!/usr/bin/env python3
"""
Performance Testing Framework for Graph-Sitter
Benchmarks Graph-Sitter performance across different codebase sizes and operations.
"""

import time
import psutil
import statistics
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import concurrent.futures
import threading

try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.core.enums import UsageType
except ImportError:
    print("Graph-Sitter not available. Using mock implementation for testing.")
    # Mock implementation for testing
    class Codebase:
        def __init__(self, path, config=None):
            self.path = path
            self.config = config
            # Simulate some processing time
            time.sleep(0.1)
            
        def get_symbol(self, name):
            time.sleep(0.001)  # Simulate lookup time
            return MockSymbol(name)
            
        @property
        def functions(self):
            return [MockSymbol(f"function_{i}") for i in range(100)]
            
        @property
        def classes(self):
            return [MockSymbol(f"class_{i}") for i in range(20)]
    
    class MockSymbol:
        def __init__(self, name):
            self.name = name
            self.dependencies = []
            self.usages = []
            
    class CodebaseConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    operation_name: str
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    iterations: int
    min_time_ms: float
    max_time_ms: float
    median_time_ms: float
    std_dev_ms: float
    operations_per_second: float
    memory_peak_mb: float
    memory_average_mb: float


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    test_name: str
    codebase_size: str
    configuration: Dict[str, Any]
    metrics: List[PerformanceMetrics]
    total_duration_seconds: float
    timestamp: str
    system_info: Dict[str, Any]


class PerformanceMonitor:
    """Monitor system performance during operations."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.measurements = []
        self.monitor_thread = None
    
    def start_monitoring(self, interval: float = 0.1):
        """Start monitoring system resources."""
        self.monitoring = True
        self.measurements = []
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,)
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and return measurements."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        return self.measurements
    
    def _monitor_loop(self, interval: float):
        """Monitor loop running in separate thread."""
        while self.monitoring:
            try:
                memory_info = self.process.memory_info()
                cpu_percent = self.process.cpu_percent()
                
                self.measurements.append({
                    'timestamp': time.time(),
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'cpu_percent': cpu_percent
                })
                
                time.sleep(interval)
            except Exception:
                break


class PerformanceTester:
    """Performance testing framework for Graph-Sitter operations."""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.results = []
    
    @contextmanager
    def measure_performance(self, operation_name: str, iterations: int = 1):
        """Context manager for measuring operation performance."""
        execution_times = []
        
        # Start monitoring
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            for i in range(iterations):
                iter_start = time.time()
                yield i
                iter_end = time.time()
                execution_times.append((iter_end - iter_start) * 1000)  # Convert to ms
        finally:
            end_time = time.time()
            measurements = self.monitor.stop_monitoring()
        
        # Calculate metrics
        total_time_ms = (end_time - start_time) * 1000
        
        if measurements:
            memory_values = [m['memory_mb'] for m in measurements]
            cpu_values = [m['cpu_percent'] for m in measurements if m['cpu_percent'] > 0]
            
            memory_peak = max(memory_values) if memory_values else 0
            memory_average = statistics.mean(memory_values) if memory_values else 0
            cpu_average = statistics.mean(cpu_values) if cpu_values else 0
        else:
            memory_peak = memory_average = cpu_average = 0
        
        # Create metrics object
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            execution_time_ms=total_time_ms,
            memory_usage_mb=memory_average,
            cpu_usage_percent=cpu_average,
            iterations=iterations,
            min_time_ms=min(execution_times) if execution_times else 0,
            max_time_ms=max(execution_times) if execution_times else 0,
            median_time_ms=statistics.median(execution_times) if execution_times else 0,
            std_dev_ms=statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            operations_per_second=iterations / (total_time_ms / 1000) if total_time_ms > 0 else 0,
            memory_peak_mb=memory_peak,
            memory_average_mb=memory_average
        )
        
        self.results.append(metrics)
    
    def benchmark_codebase_initialization(self, repo_path: str, configs: List[CodebaseConfig]) -> List[PerformanceMetrics]:
        """Benchmark codebase initialization with different configurations."""
        results = []
        
        for i, config in enumerate(configs):
            config_name = f"config_{i}"
            
            with self.measure_performance(f"codebase_init_{config_name}", iterations=3) as iteration:
                codebase = Codebase(repo_path, config=config)
                # Force some analysis to ensure initialization is complete
                if hasattr(codebase, 'functions'):
                    _ = len(codebase.functions)
        
        return self.results[-len(configs):]
    
    def benchmark_symbol_operations(self, codebase: Codebase, iterations: int = 1000) -> List[PerformanceMetrics]:
        """Benchmark symbol lookup and analysis operations."""
        results = []
        
        # Symbol lookup benchmark
        with self.measure_performance("symbol_lookup", iterations=iterations):
            for i in range(iterations):
                symbol = codebase.get_symbol(f"test_symbol_{i % 10}")
        
        # Dependencies analysis benchmark
        if hasattr(codebase, 'functions') and codebase.functions:
            functions_sample = codebase.functions[:min(100, len(codebase.functions))]
            
            with self.measure_performance("dependencies_analysis", iterations=len(functions_sample)):
                for function in functions_sample:
                    if hasattr(function, 'dependencies'):
                        deps = function.dependencies
        
        # Usages analysis benchmark
        if hasattr(codebase, 'functions') and codebase.functions:
            with self.measure_performance("usages_analysis", iterations=len(functions_sample)):
                for function in functions_sample:
                    if hasattr(function, 'usages'):
                        usages = function.usages
        
        return self.results[-3:]  # Return last 3 results
    
    def benchmark_pattern_matching(self, codebase: Codebase, patterns: List[str]) -> List[PerformanceMetrics]:
        """Benchmark pattern matching operations."""
        results = []
        
        for pattern in patterns:
            with self.measure_performance(f"pattern_match_{pattern}", iterations=10):
                if hasattr(codebase, 'find_patterns'):
                    matches = codebase.find_patterns(pattern, {})
                else:
                    # Mock pattern matching
                    time.sleep(0.05)  # Simulate pattern matching time
        
        return self.results[-len(patterns):]
    
    def benchmark_concurrent_operations(self, codebase: Codebase, max_workers: int = 4) -> PerformanceMetrics:
        """Benchmark concurrent operations."""
        
        def worker_task(worker_id: int) -> float:
            start_time = time.time()
            
            # Simulate concurrent symbol lookups
            for i in range(50):
                symbol = codebase.get_symbol(f"worker_{worker_id}_symbol_{i}")
            
            return time.time() - start_time
        
        with self.measure_performance("concurrent_operations", iterations=1):
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(worker_task, i) for i in range(max_workers)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        return self.results[-1]
    
    def benchmark_memory_usage(self, repo_paths: List[str]) -> List[PerformanceMetrics]:
        """Benchmark memory usage across different codebase sizes."""
        results = []
        
        for repo_path in repo_paths:
            repo_name = Path(repo_path).name
            
            with self.measure_performance(f"memory_usage_{repo_name}", iterations=1):
                codebase = Codebase(repo_path)
                
                # Force analysis to measure peak memory
                if hasattr(codebase, 'functions'):
                    functions = codebase.functions
                if hasattr(codebase, 'classes'):
                    classes = codebase.classes
                
                # Hold references to force memory usage
                time.sleep(1)
        
        return self.results[-len(repo_paths):]
    
    def run_comprehensive_benchmark(self, repo_path: str, output_path: Optional[str] = None) -> BenchmarkResult:
        """Run comprehensive performance benchmark."""
        print(f"Starting comprehensive benchmark for: {repo_path}")
        start_time = time.time()
        
        # Test configurations
        configs = [
            CodebaseConfig(parallel_processing=False, lazy_loading=False),
            CodebaseConfig(parallel_processing=True, lazy_loading=False),
            CodebaseConfig(parallel_processing=False, lazy_loading=True),
            CodebaseConfig(parallel_processing=True, lazy_loading=True),
        ]
        
        # Initialize codebase with best config for subsequent tests
        print("Initializing codebase...")
        codebase = Codebase(repo_path, config=configs[-1])
        
        all_metrics = []
        
        # Benchmark initialization
        print("Benchmarking initialization...")
        init_metrics = self.benchmark_codebase_initialization(repo_path, configs)
        all_metrics.extend(init_metrics)
        
        # Benchmark symbol operations
        print("Benchmarking symbol operations...")
        symbol_metrics = self.benchmark_symbol_operations(codebase)
        all_metrics.extend(symbol_metrics)
        
        # Benchmark pattern matching
        print("Benchmarking pattern matching...")
        patterns = ["function_call", "class_definition", "import_statement"]
        pattern_metrics = self.benchmark_pattern_matching(codebase, patterns)
        all_metrics.extend(pattern_metrics)
        
        # Benchmark concurrent operations
        print("Benchmarking concurrent operations...")
        concurrent_metrics = self.benchmark_concurrent_operations(codebase)
        all_metrics.append(concurrent_metrics)
        
        total_duration = time.time() - start_time
        
        # Create benchmark result
        result = BenchmarkResult(
            test_name="comprehensive_benchmark",
            codebase_size=self._estimate_codebase_size(repo_path),
            configuration=asdict(configs[-1]),
            metrics=all_metrics,
            total_duration_seconds=total_duration,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            system_info=self._get_system_info()
        )
        
        # Save results
        if output_path:
            self._save_results(result, output_path)
        
        # Print summary
        self._print_benchmark_summary(result)
        
        return result
    
    def _estimate_codebase_size(self, repo_path: str) -> str:
        """Estimate codebase size category."""
        try:
            # Count Python files as a rough estimate
            python_files = list(Path(repo_path).rglob("*.py"))
            file_count = len(python_files)
            
            if file_count < 10:
                return "small"
            elif file_count < 100:
                return "medium"
            elif file_count < 1000:
                return "large"
            else:
                return "very_large"
        except Exception:
            return "unknown"
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmark context."""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
            'platform': psutil.sys.platform
        }
    
    def _save_results(self, result: BenchmarkResult, output_path: str):
        """Save benchmark results to file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable format
        result_dict = asdict(result)
        
        with open(output_file, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        print(f"Benchmark results saved to: {output_file}")
    
    def _print_benchmark_summary(self, result: BenchmarkResult):
        """Print benchmark summary to console."""
        print("\n" + "="*80)
        print("GRAPH-SITTER PERFORMANCE BENCHMARK SUMMARY")
        print("="*80)
        print(f"Repository: {result.codebase_size} codebase")
        print(f"Total Duration: {result.total_duration_seconds:.2f}s")
        print(f"System: {result.system_info['cpu_count']} CPUs, "
              f"{result.system_info['memory_total_gb']:.1f}GB RAM")
        print()
        
        # Group metrics by category
        categories = {}
        for metric in result.metrics:
            category = metric.operation_name.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(metric)
        
        for category, metrics in categories.items():
            print(f"{category.upper()} OPERATIONS:")
            for metric in metrics:
                print(f"  {metric.operation_name}:")
                print(f"    Execution Time: {metric.execution_time_ms:.2f}ms")
                print(f"    Operations/sec: {metric.operations_per_second:.1f}")
                print(f"    Memory Usage: {metric.memory_average_mb:.2f}MB")
                print(f"    CPU Usage: {metric.cpu_usage_percent:.1f}%")
                if metric.iterations > 1:
                    print(f"    Median Time: {metric.median_time_ms:.2f}ms")
                    print(f"    Std Dev: {metric.std_dev_ms:.2f}ms")
                print()
        
        print("="*80)


def main():
    """Main function for running performance tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Graph-Sitter Performance Testing Framework')
    parser.add_argument('repo_path', help='Path to the repository to benchmark')
    parser.add_argument('--output', '-o', help='Output file for benchmark results')
    parser.add_argument('--quick', action='store_true', help='Run quick benchmark (fewer iterations)')
    
    args = parser.parse_args()
    
    # Create tester
    tester = PerformanceTester()
    
    # Run benchmark
    result = tester.run_comprehensive_benchmark(args.repo_path, args.output)
    
    return 0


if __name__ == '__main__':
    exit(main())

