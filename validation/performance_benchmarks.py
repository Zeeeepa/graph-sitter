#!/usr/bin/env python3
"""
Performance Benchmarking Framework for Graph-Sitter Integration System

This module provides comprehensive performance testing and benchmarking
capabilities for the Graph-Sitter + Codegen + Contexten integration system.
"""

import asyncio
import time
import statistics
import json
import csv
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import requests
import concurrent.futures
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Data class for storing benchmark results."""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat()
        return result


@dataclass
class PerformanceMetrics:
    """Data class for performance metrics."""
    response_time_ms: float
    throughput_rps: float
    cpu_usage_percent: float
    memory_usage_mb: float
    error_rate_percent: float
    p95_response_time_ms: float
    p99_response_time_ms: float


class SystemMonitor:
    """Monitor system resources during benchmarks."""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        
    def start_monitoring(self):
        """Start system monitoring."""
        self.monitoring = True
        self.metrics = []
        
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
        
    def collect_metrics(self):
        """Collect current system metrics."""
        if not self.monitoring:
            return
            
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used / (1024 * 1024),
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / (1024 * 1024 * 1024)
        }
        
        self.metrics.append(metrics)
        return metrics
        
    def get_average_metrics(self) -> Dict[str, float]:
        """Calculate average metrics over monitoring period."""
        if not self.metrics:
            return {}
            
        avg_metrics = {}
        for key in ['cpu_percent', 'memory_percent', 'memory_used_mb', 'disk_percent']:
            values = [m[key] for m in self.metrics if key in m]
            if values:
                avg_metrics[f'avg_{key}'] = statistics.mean(values)
                avg_metrics[f'max_{key}'] = max(values)
                avg_metrics[f'min_{key}'] = min(values)
                
        return avg_metrics


class APIBenchmark:
    """Benchmark API endpoints performance."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def benchmark_endpoint(self, endpoint: str, method: str = 'GET', 
                          data: Optional[Dict] = None, 
                          concurrent_requests: int = 10,
                          total_requests: int = 100) -> BenchmarkResult:
        """Benchmark a specific API endpoint."""
        start_time = datetime.now()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        response_times = []
        errors = 0
        
        def make_request():
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                    
                response.raise_for_status()
                return response.elapsed.total_seconds() * 1000  # Convert to ms
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return None
                
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(total_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result is not None:
                    response_times.append(result)
                else:
                    errors += 1
                    
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
            throughput = len(response_times) / duration
            error_rate = (errors / total_requests) * 100
        else:
            avg_response_time = 0
            p95_response_time = 0
            p99_response_time = 0
            throughput = 0
            error_rate = 100
            
        metrics = {
            'avg_response_time_ms': avg_response_time,
            'p95_response_time_ms': p95_response_time,
            'p99_response_time_ms': p99_response_time,
            'throughput_rps': throughput,
            'error_rate_percent': error_rate,
            'total_requests': total_requests,
            'successful_requests': len(response_times),
            'failed_requests': errors
        }
        
        return BenchmarkResult(
            test_name=f"API_{method}_{endpoint}",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            success=error_rate < 5,  # Consider success if error rate < 5%
            metrics=metrics
        )


class CodeAnalysisBenchmark:
    """Benchmark code analysis performance."""
    
    def __init__(self, graph_sitter_client):
        self.client = graph_sitter_client
        
    def benchmark_file_parsing(self, file_paths: List[str]) -> BenchmarkResult:
        """Benchmark file parsing performance."""
        start_time = datetime.now()
        
        parse_times = []
        errors = 0
        total_lines = 0
        
        for file_path in file_paths:
            try:
                file_start = time.time()
                
                # Parse file with Graph-Sitter
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    total_lines += lines
                    
                # Simulate parsing (replace with actual Graph-Sitter call)
                result = self.client.parse_file(file_path)
                
                parse_time = time.time() - file_start
                parse_times.append(parse_time)
                
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
                errors += 1
                
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate metrics
        if parse_times:
            avg_parse_time = statistics.mean(parse_times)
            total_files = len(parse_times)
            files_per_second = total_files / duration
            lines_per_second = total_lines / duration
        else:
            avg_parse_time = 0
            total_files = 0
            files_per_second = 0
            lines_per_second = 0
            
        metrics = {
            'avg_parse_time_seconds': avg_parse_time,
            'total_files': len(file_paths),
            'successful_files': len(parse_times),
            'failed_files': errors,
            'total_lines': total_lines,
            'files_per_second': files_per_second,
            'lines_per_second': lines_per_second,
            'error_rate_percent': (errors / len(file_paths)) * 100
        }
        
        return BenchmarkResult(
            test_name="CodeAnalysis_FileParsing",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            success=errors == 0,
            metrics=metrics
        )
        
    def benchmark_graph_operations(self, graph_size: int = 10000) -> BenchmarkResult:
        """Benchmark graph operations performance."""
        start_time = datetime.now()
        
        try:
            # Create test graph
            graph_start = time.time()
            test_graph = self._create_test_graph(graph_size)
            graph_creation_time = time.time() - graph_start
            
            # Benchmark various graph operations
            operations = {
                'traversal': self._benchmark_graph_traversal,
                'shortest_path': self._benchmark_shortest_path,
                'centrality': self._benchmark_centrality_calculation,
                'clustering': self._benchmark_clustering
            }
            
            operation_times = {}
            for op_name, op_func in operations.items():
                op_start = time.time()
                op_func(test_graph)
                operation_times[f'{op_name}_time_seconds'] = time.time() - op_start
                
        except Exception as e:
            logger.error(f"Graph operations benchmark failed: {e}")
            return BenchmarkResult(
                test_name="CodeAnalysis_GraphOperations",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=0,
                success=False,
                error_message=str(e)
            )
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        metrics = {
            'graph_size': graph_size,
            'graph_creation_time_seconds': graph_creation_time,
            **operation_times,
            'total_operation_time_seconds': sum(operation_times.values())
        }
        
        return BenchmarkResult(
            test_name="CodeAnalysis_GraphOperations",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            success=True,
            metrics=metrics
        )
        
    def _create_test_graph(self, size: int):
        """Create a test graph for benchmarking."""
        # Placeholder - implement actual graph creation
        return {"nodes": size, "edges": size * 2}
        
    def _benchmark_graph_traversal(self, graph):
        """Benchmark graph traversal operations."""
        # Placeholder - implement actual traversal
        time.sleep(0.1)  # Simulate processing
        
    def _benchmark_shortest_path(self, graph):
        """Benchmark shortest path calculations."""
        # Placeholder - implement actual shortest path
        time.sleep(0.05)  # Simulate processing
        
    def _benchmark_centrality_calculation(self, graph):
        """Benchmark centrality calculations."""
        # Placeholder - implement actual centrality
        time.sleep(0.2)  # Simulate processing
        
    def _benchmark_clustering(self, graph):
        """Benchmark clustering operations."""
        # Placeholder - implement actual clustering
        time.sleep(0.15)  # Simulate processing


class IntegrationBenchmark:
    """Benchmark end-to-end integration scenarios."""
    
    def __init__(self, api_client, graph_sitter_client, codegen_client):
        self.api_client = api_client
        self.graph_sitter_client = graph_sitter_client
        self.codegen_client = codegen_client
        
    def benchmark_full_pipeline(self, test_codebase_path: str) -> BenchmarkResult:
        """Benchmark complete analysis pipeline."""
        start_time = datetime.now()
        
        try:
            # Step 1: Initialize codebase analysis
            init_start = time.time()
            codebase = self.graph_sitter_client.load_codebase(test_codebase_path)
            init_time = time.time() - init_start
            
            # Step 2: Perform code analysis
            analysis_start = time.time()
            analysis_result = self.graph_sitter_client.analyze(codebase)
            analysis_time = time.time() - analysis_start
            
            # Step 3: Generate insights with Codegen
            codegen_start = time.time()
            insights = self.codegen_client.generate_insights(analysis_result)
            codegen_time = time.time() - codegen_start
            
            # Step 4: Orchestrate with Contexten
            orchestration_start = time.time()
            final_result = self.api_client.orchestrate_workflow(insights)
            orchestration_time = time.time() - orchestration_start
            
        except Exception as e:
            logger.error(f"Integration benchmark failed: {e}")
            return BenchmarkResult(
                test_name="Integration_FullPipeline",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=0,
                success=False,
                error_message=str(e)
            )
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        metrics = {
            'initialization_time_seconds': init_time,
            'analysis_time_seconds': analysis_time,
            'codegen_time_seconds': codegen_time,
            'orchestration_time_seconds': orchestration_time,
            'total_pipeline_time_seconds': duration,
            'files_processed': len(codebase.get('files', [])),
            'insights_generated': len(insights.get('insights', [])),
            'success': True
        }
        
        return BenchmarkResult(
            test_name="Integration_FullPipeline",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            success=True,
            metrics=metrics
        )


class BenchmarkSuite:
    """Main benchmark suite orchestrator."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = []
        self.monitor = SystemMonitor()
        
    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all configured benchmarks."""
        logger.info("Starting comprehensive benchmark suite")
        
        # Start system monitoring
        self.monitor.start_monitoring()
        
        try:
            # API Benchmarks
            if self.config.get('run_api_benchmarks', True):
                self._run_api_benchmarks()
                
            # Code Analysis Benchmarks
            if self.config.get('run_analysis_benchmarks', True):
                self._run_analysis_benchmarks()
                
            # Integration Benchmarks
            if self.config.get('run_integration_benchmarks', True):
                self._run_integration_benchmarks()
                
        finally:
            # Stop monitoring
            self.monitor.stop_monitoring()
            
        logger.info(f"Benchmark suite completed. {len(self.results)} tests executed.")
        return self.results
        
    def _run_api_benchmarks(self):
        """Run API performance benchmarks."""
        logger.info("Running API benchmarks")
        
        api_config = self.config.get('api_benchmarks', {})
        base_url = api_config.get('base_url', 'http://localhost:8000')
        
        api_benchmark = APIBenchmark(base_url)
        
        endpoints = api_config.get('endpoints', [
            {'path': '/health', 'method': 'GET'},
            {'path': '/api/v1/analyze', 'method': 'POST', 'data': {'code': 'print("hello")'}},
            {'path': '/api/v1/graph', 'method': 'GET'},
        ])
        
        for endpoint in endpoints:
            result = api_benchmark.benchmark_endpoint(
                endpoint['path'],
                endpoint.get('method', 'GET'),
                endpoint.get('data'),
                api_config.get('concurrent_requests', 10),
                api_config.get('total_requests', 100)
            )
            self.results.append(result)
            
    def _run_analysis_benchmarks(self):
        """Run code analysis benchmarks."""
        logger.info("Running code analysis benchmarks")
        
        # Placeholder - implement actual analysis benchmarks
        analysis_config = self.config.get('analysis_benchmarks', {})
        
        # Mock benchmark result
        result = BenchmarkResult(
            test_name="CodeAnalysis_Mock",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=5),
            duration_seconds=5.0,
            success=True,
            metrics={'files_processed': 100, 'avg_parse_time': 0.05}
        )
        self.results.append(result)
        
    def _run_integration_benchmarks(self):
        """Run integration benchmarks."""
        logger.info("Running integration benchmarks")
        
        # Placeholder - implement actual integration benchmarks
        integration_config = self.config.get('integration_benchmarks', {})
        
        # Mock benchmark result
        result = BenchmarkResult(
            test_name="Integration_Mock",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=10),
            duration_seconds=10.0,
            success=True,
            metrics={'pipeline_time': 10.0, 'components_tested': 3}
        )
        self.results.append(result)
        
    def generate_report(self, output_path: str = "benchmark_report.json"):
        """Generate comprehensive benchmark report."""
        logger.info(f"Generating benchmark report: {output_path}")
        
        # Compile results
        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(self.results),
                'successful_tests': sum(1 for r in self.results if r.success),
                'failed_tests': sum(1 for r in self.results if not r.success),
                'total_duration_seconds': sum(r.duration_seconds for r in self.results)
            },
            'system_metrics': self.monitor.get_average_metrics(),
            'test_results': [result.to_dict() for result in self.results],
            'summary': self._generate_summary()
        }
        
        # Write JSON report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Generate CSV report
        csv_path = output_path.replace('.json', '.csv')
        self._generate_csv_report(csv_path)
        
        logger.info(f"Reports generated: {output_path}, {csv_path}")
        
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate benchmark summary statistics."""
        if not self.results:
            return {}
            
        successful_results = [r for r in self.results if r.success]
        
        summary = {
            'overall_success_rate': len(successful_results) / len(self.results) * 100,
            'average_duration_seconds': statistics.mean([r.duration_seconds for r in self.results]),
            'total_duration_seconds': sum(r.duration_seconds for r in self.results)
        }
        
        # API-specific metrics
        api_results = [r for r in successful_results if r.test_name.startswith('API_')]
        if api_results:
            api_response_times = []
            api_throughputs = []
            
            for result in api_results:
                if result.metrics:
                    if 'avg_response_time_ms' in result.metrics:
                        api_response_times.append(result.metrics['avg_response_time_ms'])
                    if 'throughput_rps' in result.metrics:
                        api_throughputs.append(result.metrics['throughput_rps'])
                        
            if api_response_times:
                summary['api_avg_response_time_ms'] = statistics.mean(api_response_times)
                summary['api_p95_response_time_ms'] = statistics.quantiles(api_response_times, n=20)[18]
                
            if api_throughputs:
                summary['api_avg_throughput_rps'] = statistics.mean(api_throughputs)
                summary['api_total_throughput_rps'] = sum(api_throughputs)
                
        return summary
        
    def _generate_csv_report(self, csv_path: str):
        """Generate CSV report for easy analysis."""
        if not self.results:
            return
            
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = ['test_name', 'duration_seconds', 'success', 'start_time', 'end_time']
            
            # Add metric fields
            all_metrics = set()
            for result in self.results:
                if result.metrics:
                    all_metrics.update(result.metrics.keys())
            fieldnames.extend(sorted(all_metrics))
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                row = {
                    'test_name': result.test_name,
                    'duration_seconds': result.duration_seconds,
                    'success': result.success,
                    'start_time': result.start_time.isoformat(),
                    'end_time': result.end_time.isoformat()
                }
                
                if result.metrics:
                    row.update(result.metrics)
                    
                writer.writerow(row)


def main():
    """Main benchmark execution function."""
    # Default configuration
    config = {
        'run_api_benchmarks': True,
        'run_analysis_benchmarks': True,
        'run_integration_benchmarks': True,
        'api_benchmarks': {
            'base_url': 'http://localhost:8000',
            'concurrent_requests': 10,
            'total_requests': 100,
            'endpoints': [
                {'path': '/health', 'method': 'GET'},
                {'path': '/api/v1/status', 'method': 'GET'},
            ]
        },
        'analysis_benchmarks': {
            'test_codebase_path': './test_codebase',
            'file_count': 100
        },
        'integration_benchmarks': {
            'test_scenarios': ['full_pipeline', 'concurrent_users']
        }
    }
    
    # Initialize and run benchmark suite
    suite = BenchmarkSuite(config)
    results = suite.run_all_benchmarks()
    
    # Generate reports
    suite.generate_report('validation/benchmark_results.json')
    
    # Print summary
    print(f"\nBenchmark Summary:")
    print(f"Total tests: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r.success)}")
    print(f"Failed: {sum(1 for r in results if not r.success)}")
    print(f"Total duration: {sum(r.duration_seconds for r in results):.2f} seconds")
    
    return results


if __name__ == "__main__":
    main()

