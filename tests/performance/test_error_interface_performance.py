#!/usr/bin/env python3
"""
Performance Tests for Unified Error Interface

This test suite focuses on performance testing of the unified error interface methods,
including benchmarking, memory usage, and scalability testing.
"""

import pytest
import time
import tempfile
import shutil
import psutil
import os
import threading
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from graph_sitter.enhanced.codebase import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    pytest.skip("Graph-sitter not available", allow_module_level=True)


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        print(f"{self.operation_name}: {self.duration:.3f} seconds")


class MemoryProfiler:
    """Context manager for memory profiling."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.process = psutil.Process(os.getpid())
        self.start_memory = None
        self.end_memory = None
        self.memory_diff = None
    
    def __enter__(self):
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.memory_diff = self.end_memory - self.start_memory
        print(f"{self.operation_name} memory usage: {self.memory_diff:.2f} MB")


class TestErrorInterfacePerformance:
    """Performance tests for unified error interface."""
    
    @pytest.fixture
    def small_codebase(self):
        """Create a small codebase for performance testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create 5 files with various errors
        files = {
            "file1.py": '''
import os
import sys

def function_with_error():
    undefined_variable = some_undefined_var  # NameError
    return undefined_variable

class TestClass:
    def method(self):
        return self.nonexistent_attr  # AttributeError
''',
            "file2.py": '''
from typing import List, Dict

def type_error_function(items: List[str]) -> Dict[str, int]:
    result = {}
    for item in items:
        result[item] = item.length()  # AttributeError: str has no attribute 'length'
    return result
''',
            "file3.py": '''
import json

def syntax_issues():
    data = {"key": "value"
    # Missing closing brace - syntax error
    return data
''',
            "file4.py": '''
def long_function_with_many_issues():
    """Function with multiple code quality issues."""
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10  # Too many local variables
    
    if x > 0:
        if y > 0:
            if z > 0:
                if a > 0:
                    if b > 0:  # Too deeply nested
                        return "deeply nested"
    
    return undefined_return_var  # NameError
''',
            "file5.py": '''
"""Valid file for comparison."""

def valid_function():
    """A properly implemented function."""
    return "success"

class ValidClass:
    """A properly implemented class."""
    
    def __init__(self):
        self.value = "initialized"
    
    def get_value(self):
        """Get the value."""
        return self.value
'''
        }
        
        for filename, content in files.items():
            (Path(temp_dir) / filename).write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def medium_codebase(self):
        """Create a medium-sized codebase for performance testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create 25 files
        for i in range(25):
            content = f'''
"""Module {i} for performance testing."""

import os
import sys
from typing import List, Dict, Optional

class Module{i}Class:
    """Class for module {i}."""
    
    def __init__(self):
        self.value = {i}
        self.undefined_attr = undefined_variable_{i}  # NameError
    
    def process_data(self, items: List[str]) -> Dict[str, int]:
        """Process data with potential errors."""
        result = {{}}
        for item in items:
            if item:
                result[item] = len(item) + {i}
            else:
                result[item] = nonexistent_function()  # NameError
        return result
    
    def method_with_type_error(self, param):
        """Method with type error."""
        return param + "string" + {i}  # Potential type error

def function_{i}():
    """Function {i} with issues."""
    instance = Module{i}Class()
    data = ["item1", "item2", None]
    result = instance.process_data(data)
    
    # Unused variable
    unused_var = "not used"
    
    return result.get("nonexistent_key").upper()  # AttributeError

if __name__ == "__main__":
    function_{i}()
'''
            (Path(temp_dir) / f"module_{i}.py").write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def large_codebase(self):
        """Create a large codebase for stress testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create 100 files
        for i in range(100):
            content = f'''
"""Large module {i} for stress testing."""

import os
import sys
import json
import re
from typing import List, Dict, Optional, Union, Any
from pathlib import Path

class LargeModule{i}:
    """Large class with many methods and potential issues."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data = []
        self.processed = False
        self.error_count = 0
        self.undefined_init_var = some_undefined_variable  # NameError
    
    def validate_config(self) -> bool:
        """Validate configuration with errors."""
        if not self.config:
            return False
        
        required_keys = ["key1", "key2", "key3"]
        for key in required_keys:
            if key not in self.config:
                self.error_count += 1
                return False
        
        # Type error
        return self.config["key1"] + 42  # Potential type error
    
    def process_large_dataset(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process large dataset with multiple issues."""
        results = {{}}
        
        for i, item in enumerate(dataset):
            try:
                # Multiple potential errors
                processed_item = {{
                    "id": item["id"],
                    "value": item["value"] * 2,
                    "processed": True,
                    "index": i,
                    "undefined": undefined_processing_var  # NameError
                }}
                
                # Attribute error
                results[item.get_key()] = processed_item  # AttributeError
                
            except KeyError as e:
                self.error_count += 1
                continue
            except Exception as e:
                # Broad exception handling (code smell)
                pass
        
        return results
    
    def complex_calculation(self, x: float, y: float, z: float) -> float:
        """Complex calculation with nested conditions."""
        if x > 0:
            if y > 0:
                if z > 0:
                    if x > y:
                        if y > z:
                            if x > z:
                                # Too deeply nested
                                return x * y * z + undefined_calc_var  # NameError
                            else:
                                return x + y + z
                        else:
                            return x - y - z
                    else:
                        return y - x - z
                else:
                    return x + y
            else:
                return x
        else:
            return 0.0
    
    def method_with_many_params(self, a, b, c, d, e, f, g, h, i, j, k, l):
        """Method with too many parameters."""
        return a + b + c + d + e + f + g + h + i + j + k + l + undefined_sum_var
    
    def unused_method_1(self):
        """Unused method 1."""
        pass
    
    def unused_method_2(self):
        """Unused method 2."""
        pass
    
    def unused_method_3(self):
        """Unused method 3."""
        pass

def global_function_{i}(param1, param2, param3, param4, param5):
    """Global function with issues."""
    instance = LargeModule{i}({{"key1": "value1", "key2": "value2"}})
    
    # Long line that exceeds recommended length limits and should trigger style warnings
    very_long_variable_name_that_makes_this_line_extremely_long = param1 + param2 + param3 + param4 + param5 + "additional_string_to_make_it_even_longer"
    
    dataset = [
        {{"id": 1, "value": 10}},
        {{"id": 2, "value": 20}},
        {{"id": 3, "value": 30}}
    ]
    
    result = instance.process_large_dataset(dataset)
    calculation = instance.complex_calculation(1.0, 2.0, 3.0)
    
    return result, calculation, undefined_global_var  # NameError

# Module-level undefined variable
MODULE_CONSTANT = undefined_module_constant

if __name__ == "__main__":
    global_function_{i}("a", "b", "c", "d", "e")
'''
            (Path(temp_dir) / f"large_module_{i}.py").write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_errors_method_performance_small(self, small_codebase):
        """Test errors() method performance on small codebase."""
        codebase = Codebase(small_codebase)
        
        with PerformanceTimer("errors() - small codebase") as timer:
            with MemoryProfiler("errors() - small codebase") as memory:
                errors = codebase.errors()
        
        print(f"Found {len(errors)} errors in small codebase")
        
        # Performance assertions
        assert timer.duration < 10.0, f"Small codebase analysis took too long: {timer.duration:.3f}s"
        assert memory.memory_diff < 100, f"Memory usage too high: {memory.memory_diff:.2f}MB"
    
    def test_errors_method_performance_medium(self, medium_codebase):
        """Test errors() method performance on medium codebase."""
        codebase = Codebase(medium_codebase)
        
        with PerformanceTimer("errors() - medium codebase") as timer:
            with MemoryProfiler("errors() - medium codebase") as memory:
                errors = codebase.errors()
        
        print(f"Found {len(errors)} errors in medium codebase")
        
        # Performance assertions
        assert timer.duration < 30.0, f"Medium codebase analysis took too long: {timer.duration:.3f}s"
        assert memory.memory_diff < 200, f"Memory usage too high: {memory.memory_diff:.2f}MB"
    
    def test_errors_method_performance_large(self, large_codebase):
        """Test errors() method performance on large codebase."""
        codebase = Codebase(large_codebase)
        
        with PerformanceTimer("errors() - large codebase") as timer:
            with MemoryProfiler("errors() - large codebase") as memory:
                errors = codebase.errors()
        
        print(f"Found {len(errors)} errors in large codebase")
        
        # Performance assertions (more lenient for large codebase)
        assert timer.duration < 120.0, f"Large codebase analysis took too long: {timer.duration:.3f}s"
        assert memory.memory_diff < 500, f"Memory usage too high: {memory.memory_diff:.2f}MB"
    
    def test_caching_performance(self, medium_codebase):
        """Test that caching improves performance on repeated calls."""
        codebase = Codebase(medium_codebase)
        
        # First call (cold cache)
        with PerformanceTimer("errors() - first call") as timer1:
            errors1 = codebase.errors()
        
        # Second call (warm cache)
        with PerformanceTimer("errors() - second call") as timer2:
            errors2 = codebase.errors()
        
        # Third call (warm cache)
        with PerformanceTimer("errors() - third call") as timer3:
            errors3 = codebase.errors()
        
        print(f"First call: {timer1.duration:.3f}s")
        print(f"Second call: {timer2.duration:.3f}s")
        print(f"Third call: {timer3.duration:.3f}s")
        
        # Results should be consistent
        assert len(errors1) == len(errors2) == len(errors3)
        
        # Subsequent calls should be faster (allowing some variance)
        if timer1.duration > 1.0:  # Only test if first call was significant
            assert timer2.duration <= timer1.duration * 0.8, "Second call should benefit from caching"
            assert timer3.duration <= timer1.duration * 0.8, "Third call should benefit from caching"
    
    def test_full_error_context_performance(self, medium_codebase):
        """Test full_error_context() method performance."""
        codebase = Codebase(medium_codebase)
        errors = codebase.errors()
        
        if not errors:
            pytest.skip("No errors found for context testing")
        
        # Test context generation for multiple errors
        context_times = []
        
        for i, error in enumerate(errors[:10]):  # Test first 10 errors
            with PerformanceTimer(f"full_error_context() - error {i+1}") as timer:
                context = codebase.full_error_context(error['id'])
            
            context_times.append(timer.duration)
            
            # Verify context quality
            assert isinstance(context, dict)
            assert 'context' in context
            assert 'suggestions' in context
        
        avg_context_time = sum(context_times) / len(context_times)
        max_context_time = max(context_times)
        
        print(f"Average context generation time: {avg_context_time:.3f}s")
        print(f"Maximum context generation time: {max_context_time:.3f}s")
        
        # Performance assertions
        assert avg_context_time < 2.0, f"Average context time too slow: {avg_context_time:.3f}s"
        assert max_context_time < 5.0, f"Maximum context time too slow: {max_context_time:.3f}s"
    
    def test_resolve_errors_performance(self, small_codebase):
        """Test resolve_errors() method performance."""
        codebase = Codebase(small_codebase)
        
        with PerformanceTimer("resolve_errors()") as timer:
            with MemoryProfiler("resolve_errors()") as memory:
                result = codebase.resolve_errors()
        
        print(f"Resolved {result['fixed_errors']}/{result['total_errors']} errors")
        
        # Performance assertions
        assert timer.duration < 30.0, f"Error resolution took too long: {timer.duration:.3f}s"
        assert memory.memory_diff < 100, f"Memory usage too high: {memory.memory_diff:.2f}MB"
    
    def test_concurrent_access_performance(self, medium_codebase):
        """Test performance under concurrent access."""
        codebase = Codebase(medium_codebase)
        
        def worker_task(worker_id: int) -> Dict[str, Any]:
            """Worker task for concurrent testing."""
            start_time = time.perf_counter()
            
            # Perform various operations
            errors = codebase.errors()
            
            if errors:
                context = codebase.full_error_context(errors[0]['id'])
                resolve_result = codebase.resolve_error(errors[0]['id'])
            else:
                context = {}
                resolve_result = {}
            
            end_time = time.perf_counter()
            
            return {
                'worker_id': worker_id,
                'duration': end_time - start_time,
                'errors_count': len(errors),
                'context_keys': len(context.keys()) if context else 0,
                'resolve_success': resolve_result.get('success', False)
            }
        
        # Run concurrent workers
        num_workers = 5
        
        with PerformanceTimer(f"Concurrent access - {num_workers} workers") as timer:
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(worker_task, i) for i in range(num_workers)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        durations = [r['duration'] for r in results]
        error_counts = [r['errors_count'] for r in results]
        
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        print(f"Concurrent access - Average worker time: {avg_duration:.3f}s")
        print(f"Concurrent access - Maximum worker time: {max_duration:.3f}s")
        print(f"Concurrent access - Total time: {timer.duration:.3f}s")
        
        # All workers should get consistent results
        assert len(set(error_counts)) <= 2, "Error counts should be consistent across workers"
        
        # Performance should be reasonable
        assert avg_duration < 20.0, f"Average worker time too slow: {avg_duration:.3f}s"
        assert max_duration < 30.0, f"Maximum worker time too slow: {max_duration:.3f}s"
    
    def test_memory_usage_scaling(self, small_codebase, medium_codebase):
        """Test memory usage scaling with codebase size."""
        # Test small codebase
        with MemoryProfiler("Small codebase memory") as small_memory:
            small_codebase_obj = Codebase(small_codebase)
            small_errors = small_codebase_obj.errors()
        
        # Test medium codebase
        with MemoryProfiler("Medium codebase memory") as medium_memory:
            medium_codebase_obj = Codebase(medium_codebase)
            medium_errors = medium_codebase_obj.errors()
        
        print(f"Small codebase: {len(small_errors)} errors, {small_memory.memory_diff:.2f}MB")
        print(f"Medium codebase: {len(medium_errors)} errors, {medium_memory.memory_diff:.2f}MB")
        
        # Memory usage should scale reasonably
        if len(medium_errors) > len(small_errors):
            memory_ratio = medium_memory.memory_diff / max(small_memory.memory_diff, 1)
            error_ratio = len(medium_errors) / max(len(small_errors), 1)
            
            print(f"Memory scaling ratio: {memory_ratio:.2f}")
            print(f"Error scaling ratio: {error_ratio:.2f}")
            
            # Memory usage should not scale worse than O(n^2)
            assert memory_ratio <= error_ratio * 2, "Memory usage scaling is too poor"
    
    def test_repeated_operations_performance(self, small_codebase):
        """Test performance of repeated operations."""
        codebase = Codebase(small_codebase)
        
        # Warm up
        errors = codebase.errors()
        
        if not errors:
            pytest.skip("No errors found for repeated operations testing")
        
        error_id = errors[0]['id']
        
        # Test repeated context calls
        context_times = []
        for i in range(10):
            with PerformanceTimer(f"Context call {i+1}") as timer:
                context = codebase.full_error_context(error_id)
            context_times.append(timer.duration)
        
        # Test repeated resolution calls
        resolve_times = []
        for i in range(5):
            with PerformanceTimer(f"Resolve call {i+1}") as timer:
                result = codebase.resolve_error(error_id)
            resolve_times.append(timer.duration)
        
        avg_context_time = sum(context_times) / len(context_times)
        avg_resolve_time = sum(resolve_times) / len(resolve_times)
        
        print(f"Average repeated context time: {avg_context_time:.3f}s")
        print(f"Average repeated resolve time: {avg_resolve_time:.3f}s")
        
        # Repeated operations should be fast
        assert avg_context_time < 1.0, f"Repeated context calls too slow: {avg_context_time:.3f}s"
        assert avg_resolve_time < 2.0, f"Repeated resolve calls too slow: {avg_resolve_time:.3f}s"


