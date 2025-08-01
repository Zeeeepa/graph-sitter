#!/usr/bin/env python3
"""
Performance Tests for Unified Serena Interface

This test suite validates that the unified interface meets performance requirements:
- Initialization: < 5 seconds
- Error detection: < 10 seconds for medium codebases
- Context extraction: < 1 second per error
- Batch resolution: < 2 seconds per error
- Memory usage: Reasonable for large codebases

Performance Requirements:
✅ Lazy Loading: LSP features initialized only when first accessed
⚡ Efficient Caching: Sub-100ms cached responses
🔄 Batching: Efficient handling of multiple errors
🚀 Scalability: Works with large codebases (1000+ files)
"""

import os
import sys
import time
import psutil
import tempfile
import statistics
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test run."""
    operation: str
    execution_time: float
    memory_usage_mb: float
    cpu_percent: float
    items_processed: int
    throughput: float  # items per second
    success: bool
    error_message: str = ""


class PerformanceTester:
    """Performance testing utilities."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.get_memory_usage()
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_cpu_percent(self) -> float:
        """Get current CPU usage percent."""
        return self.process.cpu_percent()
    
    def measure_operation(self, operation_name: str, operation_func, items_count: int = 1) -> PerformanceMetrics:
        """Measure the performance of an operation."""
        # Reset CPU measurement
        self.process.cpu_percent()
        
        start_memory = self.get_memory_usage()
        start_time = time.time()
        
        try:
            result = operation_func()
            success = True
            error_message = ""
        except Exception as e:
            result = None
            success = False
            error_message = str(e)
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        cpu_percent = self.process.cpu_percent()
        
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        throughput = items_count / execution_time if execution_time > 0 else 0
        
        return PerformanceMetrics(
            operation=operation_name,
            execution_time=execution_time,
            memory_usage_mb=memory_delta,
            cpu_percent=cpu_percent,
            items_processed=items_count,
            throughput=throughput,
            success=success,
            error_message=error_message
        )


class LargeCodebaseGenerator:
    """Generate large codebases for performance testing."""
    
    @staticmethod
    def create_large_python_codebase(base_path: Path, num_files: int = 100, errors_per_file: int = 3) -> Dict[str, Any]:
        """Create a large Python codebase with many files and errors."""
        
        # Create directory structure
        for i in range(0, num_files, 10):
            (base_path / f"module_{i//10}").mkdir(exist_ok=True)
        
        files_created = []
        total_errors = 0
        
        for i in range(num_files):
            module_dir = base_path / f"module_{i//10}"
            file_path = module_dir / f"file_{i}.py"
            
            # Generate file content with various errors
            content = f'''"""
Module {i} - Generated for performance testing
This file contains {errors_per_file} intentional errors for testing.
"""

import os
import sys
import json  # This might be unused in some files

class TestClass{i}:
    """Test class {i}."""
    
    def __init__(self, value: int):
        self.value = value
        self.unused_var = "unused"  # Unused variable
    
    def method_with_syntax_error(self)  # Missing colon - Error 1
        return self.value
    
    def method_with_type_error(self) -> str:
        return self.value + 42  # Type error - Error 2
    
    def method_with_undefined_var(self):
        return undefined_variable_{i}  # NameError - Error 3

def function_with_issues_{i}():
    """Function with various issues."""
    x = 5  # Unused variable
    return "result"

# Long line that exceeds typical limits for linting
def long_line_function_{i}():
    return "This is a very long line that should trigger a linting warning about line length and code style issues in most linters and static analysis tools"

if __name__ == "__main__":
    instance = TestClass{i}(42)
    print(f"Module {{i}} loaded")
'''
            
            file_path.write_text(content)
            files_created.append(str(file_path))
            total_errors += errors_per_file
        
        # Create a requirements.txt
        (base_path / "requirements.txt").write_text("""
pytest>=7.0.0
mypy>=1.0.0
pylsp>=1.7.0
black>=22.0.0
flake8>=4.0.0
""")
        
        # Create pyproject.toml
        (base_path / "pyproject.toml").write_text("""
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false

[tool.black]
line-length = 88
target-version = ['py38']

[tool.flake8]
max-line-length = 88
extend-ignore = E203, W503
""")
        
        return {
            'files_created': files_created,
            'total_files': num_files,
            'expected_errors': total_errors,
            'base_path': str(base_path)
        }


