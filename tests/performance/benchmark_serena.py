"""
Performance Benchmarks for Serena LSP Integration

Comprehensive performance testing for all Serena capabilities.
"""

import time
import statistics
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any
import json

from graph_sitter.extensions.serena.core import SerenaCore, SerenaConfig
from graph_sitter.extensions.serena.integration import SerenaIntegration


class MockCodebase:
    """Mock Codebase for benchmarking."""
    
    def __init__(self, repo_path: str, num_files: int = 100):
        self.repo_path = repo_path
        self.files = []
        self.symbols = []
        
        # Generate mock files
        for i in range(num_files):
            mock_file = type('MockFile', (), {
                'path': f'src/file_{i}.py',
                'content': self._generate_file_content(i),
                'symbols': self._generate_symbols(i)
            })()
            self.files.append(mock_file)
    
    def _generate_file_content(self, file_num: int) -> str:
        """Generate realistic file content."""
        return f'''"""
Module {file_num} - Test module for benchmarking.
"""

import os
import sys
from typing import List, Dict, Optional

class TestClass{file_num}:
    """Test class for benchmarking."""
    
    def __init__(self, name: str, value: int = 0):
        self.name = name
        self.value = value
    
    def calculate_result(self, items: List[int]) -> int:
        """Calculate result from items."""
        total = sum(items)
        return total * self.value
    
    def process_data(self, data: Dict[str, Any]) -> Optional[str]:
        """Process data and return result."""
        if not data:
            return None
        
        result = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                result.append(f"{key}: {value * 2}")
            else:
                result.append(f"{key}: {str(value)}")
        
        return ", ".join(result)

def utility_function_{file_num}(param1: str, param2: int = 10) -> bool:
    """Utility function for testing."""
    return len(param1) > param2

def complex_calculation_{file_num}(data: List[Dict[str, Any]]) -> float:
    """Complex calculation for benchmarking."""
    total = 0.0
    for item in data:
        if 'value' in item:
            total += float(item['value'])
        if 'multiplier' in item:
            total *= float(item['multiplier'])
    return total

# Global variables
CONSTANT_{file_num} = "test_constant_{file_num}"
CONFIG_{file_num} = {{
    "enabled": True,
    "max_items": 1000,
    "timeout": 30.0
}}
'''
    
    def _generate_symbols(self, file_num: int) -> List:
        """Generate mock symbols for the file."""
        return [
            type('MockSymbol', (), {
                'name': f'TestClass{file_num}',
                'symbol_type': 'class',
                'start_line': 8,
                'start_character': 0
            })(),
            type('MockSymbol', (), {
                'name': f'utility_function_{file_num}',
                'symbol_type': 'function',
                'start_line': 35,
                'start_character': 0
            })(),
            type('MockSymbol', (), {
                'name': f'complex_calculation_{file_num}',
                'symbol_type': 'function',
                'start_line': 39,
                'start_character': 0
            })()
        ]
    
    def get_file(self, file_path: str):
        """Get file by path."""
        for file in self.files:
            if file.path == file_path:
                return file
        return None


