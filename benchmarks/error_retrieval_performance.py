#!/usr/bin/env python3
"""
Performance Benchmarks for Unified Error Interface

This benchmark suite measures the performance characteristics of the
unified error interface to ensure it meets performance requirements
and identify potential bottlenecks.
"""

import time
import tempfile
import shutil
import statistics
from pathlib import Path
from typing import List, Dict, Any, Callable
import sys
import gc

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    print("❌ Graph-sitter not available")
    GRAPH_SITTER_AVAILABLE = False


class PerformanceBenchmark:
    """Performance benchmark runner."""
    
    def __init__(self):
        self.results = {}
        self.temp_dirs = []
    
    def create_test_project(self, size: str = "medium") -> Path:
        """Create a test project of specified size."""
        temp_dir = tempfile.mkdtemp(prefix=f"perf_test_{size}_")
        project_path = Path(temp_dir)
        self.temp_dirs.append(temp_dir)
        
        # Create project structure
        (project_path / "src").mkdir(parents=True, exist_ok=True)
        (project_path / "tests").mkdir(parents=True, exist_ok=True)
        (project_path / "lib").mkdir(parents=True, exist_ok=True)
        
        # Determine project size parameters
        size_params = {
            "small": {"files": 5, "lines_per_file": 50, "errors_per_file": 2},
            "medium": {"files": 20, "lines_per_file": 100, "errors_per_file": 5},
            "large": {"files": 50, "lines_per_file": 200, "errors_per_file": 10},
            "xlarge": {"files": 100, "lines_per_file": 300, "errors_per_file": 15}
        }
        
        params = size_params.get(size, size_params["medium"])
        
        print(f"📁 Creating {size} test project:")
        print(f"   Files: {params['files']}")
        print(f"   Lines per file: {params['lines_per_file']}")
        print(f"   Errors per file: {params['errors_per_file']}")
        
        # Generate files with various error types
        for i in range(params["files"]):
            file_content = self._generate_file_with_errors(
                f"file_{i:03d}",
                params["lines_per_file"],
                params["errors_per_file"]
            )
            
            # Distribute files across directories
            if i % 3 == 0:
                file_path = project_path / "src" / f"module_{i:03d}.py"
            elif i % 3 == 1:
                file_path = project_path / "tests" / f"test_{i:03d}.py"
            else:
                file_path = project_path / "lib" / f"utils_{i:03d}.py"
            
            with open(file_path, "w") as f:
                f.write(file_content)
        
        print(f"✅ Created {size} project at {project_path}")
        return project_path
    
    def _generate_file_with_errors(self, module_name: str, target_lines: int, error_count: int) -> str:
        """Generate a Python file with specified number of lines and errors."""
        lines = []
        
        # Add header
        lines.append(f'"""Module {module_name} with intentional errors for testing."""')
        lines.append("")
        
        # Add imports (some unused)
        lines.append("import os")
        lines.append("import sys")
        lines.append("import json  # Unused import")
        lines.append("import tempfile  # Unused import")
        lines.append("from typing import List, Dict, Optional")
        lines.append("")
        
        # Add functions with various error types
        errors_added = 0
        function_count = max(1, target_lines // 20)
        
        for func_i in range(function_count):
            lines.append(f"def function_{func_i}(param1, param2):")
            lines.append(f'    """Function {func_i} with some issues."""')
            
            # Add function body with potential errors
            func_lines = max(5, (target_lines - len(lines)) // (function_count - func_i))
            
            for line_i in range(func_lines - 2):  # -2 for def and docstring
                if errors_added < error_count and line_i % 3 == 0:
                    # Add an error
                    error_type = errors_added % 4
                    if error_type == 0:
                        lines.append("    unused_variable = 'never used'")
                    elif error_type == 1:
                        lines.append("    result=param1+param2  # Missing spaces")
                    elif error_type == 2:
                        lines.append("    undefined_var.some_method()")
                    else:
                        lines.append("    very_long_line_that_exceeds_the_recommended_line_length_limit_and_should_be_broken_into_multiple_lines_for_better_readability = True")
                    errors_added += 1
                else:
                    # Add normal code
                    lines.append(f"    result_{line_i} = param1 + param2 + {line_i}")
            
            lines.append("    return result_0")
            lines.append("")
        
        # Add a class
        lines.append(f"class {module_name.title()}Class:")
        lines.append(f'    """Class for {module_name}."""')
        lines.append("")
        lines.append("    def __init__(self, name: str) -> None:")
        lines.append("        self.name = name")
        lines.append("")
        lines.append("    def process(self) -> str:")
        lines.append('        return f"Processing {self.name}"')
        lines.append("")
        
        # Add remaining errors if needed
        while errors_added < error_count and len(lines) < target_lines:
            lines.append("# Additional error line")
            lines.append("another_unused_var = 'unused'")
            errors_added += 1
        
        # Pad to target line count
        while len(lines) < target_lines:
            lines.append(f"# Padding line {len(lines)}")
        
        return "\n".join(lines)
    
    def measure_time(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Measure execution time of a function."""
        # Warm up
        try:
            func(*args, **kwargs)
        except Exception:
            pass
        
        # Force garbage collection
        gc.collect()
        
        # Measure multiple runs
        times = []
        for _ in range(5):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                result = None
                success = False
                print(f"⚠️  Function failed: {e}")
            end_time = time.perf_counter()
            
            times.append(end_time - start_time)
        
        return {
            "success": success,
            "result": result,
            "times": times,
            "mean_time": statistics.mean(times),
            "median_time": statistics.median(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def benchmark_error_detection(self, codebase: Codebase, project_size: str) -> Dict[str, Any]:
        """Benchmark error detection performance."""
        print(f"\n🔍 Benchmarking error detection for {project_size} project...")
        
        results = {}
        
        # Benchmark: Get all errors
        print("   Testing: codebase.errors()")
        results["get_all_errors"] = self.measure_time(codebase.errors)
        
        # Benchmark: Get errors with different filters
        print("   Testing: codebase.errors(include_warnings=True)")
        results["get_errors_with_warnings"] = self.measure_time(
            codebase.errors, include_warnings=True
        )
        
        print("   Testing: codebase.errors(include_hints=True)")
        results["get_errors_with_hints"] = self.measure_time(
            codebase.errors, include_warnings=True, include_hints=True
        )
        
        # Benchmark: Get error summary
        print("   Testing: codebase.error_summary()")
        results["get_error_summary"] = self.measure_time(codebase.error_summary)
        
        # Benchmark: Get fixable errors
        print("   Testing: codebase.get_fixable_errors()")
        results["get_fixable_errors"] = self.measure_time(codebase.get_fixable_errors)
        
        return results
    
    def benchmark_error_context(self, codebase: Codebase, project_size: str) -> Dict[str, Any]:
        """Benchmark error context retrieval performance."""
        print(f"\n🔍 Benchmarking error context for {project_size} project...")
        
        results = {}
        
        # Get some errors first
        errors = codebase.errors()
        
        if not errors:
            print("   ⚠️  No errors found, skipping context benchmarks")
            return results
        
        # Benchmark: Get full error context
        print("   Testing: codebase.full_error_context()")
        results["get_error_context"] = self.measure_time(
            codebase.full_error_context, errors[0].id
        )
        
        # Benchmark: Preview fix
        print("   Testing: codebase.preview_fix()")
        results["preview_fix"] = self.measure_time(
            codebase.preview_fix, errors[0].id
        )
        
        # Benchmark: Multiple context retrievals
        if len(errors) >= 5:
            print("   Testing: Multiple context retrievals")
            
            def get_multiple_contexts():
                contexts = []
                for error in errors[:5]:
                    context = codebase.full_error_context(error.id)
                    contexts.append(context)
                return contexts
            
            results["get_multiple_contexts"] = self.measure_time(get_multiple_contexts)
        
        return results
    
    def benchmark_error_filtering(self, codebase: Codebase, project_size: str) -> Dict[str, Any]:
        """Benchmark error filtering performance."""
        print(f"\n🔍 Benchmarking error filtering for {project_size} project...")
        
        results = {}
        
        # Get all errors to determine available filters
        all_errors = codebase.errors(include_warnings=True, include_hints=True)
        
        if not all_errors:
            print("   ⚠️  No errors found, skipping filtering benchmarks")
            return results
        
        # Benchmark: Filter by category
        categories = set(error.category.value for error in all_errors)
        if categories:
            category = next(iter(categories))
            print(f"   Testing: Filter by category '{category}'")
            results["filter_by_category"] = self.measure_time(
                codebase.errors, category=category
            )
        
        # Benchmark: Filter by source
        sources = set(error.source for error in all_errors)
        if sources:
            source = next(iter(sources))
            print(f"   Testing: Filter by source '{source}'")
            results["filter_by_source"] = self.measure_time(
                codebase.errors, source=source
            )
        
        # Benchmark: Filter by file
        files = set(error.location.file_path for error in all_errors)
        if files:
            file_path = next(iter(files))
            print(f"   Testing: Filter by file '{file_path}'")
            results["filter_by_file"] = self.measure_time(
                codebase.errors, file_path=file_path
            )
        
        return results
    
    def benchmark_error_resolution(self, codebase: Codebase, project_size: str) -> Dict[str, Any]:
        """Benchmark error resolution performance."""
        print(f"\n🔍 Benchmarking error resolution for {project_size} project...")
        
        results = {}
        
        # Get fixable errors
        fixable_errors = codebase.get_fixable_errors(auto_fixable_only=True)
        
        if not fixable_errors:
            print("   ⚠️  No auto-fixable errors found, skipping resolution benchmarks")
            return results
        
        # Benchmark: Resolve single error (preview only to avoid modifying files)
        print("   Testing: codebase.preview_fix() for resolution")
        results["preview_single_fix"] = self.measure_time(
            codebase.preview_fix, fixable_errors[0].id
        )
        
        # Benchmark: Get resolution stats
        if hasattr(codebase, '_get_error_interface'):
            interface = codebase._get_error_interface()
            if hasattr(interface, 'get_resolution_stats'):
                print("   Testing: Get resolution stats")
                results["get_resolution_stats"] = self.measure_time(
                    interface.get_resolution_stats
                )
        
        return results
    
    def benchmark_caching_performance(self, codebase: Codebase, project_size: str) -> Dict[str, Any]:
        """Benchmark caching performance."""
        print(f"\n🔍 Benchmarking caching performance for {project_size} project...")
        
        results = {}
        
        # Benchmark: First call (cold cache)
        print("   Testing: First call (cold cache)")
        results["first_call"] = self.measure_time(codebase.errors)
        
        # Benchmark: Second call (warm cache)
        print("   Testing: Second call (warm cache)")
        results["second_call"] = self.measure_time(codebase.errors)
        
        # Benchmark: Multiple rapid calls
        print("   Testing: Multiple rapid calls")
        
        def multiple_calls():
            results = []
            for _ in range(10):
                errors = codebase.errors()
                results.append(len(errors))
            return results
        
        results["multiple_calls"] = self.measure_time(multiple_calls)
        
        # Benchmark: Cache refresh
        print("   Testing: Cache refresh")
        results["cache_refresh"] = self.measure_time(codebase.refresh_errors)
        
        return results
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmarks."""
        print("🚀 UNIFIED SERENA ERROR INTERFACE - PERFORMANCE BENCHMARKS")
        print("=" * 80)
        
        if not GRAPH_SITTER_AVAILABLE:
            print("❌ Cannot run benchmarks without graph-sitter")
            return {}
        
        all_results = {}
        
        # Test different project sizes
        project_sizes = ["small", "medium", "large"]
        
        for size in project_sizes:
            print(f"\n📊 BENCHMARKING {size.upper()} PROJECT")
            print("=" * 60)
            
            # Create test project
            project_path = self.create_test_project(size)
            
            try:
                # Initialize codebase
                print(f"🔧 Initializing codebase...")
                start_init = time.perf_counter()
                codebase = Codebase(str(project_path))
                end_init = time.perf_counter()
                
                init_time = end_init - start_init
                print(f"✅ Codebase initialized in {init_time:.3f}s")
                
                # Check if unified interface is available
                if not hasattr(codebase, 'errors'):
                    print("⚠️  Unified error interface not available, skipping benchmarks")
                    continue
                
                # Run benchmarks
                size_results = {
                    "project_size": size,
                    "initialization_time": init_time,
                    "error_detection": self.benchmark_error_detection(codebase, size),
                    "error_context": self.benchmark_error_context(codebase, size),
                    "error_filtering": self.benchmark_error_filtering(codebase, size),
                    "error_resolution": self.benchmark_error_resolution(codebase, size),
                    "caching": self.benchmark_caching_performance(codebase, size)
                }
                
                all_results[size] = size_results
                
                # Print summary for this size
                self._print_size_summary(size, size_results)
                
            except Exception as e:
                print(f"❌ Error benchmarking {size} project: {e}")
                import traceback
                traceback.print_exc()
        
        # Print overall summary
        self._print_overall_summary(all_results)
        
        return all_results
    
    def _print_size_summary(self, size: str, results: Dict[str, Any]) -> None:
        """Print summary for a specific project size."""
        print(f"\n📊 SUMMARY FOR {size.upper()} PROJECT:")
        print("-" * 40)
        
        # Error detection performance
        detection = results.get("error_detection", {})
        if detection:
            get_errors = detection.get("get_all_errors", {})
            if get_errors.get("success"):
                print(f"   Get all errors: {get_errors['mean_time']:.3f}s ± {get_errors['std_dev']:.3f}s")
            
            summary = detection.get("get_error_summary", {})
            if summary.get("success"):
                print(f"   Get error summary: {summary['mean_time']:.3f}s ± {summary['std_dev']:.3f}s")
        
        # Caching performance
        caching = results.get("caching", {})
        if caching:
            first_call = caching.get("first_call", {})
            second_call = caching.get("second_call", {})
            
            if first_call.get("success") and second_call.get("success"):
                speedup = first_call['mean_time'] / second_call['mean_time'] if second_call['mean_time'] > 0 else 1
                print(f"   Cache speedup: {speedup:.1f}x")
                print(f"   First call: {first_call['mean_time']:.3f}s")
                print(f"   Second call: {second_call['mean_time']:.3f}s")
    
    def _print_overall_summary(self, all_results: Dict[str, Any]) -> None:
        """Print overall performance summary."""
        print("\n" + "=" * 80)
        print("📊 OVERALL PERFORMANCE SUMMARY")
        print("=" * 80)
        
        # Performance targets (these are reasonable expectations)
        targets = {
            "small": {"get_all_errors": 2.0, "get_error_summary": 1.0},
            "medium": {"get_all_errors": 5.0, "get_error_summary": 2.0},
            "large": {"get_all_errors": 10.0, "get_error_summary": 5.0}
        }
        
        print("🎯 PERFORMANCE TARGETS vs ACTUAL:")
        print("-" * 50)
        
        for size, results in all_results.items():
            if size not in targets:
                continue
            
            print(f"\n{size.upper()} PROJECT:")
            
            detection = results.get("error_detection", {})
            target = targets[size]
            
            # Check get_all_errors performance
            get_errors = detection.get("get_all_errors", {})
            if get_errors.get("success"):
                actual_time = get_errors["mean_time"]
                target_time = target["get_all_errors"]
                status = "✅" if actual_time <= target_time else "⚠️"
                print(f"   {status} Get all errors: {actual_time:.3f}s (target: {target_time:.1f}s)")
            
            # Check get_error_summary performance
            summary = detection.get("get_error_summary", {})
            if summary.get("success"):
                actual_time = summary["mean_time"]
                target_time = target["get_error_summary"]
                status = "✅" if actual_time <= target_time else "⚠️"
                print(f"   {status} Get error summary: {actual_time:.3f}s (target: {target_time:.1f}s)")
        
        # Caching effectiveness
        print(f"\n🚀 CACHING EFFECTIVENESS:")
        print("-" * 30)
        
        for size, results in all_results.items():
            caching = results.get("caching", {})
            first_call = caching.get("first_call", {})
            second_call = caching.get("second_call", {})
            
            if first_call.get("success") and second_call.get("success"):
                speedup = first_call['mean_time'] / second_call['mean_time'] if second_call['mean_time'] > 0 else 1
                status = "✅" if speedup >= 2.0 else "⚠️" if speedup >= 1.5 else "❌"
                print(f"   {status} {size.title()}: {speedup:.1f}x speedup")
        
        print(f"\n🏆 RECOMMENDATIONS:")
        print("-" * 20)
        print("✅ Performance targets met: Interface is ready for production")
        print("⚠️  Performance targets missed: Consider optimization")
        print("❌ Poor performance: Requires investigation and fixes")
    
    def cleanup(self) -> None:
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"⚠️  Could not clean up {temp_dir}: {e}")


def main():
    """Main benchmark function."""
    benchmark = PerformanceBenchmark()
    
    try:
        results = benchmark.run_comprehensive_benchmark()
        
        # Save results to file
        import json
        results_file = "error_interface_performance_results.json"
        
        try:
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
        
    finally:
        benchmark.cleanup()


if __name__ == "__main__":
    main()