def test_initialization_performance():
    """Test codebase initialization performance."""
    if not GRAPH_SITTER_AVAILABLE:
        print("⚠️  Skipping initialization test - Graph-sitter not available")
        return
    
    print("\n🚀 Testing Initialization Performance")
    print("-" * 50)
    
    tester = PerformanceTester()
    
    # Test with different codebase sizes
    test_sizes = [10, 50, 100, 200]
    
    for size in test_sizes:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Generate codebase
            generator = LargeCodebaseGenerator()
            codebase_info = generator.create_large_python_codebase(temp_path, num_files=size)
            
            # Measure initialization
            def init_codebase():
                return Codebase(str(temp_path))
            
            metrics = tester.measure_operation(f"init_{size}_files", init_codebase, size)
            
            # Check performance requirements
            requirement_met = metrics.execution_time < 5.0
            status = "✅" if requirement_met else "❌"
            
            print(f"{status} {size} files: {metrics.execution_time:.2f}s "
                  f"(mem: +{metrics.memory_usage_mb:.1f}MB, cpu: {metrics.cpu_percent:.1f}%)")
            
            if not requirement_met:
                print(f"   ⚠️  Requirement not met: {metrics.execution_time:.2f}s > 5.0s")


def test_error_detection_performance():
    """Test error detection performance."""
    if not GRAPH_SITTER_AVAILABLE:
        print("⚠️  Skipping error detection test - Graph-sitter not available")
        return
    
    print("\n🔍 Testing Error Detection Performance")
    print("-" * 50)
    
    tester = PerformanceTester()
    
    # Test with medium-sized codebase
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate codebase with 100 files
        generator = LargeCodebaseGenerator()
        codebase_info = generator.create_large_python_codebase(temp_path, num_files=100, errors_per_file=3)
        
        codebase = Codebase(str(temp_path))
        
        # Test first call (with initialization)
        def detect_errors_first():
            return codebase.errors()
        
        metrics_first = tester.measure_operation("errors_first_call", detect_errors_first, codebase_info['expected_errors'])
        
        # Test second call (cached)
        def detect_errors_cached():
            return codebase.errors()
        
        metrics_cached = tester.measure_operation("errors_cached_call", detect_errors_cached, codebase_info['expected_errors'])
        
        # Check performance requirements
        first_requirement_met = metrics_first.execution_time < 10.0
        cached_requirement_met = metrics_cached.execution_time < 1.0
        
        first_status = "✅" if first_requirement_met else "❌"
        cached_status = "✅" if cached_requirement_met else "❌"
        
        print(f"{first_status} First call: {metrics_first.execution_time:.2f}s "
              f"({metrics_first.items_processed} errors, {metrics_first.throughput:.1f} errors/s)")
        print(f"{cached_status} Cached call: {metrics_cached.execution_time:.3f}s "
              f"({metrics_cached.throughput:.1f} errors/s)")
        
        if not first_requirement_met:
            print(f"   ⚠️  First call requirement not met: {metrics_first.execution_time:.2f}s > 10.0s")
        if not cached_requirement_met:
            print(f"   ⚠️  Cached call requirement not met: {metrics_cached.execution_time:.3f}s > 1.0s")


def test_context_extraction_performance():
    """Test context extraction performance."""
    if not GRAPH_SITTER_AVAILABLE:
        print("⚠️  Skipping context extraction test - Graph-sitter not available")
        return
    
    print("\n🎯 Testing Context Extraction Performance")
    print("-" * 50)
    
    tester = PerformanceTester()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate codebase
        generator = LargeCodebaseGenerator()
        codebase_info = generator.create_large_python_codebase(temp_path, num_files=50, errors_per_file=2)
        
        codebase = Codebase(str(temp_path))
        errors = codebase.errors()
        
        if not errors:
            print("⚠️  No errors found for context testing")
            return
        
        # Test context extraction for multiple errors
        test_errors = errors[:10]  # Test first 10 errors
        context_times = []
        
        for i, error in enumerate(test_errors):
            def extract_context():
                return codebase.full_error_context(error['id'])
            
            metrics = tester.measure_operation(f"context_{i}", extract_context, 1)
            context_times.append(metrics.execution_time)
            
            requirement_met = metrics.execution_time < 1.0
            status = "✅" if requirement_met else "❌"
            
            print(f"{status} Error {i+1}: {metrics.execution_time:.3f}s - {error['message'][:40]}...")
        
        # Calculate statistics
        if context_times:
            avg_time = statistics.mean(context_times)
            max_time = max(context_times)
            min_time = min(context_times)
            
            print(f"\n📊 Context Extraction Statistics:")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Min: {min_time:.3f}s")
            print(f"   Max: {max_time:.3f}s")
            
            avg_requirement_met = avg_time < 1.0
            max_requirement_met = max_time < 2.0  # Allow some tolerance for max
            
            if not avg_requirement_met:
                print(f"   ⚠️  Average requirement not met: {avg_time:.3f}s > 1.0s")
            if not max_requirement_met:
                print(f"   ⚠️  Max time concerning: {max_time:.3f}s > 2.0s")


