"""
Performance Benchmarking Framework

Provides comprehensive performance testing and benchmarking capabilities
for all system components with detailed metrics collection and analysis.
"""

import asyncio
import gc
import psutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from statistics import mean, median, stdev

import pytest
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID

from graph_sitter.shared.logging.logger import get_logger

logger = get_logger(__name__)
console = Console()


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    peak_memory_mb: float
    gc_collections: int
    io_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary format."""
        return {
            "execution_time_ms": self.execution_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "peak_memory_mb": self.peak_memory_mb,
            "gc_collections": self.gc_collections,
            "io_operations": self.io_operations,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    test_name: str
    component: str
    iterations: int
    metrics: List[PerformanceMetrics]
    baseline_metrics: Optional[PerformanceMetrics] = None
    
    @property
    def average_metrics(self) -> PerformanceMetrics:
        """Calculate average metrics across all iterations."""
        if not self.metrics:
            return PerformanceMetrics(0, 0, 0, 0, 0)
        
        return PerformanceMetrics(
            execution_time_ms=mean(m.execution_time_ms for m in self.metrics),
            memory_usage_mb=mean(m.memory_usage_mb for m in self.metrics),
            cpu_usage_percent=mean(m.cpu_usage_percent for m in self.metrics),
            peak_memory_mb=max(m.peak_memory_mb for m in self.metrics),
            gc_collections=sum(m.gc_collections for m in self.metrics),
            io_operations=sum(m.io_operations for m in self.metrics),
            cache_hits=sum(m.cache_hits for m in self.metrics),
            cache_misses=sum(m.cache_misses for m in self.metrics),
        )
    
    @property
    def performance_regression(self) -> Optional[Dict[str, float]]:
        """Calculate performance regression compared to baseline."""
        if not self.baseline_metrics:
            return None
        
        current = self.average_metrics
        baseline = self.baseline_metrics
        
        return {
            "execution_time_regression_percent": (
                (current.execution_time_ms - baseline.execution_time_ms) / baseline.execution_time_ms * 100
            ),
            "memory_regression_percent": (
                (current.memory_usage_mb - baseline.memory_usage_mb) / baseline.memory_usage_mb * 100
            ),
            "cpu_regression_percent": (
                (current.cpu_usage_percent - baseline.cpu_usage_percent) / baseline.cpu_usage_percent * 100
            ),
        }


class PerformanceMonitor:
    """Monitor system performance during test execution."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time: Optional[float] = None
        self.start_memory: Optional[float] = None
        self.start_gc_count: Optional[int] = None
        self.peak_memory: float = 0
        self.cpu_samples: List[float] = []
        
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_gc_count = sum(gc.get_count())
        self.peak_memory = self.start_memory
        self.cpu_samples = []
        
        # Force garbage collection before starting
        gc.collect()
    
    def sample_performance(self):
        """Take a performance sample."""
        if self.start_time is None:
            return
        
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = max(self.peak_memory, current_memory)
        
        cpu_percent = self.process.cpu_percent()
        self.cpu_samples.append(cpu_percent)
    
    def stop_monitoring(self) -> PerformanceMetrics:
        """Stop monitoring and return collected metrics."""
        if self.start_time is None:
            raise ValueError("Monitoring was not started")
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        end_gc_count = sum(gc.get_count())
        
        execution_time_ms = (end_time - self.start_time) * 1000
        memory_usage_mb = end_memory - self.start_memory
        cpu_usage_percent = mean(self.cpu_samples) if self.cpu_samples else 0
        gc_collections = end_gc_count - self.start_gc_count
        
        return PerformanceMetrics(
            execution_time_ms=execution_time_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            peak_memory_mb=self.peak_memory,
            gc_collections=gc_collections
        )


