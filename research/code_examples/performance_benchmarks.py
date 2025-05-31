#!/usr/bin/env python3
"""
Graph-Sitter Performance Benchmarking
=====================================

This module provides comprehensive performance benchmarks for Graph-Sitter
operations across different codebase sizes and complexity levels.
"""

import time
import psutil
import os
from pathlib import Path
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
from contextlib import contextmanager
import json

from graph_sitter import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    operation: str
    duration: float
    memory_usage: float
    items_processed: int
    throughput: float
    metadata: Dict[str, Any]


class PerformanceProfiler:
    """Context manager for profiling performance metrics."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.start_memory = None
        self.process = psutil.Process(os.getpid())
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.perf_counter() - self.start_time
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.memory_usage = self.end_memory - self.start_memory


def benchmark_codebase_initialization(codebase_path: str) -> BenchmarkResult:
    """
    Benchmark codebase initialization performance.
    
    Args:
        codebase_path: Path to the codebase to analyze
        
    Returns:
        BenchmarkResult with initialization metrics
    """
    with PerformanceProfiler("codebase_initialization") as profiler:
        codebase = Codebase(codebase_path)
        file_count = len(codebase.files)
    
    return BenchmarkResult(
        operation="codebase_initialization",
        duration=profiler.duration,
        memory_usage=profiler.memory_usage,
        items_processed=file_count,
        throughput=file_count / profiler.duration if profiler.duration > 0 else 0,
        metadata={
            "codebase_path": codebase_path,
            "total_files": file_count
        }
    )


def benchmark_function_analysis(codebase: Codebase) -> BenchmarkResult:
    """
    Benchmark function analysis and dependency resolution.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        BenchmarkResult with function analysis metrics
    """
    with PerformanceProfiler("function_analysis") as profiler:
        functions = codebase.functions
        function_count = len(functions)
        
        # Analyze dependencies for all functions
        total_dependencies = 0
        for function in functions:
            total_dependencies += len(function.dependencies)
    
    return BenchmarkResult(
        operation="function_analysis",
        duration=profiler.duration,
        memory_usage=profiler.memory_usage,
        items_processed=function_count,
        throughput=function_count / profiler.duration if profiler.duration > 0 else 0,
        metadata={
            "total_functions": function_count,
            "total_dependencies": total_dependencies,
            "avg_dependencies_per_function": total_dependencies / function_count if function_count > 0 else 0
        }
    )


def benchmark_symbol_resolution(codebase: Codebase) -> BenchmarkResult:
    """
    Benchmark symbol resolution and usage tracking.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        BenchmarkResult with symbol resolution metrics
    """
    with PerformanceProfiler("symbol_resolution") as profiler:
        symbols = []
        total_usages = 0
        
        # Collect all symbols and their usages
        for function in codebase.functions:
            symbols.append(function)
            total_usages += len(function.usages)
        
        for class_def in codebase.classes:
            symbols.append(class_def)
            total_usages += len(class_def.usages)
    
    symbol_count = len(symbols)
    
    return BenchmarkResult(
        operation="symbol_resolution",
        duration=profiler.duration,
        memory_usage=profiler.memory_usage,
        items_processed=symbol_count,
        throughput=symbol_count / profiler.duration if profiler.duration > 0 else 0,
        metadata={
            "total_symbols": symbol_count,
            "total_usages": total_usages,
            "avg_usages_per_symbol": total_usages / symbol_count if symbol_count > 0 else 0
        }
    )


def benchmark_import_resolution(codebase: Codebase) -> BenchmarkResult:
    """
    Benchmark import resolution and cross-file dependencies.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        BenchmarkResult with import resolution metrics
    """
    with PerformanceProfiler("import_resolution") as profiler:
        total_imports = 0
        total_import_symbols = 0
        
        for file in codebase.source_files:
            file_imports = file.imports
            total_imports += len(file_imports)
            
            for import_stmt in file_imports:
                total_import_symbols += len(import_stmt.symbols)
    
    return BenchmarkResult(
        operation="import_resolution",
        duration=profiler.duration,
        memory_usage=profiler.memory_usage,
        items_processed=total_imports,
        throughput=total_imports / profiler.duration if profiler.duration > 0 else 0,
        metadata={
            "total_imports": total_imports,
            "total_import_symbols": total_import_symbols,
            "avg_symbols_per_import": total_import_symbols / total_imports if total_imports > 0 else 0
        }
    )


def benchmark_file_parsing(codebase: Codebase) -> BenchmarkResult:
    """
    Benchmark individual file parsing performance.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        BenchmarkResult with file parsing metrics
    """
    with PerformanceProfiler("file_parsing") as profiler:
        total_lines = 0
        file_count = 0
        
        for file in codebase.source_files:
            file_count += 1
            total_lines += len(file.source.splitlines())
            
            # Force parsing by accessing parsed content
            _ = file.functions
            _ = file.classes
            _ = file.imports
    
    return BenchmarkResult(
        operation="file_parsing",
        duration=profiler.duration,
        memory_usage=profiler.memory_usage,
        items_processed=file_count,
        throughput=file_count / profiler.duration if profiler.duration > 0 else 0,
        metadata={
            "total_files": file_count,
            "total_lines": total_lines,
            "avg_lines_per_file": total_lines / file_count if file_count > 0 else 0,
            "lines_per_second": total_lines / profiler.duration if profiler.duration > 0 else 0
        }
    )


def benchmark_dependency_graph_construction(codebase: Codebase) -> BenchmarkResult:
    """
    Benchmark dependency graph construction performance.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        BenchmarkResult with graph construction metrics
    """
    with PerformanceProfiler("dependency_graph") as profiler:
        # Build comprehensive dependency graph
        nodes = []
        edges = []
        
        # Add all functions as nodes
        for function in codebase.functions:
            nodes.append(function.name)
            
            # Add dependency edges
            for dependency in function.dependencies:
                edges.append((function.name, dependency.name))
        
        # Add all classes as nodes
        for class_def in codebase.classes:
            nodes.append(class_def.name)
            
            # Add inheritance edges
            if hasattr(class_def, 'parent_classes') and class_def.parent_classes:
                for parent in class_def.parent_classes:
                    edges.append((class_def.name, parent.name))
    
    node_count = len(nodes)
    edge_count = len(edges)
    
    return BenchmarkResult(
        operation="dependency_graph_construction",
        duration=profiler.duration,
        memory_usage=profiler.memory_usage,
        items_processed=node_count + edge_count,
        throughput=(node_count + edge_count) / profiler.duration if profiler.duration > 0 else 0,
        metadata={
            "total_nodes": node_count,
            "total_edges": edge_count,
            "graph_density": edge_count / (node_count * (node_count - 1)) if node_count > 1 else 0
        }
    )


def run_comprehensive_benchmark(codebase_path: str) -> Dict[str, BenchmarkResult]:
    """
    Run comprehensive performance benchmarks on a codebase.
    
    Args:
        codebase_path: Path to the codebase to benchmark
        
    Returns:
        Dictionary of benchmark results
    """
    print(f"🚀 Starting comprehensive benchmark for: {codebase_path}")
    results = {}
    
    # 1. Codebase initialization
    print("  📊 Benchmarking codebase initialization...")
    results["initialization"] = benchmark_codebase_initialization(codebase_path)
    
    # Initialize codebase for subsequent tests
    codebase = Codebase(codebase_path)
    
    # 2. File parsing
    print("  📄 Benchmarking file parsing...")
    results["file_parsing"] = benchmark_file_parsing(codebase)
    
    # 3. Function analysis
    print("  🔧 Benchmarking function analysis...")
    results["function_analysis"] = benchmark_function_analysis(codebase)
    
    # 4. Symbol resolution
    print("  🔍 Benchmarking symbol resolution...")
    results["symbol_resolution"] = benchmark_symbol_resolution(codebase)
    
    # 5. Import resolution
    print("  📦 Benchmarking import resolution...")
    results["import_resolution"] = benchmark_import_resolution(codebase)
    
    # 6. Dependency graph construction
    print("  🕸️  Benchmarking dependency graph construction...")
    results["dependency_graph"] = benchmark_dependency_graph_construction(codebase)
    
    print("  ✅ Benchmark complete!")
    return results


def analyze_performance_characteristics(results: Dict[str, BenchmarkResult]) -> Dict[str, Any]:
    """
    Analyze performance characteristics from benchmark results.
    
    Args:
        results: Dictionary of benchmark results
        
    Returns:
        Performance analysis summary
    """
    analysis = {
        "total_duration": sum(result.duration for result in results.values()),
        "total_memory_usage": sum(result.memory_usage for result in results.values()),
        "operation_breakdown": {},
        "performance_insights": [],
        "bottlenecks": []
    }
    
    # Analyze each operation
    for operation, result in results.items():
        analysis["operation_breakdown"][operation] = {
            "duration": result.duration,
            "memory_usage": result.memory_usage,
            "throughput": result.throughput,
            "items_processed": result.items_processed,
            "percentage_of_total_time": (result.duration / analysis["total_duration"]) * 100
        }
    
    # Identify bottlenecks (operations taking >20% of total time)
    for operation, breakdown in analysis["operation_breakdown"].items():
        if breakdown["percentage_of_total_time"] > 20:
            analysis["bottlenecks"].append({
                "operation": operation,
                "percentage": breakdown["percentage_of_total_time"],
                "duration": breakdown["duration"]
            })
    
    # Generate performance insights
    fastest_operation = min(results.items(), key=lambda x: x[1].duration)
    slowest_operation = max(results.items(), key=lambda x: x[1].duration)
    highest_throughput = max(results.items(), key=lambda x: x[1].throughput)
    
    analysis["performance_insights"] = [
        f"Fastest operation: {fastest_operation[0]} ({fastest_operation[1].duration:.3f}s)",
        f"Slowest operation: {slowest_operation[0]} ({slowest_operation[1].duration:.3f}s)",
        f"Highest throughput: {highest_throughput[0]} ({highest_throughput[1].throughput:.1f} items/sec)",
        f"Total analysis time: {analysis['total_duration']:.3f}s",
        f"Total memory usage: {analysis['total_memory_usage']:.1f}MB"
    ]
    
    return analysis


def generate_performance_report(codebase_path: str, results: Dict[str, BenchmarkResult], 
                              analysis: Dict[str, Any]) -> str:
    """
    Generate a comprehensive performance report.
    
    Args:
        codebase_path: Path to the analyzed codebase
        results: Benchmark results
        analysis: Performance analysis
        
    Returns:
        Formatted performance report
    """
    report = f"""
