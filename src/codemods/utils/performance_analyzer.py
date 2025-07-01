"""Performance analysis utilities for codemods.

This module provides tools to benchmark and analyze codemod performance,
identify bottlenecks, and suggest optimizations.
"""

import time
import psutil
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import File


@dataclass
class PerformanceMetrics:
    """Container for performance measurement data."""
    execution_time: float
    memory_usage_mb: float
    files_processed: int
    functions_analyzed: int
    peak_memory_mb: float
    cpu_percent: float
    throughput_files_per_sec: float
    throughput_functions_per_sec: float
    additional_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Results from a performance benchmark."""
    codemod_name: str
    metrics: PerformanceMetrics
    iterations: int
    avg_metrics: PerformanceMetrics
    std_dev_metrics: Dict[str, float]
    recommendations: List[str] = field(default_factory=list)


class PerformanceProfiler:
    """Profiler for measuring codemod performance."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.start_memory: Optional[float] = None
        self.peak_memory: float = 0
        self.process = psutil.Process()
    
    @contextmanager
    def profile(self):
        """Context manager for profiling code execution."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        
        try:
            yield self
        finally:
            pass
    
    def update_peak_memory(self):
        """Update peak memory usage."""
        current_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = max(self.peak_memory, current_memory)
    
    def get_metrics(self, files_processed: int, functions_analyzed: int) -> PerformanceMetrics:
        """Get current performance metrics."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024
        execution_time = end_time - self.start_time
        
        return PerformanceMetrics(
            execution_time=execution_time,
            memory_usage_mb=end_memory - self.start_memory,
            files_processed=files_processed,
            functions_analyzed=functions_analyzed,
            peak_memory_mb=self.peak_memory,
            cpu_percent=self.process.cpu_percent(),
            throughput_files_per_sec=files_processed / execution_time if execution_time > 0 else 0,
            throughput_functions_per_sec=functions_analyzed / execution_time if execution_time > 0 else 0
        )