class PerformanceBenchmark:
    """
    Comprehensive performance benchmarking framework.
    
    Provides tools for measuring and analyzing performance across
    all system components with regression detection and reporting.
    """
    
    def __init__(self, baseline_file: Optional[Path] = None):
        self.baseline_file = baseline_file
        self.baselines: Dict[str, PerformanceMetrics] = {}
        self.results: List[BenchmarkResult] = []
        self.load_baselines()
    
    def load_baselines(self):
        """Load baseline performance metrics from file."""
        if self.baseline_file and self.baseline_file.exists():
            try:
                import json
                with open(self.baseline_file, 'r') as f:
                    data = json.load(f)
                    for test_name, metrics_dict in data.items():
                        self.baselines[test_name] = PerformanceMetrics(**metrics_dict)
                logger.info(f"Loaded {len(self.baselines)} baseline metrics")
            except Exception as e:
                logger.warning(f"Failed to load baselines: {e}")
    
    def save_baselines(self):
        """Save current results as new baselines."""
        if not self.baseline_file:
            return
        
        try:
            import json
            baseline_data = {}
            for result in self.results:
                baseline_data[f"{result.component}.{result.test_name}"] = result.average_metrics.to_dict()
            
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.baseline_file, 'w') as f:
                json.dump(baseline_data, f, indent=2)
            
            logger.info(f"Saved {len(baseline_data)} baseline metrics")
        except Exception as e:
            logger.error(f"Failed to save baselines: {e}")
    
    async def benchmark_function(
        self,
        func: Callable,
        test_name: str,
        component: str,
        iterations: int = 10,
        warmup_iterations: int = 2,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """
        Benchmark a function with comprehensive performance monitoring.
        
        Args:
            func: Function to benchmark
            test_name: Name of the test
            component: Component being tested
            iterations: Number of benchmark iterations
            warmup_iterations: Number of warmup iterations
            *args, **kwargs: Arguments to pass to the function
        """
        console.print(f"🏃 Benchmarking {component}.{test_name} ({iterations} iterations)")
        
        # Warmup iterations
        for _ in range(warmup_iterations):
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
        
        # Benchmark iterations
        metrics_list = []
        
        with Progress() as progress:
            task = progress.add_task(f"Benchmarking {test_name}", total=iterations)
            
            for i in range(iterations):
                monitor = PerformanceMonitor()
                monitor.start_monitoring()
                
                try:
                    # Sample performance during execution
                    if asyncio.iscoroutinefunction(func):
                        # For async functions, sample periodically
                        async def monitored_execution():
                            task = asyncio.create_task(func(*args, **kwargs))
                            while not task.done():
                                monitor.sample_performance()
                                await asyncio.sleep(0.01)  # Sample every 10ms
                            return await task
                        
                        await monitored_execution()
                    else:
                        # For sync functions, sample before and after
                        monitor.sample_performance()
                        result = func(*args, **kwargs)
                        monitor.sample_performance()
                    
                    metrics = monitor.stop_monitoring()
                    metrics_list.append(metrics)
                    
                except Exception as e:
                    logger.error(f"Benchmark iteration {i+1} failed: {e}")
                    # Create error metrics
                    metrics = PerformanceMetrics(0, 0, 0, 0, 0)
                    metrics_list.append(metrics)
                
                progress.update(task, advance=1)
        
        # Get baseline metrics if available
        baseline_key = f"{component}.{test_name}"
        baseline_metrics = self.baselines.get(baseline_key)
        
        result = BenchmarkResult(
            test_name=test_name,
            component=component,
            iterations=iterations,
            metrics=metrics_list,
            baseline_metrics=baseline_metrics
        )
        
        self.results.append(result)
        self._display_benchmark_result(result)
        
        return result
    
    def _display_benchmark_result(self, result: BenchmarkResult):
        """Display benchmark results in a formatted table."""
        avg_metrics = result.average_metrics
        
        table = Table(title=f"Benchmark: {result.component}.{result.test_name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Average", style="green")
        table.add_column("Min", style="yellow")
        table.add_column("Max", style="red")
        table.add_column("Std Dev", style="magenta")
        table.add_column("Regression", style="red")
        
        # Execution time
        exec_times = [m.execution_time_ms for m in result.metrics]
        regression_text = ""
        if result.baseline_metrics:
            regression = result.performance_regression
            if regression:
                exec_regression = regression["execution_time_regression_percent"]
                regression_text = f"{exec_regression:+.1f}%"
        
        table.add_row(
            "Execution Time (ms)",
            f"{avg_metrics.execution_time_ms:.2f}",
            f"{min(exec_times):.2f}",
            f"{max(exec_times):.2f}",
            f"{stdev(exec_times) if len(exec_times) > 1 else 0:.2f}",
            regression_text
        )
        
        # Memory usage
        memory_usage = [m.memory_usage_mb for m in result.metrics]
        regression_text = ""
        if result.baseline_metrics and result.performance_regression:
            mem_regression = result.performance_regression["memory_regression_percent"]
            regression_text = f"{mem_regression:+.1f}%"
        
        table.add_row(
            "Memory Usage (MB)",
            f"{avg_metrics.memory_usage_mb:.2f}",
            f"{min(memory_usage):.2f}",
            f"{max(memory_usage):.2f}",
            f"{stdev(memory_usage) if len(memory_usage) > 1 else 0:.2f}",
            regression_text
        )
        
        # CPU usage
        cpu_usage = [m.cpu_usage_percent for m in result.metrics]
        table.add_row(
            "CPU Usage (%)",
            f"{avg_metrics.cpu_usage_percent:.1f}",
            f"{min(cpu_usage):.1f}",
            f"{max(cpu_usage):.1f}",
            f"{stdev(cpu_usage) if len(cpu_usage) > 1 else 0:.1f}",
            ""
        )
        
        # Peak memory
        table.add_row(
            "Peak Memory (MB)",
            f"{avg_metrics.peak_memory_mb:.2f}",
            "",
            "",
            "",
            ""
        )
        
        console.print(table)
        
        # Performance warnings
        if result.performance_regression:
            regression = result.performance_regression
            if regression["execution_time_regression_percent"] > 10:
                console.print("⚠️  [red]Significant execution time regression detected![/red]")
            if regression["memory_regression_percent"] > 20:
                console.print("⚠️  [red]Significant memory usage regression detected![/red]")
    
    async def benchmark_graph_sitter_parsing(self, codebase_path: Path) -> BenchmarkResult:
        """Benchmark Graph-Sitter parsing performance."""
        from graph_sitter.core.codebase import Codebase
        
        async def parse_codebase():
            codebase = Codebase.from_path(codebase_path)
            # Force parsing of all files
            for file in codebase.files:
                _ = file.ast
            return codebase
        
        return await self.benchmark_function(
            parse_codebase,
            "codebase_parsing",
            "graph_sitter",
            iterations=5,
            warmup_iterations=1
        )
    
    async def benchmark_symbol_resolution(self, codebase_path: Path) -> BenchmarkResult:
        """Benchmark symbol resolution performance."""
        from graph_sitter.core.codebase import Codebase
        
        async def resolve_symbols():
            codebase = Codebase.from_path(codebase_path)
            symbol_count = 0
            for file in codebase.files:
                for symbol in file.symbols:
                    symbol_count += 1
                    # Force resolution
                    _ = symbol.resolved_symbol
            return symbol_count
        
        return await self.benchmark_function(
            resolve_symbols,
            "symbol_resolution",
            "graph_sitter",
            iterations=3,
            warmup_iterations=1
        )
    
    async def benchmark_codegen_agent_creation(self) -> BenchmarkResult:
        """Benchmark Codegen agent creation performance."""
        try:
            from codegen import Agent
            
            def create_agent():
                # Mock agent creation for testing
                return Agent(org_id="test", token="test")
            
            return await self.benchmark_function(
                create_agent,
                "agent_creation",
                "codegen_sdk",
                iterations=10,
                warmup_iterations=2
            )
        except ImportError:
            logger.warning("Codegen SDK not available for benchmarking")
            # Return mock result
            return BenchmarkResult(
                test_name="agent_creation",
                component="codegen_sdk",
                iterations=0,
                metrics=[]
            )
    
    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report."""
        if not self.results:
            return "No benchmark results available."
        
        report_lines = [
            "# Performance Benchmark Report",
            f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total benchmarks: {len(self.results)}",
            "",
            "## Summary",
        ]
        
        # Overall statistics
        total_tests = len(self.results)
        regression_count = 0
        
        for result in self.results:
            if result.performance_regression:
                regression = result.performance_regression
                if (regression["execution_time_regression_percent"] > 5 or
                    regression["memory_regression_percent"] > 10):
                    regression_count += 1
        
        report_lines.extend([
            f"- Tests with performance regressions: {regression_count}/{total_tests}",
            f"- Average execution time: {mean(r.average_metrics.execution_time_ms for r in self.results):.2f}ms",
            f"- Average memory usage: {mean(r.average_metrics.memory_usage_mb for r in self.results):.2f}MB",
            "",
            "## Detailed Results",
        ])
        
        # Detailed results for each benchmark
        for result in self.results:
            avg_metrics = result.average_metrics
            report_lines.extend([
                f"### {result.component}.{result.test_name}",
                f"- Iterations: {result.iterations}",
                f"- Execution time: {avg_metrics.execution_time_ms:.2f}ms",
                f"- Memory usage: {avg_metrics.memory_usage_mb:.2f}MB",
                f"- Peak memory: {avg_metrics.peak_memory_mb:.2f}MB",
                f"- CPU usage: {avg_metrics.cpu_usage_percent:.1f}%",
            ])
            
            if result.performance_regression:
                regression = result.performance_regression
                report_lines.extend([
                    "- **Performance Regression:**",
                    f"  - Execution time: {regression['execution_time_regression_percent']:+.1f}%",
                    f"  - Memory usage: {regression['memory_regression_percent']:+.1f}%",
                    f"  - CPU usage: {regression['cpu_regression_percent']:+.1f}%",
                ])
            
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        if not self.results:
            return {}
        
        return {
            "total_benchmarks": len(self.results),
            "average_execution_time_ms": mean(r.average_metrics.execution_time_ms for r in self.results),
            "average_memory_usage_mb": mean(r.average_metrics.memory_usage_mb for r in self.results),
            "peak_memory_usage_mb": max(r.average_metrics.peak_memory_mb for r in self.results),
            "total_gc_collections": sum(r.average_metrics.gc_collections for r in self.results),
            "regressions_detected": sum(
                1 for r in self.results 
                if r.performance_regression and (
                    r.performance_regression["execution_time_regression_percent"] > 5 or
                    r.performance_regression["memory_regression_percent"] > 10
                )
            )
        }