# Graph-Sitter Performance Benchmark Report

## Codebase: {codebase_path}
**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Total Analysis Time**: {analysis['total_duration']:.3f} seconds
- **Total Memory Usage**: {analysis['total_memory_usage']:.1f} MB
- **Operations Benchmarked**: {len(results)}

## Performance Insights
"""
    
    for insight in analysis["performance_insights"]:
        report += f"- {insight}\n"
    
    report += "\n## Detailed Results\n\n"
    
    for operation, result in results.items():
        report += f"### {operation.replace('_', ' ').title()}\n"
        report += f"- **Duration**: {result.duration:.3f}s\n"
        report += f"- **Memory Usage**: {result.memory_usage:.1f}MB\n"
        report += f"- **Items Processed**: {result.items_processed:,}\n"
        report += f"- **Throughput**: {result.throughput:.1f} items/sec\n"
        
        if result.metadata:
            report += "- **Metadata**:\n"
            for key, value in result.metadata.items():
                report += f"  - {key}: {value}\n"
        report += "\n"
    
    if analysis["bottlenecks"]:
        report += "## Performance Bottlenecks\n\n"
        for bottleneck in analysis["bottlenecks"]:
            report += f"- **{bottleneck['operation']}**: {bottleneck['percentage']:.1f}% of total time ({bottleneck['duration']:.3f}s)\n"
        report += "\n"
    
    report += """## Recommendations