class TestScalabilityBenchmarks:
    """Scalability benchmarks for different codebase sizes."""
    
    def create_synthetic_codebase(self, num_files: int, errors_per_file: int) -> str:
        """Create synthetic codebase for benchmarking."""
        temp_dir = tempfile.mkdtemp()
        
        for i in range(num_files):
            errors = []
            for j in range(errors_per_file):
                errors.append(f"    undefined_var_{j} = some_undefined_variable_{j}  # NameError")
            
            content = f'''
"""Synthetic module {i} for benchmarking."""

import os
import sys

class BenchmarkClass{i}:
    def __init__(self):
        self.value = {i}
{chr(10).join(errors)}
    
    def method_{i}(self):
        return self.nonexistent_attr_{i}  # AttributeError

def function_{i}():
    instance = BenchmarkClass{i}()
    return instance.method_{i}()
'''
            (Path(temp_dir) / f"benchmark_{i}.py").write_text(content)
        
        return temp_dir
    
    @pytest.mark.parametrize("num_files,errors_per_file", [
        (10, 2),
        (25, 3),
        (50, 4),
        (100, 5)
    ])
    def test_scalability_benchmark(self, num_files, errors_per_file):
        """Benchmark performance across different codebase sizes."""
        codebase_dir = self.create_synthetic_codebase(num_files, errors_per_file)
        
        try:
            codebase = Codebase(codebase_dir)
            
            with PerformanceTimer(f"Benchmark {num_files} files, {errors_per_file} errors/file") as timer:
                with MemoryProfiler(f"Benchmark {num_files} files") as memory:
                    errors = codebase.errors()
            
            expected_errors = num_files * errors_per_file
            print(f"Expected ~{expected_errors} errors, found {len(errors)}")
            print(f"Performance: {timer.duration:.3f}s, Memory: {memory.memory_diff:.2f}MB")
            
            # Calculate performance metrics
            errors_per_second = len(errors) / timer.duration if timer.duration > 0 else 0
            memory_per_error = memory.memory_diff / len(errors) if len(errors) > 0 else 0
            
            print(f"Throughput: {errors_per_second:.1f} errors/second")
            print(f"Memory efficiency: {memory_per_error:.3f} MB/error")
            
            # Performance should be reasonable
            assert timer.duration < num_files * 2.0, f"Performance too slow for {num_files} files"
            assert memory.memory_diff < num_files * 10.0, f"Memory usage too high for {num_files} files"
            
        finally:
            shutil.rmtree(codebase_dir)


if __name__ == "__main__":
    # Run performance tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short", "-m", "not slow"])