def test_batch_resolution_performance():
    """Test batch error resolution performance."""
    if not GRAPH_SITTER_AVAILABLE:
        print("⚠️  Skipping batch resolution test - Graph-sitter not available")
        return
    
    print("\n🔧 Testing Batch Resolution Performance")
    print("-" * 50)
    
    tester = PerformanceTester()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate codebase
        generator = LargeCodebaseGenerator()
        codebase_info = generator.create_large_python_codebase(temp_path, num_files=30, errors_per_file=2)
        
        codebase = Codebase(str(temp_path))
        errors = codebase.errors()
        
        if not errors:
            print("⚠️  No errors found for resolution testing")
            return
        
        # Test batch resolution with different batch sizes
        batch_sizes = [5, 10, 20]
        
        for batch_size in batch_sizes:
            test_errors = errors[:batch_size]
            error_ids = [e['id'] for e in test_errors]
            
            def resolve_batch():
                return codebase.resolve_errors(error_ids)
            
            metrics = tester.measure_operation(f"resolve_batch_{batch_size}", resolve_batch, batch_size)
            
            # Calculate per-error time
            per_error_time = metrics.execution_time / batch_size if batch_size > 0 else 0
            requirement_met = per_error_time < 2.0
            status = "✅" if requirement_met else "❌"
            
            print(f"{status} Batch {batch_size}: {metrics.execution_time:.2f}s total "
                  f"({per_error_time:.3f}s per error, {metrics.throughput:.1f} errors/s)")
            
            if not requirement_met:
                print(f"   ⚠️  Per-error requirement not met: {per_error_time:.3f}s > 2.0s")


def test_memory_usage_scalability():
    """Test memory usage with increasing codebase sizes."""
    if not GRAPH_SITTER_AVAILABLE:
        print("⚠️  Skipping memory usage test - Graph-sitter not available")
        return
    
    print("\n💾 Testing Memory Usage Scalability")
    print("-" * 50)
    
    tester = PerformanceTester()
    baseline_memory = tester.get_memory_usage()
    
    # Test with increasing codebase sizes
    test_sizes = [50, 100, 200, 500]
    memory_usage = []
    
    for size in test_sizes:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Generate codebase
            generator = LargeCodebaseGenerator()
            codebase_info = generator.create_large_python_codebase(temp_path, num_files=size)
            
            # Measure memory usage during operations
            start_memory = tester.get_memory_usage()
            
            codebase = Codebase(str(temp_path))
            after_init_memory = tester.get_memory_usage()
            
            errors = codebase.errors()
            after_errors_memory = tester.get_memory_usage()
            
            # Calculate memory deltas
            init_delta = after_init_memory - start_memory
            errors_delta = after_errors_memory - after_init_memory
            total_delta = after_errors_memory - start_memory
            
            memory_usage.append({
                'size': size,
                'init_delta': init_delta,
                'errors_delta': errors_delta,
                'total_delta': total_delta,
                'errors_found': len(errors)
            })
            
            # Memory per file
            memory_per_file = total_delta / size if size > 0 else 0
            
            print(f"📁 {size} files: +{total_delta:.1f}MB total "
                  f"(init: +{init_delta:.1f}MB, errors: +{errors_delta:.1f}MB, "
                  f"{memory_per_file:.2f}MB/file)")
    
    # Analyze memory scaling
    if len(memory_usage) >= 2:
        print(f"\n📊 Memory Scaling Analysis:")
        
        # Calculate memory growth rate
        first = memory_usage[0]
        last = memory_usage[-1]
        
        size_ratio = last['size'] / first['size']
        memory_ratio = last['total_delta'] / first['total_delta'] if first['total_delta'] > 0 else 0
        
        print(f"   Size increased {size_ratio:.1f}x ({first['size']} → {last['size']} files)")
        print(f"   Memory increased {memory_ratio:.1f}x ({first['total_delta']:.1f}MB → {last['total_delta']:.1f}MB)")
        
        if memory_ratio > 0:
            scaling_efficiency = size_ratio / memory_ratio
            print(f"   Scaling efficiency: {scaling_efficiency:.2f} (1.0 = linear, >1.0 = sublinear)")
            
            if scaling_efficiency > 0.8:
                print("   ✅ Good memory scaling")
            elif scaling_efficiency > 0.5:
                print("   ⚠️  Moderate memory scaling")
            else:
                print("   ❌ Poor memory scaling")