class SerenaPerformanceBenchmark:
    """Performance benchmark suite for Serena."""
    
    def __init__(self, num_files: int = 100):
        self.num_files = num_files
        self.results = {}
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock codebase
        self.codebase = MockCodebase(self.temp_dir, num_files)
        
        # Create Serena integration
        self.serena_integration = SerenaIntegration(self.codebase)
    
    def run_benchmark(self, operation_name: str, operation_func, iterations: int = 100) -> Dict[str, Any]:
        """Run a benchmark for a specific operation."""
        print(f"Benchmarking {operation_name}...")
        
        times = []
        errors = 0
        
        for i in range(iterations):
            try:
                start_time = time.perf_counter()
                result = operation_func()
                end_time = time.perf_counter()
                
                elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
                times.append(elapsed)
                
                # Validate result
                if result is None or (isinstance(result, list) and len(result) == 0):
                    # This is expected for mock operations
                    pass
                
            except Exception as e:
                errors += 1
                print(f"Error in iteration {i}: {e}")
        
        if not times:
            return {
                'operation': operation_name,
                'error': 'No successful iterations',
                'errors': errors
            }
        
        return {
            'operation': operation_name,
            'iterations': len(times),
            'errors': errors,
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'mean_time_ms': statistics.mean(times),
            'median_time_ms': statistics.median(times),
            'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0,
            'total_time_ms': sum(times),
            'ops_per_second': 1000 / statistics.mean(times) if statistics.mean(times) > 0 else 0
        }
    
    def benchmark_completions(self) -> Dict[str, Any]:
        """Benchmark code completions."""
        def operation():
            return self.serena_integration.get_completions("src/file_0.py", 10, 5)
        
        return self.run_benchmark("get_completions", operation, 50)
    
    def benchmark_hover_info(self) -> Dict[str, Any]:
        """Benchmark hover information."""
        def operation():
            return self.serena_integration.get_hover_info("src/file_0.py", 15, 10)
        
        return self.run_benchmark("get_hover_info", operation, 50)
    
    def benchmark_signature_help(self) -> Dict[str, Any]:
        """Benchmark signature help."""
        def operation():
            return self.serena_integration.get_signature_help("src/file_0.py", 20, 15)
        
        return self.run_benchmark("get_signature_help", operation, 50)
    
    def benchmark_rename_symbol(self) -> Dict[str, Any]:
        """Benchmark symbol renaming."""
        def operation():
            return self.serena_integration.rename_symbol("src/file_0.py", 10, 5, "new_name", preview=True)
        
        return self.run_benchmark("rename_symbol", operation, 20)
    
    def benchmark_extract_method(self) -> Dict[str, Any]:
        """Benchmark method extraction."""
        def operation():
            return self.serena_integration.extract_method("src/file_0.py", 15, 25, "extracted_method")
        
        return self.run_benchmark("extract_method", operation, 20)
    
    def benchmark_semantic_search(self) -> Dict[str, Any]:
        """Benchmark semantic search."""
        def operation():
            return self.serena_integration.semantic_search("test function")
        
        return self.run_benchmark("semantic_search", operation, 10)
    
    def benchmark_find_code_patterns(self) -> Dict[str, Any]:
        """Benchmark code pattern finding."""
        def operation():
            return self.serena_integration.find_code_patterns("def.*test.*")
        
        return self.run_benchmark("find_code_patterns", operation, 10)
    
    def benchmark_get_symbol_context(self) -> Dict[str, Any]:
        """Benchmark symbol context retrieval."""
        def operation():
            return self.serena_integration.get_symbol_context("TestClass0")
        
        return self.run_benchmark("get_symbol_context", operation, 30)
    
    def benchmark_organize_imports(self) -> Dict[str, Any]:
        """Benchmark import organization."""
        def operation():
            return self.serena_integration.organize_imports("src/file_0.py")
        
        return self.run_benchmark("organize_imports", operation, 30)
    
    def benchmark_generate_tests(self) -> Dict[str, Any]:
        """Benchmark test generation."""
        def operation():
            return self.serena_integration.generate_tests("utility_function_0")
        
        return self.run_benchmark("generate_tests", operation, 10)
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks and return results."""
        print(f"Starting Serena performance benchmarks with {self.num_files} files...")
        print("=" * 60)
        
        benchmarks = [
            self.benchmark_completions,
            self.benchmark_hover_info,
            self.benchmark_signature_help,
            self.benchmark_rename_symbol,
            self.benchmark_extract_method,
            self.benchmark_semantic_search,
            self.benchmark_find_code_patterns,
            self.benchmark_get_symbol_context,
            self.benchmark_organize_imports,
            self.benchmark_generate_tests
        ]
        
        results = []
        total_start_time = time.perf_counter()
        
        for benchmark_func in benchmarks:
            result = benchmark_func()
            results.append(result)
            
            # Print immediate results
            if 'error' not in result:
                print(f"{result['operation']:25} | "
                      f"Mean: {result['mean_time_ms']:6.2f}ms | "
                      f"Median: {result['median_time_ms']:6.2f}ms | "
                      f"Ops/sec: {result['ops_per_second']:6.1f}")
            else:
                print(f"{result['operation']:25} | ERROR: {result['error']}")
        
        total_end_time = time.perf_counter()
        total_time = (total_end_time - total_start_time) * 1000
        
        print("=" * 60)
        print(f"Total benchmark time: {total_time:.2f}ms")
        
        return {
            'benchmark_config': {
                'num_files': self.num_files,
                'total_time_ms': total_time
            },
            'results': results
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> None:
        """Save benchmark results to JSON file."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"serena_benchmark_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {filename}")
    
    def cleanup(self) -> None:
        """Clean up temporary resources."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def run_performance_comparison():
    """Run performance comparison with different configurations."""
    print("Serena LSP Integration Performance Benchmarks")
    print("=" * 60)
    
    configurations = [
        {'num_files': 50, 'name': 'Small codebase'},
        {'num_files': 100, 'name': 'Medium codebase'},
        {'num_files': 500, 'name': 'Large codebase'}
    ]
    
    all_results = {}
    
    for config in configurations:
        print(f"\n🚀 Testing {config['name']} ({config['num_files']} files)")
        print("-" * 40)
        
        benchmark = SerenaPerformanceBenchmark(config['num_files'])
        results = benchmark.run_all_benchmarks()
        
        all_results[config['name']] = results
        
        # Save individual results
        benchmark.save_results(results, f"serena_benchmark_{config['name'].lower().replace(' ', '_')}.json")
        benchmark.cleanup()
    
    # Save combined results
    with open('serena_benchmark_comparison.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n📊 Performance Summary")
    print("=" * 60)
    
    # Print comparison table
    operations = ['get_completions', 'get_hover_info', 'semantic_search', 'rename_symbol']
    
    print(f"{'Operation':<20} | {'Small (50)':<12} | {'Medium (100)':<12} | {'Large (500)':<12}")
    print("-" * 65)
    
    for op in operations:
        row = f"{op:<20} |"
        
        for config_name in ['Small codebase', 'Medium codebase', 'Large codebase']:
            if config_name in all_results:
                results = all_results[config_name]['results']
                op_result = next((r for r in results if r['operation'] == op), None)
                
                if op_result and 'mean_time_ms' in op_result:
                    row += f" {op_result['mean_time_ms']:8.2f}ms |"
                else:
                    row += f" {'ERROR':<10} |"
            else:
                row += f" {'N/A':<10} |"
        
        print(row)
    
    print("\n✅ Benchmark complete! Check JSON files for detailed results.")


if __name__ == "__main__":
    run_performance_comparison()