### Optimization Opportunities
1. **Caching**: Implement aggressive caching for expensive operations
2. **Lazy Loading**: Use lazy loading for large codebases
3. **Parallel Processing**: Consider parallel processing for independent operations
4. **Memory Management**: Monitor memory usage for large codebases

### Scaling Considerations
- For codebases >10,000 files: Consider chunked processing
- For memory-constrained environments: Implement streaming analysis
- For real-time analysis: Use incremental parsing capabilities

"""
    
    return report


def main():
    """
    Run performance benchmarks on the current codebase.
    """
    print("🔥 Graph-Sitter Performance Benchmark Suite")
    print("=" * 60)
    
    # Benchmark current codebase
    codebase_path = "."
    results = run_comprehensive_benchmark(codebase_path)
    
    # Analyze results
    analysis = analyze_performance_characteristics(results)
    
    # Generate and display report
    report = generate_performance_report(codebase_path, results, analysis)
    print(report)
    
    # Save results to file
    output_file = "research/performance_benchmark_results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Convert results to JSON-serializable format
    json_results = {}
    for operation, result in results.items():
        json_results[operation] = {
            "operation": result.operation,
            "duration": result.duration,
            "memory_usage": result.memory_usage,
            "items_processed": result.items_processed,
            "throughput": result.throughput,
            "metadata": result.metadata
        }
    
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "codebase_path": codebase_path,
            "results": json_results,
            "analysis": analysis
        }, f, indent=2)
    
    print(f"\n📊 Results saved to: {output_file}")
    
    # Save report to markdown file
    report_file = "research/performance_benchmark_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"📄 Report saved to: {report_file}")


if __name__ == "__main__":
    main()