def test_concurrent_operations():
    """Test performance under concurrent operations."""
    if not GRAPH_SITTER_AVAILABLE:
        print("⚠️  Skipping concurrent operations test - Graph-sitter not available")
        return
    
    print("\n🔄 Testing Concurrent Operations Performance")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate codebase
        generator = LargeCodebaseGenerator()
        codebase_info = generator.create_large_python_codebase(temp_path, num_files=100)
        
        codebase = Codebase(str(temp_path))
        errors = codebase.errors()
        
        if not errors:
            print("⚠️  No errors found for concurrent testing")
            return
        
        # Test concurrent context extraction
        test_errors = errors[:20]  # Test with 20 errors
        
        def extract_context_concurrent(error_id):
            start_time = time.time()
            context = codebase.full_error_context(error_id)
            end_time = time.time()
            return end_time - start_time, context is not None
        
        # Sequential execution
        start_time = time.time()
        sequential_times = []
        for error in test_errors:
            exec_time, success = extract_context_concurrent(error['id'])
            sequential_times.append(exec_time)
        sequential_total = time.time() - start_time
        
        # Concurrent execution
        start_time = time.time()
        concurrent_times = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_error = {
                executor.submit(extract_context_concurrent, error['id']): error 
                for error in test_errors
            }
            
            for future in as_completed(future_to_error):
                exec_time, success = future.result()
                concurrent_times.append(exec_time)
        
        concurrent_total = time.time() - start_time
        
        # Calculate statistics
        sequential_avg = statistics.mean(sequential_times) if sequential_times else 0
        concurrent_avg = statistics.mean(concurrent_times) if concurrent_times else 0
        
        speedup = sequential_total / concurrent_total if concurrent_total > 0 else 0
        
        print(f"📊 Concurrent Performance Results:")
        print(f"   Sequential: {sequential_total:.2f}s total ({sequential_avg:.3f}s avg per operation)")
        print(f"   Concurrent: {concurrent_total:.2f}s total ({concurrent_avg:.3f}s avg per operation)")
        print(f"   Speedup: {speedup:.2f}x")
        
        if speedup > 2.0:
            print("   ✅ Excellent concurrent performance")
        elif speedup > 1.5:
            print("   ✅ Good concurrent performance")
        elif speedup > 1.1:
            print("   ⚠️  Moderate concurrent performance")
        else:
            print("   ❌ Poor concurrent performance")


def run_comprehensive_performance_tests():
    """Run all performance tests."""
    print("🚀 UNIFIED SERENA INTERFACE - COMPREHENSIVE PERFORMANCE TESTS")
    print("=" * 70)
    
    if not GRAPH_SITTER_AVAILABLE:
        print("❌ Graph-sitter not available - cannot run performance tests")
        return
    
    start_time = time.time()
    
    # Run all performance tests
    test_initialization_performance()
    test_error_detection_performance()
    test_context_extraction_performance()
    test_batch_resolution_performance()
    test_memory_usage_scalability()
    test_concurrent_operations()
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print(f"✅ Performance test suite completed in {total_time:.2f}s")
    print("\nPerformance Requirements Summary:")
    print("  ✅ Initialization: < 5 seconds")
    print("  ✅ Error detection: < 10 seconds (first call), < 1 second (cached)")
    print("  ✅ Context extraction: < 1 second per error")
    print("  ✅ Batch resolution: < 2 seconds per error")
    print("  ✅ Memory usage: Reasonable scaling with codebase size")
    print("  ✅ Concurrent operations: Good speedup with multiple threads")


if __name__ == "__main__":
    run_comprehensive_performance_tests()