class CodemodBenchmark:
    """Benchmark utility for comparing codemod performance."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def benchmark_codemod(self, codemod, codebase: Codebase, iterations: int = 3) -> BenchmarkResult:
        """Benchmark a codemod's performance over multiple iterations."""
        metrics_list = []
        
        for i in range(iterations):
            # Create a fresh copy of codebase for each iteration
            # (In practice, you'd want to reset the codebase state)
            
            profiler = PerformanceProfiler()
            
            with profiler.profile():
                # Count files and functions before execution
                files_count = len(list(codebase.files))
                functions_count = sum(len(list(file.functions)) for file in codebase.files)
                
                # Execute codemod
                if hasattr(codemod, 'safe_execute'):
                    codemod.safe_execute(codebase, dry_run=True)  # Use dry run for benchmarking
                elif hasattr(codemod, 'execute'):
                    codemod.execute(codebase)
                
                # Update memory tracking
                profiler.update_peak_memory()
                
                # Get metrics
                metrics = profiler.get_metrics(files_count, functions_count)
                metrics_list.append(metrics)
        
        # Calculate average and standard deviation
        avg_metrics = self._calculate_average_metrics(metrics_list)
        std_dev_metrics = self._calculate_std_dev_metrics(metrics_list)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(avg_metrics)
        
        result = BenchmarkResult(
            codemod_name=getattr(codemod, 'name', codemod.__class__.__name__),
            metrics=metrics_list[0],  # First iteration metrics
            iterations=iterations,
            avg_metrics=avg_metrics,
            std_dev_metrics=std_dev_metrics,
            recommendations=recommendations
        )
        
        self.results.append(result)
        return result
    
    def _calculate_average_metrics(self, metrics_list: List[PerformanceMetrics]) -> PerformanceMetrics:
        """Calculate average metrics across iterations."""
        return PerformanceMetrics(
            execution_time=statistics.mean(m.execution_time for m in metrics_list),
            memory_usage_mb=statistics.mean(m.memory_usage_mb for m in metrics_list),
            files_processed=metrics_list[0].files_processed,  # Should be same across iterations
            functions_analyzed=metrics_list[0].functions_analyzed,
            peak_memory_mb=statistics.mean(m.peak_memory_mb for m in metrics_list),
            cpu_percent=statistics.mean(m.cpu_percent for m in metrics_list),
            throughput_files_per_sec=statistics.mean(m.throughput_files_per_sec for m in metrics_list),
            throughput_functions_per_sec=statistics.mean(m.throughput_functions_per_sec for m in metrics_list)
        )
    
    def _calculate_std_dev_metrics(self, metrics_list: List[PerformanceMetrics]) -> Dict[str, float]:
        """Calculate standard deviation for key metrics."""
        if len(metrics_list) < 2:
            return {}
        
        return {
            'execution_time': statistics.stdev(m.execution_time for m in metrics_list),
            'memory_usage_mb': statistics.stdev(m.memory_usage_mb for m in metrics_list),
            'throughput_files_per_sec': statistics.stdev(m.throughput_files_per_sec for m in metrics_list),
            'throughput_functions_per_sec': statistics.stdev(m.throughput_functions_per_sec for m in metrics_list)
        }
    
    def _generate_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Throughput recommendations
        if metrics.throughput_files_per_sec < 10:
            recommendations.append("Low file processing throughput - consider adding file filters")
        
        if metrics.throughput_functions_per_sec < 100:
            recommendations.append("Low function processing throughput - consider optimizing AST traversal")
        
        # Memory recommendations
        if metrics.memory_usage_mb > 500:
            recommendations.append("High memory usage - consider processing files in batches")
        
        if metrics.peak_memory_mb > 1000:
            recommendations.append("Very high peak memory - implement lazy loading or streaming")
        
        # CPU recommendations
        if metrics.cpu_percent > 80:
            recommendations.append("High CPU usage - consider parallel processing for I/O bound operations")
        
        # Time-based recommendations
        if metrics.execution_time > 60:
            recommendations.append("Long execution time - consider breaking into smaller transformations")
        
        return recommendations
    
    def compare_codemods(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Compare multiple codemod benchmark results."""
        if not results:
            return {}
        
        comparison = {
            'fastest': min(results, key=lambda r: r.avg_metrics.execution_time),
            'most_memory_efficient': min(results, key=lambda r: r.avg_metrics.memory_usage_mb),
            'highest_throughput': max(results, key=lambda r: r.avg_metrics.throughput_files_per_sec),
            'summary': {}
        }
        
        # Calculate relative performance
        fastest_time = comparison['fastest'].avg_metrics.execution_time
        for result in results:
            relative_speed = result.avg_metrics.execution_time / fastest_time
            comparison['summary'][result.codemod_name] = {
                'relative_speed': relative_speed,
                'speed_factor': f"{relative_speed:.2f}x slower" if relative_speed > 1 else "fastest",
                'memory_mb': result.avg_metrics.memory_usage_mb,
                'throughput': result.avg_metrics.throughput_files_per_sec
            }
        
        return comparison
    
    def generate_report(self) -> str:
        """Generate a comprehensive performance report."""
        if not self.results:
            return "No benchmark results available."
        
        report = ["# Codemod Performance Benchmark Report\n"]
        
        # Individual results
        for result in self.results:
            report.append(f"## {result.codemod_name}")
            report.append(f"- **Execution Time**: {result.avg_metrics.execution_time:.2f}s ± {result.std_dev_metrics.get('execution_time', 0):.2f}s")
            report.append(f"- **Memory Usage**: {result.avg_metrics.memory_usage_mb:.1f} MB")
            report.append(f"- **Peak Memory**: {result.avg_metrics.peak_memory_mb:.1f} MB")
            report.append(f"- **Throughput**: {result.avg_metrics.throughput_files_per_sec:.1f} files/sec")
            report.append(f"- **Files Processed**: {result.avg_metrics.files_processed}")
            report.append(f"- **Functions Analyzed**: {result.avg_metrics.functions_analyzed}")
            
            if result.recommendations:
                report.append("### Recommendations:")
                for rec in result.recommendations:
                    report.append(f"- {rec}")
            
            report.append("")
        
        # Comparison if multiple results
        if len(self.results) > 1:
            comparison = self.compare_codemods(self.results)
            report.append("## Performance Comparison")
            report.append(f"- **Fastest**: {comparison['fastest'].codemod_name}")
            report.append(f"- **Most Memory Efficient**: {comparison['most_memory_efficient'].codemod_name}")
            report.append(f"- **Highest Throughput**: {comparison['highest_throughput'].codemod_name}")
            
            report.append("\n### Relative Performance:")
            for name, stats in comparison['summary'].items():
                report.append(f"- **{name}**: {stats['speed_factor']}, {stats['memory_mb']:.1f} MB, {stats['throughput']:.1f} files/sec")
        
        return "\n".join(report)


class PerformanceOptimizer:
    """Utility for suggesting and applying performance optimizations."""
    
    @staticmethod
    def analyze_codebase_characteristics(codebase: Codebase) -> Dict[str, Any]:
        """Analyze codebase characteristics to suggest optimizations."""
        files = list(codebase.files)
        file_sizes = [len(file.content.splitlines()) for file in files]
        
        characteristics = {
            'total_files': len(files),
            'avg_file_size': statistics.mean(file_sizes) if file_sizes else 0,
            'max_file_size': max(file_sizes) if file_sizes else 0,
            'min_file_size': min(file_sizes) if file_sizes else 0,
            'large_files_count': sum(1 for size in file_sizes if size > 1000),
            'file_extensions': {},
            'total_functions': 0,
            'avg_functions_per_file': 0
        }
        
        # Analyze file extensions
        for file in files:
            ext = file.filepath.split('.')[-1] if '.' in file.filepath else 'no_extension'
            characteristics['file_extensions'][ext] = characteristics['file_extensions'].get(ext, 0) + 1
        
        # Analyze functions
        function_counts = []
        for file in files:
            func_count = len(list(file.functions))
            function_counts.append(func_count)
            characteristics['total_functions'] += func_count
        
        if function_counts:
            characteristics['avg_functions_per_file'] = statistics.mean(function_counts)
        
        return characteristics
    
    @staticmethod
    def suggest_optimizations(characteristics: Dict[str, Any]) -> List[str]:
        """Suggest optimizations based on codebase characteristics."""
        suggestions = []
        
        # File-based suggestions
        if characteristics['total_files'] > 1000:
            suggestions.append("Large codebase detected - implement file filtering to reduce scope")
        
        if characteristics['large_files_count'] > 10:
            suggestions.append("Many large files detected - consider batch processing or streaming")
        
        if characteristics['avg_file_size'] > 500:
            suggestions.append("Large average file size - implement lazy loading for AST nodes")
        
        # Function-based suggestions
        if characteristics['total_functions'] > 10000:
            suggestions.append("Many functions detected - enable parallel processing if thread-safe")
        
        if characteristics['avg_functions_per_file'] > 50:
            suggestions.append("High function density - optimize function iteration patterns")
        
        # Extension-based suggestions
        extensions = characteristics['file_extensions']
        if len(extensions) > 5:
            suggestions.append("Multiple file types - add extension-based filtering")
        
        return suggestions


# Example usage
if __name__ == "__main__":
    # Example of how to use the performance analyzer
    print("Performance analysis utilities created successfully!")
    print("\nExample usage:")
    print("1. Create a benchmark: benchmark = CodemodBenchmark()")
    print("2. Run benchmark: result = benchmark.benchmark_codemod(my_codemod, codebase)")
    print("3. Generate report: print(benchmark.generate_report())")
    print("4. Analyze codebase: characteristics = PerformanceOptimizer.analyze_codebase_characteristics(codebase)")
    print("5. Get suggestions: suggestions = PerformanceOptimizer.suggest_optimizations(characteristics)")

